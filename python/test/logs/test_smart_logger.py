import json
import uuid
from unittest.mock import patch

from oguild.logs import SmartLogger


class TestSmartLogger:
    """Test cases for SmartLogger class."""

    def test_uuid_formatting(self):
        """Test UUID formatting in log messages."""
        logger = SmartLogger("test")

        test_uuid = str(uuid.uuid4())
        message = f"User with UUID('{test_uuid}') logged in"
        formatted = logger._pretty_format(message)

        assert test_uuid in formatted
        assert "UUID(" not in formatted

    def test_json_formatting(self):
        """Test JSON formatting in log messages."""
        logger = SmartLogger("test")

        test_dict = {"name": "test", "value": 123}
        formatted = logger._pretty_format(test_dict)

        parsed = json.loads(formatted)
        assert parsed == test_dict
        assert "\n" in formatted  # Pretty printed

    def test_list_formatting(self):
        """Test list formatting in log messages."""
        logger = SmartLogger("test")

        test_list = [1, 2, 3, {"nested": "value"}]
        formatted = logger._pretty_format(test_list)

        parsed = json.loads(formatted)
        assert parsed == test_list
        assert "\n" in formatted  # Pretty printed

    def test_uuid_in_dict(self):
        """Test UUID handling in dictionaries."""
        logger = SmartLogger("test")

        test_uuid = uuid.uuid4()
        test_dict = {"id": test_uuid, "name": "test"}
        formatted = logger._pretty_format(test_dict)

        parsed = json.loads(formatted)
        assert parsed["id"] == str(test_uuid)
        assert parsed["name"] == "test"

    def test_log_methods_with_format(self):
        """Test logging methods with format=True."""
        logger = SmartLogger("test")

        with patch.object(logger, "_log_with_format_option") as mock_log:
            test_dict = {"key": "value"}
            logger.info(test_dict, format=True)

            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][1] == test_dict
            assert call_args[1]["format"] is True

    def test_log_methods_without_format(self):
        """Test logging methods without format=True."""
        logger = SmartLogger("test")

        with patch.object(logger, "_log_with_format_option") as mock_log:
            test_dict = {"key": "value"}
            logger.info(test_dict, format=False)

            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][1] == test_dict
