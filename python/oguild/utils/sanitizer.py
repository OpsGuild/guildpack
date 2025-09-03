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
        return await sanitize_fields(
            data.dict(exclude_none=True),
            empty_values=empty_values,
            key_mapping=key_mapping,
            field_processors=field_processors,
        )

    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            # Check for empty values
            if value in empty_values or value == [] or value == {}:
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
            if v not in empty_values and v != [] and v != {}
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
