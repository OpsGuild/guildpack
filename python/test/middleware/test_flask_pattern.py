#!/usr/bin/env python3
"""
Test Flask usage pattern with ErrorMiddleware
"""

# import pytest  # Not used in this test
from oguild import ErrorMiddleware


class TestFlaskPattern:
    """Test ErrorMiddleware with Flask framework"""

    def test_flask_error_handler_method(self):
        """Test Flask error handler method exists and works"""
        error_middleware = ErrorMiddleware()

        assert hasattr(error_middleware, "flask_error_handler")
        assert callable(error_middleware.flask_error_handler)

        # Test that it returns a tuple (content, status_code)
        try:
            raise ValueError("Test error")
        except Exception as exc:
            result = error_middleware.flask_error_handler(exc)
            assert isinstance(result, tuple)
            assert len(result) == 2
            content, status_code = result
            assert isinstance(content, dict)
            assert isinstance(status_code, int)

    def test_flask_error_handler_integration(self):
        """Test Flask error handler integration"""
        error_middleware = ErrorMiddleware()

        test_exceptions = [
            ValueError("Value error"),
            TypeError("Type error"),
            RuntimeError("Runtime error"),
            Exception("Generic error"),
        ]

        for exc in test_exceptions:
            content, status_code = error_middleware.flask_error_handler(exc)

            assert isinstance(content, dict)
            assert isinstance(status_code, int)
            assert "message" in content
            assert "status_code" in content
            assert "error" in content
            assert "error_id" in content["error"]
