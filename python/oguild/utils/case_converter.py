"""
Case conversion utilities for converting between different naming conventions.

Supported cases:
- snake_case
- camelCase
- PascalCase (UpperCamelCase)
- kebab-case (dash-case)
- SCREAMING_SNAKE_CASE (CONSTANT_CASE)
- dot.case
- Title Case
"""

import re
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Union


class Case(str, Enum):
    """Enum for supported case types."""
    SNAKE = "snake"
    CAMEL = "camel"
    PASCAL = "pascal"
    KEBAB = "kebab"
    SCREAMING_SNAKE = "screaming_snake"
    DOT = "dot"
    TITLE = "title"


def get_local_datetime() -> datetime:
    """Get the current local datetime with timezone info."""
    return datetime.now().astimezone()


# Individual case conversion functions

def camel_to_snake(name: str) -> str:
    """
    Convert camelCase or PascalCase string to snake_case.

    Examples:
        >>> camel_to_snake("camelCase")
        'camel_case'
        >>> camel_to_snake("PascalCase")
        'pascal_case'
        >>> camel_to_snake("getHTTPResponse")
        'get_http_response'
    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def snake_to_camel(name: str) -> str:
    """
    Convert snake_case string to camelCase.

    Examples:
        >>> snake_to_camel("snake_case")
        'snakeCase'
        >>> snake_to_camel("get_http_response")
        'getHttpResponse'
    """
    components = name.split("_")
    return components[0] + "".join(x.capitalize() for x in components[1:])


def snake_to_pascal(name: str) -> str:
    """
    Convert snake_case string to PascalCase (UpperCamelCase).

    Examples:
        >>> snake_to_pascal("snake_case")
        'SnakeCase'
        >>> snake_to_pascal("get_http_response")
        'GetHttpResponse'
    """
    components = name.split("_")
    return "".join(x.capitalize() for x in components)


def snake_to_kebab(name: str) -> str:
    """
    Convert snake_case string to kebab-case.

    Examples:
        >>> snake_to_kebab("snake_case")
        'snake-case'
    """
    return name.replace("_", "-")


def snake_to_screaming_snake(name: str) -> str:
    """
    Convert snake_case string to SCREAMING_SNAKE_CASE.

    Examples:
        >>> snake_to_screaming_snake("snake_case")
        'SNAKE_CASE'
    """
    return name.upper()


def snake_to_dot(name: str) -> str:
    """
    Convert snake_case string to dot.case.

    Examples:
        >>> snake_to_dot("snake_case")
        'snake.case'
    """
    return name.replace("_", ".")


def snake_to_title(name: str) -> str:
    """
    Convert snake_case string to Title Case.

    Examples:
        >>> snake_to_title("snake_case")
        'Snake Case'
    """
    return " ".join(x.capitalize() for x in name.split("_"))


def kebab_to_snake(name: str) -> str:
    """
    Convert kebab-case string to snake_case.

    Examples:
        >>> kebab_to_snake("kebab-case")
        'kebab_case'
    """
    return name.replace("-", "_")


def pascal_to_snake(name: str) -> str:
    """
    Convert PascalCase string to snake_case.
    Same as camel_to_snake since the logic handles both.

    Examples:
        >>> pascal_to_snake("PascalCase")
        'pascal_case'
    """
    return camel_to_snake(name)


def dot_to_snake(name: str) -> str:
    """
    Convert dot.case string to snake_case.

    Examples:
        >>> dot_to_snake("dot.case")
        'dot_case'
    """
    return name.replace(".", "_")


def screaming_snake_to_snake(name: str) -> str:
    """
    Convert SCREAMING_SNAKE_CASE string to snake_case.

    Examples:
        >>> screaming_snake_to_snake("SCREAMING_SNAKE_CASE")
        'screaming_snake_case'
    """
    return name.lower()


def to_snake(name: str) -> str:
    """
    Convert any common case format to snake_case.
    Auto-detects the input format.

    Examples:
        >>> to_snake("camelCase")
        'camel_case'
        >>> to_snake("PascalCase")
        'pascal_case'
        >>> to_snake("kebab-case")
        'kebab_case'
        >>> to_snake("dot.case")
        'dot_case'
        >>> to_snake("SCREAMING_SNAKE")
        'screaming_snake'
    """
    # Handle kebab-case
    if "-" in name:
        name = name.replace("-", "_")
    # Handle dot.case
    if "." in name:
        name = name.replace(".", "_")
    # Handle SCREAMING_SNAKE (all uppercase with underscores)
    if name.isupper() and "_" in name:
        return name.lower()
    # Handle camelCase and PascalCase
    return camel_to_snake(name)


# Case conversion mapping
_TO_CASE_CONVERTERS: Dict[Case, Callable[[str], str]] = {
    Case.SNAKE: lambda x: x,  # Identity if already snake
    Case.CAMEL: snake_to_camel,
    Case.PASCAL: snake_to_pascal,
    Case.KEBAB: snake_to_kebab,
    Case.SCREAMING_SNAKE: snake_to_screaming_snake,
    Case.DOT: snake_to_dot,
    Case.TITLE: snake_to_title,
}

# Type alias for case parameter
CaseType = Union[Case, str]


def _normalize_case(case: CaseType) -> Case:
    """
    Normalize case input to a Case enum.
    Accepts both Case enum values and strings like 'snake', 'camel', etc.

    Args:
        case: Case enum or string (e.g., 'snake', 'camel', 'pascal', 'kebab')

    Returns:
        Case enum value

    Raises:
        ValueError: If the case string is not recognized
    """
    if isinstance(case, Case):
        return case

    if isinstance(case, str):
        case_lower = case.lower().replace("-", "_").replace(" ", "_")
        try:
            return Case(case_lower)
        except ValueError:
            valid_cases = [c.value for c in Case]
            raise ValueError(
                f"Invalid case '{case}'. Valid options: "
                f"{', '.join(valid_cases)}"
            )

    raise TypeError(
        f"case must be Case enum or string, not {type(case).__name__}"
    )


def convert_case(name: str, to_case: CaseType) -> str:
    """
    Convert a string from any case to the specified case.

    Args:
        name: The string to convert
        to_case: Target case - either Case enum or string (e.g. 'snake',
                  'camel', 'pascal')

    Returns:
        The converted string

    Examples:
        >>> convert_case("camelCase", "snake")
        'camel_case'
        >>> convert_case("snake_case", "camel")
        'snakeCase'
        >>> convert_case("any-format", "pascal")
        'AnyFormat'
        >>> convert_case("hello_world", Case.KEBAB)
        'hello-world'
    """
    target = _normalize_case(to_case)
    # First normalize to snake_case
    snake = to_snake(name)
    # Then convert to target case
    converter = _TO_CASE_CONVERTERS.get(target, lambda x: x)
    return converter(snake)


# Dictionary key conversion functions

def convert_dict_keys(
    data: Dict[str, Any],
    to_case: CaseType,
    convert_values: bool = False
) -> Dict[str, Any]:
    """
    Recursively convert all dictionary keys to the specified case.

    Args:
        data: The dictionary to convert
        to_case: Target case - either Case enum or string (e.g. 'snake',
                  'camel', 'pascal')
        convert_values: If True, also convert string values

    Returns:
        New dictionary with converted keys

    Examples:
        >>> convert_dict_keys({"firstName": "John"}, "snake")
        {'first_name': 'John'}
        >>> convert_dict_keys({"user_name": "Jane"}, "camel")
        {'userName': 'Jane'}
        >>> convert_dict_keys({"firstName": "John"}, "screaming_snake")
        {'FIRST_NAME': 'John'}
    """
    target = _normalize_case(to_case)

    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        new_key = convert_case(str(key), target)

        if isinstance(value, dict):
            result[new_key] = convert_dict_keys(value, target, convert_values)
        elif isinstance(value, list):
            result[new_key] = [
                convert_dict_keys(item, target, convert_values)
                if isinstance(item, dict)
                else (convert_case(item, target)
                      if convert_values and isinstance(item, str) else item)
                for item in value
            ]
        elif convert_values and isinstance(value, str):
            result[new_key] = convert_case(value, target)
        else:
            result[new_key] = value

    return result


def convert_dict_keys_to_snake_case(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively convert all dictionary keys from camelCase to snake_case.
    Convenience function that calls convert_dict_keys with Case.SNAKE.
    """
    return convert_dict_keys(data, Case.SNAKE)


def convert_dict_keys_to_camel_case(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively convert all dictionary keys from snake_case to camelCase,
    also converting values to JSON-serializable format.
    """
    # Import here to avoid circular imports
    from .sanitizer import convert_value

    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        camel_key = snake_to_camel(str(key))
        if isinstance(value, dict):
            result[camel_key] = convert_dict_keys_to_camel_case(value)
        elif isinstance(value, list):
            result[camel_key] = [
                convert_dict_keys_to_camel_case(item)
                if isinstance(item, dict)
                else convert_value(item)
                for item in value
            ]
        else:
            result[camel_key] = convert_value(value)

    return result


# Convenience aliases for converting any case to a specific case

def to_camel_case(name: str) -> str:
    """Convert any case to camelCase."""
    return snake_to_camel(to_snake(name))


def to_pascal_case(name: str) -> str:
    """Convert any case to PascalCase."""
    return snake_to_pascal(to_snake(name))


def to_kebab_case(name: str) -> str:
    """Convert any case to kebab-case."""
    return snake_to_kebab(to_snake(name))


def to_screaming_snake_case(name: str) -> str:
    """Convert any case to SCREAMING_SNAKE_CASE."""
    return snake_to_screaming_snake(to_snake(name))
