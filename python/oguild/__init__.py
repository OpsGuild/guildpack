"""OGuild utilities — reusable logging and helpers for Python projects."""

from .logs import Logger, logger
from .response import (AuthenticationErrorHandler, CommonErrorHandler,
                       DatabaseErrorHandler, Error, FileErrorHandler,
                       NetworkErrorHandler, Ok, ValidationErrorHandler, police)
from .utils import sanitize_fields
from .middleware import ErrorMiddleware, create_error_middleware
# Also import from middlewares for plural form compatibility
from .middlewares import ErrorMiddleware as MiddlewaresErrorMiddleware, create_error_middleware as create_error_middlewares

# Import aliases for backward compatibility (singular/plural forms)
from .log import Logger as LogLogger, logger as log_logger
from .responses import (Ok as ResponsesOk, Error as ResponsesError,
                       police as responses_police)

__all__ = [
    "Logger",
    "logger",
    "Ok",
    "Error",
    "police",
    "CommonErrorHandler",
    "DatabaseErrorHandler",
    "ValidationErrorHandler",
    "NetworkErrorHandler",
    "AuthenticationErrorHandler",
    "FileErrorHandler",
    "sanitize_fields",
    "ErrorMiddleware",
    "create_error_middleware",
    # Aliases for singular/plural compatibility
    "LogLogger",
    "log_logger",
    "ResponsesOk",
    "ResponsesError",
    "responses_police",
    "MiddlewaresErrorMiddleware",
    "create_error_middlewares",
]
