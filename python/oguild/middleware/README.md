# OGuild Middleware

Universal error middleware that works with all frameworks using their native middleware injection patterns.

## ErrorMiddleware

One middleware class that automatically adapts to each framework's middleware system.

### FastAPI Usage

```python
from fastapi import FastAPI
from oguild import ErrorMiddleware

app = FastAPI()

# Basic usage
app.add_middleware(ErrorMiddleware)

# With custom configuration
app.add_middleware(ErrorMiddleware,
    default_error_message="Something went wrong",
    default_error_code=500,
    include_request_info=False  # Default: False (no request info)
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/error")
async def error_endpoint():
    raise ValueError("This will be caught by ErrorMiddleware")
    # Response: {"message": "An unexpected error occurred", ...}

@app.get("/custom-error")
async def custom_error_endpoint():
    from oguild import Error
    raise Error(msg="Custom error message", code=400)
    # Response: {"detail": {"message": "Custom error message", ...}}
```

### Starlette Usage

```python
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Route
from oguild import ErrorMiddleware

app = Starlette(
    routes=[Route("/", homepage)],
    middleware=[Middleware(ErrorMiddleware)]
)
```

### Django Usage

```python
# your_app/middleware.py
from oguild import ErrorMiddleware

# Create middleware instance
error_middleware = ErrorMiddleware()

# Use Django's middleware pattern
class DjangoErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.error_handler = error_middleware.django_middleware(get_response)

    def __call__(self, request):
        return self.error_handler(request)

# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'your_app.middleware.DjangoErrorMiddleware',  # Add this
    # ... other middleware
]
```

### Flask Usage

```python
from flask import Flask
from oguild import ErrorMiddleware

app = Flask(__name__)

# Create middleware instance
error_middleware = ErrorMiddleware()

# Use Flask's error handler pattern
@app.errorhandler(Exception)
def handle_exception(exc):
    return error_middleware.flask_error_handler(exc)

@app.route("/")
def root():
    return {"message": "Hello World"}

@app.route("/error")
def error_endpoint():
    raise ValueError("This will be caught by ErrorMiddleware")
```

## Message Handling

The middleware handles different types of exceptions differently:

- **Regular exceptions** (ValueError, AttributeError, etc.) → Uses default message: `"An unexpected error occurred"`
- **Custom Error instances** → Uses the custom message you provided

```python
# Regular exception - middleware catches it
raise ValueError("Something went wrong")
# Response: {"message": "An unexpected error occurred", ...}

# Custom Error - handled directly by framework
from oguild import Error
raise Error(msg="Custom message", code=400)
# Response: {"detail": {"message": "Custom message", ...}}
```

## Framework Support

- ✅ **FastAPI** - `app.add_middleware(ErrorMiddleware)`
- ✅ **Starlette** - `Middleware(ErrorMiddleware)`
- ✅ **Django** - `error_middleware.django_middleware(get_response)`
- ✅ **Flask** - `@app.errorhandler(Exception)` + `error_middleware.flask_error_handler(exc)`

The same `ErrorMiddleware` class works with all frameworks using their native patterns!

## Factory Function

You can also use the factory function to create pre-configured middleware:

```python
from oguild import create_error_middleware

# Create a custom middleware class
CustomErrorMiddleware = create_error_middleware(
    default_error_message="Custom error occurred",
    default_error_code=400,
    include_request_info=True
)

# Use it with any framework
app.add_middleware(CustomErrorMiddleware)
```
