from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Callable, Dict
from uuid import UUID

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
