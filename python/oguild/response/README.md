# OpsGuild Response Module

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Framework Agnostic](https://img.shields.io/badge/framework-agnostic-green.svg)](https://github.com/OpsGuild/guildpack)

A universal response handling system that provides consistent error handling and response formatting across multiple Python web frameworks including FastAPI, Django, Flask, and Starlette.

## 🚀 Features

- **Framework Agnostic** - Works seamlessly with FastAPI, Django, Flask, Starlette, and more
- **Smart Error Handling** - Automatic error classification and appropriate HTTP status codes
- **Async/Sync Support** - Handles both synchronous and asynchronous functions
- **Comprehensive Error Types** - Specialized handlers for database, validation, authentication, network, and file errors
- **Automatic Logging** - Built-in logging with detailed error information and stack traces
- **Decorator Support** - Easy-to-use `@police` decorator for automatic error handling
- **Type Safety** - Full type hints and modern Python support

## 📦 Installation

```bash
# Using Poetry (recommended)
poetry add oguild

# Using pip
pip install oguild
```

## 🎯 Quick Start

### Basic Usage

```python
from oguild.response import Ok, Error, police

# Success response
def get_user(user_id: int):
    user = {"id": user_id, "name": "John Doe"}
    return Ok(200, "User retrieved successfully", user)

# Error handling
def get_user_with_error(user_id: int):
    try:
        user = fetch_user(user_id)  # This might fail
        return Ok(200, "User retrieved successfully", user)
    except Exception as e:
        raise Error(e, "Failed to retrieve user", 404)

# Using the police decorator
@police(default_msg="Failed to process request", default_code=500)
def process_data(data):
    # Your function logic here
    return processed_data
```

### Framework Integration

The response system automatically detects and integrates with your web framework:

```python
# FastAPI
from fastapi import FastAPI
from oguild.response import Ok, Error

app = FastAPI()

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    try:
        user = await fetch_user(user_id)
        return Ok(200, "User found", user)()
    except Exception as e:
        raise Error(e, "User not found", 404)

# Django
from django.http import JsonResponse
from oguild.response import Ok, Error

def get_user(request, user_id):
    try:
        user = fetch_user(user_id)
        return Ok(200, "User found", user).to_framework_response()
    except Exception as e:
        raise Error(e, "User not found", 404)

# Flask
from flask import Flask
from oguild.response import Ok, Error

app = Flask(__name__)

@app.route("/users/<int:user_id>")
def get_user(user_id):
    try:
        user = fetch_user(user_id)
        return Ok(200, "User found", user).to_framework_response()
    except Exception as e:
        raise Error(e, "User not found", 404)
```

## 🔧 API Reference

### Ok Class

Universal success response class that works across all frameworks.

```python
Ok(
    status_code: int = 200,
    message: str = "Success", 
    response_dict: Optional[Dict[str, Any]] = None,
    **kwargs: Any
)
```

**Methods:**
- `to_framework_response()` - Convert to framework-specific response
- `__call__()` - Auto-detect sync/async context and return appropriate response
- `__await__()` - Async context support

### Error Class

Comprehensive error handling with automatic classification.

```python
Error(
    e: Optional[Exception] = None,
    msg: Optional[str] = None,
    code: Optional[int] = None,
    level: Optional[str] = None,
    additional_info: Optional[dict] = None
)
```

**Methods:**
- `to_dict()` - Convert error to dictionary with logging
- `to_framework_exception()` - Convert to framework-specific exception
- `__call__()` - Raise framework-specific exception
- `__await__()` - Async context support

### Police Decorator

Automatic error handling decorator for functions.

```python
@police(default_msg: Optional[str] = None, default_code: Optional[int] = None)
def your_function():
    # Your function logic
    pass
```

## 🛡️ Error Handlers

The response system includes specialized error handlers for different types of errors:

### CommonErrorHandler
Handles standard Python exceptions and framework-specific errors:
- `ValueError` → 400 Bad Request
- `TypeError` → 400 Bad Request  
- `KeyError` → 400 Bad Request
- `PermissionError` → 403 Forbidden
- `FileNotFoundError` → 404 Not Found
- `TimeoutError` → 408 Request Timeout
- `ConnectionError` → 503 Service Unavailable

### DatabaseErrorHandler
Handles database-related errors:
- SQLAlchemy exceptions
- Database connection errors
- Query execution errors

### ValidationErrorHandler
Handles data validation errors:
- Pydantic validation errors
- Schema validation errors
- Input validation errors

### AuthenticationErrorHandler
Handles authentication and authorization errors:
- JWT token errors
- Permission denied errors
- Authentication failures

### NetworkErrorHandler
Handles network-related errors:
- HTTP request errors
- API communication errors
- Network connectivity issues

### FileErrorHandler
Handles file system errors:
- File I/O errors
- File permission errors
- File format errors

## 📝 Examples

### Advanced Error Handling

```python
from oguild.response import Error, police

@police(default_msg="Database operation failed", default_code=500)
async def create_user(user_data: dict):
    try:
        # Database operation that might fail
        user = await db.users.create(user_data)
        return user
    except ValidationError as e:
        # This will be handled by ValidationErrorHandler
        raise Error(e, "Invalid user data", 400)
    except DatabaseError as e:
        # This will be handled by DatabaseErrorHandler  
        raise Error(e, "Database error occurred", 500)
```

### Custom Error Information

```python
from oguild.response import Error

def process_payment(amount: float):
    try:
        result = payment_service.charge(amount)
        return result
    except PaymentError as e:
        raise Error(
            e,
            "Payment processing failed",
            402,  # Payment Required
            level="WARNING",
            additional_info={
                "amount": amount,
                "payment_method": "credit_card",
                "retry_after": 300
            }
        )
```

### Async Function Support

```python
from oguild.response import Ok, Error, police

@police(default_msg="Async operation failed")
async def fetch_user_data(user_id: int):
    try:
        user = await user_service.get_user(user_id)
        profile = await profile_service.get_profile(user_id)
        
        return Ok(200, "User data retrieved", {
            "user": user,
            "profile": profile
        })
    except UserNotFoundError as e:
        raise Error(e, "User not found", 404)
```

## 🔍 Logging

The response system automatically logs errors with detailed information:

```python
# Error logging includes:
# - Error message and type
# - HTTP status code
# - Stack trace
# - Exception attributes
# - Additional context information
```

## 🧪 Testing

```python
import pytest
from oguild.response import Ok, Error

def test_success_response():
    response = Ok(200, "Success", {"data": "test"})
    assert response.status_code == 200
    assert response.payload["message"] == "Success"
    assert response.payload["data"] == "test"

def test_error_response():
    try:
        raise ValueError("Test error")
    except ValueError as e:
        error = Error(e, "Test failed", 400)
        error_dict = error.to_dict()
        assert error_dict["status_code"] == 400
        assert "Test failed" in error_dict["message"]
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](../../../README.md#contributing) for details.

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](../../../LICENSE) file for details.

---

**Made with ❤️ by the OpsGuild team**
