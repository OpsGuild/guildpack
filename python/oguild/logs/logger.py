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


# Internal storage for runtime-configured log level
_CONFIGURED_LOG_LEVEL = None


def get_default_log_level():
    """Get the effective default log level (configured or from environment)."""
    if _CONFIGURED_LOG_LEVEL is not None:
        return _CONFIGURED_LOG_LEVEL
    return getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper())


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
        """Replace JSON-like structures with pretty-printed versions."""
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
                k: self._sanitize_for_json(
                    str(v) if isinstance(v, uuid.UUID) else v
                )
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
        if self.isEnabledFor(logging.INFO):
            self._log_with_format_option(
                logging.INFO, msg, args, format=format, **kwargs
            )

    def debug(self, msg, *args, format=False, **kwargs):
        if self.isEnabledFor(logging.DEBUG):
            self._log_with_format_option(
                logging.DEBUG, msg, args, format=format, **kwargs
            )

    def warning(self, msg, *args, format=False, **kwargs):
        if self.isEnabledFor(logging.WARNING):
            self._log_with_format_option(
                logging.WARNING, msg, args, format=format, **kwargs
            )

    def error(self, msg, *args, format=False, **kwargs):
        if self.isEnabledFor(logging.ERROR):
            self._log_with_format_option(
                logging.ERROR, msg, args, format=format, **kwargs
            )

    def critical(self, msg, *args, format=False, **kwargs):
        if self.isEnabledFor(logging.CRITICAL):
            self._log_with_format_option(
                logging.CRITICAL, msg, args, format=format, **kwargs
            )


class _DynamicLoggerWrapper:
    """
    Internal wrapper that dynamically detects the calling module at log time.
    Used by Logger when logger_name is None.
    """

    def __init__(
        self,
        log_file: str = None,
        log_level: int = None,
        log_format: str = "\n%(levelname)s: (%(name)s) == %(message)s "
        " [%(asctime)s]",
        logstash_host: str = None,
        logstash_port: int = None,
        logstash_database_path: str = None,
    ):
        self._log_file = log_file
        self._log_level = log_level  # Can be None to use effective default
        self._log_format = log_format
        self._logstash_host = logstash_host
        self._logstash_port = logstash_port
        self._logstash_database_path = logstash_database_path
        self._loggers = {}  # Cache of loggers by module name

    def _get_caller_module_name(self):
        """Auto-detect the calling module from the stack."""
        # Modules to ignore when detecting the caller
        ignore_modules = (
            "oguild.logs", "oguild.log", "oguild", "logging",
            "_pytest", "pytest", "unittest", "pluggy"
        )

        for frame_info in inspect.stack():
            frame = frame_info.frame
            module_name = frame.f_globals.get("__name__")
            if module_name and not any(
                module_name.startswith(m) for m in ignore_modules
            ):
                return module_name
        return "__main__"

    def _get_or_create_logger(self, module_name):
        """Get existing logger or create a new one for the module."""
        if module_name not in self._loggers:
            logging.setLoggerClass(SmartLogger)
            log = logging.getLogger(module_name)
            log.setLevel(self._get_log_level(self._log_level))
            log.propagate = False

            if not log.handlers:
                formatter = logging.Formatter(self._log_format)

                # Console handler
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(formatter)
                log.addHandler(console_handler)

                # File handler
                if self._log_file:
                    os.makedirs(os.path.dirname(self._log_file), exist_ok=True)
                    file_handler = logging.FileHandler(self._log_file)
                    file_handler.setFormatter(formatter)
                    log.addHandler(file_handler)

                # Logstash handler
                if self._logstash_host and LOGSTASH_AVAILABLE:
                    try:
                        logstash_handler = AsynchronousLogstashHandler(
                            host=self._logstash_host,
                            port=self._logstash_port,
                            database_path=self._logstash_database_path,
                        )
                        logstash_handler.setFormatter(LogstashFormatter())
                        log.addHandler(logstash_handler)
                    except Exception as e:
                        log.error(
                            f"Failed to initialize Logstash handler: {e}"
                        )

            self._loggers[module_name] = log

        return self._loggers[module_name]

    def _log(self, level, msg, *args, **kwargs):
        """Internal method to log with dynamic detection."""
        module_name = self._get_caller_module_name()
        log = self._get_or_create_logger(module_name)
        getattr(log, level)(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log("info", msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self._log("debug", msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log("warning", msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log("error", msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._log("critical", msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self._log("exception", msg, *args, **kwargs)

    def _get_log_level(self, log_level):
        """Get log level from parameter or global default."""
        if log_level is None:
            return get_default_log_level()
        return log_level

    def setLevel(self, level):
        """Update log level for all cached loggers and the global default."""
        global _CONFIGURED_LOG_LEVEL
        _CONFIGURED_LOG_LEVEL = level
        self._log_level = level
        for log in self._loggers.values():
            log.setLevel(level)


class Logger:
    """
    Logger class with automatic module detection when logger_name is None.

    Usage:
        # Dynamic detection (detects caller module at each log call):
        logger = Logger().get_logger()

        # Fixed name (traditional behavior):
        logger = Logger(logger_name="my_app").get_logger()
    """

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
        self._logger_name = logger_name
        self._logstash_port = self._validate_logstash_port(logstash_port)
        self._log_level = self._get_log_level(log_level)
        self._log_file = log_file
        self._log_format = log_format
        self._logstash_host = logstash_host
        self._logstash_database_path = logstash_database_path

        # Only setup fixed logger if name is provided
        if logger_name is not None:
            self._setup_logger(
                logger_name, self._log_level, log_format, log_file,
                logstash_host, self._logstash_port, logstash_database_path
            )
            self._dynamic_wrapper = None
        else:
            self.logger = None
            self._dynamic_wrapper = _DynamicLoggerWrapper(
                log_file=log_file,
                log_level=self._log_level,
                log_format=log_format,
                logstash_host=logstash_host,
                logstash_port=self._logstash_port,
                logstash_database_path=logstash_database_path,
            )

    def _validate_logstash_port(self, port):
        """Validate and convert logstash port to integer."""
        if port is None:
            return None
        try:
            return int(port)
        except ValueError:
            raise ValueError(f"Invalid logstash_port: {port}")

    def _get_log_level(self, log_level):
        """Get log level from parameter or global default."""
        if log_level is None:
            return get_default_log_level()
        return log_level

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
                self.logger.error(
                    f"Failed to initialize Logstash handler: {e}"
                )

    def get_logger(self):
        """
        Returns the logger instance.

        - If logger_name was provided: returns standard Logger
        - If logger_name is None: returns dynamic wrapper
        """
        if self._dynamic_wrapper is not None:
            return self._dynamic_wrapper
        return self.logger

    def info(self, msg, *args, **kwargs):
        """Proxy info logging to the underlying logger."""
        return self.get_logger().info(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        """Proxy debug logging to the underlying logger."""
        return self.get_logger().debug(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Proxy warning logging to the underlying logger."""
        return self.get_logger().warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """Proxy error logging to the underlying logger."""
        return self.get_logger().error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """Proxy critical logging to the underlying logger."""
        return self.get_logger().critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        """Proxy exception logging to the underlying logger."""
        return self.get_logger().exception(msg, *args, **kwargs)

    def setLevel(self, level):
        """Proxy setLevel to the underlying logger."""
        return self.get_logger().setLevel(level)


# Default logger instance with dynamic module detection
logger = Logger().get_logger()
