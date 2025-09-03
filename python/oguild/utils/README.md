# OpsGuild Utils Module

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Async Support](https://img.shields.io/badge/async-supported-green.svg)](https://github.com/OpsGuild/guildpack)

A collection of utility functions for data processing, encoding, decoding, and sanitization in Python applications. Designed to work seamlessly with both synchronous and asynchronous code.

## 🚀 Features

- **JSON Field Processing** - Encode and decode JSON fields in data structures
- **Data Sanitization** - Clean and normalize data with customizable rules
- **Async Support** - All functions support async/await patterns
- **Type Safety** - Full type hints and modern Python support
- **Flexible Configuration** - Customizable field processors and mapping rules
- **Pydantic Integration** - Works seamlessly with Pydantic models
- **Error Handling** - Robust error handling with detailed logging

## 📦 Installation

```bash
# Using Poetry (recommended)
poetry add oguild

# Using pip
pip install oguild
```

## 🎯 Quick Start

### JSON Field Processing

```python
from oguild.utils import encode_json_fields, decode_json_fields

# Encode dictionary/list fields to JSON strings
data = [
    {"id": 1, "metadata": {"key": "value"}, "tags": ["tag1", "tag2"]},
    {"id": 2, "metadata": {"key2": "value2"}, "tags": ["tag3"]}
]

# Encode specific fields to JSON strings
encoded_data = await encode_json_fields(data, ["metadata", "tags"])
# Result: [{"id": 1, "metadata": '{"key": "value"}', "tags": '["tag1", "tag2"]'}, ...]

# Decode JSON strings back to objects
decoded_data = await decode_json_fields(encoded_data, ["metadata", "tags"])
# Result: [{"id": 1, "metadata": {"key": "value"}, "tags": ["tag1", "tag2"]}, ...]
```

### Data Sanitization

```python
from oguild.utils import sanitize_fields
from pydantic import BaseModel

# Basic sanitization
data = {
    "id": 1,
    "name": "John Doe",
    "email": "",
    "age": None,
    "metadata": {"key": "value", "empty": ""}
}

sanitized = await sanitize_fields(data)
# Result: {"id": 1, "name": "John Doe", "metadata": {"key": "value"}}
# Empty values (None, "") are removed by default

# Custom sanitization with field mapping
custom_sanitized = await sanitize_fields(
    data,
    empty_values={None, "", "N/A"},
    key_mapping={"_id": "id", "user_name": "name"}
)
```

## 🔧 API Reference

### encode_json_fields

Serializes specified dictionary fields into JSON strings.

```python
async def encode_json_fields(
    rows: Union[list, dict], 
    json_keys: list[str]
) -> Union[list, dict]
```

**Parameters:**
- `rows` - List of dictionaries or single dictionary to process
- `json_keys` - List of field names to encode as JSON strings

**Returns:**
- Processed data with specified fields encoded as JSON strings

**Example:**
```python
data = {"id": 1, "config": {"setting": "value"}}
result = await encode_json_fields(data, ["config"])
# Result: {"id": 1, "config": '{"setting": "value"}'}
```

### decode_json_fields

Parses specified JSON fields in each row of the result set.

```python
async def decode_json_fields(
    rows: list, 
    json_keys: list[str]
) -> list
```

**Parameters:**
- `rows` - List of dictionaries to process
- `json_keys` - List of field names to decode from JSON strings

**Returns:**
- List of dictionaries with specified fields decoded from JSON

**Example:**
```python
data = [{"id": 1, "config": '{"setting": "value"}'}]
result = await decode_json_fields(data, ["config"])
# Result: [{"id": 1, "config": {"setting": "value"}}]
```

### sanitize_fields

Cleans and normalizes data structures with customizable rules.

```python
async def sanitize_fields(
    data: Any,
    empty_values: set = DEFAULT_EMPTY_VALUES,
    key_mapping: dict = DEFAULT_KEY_MAPPING,
    field_processors: dict = DEFAULT_FIELD_PROCESSORS
) -> Any
```

**Parameters:**
- `data` - Data to sanitize (dict, list, Pydantic model, or primitive)
- `empty_values` - Set of values to consider as empty and remove
- `key_mapping` - Dictionary mapping old keys to new keys
- `field_processors` - Dictionary of field-specific processing functions

**Returns:**
- Sanitized data with the same structure

**Default Values:**
- `DEFAULT_EMPTY_VALUES = {None, ""}`
- `DEFAULT_KEY_MAPPING = {"_id": "id"}`
- `DEFAULT_FIELD_PROCESSORS = {}`

## 📝 Examples

### Advanced Data Sanitization

```python
from oguild.utils import sanitize_fields
from datetime import datetime
from decimal import Decimal
from uuid import UUID

# Complex data structure
data = {
    "_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_name": "John Doe",
    "email": "",
    "age": None,
    "balance": Decimal("123.45"),
    "created_at": datetime.now(),
    "metadata": {
        "last_login": None,
        "preferences": {"theme": "dark", "notifications": ""}
    },
    "tags": ["", "important", None, "urgent"]
}

# Custom field processors
def process_balance(value):
    return float(value) if value else 0.0

def process_tags(value):
    return [tag for tag in value if tag and tag.strip()]

# Sanitize with custom rules
sanitized = await sanitize_fields(
    data,
    empty_values={None, "", "N/A", "null"},
    key_mapping={
        "_id": "id",
        "user_name": "name"
    },
    field_processors={
        "balance": process_balance,
        "tags": process_tags
    }
)

# Result:
# {
#     "id": "123e4567-e89b-12d3-a456-426614174000",
#     "name": "John Doe", 
#     "balance": 123.45,
#     "created_at": "2024-01-15T10:30:00",
#     "metadata": {
#         "preferences": {"theme": "dark"}
#     },
#     "tags": ["important", "urgent"]
# }
```

### Pydantic Model Integration

```python
from pydantic import BaseModel
from oguild.utils import sanitize_fields

class User(BaseModel):
    id: int
    name: str
    email: str = ""
    metadata: dict = {}

# Pydantic model sanitization
user = User(id=1, name="John", email="", metadata={"key": "value", "empty": ""})
sanitized_user = await sanitize_fields(user)

# Result: {"id": 1, "name": "John", "metadata": {"key": "value"}}
```

### Database Result Processing

```python
from oguild.utils import encode_json_fields, decode_json_fields

# Simulate database results with JSON fields
db_results = [
    {
        "id": 1,
        "user_id": 123,
        "settings": {"theme": "dark", "notifications": True},
        "tags": ["admin", "premium"]
    },
    {
        "id": 2, 
        "user_id": 456,
        "settings": {"theme": "light", "notifications": False},
        "tags": ["user"]
    }
]

# Encode for database storage
encoded_results = await encode_json_fields(db_results, ["settings", "tags"])

# Store in database...
# Retrieve from database...

# Decode for application use
decoded_results = await decode_json_fields(encoded_results, ["settings", "tags"])
```

### Error Handling

```python
from oguild.utils import encode_json_fields
import json

# Handle encoding errors gracefully
data = {"id": 1, "invalid_json": {"circular": None}}
data["invalid_json"]["circular"] = data["invalid_json"]  # Create circular reference

try:
    result = await encode_json_fields(data, ["invalid_json"])
    # Error is logged but processing continues
except Exception as e:
    print(f"Encoding failed: {e}")
```

## 🛠️ Configuration

### Custom Field Processors

```python
from oguild.utils import sanitize_fields

def process_email(value):
    """Normalize email addresses."""
    if not value:
        return None
    return value.lower().strip()

def process_phone(value):
    """Format phone numbers."""
    if not value:
        return None
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, value))
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return value

# Use custom processors
sanitized = await sanitize_fields(
    data,
    field_processors={
        "email": process_email,
        "phone": process_phone
    }
)
```

### Custom Empty Values

```python
from oguild.utils import sanitize_fields

# Define custom empty values
custom_empty_values = {None, "", "N/A", "null", "undefined", 0, False}

sanitized = await sanitize_fields(
    data,
    empty_values=custom_empty_values
)
```

## 🧪 Testing

```python
import pytest
from oguild.utils import encode_json_fields, decode_json_fields, sanitize_fields

@pytest.mark.asyncio
async def test_encode_json_fields():
    data = {"id": 1, "config": {"key": "value"}}
    result = await encode_json_fields(data, ["config"])
    assert result["config"] == '{"key": "value"}'

@pytest.mark.asyncio
async def test_decode_json_fields():
    data = [{"id": 1, "config": '{"key": "value"}'}]
    result = await decode_json_fields(data, ["config"])
    assert result[0]["config"] == {"key": "value"}

@pytest.mark.asyncio
async def test_sanitize_fields():
    data = {"id": 1, "name": "John", "email": ""}
    result = await sanitize_fields(data)
    assert "email" not in result
    assert result["name"] == "John"
```

## 🔍 Logging

The utils module integrates with the OpsGuild logging system:

```python
# Errors during JSON encoding/decoding are automatically logged
# Sanitization errors are logged with context information
# All operations include debug-level logging for troubleshooting
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](../../../README.md#contributing) for details.

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](../../../LICENSE) file for details.

---

**Made with ❤️ by the OpsGuild team**
