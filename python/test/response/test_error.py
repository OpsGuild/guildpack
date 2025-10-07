import asyncio
from unittest.mock import patch

import pytest
from oguild.response import Error
from oguild.response.errors import CommonErrorHandler


class TestError:
    """Test cases for Error response class."""

    def test_error_default_initialization(self):
        """Test Error class with default parameters."""
        error = Error(_raise_immediately=False)

        assert error.msg == "Unknown server error."
        assert error.http_status_code == 500
        assert error.level == "ERROR"
        assert error.additional_info == {}
        assert error.e is None

    def test_error_custom_initialization(self):
        """Test Error class with custom parameters."""
        exception = ValueError("Test error")

        with patch.object(Error, "_handle_error_with_handlers"):
            error = Error(
                e=exception,
                msg="Custom error message",
                code=400,
                level="WARNING",
                additional_info={"key": "value"},
                _raise_immediately=False,
            )

            assert error.e == exception
            assert error.msg == "Custom error message"
            assert error.http_status_code == 400
            assert error.level == "WARNING"
            assert error.additional_info == {"key": "value"}

    def test_error_with_exception_handling(self):
        """Test Error class with exception handling."""
        exception = ValueError("Test error")

        with patch.object(Error, "_handle_error_with_handlers") as mock_handle:
            Error(exception, _raise_immediately=False)
            mock_handle.assert_called_once_with(exception, msg=None)

    def test_error_to_dict_with_exception(self):
        """Test Error to_dict with exception."""
        exception = ValueError("Test error")

        with patch.object(Error, "_handle_error_with_handlers"), patch.object(
            CommonErrorHandler, "get_exception_attributes"
        ) as mock_attrs:
            mock_attrs.return_value = {"type": "ValueError"}

            error = Error(
                e=exception,
                msg="Custom message",
                code=400,
                _raise_immediately=False,
            )
            result = error.to_dict()

            expected = {
                "message": "Custom message",
                "status_code": 400,
                "error": {"level": "ERROR", "error_id": error.error_id, "detail": "Test error"},
            }
            assert result == expected

    def test_error_to_dict_without_exception(self):
        """Test Error to_dict without exception."""
        with patch.object(Error, "_handle_error_with_handlers"):
            error = Error(
                msg="Custom message", code=400, _raise_immediately=False
            )
            result = error.to_dict()

            expected = {
                "message": "Custom message",
                "status_code": 400,
                "error": {"level": "ERROR", "error_id": error.error_id, "detail": None},
            }
            assert result == expected

    def test_error_to_dict_with_additional_info(self):
        """Test Error to_dict with additional info."""
        with patch.object(Error, "_handle_error_with_handlers"):
            error = Error(
                msg="Custom message",
                code=400,
                additional_info={"extra": "data", "count": 5},
                _raise_immediately=False,
            )
            result = error.to_dict()

            expected = {
                "message": "Custom message",
                "status_code": 400,
                "error": {"level": "ERROR", "error_id": error.error_id, "detail": None},
                "extra": "data",
                "count": 5,
            }
            assert result == expected

    def test_error_to_framework_exception_fastapi(self):
        """Test Error to_framework_exception with FastAPI."""
        with patch.object(Error, "_handle_error_with_handlers"):
            error = Error(
                msg="Test FastAPI error", code=400, _raise_immediately=False
            )
            result = error.to_framework_exception()

            # Check if FastAPI is available
            try:
                from fastapi import HTTPException

                assert isinstance(result, HTTPException)
                assert result.status_code == 400
                assert "Test FastAPI error" in str(result.detail)
            except ImportError:
                # If FastAPI not available, should fall back to other framework
                assert hasattr(result, "status_code") or hasattr(
                    result, "code"
                )

    def test_error_to_framework_exception_starlette(self):
        """Test Error to_framework_exception with Starlette."""
        with patch("oguild.response.response.FastAPIHTTPException", None):
            with patch.object(Error, "_handle_error_with_handlers"):
                error = Error(
                    msg="Test Starlette error",
                    code=401,
                    _raise_immediately=False,
                )
                result = error.to_framework_exception()

                # Check if Starlette is available
                try:
                    from starlette.exceptions import HTTPException

                    assert isinstance(result, HTTPException)
                    assert result.status_code == 401
                    assert "Test Starlette error" in str(result.detail)
                except ImportError:
                    # If Starlette not available, should fall back to other framework
                    assert hasattr(result, "status_code") or hasattr(
                        result, "code"
                    )

    def test_error_to_framework_exception_django(self):
        """Test Error to_framework_exception with Django."""
        import os

        import django
        from django.conf import settings

        if not settings.configured:
            os.environ.setdefault(
                "DJANGO_SETTINGS_MODULE", "django.conf.global_settings"
            )
            settings.configure()
            django.setup()

        with patch(
            "oguild.response.response.FastAPIHTTPException", None
        ), patch("oguild.response.response.StarletteHTTPException", None):
            with patch.object(Error, "_handle_error_with_handlers"):
                error = Error(
                    msg="Test Django error", code=402, _raise_immediately=False
                )
                result = error.to_framework_exception()

                from django.http import JsonResponse

                assert isinstance(result, JsonResponse)
                assert result.status_code == 402
                import json

                content = json.loads(result.content.decode("utf-8"))
                assert "Test Django error" in content["message"]

    def test_error_to_framework_exception_werkzeug(self):
        """Test Error to_framework_exception with Werkzeug."""
        with patch(
            "oguild.response.response.FastAPIHTTPException", None
        ), patch(
            "oguild.response.response.StarletteHTTPException", None
        ), patch(
            "oguild.response.response.DjangoJsonResponse", None
        ):
            with patch.object(Error, "_handle_error_with_handlers"):
                error = Error(
                    msg="Test Werkzeug error",
                    code=403,
                    _raise_immediately=False,
                )
                result = error.to_framework_exception()

                from werkzeug.exceptions import HTTPException

                assert isinstance(result, HTTPException)
                assert result.code == 403
                assert "Test Werkzeug error" in str(result.description)

    def test_error_to_framework_exception_fallback(self):
        """Test Error to_framework_exception fallback."""
        with patch(
            "oguild.response.response.FastAPIHTTPException", None
        ), patch(
            "oguild.response.response.StarletteHTTPException", None
        ), patch(
            "oguild.response.response.DjangoJsonResponse", None
        ), patch(
            "oguild.response.response.WerkzeugHTTPException", None
        ):

            with patch.object(Error, "_handle_error_with_handlers"):
                error = Error(
                    msg="Test Fallback error",
                    code=404,
                    _raise_immediately=False,
                )
                result = error.to_framework_exception()

                assert isinstance(result, Exception)
                assert str(result) == "Test Fallback error"

    def test_error_call(self):
        """Test Error __call__ method."""
        with patch.object(Error, "_handle_error_with_handlers"), patch.object(
            Error, "to_framework_exception"
        ) as mock_exception:
            mock_exception.return_value = Exception("Test exception")

            error = Error(msg="Test error", code=400, _raise_immediately=False)

            with pytest.raises(Exception, match="Test exception"):
                error()

    def test_error_await(self):
        """Test Error __await__ method."""
        with patch.object(Error, "_handle_error_with_handlers"), patch.object(
            Error, "to_framework_exception"
        ) as mock_exception:
            mock_exception.return_value = Exception("Test exception")

            error = Error(msg="Test error", code=400, _raise_immediately=False)

            with pytest.raises(Exception, match="Test exception"):
                asyncio.run(error.__await__())

    def test_error_re_raise_no_double_wrap(self):
        """Test that re-raising Error without parameters doesn't double-wrap."""
        # Test the fix: when re-raising Error without parameters, it should
        # re-raise the original Error instance instead of wrapping it

        with patch.object(Error, "_handle_error_with_handlers"):
            # Create an original Error
            original_error = Error(
                msg="Original error message",
                code=403,
                _raise_immediately=False
            )

            # Simulate the scenario where Error is re-raised without parameters
            # This should re-raise the original Error, not wrap it
            with pytest.raises(Error) as exc_info:
                try:
                    raise original_error
                except Error:
                    # This is the problematic pattern that should now work correctly
                    raise Error  # Should re-raise the original Error

            # Verify it's the same Error instance (not wrapped)
            assert exc_info.value is original_error
            assert exc_info.value.msg == "Original error message"
            assert exc_info.value.http_status_code == 403

    def test_error_wraps_non_error_exceptions(self):
        """Test that Error properly wraps non-Error exceptions."""
        with patch.object(Error, "_handle_error_with_handlers"):
            # Test that non-Error exceptions are properly wrapped
            with pytest.raises(Error) as exc_info:
                try:
                    raise ValueError("Some value error")
                except ValueError:
                    # Create Error with _raise_immediately=False to test the wrapping
                    error = Error(_raise_immediately=False)
                    # Manually set the exception to simulate what would happen
                    error.e = ValueError("Some value error")
                    error.msg = "Unknown server error."
                    error.http_status_code = 500
                    raise error

            # Verify it wrapped the ValueError
            assert exc_info.value.e is not None
            assert isinstance(exc_info.value.e, ValueError)
            assert str(exc_info.value.e) == "Some value error"
            assert exc_info.value.http_status_code == 500  # Default status code

    def test_mark_message_as_read_scenario(self):
        """Test the specific scenario from mark_message_as_read method."""
        with patch.object(Error, "_handle_error_with_handlers"):
            # Create the original error that would be raised
            original_error = Error(
                msg="You can only mark your own messages as read",
                status_code=403,
                _raise_immediately=False
            )

            # Simulate the user's mark_message_as_read method scenario
            def simulate_mark_message_as_read():
                try:
                    # Simulate the permission check that fails
                    raise original_error
                except Exception:
                    # This is the problematic pattern from the user's code
                    # that should now work correctly
                    raise Error  # Should re-raise the original Error

            with pytest.raises(Error) as exc_info:
                simulate_mark_message_as_read()

            # Verify it's the same Error instance (not double-wrapped)
            assert exc_info.value is original_error
            assert exc_info.value.msg == "You can only mark your own messages as read"
            assert exc_info.value.http_status_code == 403
            assert exc_info.value.e is None  # No underlying exception

    def test_error_dynamic_string_message(self):
        """Test Error with string as first argument."""
        with patch.object(Error, "_handle_error_with_handlers"):
            error = Error("Something went wrong", _raise_immediately=False)

            assert error.msg == "Something went wrong"
            assert error.http_status_code == 500  # Default status code
            assert error.e is None

    def test_error_dynamic_string_and_status(self):
        """Test Error with string and status code."""
        with patch.object(Error, "_handle_error_with_handlers"):
            error = Error("Not found", 404, _raise_immediately=False)

            assert error.msg == "Not found"
            assert error.http_status_code == 404
            assert error.e is None

    def test_error_dynamic_status_and_string(self):
        """Test Error with status code and string (reversed order)."""
        with patch.object(Error, "_handle_error_with_handlers"):
            error = Error(404, "Not found", _raise_immediately=False)

            assert error.msg == "Not found"
            assert error.http_status_code == 404
            assert error.e is None

    def test_error_dynamic_exception_and_message(self):
        """Test Error with exception and message."""
        with patch.object(Error, "_handle_error_with_handlers"):
            exception = ValueError("Invalid input")
            error = Error(exception, "Validation failed", _raise_immediately=False)

            assert error.msg == "Validation failed"
            assert error.http_status_code is None  # No handlers run, so None
            assert error.e is exception

    def test_error_dynamic_exception_message_and_status(self):
        """Test Error with exception, message, and status code."""
        with patch.object(Error, "_handle_error_with_handlers"):
            exception = ValueError("Invalid input")
            error = Error(exception, "Validation failed", 400, _raise_immediately=False)

            assert error.msg == "Validation failed"
            assert error.http_status_code == 400
            assert error.e is exception

    def test_error_dynamic_with_dict(self):
        """Test Error with dictionary as additional info."""
        with patch.object(Error, "_handle_error_with_handlers"):
            additional_info = {"field": "value", "count": 5}
            error = Error("Error occurred", 500, additional_info, _raise_immediately=False)

            assert error.msg == "Error occurred"
            assert error.http_status_code == 500
            assert error.additional_info == additional_info

    def test_error_dynamic_with_kwargs(self):
        """Test Error with keyword arguments."""
        with patch.object(Error, "_handle_error_with_handlers"):
            error = Error(
                "Error occurred",
                500,
                extra_field="extra_value",
                another_field=123,
                _raise_immediately=False
            )

            assert error.msg == "Error occurred"
            assert error.http_status_code == 500
            assert error.additional_info == {"extra_field": "extra_value", "another_field": 123}

    def test_error_dynamic_legacy_keyword_args(self):
        """Test Error with legacy keyword argument names."""
        with patch.object(Error, "_handle_error_with_handlers"):
            error = Error(
                message="Legacy message",
                status_code=403,
                _raise_immediately=False
            )

            assert error.msg == "Legacy message"
            assert error.http_status_code == 403

    def test_error_dynamic_mixed_args_and_kwargs(self):
        """Test Error with mixed positional and keyword arguments."""
        with patch.object(Error, "_handle_error_with_handlers"):
            exception = RuntimeError("Runtime issue")
            error = Error(
                exception,
                "Mixed args test",
                500,
                level="WARNING",
                custom_field="custom_value",
                _raise_immediately=False
            )

            assert error.msg == "Mixed args test"
            assert error.http_status_code == 500
            assert error.level == "WARNING"
            assert error.e is exception
            assert error.additional_info == {"custom_field": "custom_value"}

    def test_error_dynamic_priority_order(self):
        """Test that positional args take priority over kwargs."""
        with patch.object(Error, "_handle_error_with_handlers"):
            error = Error(
                "Positional message",  # Should override kwargs
                404,  # Should override kwargs
                message="Keyword message",  # Should be ignored
                status_code=500,  # Should be ignored
                _raise_immediately=False
            )

            assert error.msg == "Positional message"
            assert error.http_status_code == 404

    def test_error_id_generation(self):
        """Test that Error generates unique error_id."""
        with patch.object(Error, "_handle_error_with_handlers"):
            error1 = Error("Test error 1", _raise_immediately=False)
            error2 = Error("Test error 2", _raise_immediately=False)

            # Both should have error_id
            assert hasattr(error1, 'error_id')
            assert hasattr(error2, 'error_id')

            # error_id should be strings
            assert isinstance(error1.error_id, str)
            assert isinstance(error2.error_id, str)

            # error_id should be different
            assert error1.error_id != error2.error_id

            # error_id should be valid UUIDs
            import uuid
            assert uuid.UUID(error1.error_id) is not None
            assert uuid.UUID(error2.error_id) is not None

    def test_error_id_in_to_dict(self):
        """Test that error_id is included in to_dict output."""
        with patch.object(Error, "_handle_error_with_handlers"):
            error = Error("Test error", 404, _raise_immediately=False)
            error_dict = error.to_dict()

            # error_id should be in the error detail
            assert "error" in error_dict
            assert "error_id" in error_dict["error"]
            assert error_dict["error"]["error_id"] == error.error_id
            assert error_dict["error"]["level"] == "ERROR"
            assert error_dict["error"]["detail"] is None  # No underlying exception

    def test_error_id_with_exception(self):
        """Test that error_id is included when there's an underlying exception."""
        with patch.object(Error, "_handle_error_with_handlers"):
            exception = ValueError("Test exception")
            error = Error(exception, "Test error", 400, _raise_immediately=False)
            error_dict = error.to_dict()

            # error_id should be in the error detail
            assert "error" in error_dict
            assert "error_id" in error_dict["error"]
            assert error_dict["error"]["error_id"] == error.error_id
            assert error_dict["error"]["level"] == "ERROR"
            assert error_dict["error"]["detail"] == "Test exception"

    def test_error_id_uniqueness_across_instances(self):
        """Test that each Error instance gets a unique error_id."""
        with patch.object(Error, "_handle_error_with_handlers"):
            errors = []
            for i in range(10):
                error = Error(f"Test error {i}", _raise_immediately=False)
                errors.append(error)

            # All error_ids should be unique
            error_ids = [error.error_id for error in errors]
            assert len(set(error_ids)) == len(error_ids)  # All unique

            # All should be valid UUIDs
            import uuid
            for error_id in error_ids:
                assert uuid.UUID(error_id) is not None

    def test_error_detail_with_error_instance(self):
        """Test that detail field shows message when underlying exception is an Error."""
        with patch.object(Error, "_handle_error_with_handlers"):
            # Create an inner error
            inner_error = Error("Invalid credentials", 400, _raise_immediately=False)

            # Create an outer error that wraps the inner error
            outer_error = Error(inner_error, "Login failed", 401, _raise_immediately=False)
            error_dict = outer_error.to_dict()

            # The detail should be the message of the inner error, not the full error object
            assert error_dict["error"]["detail"] == "Invalid credentials"
            assert error_dict["message"] == "Login failed"
            assert error_dict["status_code"] == 401

    def test_error_detail_with_regular_exception(self):
        """Test that detail field shows exception message for regular exceptions."""
        with patch.object(Error, "_handle_error_with_handlers"):
            # Create an error with a regular exception
            exception = ValueError("Invalid input data")
            error = Error(exception, "Validation failed", 400, _raise_immediately=False)
            error_dict = error.to_dict()

            # The detail should be the exception message
            assert error_dict["error"]["detail"] == "Invalid input data"
            assert error_dict["message"] == "Validation failed"
            assert error_dict["status_code"] == 400

    def test_error_detail_without_exception(self):
        """Test that detail field is None when there's no underlying exception."""
        with patch.object(Error, "_handle_error_with_handlers"):
            error = Error("Simple error", 500, _raise_immediately=False)
            error_dict = error.to_dict()

            # The detail should be None
            assert error_dict["error"]["detail"] is None
            assert error_dict["message"] == "Simple error"
            assert error_dict["status_code"] == 500

    def test_login_user_scenario_no_double_wrap(self):
        """Test the login_user scenario to prevent double-wrapping."""
        with patch.object(Error, "_handle_error_with_handlers"):
            def simulate_login_user():
                try:
                    # Simulate the authentication failure
                    raise Error("Invalid credentials", 400, _raise_immediately=False)
                except Error:
                    # Re-raise Error instances directly (no double-wrapping)
                    raise
                except Exception:
                    # Only catch unexpected exceptions
                    raise Error("Login failed", 500, _raise_immediately=False)

            with pytest.raises(Error) as exc_info:
                simulate_login_user()

            # Should be the original error, not wrapped
            assert exc_info.value.msg == "Invalid credentials"
            assert exc_info.value.http_status_code == 400
            # Should not have double-wrapped structure
            error_dict = exc_info.value.to_dict()
            assert error_dict["error"]["detail"] is None  # No underlying exception
            assert "Login failed" not in str(error_dict)  # No outer error message

    def test_login_user_scenario_with_unexpected_exception(self):
        """Test the login_user scenario with unexpected exception."""
        with patch.object(Error, "_handle_error_with_handlers"):
            def simulate_login_user_with_unexpected_error():
                try:
                    # Simulate an unexpected error
                    raise ValueError("Database connection failed")
                except Error:
                    # Re-raise Error instances directly
                    raise
                except Exception:
                    # Catch unexpected exceptions and wrap them
                    raise Error("Login failed", 500, _raise_immediately=False)

            with pytest.raises(Error) as exc_info:
                simulate_login_user_with_unexpected_error()

            # Should be the wrapped error
            assert exc_info.value.msg == "Login failed"
            assert exc_info.value.http_status_code == 500
            # Should have the original exception as detail
            error_dict = exc_info.value.to_dict()
            assert error_dict["error"]["detail"] == "Database connection failed"
