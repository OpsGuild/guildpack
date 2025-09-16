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
                "error": {"level": "ERROR", "detail": "Test error"},
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
                "error": {"level": "ERROR", "detail": None},
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
                "error": {"level": "ERROR", "detail": None},
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
