import json
from typing import Any, Dict

try:
    from fastapi import HTTPException as FastAPIHTTPException
except ImportError:
    FastAPIHTTPException = None

try:
    from starlette.exceptions import HTTPException as StarletteHTTPException
except ImportError:
    StarletteHTTPException = None

try:
    from django.http import (HttpResponseBadRequest, HttpResponseForbidden,
                             HttpResponseNotFound, HttpResponseServerError)

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

try:
    from starlette.exceptions import HTTPException as BaseHTTPException
except ImportError:
    BaseHTTPException = Exception


class CommonErrorHandler:
    """Handler for common Python exceptions and framework-specific errors."""

    def __init__(self, logger):
        self.logger = logger

    def handle_error(self, e: Exception) -> Dict[str, Any]:
        """Handle common Python exceptions and return error details."""
        error_info = {
            "level": "ERROR",
            "http_status_code": 500,
            "message": "An unexpected error occurred.",
            "error_type": type(e).__name__,
        }

        if isinstance(e, BaseHTTPException):
            error_info.update(self._handle_http_exception(e))
        elif FastAPIHTTPException and isinstance(e, FastAPIHTTPException):
            error_info.update(self._handle_fastapi_exception(e))
        elif StarletteHTTPException and isinstance(e, StarletteHTTPException):
            error_info.update(self._handle_starlette_exception(e))
        elif WerkzeugHTTPException and isinstance(e, WerkzeugHTTPException):
            error_info.update(self._handle_werkzeug_exception(e))
        elif DjangoHTTPExceptions and any(
            isinstance(e, exc_class)
            for exc_class in DjangoHTTPExceptions.values()
        ):
            error_info.update(self._handle_django_exception(e))
        else:
            error_info.update(self._handle_standard_exceptions(e))

        return error_info

    def _handle_http_exception(self, e: BaseHTTPException) -> Dict[str, Any]:
        """Handle Starlette HTTPException."""
        return {
            "level": "WARNING",
            "http_status_code": getattr(e, "status_code", 500),
            "message": getattr(e, "detail", "HTTP error occurred."),
        }

    def _handle_fastapi_exception(
        self, e: FastAPIHTTPException
    ) -> Dict[str, Any]:
        """Handle FastAPI HTTPException."""
        return {
            "level": "WARNING",
            "http_status_code": e.status_code,
            "message": e.detail or "HTTP error occurred.",
        }

    def _handle_starlette_exception(
        self, e: StarletteHTTPException
    ) -> Dict[str, Any]:
        """Handle Starlette HTTPException."""
        return {
            "level": "WARNING",
            "http_status_code": e.status_code,
            "message": e.detail or "HTTP error occurred.",
        }

    def _handle_werkzeug_exception(
        self, e: WerkzeugHTTPException
    ) -> Dict[str, Any]:
        """Handle Werkzeug HTTPException."""
        return {
            "level": "WARNING",
            "http_status_code": e.code,
            "message": e.description or "HTTP error occurred.",
        }

    def _handle_django_exception(self, e: Exception) -> Dict[str, Any]:
        """Handle Django HTTP exceptions."""
        for status_code, exc_class in DjangoHTTPExceptions.items():
            if isinstance(e, exc_class):
                return {
                    "level": "WARNING",
                    "http_status_code": status_code,
                    "message": str(e) or "HTTP error occurred.",
                }
        return {
            "level": "ERROR",
            "http_status_code": 500,
            "message": "Django HTTP error occurred.",
        }

    def _handle_standard_exceptions(self, e: Exception) -> Dict[str, Any]:
        """Handle standard Python exceptions."""
        exception_handlers = {
            ValueError: self._handle_value_error,
            TypeError: self._handle_type_error,
            KeyError: self._handle_key_error,
            IndexError: self._handle_index_error,
            AttributeError: self._handle_attribute_error,
            PermissionError: self._handle_permission_error,
            FileNotFoundError: self._handle_file_not_found_error,
            MemoryError: self._handle_memory_error,
            TimeoutError: self._handle_timeout_error,
            ConnectionError: self._handle_connection_error,
            OSError: self._handle_os_error,
        }

        handler = exception_handlers.get(type(e))
        if handler:
            return handler(e)

        return self._handle_generic_error(e)

    def _handle_value_error(self, e: ValueError) -> Dict[str, Any]:
        return {
            "level": "WARNING",
            "http_status_code": 400,
            "message": str(e) or "Invalid value provided.",
        }

    def _handle_type_error(self, e: TypeError) -> Dict[str, Any]:
        return {
            "level": "WARNING",
            "http_status_code": 400,
            "message": str(e) or "Type mismatch in request.",
        }

    def _handle_key_error(self, e: KeyError) -> Dict[str, Any]:
        key = str(e).strip("'\"") if e.args else "Key"
        return {
            "level": "WARNING",
            "http_status_code": 400,
            "message": f"Missing key: {key}.",
        }

    def _handle_index_error(self, e: IndexError) -> Dict[str, Any]:
        return {
            "level": "WARNING",
            "http_status_code": 400,
            "message": "Index out of range.",
        }

    def _handle_attribute_error(self, e: AttributeError) -> Dict[str, Any]:
        return {
            "level": "ERROR",
            "http_status_code": 500,
            "message": "Attribute error in processing the request.",
        }

    def _handle_permission_error(self, e: PermissionError) -> Dict[str, Any]:
        return {
            "level": "WARNING",
            "http_status_code": 403,
            "message": "You do not have permission to perform this action.",
        }

    def _handle_file_not_found_error(self, e: FileNotFoundError) -> Dict[str, Any]:
        return {
            "level": "WARNING",
            "http_status_code": 404,
            "message": "Requested file was not found.",
        }

    def _handle_memory_error(self, e: MemoryError) -> Dict[str, Any]:
        return {
            "level": "ERROR",
            "http_status_code": 507,
            "message": "Insufficient memory to process the request.",
        }

    def _handle_timeout_error(self, e: TimeoutError) -> Dict[str, Any]:
        return {
            "level": "WARNING",
            "http_status_code": 408,
            "message": "Request timeout occurred.",
        }

    def _handle_connection_error(self, e: ConnectionError) -> Dict[str, Any]:
        return {
            "level": "ERROR",
            "http_status_code": 503,
            "message": "Connection error occurred.",
        }

    def _handle_os_error(self, e: OSError) -> Dict[str, Any]:
        return {
            "level": "ERROR",
            "http_status_code": 500,
            "message": "Operating system error occurred.",
        }

    def _handle_generic_error(self, e: Exception) -> Dict[str, Any]:
        return {
            "level": "ERROR",
            "http_status_code": getattr(e, "http_status_code", 500),
            "message": str(e) or "An unexpected error occurred.",
        }

    def get_exception_attributes(self, e: Exception) -> str:
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
