import functools
import json
import re
import traceback
from typing import Any, Optional

import asyncpg
import pydantic
from oguild.logs import Logger
from oguild.utils import sanitize_fields
from starlette.exceptions import HTTPException

logger = Logger("response").get_logger()

# Optional imports for framework-specific responses
try:
    from fastapi.responses import JSONResponse as FastAPIJSONResponse
except ImportError:
    FastAPIJSONResponse = None

try:
    from starlette.responses import JSONResponse as StarletteJSONResponse
except ImportError:
    StarletteJSONResponse = None

try:
    from django.http import JsonResponse as DjangoJsonResponse
except ImportError:
    DjangoJsonResponse = None

try:
    from flask import Response as FlaskResponse
except ImportError:
    FlaskResponse = None

# Optional imports for framework-specific HTTP exceptions
try:
    from fastapi import HTTPException as FastAPIHTTPException
except ImportError:
    FastAPIHTTPException = None

try:
    from starlette.exceptions import HTTPException as StarletteHTTPException
except ImportError:
    StarletteHTTPException = None

try:
    from django.http import Http404, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError
    DjangoHTTPExceptions = {
        400: HttpResponseBadRequest,
        403: HttpResponseForbidden,
        404: HttpResponseNotFound,
        500: HttpResponseServerError,
    }
except ImportError:
    DjangoHTTPExceptions = {}

try:
    from werkzeug.exceptions import HTTPException as WerkzeugHTTPException
except ImportError:
    WerkzeugHTTPException = None


class CustomError(Exception):
    """Custom error class for handling application-specific errors."""

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
        super().__init__(self.msg)



def format_param(param, max_len=300):
    """Format a parameter nicely, truncate long strings."""
    if isinstance(param, str):
        preview = param.replace("\n", "\\n")
        if len(preview) > max_len:
            preview = preview[:max_len] + "...[truncated]"
        return f"'{preview}'"
    else:
        return repr(param)


def create_http_exception(
    status_code: int,
    message: str = "HTTP error occurred",
    framework: Optional[str] = None
):
    """Create a framework-agnostic HTTP exception."""
    # Explicit framework choice
    if framework == "fastapi" and FastAPIHTTPException:
        return FastAPIHTTPException(status_code=status_code, detail=message)
    if framework == "starlette" and StarletteHTTPException:
        return StarletteHTTPException(status_code=status_code, detail=message)
    if framework == "django" and DjangoHTTPExceptions:
        exception_class = DjangoHTTPExceptions.get(status_code)
        if exception_class:
            return exception_class(message)
    if framework == "flask" and WerkzeugHTTPException:
        return WerkzeugHTTPException(description=message, code=status_code)

    # Auto-detect
    if FastAPIHTTPException:
        return FastAPIHTTPException(status_code=status_code, detail=message)
    if StarletteHTTPException:
        return StarletteHTTPException(status_code=status_code, detail=message)
    if DjangoHTTPExceptions:
        exception_class = DjangoHTTPExceptions.get(status_code)
        if exception_class:
            return exception_class(message)
    if WerkzeugHTTPException:
        return WerkzeugHTTPException(description=message, code=status_code)

    # Fallback to generic exception
    return Exception(f"HTTP {status_code}: {message}")


def catch_error(func):
    """Decorator to catch and format errors."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Format args and kwargs nicely
        formatted_args = ", ".join(format_param(a) for a in args)
        formatted_kwargs = ", ".join(
            f"{k}={format_param(v)}" for k, v in kwargs.items()
        )
        full_params = f"{func.__name__}({formatted_args}"
        if formatted_kwargs:
            full_params += f", {formatted_kwargs}"
        full_params += ")"

        try:
            return await func(*args, **kwargs)
        except Exception as e:
            raise CustomError(e, f"Unexpected error in {func.__name__}", 500)

    return wrapper


class OK:
    """Success response class."""

    def __init__(
        self,
        message: str = "Success",
        status_code: int = 200,
        data: Optional[Any] = None,
        meta: Optional[Any] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.data = data or []
        self.meta = meta or []

    async def __call__(self):
        """Create a JSON response."""
        response = {
            "message": self.message,
            "status_code": self.status_code,
            "data": await sanitize_fields(self.data),
            "meta": await sanitize_fields(self.meta),
        }

        # Try to use framework-specific response, fallback to dict
        try:
            if FastAPIJSONResponse:
                return FastAPIJSONResponse(
                    content=response, status_code=self.status_code
                )
            elif StarletteJSONResponse:
                return StarletteJSONResponse(
                    content=response, status_code=self.status_code
                )
            elif DjangoJsonResponse:
                return DjangoJsonResponse(response, status=self.status_code)
            elif FlaskResponse:
                return FlaskResponse(
                    json.dumps(response),
                    status=self.status_code,
                    mimetype="application/json",
                )
            else:
                return response
        except Exception:
            return response

    def __await__(self):
        return self.__call__().__await__()


class Error(Exception):
    """Error response class for handling various types of errors."""

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

        if not e:
            super().__init__(self.msg)
            return

        if isinstance(e, CustomError):
            self.e = e.e
            self.msg = e.msg or self.msg
            self.http_status_code = e.http_status_code or self.http_status_code
            self.level = e.level or self.level
            self.additional_info = e.additional_info or self.additional_info
            return

        if isinstance(e, asyncpg.PostgresError):
            self._handle_postgres_error(e)
        else:
            self._handle_common_errors(e)

    def _get_attrs(self, e: Exception):
        """Get attributes of an exception for logging."""
        attrs = {}

        for attr in dir(e):
            if attr.startswith("__"):
                continue
            try:
                value = getattr(e, attr)
                if value is None:
                    continue
                if isinstance(value, (str, int, float, bool)):
                    attrs[attr] = value
                elif isinstance(value, (list, tuple)):
                    attrs[attr] = [str(v) for v in value]
                elif isinstance(value, dict):
                    attrs[attr] = {k: str(v) for k, v in value.items()}
                else:
                    attrs[attr] = str(value)
            except Exception:
                attrs[attr] = "<could not retrieve>"

        return json.dumps(dict(sorted(attrs.items())), indent=2)

    def _handle_postgres_error(self, e: asyncpg.PostgresError):
        """Handle PostgreSQL-specific errors."""
        self.level = getattr(e, "severity", "ERROR")

        if isinstance(e, asyncpg.exceptions.UniqueViolationError):
            self.http_status_code = 409
            constraint = getattr(e, "constraint_name", None)
            if constraint:
                parts = constraint.split("_")
                if len(parts) >= 3:
                    column = parts[1].replace("_", " ").capitalize()
                    self.msg = f"{column} already exist."
                else:
                    self.msg = "Resource already exists."
            else:
                self.msg = "Resource already exists."

        elif isinstance(e, asyncpg.exceptions.ForeignKeyViolationError):
            self.http_status_code = 400
            constraint = getattr(e, "constraint_name", None)
            if constraint:
                parts = constraint.split("_")
                if len(parts) > 2:
                    middle_parts = [p for p in parts[1:-1] if p != "id"]
                    if middle_parts:
                        field = " ".join(middle_parts).replace("_", " ")
                        self.msg = f"Selected {field} does not exist."
                    else:
                        self.msg = "Invalid foreign key reference."
                elif constraint.startswith("fk_") and len(parts) == 2:
                    field = constraint[3:].replace("_", " ")
                    self.msg = f"Selected {field} does not exist."
                else:
                    self.msg = "Invalid foreign key reference."
            else:
                self.msg = "Foreign key constraint failed."

        elif isinstance(e, asyncpg.exceptions.CheckViolationError):
            self.http_status_code = 400
            constraint = getattr(e, "constraint_name", None)
            if constraint:
                parts = constraint.split("_")
                if len(parts) >= 2:
                    field = parts[1].replace("_", " ")
                    self.msg = f"Invalid value for {field}."
                else:
                    self.msg = "Check constraint failed."
            else:
                self.msg = "Check constraint failed."

        elif isinstance(e, asyncpg.exceptions.NotNullViolationError):
            self.http_status_code = 400
            column = getattr(e, "column_name", None)
            if column:
                self.msg = (
                    f"{column.replace('_', ' ').capitalize()} is required."
                )
            else:
                self.msg = "A required field is missing."

        elif isinstance(e, asyncpg.exceptions.UndefinedColumnError):
            self.http_status_code = 500
            column = None
            if e.args and len(e.args) > 0:
                msg = e.args[0]
                match = re.search(
                    r'column "(?P<col>[^"]+)" does not exist', msg
                )
                if match:
                    column = match.group("col")

            if column:
                column_fmt = column.replace("_", " ")
                self.msg = f"{column_fmt.capitalize()} field does not exist."
            else:
                self.msg = "Invalid column reference."

        elif isinstance(e, asyncpg.exceptions.DataError):
            self.http_status_code = 400
            original_msg = str(e.args[0]).lower() if e.args else str(e).lower()

            if "out of range" in original_msg:
                self.msg = "Provided value is out of allowed range."
            elif "invalid input syntax" in original_msg:
                self.msg = "Invalid input syntax for a field."
            elif "invalid input value for enum" in original_msg:
                self.msg = "Invalid value provided for enum field."
            elif "invalid uuid" in original_msg:
                self.msg = "Invalid ID format provided."
            else:
                self.msg = "Invalid data provided."

        elif isinstance(e, asyncpg.exceptions.InvalidTextRepresentationError):
            self.http_status_code = 400
            self.msg = "Invalid input syntax for a field."

        elif isinstance(e, asyncpg.exceptions.PostgresSyntaxError):
            self.http_status_code = 500
            self.msg = "Something went wrong while processing your request."

        elif isinstance(e, asyncpg.exceptions.NumericValueOutOfRangeError):
            self.http_status_code = 400
            self.msg = "A numeric value is out of range."

        elif isinstance(e, asyncpg.exceptions.DivisionByZeroError):
            self.http_status_code = 400
            self.msg = "Attempted division by zero."

        elif isinstance(e, asyncpg.exceptions.StringDataRightTruncationError):
            self.http_status_code = 400
            self.msg = "Input string is too long for the column."

        elif isinstance(e, asyncpg.exceptions.InvalidDatetimeFormatError):
            self.http_status_code = 400
            self.msg = "Invalid datetime format."

    def _handle_common_errors(self, e: Exception):
        """Handle common Python exceptions."""
        self.level = getattr(e, "severity", "ERROR")

        # Framework-agnostic HTTPException detection
        if isinstance(e, HTTPException):
            self.http_status_code = e.status_code
            self.msg = e.detail or "HTTP error occurred."
        elif FastAPIHTTPException and isinstance(e, FastAPIHTTPException):
            self.http_status_code = e.status_code
            self.msg = e.detail or "HTTP error occurred."
        elif StarletteHTTPException and isinstance(e, StarletteHTTPException):
            self.http_status_code = e.status_code
            self.msg = e.detail or "HTTP error occurred."
        elif WerkzeugHTTPException and isinstance(e, WerkzeugHTTPException):
            self.http_status_code = e.code
            self.msg = e.description or "HTTP error occurred."
        elif DjangoHTTPExceptions and any(isinstance(e, exc_class) for exc_class in DjangoHTTPExceptions.values()):
            # Map Django HTTP exceptions to status codes
            for status_code, exc_class in DjangoHTTPExceptions.items():
                if isinstance(e, exc_class):
                    self.http_status_code = status_code
                    self.msg = str(e) or "HTTP error occurred."
                    break

        elif isinstance(e, pydantic.ValidationError):
            self.http_status_code = 422
            self.msg = "Request validation failed."

        elif isinstance(e, ValueError):
            self.http_status_code = 400
            self.msg = str(e) or "Invalid value provided."

        elif isinstance(e, TypeError):
            self.http_status_code = 400
            self.msg = str(e) or "Type mismatch in request."

        elif isinstance(e, KeyError):
            self.http_status_code = 400
            key = str(e).strip("'\"") if e.args else "Key"
            self.msg = f"Missing key: {key}."

        elif isinstance(e, IndexError):
            self.http_status_code = 400
            self.msg = "Index out of range."

        elif isinstance(e, AttributeError):
            self.http_status_code = 500
            self.msg = "Attribute error in processing the request."

        elif isinstance(e, PermissionError):
            self.http_status_code = 403
            self.msg = "You do not have permission to perform this action."

        elif isinstance(e, FileNotFoundError):
            self.http_status_code = 404
            self.msg = "Requested file was not found."

        else:
            self.msg = self.msg or (
                "An error occurred while processing your request."
                if self.e
                else None
            )

            self.http_status_code = getattr(e, "http_status_code", 500)

    def __str__(self):
        return f"{self.msg}"

    def to_dict(self):
        """Convert error to dictionary format."""
        if self.e:
            self.logger.debug(f"Error attributes: {self._get_attrs(self.e)}")
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

        error_dict = {
            "message": self.msg,
            "error": {
                "level": self.level,
                "error_message": str(self.e).strip() if self.e else None,
                "status_code": self.http_status_code,
            },
        }

        return {**error_dict, **self.additional_info}

    def to_framework_exception(self, framework: Optional[str] = None):
        """Convert to framework-specific HTTP exception."""
        error_dict = self.to_dict()
        
        # Explicit framework choice
        if framework == "fastapi" and FastAPIHTTPException:
            return FastAPIHTTPException(
                status_code=self.http_status_code,
                detail=self.msg
            )
        if framework == "starlette" and StarletteHTTPException:
            return StarletteHTTPException(
                status_code=self.http_status_code,
                detail=self.msg
            )
        if framework == "django" and DjangoHTTPExceptions:
            exception_class = DjangoHTTPExceptions.get(self.http_status_code)
            if exception_class:
                return exception_class(self.msg)
        if framework == "flask" and WerkzeugHTTPException:
            return WerkzeugHTTPException(
                description=self.msg,
                code=self.http_status_code
            )

        # Auto-detect
        if FastAPIHTTPException:
            return FastAPIHTTPException(
                status_code=self.http_status_code,
                detail=self.msg
            )
        if StarletteHTTPException:
            return StarletteHTTPException(
                status_code=self.http_status_code,
                detail=self.msg
            )
        if DjangoHTTPExceptions:
            exception_class = DjangoHTTPExceptions.get(self.http_status_code)
            if exception_class:
                return exception_class(self.msg)
        if WerkzeugHTTPException:
            return WerkzeugHTTPException(
                description=self.msg,
                code=self.http_status_code
            )

        # Fallback to generic exception
        return Exception(self.msg)
