import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

import asyncpg
import pydantic

from oguild.response import (
    CustomError, format_param, create_http_exception, catch_error,
    OK, Error
)


class TestCustomError:
    """Test cases for CustomError class."""

    def test_custom_error_default_values(self):
        """Test CustomError with default values."""
        error = CustomError()
        
        assert error.e is None
        assert error.msg == "Unknown server error."
        assert error.http_status_code == 500
        assert error.level == "ERROR"
        assert error.additional_info == {}

    def test_custom_error_with_values(self):
        """Test CustomError with custom values."""
        original_error = ValueError("Original error")
        error = CustomError(
            e=original_error,
            msg="Custom error message",
            code=400,
            level="WARNING",
            additional_info={"key": "value"}
        )
        
        assert error.e == original_error
        assert error.msg == "Custom error message"
        assert error.http_status_code == 400
        assert error.level == "WARNING"
        assert error.additional_info == {"key": "value"}

    def test_custom_error_string_representation(self):
        """Test CustomError string representation."""
        error = CustomError(msg="Test error")
        assert str(error) == "Test error"


class TestFormatParam:
    """Test cases for format_param function."""

    def test_format_param_string(self):
        """Test formatting string parameters."""
        result = format_param("test string")
        assert result == "'test string'"

    def test_format_param_string_with_newlines(self):
        """Test formatting string with newlines."""
        result = format_param("line1\nline2")
        assert result == "'line1\\nline2'"

    def test_format_param_long_string(self):
        """Test formatting long strings with truncation."""
        long_string = "a" * 400
        result = format_param(long_string)
        
        assert len(result) < len(long_string) + 10  # Account for quotes and truncation
        assert "...[truncated]" in result

    def test_format_param_short_string(self):
        """Test formatting short strings without truncation."""
        short_string = "short"
        result = format_param(short_string, max_len=10)
        assert result == "'short'"

    def test_format_param_non_string(self):
        """Test formatting non-string parameters."""
        test_cases = [
            (123, "123"),
            (123.45, "123.45"),
            (True, "True"),
            (False, "False"),
            (None, "None"),
            ([1, 2, 3], "[1, 2, 3]"),
            ({"key": "value"}, "{'key': 'value'}")
        ]
        
        for input_value, expected in test_cases:
            result = format_param(input_value)
            assert result == expected


class TestCreateHttpException:
    """Test cases for create_http_exception function."""

    def test_create_http_exception_generic(self):
        """Test creating generic HTTP exception."""
        exception = create_http_exception(404, "Not found")
        
        assert isinstance(exception, Exception)
        assert str(exception) == "HTTP 404: Not found"

    @patch('oguild.response.FastAPIHTTPException')
    def test_create_http_exception_fastapi(self, mock_fastapi_exception):
        """Test creating FastAPI HTTP exception."""
        mock_exception = MagicMock()
        mock_fastapi_exception.return_value = mock_exception
        
        exception = create_http_exception(404, "Not found", framework="fastapi")
        
        mock_fastapi_exception.assert_called_once_with(
            status_code=404, detail="Not found"
        )
        assert exception == mock_exception

    @patch('oguild.response.StarletteHTTPException')
    def test_create_http_exception_starlette(self, mock_starlette_exception):
        """Test creating Starlette HTTP exception."""
        mock_exception = MagicMock()
        mock_starlette_exception.return_value = mock_exception
        
        exception = create_http_exception(404, "Not found", framework="starlette")
        
        mock_starlette_exception.assert_called_once_with(
            status_code=404, detail="Not found"
        )
        assert exception == mock_exception

    @patch('oguild.response.DjangoHTTPExceptions')
    def test_create_http_exception_django(self, mock_django_exceptions):
        """Test creating Django HTTP exception."""
        mock_exception_class = MagicMock()
        mock_exception = MagicMock()
        mock_exception_class.return_value = mock_exception
        mock_django_exceptions.get.return_value = mock_exception_class
        
        exception = create_http_exception(404, "Not found", framework="django")
        
        mock_django_exceptions.get.assert_called_once_with(404)
        mock_exception_class.assert_called_once_with("Not found")
        assert exception == mock_exception

    @patch('oguild.response.WerkzeugHTTPException')
    def test_create_http_exception_flask(self, mock_werkzeug_exception):
        """Test creating Flask HTTP exception."""
        mock_exception = MagicMock()
        mock_werkzeug_exception.return_value = mock_exception
        
        exception = create_http_exception(404, "Not found", framework="flask")
        
        mock_werkzeug_exception.assert_called_once_with(
            description="Not found", code=404
        )
        assert exception == mock_exception


class TestCatchError:
    """Test cases for catch_error decorator."""

    @pytest.mark.asyncio
    async def test_catch_error_success(self):
        """Test catch_error decorator with successful function."""
        @catch_error
        async def test_func(x, y):
            return x + y
        
        result = await test_func(2, 3)
        assert result == 5

    @pytest.mark.asyncio
    async def test_catch_error_exception(self):
        """Test catch_error decorator with exception."""
        @catch_error
        async def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(CustomError) as exc_info:
            await test_func()
        
        error = exc_info.value
        assert error.msg == "Unexpected error in test_func"
        assert error.http_status_code == 500
        assert isinstance(error.e, ValueError)

    @pytest.mark.asyncio
    async def test_catch_error_with_args_kwargs(self):
        """Test catch_error decorator with arguments and keyword arguments."""
        @catch_error
        async def test_func(x, y, z=None):
            raise RuntimeError("Test error")
        
        with pytest.raises(CustomError) as exc_info:
            await test_func(1, 2, z=3)
        
        error = exc_info.value
        assert error.msg == "Unexpected error in test_func"
        assert error.http_status_code == 500


class TestOK:
    """Test cases for OK response class."""

    def test_ok_default_values(self):
        """Test OK class with default values."""
        response = OK()
        
        assert response.message == "Success"
        assert response.status_code == 200
        assert response.data == []
        assert response.meta == []

    def test_ok_custom_values(self):
        """Test OK class with custom values."""
        response = OK(
            message="Custom success",
            status_code=201,
            data={"id": 1},
            meta={"count": 1}
        )
        
        assert response.message == "Custom success"
        assert response.status_code == 201
        assert response.data == {"id": 1}
        assert response.meta == {"count": 1}

    @pytest.mark.asyncio
    async def test_ok_call_method(self):
        """Test OK __call__ method."""
        response = OK(
            message="Test",
            data={"name": "test"},
            meta={"count": 1}
        )
        
        result = await response()
        
        assert isinstance(result, dict)
        assert result["message"] == "Test"
        assert result["status_code"] == 200
        assert result["data"] == {"name": "test"}
        assert result["meta"] == {"count": 1}

    @pytest.mark.asyncio
    async def test_ok_await_method(self):
        """Test OK __await__ method."""
        response = OK(message="Test")
        
        result = await response
        
        assert isinstance(result, dict)
        assert result["message"] == "Test"

    @patch('oguild.response.FastAPIJSONResponse')
    @pytest.mark.asyncio
    async def test_ok_fastapi_response(self, mock_fastapi_response):
        """Test OK with FastAPI response."""
        mock_response = MagicMock()
        mock_fastapi_response.return_value = mock_response
        
        response = OK(message="Test")
        result = await response()
        
        mock_fastapi_response.assert_called_once()
        assert result == mock_response

    @patch('oguild.response.StarletteJSONResponse')
    @pytest.mark.asyncio
    async def test_ok_starlette_response(self, mock_starlette_response):
        """Test OK with Starlette response."""
        mock_response = MagicMock()
        mock_starlette_response.return_value = mock_response
        
        # Mock FastAPI not available
        with patch('oguild.response.FastAPIJSONResponse', None):
            response = OK(message="Test")
            result = await response()
            
            mock_starlette_response.assert_called_once()
            assert result == mock_response

    @patch('oguild.response.DjangoJsonResponse')
    @pytest.mark.asyncio
    async def test_ok_django_response(self, mock_django_response):
        """Test OK with Django response."""
        mock_response = MagicMock()
        mock_django_response.return_value = mock_response
        
        # Mock FastAPI and Starlette not available
        with patch('oguild.response.FastAPIJSONResponse', None), \
             patch('oguild.response.StarletteJSONResponse', None):
            response = OK(message="Test")
            result = await response()
            
            mock_django_response.assert_called_once()
            assert result == mock_response

    @patch('oguild.response.FlaskResponse')
    @pytest.mark.asyncio
    async def test_ok_flask_response(self, mock_flask_response):
        """Test OK with Flask response."""
        mock_response = MagicMock()
        mock_flask_response.return_value = mock_response
        
        # Mock other frameworks not available
        with patch('oguild.response.FastAPIJSONResponse', None), \
             patch('oguild.response.StarletteJSONResponse', None), \
             patch('oguild.response.DjangoJsonResponse', None):
            response = OK(message="Test")
            result = await response()
            
            mock_flask_response.assert_called_once()
            assert result == mock_response


class TestError:
    """Test cases for Error response class."""

    def test_error_default_values(self):
        """Test Error class with default values."""
        error = Error()
        
        assert error.e is None
        assert error.msg == "Unknown server error."
        assert error.http_status_code == 500
        assert error.level == "ERROR"
        assert error.additional_info == {}

    def test_error_with_exception(self):
        """Test Error class with exception."""
        original_error = ValueError("Original error")
        error = Error(
            e=original_error,
            msg="Custom error",
            code=400,
            level="WARNING",
            additional_info={"key": "value"}
        )
        
        assert error.e == original_error
        assert error.msg == "Custom error"
        assert error.http_status_code == 400
        assert error.level == "WARNING"
        assert error.additional_info == {"key": "value"}

    def test_error_with_custom_error(self):
        """Test Error class with CustomError."""
        original_error = ValueError("Original error")
        custom_error = CustomError(
            e=original_error,
            msg="Custom error message",
            code=404,
            level="INFO",
            additional_info={"custom": "info"}
        )
        
        error = Error(e=custom_error)
        
        assert error.e == original_error
        assert error.msg == "Custom error message"
        assert error.http_status_code == 404
        assert error.level == "INFO"
        assert error.additional_info == {"custom": "info"}

    def test_error_postgres_unique_violation(self):
        """Test Error with PostgreSQL unique violation."""
        mock_error = MagicMock()
        mock_error.constraint_name = "fk_user_email_unique"
        mock_error.__class__ = asyncpg.exceptions.UniqueViolationError
        
        error = Error(e=mock_error)
        
        assert error.http_status_code == 409
        assert "Email already exist" in error.msg

    def test_error_postgres_foreign_key_violation(self):
        """Test Error with PostgreSQL foreign key violation."""
        mock_error = MagicMock()
        mock_error.constraint_name = "fk_user_department_id"
        mock_error.__class__ = asyncpg.exceptions.ForeignKeyViolationError
        
        error = Error(e=mock_error)
        
        assert error.http_status_code == 400
        assert "Selected department does not exist" in error.msg

    def test_error_postgres_not_null_violation(self):
        """Test Error with PostgreSQL not null violation."""
        mock_error = MagicMock()
        mock_error.column_name = "user_name"
        mock_error.__class__ = asyncpg.exceptions.NotNullViolationError
        
        error = Error(e=mock_error)
        
        assert error.http_status_code == 400
        assert "User name is required" in error.msg

    def test_error_pydantic_validation(self):
        """Test Error with Pydantic validation error."""
        mock_error = MagicMock()
        mock_error.__class__ = pydantic.ValidationError
        
        error = Error(e=mock_error)
        
        assert error.http_status_code == 422
        assert error.msg == "Request validation failed."

    def test_error_value_error(self):
        """Test Error with ValueError."""
        original_error = ValueError("Invalid value")
        error = Error(e=original_error)
        
        assert error.http_status_code == 400
        assert error.msg == "Invalid value"

    def test_error_key_error(self):
        """Test Error with KeyError."""
        original_error = KeyError("missing_key")
        error = Error(e=original_error)
        
        assert error.http_status_code == 400
        assert "Missing key: missing_key" in error.msg

    def test_error_permission_error(self):
        """Test Error with PermissionError."""
        original_error = PermissionError("Access denied")
        error = Error(e=original_error)
        
        assert error.http_status_code == 403
        assert error.msg == "You do not have permission to perform this action."

    def test_error_file_not_found(self):
        """Test Error with FileNotFoundError."""
        original_error = FileNotFoundError("File not found")
        error = Error(e=original_error)
        
        assert error.http_status_code == 404
        assert error.msg == "Requested file was not found."

    def test_error_to_dict(self):
        """Test Error to_dict method."""
        original_error = ValueError("Test error")
        error = Error(
            e=original_error,
            msg="Custom error message",
            code=400,
            level="WARNING",
            additional_info={"extra": "info"}
        )
        
        with patch.object(error.logger, 'debug') as mock_debug:
            result = error.to_dict()
        
        expected = {
            "message": "Custom error message",
            "error": {
                "level": "WARNING",
                "error_message": "Test error",
                "status_code": 400,
            },
            "extra": "info"
        }
        
        assert result == expected
        mock_debug.assert_called()

    def test_error_to_dict_no_exception(self):
        """Test Error to_dict method without exception."""
        error = Error(msg="Test error")
        
        with patch.object(error.logger, 'error') as mock_error:
            result = error.to_dict()
        
        expected = {
            "message": "Test error",
            "error": {
                "level": "ERROR",
                "error_message": None,
                "status_code": 500,
            }
        }
        
        assert result == expected
        mock_error.assert_called_once_with("Test error")

    def test_error_get_attrs(self):
        """Test Error _get_attrs method."""
        mock_error = MagicMock()
        mock_error.attr1 = "value1"
        mock_error.attr2 = 123
        mock_error.attr3 = None
        mock_error._private = "private"
        
        error = Error(e=mock_error)
        attrs = error._get_attrs(mock_error)
        
        attrs_dict = json.loads(attrs)
        assert "attr1" in attrs_dict
        assert "attr2" in attrs_dict
        assert "attr3" not in attrs_dict  # None values are excluded
        assert "_private" not in attrs_dict  # Private attributes are excluded

    @patch('oguild.response.FastAPIHTTPException')
    def test_error_to_framework_exception_fastapi(self, mock_fastapi_exception):
        """Test Error to_framework_exception with FastAPI."""
        mock_exception = MagicMock()
        mock_fastapi_exception.return_value = mock_exception
        
        error = Error(msg="Test error", code=400)
        result = error.to_framework_exception(framework="fastapi")
        
        mock_fastapi_exception.assert_called_once_with(
            status_code=400, detail="Test error"
        )
        assert result == mock_exception

    @patch('oguild.response.StarletteHTTPException')
    def test_error_to_framework_exception_starlette(self, mock_starlette_exception):
        """Test Error to_framework_exception with Starlette."""
        mock_exception = MagicMock()
        mock_starlette_exception.return_value = mock_exception
        
        error = Error(msg="Test error", code=400)
        result = error.to_framework_exception(framework="starlette")
        
        mock_starlette_exception.assert_called_once_with(
            status_code=400, detail="Test error"
        )
        assert result == mock_exception

    @patch('oguild.response.DjangoHTTPExceptions')
    def test_error_to_framework_exception_django(self, mock_django_exceptions):
        """Test Error to_framework_exception with Django."""
        mock_exception_class = MagicMock()
        mock_exception = MagicMock()
        mock_exception_class.return_value = mock_exception
        mock_django_exceptions.get.return_value = mock_exception_class
        
        error = Error(msg="Test error", code=400)
        result = error.to_framework_exception(framework="django")
        
        mock_django_exceptions.get.assert_called_once_with(400)
        mock_exception_class.assert_called_once_with("Test error")
        assert result == mock_exception

    @patch('oguild.response.WerkzeugHTTPException')
    def test_error_to_framework_exception_flask(self, mock_werkzeug_exception):
        """Test Error to_framework_exception with Flask."""
        mock_exception = MagicMock()
        mock_werkzeug_exception.return_value = mock_exception
        
        error = Error(msg="Test error", code=400)
        result = error.to_framework_exception(framework="flask")
        
        mock_werkzeug_exception.assert_called_once_with(
            description="Test error", code=400
        )
        assert result == mock_exception

    def test_error_string_representation(self):
        """Test Error string representation."""
        error = Error(msg="Test error")
        assert str(error) == "Test error"

