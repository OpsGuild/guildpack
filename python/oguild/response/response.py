import functools
import inspect
import json
import sys
import traceback
from http import HTTPStatus
from typing import Any, Callable, Dict, List, Optional

from oguild.logs import Logger

from .errors import (AuthenticationErrorHandler, CommonErrorHandler,
                     DatabaseErrorHandler, FileErrorHandler,
                     NetworkErrorHandler, ValidationErrorHandler)

logger = Logger("response").get_logger()

try:
    from fastapi import HTTPException as FastAPIHTTPException
    from fastapi.encoders import jsonable_encoder
    from fastapi.responses import JSONResponse as FastAPIJSONResponse
except ImportError:
    FastAPIJSONResponse = None
    FastAPIHTTPException = None
    jsonable_encoder = None

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
    _func: Optional[Callable] = None,
    *,
    default_msg: Optional[str] = None,
    default_code: Optional[int] = None,
):
    """
    Decorator to catch and format errors for sync or async functions.
    Can be used with or without parentheses:
        @police
        def foo(): ...

        @police(default_msg="Custom", default_code=400)
        def bar(): ...
    """

    def decorator(func: Callable):
        is_coroutine = inspect.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error = Error(
                    e,
                    msg=default_msg or f"Unexpected error in {func.__name__}",
                    code=default_code or 500,
                    _raise_immediately=False,
                )
                raise error.to_framework_exception()

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error = Error(
                    e,
                    msg=default_msg or f"Unexpected error in {func.__name__}",
                    code=default_code or 500,
                    _raise_immediately=False,
                )
                raise error.to_framework_exception()

        return async_wrapper if is_coroutine else sync_wrapper

    if _func is not None and callable(_func):
        return decorator(_func)

    return decorator


def _default_encoder(obj: Any):
    import dataclasses
    import datetime
    import uuid

    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    if hasattr(obj, "dict"):  # Pydantic v1
        return obj.dict()
    if hasattr(obj, "model_dump"):  # Pydantic v2
        return obj.model_dump()
    return str(obj)


class Ok:
    """
    Return a framework-native JSON response with the correct HTTP status code.
    Usage:
        return Ok(201)
        return Ok(201, "Created", {"id": 1})
        return Ok("Login successful", 201, user)
        return Ok(message="Done", status_code=200, data=user, foo="bar")
    """

    def __new__(cls, *args: Any, **kwargs: Any):
        status_code: int = kwargs.pop("status_code", 200)
        message: Optional[str] = kwargs.pop("message", None)
        data: Optional[Any] = kwargs.pop("data", None)
        extras: List[Any] = []

        # Positional parsing
        for arg in args:
            if isinstance(arg, int):
                status_code = arg
            elif isinstance(arg, str) and message is None:
                message = arg
            elif data is None:
                data = arg
            else:
                extras.append(arg)

        if not message:
            try:
                message = HTTPStatus(status_code).phrase
            except Exception:
                message = "Success"

        payload: Dict[str, Any] = {
            "status_code": status_code,
            "message": message,
        }

        if data not in (None, {}, [], (), ""):
            payload["data"] = list(data) if isinstance(data, tuple) else data

        if extras:
            payload["extras"] = extras

        if kwargs:
            payload.update(kwargs)

        if jsonable_encoder:
            payload = jsonable_encoder(payload)
        else:
            payload = json.loads(json.dumps(payload, default=_default_encoder))

        if FastAPIJSONResponse is not None:
            return FastAPIJSONResponse(
                content=payload, status_code=status_code
            )

        if StarletteJSONResponse is not None:
            return StarletteJSONResponse(
                content=payload, status_code=status_code
            )

        if DjangoJsonResponse is not None:
            return DjangoJsonResponse(payload, status=status_code)

        if FlaskResponse is not None:
            return FlaskResponse(
                json.dumps(payload, default=_default_encoder),
                status=status_code,
                mimetype="application/json",
            )

        return payload


class Error(Exception):
    """Error response class with multi-framework support."""

    def __new__(
        cls,
        e: Optional[Exception] = None,
        msg: Optional[str] = None,
        code: Optional[int] = None,
        level: Optional[str] = None,
        additional_info: Optional[dict] = None,
        _raise_immediately: bool = True,
        **kwargs,
    ):
        instance = super().__new__(cls)
        return instance

    def __init__(
        self,
        e: Optional[Exception] = None,
        msg: Optional[str] = None,
        code: Optional[int] = None,
        level: Optional[str] = None,
        additional_info: Optional[dict] = None,
        _raise_immediately: bool = True,
        **kwargs,
    ):
        if "error" in kwargs and not e:
            e = kwargs["error"]
        if "message" in kwargs and not msg:
            msg = kwargs["message"]
        if "status_code" in kwargs and not code:
            code = kwargs["status_code"]
        if e is None:
            exc_type, exc_value, _ = sys.exc_info()
            if exc_value is not None:
                e = exc_value

        self.e = e
        self.msg = msg or "Unknown server error."
        self.http_status_code = code or 500
        self.level = level or "ERROR"
        self.additional_info = additional_info or {}
        self.logger = Logger(str(self.http_status_code)).get_logger()

        # Handlers
        self.common_handler = CommonErrorHandler(self.logger)
        self.database_handler = DatabaseErrorHandler(self.logger)
        self.validation_handler = ValidationErrorHandler(self.logger)
        self.network_handler = NetworkErrorHandler(self.logger)
        self.auth_handler = AuthenticationErrorHandler(self.logger)
        self.file_handler = FileErrorHandler(self.logger)

        if e:
            self._handle_error_with_handlers(e, msg=msg)

        if _raise_immediately:
            raise self.to_framework_exception()

    def _handle_error_with_handlers(
        self, e: Exception, msg: Optional[str] = None
    ):
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

        if not msg:
            self.msg = info.get("message", self.msg)

    def to_dict(self):
        if self.e:
            self.logger.debug(
                f"Error attributes: {self.common_handler.get_exception_attributes(self.e)}"
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
            try:
                return DjangoJsonResponse(
                    error_dict, status=self.http_status_code
                )
            except Exception:
                pass
        if WerkzeugHTTPException:
            import json

            exception = WerkzeugHTTPException(
                description=json.dumps(error_dict)
            )
            exception.code = self.http_status_code
            return exception

        return Exception(self.msg)

    def __call__(self):
        """Make Error callable by raising the framework exception."""
        raise self.to_framework_exception()

    def __await__(self):
        """Make Error awaitable by raising the framework exception."""
        raise self.to_framework_exception()
