"""Tests for encode_json_fields function."""

import pytest

from oguild.utils import encode_json_fields


class TestEncodeJsonFields:
    """Test cases for encode_json_fields function."""

    @pytest.mark.asyncio
    async def test_encode_single_row(self):
        """Test encoding JSON fields in a single row."""
        row = {
            "id": 1,
            "name": "test",
            "metadata": {"key": "value"},
            "tags": ["tag1", "tag2"]
        }
        json_keys = ["metadata", "tags"]
        
        result = await encode_json_fields(row, json_keys)
        
        expected = {
            "id": 1,
            "name": "test",
            "metadata": '{"key": "value"}',
            "tags": '["tag1", "tag2"]'
        }
        assert result == expected

    @pytest.mark.asyncio
    async def test_encode_multiple_rows(self):
        """Test encoding JSON fields in multiple rows."""
        rows = [
            {
                "id": 1,
                "name": "test1",
                "metadata": {"key": "value1"}
            },
            {
                "id": 2,
                "name": "test2",
                "metadata": {"key": "value2"}
            }
        ]
        json_keys = ["metadata"]
        
        result = await encode_json_fields(rows, json_keys)
        
        expected = [
            {
                "id": 1,
                "name": "test1",
                "metadata": '{"key": "value1"}'
            },
            {
                "id": 2,
                "name": "test2",
                "metadata": '{"key": "value2"}'
            }
        ]
        assert result == expected

    @pytest.mark.asyncio
    async def test_encode_non_dict_values(self):
        """Test encoding when JSON keys contain non-dict/list values."""
        row = {
            "id": 1,
            "name": "test",
            "metadata": "not a dict",
            "tags": 123
        }
        json_keys = ["metadata", "tags"]
        
        result = await encode_json_fields(row, json_keys)
        
        # Should not change non-dict/list values
        expected = {
            "id": 1,
            "name": "test",
            "metadata": "not a dict",
            "tags": 123
        }
        assert result == expected

    @pytest.mark.asyncio
    async def test_encode_missing_keys(self):
        """Test encoding when JSON keys don't exist in row."""
        row = {"id": 1, "name": "test"}
        json_keys = ["metadata", "tags"]
        
        result = await encode_json_fields(row, json_keys)
        
        # Should not change anything
        expected = {"id": 1, "name": "test"}
        assert result == expected

    @pytest.mark.asyncio
    async def test_encode_encoding_error(self):
        """Test handling of JSON encoding errors."""
        # Create an object that can't be JSON serialized
        class NonSerializable:
            pass
        
        row = {
            "id": 1,
            "name": "test",
            "metadata": {"key": NonSerializable()}
        }
        json_keys = ["metadata"]
        
        # Should not raise an exception, should keep original value
        result = await encode_json_fields(row, json_keys)
        assert result == row

    @pytest.mark.asyncio
    async def test_encode_empty_dict_list(self):
        """Test encoding empty dict and list."""
        row = {
            "id": 1,
            "name": "test",
            "empty_dict": {},
            "empty_list": []
        }
        json_keys = ["empty_dict", "empty_list"]
        
        result = await encode_json_fields(row, json_keys)
        
        expected = {
            "id": 1,
            "name": "test",
            "empty_dict": "{}",
            "empty_list": "[]"
        }
        assert result == expected
