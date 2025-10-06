"""
Framework-agnostic error middleware that works with all supported frameworks.
"""

from typing import Any, Dict, Optional, Union

from oguild.response import Error

try:
    from fastapi import Request
    from fastapi.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    BaseHTTPMiddleware = object
    Request = Any
    JSONResponse = Any

try:
    from django.http import HttpRequest
    from django.http import JsonResponse as DjangoJsonResponse

    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False
    HttpRequest = Any
    DjangoJsonResponse = Any

try:
    from flask import Request as FlaskRequest

    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    FlaskRequest = Any


class ErrorMiddleware(BaseHTTPMiddleware if FASTAPI_AVAILABLE else object):
    """
    Universal error middleware that works with all frameworks.
    Automatically detects the framework and adapts accordingly.
    """

    def __init__(
        self,
        app=None,
        default_error_message: str = "An unexpected error occurred",
        default_error_code: int = 500,
        include_request_info: bool = False,
    ):
        if FASTAPI_AVAILABLE and app is not None:
            super().__init__(app)

        self.app = app
        self.default_error_message = default_error_message
        self.default_error_code = default_error_code
        self.include_request_info = include_request_info

    async def dispatch(self, request, call_next):
        """FastAPI/Starlette middleware dispatch method"""
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            return await self._handle_asgi_exception(exc, request)

    async def _handle_asgi_exception(self, exc, request):
        """Handle exception in ASGI context"""
        request_info = {}
        if self.include_request_info:
            request_info = {
                "request_url": str(request.url),
                "request_method": request.method,
                "request_headers": dict(request.headers),
                "client_ip": request.client.host if request.client else None,
            }

        if isinstance(exc, Error):
            error = exc
        else:
            error = Error(
                e=exc,
                msg=self.default_error_message,
                code=self.default_error_code,
                additional_info=request_info,
                _raise_immediately=False,
            )

        framework_exc = error.to_framework_exception()

        if hasattr(framework_exc, "status_code") and hasattr(
            framework_exc, "detail"
        ):
            if isinstance(framework_exc.detail, dict):
                return JSONResponse(
                    content=framework_exc.detail,
                    status_code=framework_exc.status_code,
                )
            else:
                return JSONResponse(
                    content={"message": str(framework_exc.detail)},
                    status_code=framework_exc.status_code,
                )
        else:
            error_dict = error.to_dict()
            return JSONResponse(
                content=error_dict,
                status_code=error_dict.get("status_code", 500),
            )

    def django_middleware(self, get_response):
        """Django middleware integration"""

        def middleware(request):
            try:
                response = get_response(request)
                return response
            except Exception as exc:
                request_info = {}
                if self.include_request_info:
                    request_info = {
                        "request_url": request.build_absolute_uri(),
                        "request_method": request.method,
                        "request_headers": dict(request.META),
                        "client_ip": request.META.get("REMOTE_ADDR"),
                    }

                error = Error(
                    e=exc,
                    msg=str(exc),
                    code=self.default_error_code,
                    additional_info=request_info,
                    _raise_immediately=False,
                )

                framework_exc = error.to_framework_exception()

                if DJANGO_AVAILABLE:
                    return DjangoJsonResponse(
                        data=(
                            framework_exc.detail
                            if hasattr(framework_exc, "detail")
                            else error.to_dict()
                        ),
                        status=(
                            framework_exc.status_code
                            if hasattr(framework_exc, "status_code")
                            else 500
                        ),
                    )
                else:
                    return {"error": error.to_dict()}

        return middleware

    def flask_error_handler(self, exc):
        """Flask error handler integration"""
        request_info = {}
        if self.include_request_info:
            try:
                from flask import request

                if hasattr(request, "url"):
                    request_info = {
                        "request_url": request.url,
                        "request_method": request.method,
                        "request_headers": dict(request.headers),
                        "client_ip": request.remote_addr,
                    }
            except (ImportError, RuntimeError):
                pass

        if isinstance(exc, Error):
            error = exc
        else:
            error = Error(
                e=exc,
                msg=self.default_error_message,
                code=self.default_error_code,
                additional_info=request_info,
                _raise_immediately=False,
            )

        framework_exc = error.to_framework_exception()

        content = (
            framework_exc.detail
            if hasattr(framework_exc, "detail")
            else error.to_dict()
        )
        status_code = (
            framework_exc.status_code
            if hasattr(framework_exc, "status_code")
            else 500
        )
        return content, status_code

    def handle_exception(
        self, exc: Exception, request_info: Optional[Dict[str, Any]] = None
    ) -> Error:
        """Handle an exception and return an Error instance."""
        additional_info = {}

        if self.include_request_info and request_info:
            additional_info.update(request_info)

        error = Error(
            e=exc,
            msg=str(exc),
            code=self.default_error_code,
            additional_info=additional_info,
            _raise_immediately=False,
        )

        return error

    def create_response(self, error: Error) -> Any:
        """Convert an Error instance to a framework-specific response."""
        return error.to_framework_exception()


def create_error_middleware(
    default_error_message: str = "An unexpected error occurred",
    default_error_code: int = 500,
    include_request_info: bool = False,
):
    """Factory function to create an ErrorMiddleware with custom configuration."""

    class ConfiguredErrorMiddleware(ErrorMiddleware):
        def __init__(self, app=None):
            super().__init__(
                app,
                default_error_message=default_error_message,
                default_error_code=default_error_code,
                include_request_info=include_request_info,
            )

    return ConfiguredErrorMiddleware
