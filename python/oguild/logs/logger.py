import ast
import json
import logging
import os
import re
import uuid


class SmartLogger(logging.Logger):
    uuid_pattern = re.compile(r"UUID\(['\"]([0-9a-fA-F\-]+)['\"]\)")

    def _pretty_format(self, msg):
        if isinstance(msg, str):
            cleaned = self.uuid_pattern.sub(r'"\1"', msg)

            # Try to locate and replace *every* JSON-like dict/list structure
            # in the string
            def replace_all_json_structures(text):
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

                def try_parse_and_pretty(m):
                    raw = m.group(0)
                    try:
                        parsed = ast.literal_eval(raw)
                        pretty = json.dumps(
                            parsed, indent=2, ensure_ascii=False
                        )
                        return pretty
                    except Exception:
                        return raw

                return re.sub(pattern, try_parse_and_pretty, text)

            return replace_all_json_structures(cleaned)

        elif isinstance(msg, (dict, list)):

            def sanitize(obj):
                if isinstance(obj, dict):
                    return {
                        k: sanitize(str(v) if isinstance(v, uuid.UUID) else v)
                        for k, v in obj.items()
                    }
                elif isinstance(obj, list):
                    return [sanitize(v) for v in obj]
                else:
                    return str(obj) if isinstance(obj, uuid.UUID) else obj

            try:
                return json.dumps(sanitize(msg), indent=2, ensure_ascii=False)
            except Exception:
                return str(msg)

        return str(msg)

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
    """Logger setup that supports per-call formatting"""

    def __init__(
        self,
        logger_name: str,
        log_file: str = "/logs/app.log",
        log_level: int = getattr(
            logging, os.getenv("LOG_LEVEL", "INFO").upper()
        ),
    ):
        logging.setLoggerClass(SmartLogger)
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(log_level)
        self.logger.propagate = False

        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        if not self.logger.handlers:
            formatter = logging.Formatter(
                "\n%(levelname)s: (%(name)s) == %(message)s [%(asctime)s]"
            )

            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger
