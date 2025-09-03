from datetime import date, datetime, time
from decimal import Decimal
from uuid import uuid4

import pytest
from oguild.utils import sanitize_fields
from pydantic import BaseModel


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
            "none_value": None,
        }
        result = await sanitize_fields(data)

        expected = {"name": "test"}
        assert result == expected

    @pytest.mark.asyncio
    async def test_sanitize_nested_dict(self):
        """Test sanitizing nested dictionaries."""
        data = {
            "user": {"name": "test", "profile": {"age": 25, "empty": None}},
            "empty": [],
        }
        result = await sanitize_fields(data)

        expected = {"user": {"name": "test", "profile": {"age": 25}}}
        assert result == expected

    @pytest.mark.asyncio
    async def test_sanitize_list(self):
        """Test sanitizing lists."""
        data = [
            {"name": "test1", "empty": None},
            {"name": "test2", "empty": []},
            {"name": "test3", "empty": {}},
        ]
        result = await sanitize_fields(data)

        expected = [{"name": "test1"}, {"name": "test2"}, {"name": "test3"}]
        assert result == expected

    @pytest.mark.asyncio
    async def test_sanitize_mixed_list(self):
        """Test sanitizing mixed content lists."""
        data = ["test", None, "", [], {}, {"name": "test"}]
        result = await sanitize_fields(data)

        expected = ["test", {"name": "test"}]
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
            (False, False),
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
                        "tags": ["tag1", "", "tag3"],
                    },
                    "empty": [],
                },
                {
                    "_id": uuid4(),
                    "name": "user2",
                    "profile": {"age": 30, "empty": {}, "tags": []},
                },
            ],
            "metadata": {
                "created_at": datetime(2023, 1, 1, 12, 0, 0),
                "price": Decimal("99.99"),
                "empty": None,
            },
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
