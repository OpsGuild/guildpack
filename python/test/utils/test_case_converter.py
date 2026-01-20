"""Tests for case converter utilities."""

import pytest
from datetime import date
from decimal import Decimal
from uuid import UUID

from oguild.utils import (
    Case,
    camel_to_snake,
    snake_to_camel,
    snake_to_pascal,
    snake_to_kebab,
    snake_to_screaming_snake,
    snake_to_dot,
    snake_to_title,
    kebab_to_snake,
    pascal_to_snake,
    dot_to_snake,
    screaming_snake_to_snake,
    to_snake,
    convert_case,
    convert_dict_keys,
    convert_dict_keys_to_snake_case,
    convert_dict_keys_to_camel_case,
    convert_value,
    filter_null_fields,
    serialize_response,
    serialize_request,
    to_pascal_case,
    to_kebab_case,
    to_screaming_snake_case,
)


class TestIndividualConverters:
    """Tests for individual case conversion functions."""

    def test_camel_to_snake(self):
        assert camel_to_snake("camelCase") == "camel_case"
        assert camel_to_snake("PascalCase") == "pascal_case"
        assert camel_to_snake("getHTTPResponse") == "get_http_response"
        assert camel_to_snake("simple") == "simple"
        assert camel_to_snake("") == ""

    def test_snake_to_camel(self):
        assert snake_to_camel("snake_case") == "snakeCase"
        assert snake_to_camel("get_http_response") == "getHttpResponse"
        assert snake_to_camel("simple") == "simple"
        assert snake_to_camel("") == ""

    def test_snake_to_pascal(self):
        assert snake_to_pascal("snake_case") == "SnakeCase"
        assert snake_to_pascal("get_http_response") == "GetHttpResponse"
        assert snake_to_pascal("simple") == "Simple"

    def test_snake_to_kebab(self):
        assert snake_to_kebab("snake_case") == "snake-case"
        assert snake_to_kebab("simple") == "simple"

    def test_snake_to_screaming_snake(self):
        assert snake_to_screaming_snake("snake_case") == "SNAKE_CASE"
        assert snake_to_screaming_snake("simple") == "SIMPLE"

    def test_snake_to_dot(self):
        assert snake_to_dot("snake_case") == "snake.case"
        assert snake_to_dot("simple") == "simple"

    def test_snake_to_title(self):
        assert snake_to_title("snake_case") == "Snake Case"
        assert snake_to_title("get_http_response") == "Get Http Response"

    def test_kebab_to_snake(self):
        assert kebab_to_snake("kebab-case") == "kebab_case"

    def test_pascal_to_snake(self):
        assert pascal_to_snake("PascalCase") == "pascal_case"

    def test_dot_to_snake(self):
        assert dot_to_snake("dot.case") == "dot_case"

    def test_screaming_snake_to_snake(self):
        assert screaming_snake_to_snake("SCREAMING_SNAKE") == "screaming_snake"


class TestToSnake:
    """Tests for the universal to_snake converter."""

    def test_from_camel(self):
        assert to_snake("camelCase") == "camel_case"

    def test_from_pascal(self):
        assert to_snake("PascalCase") == "pascal_case"

    def test_from_kebab(self):
        assert to_snake("kebab-case") == "kebab_case"

    def test_from_dot(self):
        assert to_snake("dot.case") == "dot_case"

    def test_from_screaming(self):
        assert to_snake("SCREAMING_SNAKE") == "screaming_snake"

    def test_already_snake(self):
        assert to_snake("snake_case") == "snake_case"


class TestConvertCase:
    """Tests for the generic convert_case function."""

    def test_to_camel(self):
        assert convert_case("snake_case", Case.CAMEL) == "snakeCase"
        assert convert_case("PascalCase", Case.CAMEL) == "pascalCase"

    def test_to_pascal(self):
        assert convert_case("snake_case", Case.PASCAL) == "SnakeCase"
        assert convert_case("camelCase", Case.PASCAL) == "CamelCase"

    def test_to_kebab(self):
        assert convert_case("snake_case", Case.KEBAB) == "snake-case"
        assert convert_case("camelCase", Case.KEBAB) == "camel-case"

    def test_to_screaming_snake(self):
        assert convert_case("snake_case", Case.SCREAMING_SNAKE) == "SNAKE_CASE"

    def test_to_dot(self):
        assert convert_case("snake_case", Case.DOT) == "snake.case"

    def test_to_title(self):
        assert convert_case("snake_case", Case.TITLE) == "Snake Case"

    def test_to_snake(self):
        assert convert_case("camelCase", Case.SNAKE) == "camel_case"


class TestConvertDictKeys:
    """Tests for dictionary key conversion."""

    def test_convert_keys_to_camel(self):
        data = {"user_name": "John", "email_address": "john@example.com"}
        result = convert_dict_keys(data, Case.CAMEL)
        assert result == {
            "userName": "John", "emailAddress": "john@example.com"
        }

    def test_convert_keys_to_snake(self):
        data = {"userName": "John", "emailAddress": "john@example.com"}
        result = convert_dict_keys(data, Case.SNAKE)
        assert result == {
            "user_name": "John", "email_address": "john@example.com"
        }

    def test_convert_nested_dict(self):
        data = {"user_info": {"first_name": "John", "last_name": "Doe"}}
        result = convert_dict_keys(data, Case.CAMEL)
        assert result == {"userInfo": {"firstName": "John", "lastName": "Doe"}}

    def test_convert_with_list(self):
        data = {"users": [{"user_name": "John"}, {"user_name": "Jane"}]}
        result = convert_dict_keys(data, Case.CAMEL)
        assert result == {
            "users": [{"userName": "John"}, {"userName": "Jane"}]
        }

    def test_convert_dict_keys_to_snake_case(self):
        data = {"userName": "John"}
        result = convert_dict_keys_to_snake_case(data)
        assert result == {"user_name": "John"}

    def test_convert_dict_keys_to_camel_case(self):
        data = {"user_name": "John"}
        result = convert_dict_keys_to_camel_case(data)
        assert result == {"userName": "John"}


class TestConvertValue:
    """Tests for value conversion."""

    def test_convert_uuid(self):
        uid = UUID("12345678-1234-5678-1234-567812345678")
        assert convert_value(uid) == "12345678-1234-5678-1234-567812345678"

    def test_convert_date(self):
        d = date(2024, 1, 15)
        assert convert_value(d) == "2024-01-15"

    def test_convert_decimal(self):
        d = Decimal("10.50")
        assert convert_value(d) == 10.50

    def test_convert_primitives(self):
        assert convert_value(42) == 42
        assert convert_value(3.14) == 3.14
        assert convert_value(True) is True
        assert convert_value("hello") == "hello"

    def test_convert_bytes(self):
        assert convert_value(b"hello") == "hello"

    def test_convert_none(self):
        assert convert_value(None) is None


class TestFilterNullFields:
    """Tests for null field filtering."""

    def test_filter_none_values(self):
        data = {"name": "John", "age": None, "email": "john@example.com"}
        result = filter_null_fields(data)
        assert result == {"name": "John", "email": "john@example.com"}

    def test_filter_nested(self):
        data = {"user": {"name": "John", "nickname": None}}
        result = filter_null_fields(data)
        assert result == {"user": {"name": "John"}}

    def test_filter_list(self):
        data = [{"name": "John", "age": None}, None, {"name": "Jane"}]
        result = filter_null_fields(data)
        assert result == [{"name": "John"}, {"name": "Jane"}]


class TestSerializeResponse:
    """Tests for response serialization."""

    def test_serialize_to_camel(self):
        data = {"user_name": "John", "email_address": "john@example.com"}
        result = serialize_response(data, Case.CAMEL)
        assert result == {
            "userName": "John", "emailAddress": "john@example.com"
        }

    def test_serialize_to_kebab(self):
        data = {"user_name": "John"}
        result = serialize_response(data, Case.KEBAB)
        assert result == {"user-name": "John"}

    def test_serialize_default_uses_camel(self):
        """Test that default (None) uses camelCase conversion."""
        data = {"user_name": "John"}
        result = serialize_response(data, None)
        assert result == {"userName": "John"}

    def test_serialize_filters_nulls(self):
        data = {"user_name": "John", "age": None}
        result = serialize_response(data, Case.CAMEL)
        assert result == {"userName": "John"}

    def test_serialize_list(self):
        data = [{"user_name": "John"}, {"user_name": "Jane"}]
        result = serialize_response(data, Case.CAMEL)
        assert result == [{"userName": "John"}, {"userName": "Jane"}]

    def test_serialize_default_is_camel(self):
        data = {"user_name": "John"}
        result = serialize_response(data)
        assert result == {"userName": "John"}


class TestSerializeRequest:
    """Tests for request serialization."""

    def test_serialize_to_snake(self):
        data = {"userName": "John", "emailAddress": "john@example.com"}
        result = serialize_request(data, Case.SNAKE)
        assert result == {
            "user_name": "John", "email_address": "john@example.com"
        }

    def test_serialize_none_returns_empty_dict(self):
        result = serialize_request(None, Case.SNAKE)
        assert result == {}

    def test_serialize_default_uses_snake(self):
        """Test that default (None) uses snake_case conversion."""
        data = {"userName": "John"}
        result = serialize_request(data, None)
        assert result == {"user_name": "John"}

    def test_serialize_list(self):
        data = [{"userName": "John"}, {"userName": "Jane"}]
        result = serialize_request(data, Case.SNAKE)
        assert result == [{"user_name": "John"}, {"user_name": "Jane"}]

    def test_serialize_default_is_snake(self):
        data = {"userName": "John"}
        result = serialize_request(data)
        assert result == {"user_name": "John"}


class TestConvenienceAliases:
    """Tests for convenience alias functions."""

    def test_to_pascal_case(self):
        assert to_pascal_case("snake_case") == "SnakeCase"
        assert to_pascal_case("camelCase") == "CamelCase"

    def test_to_kebab_case(self):
        assert to_kebab_case("snake_case") == "snake-case"
        assert to_kebab_case("camelCase") == "camel-case"

    def test_to_screaming_snake_case(self):
        assert to_screaming_snake_case("snake_case") == "SNAKE_CASE"
        assert to_screaming_snake_case("camelCase") == "CAMEL_CASE"


class TestStringBasedCaseSelection:
    """Tests for using strings instead of Case enum."""

    def test_convert_case_with_string(self):
        assert convert_case("camelCase", "snake") == "camel_case"
        assert convert_case("snake_case", "camel") == "snakeCase"
        assert convert_case("any_format", "pascal") == "AnyFormat"
        assert convert_case("hello_world", "kebab") == "hello-world"
        assert convert_case("user_name", "screaming_snake") == "USER_NAME"
        assert convert_case("user_name", "SCREAMING_SNAKE") == "USER_NAME"

    def test_convert_dict_keys_with_string(self):
        data = {"firstName": "John"}
        assert convert_dict_keys(data, "snake") == {"first_name": "John"}
        assert convert_dict_keys(data, "screaming_snake") == {
            "FIRST_NAME": "John"
        }

    def test_serialize_response_with_string(self):
        data = {"user_name": "John"}
        assert serialize_response(data, "camel") == {"userName": "John"}
        assert serialize_response(data, "kebab") == {"user-name": "John"}

    def test_serialize_request_with_string(self):
        data = {"userName": "John"}
        assert serialize_request(data, "snake") == {"user_name": "John"}

    def test_invalid_case_string(self):
        with pytest.raises(ValueError, match="Invalid case 'invalid_case'"):
            convert_case("test", "invalid_case")
