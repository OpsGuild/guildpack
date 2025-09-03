import json
from collections.abc import Mapping

from oguild.logs import logger


async def decode_json_fields(rows, json_keys: list[str]):
    """
    Parses specified JSON fields in each row of the result set.
    """
    for row in rows:
        if not isinstance(row, Mapping):
            continue

        for key in json_keys:
            if (
                key in row
                and isinstance(row[key], str)
                and row[key].strip().startswith(("{", "["))
            ):
                try:
                    row[key] = json.loads(row[key])
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON for key '{key}': {e}")
    return rows
