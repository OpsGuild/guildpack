from unittest.mock import patch

from oguild.logs import Logger


class TestLoggerIntegration:
    """Integration tests for Logger."""

    def test_logger_with_format_option(self):
        """Test logger with format option."""
        logger_instance = Logger("test_integration")
        logger = logger_instance.get_logger()

        with patch.object(logger, "_log_with_format_option") as mock_log:
            test_dict = {"key": "value"}
            logger.info(test_dict, format=True)

            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][1] == test_dict
            assert call_args[1]["format"] is True

    def test_logger_without_format_option(self):
        """Test logger without format option."""
        logger_instance = Logger("test_integration2")
        logger = logger_instance.get_logger()

        with patch.object(logger, "_log_with_format_option") as mock_log:
            test_dict = {"key": "value"}
            logger.info(test_dict, format=False)

            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][1] == test_dict
