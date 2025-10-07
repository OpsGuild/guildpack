#!/usr/bin/env python3
"""
Test common ErrorMiddleware functionality across all frameworks
"""

# import pytest  # Not used in this test
from oguild import ErrorMiddleware, create_error_middleware


class TestMiddlewareCommon:
    """Test common ErrorMiddleware functionality"""

    def test_middleware_initialization_without_app(self):
        """Test ErrorMiddleware can be initialized without app"""
        middleware = ErrorMiddleware()
        assert middleware.app is None
        assert (
            middleware.default_error_message == "An unexpected error occurred"
        )
        assert middleware.default_error_code == 500
        assert middleware.include_request_info is False

    def test_middleware_custom_configuration(self):
        """Test ErrorMiddleware with custom configuration"""
        middleware = ErrorMiddleware(
            default_error_message="Custom error",
            default_error_code=400,
            include_request_info=False,
        )

        assert middleware.default_error_message == "Custom error"
        assert middleware.default_error_code == 400
        assert middleware.include_request_info is False

    def test_create_error_middleware_factory(self):
        """Test create_error_middleware factory function"""
        # Test default configuration
        MiddlewareClass = create_error_middleware()
        middleware = MiddlewareClass()

        assert isinstance(middleware, ErrorMiddleware)
        assert (
            middleware.default_error_message == "An unexpected error occurred"
        )

        # Test custom configuration
        MiddlewareClass = create_error_middleware(
            default_error_message="Factory error",
            default_error_code=400,
            include_request_info=False,
        )
        middleware = MiddlewareClass()

        assert middleware.default_error_message == "Factory error"
        assert middleware.default_error_code == 400
        assert middleware.include_request_info is False
