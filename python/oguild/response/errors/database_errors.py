import re
from typing import Any, Dict

try:
    import asyncpg

    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    asyncpg = None

try:
    import psycopg2

    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    psycopg2 = None

try:
    import sqlite3

    SQLITE3_AVAILABLE = True
except ImportError:
    SQLITE3_AVAILABLE = False
    sqlite3 = None

try:
    import pymongo

    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    pymongo = None

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class DatabaseErrorHandler:
    """Handler for database-specific errors."""

    def __init__(self, logger):
        self.logger = logger

    def _is_database_error(self, e: Exception) -> bool:
        """Check if the exception is a database-related error."""
        if ASYNCPG_AVAILABLE and isinstance(e, asyncpg.PostgresError):
            return True
        elif PSYCOPG2_AVAILABLE and isinstance(e, psycopg2.Error):
            return True
        elif SQLITE3_AVAILABLE and isinstance(e, sqlite3.Error):
            return True
        elif PYMONGO_AVAILABLE and isinstance(e, pymongo.errors.PyMongoError):
            return True
        elif REDIS_AVAILABLE and isinstance(e, redis.RedisError):
            return True
        return False

    def handle_error(self, e: Exception) -> Dict[str, Any]:
        """Handle database-specific errors and return error details."""
        if ASYNCPG_AVAILABLE and isinstance(e, asyncpg.PostgresError):
            return self._handle_asyncpg_error(e)
        elif PSYCOPG2_AVAILABLE and isinstance(e, psycopg2.Error):
            return self._handle_psycopg2_error(e)
        elif SQLITE3_AVAILABLE and isinstance(e, sqlite3.Error):
            return self._handle_sqlite3_error(e)
        elif PYMONGO_AVAILABLE and isinstance(e, pymongo.errors.PyMongoError):
            return self._handle_pymongo_error(e)
        elif REDIS_AVAILABLE and isinstance(e, redis.RedisError):
            return self._handle_redis_error(e)
        else:
            return {
                "level": "ERROR",
                "http_status_code": 500,
                "message": "Database error occurred.",
                "error_type": type(e).__name__,
            }

    def _handle_asyncpg_error(
        self, e: "asyncpg.PostgresError"
    ) -> Dict[str, Any]:
        """Handle AsyncPG PostgreSQL errors."""
        error_info = {
            "level": getattr(e, "severity", "ERROR"),
            "http_status_code": 500,
            "message": "Database error occurred.",
            "error_type": type(e).__name__,
        }

        if isinstance(e, asyncpg.exceptions.UniqueViolationError):
            error_info.update(self._handle_unique_violation(e))
        elif isinstance(e, asyncpg.exceptions.ForeignKeyViolationError):
            error_info.update(self._handle_foreign_key_violation(e))
        elif isinstance(e, asyncpg.exceptions.CheckViolationError):
            error_info.update(self._handle_check_violation(e))
        elif isinstance(e, asyncpg.exceptions.NotNullViolationError):
            error_info.update(self._handle_not_null_violation(e))
        elif isinstance(e, asyncpg.exceptions.UndefinedColumnError):
            error_info.update(self._handle_undefined_column(e))
        elif isinstance(e, asyncpg.exceptions.DataError):
            error_info.update(self._handle_data_error(e))
        elif isinstance(e, asyncpg.exceptions.InvalidTextRepresentationError):
            error_info.update(
                {
                    "http_status_code": 400,
                    "message": "Invalid input syntax for a field.",
                }
            )
        elif isinstance(e, asyncpg.exceptions.PostgresSyntaxError):
            error_info.update(
                {
                    "http_status_code": 500,
                    "message": "Something went wrong while processing your request.",
                }
            )
        elif isinstance(e, asyncpg.exceptions.NumericValueOutOfRangeError):
            error_info.update(
                {
                    "http_status_code": 400,
                    "message": "A numeric value is out of range.",
                }
            )
        elif isinstance(e, asyncpg.exceptions.DivisionByZeroError):
            error_info.update(
                {
                    "http_status_code": 400,
                    "message": "Attempted division by zero.",
                }
            )
        elif isinstance(e, asyncpg.exceptions.StringDataRightTruncationError):
            error_info.update(
                {
                    "http_status_code": 400,
                    "message": "Input string is too long for the column.",
                }
            )
        elif isinstance(e, asyncpg.exceptions.InvalidDatetimeFormatError):
            error_info.update(
                {
                    "http_status_code": 400,
                    "message": "Invalid datetime format.",
                }
            )
        elif isinstance(e, asyncpg.exceptions.ConnectionDoesNotExistError):
            error_info.update(
                {
                    "http_status_code": 503,
                    "message": "Database connection is not available.",
                }
            )
        elif isinstance(e, asyncpg.exceptions.ConnectionFailureError):
            error_info.update(
                {
                    "http_status_code": 503,
                    "message": "Failed to connect to the database.",
                }
            )

        return error_info

    def _handle_psycopg2_error(self, e: "psycopg2.Error") -> Dict[str, Any]:
        """Handle psycopg2 PostgreSQL errors."""
        error_info = {
            "level": "ERROR",
            "http_status_code": 500,
            "message": "Database error occurred.",
            "error_type": type(e).__name__,
        }

        if isinstance(e, psycopg2.IntegrityError):
            error_info.update(
                {
                    "http_status_code": 409,
                    "message": "Data integrity constraint violation.",
                }
            )
        elif isinstance(e, psycopg2.OperationalError):
            error_info.update(
                {
                    "http_status_code": 503,
                    "message": "Database operation failed.",
                }
            )
        elif isinstance(e, psycopg2.ProgrammingError):
            error_info.update(
                {
                    "http_status_code": 500,
                    "message": "Database programming error.",
                }
            )
        elif isinstance(e, psycopg2.DataError):
            error_info.update(
                {
                    "http_status_code": 400,
                    "message": "Invalid data provided.",
                }
            )

        return error_info

    def _handle_sqlite3_error(self, e: "sqlite3.Error") -> Dict[str, Any]:
        """Handle SQLite3 errors."""
        error_info = {
            "level": "ERROR",
            "http_status_code": 500,
            "message": "Database error occurred.",
            "error_type": type(e).__name__,
        }

        if isinstance(e, sqlite3.IntegrityError):
            error_info.update(
                {
                    "http_status_code": 409,
                    "message": "Data integrity constraint violation.",
                }
            )
        elif isinstance(e, sqlite3.OperationalError):
            error_info.update(
                {
                    "http_status_code": 503,
                    "message": "Database operation failed.",
                }
            )
        elif isinstance(e, sqlite3.ProgrammingError):
            error_info.update(
                {
                    "http_status_code": 500,
                    "message": "Database programming error.",
                }
            )
        elif isinstance(e, sqlite3.DataError):
            error_info.update(
                {
                    "http_status_code": 400,
                    "message": "Invalid data provided.",
                }
            )

        return error_info

    def _handle_pymongo_error(
        self, e: "pymongo.errors.PyMongoError"
    ) -> Dict[str, Any]:
        """Handle PyMongo MongoDB errors."""
        error_info = {
            "level": "ERROR",
            "http_status_code": 500,
            "message": "Database error occurred.",
            "error_type": type(e).__name__,
        }

        if isinstance(e, pymongo.errors.DuplicateKeyError):
            error_info.update(
                {
                    "http_status_code": 409,
                    "message": "Document with this key already exists.",
                }
            )
        elif isinstance(e, pymongo.errors.ConnectionFailure):
            error_info.update(
                {
                    "http_status_code": 503,
                    "message": "Failed to connect to the database.",
                }
            )
        elif isinstance(e, pymongo.errors.OperationFailure):
            error_info.update(
                {
                    "http_status_code": 500,
                    "message": "Database operation failed.",
                }
            )
        elif isinstance(e, pymongo.errors.ValidationError):
            error_info.update(
                {
                    "http_status_code": 400,
                    "message": "Document validation failed.",
                }
            )

        return error_info

    def _handle_redis_error(self, e: "redis.RedisError") -> Dict[str, Any]:
        """Handle Redis errors."""
        error_info = {
            "level": "ERROR",
            "http_status_code": 503,
            "message": "Cache service error occurred.",
            "error_type": type(e).__name__,
        }

        if isinstance(e, redis.ConnectionError):
            error_info.update(
                {
                    "message": "Failed to connect to cache service.",
                }
            )
        elif isinstance(e, redis.TimeoutError):
            error_info.update(
                {
                    "http_status_code": 408,
                    "message": "Cache operation timeout.",
                }
            )
        elif isinstance(e, redis.DataError):
            error_info.update(
                {
                    "http_status_code": 400,
                    "message": "Invalid data for cache operation.",
                }
            )

        return error_info

    def _handle_unique_violation(
        self, e: "asyncpg.exceptions.UniqueViolationError"
    ) -> Dict[str, Any]:
        """Handle unique constraint violations."""
        constraint = getattr(e, "constraint_name", None)
        if constraint:
            parts = constraint.split("_")
            if len(parts) >= 3:
                column = parts[1].replace("_", " ").capitalize()
                return {
                    "http_status_code": 409,
                    "message": f"{column} already exists.",
                }
            else:
                return {
                    "http_status_code": 409,
                    "message": "Resource already exists.",
                }
        else:
            return {
                "http_status_code": 409,
                "message": "Resource already exists.",
            }

    def _handle_foreign_key_violation(
        self, e: "asyncpg.exceptions.ForeignKeyViolationError"
    ) -> Dict[str, Any]:
        """Handle foreign key constraint violations."""
        constraint = getattr(e, "constraint_name", None)
        if constraint:
            parts = constraint.split("_")
            if len(parts) > 2:
                middle_parts = [p for p in parts[1:-1] if p != "id"]
                if middle_parts:
                    field = " ".join(middle_parts).replace("_", " ")
                    return {
                        "http_status_code": 400,
                        "message": f"Selected {field} does not exist.",
                    }
                else:
                    return {
                        "http_status_code": 400,
                        "message": "Invalid foreign key reference.",
                    }
            elif constraint.startswith("fk_") and len(parts) == 2:
                field = constraint[3:].replace("_", " ")
                return {
                    "http_status_code": 400,
                    "message": f"Selected {field} does not exist.",
                }
            else:
                return {
                    "http_status_code": 400,
                    "message": "Invalid foreign key reference.",
                }
        else:
            return {
                "http_status_code": 400,
                "message": "Foreign key constraint failed.",
            }

    def _handle_check_violation(
        self, e: "asyncpg.exceptions.CheckViolationError"
    ) -> Dict[str, Any]:
        """Handle check constraint violations."""
        constraint = getattr(e, "constraint_name", None)
        if constraint:
            parts = constraint.split("_")
            if len(parts) >= 2:
                field = parts[1].replace("_", " ")
                return {
                    "http_status_code": 400,
                    "message": f"Invalid value for {field}.",
                }
            else:
                return {
                    "http_status_code": 400,
                    "message": "Check constraint failed.",
                }
        else:
            return {
                "http_status_code": 400,
                "message": "Check constraint failed.",
            }

    def _handle_not_null_violation(
        self, e: "asyncpg.exceptions.NotNullViolationError"
    ) -> Dict[str, Any]:
        """Handle not null constraint violations."""
        column = getattr(e, "column_name", None)
        if column:
            return {
                "http_status_code": 400,
                "message": f"{column.replace('_', ' ').capitalize()} is required.",
            }
        else:
            return {
                "http_status_code": 400,
                "message": "A required field is missing.",
            }

    def _handle_undefined_column(
        self, e: "asyncpg.exceptions.UndefinedColumnError"
    ) -> Dict[str, Any]:
        """Handle undefined column errors."""
        column = None
        if e.args and len(e.args) > 0:
            msg = e.args[0]
            match = re.search(r'column "(?P<col>[^"]+)" does not exist', msg)
            if match:
                column = match.group("col")

        if column:
            column_fmt = column.replace("_", " ")
            return {
                "http_status_code": 500,
                "message": f"{column_fmt.capitalize()} field does not exist.",
            }
        else:
            return {
                "http_status_code": 500,
                "message": "Invalid column reference.",
            }

    def _handle_data_error(
        self, e: "asyncpg.exceptions.DataError"
    ) -> Dict[str, Any]:
        """Handle data-related errors."""
        original_msg = str(e.args[0]).lower() if e.args else str(e).lower()

        if "out of range" in original_msg:
            return {
                "http_status_code": 400,
                "message": "Provided value is out of allowed range.",
            }
        elif "invalid input syntax" in original_msg:
            return {
                "http_status_code": 400,
                "message": "Invalid input syntax for a field.",
            }
        elif "invalid input value for enum" in original_msg:
            return {
                "http_status_code": 400,
                "message": "Invalid value provided for enum field.",
            }
        elif "invalid uuid" in original_msg:
            return {
                "http_status_code": 400,
                "message": "Invalid ID format provided.",
            }
        else:
            return {
                "http_status_code": 400,
                "message": "Invalid data provided.",
            }
