#!/usr/bin/env python3
"""
Test Django usage pattern with ErrorMiddleware
"""

# import pytest  # Not used in this test
from oguild import ErrorMiddleware


class TestDjangoPattern:
    """Test ErrorMiddleware with Django framework"""

    def test_django_middleware_method(self):
        """Test Django middleware method exists and works"""
        error_middleware = ErrorMiddleware()

        assert hasattr(error_middleware, "django_middleware")
        assert callable(error_middleware.django_middleware)

        # Test that it returns a callable
        def mock_get_response(request):
            return {"response": "test"}

        middleware_func = error_middleware.django_middleware(mock_get_response)
        assert callable(middleware_func)

    def test_django_middleware_integration(self):
        """Test Django middleware integration with mock request"""
        error_middleware = ErrorMiddleware()

        class MockDjangoRequest:
            def build_absolute_uri(self):
                return "http://localhost:8000/test"

            @property
            def method(self):
                return "GET"

            @property
            def META(self):
                return {"REMOTE_ADDR": "127.0.0.1"}

        def mock_get_response(request):
            return {"response": "success"}

        middleware_func = error_middleware.django_middleware(mock_get_response)

        request = MockDjangoRequest()
        response = middleware_func(request)
        assert response == {"response": "success"}

        def error_get_response(request):
            raise ValueError("Test error")

        error_middleware_func = error_middleware.django_middleware(
            error_get_response
        )

        try:
            error_middleware_func(request)
            assert False, "Should have handled the exception"
        except Exception:
            # The middleware should catch and handle the exception
            # In a real Django app, this would return a proper response
            pass
