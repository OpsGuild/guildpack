import logging
import os
import sys
from unittest.mock import patch
import pytest

# Directly get the module object from sys.modules to avoid name collisions with 'logger' instance
import oguild.logs.logger 
def get_logger_module():
    return sys.modules["oguild.logs.logger"]

from oguild.logs import Logger, logger

class TestLogInheritance:
    """Test cases for log level inheritance functionality."""

    def test_global_level_reset(self):
        """Test that setting level on 'logger' updates global state."""
        l_mod = get_logger_module()
        logger.setLevel(logging.DEBUG)
        assert l_mod.get_default_log_level() == logging.DEBUG
        assert l_mod._CONFIGURED_LOG_LEVEL == logging.DEBUG
        
        logger.setLevel(logging.WARNING)
        assert l_mod.get_default_log_level() == logging.WARNING

    def test_new_logger_inherits_global_level(self):
        """Test that new Logger instances inherit the global level."""
        # Set runtime level
        logger.setLevel(logging.ERROR)
        
        # New Logger should pick it up
        new_logger = Logger("test_inheritance").get_logger()
        # Wait, if conftest sets logger._log_level = None, we need to be sure it picks up current config
        assert new_logger.level == logging.ERROR

    def test_dynamic_logger_inherits_global_level(self):
        """Test that dynamic loggers inherit global level if not explicitly set."""
        logger.setLevel(logging.CRITICAL)
        
        from oguild.logs.logger import _DynamicLoggerWrapper
        # Create a fresh wrapper with no level set
        wrapper = _DynamicLoggerWrapper()
        
        # It should use the effective default (CRITICAL)
        assert wrapper._get_log_level(None) == logging.CRITICAL

    def test_env_var_respected_if_not_configured(self):
        """Test that environment variables are still respected if no runtime level is set."""
        l_mod = get_logger_module()
        l_mod._CONFIGURED_LOG_LEVEL = None
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            assert l_mod.get_default_log_level() == logging.DEBUG

    def test_level_check_in_smart_logger(self):
        """Test that SmartLogger respects level checks (isEnabledFor)."""
        logger.setLevel(logging.WARNING)
        
        sm = Logger("test_smart").get_logger()
        assert sm.level == logging.WARNING

        with patch.object(logging.Logger, "handle") as mock_handle:
            sm.debug("This should be suppressed")
            mock_handle.assert_not_called()
            
            sm.warning("This should pass")
            mock_handle.assert_called()
