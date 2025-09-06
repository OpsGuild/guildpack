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
    return Ok("User retrieved successfully", user, status_code=200)

# Error handling - both patterns work
def get_user_with_error(user_id: int):
    try:
        user = fetch_user(user_id)  # This might fail
        return Ok("User retrieved successfully", user, status_code=200)
    except Exception as e:
        raise Error(e, "Failed to retrieve user", 404)
    # OR alternatively:
    # except Exception:
    #     raise Error("Failed to retrieve user", 404)

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
        return Ok("User found", user, status_code=200)()
    except Exception as e:
        raise Error(e, "User not found", 404)

# Django
from django.http import JsonResponse
from oguild.response import Ok, Error

def get_user(request, user_id):
    try:
        user = fetch_user(user_id)
        return Ok("User found", user, status_code=200).to_framework_response()
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
        return Ok("User found", user, status_code=200).to_framework_response()
    except Exception as e:
        raise Error(e, "User not found", 404)
```

## 🔧 API Reference

### Ok Class

Universal success response class that works across all frameworks. The Ok class is highly flexible and supports multiple usage patterns.

#### Constructor Signature

```python
Ok(*args: Any, **kwargs: Any)
```

The Ok class accepts any number of positional arguments and keyword arguments, automatically detecting their types and assigning them appropriately.

#### Usage Patterns

The Ok class supports multiple flexible usage patterns:

**1. Status Code Only**
```python
return Ok(201)  # Returns: {"status_code": 201, "message": "Created"}
```

**2. Message Only**
```python
return Ok("login successful")  # Returns: {"status_code": 200, "message": "login successful"}
```

**3. Data Only**
```python
result = {"user_id": 123, "name": "John Doe"}
return Ok(result)  # Returns: {"status_code": 200, "message": "OK", "data": result}
```

**4. Complete Response with All Parameters**
```python
result = {"user_id": 123, "name": "John Doe"}
session_data = {"token": "abc123", "expires": "2024-01-01"}
return Ok(result, 201, "Login successful", {"session": session_data})
# Returns: {
#   "status_code": 201, 
#   "message": "Login successful", 
#   "data": result, 
#   "extras": [{"session": session_data}]
# }
```

**5. Using Keyword Arguments**
```python
result = {"user_id": 123, "name": "John Doe"}
session_data = {"token": "abc123", "expires": "2024-01-01"}
return Ok(result, 201, "Login successful", meta={"session": session_data})
# Returns: {
#   "status_code": 201, 
#   "message": "Login successful", 
#   "data": result, 
#   "meta": {"session": session_data}
# }
```

**6. Using Named Parameters**
```python
return Ok(
    data={"user_id": 123, "name": "John Doe"},
    status_code=201,
    message="User created successfully",
    session="abc123"
)
# Returns: {
#   "status_code": 201, 
#   "message": "User created successfully", 
#   "data": {"user_id": 123, "name": "John Doe"},
#   "session": "abc123"
# }
```

#### Parameter Detection Logic

The Ok class intelligently detects parameter types:

- **Integer**: Treated as `status_code`
- **String**: Treated as `message` (if no message set yet)
- **Dictionary/List/Tuple**: Treated as `data` (if no data set yet)
- **Additional arguments**: Added to `extras` list
- **Keyword arguments**: Added directly to the response

#### Methods

- `to_framework_response()` - Convert to framework-specific response
- `__call__()` - Auto-detect sync/async context and return appropriate response
- `__await__()` - Async context support

### Error Class

Comprehensive error handling with automatic classification and exception detection.

```python
Error(
    e: Optional[Exception] = None,
    msg: Optional[str] = None,
    code: Optional[int] = None,
    level: Optional[str] = None,
    additional_info: Optional[dict] = None
)
```

**Automatic Exception Detection:**
When no exception is provided (`e=None`), the Error class automatically detects the current exception using `sys.exc_info()`. This provides flexibility in how you handle exceptions:

```python
# Option 1: Explicit exception passing (always works)
try:
    risky_operation()
except Exception as e:
    raise Error(e, "Operation failed", 500)

# Option 2: Automatic exception detection (cleaner syntax)
try:
    risky_operation()
except Exception:
    raise Error("Operation failed", 500)

# Both approaches preserve the original exception details for logging and debugging
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

### Automatic Exception Detection

The Error class now automatically detects exceptions when none are explicitly provided, giving you flexibility in how you handle exceptions:

```python
from oguild.response import Error

def divide_numbers(a, b):
    try:
        return a / b
    except ZeroDivisionError as e:
        raise Error(e, "Cannot divide by zero", 400)
    except TypeError as e:
        raise Error(e, "Invalid number types", 400)
    except Exception as e:
        raise Error(e, "Unexpected calculation error", 500)

# OR using automatic detection (cleaner syntax):
def divide_numbers_auto(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        raise Error("Cannot divide by zero", 400)
    except TypeError:
        raise Error("Invalid number types", 400)
    except Exception:
        raise Error("Unexpected calculation error", 500)

# OR use with default error message
def divide_numbers_auto(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        raise Error
    except TypeError:
        raise Error
    except Exception:
        raise Error

# All approaches preserve the original exception details
# including the original exception type, message, and stack trace
```

Choose the pattern that fits your coding style - both work identically!

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
            e=e,
            msg="Payment processing failed",
            code=402,  # Payment Required
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

        return Ok("User data retrieved", {
            "user": user,
            "profile": profile
        }, status_code=200)
    except UserNotFoundError as e:
        raise Error(e, "User not found", 404)
```

## 🔧 Framework-Specific Response Handling

### FastAPI Detail Key Wrapping

FastAPI automatically wraps error responses in a `detail` key. To unwrap this automatically and return your custom error structure directly, you can override FastAPI's default exception handler:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from oguild.response import Error

app = FastAPI()

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if isinstance(exc.detail, dict):  # unwrap dict passed into detail
        return JSONResponse(content=exc.detail, status_code=exc.status_code)
    return JSONResponse(
        content={"message": str(exc.detail)},
        status_code=exc.status_code,
    )

# Now your Error responses will be returned directly without the detail wrapper
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    try:
        user = await fetch_user(user_id)
        return Ok("User found", user, status_code=200)()
    except Exception as e:
        raise Error(e, "User not found", 404)
```

### Django Custom Error Handling

Django doesn't wrap responses by default, but you can create custom middleware for consistent error formatting:

```python
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from oguild.response import Error

class CustomErrorMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if isinstance(exception, Error):
            error_dict = exception.to_dict()
            return JsonResponse(error_dict, status=exception.http_status_code)
        return None
```

### Flask Custom Error Handlers

Flask allows you to register custom error handlers for consistent response formatting:

```python
from flask import Flask, jsonify
from oguild.response import Error

app = Flask(__name__)

@app.errorhandler(Error)
def handle_custom_error(error):
    return jsonify(error.to_dict()), error.http_status_code

@app.errorhandler(Exception)
def handle_generic_error(error):
    custom_error = Error(error, "Internal server error", 500)
    return jsonify(custom_error.to_dict()), 500
```

### Starlette Custom Exception Handler

For pure Starlette applications, you can add a custom exception handler:

```python
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from oguild.response import Error

async def custom_exception_handler(request, exc):
    if isinstance(exc, StarletteHTTPException) and isinstance(exc.detail, dict):
        return JSONResponse(content=exc.detail, status_code=exc.status_code)
    elif isinstance(exc, Error):
        return JSONResponse(content=exc.to_dict(), status_code=exc.http_status_code)
    return JSONResponse(
        content={"message": str(exc.detail) if hasattr(exc, 'detail') else str(exc)},
        status_code=getattr(exc, 'status_code', 500)
    )

app = Starlette(exception_handlers={
    StarletteHTTPException: custom_exception_handler,
    Error: custom_exception_handler,
})
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
    response = Ok("Success", {"data": "test"}, status_code=200)
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
