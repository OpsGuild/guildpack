from unittest.mock import patch

import pytest
from oguild.response import Error
from oguild.response.errors import (AuthenticationErrorHandler,
                                    CommonErrorHandler, DatabaseErrorHandler,
                                    FileErrorHandler, NetworkErrorHandler,
                                    ValidationErrorHandler)


class TestErrorHandlers:
    """Test cases for error handler integration."""

    def test_error_handlers_initialization(self):
        """Test that error handlers are properly initialized."""
        error = Error()

        assert isinstance(error.common_handler, CommonErrorHandler)
        assert isinstance(error.database_handler, DatabaseErrorHandler)
        assert isinstance(error.validation_handler, ValidationErrorHandler)
        assert isinstance(error.network_handler, NetworkErrorHandler)
        assert isinstance(error.auth_handler, AuthenticationErrorHandler)
        assert isinstance(error.file_handler, FileErrorHandler)

    def test_error_handling_with_asyncpg_error(self):
        """Test error handling with real asyncpg error."""
        try:
            import asyncpg

            # Create a real asyncpg error
            db_error = asyncpg.PostgresError(
                'connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused'
            )

            error = Error(e=db_error)

            assert (
                "Database error occurred" in error.msg
                or "connection" in error.msg.lower()
            )
            assert error.http_status_code in [
                500,
                503,
            ]
            assert error.level in ["ERROR", None]
        except ImportError:
            pytest.skip("asyncpg not available")

    def test_error_handling_with_psycopg2_error(self):
        """Test error handling with real psycopg2 error."""
        try:
            import psycopg2

            db_error = psycopg2.OperationalError(
                'connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused'
            )

            error = Error(e=db_error)

            assert any(
                keyword in error.msg.lower()
                for keyword in [
                    "database",
                    "connection",
                    "failed",
                    "operation",
                ]
            )
            assert error.http_status_code in [500, 503]
            assert error.level in ["ERROR", None]
        except ImportError:
            pytest.skip("psycopg2 not available")

    def test_error_handling_with_pymongo_error(self):
        """Test error handling with real pymongo error."""
        try:
            import pymongo

            db_error = pymongo.errors.ConnectionFailure(
                'connection to server at "localhost" (127.0.0.1), port 27017 failed: Connection refused'
            )

            error = Error(e=db_error)

            assert any(
                keyword in error.msg.lower()
                for keyword in [
                    "database",
                    "connection",
                    "failed",
                    "operation",
                ]
            )
            assert error.http_status_code in [500, 503]
            assert error.level in ["ERROR", None]
        except ImportError:
            pytest.skip("pymongo not available")

    def test_error_handling_with_redis_error(self):
        """Test error handling with real redis error."""
        try:
            import redis

            db_error = redis.ConnectionError(
                "Error connecting to Redis at localhost:6379"
            )

            error = Error(e=db_error)

            assert any(
                keyword in error.msg.lower()
                for keyword in [
                    "database",
                    "connection",
                    "failed",
                    "operation",
                ]
            )
            assert error.http_status_code in [500, 503]
            assert error.level in ["ERROR", None]
        except ImportError:
            pytest.skip("redis not available")

    def test_error_handling_with_validation_error(self):
        """Test error handling with validation error."""
        validation_error = ValueError("Invalid input")

        with patch.object(
            DatabaseErrorHandler, "_is_database_error", return_value=False
        ), patch.object(
            ValidationErrorHandler, "_is_validation_error", return_value=True
        ), patch.object(
            ValidationErrorHandler, "handle_error"
        ) as mock_handle:
            mock_handle.return_value = {
                "message": "Validation failed",
                "http_status_code": 400,
                "level": "WARNING",
            }

            error = Error(e=validation_error)

            assert error.msg == "Validation failed"
            assert error.http_status_code == 400
            assert error.level == "WARNING"

    def test_error_handling_with_requests_error(self):
        """Test error handling with real requests error."""
        try:
            import requests

            network_error = requests.ConnectionError("Connection refused")

            error = Error(e=network_error)

            assert (
                "Network error occurred" in error.msg
                or "connection" in error.msg.lower()
            )
            assert error.http_status_code in [
                500,
                503,
                502,
            ]  # Network errors typically return 5xx
            assert error.level == "ERROR"
        except ImportError:
            pytest.skip("requests not available")

    def test_error_handling_with_aiohttp_error(self):
        """Test error handling with real aiohttp error."""
        try:
            import aiohttp

            network_error = aiohttp.ClientConnectionError("Connection refused")

            error = Error(e=network_error)

            assert (
                "Network error occurred" in error.msg
                or "connection" in error.msg.lower()
            )
            assert error.http_status_code in [500, 503, 502]
            assert error.level == "ERROR"
        except ImportError:
            pytest.skip("aiohttp not available")

    def test_error_handling_with_httpx_error(self):
        """Test error handling with real httpx error."""
        try:
            import httpx

            network_error = httpx.ConnectError("Connection refused")

            error = Error(e=network_error)

            assert (
                "Network error occurred" in error.msg
                or "connection" in error.msg.lower()
            )
            assert error.http_status_code in [500, 503, 502]
            assert error.level == "ERROR"
        except ImportError:
            pytest.skip("httpx not available")

    def test_error_handling_fallback_to_common(self):
        """Test error handling fallback to common handler."""
        unknown_error = Exception("Unknown error")

        with patch.object(
            DatabaseErrorHandler, "_is_database_error", return_value=False
        ), patch.object(
            ValidationErrorHandler, "_is_validation_error", return_value=False
        ), patch.object(
            AuthenticationErrorHandler, "_is_auth_error", return_value=False
        ), patch.object(
            FileErrorHandler, "_is_file_error", return_value=False
        ), patch.object(
            NetworkErrorHandler, "_is_network_error", return_value=False
        ), patch.object(
            CommonErrorHandler, "handle_error"
        ) as mock_handle:
            mock_handle.return_value = {
                "message": "Internal server error",
                "http_status_code": 500,
                "level": "ERROR",
            }

            error = Error(e=unknown_error)

            assert error.msg == "Internal server error"
            assert error.http_status_code == 500
            assert error.level == "ERROR"

    def test_error_handling_with_jwt_error(self):
        """Test error handling with real JWT error."""
        try:
            import jwt

            auth_error = jwt.ExpiredSignatureError("Token has expired")

            error = Error(e=auth_error)

            assert (
                "Authentication token has expired" in error.msg
                or "token" in error.msg.lower()
            )
            assert error.http_status_code == 401
            assert error.level == "WARNING"
        except ImportError:
            pytest.skip("jwt not available")

    def test_error_handling_with_authlib_error(self):
        """Test error handling with real authlib error."""
        try:
            import authlib

            auth_error = authlib.oauth2.rfc6749.errors.InvalidClientError(
                "Invalid client credentials"
            )

            error = Error(e=auth_error)

            assert (
                "Invalid client credentials" in error.msg
                or "oauth" in error.msg.lower()
            )
            assert error.http_status_code == 401
            assert error.level == "WARNING"
        except ImportError:
            pytest.skip("authlib not available")

    def test_error_handling_with_oauthlib_error(self):
        """Test error handling with real oauthlib error."""
        try:
            import oauthlib

            auth_error = oauthlib.oauth2.rfc6749.errors.InvalidClientError(
                "Invalid client credentials"
            )

            error = Error(e=auth_error)

            assert (
                "Invalid client credentials" in error.msg
                or "oauth" in error.msg.lower()
            )
            assert error.http_status_code == 401
            assert error.level == "WARNING"
        except ImportError:
            pytest.skip("oauthlib not available")

    def test_error_handling_with_minio_error(self):
        """Test error handling with real minio error."""
        try:
            import minio

            file_error = minio.error.MinioException("Access denied")

            error = Error(e=file_error)

            assert any(
                keyword in error.msg.lower()
                for keyword in ["file", "storage", "minio", "access", "error"]
            )
            assert error.http_status_code in [
                403,
                500,
                503,
            ]  # File errors can be 403, 500, or 503
            assert error.level in ["ERROR", None]
        except ImportError:
            pytest.skip("minio not available")
