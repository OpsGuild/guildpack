from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Callable, Dict, List, Union
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
    """
    Recursively sanitize data structures:
    - Remove empty fields
    - Apply key remapping
    - Apply per-field processors
    - Convert types like UUID, datetime, Decimal
    """

    if isinstance(data, BaseModel):
        # Use model_dump for Pydantic V2 compatibility
        try:
            model_data = data.model_dump(exclude_none=True)
        except AttributeError:
            # Fallback for older Pydantic versions
            model_data = data.dict(exclude_none=True)
        
        return await sanitize_fields(
            model_data,
            empty_values=empty_values,
            key_mapping=key_mapping,
            field_processors=field_processors,
        )

    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            # Check for empty values
            is_empty = False
            if isinstance(value, (list, dict)):
                is_empty = not value  # Empty list or dict
            else:
                is_empty = value in empty_values or value == [] or value == {}
            
            if is_empty:
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

    if isinstance(data, list):
        sanitized_list = [
            await sanitize_fields(
                v, empty_values, key_mapping, field_processors
            )
            for v in data
        ]
        return [
            v
            for v in sanitized_list
            if not (
                (isinstance(v, (list, dict)) and not v) or
                (not isinstance(v, (list, dict)) and (v in empty_values or v == [] or v == {}))
            )
        ]

    if isinstance(data, UUID):
        return str(data)
    if isinstance(data, datetime):
        return data.isoformat()
    if isinstance(data, date):
        return data.isoformat()
    if isinstance(data, time):
        return data.strftime("%H:%M:%S")
    if isinstance(data, Decimal):
        return float(data)

    return data
