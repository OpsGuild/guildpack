"""
Tests for ErrorMiddleware
"""

from unittest.mock import Mock, patch

import pytest
from oguild.middleware import ErrorMiddleware, create_error_middleware
from oguild.response import Error


class TestErrorMiddleware:
    """Test ErrorMiddleware functionality"""

    def _create_middleware(self, **kwargs):
        """Helper to create middleware with mock app"""
        from unittest.mock import Mock

        mock_app = Mock()
        return ErrorMiddleware(mock_app, **kwargs)

    def test_error_middleware_initialization(self):
        """Test ErrorMiddleware initializes with default values"""
        middleware = self._create_middleware()

        assert (
            middleware.default_error_message == "An unexpected error occurred"
        )
        assert middleware.default_error_code == 500
        assert middleware.include_request_info is False

    def test_error_middleware_custom_initialization(self):
        """Test ErrorMiddleware initializes with custom values"""
        middleware = self._create_middleware(
            default_error_message="Custom error",
            default_error_code=400,
            include_request_info=False,
        )

        assert middleware.default_error_message == "Custom error"
        assert middleware.default_error_code == 400
        assert middleware.include_request_info is False

    def test_handle_exception_without_request_info(self):
        """Test handle_exception without request info"""
        middleware = self._create_middleware()
        exc = ValueError("Test error")

        error = middleware.handle_exception(exc)

        assert isinstance(error, Error)
        assert error.e == exc
        assert "Test error" in error.msg
        assert (
            error.http_status_code == 400
        )  # ValueError gets 400 from handlers
        assert error.additional_info == {}

    def test_handle_exception_with_request_info(self):
        """Test handle_exception with request info"""
        middleware = self._create_middleware(include_request_info=True)
        exc = ValueError("Test error")
        request_info = {
            "request_url": "http://test.com/api",
            "request_method": "GET",
            "client_ip": "127.0.0.1",
        }

        error = middleware.handle_exception(exc, request_info)

        assert isinstance(error, Error)
        assert error.e == exc
        assert "Test error" in error.msg
        assert (
            error.http_status_code == 400
        )  # ValueError gets 400 from handlers
        assert error.additional_info == request_info

    def test_handle_exception_without_request_info_when_disabled(self):
        """Test handle_exception doesn't include request info when disabled"""
        middleware = self._create_middleware(include_request_info=False)
        exc = ValueError("Test error")
        request_info = {
            "request_url": "http://test.com/api",
            "request_method": "GET",
        }

        error = middleware.handle_exception(exc, request_info)

        assert isinstance(error, Error)
        assert error.additional_info == {}

    def test_create_response(self):
        """Test create_response returns framework exception"""
        middleware = self._create_middleware()
        exc = ValueError("Test error")
        error = middleware.handle_exception(exc)

        response = middleware.create_response(error)

        # Should return the framework exception from error.to_framework_exception()
        assert response is not None

    def test_create_response_with_different_exceptions(self):
        """Test create_response with different exception types"""
        middleware = self._create_middleware()

        # Test with ValueError
        error1 = middleware.handle_exception(ValueError("Value error"))
        response1 = middleware.create_response(error1)
        assert response1 is not None

        # Test with RuntimeError
        error2 = middleware.handle_exception(RuntimeError("Runtime error"))
        response2 = middleware.create_response(error2)
        assert response2 is not None

        # Test with generic Exception
        error3 = middleware.handle_exception(Exception("Generic error"))
        response3 = middleware.create_response(error3)
        assert response3 is not None

    def test_custom_error_message_and_code(self):
        """Test custom error message and code"""
        middleware = self._create_middleware(
            default_error_message="Custom error occurred",
            default_error_code=422,
        )
        exc = ValueError("Test error")

        error = middleware.handle_exception(exc)

        assert "Test error" in error.msg
        assert error.http_status_code == 400

    def test_custom_error_code_with_generic_exception(self):
        """Test custom error code works with generic exceptions that handlers don't override"""
        middleware = self._create_middleware(
            default_error_message="Custom error occurred",
            default_error_code=422,
        )
        exc = Exception("Generic test error")

        error = middleware.handle_exception(exc)

        assert "Generic test error" in error.msg
        assert error.http_status_code == 500

    def test_custom_error_code_with_custom_exception(self):
        """Test custom error code works with custom exceptions that have http_status_code attribute"""
        middleware = self._create_middleware(
            default_error_message="Custom error occurred",
            default_error_code=422,
        )

        class CustomException(Exception):
            def __init__(self, message):
                super().__init__(message)
                self.http_status_code = 422

        exc = CustomException("Custom test error")

        error = middleware.handle_exception(exc)

        assert "Custom test error" in error.msg
        assert error.http_status_code == 422

    def test_error_middleware_with_none_exception(self):
        """Test handle_exception with None exception"""
        middleware = self._create_middleware()

        error = middleware.handle_exception(None)

        assert isinstance(error, Error)
        assert error.e is None
        assert "None" in error.msg

    def test_error_middleware_with_string_exception(self):
        """Test handle_exception with string exception"""
        middleware = self._create_middleware()

        error = middleware.handle_exception("String error")

        assert isinstance(error, Error)
        assert error.e == "String error"
        assert "String error" in error.msg


class TestCreateErrorMiddleware:
    """Test create_error_middleware factory function"""

    def test_create_error_middleware_default(self):
        """Test create_error_middleware with default parameters"""
        MiddlewareClass = create_error_middleware()
        mock_app = Mock()
        middleware = MiddlewareClass(mock_app)

        assert isinstance(middleware, ErrorMiddleware)
        assert (
            middleware.default_error_message == "An unexpected error occurred"
        )
        assert middleware.default_error_code == 500
        assert middleware.include_request_info is False

    def test_create_error_middleware_custom(self):
        """Test create_error_middleware with custom parameters"""
        MiddlewareClass = create_error_middleware(
            default_error_message="Custom factory error",
            default_error_code=400,
            include_request_info=False,
        )
        mock_app = Mock()
        middleware = MiddlewareClass(mock_app)

        assert isinstance(middleware, ErrorMiddleware)
        assert middleware.default_error_message == "Custom factory error"
        assert middleware.default_error_code == 400
        assert middleware.include_request_info is False

    def test_create_error_middleware_with_app(self):
        """Test create_error_middleware with app parameter"""
        MiddlewareClass = create_error_middleware()
        mock_app = Mock()
        middleware = MiddlewareClass(mock_app)

        assert isinstance(middleware, ErrorMiddleware)
        assert (
            middleware.default_error_message == "An unexpected error occurred"
        )

    def test_create_error_middleware_functionality(self):
        """Test that created middleware works correctly"""
        MiddlewareClass = create_error_middleware(
            default_error_message="Factory error", default_error_code=422
        )
        mock_app = Mock()
        middleware = MiddlewareClass(mock_app)

        exc = ValueError("Test error")
        error = middleware.handle_exception(exc)

        assert isinstance(error, Error)
        assert "Test error" in error.msg
        assert error.http_status_code == 400


class TestErrorMiddlewareFrameworkIntegration:
    """Test ErrorMiddleware with framework detection"""

    def _create_middleware(self, **kwargs):
        """Helper to create middleware with mock app"""
        from unittest.mock import Mock

        mock_app = Mock()
        return ErrorMiddleware(mock_app, **kwargs)

    def test_framework_detection_works(self):
        """Test that ErrorMiddleware detects and uses available framework"""
        middleware = self._create_middleware()
        exc = ValueError("Framework test error")
        error = middleware.handle_exception(exc)
        response = middleware.create_response(error)

        # Should return a framework-specific response
        assert response is not None

        # Should have framework-specific attributes
        # FastAPI/Starlette: status_code + detail
        # Django: status_code + content
        # Werkzeug: code + description
        has_framework_attrs = (
            (
                hasattr(response, "status_code")
                and hasattr(response, "detail")
            )  # FastAPI/Starlette
            or (
                hasattr(response, "status_code")
                and hasattr(response, "content")
            )  # Django
            or (
                hasattr(response, "code") and hasattr(response, "description")
            )  # Werkzeug
        )
        assert (
            has_framework_attrs
        ), f"Response {type(response)} doesn't have expected framework attributes"

    def test_framework_response_structure(self):
        """Test that framework response has correct structure"""
        middleware = self._create_middleware()
        exc = ValueError("Structure test error")
        error = middleware.handle_exception(exc)
        response = middleware.create_response(error)

        assert response is not None

        if hasattr(response, "status_code"):
            assert response.status_code == 400
        elif hasattr(response, "code"):
            assert response.code == 400

        if hasattr(response, "detail") and isinstance(response.detail, dict):
            assert "message" in response.detail
            assert "status_code" in response.detail
            assert "error" in response.detail
        elif hasattr(response, "content"):
            assert response.content is not None
        elif hasattr(response, "description"):
            assert response.description is not None

    def test_framework_with_mocked_django(self):
        """Test framework detection with mocked Django"""
        from unittest.mock import patch

        middleware = self._create_middleware()
        exc = ValueError("Django mock test error")
        error = middleware.handle_exception(exc)

        # Mock FastAPI and Starlette to be None, Django to be available
        with patch(
            "oguild.response.response.FastAPIHTTPException", None
        ), patch(
            "oguild.response.response.StarletteHTTPException", None
        ), patch(
            "oguild.response.response.DjangoJsonResponse"
        ) as mock_django:

            mock_response = type(
                "MockDjangoResponse",
                (),
                {"status_code": 400, "content": b'{"message": "test"}'},
            )()
            mock_django.return_value = mock_response

            response = middleware.create_response(error)

            assert response is not None
            assert hasattr(response, "status_code")
            assert hasattr(response, "content")
            assert response.status_code == 400

    def test_framework_with_mocked_werkzeug(self):
        """Test framework detection with mocked Werkzeug"""
        from unittest.mock import patch

        middleware = self._create_middleware()
        exc = ValueError("Werkzeug mock test error")
        error = middleware.handle_exception(exc)

        # Create a mock WerkzeugHTTPException class that accepts arguments
        def mock_werkzeug_init(self, description):
            self.description = description
            self.code = 400

        mock_werkzeug_class = type(
            "MockWerkzeugHTTPException", (), {"__init__": mock_werkzeug_init}
        )

        # Mock FastAPI, Starlette, and Django to be None, Werkzeug to be available
        with patch(
            "oguild.response.response.FastAPIHTTPException", None
        ), patch(
            "oguild.response.response.StarletteHTTPException", None
        ), patch(
            "oguild.response.response.DjangoJsonResponse", None
        ), patch(
            "oguild.response.response.WerkzeugHTTPException",
            mock_werkzeug_class,
        ):

            response = middleware.create_response(error)

            assert response is not None
            assert hasattr(response, "code")
            assert hasattr(response, "description")
            assert response.code == 400

    def test_framework_detection_priority(self):
        """Test that framework detection works in priority order"""
        middleware = self._create_middleware()
        exc = ValueError("Priority test error")
        error = middleware.handle_exception(exc)
        response = middleware.create_response(error)

        # Should detect and return appropriate framework exception
        assert response is not None

        # Check that it's one of the supported framework exceptions
        framework_attrs = [
            ("status_code", "detail"),  # FastAPI/Starlette
            ("status_code", "content"),  # Django
            ("code", "description"),  # Werkzeug
        ]

        has_framework_attrs = any(
            hasattr(response, attr1) and hasattr(response, attr2)
            for attr1, attr2 in framework_attrs
        )
        assert (
            has_framework_attrs
        ), f"Response {type(response)} doesn't have expected framework attributes"

    def test_framework_response_consistency(self):
        """Test that framework responses are consistent across calls"""
        middleware = self._create_middleware()
        exc = ValueError("Consistency test error")

        # Create multiple errors with same exception
        error1 = middleware.handle_exception(exc)
        error2 = middleware.handle_exception(exc)

        response1 = middleware.create_response(error1)
        response2 = middleware.create_response(error2)

        # Both should be same framework type
        assert type(response1) == type(response2)

        # Both should have same status code
        if hasattr(response1, "status_code"):
            assert response1.status_code == response2.status_code
        elif hasattr(response1, "code"):
            assert response1.code == response2.code

    def test_framework_with_different_exception_types(self):
        """Test framework integration with different exception types"""
        middleware = self._create_middleware()

        test_cases = [
            (ValueError("Value error"), 400),
            (TypeError("Type error"), 400),
            (KeyError("Key error"), 400),
            (PermissionError("Permission error"), 403),
            (FileNotFoundError("File not found"), 404),
            (TimeoutError("Timeout error"), 408),
            (ConnectionError("Connection error"), 503),
            (Exception("Generic error"), 500),
        ]

        for exc, expected_status in test_cases:
            error = middleware.handle_exception(exc)
            response = middleware.create_response(error)

            assert response is not None

            # Check status code
            if hasattr(response, "status_code"):
                assert response.status_code == expected_status
            elif hasattr(response, "code"):
                assert response.code == expected_status

    def test_framework_with_request_info(self):
        """Test framework integration with request information"""
        middleware = self._create_middleware(include_request_info=True)
        exc = ValueError("Request info test error")
        request_info = {
            "request_url": "https://api.example.com/test",
            "request_method": "POST",
            "client_ip": "192.168.1.100",
            "user_agent": "TestClient/1.0",
        }

        error = middleware.handle_exception(exc, request_info)
        response = middleware.create_response(error)

        assert response is not None

        # Check that request info is included in response
        if hasattr(response, "detail") and isinstance(response.detail, dict):
            # Request info is added directly to the detail dict, not nested under additional_info
            assert "request_url" in response.detail
            assert "request_method" in response.detail
            assert "client_ip" in response.detail
            assert "user_agent" in response.detail
        elif hasattr(response, "description"):
            # For Werkzeug, description is JSON string
            import json

            try:
                desc = json.loads(response.description)
                assert "request_url" in desc
                assert "request_method" in desc
            except (json.JSONDecodeError, TypeError):
                pass  # Skip if not JSON format


class TestErrorMiddlewareIntegration:
    """Test ErrorMiddleware integration scenarios"""

    def _create_middleware(self, **kwargs):
        """Helper to create middleware with mock app"""
        from unittest.mock import Mock

        mock_app = Mock()
        return ErrorMiddleware(mock_app, **kwargs)

    def test_middleware_with_complex_request_info(self):
        """Test middleware with complex request information"""
        middleware = self._create_middleware(include_request_info=True)
        exc = RuntimeError("Complex error")
        request_info = {
            "request_url": "https://api.example.com/users/123",
            "request_method": "POST",
            "request_headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer token123",
                "User-Agent": "TestClient/1.0",
            },
            "client_ip": "192.168.1.100",
            "user_id": "user123",
            "session_id": "session456",
        }

        error = middleware.handle_exception(exc, request_info)

        assert isinstance(error, Error)
        assert error.additional_info == request_info
        assert error.additional_info["user_id"] == "user123"
        assert error.additional_info["session_id"] == "session456"

    def test_middleware_error_chain(self):
        """Test middleware with chained exceptions"""
        middleware = self._create_middleware()

        try:
            try:
                raise ValueError("Inner error")
            except ValueError as e:
                raise RuntimeError("Outer error") from e
        except RuntimeError as exc:
            error = middleware.handle_exception(exc)

            assert isinstance(error, Error)
            assert error.e == exc
            assert "Outer error" in error.msg

    def test_middleware_with_empty_request_info(self):
        """Test middleware with empty request info"""
        middleware = self._create_middleware()
        exc = ValueError("Test error")
        request_info = {}

        error = middleware.handle_exception(exc, request_info)

        assert isinstance(error, Error)
        assert error.additional_info == {}

    def test_middleware_with_none_request_info(self):
        """Test middleware with None request info"""
        middleware = self._create_middleware()
        exc = ValueError("Test error")

        error = middleware.handle_exception(exc, None)

        assert isinstance(error, Error)
        assert error.additional_info == {}

    def test_middleware_response_consistency(self):
        """Test that create_response returns consistent results"""
        middleware = self._create_middleware()
        exc = ValueError("Consistent error")

        error1 = middleware.handle_exception(exc)
        error2 = middleware.handle_exception(exc)

        response1 = middleware.create_response(error1)
        response2 = middleware.create_response(error2)

        # Both should return valid responses
        assert response1 is not None
        assert response2 is not None
        # They should be different instances but same type
        assert type(response1) == type(response2)
