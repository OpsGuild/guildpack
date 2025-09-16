"""Alias for oguild.response module - allows importing from oguild.responses or oguild.response."""

# Import everything from the response module
from ..response import *

# Re-export everything for backward compatibility
__all__ = [
    "Ok",
    "Error",
    "police",
    "CommonErrorHandler",
    "DatabaseErrorHandler",
    "ValidationErrorHandler",
    "NetworkErrorHandler",
    "AuthenticationErrorHandler",
    "FileErrorHandler",
]
