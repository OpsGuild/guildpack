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
        if isinstance(e, ValueError):
            return {
                "level": "WARNING",
                "http_status_code": 400,
                "message": str(e) or "Invalid value provided.",
            }
        elif isinstance(e, TypeError):
            return {
                "level": "WARNING",
                "http_status_code": 400,
                "message": str(e) or "Type mismatch in request.",
            }
        elif isinstance(e, KeyError):
            key = str(e).strip("'\"") if e.args else "Key"
            return {
                "level": "WARNING",
                "http_status_code": 400,
                "message": f"Missing key: {key}.",
            }
        elif isinstance(e, IndexError):
            return {
                "level": "WARNING",
                "http_status_code": 400,
                "message": "Index out of range.",
            }
        elif isinstance(e, AttributeError):
            return {
                "level": "ERROR",
                "http_status_code": 500,
                "message": "Attribute error in processing the request.",
            }
        elif isinstance(e, PermissionError):
            return {
                "level": "WARNING",
                "http_status_code": 403,
                "message": "You do not have permission to perform this action.",
            }
        elif isinstance(e, FileNotFoundError):
            return {
                "level": "WARNING",
                "http_status_code": 404,
                "message": "Requested file was not found.",
            }
        elif isinstance(e, MemoryError):
            return {
                "level": "ERROR",
                "http_status_code": 507,
                "message": "Insufficient memory to process the request.",
            }
        elif isinstance(e, TimeoutError):
            return {
                "level": "WARNING",
                "http_status_code": 408,
                "message": "Request timeout occurred.",
            }
        elif isinstance(e, ConnectionError):
            return {
                "level": "ERROR",
                "http_status_code": 503,
                "message": "Connection error occurred.",
            }
        elif isinstance(e, OSError):
            return {
                "level": "ERROR",
                "http_status_code": 500,
                "message": "Operating system error occurred.",
            }
        else:
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
