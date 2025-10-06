"""
OGuild Middlewares - Plural form alias for middleware module
"""

# Import everything from the middleware module
from ..middleware import ErrorMiddleware, create_error_middleware

__all__ = [
    "ErrorMiddleware",
    "create_error_middleware",
]
