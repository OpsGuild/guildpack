import pytest
import logging
import sys
from oguild.logs import logger

@pytest.fixture(autouse=True)
def reset_log_level():
    """Automatically reset the global log level after each test to ensure isolation."""
    # Helper to get the actual module
    def get_l_mod():
        return sys.modules["oguild.logs.logger"]

    # Reset before test
    get_l_mod()._CONFIGURED_LOG_LEVEL = None
    logger._log_level = None
    
    yield
    
    # Reset after test
    get_l_mod()._CONFIGURED_LOG_LEVEL = None
    logger._log_level = None
