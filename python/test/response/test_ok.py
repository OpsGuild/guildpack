from unittest.mock import MagicMock, patch

import pytest
from oguild.response import Ok


class TestOk:
    """Test cases for Ok response class."""

    def test_ok_default_initialization(self):
        """Test Ok class with default parameters."""
        response = Ok()

        assert response.status_code == 200
        assert response.payload["message"] == "Success"
        assert response.payload["status_code"] == 200

    def test_ok_custom_initialization(self):
        """Test Ok class with custom parameters."""
        response = Ok(
            message="Created successfully",
            response_dict={"id": 123, "name": "test"},
            extra_field="extra_value",
            status_code=201,
        )

        assert response.status_code == 201
        assert response.payload["message"] == "Created successfully"
        assert response.payload["status_code"] == 201
        assert response.payload["id"] == 123
        assert response.payload["name"] == "test"
        assert response.payload["extra_field"] == "extra_value"

    def test_ok_with_kwargs_only(self):
        """Test Ok class with only kwargs."""
        response = Ok(data=[1, 2, 3], count=3)

        assert response.status_code == 200
        assert response.payload["message"] == "Success"
        assert response.payload["data"] == [1, 2, 3]
        assert response.payload["count"] == 3

    def test_ok_with_response_dict_and_kwargs(self):
        """Test Ok class with both response_dict and kwargs."""
        response = Ok(
            response_dict={"existing": "value"}, new_field="new_value"
        )

        assert response.payload["existing"] == "value"
        assert response.payload["new_field"] == "new_value"
        assert response.payload["message"] == "Success"

    def test_ok_to_framework_response_fastapi(self):
        """Test Ok to_framework_response with FastAPI."""
        response = Ok(message="Test", status_code=201)
        result = response.to_framework_response()

        # Check if Starlette is available (FastAPI uses Starlette responses)
        try:
            from starlette.responses import JSONResponse
            assert isinstance(result, JSONResponse)
            assert result.status_code == 201
            assert result.body == b'{"message":"Test","status_code":201}'
        except ImportError:
            # If Starlette not available, should fall back to other framework
            assert hasattr(result, 'status_code') or isinstance(result, dict)

    def test_ok_to_framework_response_starlette(self):
        """Test Ok to_framework_response with Starlette."""
        with patch("oguild.response.response.FastAPIJSONResponse", None):
            response = Ok(message="Test Starlette", status_code=202)
            result = response.to_framework_response()

            # Check if Starlette is available
            try:
                from starlette.responses import JSONResponse
                assert isinstance(result, JSONResponse)
                assert result.status_code == 202
                assert (
                    result.body
                    == b'{"message":"Test Starlette","status_code":202}'
                )
            except ImportError:
                # If Starlette not available, should fall back to other framework
                assert hasattr(result, 'status_code') or isinstance(result, dict)

    def test_ok_to_framework_response_django(self):
        """Test Ok to_framework_response with Django."""
        import os

        import django
        from django.conf import settings

        if not settings.configured:
            os.environ.setdefault(
                "DJANGO_SETTINGS_MODULE", "django.conf.global_settings"
            )
            settings.configure()
            django.setup()

        with patch(
            "oguild.response.response.FastAPIJSONResponse", None
        ), patch("oguild.response.response.StarletteJSONResponse", None):
            response = Ok(message="Test Django", status_code=203)
            result = response.to_framework_response()

            from django.http import JsonResponse

            assert isinstance(result, JsonResponse)
            assert result.status_code == 203
            import json

            content = json.loads(result.content.decode("utf-8"))
            assert content["message"] == "Test Django"
            assert content["status_code"] == 203

    def test_ok_to_framework_response_flask(self):
        """Test Ok to_framework_response with Flask."""
        with patch(
            "oguild.response.response.FastAPIJSONResponse", None
        ), patch(
            "oguild.response.response.StarletteJSONResponse", None
        ), patch(
            "oguild.response.response.DjangoJsonResponse", None
        ):
            response = Ok(message="Test Flask", status_code=204)
            result = response.to_framework_response()

            from flask import Response

            assert isinstance(result, Response)
            assert result.status_code == 204
            assert result.mimetype == "application/json"
            import json

            content = json.loads(result.data.decode("utf-8"))
            assert content["message"] == "Test Flask"
            assert content["status_code"] == 204

    def test_ok_to_framework_response_fallback(self):
        """Test Ok to_framework_response fallback when no framework available."""
        with patch(
            "oguild.response.response.FastAPIJSONResponse", None
        ), patch(
            "oguild.response.response.StarletteJSONResponse", None
        ), patch(
            "oguild.response.response.DjangoJsonResponse", None
        ), patch(
            "oguild.response.response.FlaskResponse", None
        ):

            response = Ok(message="Test Fallback", status_code=205)
            result = response.to_framework_response()

            assert result == response.payload
            assert result["message"] == "Test Fallback"
            assert result["status_code"] == 205

    def test_ok_to_framework_response_exception_handling(self):
        """Test Ok to_framework_response with exception handling."""
        with patch(
            "oguild.response.response.FastAPIJSONResponse"
        ) as mock_response:
            mock_response.side_effect = Exception("Framework error")

            response = Ok(message="Test Exception", status_code=206)
            result = response.to_framework_response()

            assert result == response.payload
            assert result["message"] == "Test Exception"
            assert result["status_code"] == 206

    def test_ok_call_sync_context(self):
        """Test Ok __call__ in sync context."""
        with patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.side_effect = RuntimeError("No running loop")

            with patch.object(Ok, "to_framework_response") as mock_to_response:
                mock_to_response.return_value = "sync_response"

                response = Ok(message="Test")
                result = response()

                mock_to_response.assert_called_once()
                assert result == "sync_response"

    @pytest.mark.asyncio
    async def test_ok_call_async_context(self):
        """Test Ok __call__ in async context."""
        with patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value = MagicMock()

            with patch.object(Ok, "_async_call") as mock_async_call:
                mock_async_call.return_value = "async_response"

                response = Ok(message="Test")
                result = response()

                mock_async_call.assert_called_once()
                assert hasattr(result, "__await__")

                final_result = await result
                assert final_result == "async_response"

    @pytest.mark.asyncio
    async def test_ok_async_call(self):
        """Test Ok _async_call method."""
        with patch.object(Ok, "to_framework_response") as mock_to_response:
            mock_to_response.return_value = "async_response"

            response = Ok(message="Test")
            result = await response._async_call()

            mock_to_response.assert_called_once()
            assert result == "async_response"

    @pytest.mark.asyncio
    async def test_ok_await(self):
        """Test Ok __await__ method."""
        with patch.object(Ok, "_async_call") as mock_async_call:
            mock_async_call.return_value = "await_response"

            response = Ok(message="Test")
            result = await response

            mock_async_call.assert_called_once()
            assert result == "await_response"
