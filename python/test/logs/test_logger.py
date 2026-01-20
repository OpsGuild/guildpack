import logging
import os
import tempfile
from unittest.mock import patch

import pytest
from oguild.logs import Logger


class TestLogger:
    """Test cases for Logger class."""

    def test_default_logger_name(self):
        """Test default logger returns dynamic wrapper for detection."""
        logger_instance = Logger()
        wrapped_logger = logger_instance.get_logger()

        # When no name provided, get_logger returns dynamic wrapper
        assert logger_instance._dynamic_wrapper is not None
        assert logger_instance.logger is None

        # The wrapper should have the log methods
        assert hasattr(wrapped_logger, 'info')
        assert hasattr(wrapped_logger, 'debug')
        assert hasattr(wrapped_logger, 'error')

    def test_dynamic_module_detection(self):
        """Test that dynamic wrapper detects caller module at log time."""
        logger_instance = Logger()
        wrapped_logger = logger_instance.get_logger()

        # Call a log method - this should create a logger for this test module
        wrapped_logger.info("Test message")

        # The wrapper should have cached a logger for this module
        assert len(wrapped_logger._loggers) > 0

        # The logger name should be this test module
        cached_module_names = list(wrapped_logger._loggers.keys())
        assert any('test_logger' in name for name in cached_module_names)

    def test_custom_logger_name(self):
        """Test custom logger name."""
        logger = Logger("test_logger")
        assert logger.logger.name == "test_logger"

    def test_log_level_from_env(self):
        """Test log level from environment variable."""
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            test_logger = logging.getLogger("test_env")
            test_logger.handlers.clear()
            test_logger.setLevel(logging.NOTSET)  # Reset level

            logger = Logger("test_env")
            assert logger.logger.level == logging.DEBUG

    def test_default_log_level(self):
        """Test default log level when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            logger = Logger("test")
            assert logger.logger.level == logging.INFO

    def test_file_logging(self):
        """Test file logging functionality."""
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as tmp_file:
            log_file = tmp_file.name

        try:
            logger = Logger("test_file", log_file=log_file)

            test_message = "Test log message"
            logger.logger.info(test_message)

            for handler in logger.logger.handlers:
                handler.flush()

            with open(log_file, "r") as f:
                content = f.read()
                assert test_message in content
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)

    def test_console_logging(self):
        """Test console logging functionality."""
        logger = Logger("test")

        assert len(logger.logger.handlers) >= 1

        assert isinstance(logger.logger.handlers[0], logging.StreamHandler)

    def test_logstash_handler_without_dependency(self):
        """Test logstash handler when dependency not available."""
        # Test that logger still works even when logstash is not available
        # This test verifies graceful degradation
        logger = Logger(
            "test", logstash_host="localhost", logstash_port=5959
        )

        assert logger.logger is not None
        assert len(logger.logger.handlers) >= 1
        # Should have at least console handler even without logstash
        handlers = logger.logger.handlers
        assert any(isinstance(h, logging.StreamHandler) for h in handlers)

    def test_logstash_handler_with_dependency(self):
        """Test logstash handler when dependency is available."""
        logger = Logger(
            "test_logstash", logstash_host="localhost", logstash_port=5959
        )

        assert logger.logger is not None
        assert len(logger.logger.handlers) >= 1

    def test_invalid_logstash_port(self):
        """Test handling of invalid logstash port."""
        with pytest.raises(ValueError, match="Invalid logstash_port"):
            Logger("test", logstash_host="localhost", logstash_port="invalid")

    def test_get_logger(self):
        """Test get_logger method."""
        logger_instance = Logger("test")
        logger = logger_instance.get_logger()

        from oguild.logs import SmartLogger

        assert isinstance(logger, SmartLogger)
        assert logger.name == "test"

    def test_logger_propagate_false(self):
        """Test that logger doesn't propagate to parent."""
        logger = Logger("test")
        assert logger.logger.propagate is False

    def test_multiple_handlers(self):
        """Test that multiple handlers can be added."""
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as tmp_file:
            log_file = tmp_file.name

        try:
            logger = Logger("test_multiple", log_file=log_file)

            assert len(logger.logger.handlers) >= 2

            handler_types = [type(h) for h in logger.logger.handlers]
            assert logging.StreamHandler in handler_types
            assert logging.FileHandler in handler_types
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)
