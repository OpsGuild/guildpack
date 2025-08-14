import os
import tempfile

from oguild.logs import Logger, logger


def test_console_logging(capfd):
    logger.info("Test console log")
    out, err = capfd.readouterr()
    assert "Test console log" in err


def test_file_logging():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "test.log")
        logger = Logger(
            logger_name="test.test_logger",
            log_file=log_path,
        ).get_logger()
        logger.info("Test file log")

        assert os.path.exists(log_path)
        with open(log_path) as f:
            content = f.read()
        assert "Test file log" in content


def test_module_name_logging():
    assert logger.name == "test.test_logger"
