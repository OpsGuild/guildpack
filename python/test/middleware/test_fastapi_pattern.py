#!/usr/bin/env python3
"""
Test FastAPI usage pattern with ErrorMiddleware
"""

import pytest
from oguild import ErrorMiddleware


class TestFastAPIPattern:
    """Test ErrorMiddleware with FastAPI framework"""

    def test_fastapi_pattern(self):
        """Test FastAPI usage pattern"""
        from fastapi import FastAPI

        app = FastAPI()
        app.add_middleware(ErrorMiddleware)

        assert len(app.user_middleware) == 1
        assert app.user_middleware[0].cls == ErrorMiddleware

    def test_fastapi_middleware_initialization_with_app(self):
        """Test ErrorMiddleware can be initialized with FastAPI app"""
        from fastapi import FastAPI

        app = FastAPI()
        middleware = ErrorMiddleware(app)

        assert middleware.app == app

    def test_fastapi_asgi_detection(self):
        """Test ASGI framework detection with FastAPI"""
        from fastapi import FastAPI

        app = FastAPI()
        middleware = ErrorMiddleware(app)
        # Check that it inherits from BaseHTTPMiddleware when app is provided
        assert hasattr(middleware, 'dispatch')
        assert callable(middleware.dispatch)

        middleware = ErrorMiddleware()
        # Check that it can be initialized without app
        assert middleware.app is None
