import asyncio
import functools
import inspect
import json
import traceback
from typing import Any, Callable, Dict, Optional

from oguild.logs import Logger

from .errors import (AuthenticationErrorHandler, CommonErrorHandler,
                     DatabaseErrorHandler, FileErrorHandler,
                     NetworkErrorHandler, ValidationErrorHandler)

logger = Logger("response").get_logger()

try:
    from fastapi import HTTPException as FastAPIHTTPException
    from fastapi.responses import JSONResponse as FastAPIJSONResponse
except ImportError:
    FastAPIJSONResponse = None
    FastAPIHTTPException = None

try:
    from starlette.exceptions import HTTPException as StarletteHTTPException
    from starlette.responses import JSONResponse as StarletteJSONResponse
except ImportError:
    StarletteJSONResponse = None
    StarletteHTTPException = None

try:
    from django.http import JsonResponse as DjangoJsonResponse
except ImportError:
    DjangoJsonResponse = None

try:
    from flask import Response as FlaskResponse
except ImportError:
    FlaskResponse = None

try:
    from werkzeug.exceptions import HTTPException as WerkzeugHTTPException
except ImportError:
    WerkzeugHTTPException = None


def format_param(param, max_len=300):
    """Format a parameter nicely, truncate long strings."""
    if isinstance(param, str):
        preview = param.replace("\n", "\\n")
        if len(preview) > max_len:
            preview = preview[:max_len] + "...[truncated]"
        return f"'{preview}'"
    return repr(param)


def police(
    default_msg: Optional[str] = None, default_code: Optional[int] = None
):
    """
    Decorator to catch and format errors for sync or async functions.
    """

    def decorator(func: Callable):
        is_coroutine = inspect.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            _log_call(func, args, kwargs)
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                raise Error(
                    e,
                    msg=default_msg or f"Unexpected error in {func.__name__}",
                    code=default_code or 500,
                )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            _log_call(func, args, kwargs)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                raise Error(
                    e,
                    msg=default_msg or f"Unexpected error in {func.__name__}",
                    code=default_code or 500,
                )

        return async_wrapper if is_coroutine else sync_wrapper

    return decorator


def _log_call(func, args, kwargs):
    """Helper to log function calls."""
    formatted_args = ", ".join(format_param(a) for a in args)
    formatted_kwargs = ", ".join(
        f"{k}={format_param(v)}" for k, v in kwargs.items()
    )
    full_params = (
        f"{func.__name__}({formatted_args}"
        + (f", {formatted_kwargs}" if formatted_kwargs else "")
        + ")"
    )
    logger.debug(f"Calling {full_params}")


class Ok:
    """Universal response class that works in sync and async contexts."""

    def __init__(
        self,
        message: str = "Success",
        response_dict: Optional[Dict[str, Any]] = None,
        status_code: int = 200,
        **kwargs: Any,
    ):
        self.status_code = status_code
        self.payload: Dict[str, Any] = (
            dict(response_dict) if response_dict else {}
        )
        self.payload.update(kwargs)
        self.payload.setdefault("message", message)
        self.payload.setdefault("status_code", self.status_code)

    def to_framework_response(self):
        """Convert to framework-specific response."""
        response = {**self.payload}

        try:
            if FastAPIJSONResponse:
                return FastAPIJSONResponse(
                    content=response, status_code=self.status_code
                )
            if StarletteJSONResponse:
                return StarletteJSONResponse(
                    content=response, status_code=self.status_code
                )
            if DjangoJsonResponse:
                return DjangoJsonResponse(response, status=self.status_code)
            if FlaskResponse:
                return FlaskResponse(
                    json.dumps(response),
                    status=self.status_code,
                    mimetype="application/json",
                )
            return response
        except Exception:
            return response

    def __call__(self):
        """Auto-detect sync vs async context."""
        try:
            asyncio.get_running_loop()
            return self._async_call()
        except RuntimeError:
            return self.to_framework_response()

    async def _async_call(self):
        return self.to_framework_response()

    def __await__(self):
        return self._async_call().__await__()


class Error(Exception):
    """Error response class with multi-framework support."""

    def __init__(
        self,
        e: Optional[Exception] = None,
        msg: Optional[str] = None,
        code: Optional[int] = None,
        level: Optional[str] = None,
        additional_info: Optional[dict] = None,
    ):
        self.e = e
        self.msg = msg or "Unknown server error."
        self.http_status_code = code or 500
        self.level = level or "ERROR"
        self.additional_info = additional_info or {}
        self.logger = Logger(str(self.http_status_code)).get_logger()

        # Initialize error handlers
        self.common_handler = CommonErrorHandler(self.logger)
        self.database_handler = DatabaseErrorHandler(self.logger)
        self.validation_handler = ValidationErrorHandler(self.logger)
        self.network_handler = NetworkErrorHandler(self.logger)
        self.auth_handler = AuthenticationErrorHandler(self.logger)
        self.file_handler = FileErrorHandler(self.logger)

        if e:
            self._handle_error_with_handlers(e)

        super().__init__(self.msg)

    def _handle_error_with_handlers(self, e: Exception):
        """Use specialized error handlers to determine message and code."""
        if self.database_handler._is_database_error(e):
            info = self.database_handler.handle_error(e)
        elif self.validation_handler._is_validation_error(e):
            info = self.validation_handler.handle_error(e)
        elif self.auth_handler._is_auth_error(e):
            info = self.auth_handler.handle_error(e)
        elif self.file_handler._is_file_error(e):
            info = self.file_handler.handle_error(e)
        elif self.network_handler._is_network_error(e):
            info = self.network_handler.handle_error(e)
        else:
            info = self.common_handler.handle_error(e)

        self.level = info.get("level", self.level)
        self.http_status_code = info.get(
            "http_status_code", self.http_status_code
        )
        self.msg = info.get("message", self.msg)

    def to_dict(self):
        """Convert error to dict, logging stack trace."""
        if self.e:
            self.logger.debug(
                f"Error attributes: "
                f"{self.common_handler.get_exception_attributes(self.e)}"
            )
            self.logger.debug(
                "Stack trace:\n"
                + "".join(
                    traceback.format_exception(
                        type(self.e), self.e, self.e.__traceback__
                    )
                )
            )
        else:
            self.logger.error(self.msg)

        return {
            "message": self.msg,
            "status_code": self.http_status_code,
            "error": {
                "level": self.level,
                "error_message": str(self.e).strip() if self.e else None,
            },
            **self.additional_info,
        }

    def to_framework_exception(self):
        """Convert to framework-specific HTTP exception."""
        error_dict = self.to_dict()

        if FastAPIHTTPException:
            return FastAPIHTTPException(
                status_code=self.http_status_code, detail=error_dict
            )
        if StarletteHTTPException:
            return StarletteHTTPException(
                status_code=self.http_status_code, detail=error_dict
            )
        if DjangoJsonResponse:
            return DjangoJsonResponse(error_dict, status=self.http_status_code)
        if WerkzeugHTTPException:
            import json

            exception = WerkzeugHTTPException(description=json.dumps(error_dict))
            exception.code = self.http_status_code
            return exception

        return Exception(self.msg)

    def __call__(self):
        raise self.to_framework_exception()

    def __await__(self):
        raise self.to_framework_exception()
