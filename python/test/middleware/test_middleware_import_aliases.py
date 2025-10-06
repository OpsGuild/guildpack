#!/usr/bin/env python3
"""
Test middleware import aliases - both singular and plural forms
"""

import pytest
from oguild.middleware import ErrorMiddleware as SingularErrorMiddleware, create_error_middleware as singular_create_error_middleware
from oguild.middlewares import ErrorMiddleware as PluralErrorMiddleware, create_error_middleware as plural_create_error_middleware


class TestMiddlewareImportAliases:
    """Test that middleware can be imported using both singular and plural forms"""

    def test_singular_import_works(self):
        """Test importing from oguild.middleware"""
        assert SingularErrorMiddleware is not None
        assert singular_create_error_middleware is not None

    def test_plural_import_works(self):
        """Test importing from oguild.middlewares"""
        assert PluralErrorMiddleware is not None
        assert plural_create_error_middleware is not None

    def test_imports_are_identical(self):
        """Test that both import methods provide identical classes"""
        # Test that they're the same classes
        assert SingularErrorMiddleware is PluralErrorMiddleware
        assert singular_create_error_middleware is plural_create_error_middleware

    def test_functionality_identical(self):
        """Test that both import methods provide identical functionality"""
        # Test that they work identically
        middleware1 = SingularErrorMiddleware()
        middleware2 = PluralErrorMiddleware()
        
        assert middleware1.default_error_message == middleware2.default_error_message
        assert middleware1.default_error_code == middleware2.default_error_code
        assert middleware1.include_request_info == middleware2.include_request_info

    def test_factory_function_identical(self):
        """Test that factory functions work identically"""
        # Test factory functions
        SingularFactory = singular_create_error_middleware(
            default_error_message="Test message",
            default_error_code=400,
            include_request_info=True
        )
        
        PluralFactory = plural_create_error_middleware(
            default_error_message="Test message", 
            default_error_code=400,
            include_request_info=True
        )
        
        # Create instances
        singular_instance = SingularFactory()
        plural_instance = PluralFactory()
        
        # Test they have identical behavior
        assert singular_instance.default_error_message == plural_instance.default_error_message
        assert singular_instance.default_error_code == plural_instance.default_error_code
        assert singular_instance.include_request_info == plural_instance.include_request_info
