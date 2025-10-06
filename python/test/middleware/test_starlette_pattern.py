#!/usr/bin/env python3
"""
Test Starlette usage pattern with ErrorMiddleware
"""

import pytest
from oguild import ErrorMiddleware


class TestStarlettePattern:
    """Test ErrorMiddleware with Starlette framework"""

    def test_starlette_pattern(self):
        """Test Starlette usage pattern"""
        from starlette.applications import Starlette
        from starlette.middleware import Middleware
        from starlette.responses import JSONResponse
        from starlette.routing import Route

        async def homepage(request):
            return JSONResponse({"message": "Hello World"})

        app = Starlette(
            routes=[Route("/", homepage)],
            middleware=[Middleware(ErrorMiddleware)],
        )

        # Verify middleware was added
        assert len(app.user_middleware) == 1
        assert app.user_middleware[0].cls == ErrorMiddleware
