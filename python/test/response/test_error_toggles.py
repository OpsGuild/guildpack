import logging
import traceback
from unittest.mock import patch
import pytest
from oguild.response import Error
from oguild.middleware import ErrorMiddleware

class TestErrorToggles:
    """Test cases for include_stack_trace and include_error_attributes flags."""

    def test_error_attributes_toggle(self):
        """Test that include_error_attributes suppresses debug logs in Error.to_dict()."""
        # We need to set level to DEBUG to see if it would have logged
        from oguild.logs.logger import logger
        logger.setLevel(logging.DEBUG)

        # 1. With toggle ON
        error_on = Error(ValueError("test"), include_error_attributes=True, _raise_immediately=False)
        with patch.object(error_on.logger, "debug") as mock_debug:
            error_on.to_dict()
            # Should be called with "Error attributes: ..."
            assert any("Error attributes" in str(args[0]) for args, _ in mock_debug.call_args_list)

        # 2. With toggle OFF
        error_off = Error(ValueError("test"), include_error_attributes=False, _raise_immediately=False)
        with patch.object(error_off.logger, "debug") as mock_debug:
            error_off.to_dict()
            # Should NOT be called with "Error attributes"
            assert not any("Error attributes" in str(args[0]) for args, _ in mock_debug.call_args_list)

    def test_stack_trace_toggle(self):
        """Test that include_stack_trace suppresses debug logs in Error.to_dict()."""
        from oguild.logs.logger import logger
        logger.setLevel(logging.DEBUG)

        # 1. With toggle ON
        error_on = Error(ValueError("test"), include_stack_trace=True, _raise_immediately=False)
        with patch.object(error_on.logger, "debug") as mock_debug:
            error_on.to_dict()
            assert any("Stack trace" in str(args[0]) for args, _ in mock_debug.call_args_list)

        # 2. With toggle OFF
        error_off = Error(ValueError("test"), include_stack_trace=False, _raise_immediately=False)
        with patch.object(error_off.logger, "debug") as mock_debug:
            error_off.to_dict()
            assert not any("Stack trace" in str(args[0]) for args, _ in mock_debug.call_args_list)

    def test_middleware_passes_toggles(self):
        """Test that ErrorMiddleware passes the toggle flags to Error instances."""
        mw = ErrorMiddleware(
            app=None,
            include_stack_trace=False,
            include_error_attributes=False
        )

        # Use handle_exception to get an Error instance
        error = mw.handle_exception(ValueError("test"))
        
        assert error.include_stack_trace is False
        assert error.include_error_attributes is False

    def test_middleware_factory_passes_toggles(self):
        """Test that create_error_middleware factory correctly configures toggles."""
        from oguild.middleware import create_error_middleware
        
        ConfiguredMW = create_error_middleware(
            include_stack_trace=False,
            include_error_attributes=False
        )
        
        instance = ConfiguredMW(None)
        assert instance.include_stack_trace is False
        assert instance.include_error_attributes is False
