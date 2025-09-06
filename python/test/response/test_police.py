from unittest.mock import patch

import pytest
from oguild.response import Error, police


class TestPolice:
    """Test cases for police decorator."""

    def test_police_sync_function_success(self):
        """Test police decorator with successful sync function."""

        @police()
        def test_func(x, y):
            return x + y

        result = test_func(2, 3)
        assert result == 5

    @pytest.mark.asyncio
    async def test_police_async_function_success(self):
        """Test police decorator with successful async function."""

        @police()
        async def test_func(x, y):
            return x + y

        result = await test_func(2, 3)
        assert result == 5

    def test_police_sync_function_exception(self):
        """Test police decorator with sync function that raises exception."""

        @police(default_msg="Custom error", default_code=400)
        def test_func(x, y):
            raise ValueError("Test error")

        with patch.object(Error, "_handle_error_with_handlers"):
            with pytest.raises(Exception) as exc_info:
                test_func(2, 3)

            # The police decorator now raises the framework exception, not the Error object
            # This is the correct behavior for production use
            assert "Test error" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_police_async_function_exception(self):
        """Test police decorator with async function that raises exception."""

        @police(default_msg="Custom async error", default_code=500)
        async def test_func(x, y):
            raise RuntimeError("Async test error")

        with patch.object(Error, "_handle_error_with_handlers"):
            with pytest.raises(Exception) as exc_info:
                await test_func(2, 3)

            # The police decorator now raises the framework exception, not the Error object
            # This is the correct behavior for production use
            assert "Async test error" in str(exc_info.value.detail)

    def test_police_with_defaults(self):
        """Test police decorator with default message and code."""

        @police()
        def test_func():
            raise Exception("Test error")

        with patch.object(Error, "_handle_error_with_handlers"):
            with pytest.raises(Exception) as exc_info:
                test_func()

            # The police decorator now raises the framework exception, not the Error object
            # This is the correct behavior for production use
            assert "Test error" in str(exc_info.value.detail)

    def test_police_preserves_function_metadata(self):
        """Test that police preserves function metadata."""

        @police()
        def test_func(x: int, y: int) -> int:
            """Test function docstring."""
            return x + y

        assert test_func.__name__ == "test_func"
        assert test_func.__doc__ == "Test function docstring."
        assert test_func.__annotations__ == {"x": int, "y": int, "return": int}

    def test_police_with_args_and_kwargs(self):
        """Test police decorator with various argument types."""

        @police()
        def test_func(*args, **kwargs):
            if args or kwargs:
                raise ValueError("Args or kwargs provided")
            return "success"

        result = test_func()
        assert result == "success"

        with pytest.raises(Exception):
            test_func(1, 2, key="value")
