from unittest.mock import patch

import pytest
from oguild.response import Error, Ok, police


class TestResponseIntegration:
    """Integration tests for response module."""

    def test_ok_and_error_workflow(self):
        """Test complete workflow with Ok and Error responses."""
        success_response = Ok(
            message="User created successfully", user_id=123, status_code=201
        )

        # Ok returns a framework response, check its properties
        assert success_response.status_code == 201

        # Check content
        import json
        if hasattr(success_response, 'body'):
            content = json.loads(success_response.body.decode('utf-8'))
        elif hasattr(success_response, 'content'):
            content = json.loads(success_response.content.decode('utf-8'))
        else:
            content = success_response  # fallback case

        assert content["user_id"] == 123

        try:
            raise ValueError("Invalid user data")
        except ValueError as e:
            with patch.object(Error, "_handle_error_with_handlers"):
                error_response = Error(
                    e=e, msg="Failed to create user", code=400, _raise_immediately=False
                )

                error_dict = error_response.to_dict()
                assert error_dict["status_code"] == 400
                assert "Failed to create user" in error_dict["message"]

    @pytest.mark.asyncio
    async def test_async_response_workflow(self):
        """Test async workflow with Ok and Error responses."""

        @police()
        async def async_operation(success: bool):
            if success:
                return Ok(message="Async operation successful")
            else:
                raise RuntimeError("Async operation failed")

        result = await async_operation(True)
        # Ok returns a framework response, not an Ok instance
        assert hasattr(result, 'status_code')

        # Check content
        import json
        if hasattr(result, 'body'):
            content = json.loads(result.body.decode('utf-8'))
        elif hasattr(result, 'content'):
            content = json.loads(result.content.decode('utf-8'))
        else:
            content = result  # fallback case

        assert content["message"] == "Async operation successful"

        with pytest.raises(Exception):
            await async_operation(False)

    def test_framework_compatibility(self):
        """Test framework compatibility for both Ok and Error."""
        ok_response = Ok(message="Test")

        # Ok directly returns a framework response, no need for to_framework_response
        assert hasattr(ok_response, 'status_code')
        assert ok_response.status_code == 200

        # Create a mock FastAPIHTTPException instance
        mock_fastapi_exception = type('FastAPIHTTPException', (), {
            'status_code': 400,
            'detail': 'Test error'
        })
        
        error_response = Error(e=mock_fastapi_exception(), msg="Test error", code=400, _raise_immediately=False)

        with patch.object(Error, "_handle_error_with_handlers"), patch(
            "oguild.response.response.FastAPIHTTPException", mock_fastapi_exception
        ):
            result = error_response.to_framework_exception()
            assert result == error_response.e  # Should return the original exception
