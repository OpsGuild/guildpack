import functools
import inspect
import json
import sys
import traceback
import uuid
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
    """Error response class with multi-framework support.

    Dynamic usage patterns:
        raise Error("Something went wrong")
        raise Error("Not found", 404)
        raise Error(ValueError("Invalid input"), "Validation failed", 400)
        raise Error(404, "Not found")
        raise Error(exception, status_code=500, message="Server error")
    """

    def __new__(
        cls,
        *args: Any,
        **kwargs: Any,
    ):
        instance = super().__new__(cls)
        return instance

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ):
        # If we're already in the middle of handling an exception that represents
        # a previously raised Error (either the Error itself or a framework-specific
        # HTTPException produced by Error.to_framework_exception), re-raise it
        # immediately to avoid any double-wrapping regardless of the new args.
        try:
            exc_type, exc_value, _ = sys.exc_info()
            if exc_value is not None:
                # Case 1: Original Error instance is being handled → re-raise
                if isinstance(exc_value, Error):
                    raise exc_value

                # Case 2: FastAPI/Starlette HTTPException with our error dict in .detail
                detail = getattr(exc_value, "detail", None)
                if isinstance(detail, dict) and all(
                    k in detail for k in ("message", "status_code", "error")
                ):
                    raise exc_value

                # Case 3: Werkzeug HTTPException with our error dict JSON in .description
                description = getattr(exc_value, "description", None)
                if isinstance(description, str):
                    try:
                        parsed = json.loads(description)
                        if isinstance(parsed, dict) and all(
                            k in parsed
                            for k in ("message", "status_code", "error")
                        ):
                            raise exc_value
                    except Exception:
                        pass
        except Exception:
            pass

        e: Optional[Exception] = kwargs.pop("e", None)
        msg: Optional[str] = kwargs.pop("msg", None)
        code: Optional[int] = kwargs.pop("code", None)
        level: Optional[str] = kwargs.pop("level", None)
        additional_info: Optional[dict] = kwargs.pop("additional_info", None)
        _raise_immediately: bool = kwargs.pop("_raise_immediately", True)

        if "error" in kwargs and not e:
            e = kwargs.pop("error")
        if "message" in kwargs and not msg:
            msg = kwargs.pop("message")
        if "status_code" in kwargs and not code:
            code = kwargs.pop("status_code")

        for arg in args:
            if isinstance(arg, Exception):
                e = arg
            elif isinstance(arg, str):
                msg = arg
            elif isinstance(arg, int):
                code = arg
            elif isinstance(arg, dict):
                additional_info = arg

        if e is None:
            exc_type, exc_value, _ = sys.exc_info()
            if exc_value is not None:
                if isinstance(exc_value, Error):
                    raise exc_value
                e = exc_value

        self.e = e
        self.msg = msg or "Unknown server error."
        # Set status code: use provided code, or 500 if no exception, or None to let handlers decide
        if code is not None:
            self.http_status_code = code
        elif e is None:
            self.http_status_code = 500
        else:
            self.http_status_code = None  # Let handlers determine
        self.level = level or "ERROR"
        self.additional_info = additional_info or {}

        self.error_id = str(uuid.uuid4())

        if kwargs:
            self.additional_info.update(kwargs)

        self.logger = Logger(self.error_id).get_logger()

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
        # Always use handler status code if available
        handler_status_code = info.get("http_status_code")
        if handler_status_code is not None:
            self.http_status_code = handler_status_code
        elif self.http_status_code is None:
            # If no status code was set and handler doesn't provide one, use 500
            self.http_status_code = 500

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

        detail = None
        if self.e:
            if isinstance(self.e, Error):
                detail = self.e.msg
            else:
                detail = str(self.e).strip()

        return {
            "message": self.msg,
            "status_code": self.http_status_code,
            "error": {
                "level": self.level,
                "error_id": self.error_id,
                "detail": detail,
            },
            **self.additional_info,
        }

    def to_framework_exception(self):
        # If the underlying exception is already a framework exception or Error,
        # return it directly to avoid any double-wrapping
        if (
            FastAPIHTTPException is not None
            and isinstance(self.e, FastAPIHTTPException)
        ):
            return self.e
        if (
            StarletteHTTPException is not None
            and isinstance(self.e, StarletteHTTPException)
        ):
            return self.e
        if (
            WerkzeugHTTPException is not None
            and isinstance(self.e, WerkzeugHTTPException)
        ):
            return self.e
        if isinstance(self.e, Error):
            # Delegate to the inner Error's framework exception
            return self.e.to_framework_exception()

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
