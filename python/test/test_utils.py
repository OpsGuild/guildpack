import json
import pytest
from datetime import date, datetime, time
from decimal import Decimal
from uuid import uuid4

from pydantic import BaseModel

from oguild.utils import sanitize_fields, encode_json_fields, decode_json_fields


class TestSanitizeFields:
    """Test cases for sanitize_fields function."""

    @pytest.mark.asyncio
    async def test_sanitize_simple_dict(self):
        """Test sanitizing a simple dictionary."""
        data = {"name": "test", "age": 25, "empty": None}
        result = await sanitize_fields(data)
        
        expected = {"name": "test", "age": 25}
        assert result == expected

    @pytest.mark.asyncio
    async def test_sanitize_empty_values(self):
        """Test removing empty values."""
        data = {
            "name": "test",
            "empty_string": "",
            "empty_list": [],
            "empty_dict": {},
            "none_value": None
        }
        result = await sanitize_fields(data)
        
        expected = {"name": "test"}
        assert result == expected

    @pytest.mark.asyncio
    async def test_sanitize_nested_dict(self):
        """Test sanitizing nested dictionaries."""
        data = {
            "user": {
                "name": "test",
                "profile": {
                    "age": 25,
                    "empty": None
                }
            },
            "empty": []
        }
        result = await sanitize_fields(data)
        
        expected = {
            "user": {
                "name": "test",
                "profile": {
                    "age": 25
                }
            }
        }
        assert result == expected

    @pytest.mark.asyncio
    async def test_sanitize_list(self):
        """Test sanitizing lists."""
        data = [
            {"name": "test1", "empty": None},
            {"name": "test2", "empty": []},
            {"name": "test3", "empty": {}}
        ]
        result = await sanitize_fields(data)
        
        expected = [
            {"name": "test1"},
            {"name": "test2"},
            {"name": "test3"}
        ]
        assert result == expected

    @pytest.mark.asyncio
    async def test_sanitize_mixed_list(self):
        """Test sanitizing mixed content lists."""
        data = [
            "test",
            None,
            "",
            [],
            {},
            {"name": "test"}
        ]
        result = await sanitize_fields(data)
        
        expected = [
            "test",
            {"name": "test"}
        ]
        assert result == expected

    @pytest.mark.asyncio
    async def test_sanitize_uuid(self):
        """Test UUID conversion."""
        test_uuid = uuid4()
        data = {"id": test_uuid, "name": "test"}
        result = await sanitize_fields(data)
        
        expected = {"id": str(test_uuid), "name": "test"}
        assert result == expected

    @pytest.mark.asyncio
    async def test_sanitize_datetime(self):
        """Test datetime conversion."""
        test_datetime = datetime(2023, 1, 1, 12, 0, 0)
        data = {"created_at": test_datetime, "name": "test"}
        result = await sanitize_fields(data)
        
        expected = {"created_at": "2023-01-01T12:00:00", "name": "test"}
        assert result == expected

    @pytest.mark.asyncio
    async def test_sanitize_date(self):
        """Test date conversion."""
        test_date = date(2023, 1, 1)
        data = {"birth_date": test_date, "name": "test"}
        result = await sanitize_fields(data)
        
        expected = {"birth_date": "2023-01-01", "name": "test"}
        assert result == expected

    @pytest.mark.asyncio
    async def test_sanitize_time(self):
        """Test time conversion."""
        test_time = time(12, 30, 45)
        data = {"meeting_time": test_time, "name": "test"}
        result = await sanitize_fields(data)
        
        expected = {"meeting_time": "12:30:45", "name": "test"}
        assert result == expected

    @pytest.mark.asyncio
    async def test_sanitize_decimal(self):
        """Test Decimal conversion."""
        test_decimal = Decimal("123.45")
        data = {"price": test_decimal, "name": "test"}
        result = await sanitize_fields(data)
        
        expected = {"price": 123.45, "name": "test"}
        assert result == expected

    @pytest.mark.asyncio
    async def test_sanitize_pydantic_model(self):
        """Test Pydantic model conversion."""
        class TestModel(BaseModel):
            name: str
            age: int
            empty: str = None
        
        model = TestModel(name="test", age=25)
        result = await sanitize_fields(model)
        
        expected = {"name": "test", "age": 25}
        assert result == expected

    @pytest.mark.asyncio
    async def test_sanitize_key_mapping(self):
        """Test key mapping functionality."""
        data = {"_id": "123", "name": "test"}
        key_mapping = {"_id": "id"}
        result = await sanitize_fields(data, key_mapping=key_mapping)
        
        expected = {"id": "123", "name": "test"}
        assert result == expected

    @pytest.mark.asyncio
    async def test_sanitize_field_processors(self):
        """Test field processors functionality."""
        async def uppercase_processor(value):
            return value.upper() if isinstance(value, str) else value
        
        data = {"name": "test", "description": "hello"}
        field_processors = {"name": uppercase_processor}
        result = await sanitize_fields(data, field_processors=field_processors)
        
        expected = {"name": "TEST", "description": "hello"}
        assert result == expected

    @pytest.mark.asyncio
    async def test_sanitize_field_processor_error(self):
        """Test field processor error handling."""
        async def error_processor(value):
            raise Exception("Processor error")
        
        data = {"name": "test"}
        field_processors = {"name": error_processor}
        result = await sanitize_fields(data, field_processors=field_processors)
        
        # Should keep original value on error
        expected = {"name": "test"}
        assert result == expected

    @pytest.mark.asyncio
    async def test_sanitize_custom_empty_values(self):
        """Test custom empty values."""
        data = {"name": "test", "status": "inactive", "empty": None}
        empty_values = {None, "inactive"}
        result = await sanitize_fields(data, empty_values=empty_values)
        
        expected = {"name": "test"}
        assert result == expected

    @pytest.mark.asyncio
    async def test_sanitize_primitive_types(self):
        """Test sanitizing primitive types."""
        test_cases = [
            ("string", "string"),
            (123, 123),
            (123.45, 123.45),
            (True, True),
            (False, False)
        ]
        
        for input_value, expected in test_cases:
            result = await sanitize_fields(input_value)
            assert result == expected

    @pytest.mark.asyncio
    async def test_sanitize_complex_nested(self):
        """Test sanitizing complex nested structures."""
        data = {
            "users": [
                {
                    "_id": uuid4(),
                    "name": "user1",
                    "profile": {
                        "age": 25,
                        "empty": None,
                        "tags": ["tag1", "", "tag3"]
                    },
                    "empty": []
                },
                {
                    "_id": uuid4(),
                    "name": "user2",
                    "profile": {
                        "age": 30,
                        "empty": {},
                        "tags": []
                    }
                }
            ],
            "metadata": {
                "created_at": datetime(2023, 1, 1, 12, 0, 0),
                "price": Decimal("99.99"),
                "empty": None
            }
        }
        
        key_mapping = {"_id": "id"}
        result = await sanitize_fields(data, key_mapping=key_mapping)
        
        # Check structure
        assert "users" in result
        assert "metadata" in result
        assert len(result["users"]) == 2
        
        # Check first user
        user1 = result["users"][0]
        assert "id" in user1
        assert "name" in user1
        assert "profile" in user1
        assert "empty" not in user1
        
        # Check profile
        profile = user1["profile"]
        assert "age" in profile
        assert "empty" not in profile
        assert "tags" in profile
        assert len(profile["tags"]) == 2  # Empty string removed


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


class TestDecodeJsonFields:
    """Test cases for decode_json_fields function."""

    @pytest.mark.asyncio
    async def test_decode_single_row(self):
        """Test decoding JSON fields in a single row."""
        row = {
            "id": 1,
            "name": "test",
            "metadata": '{"key": "value"}',
            "tags": '["tag1", "tag2"]'
        }
        json_keys = ["metadata", "tags"]
        
        result = await decode_json_fields([row], json_keys)
        
        expected = [{
            "id": 1,
            "name": "test",
            "metadata": {"key": "value"},
            "tags": ["tag1", "tag2"]
        }]
        assert result == expected

    @pytest.mark.asyncio
    async def test_decode_multiple_rows(self):
        """Test decoding JSON fields in multiple rows."""
        rows = [
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
        json_keys = ["metadata"]
        
        result = await decode_json_fields(rows, json_keys)
        
        expected = [
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
        assert result == expected

    @pytest.mark.asyncio
    async def test_decode_non_string_values(self):
        """Test decoding when JSON keys contain non-string values."""
        row = {
            "id": 1,
            "name": "test",
            "metadata": {"already": "decoded"},
            "tags": 123
        }
        json_keys = ["metadata", "tags"]
        
        result = await decode_json_fields([row], json_keys)
        
        # Should not change non-string values
        expected = [{
            "id": 1,
            "name": "test",
            "metadata": {"already": "decoded"},
            "tags": 123
        }]
        assert result == expected

    @pytest.mark.asyncio
    async def test_decode_missing_keys(self):
        """Test decoding when JSON keys don't exist in row."""
        row = {"id": 1, "name": "test"}
        json_keys = ["metadata", "tags"]
        
        result = await decode_json_fields([row], json_keys)
        
        # Should not change anything
        expected = [{"id": 1, "name": "test"}]
        assert result == expected

    @pytest.mark.asyncio
    async def test_decode_invalid_json(self):
        """Test handling of invalid JSON strings."""
        row = {
            "id": 1,
            "name": "test",
            "metadata": '{"invalid": json}',
            "tags": '["incomplete'
        }
        json_keys = ["metadata", "tags"]
        
        # Should not raise an exception, should keep original values
        result = await decode_json_fields([row], json_keys)
        assert result == [row]

    @pytest.mark.asyncio
    async def test_decode_non_json_strings(self):
        """Test decoding strings that don't look like JSON."""
        row = {
            "id": 1,
            "name": "test",
            "description": "This is not JSON",
            "status": "active"
        }
        json_keys = ["description", "status"]
        
        result = await decode_json_fields([row], json_keys)
        
        # Should not change strings that don't start with { or [
        expected = [{
            "id": 1,
            "name": "test",
            "description": "This is not JSON",
            "status": "active"
        }]
        assert result == expected

    @pytest.mark.asyncio
    async def test_decode_empty_json(self):
        """Test decoding empty JSON objects and arrays."""
        row = {
            "id": 1,
            "name": "test",
            "empty_dict": "{}",
            "empty_list": "[]"
        }
        json_keys = ["empty_dict", "empty_list"]
        
        result = await decode_json_fields([row], json_keys)
        
        expected = [{
            "id": 1,
            "name": "test",
            "empty_dict": {},
            "empty_list": []
        }]
        assert result == expected

    @pytest.mark.asyncio
    async def test_decode_non_mapping_rows(self):
        """Test decoding when rows contain non-mapping objects."""
        rows = [
            {"id": 1, "name": "test", "metadata": '{"key": "value"}'},
            "not a dict",
            {"id": 2, "name": "test2", "metadata": '{"key": "value2"}'}
        ]
        json_keys = ["metadata"]
        
        result = await decode_json_fields(rows, json_keys)
        
        # Should skip non-mapping objects
        expected = [
            {"id": 1, "name": "test", "metadata": {"key": "value"}},
            "not a dict",
            {"id": 2, "name": "test2", "metadata": {"key": "value2"}}
        ]
        assert result == expected

