# flake8: noqa
"""Guildpack - Alias package for oguild.

This package provides an alternative installation name for oguild.
All functionality is re-exported from oguild.

Install with: pip install guildpack
"""

# Re-export everything from oguild
from oguild import *
from oguild import __all__ as _oguild_all

# Note: Submodules (logs, utils, etc.) are available as sub-packages
# because they are now physical directories in this package.

__all__ = _oguild_all
