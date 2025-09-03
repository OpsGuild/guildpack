import ast
import inspect
import json
import logging
import os
import re
import uuid

try:
    from logstash_async.formatter import LogstashFormatter
    from logstash_async.handler import AsynchronousLogstashHandler

    LOGSTASH_AVAILABLE = True
except ImportError:
    LOGSTASH_AVAILABLE = False


class SmartLogger(logging.Logger):
    uuid_pattern = re.compile(r"UUID\(['\"]([0-9a-fA-F\-]+)['\"]\)")

    def _pretty_format(self, msg):
        if isinstance(msg, str):
            return self._format_string_message(msg)
        elif isinstance(msg, (dict, list)):
            return self._format_dict_list_message(msg)
        return str(msg)

    def _format_string_message(self, msg):
        """Format string messages with JSON structure detection."""
        cleaned = self.uuid_pattern.sub(r'"\1"', msg)
        return self._replace_json_structures(cleaned)

    def _replace_json_structures(self, text):
        """Replace JSON-like structures in text with pretty-printed versions."""
        pattern = re.compile(
            r"""
            (
                \{
                    [^{}]+
                    (?:\{[^{}]*\}[^{}]*)*
                \}
                |
                \[
                    [^\[\]]+
                    (?:\[[^\[\]]*\][^\[\]]*)*
                \]
            )
        """,
            re.VERBOSE | re.DOTALL,
        )
        return re.sub(pattern, self._try_parse_and_pretty, text)

    def _try_parse_and_pretty(self, match):
        """Try to parse and pretty-print a matched JSON structure."""
        raw = match.group(0)
        try:
            parsed = ast.literal_eval(raw)
            return json.dumps(parsed, indent=2, ensure_ascii=False)
        except Exception:
            return raw

    def _format_dict_list_message(self, msg):
        """Format dict/list messages with UUID sanitization."""
        try:
            sanitized = self._sanitize_for_json(msg)
            return json.dumps(sanitized, indent=2, ensure_ascii=False)
        except Exception:
            return str(msg)

    def _sanitize_for_json(self, obj):
        """Sanitize objects for JSON serialization."""
        if isinstance(obj, dict):
            return {
                k: self._sanitize_for_json(str(v) if isinstance(v, uuid.UUID) else v)
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [self._sanitize_for_json(v) for v in obj]
        else:
            return str(obj) if isinstance(obj, uuid.UUID) else obj

    def _log_with_format_option(
        self, level, msg, args, format=False, **kwargs
    ):
        if format:
            msg = self._pretty_format(msg)
        super()._log(level, msg, args, **kwargs)

    def info(self, msg, *args, format=False, **kwargs):
        self._log_with_format_option(
            logging.INFO, msg, args, format=format, **kwargs
        )

    def debug(self, msg, *args, format=False, **kwargs):
        self._log_with_format_option(
            logging.DEBUG, msg, args, format=format, **kwargs
        )

    def warning(self, msg, *args, format=False, **kwargs):
        self._log_with_format_option(
            logging.WARNING, msg, args, format=format, **kwargs
        )

    def error(self, msg, *args, format=False, **kwargs):
        self._log_with_format_option(
            logging.ERROR, msg, args, format=format, **kwargs
        )

    def critical(self, msg, *args, format=False, **kwargs):
        self._log_with_format_option(
            logging.CRITICAL, msg, args, format=format, **kwargs
        )


class Logger:
    def __init__(
        self,
        logger_name: str = None,
        log_file: str = None,
        log_level: int = None,
        log_format: str = "\n%(levelname)s: (%(name)s) == %(message)s "
        " [%(asctime)s]",
        logstash_host: str = None,
        logstash_port: int = 5959,
        logstash_database_path: str = None,
    ):
        logstash_port = self._validate_logstash_port(logstash_port)
        log_level = self._get_log_level(log_level)
        logger_name = self._get_logger_name(logger_name)

        self._setup_logger(logger_name, log_level, log_format, log_file,
                           logstash_host, logstash_port, logstash_database_path)

    def _validate_logstash_port(self, port):
        """Validate and convert logstash port to integer."""
        if port is None:
            return None
        try:
            return int(port)
        except ValueError:
            raise ValueError(f"Invalid logstash_port: {port}")

    def _get_log_level(self, log_level):
        """Get log level from parameter or environment."""
        if log_level is None:
            return getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper())
        return log_level

    def _get_logger_name(self, logger_name):
        """Get logger name from parameter or auto-detect from calling module."""
        if logger_name is None:
            for frame_info in inspect.stack():
                module = inspect.getmodule(frame_info.frame)
                if module and not module.__name__.startswith("oguild.logs"):
                    return module.__name__
            return "__main__"
        return logger_name

    def _setup_logger(self, logger_name, log_level, log_format, log_file,
                      logstash_host, logstash_port, logstash_database_path):
        """Setup the logger with handlers."""
        logging.setLoggerClass(SmartLogger)
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(log_level)
        self.logger.propagate = False

        if not self.logger.handlers:
            formatter = logging.Formatter(log_format)
            self._add_console_handler(formatter)
            self._add_file_handler(log_file, formatter)
            self._add_logstash_handler(logstash_host, logstash_port,
                                       logstash_database_path)

    def _add_console_handler(self, formatter):
        """Add console handler to logger."""
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _add_file_handler(self, log_file, formatter):
        """Add file handler to logger if log_file is specified."""
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def _add_logstash_handler(self, logstash_host, logstash_port,
                              logstash_database_path):
        """Add logstash handler to logger if available and configured."""
        if logstash_host and LOGSTASH_AVAILABLE:
            try:
                logstash_handler = AsynchronousLogstashHandler(
                    host=logstash_host,
                    port=logstash_port,
                    database_path=logstash_database_path,
                )
                logstash_handler.setFormatter(LogstashFormatter())
                self.logger.addHandler(logstash_handler)
            except Exception as e:
                self.logger.error(f"Failed to initialize Logstash handler: {e}")

    def get_logger(self):
        return self.logger


logger = Logger().get_logger()
