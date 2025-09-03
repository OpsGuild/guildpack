from typing import Any, Dict, List

try:
    import pydantic

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    pydantic = None

try:
    import marshmallow

    MARSHMALLOW_AVAILABLE = True
except ImportError:
    MARSHMALLOW_AVAILABLE = False
    marshmallow = None

try:
    import cerberus

    CERBERUS_AVAILABLE = True
except ImportError:
    CERBERUS_AVAILABLE = False
    cerberus = None

try:
    import jsonschema

    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    jsonschema = None


class ValidationErrorHandler:
    """Handler for validation-specific errors."""

    def __init__(self, logger):
        self.logger = logger

    def _is_validation_error(self, e: Exception) -> bool:
        """Check if the exception is a validation-related error."""
        if PYDANTIC_AVAILABLE and isinstance(e, pydantic.ValidationError):
            return True
        elif MARSHMALLOW_AVAILABLE and isinstance(
            e, marshmallow.ValidationError
        ):
            return True
        elif CERBERUS_AVAILABLE and isinstance(e, cerberus.ValidationError):
            return True
        elif JSONSCHEMA_AVAILABLE and isinstance(
            e, jsonschema.ValidationError
        ):
            return True
        return False

    def handle_error(self, e: Exception) -> Dict[str, Any]:
        """Handle validation-specific errors and return error details."""
        if PYDANTIC_AVAILABLE and isinstance(e, pydantic.ValidationError):
            return self._handle_pydantic_error(e)
        elif MARSHMALLOW_AVAILABLE and isinstance(
            e, marshmallow.ValidationError
        ):
            return self._handle_marshmallow_error(e)
        elif CERBERUS_AVAILABLE and isinstance(e, cerberus.ValidationError):
            return self._handle_cerberus_error(e)
        elif JSONSCHEMA_AVAILABLE and isinstance(
            e, jsonschema.ValidationError
        ):
            return self._handle_jsonschema_error(e)
        else:
            return {
                "level": "WARNING",
                "http_status_code": 422,
                "message": "Validation error occurred.",
                "error_type": type(e).__name__,
            }

    def _handle_pydantic_error(
        self, e: "pydantic.ValidationError"
    ) -> Dict[str, Any]:
        """Handle Pydantic validation errors."""
        errors = []

        for error in e.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            error_msg = error["msg"]
            error_type = error["type"]

            errors.append(
                {
                    "field": field_path,
                    "message": error_msg,
                    "type": error_type,
                    "input": error.get("input"),
                }
            )

        return {
            "level": "WARNING",
            "http_status_code": 422,
            "message": "Request validation failed.",
            "error_type": "ValidationError",
            "validation_errors": errors,
        }

    def _handle_marshmallow_error(
        self, e: "marshmallow.ValidationError"
    ) -> Dict[str, Any]:
        """Handle Marshmallow validation errors."""
        errors = []

        if isinstance(e.messages, dict):
            for field, messages in e.messages.items():
                if isinstance(messages, list):
                    for message in messages:
                        errors.append(
                            {
                                "field": field,
                                "message": message,
                                "type": "validation_error",
                            }
                        )
                else:
                    errors.append(
                        {
                            "field": field,
                            "message": str(messages),
                            "type": "validation_error",
                        }
                    )
        else:
            errors.append(
                {
                    "field": "general",
                    "message": str(e.messages),
                    "type": "validation_error",
                }
            )

        return {
            "level": "WARNING",
            "http_status_code": 422,
            "message": "Request validation failed.",
            "error_type": "ValidationError",
            "validation_errors": errors,
        }

    def _handle_cerberus_error(
        self, e: "cerberus.ValidationError"
    ) -> Dict[str, Any]:
        """Handle Cerberus validation errors."""
        errors = []

        for field, messages in e.errors.items():
            if isinstance(messages, list):
                for message in messages:
                    errors.append(
                        {
                            "field": field,
                            "message": message,
                            "type": "validation_error",
                        }
                    )
            else:
                errors.append(
                    {
                        "field": field,
                        "message": str(messages),
                        "type": "validation_error",
                    }
                )

        return {
            "level": "WARNING",
            "http_status_code": 422,
            "message": "Request validation failed.",
            "error_type": "ValidationError",
            "validation_errors": errors,
        }

    def _handle_jsonschema_error(
        self, e: "jsonschema.ValidationError"
    ) -> Dict[str, Any]:
        """Handle JSON Schema validation errors."""
        path = (
            " -> ".join(str(p) for p in e.absolute_path)
            if e.absolute_path
            else "root"
        )

        return {
            "level": "WARNING",
            "http_status_code": 422,
            "message": "Request validation failed.",
            "error_type": "ValidationError",
            "validation_errors": [
                {
                    "field": path,
                    "message": e.message,
                    "type": "schema_validation_error",
                    "schema_path": " -> ".join(str(p) for p in e.schema_path),
                }
            ],
        }

    def format_validation_errors(self, errors: List[Dict[str, Any]]) -> str:
        """Format validation errors into a readable string."""
        if not errors:
            return "Validation failed."

        formatted_errors = []
        for error in errors:
            field = error.get("field", "unknown")
            message = error.get("message", "validation error")
            formatted_errors.append(f"{field}: {message}")

        return "; ".join(formatted_errors)
