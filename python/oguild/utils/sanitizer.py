from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from .case_converter import Case, CaseType  # noqa: F401

from pydantic import BaseModel

DEFAULT_EMPTY_VALUES = {None, ""}
DEFAULT_KEY_MAPPING = {
    "_id": "id",
}
DEFAULT_FIELD_PROCESSORS: Dict[str, Callable[[Any], Any]] = {}


async def sanitize_fields(
    data: Any,
    empty_values: set = DEFAULT_EMPTY_VALUES,
    key_mapping: dict = DEFAULT_KEY_MAPPING,
    field_processors: dict = DEFAULT_FIELD_PROCESSORS,
) -> Any:
    if isinstance(data, BaseModel):
        return await _sanitize_model(
            data, empty_values, key_mapping, field_processors
        )
    if isinstance(data, dict):
        return await _sanitize_dict(
            data, empty_values, key_mapping, field_processors
        )
    if isinstance(data, list):
        return await _sanitize_list(
            data, empty_values, key_mapping, field_processors
        )
    return _sanitize_primitive(data, empty_values)


async def _sanitize_model(data, empty_values, key_mapping, field_processors):
    try:
        model_data = data.model_dump(exclude_none=True)
    except AttributeError:
        model_data = data.dict(exclude_none=True)

    return await sanitize_fields(
        model_data, empty_values, key_mapping, field_processors
    )


async def _sanitize_dict(data, empty_values, key_mapping, field_processors):
    sanitized = {}
    for key, value in data.items():
        if _is_empty(value, empty_values):
            continue

        new_key = key_mapping.get(key, key)

        processor = field_processors.get(new_key)
        if processor:
            try:
                sanitized[new_key] = await processor(value)
            except Exception:
                sanitized[new_key] = value
            continue

        sanitized[new_key] = await sanitize_fields(
            value, empty_values, key_mapping, field_processors
        )

    return sanitized


async def _sanitize_list(data, empty_values, key_mapping, field_processors):
    sanitized_list = [
        await sanitize_fields(v, empty_values, key_mapping, field_processors)
        for v in data
    ]
    return [v for v in sanitized_list if not _is_empty(v, empty_values)]


def _sanitize_primitive(data, empty_values):
    if isinstance(data, UUID):
        return str(data)
    if isinstance(data, (datetime, date)):
        return data.isoformat()
    if isinstance(data, time):
        return data.strftime("%H:%M:%S")
    if isinstance(data, Decimal):
        return float(data)
    return data


def _is_empty(value, empty_values):
    if isinstance(value, (list, dict)):
        return not value
    return value in empty_values or value == [] or value == {}


# ============================================================================
# Serialization utilities for request/response handling
# ============================================================================

def get_local_datetime() -> datetime:
    """Get the current local datetime with timezone info."""
    return datetime.now().astimezone()


def convert_value(value: Any) -> Any:
    """
    Convert value to a JSON-serializable format.
    Converts UTC datetime objects to local timezone before serialization.
    """
    if value is None:
        return value
    elif isinstance(value, UUID):
        return str(value)
    elif isinstance(value, str):
        return value
    elif isinstance(value, datetime):
        # Convert UTC datetime to local timezone for display
        if value.tzinfo == timezone.utc or value.tzinfo is None:
            # If it's UTC or naive, convert to local time
            if value.tzinfo is None:
                # For naive datetime, assume it's UTC
                value = value.replace(tzinfo=timezone.utc)
            # Get local timezone and convert
            local_tz = get_local_datetime().tzinfo
            local_dt = value.astimezone(local_tz)
            return local_dt.isoformat()
        return value.isoformat()
    elif isinstance(value, date):
        return value.isoformat()
    elif isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, (int, float, bool)):
        return value
    elif isinstance(value, bytes):
        return value.decode("utf-8")
    else:
        try:
            return str(value)
        except Exception:
            return value


def filter_null_fields(data: Any) -> Any:
    """
    Recursively remove null/None fields from dictionaries.
    """
    if isinstance(data, dict):
        return {
            k: filter_null_fields(v)
            for k, v in data.items()
            if v is not None
        }
    elif isinstance(data, list):
        return [filter_null_fields(item) for item in data if item is not None]
    return data


def serialize_response(
    data: Any,
    case: Optional["CaseType"] = None
) -> Any:
    """
    Serialize response data, converting field names to the specified case.

    Args:
        data: The data to serialize (dict, list, or primitive)
        case: Target case for keys (Case enum or string like 'camel', 'snake',
              'kebab'). Default is Case.CAMEL if not specified.
              Set to None explicitly to skip conversion.

    Returns:
        Serialized data with converted keys

    Examples:
        >>> from oguild.utils import Case
        >>> serialize_response({"user_name": "John"}, "camel")
        {'userName': 'John'}
        >>> serialize_response({"user_name": "John"}, Case.KEBAB)
        {'user-name': 'John'}
    """
    # Import here to avoid circular imports
    from .case_converter import (  # noqa: F401
        Case as CaseEnum,
        CaseType,
        convert_dict_keys,
        convert_dict_keys_to_camel_case,
        _normalize_case
    )

    # Default to CAMEL if case is not explicitly set
    if case is None:
        target = CaseEnum.CAMEL
    else:
        target = _normalize_case(case)

    data = filter_null_fields(data)

    if isinstance(data, dict):
        if target == CaseEnum.CAMEL:
            return convert_dict_keys_to_camel_case(data)
        return convert_dict_keys(data, target)
    elif isinstance(data, list):
        return [
            (convert_dict_keys_to_camel_case(item)
             if target == CaseEnum.CAMEL else convert_dict_keys(item, target))
            if isinstance(item, dict)
            else convert_value(item)
            for item in data
        ]
    else:
        return convert_value(data)


def serialize_request(
    data: Any,
    case: Optional["CaseType"] = None
) -> Any:
    """
    Serialize request data, converting field names to the specified case.
    Handles None/null values by returning an empty dict.

    Args:
        data: The data to serialize (dict, list, or primitive)
        case: Target case for keys (Case enum or string like 'snake', 'camel').
              Default is Case.SNAKE if not specified.
              Set explicitly to skip conversion (e.g. by passing input case).

    Returns:
        Serialized data with converted keys

    Examples:
        >>> from oguild.utils import Case
        >>> serialize_request({"userName": "John"}, "snake")
        {'user_name': 'John'}
    """
    # Import here to avoid circular imports
    from .case_converter import (  # noqa: F401
        Case as CaseEnum, CaseType, _normalize_case, convert_dict_keys
    )

    if data is None:
        return {}

    # Default to SNAKE if case is not explicitly set
    if case is None:
        target = CaseEnum.SNAKE
    else:
        target = _normalize_case(case)

    if isinstance(data, dict):
        return convert_dict_keys(data, target)
    elif isinstance(data, list):
        return [
            convert_dict_keys(item, target)
            if isinstance(item, dict)
            else item
            for item in data
        ]
    else:
        return data
