import pytest
from oguild.utils import decode_json_fields


class TestDecodeJsonFields:
    """Test cases for decode_json_fields function."""

    @pytest.mark.asyncio
    async def test_decode_single_row(self):
        """Test decoding JSON fields in a single row."""
        row = {
            "id": 1,
            "name": "test",
            "metadata": '{"key": "value"}',
            "tags": '["tag1", "tag2"]',
        }
        json_keys = ["metadata", "tags"]

        result = await decode_json_fields([row], json_keys)

        expected = [
            {
                "id": 1,
                "name": "test",
                "metadata": {"key": "value"},
                "tags": ["tag1", "tag2"],
            }
        ]
        assert result == expected

    @pytest.mark.asyncio
    async def test_decode_multiple_rows(self):
        """Test decoding JSON fields in multiple rows."""
        rows = [
            {"id": 1, "name": "test1", "metadata": '{"key": "value1"}'},
            {"id": 2, "name": "test2", "metadata": '{"key": "value2"}'},
        ]
        json_keys = ["metadata"]

        result = await decode_json_fields(rows, json_keys)

        expected = [
            {"id": 1, "name": "test1", "metadata": {"key": "value1"}},
            {"id": 2, "name": "test2", "metadata": {"key": "value2"}},
        ]
        assert result == expected

    @pytest.mark.asyncio
    async def test_decode_non_string_values(self):
        """Test decoding when JSON keys contain non-string values."""
        row = {
            "id": 1,
            "name": "test",
            "metadata": {"already": "decoded"},
            "tags": 123,
        }
        json_keys = ["metadata", "tags"]

        result = await decode_json_fields([row], json_keys)

        expected = [
            {
                "id": 1,
                "name": "test",
                "metadata": {"already": "decoded"},
                "tags": 123,
            }
        ]
        assert result == expected

    @pytest.mark.asyncio
    async def test_decode_missing_keys(self):
        """Test decoding when JSON keys don't exist in row."""
        row = {"id": 1, "name": "test"}
        json_keys = ["metadata", "tags"]

        result = await decode_json_fields([row], json_keys)

        expected = [{"id": 1, "name": "test"}]
        assert result == expected

    @pytest.mark.asyncio
    async def test_decode_invalid_json(self):
        """Test handling of invalid JSON strings."""
        row = {
            "id": 1,
            "name": "test",
            "metadata": '{"invalid": json}',
            "tags": '["incomplete',
        }
        json_keys = ["metadata", "tags"]

        result = await decode_json_fields([row], json_keys)
        assert result == [row]

    @pytest.mark.asyncio
    async def test_decode_non_json_strings(self):
        """Test decoding strings that don't look like JSON."""
        row = {
            "id": 1,
            "name": "test",
            "description": "This is not JSON",
            "status": "active",
        }
        json_keys = ["description", "status"]

        result = await decode_json_fields([row], json_keys)

        expected = [
            {
                "id": 1,
                "name": "test",
                "description": "This is not JSON",
                "status": "active",
            }
        ]
        assert result == expected

    @pytest.mark.asyncio
    async def test_decode_empty_json(self):
        """Test decoding empty JSON objects and arrays."""
        row = {"id": 1, "name": "test", "empty_dict": "{}", "empty_list": "[]"}
        json_keys = ["empty_dict", "empty_list"]

        result = await decode_json_fields([row], json_keys)

        expected = [
            {"id": 1, "name": "test", "empty_dict": {}, "empty_list": []}
        ]
        assert result == expected

    @pytest.mark.asyncio
    async def test_decode_non_mapping_rows(self):
        """Test decoding when rows contain non-mapping objects."""
        rows = [
            {"id": 1, "name": "test", "metadata": '{"key": "value"}'},
            "not a dict",
            {"id": 2, "name": "test2", "metadata": '{"key": "value2"}'},
        ]
        json_keys = ["metadata"]

        result = await decode_json_fields(rows, json_keys)

        expected = [
            {"id": 1, "name": "test", "metadata": {"key": "value"}},
            "not a dict",
            {"id": 2, "name": "test2", "metadata": {"key": "value2"}},
        ]
        assert result == expected
