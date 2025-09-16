"""Test that both oguild.log and oguild.logs imports work correctly."""

import pytest


class TestImportAliases:
    """Test import aliases for singular/plural forms."""

    def test_logs_import_works(self):
        """Test that original oguild.logs import still works."""
        from oguild.logs import Logger, logger
        assert Logger is not None
        assert logger is not None

    def test_log_import_works(self):
        """Test that new oguild.log import works."""
        from oguild.log import Logger, logger
        assert Logger is not None
        assert logger is not None

    def test_imports_are_identical(self):
        """Test that oguild.log and oguild.logs provide identical objects."""
        from oguild.logs import Logger as LogsLogger, logger as logs_logger
        from oguild.log import Logger as LogLogger, logger as log_logger
        
        # They should be the same classes/objects
        assert LogsLogger is LogLogger, "Logger classes should be identical"
        assert logs_logger is log_logger, "logger instances should be identical"

    def test_module_direct_import(self):
        """Test direct module imports work."""
        import oguild.log as log_module
        import oguild.logs as logs_module
        
        assert hasattr(log_module, 'Logger'), "oguild.log should have Logger"
        assert hasattr(logs_module, 'Logger'), "oguild.logs should have Logger"
        assert hasattr(log_module, 'logger'), "oguild.log should have logger"
        assert hasattr(logs_module, 'logger'), "oguild.logs should have logger"

    def test_logger_functionality(self):
        """Test that Logger works through both import paths."""
        from oguild.logs import Logger as LogsLogger
        from oguild.log import Logger as LogLogger
        
        # Create logger instances through both paths
        logs_logger = LogsLogger("test_logs")
        log_logger = LogLogger("test_log")
        
        # They should work identically
        assert logs_logger is not None
        assert log_logger is not None
        assert hasattr(logs_logger, 'get_logger')
        assert hasattr(log_logger, 'get_logger')
