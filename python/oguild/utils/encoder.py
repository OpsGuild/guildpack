import json

from oguild.logs import logger


async def encode_json_fields(rows, json_keys: list[str]):
    """
    Serializes specified dictionary fields into JSON strings.
    """
    if not isinstance(rows, list):
        rows = [rows]
    for row in rows:
        for key in json_keys:
            if key in row and isinstance(row[key], (dict, list)):
                try:
                    row[key] = json.dumps(row[key])
                except (TypeError, OverflowError) as e:
                    logger.error(f"Error encoding JSON for key '{key}': {e}")
                    continue
    return rows if len(rows) > 1 else rows[0]
