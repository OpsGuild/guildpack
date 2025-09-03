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

        assert success_response.status_code == 201
        assert success_response.payload["user_id"] == 123

        try:
            raise ValueError("Invalid user data")
        except ValueError as e:
            with patch.object(Error, "_handle_error_with_handlers"):
                error_response = Error(
                    e=e, msg="Failed to create user", code=400
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
        assert isinstance(result, Ok)
        assert result.payload["message"] == "Async operation successful"

        with pytest.raises(Error):
            await async_operation(False)

    def test_framework_compatibility(self):
        """Test framework compatibility for both Ok and Error."""
        ok_response = Ok(message="Test")

        with patch(
            "oguild.response.response.FastAPIJSONResponse"
        ) as mock_fastapi:
            mock_fastapi.return_value = "fastapi_ok"
            result = ok_response.to_framework_response()
            assert result == "fastapi_ok"

        error_response = Error(msg="Test error", code=400)

        with patch.object(Error, "_handle_error_with_handlers"), patch(
            "oguild.response.response.FastAPIHTTPException"
        ) as mock_fastapi:
            mock_fastapi.return_value = "fastapi_error"
            result = error_response.to_framework_exception()
            assert result == "fastapi_error"
