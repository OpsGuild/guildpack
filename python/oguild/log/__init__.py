"""Alias for oguild.logs module - allows importing from oguild.log or oguild.logs."""

# Import everything from the logs module
from ..logs import *

# Re-export everything for backward compatibility
__all__ = [
    "Logger",
    "SmartLogger",
    "logger",
]
