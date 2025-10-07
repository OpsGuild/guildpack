from typing import Any, Dict

try:
    import boto3

    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None

try:
    import azure.storage

    AZURE_STORAGE_AVAILABLE = True
except ImportError:
    AZURE_STORAGE_AVAILABLE = False
    azure = None

try:
    import google.cloud.storage
    from google.api_core import exceptions as gcs_exceptions

    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    google = None
    gcs_exceptions = None

try:
    import minio

    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False
    minio = None


class FileErrorHandler:
    """Handler for file and storage-related errors."""

    def __init__(self, logger):
        self.logger = logger

    def _is_file_error(self, e: Exception) -> bool:
        """Check if the exception is a file or storage-related error."""
        if BOTO3_AVAILABLE and isinstance(e, boto3.exceptions.Boto3Error):
            return True
        if AZURE_STORAGE_AVAILABLE and isinstance(
            e, azure.storage.StorageError
        ):
            return True
        if GCS_AVAILABLE and isinstance(
            e, gcs_exceptions.GoogleAPIError
        ):
            return True
        if MINIO_AVAILABLE and isinstance(e, minio.error.MinioException):
            return True

        if isinstance(
            e,
            (
                FileNotFoundError,
                PermissionError,
                IsADirectoryError,
                NotADirectoryError,
            ),
        ):
            return True

        if isinstance(e, OSError) and hasattr(e, "errno"):
            file_related_errnos = [
                2,
                13,
                28,
            ]  # No such file, Permission denied, No space left
            return e.errno in file_related_errnos

        error_msg = str(e).lower()
        file_keywords = [
            "file",
            "directory",
            "path",
            "storage",
            "disk",
            "space",
            "permission",
            "access denied",
        ]
        return any(keyword in error_msg for keyword in file_keywords)

    def handle_error(self, e: Exception) -> Dict[str, Any]:
        """Handle file and storage-related errors and return error details."""
        if BOTO3_AVAILABLE and isinstance(e, boto3.exceptions.Boto3Error):
            return self._handle_boto3_error(e)
        elif AZURE_STORAGE_AVAILABLE and isinstance(
            e, azure.storage.StorageError
        ):
            return self._handle_azure_error(e)
        elif GCS_AVAILABLE and isinstance(
            e, gcs_exceptions.GoogleAPIError
        ):
            return self._handle_gcs_error(e)
        elif MINIO_AVAILABLE and isinstance(e, minio.error.MinioException):
            return self._handle_minio_error(e)
        else:
            return self._handle_generic_file_error(e)

    def _handle_boto3_error(
        self, e: "boto3.exceptions.Boto3Error"
    ) -> Dict[str, Any]:
        """Handle AWS Boto3 errors."""
        error_info = {
            "level": "ERROR",
            "http_status_code": 503,
            "message": "Cloud storage error occurred.",
            "error_type": type(e).__name__,
        }

        if hasattr(e, "response") and e.response:
            status_code = e.response.get("ResponseMetadata", {}).get(
                "HTTPStatusCode"
            )
            if status_code:
                if status_code == 404:
                    error_info.update(
                        {
                            "http_status_code": 404,
                            "message": "File not found in storage.",
                        }
                    )
                elif status_code == 403:
                    error_info.update(
                        {
                            "http_status_code": 403,
                            "message": "Access denied to storage resource.",
                        }
                    )
                elif status_code == 409:
                    error_info.update(
                        {
                            "http_status_code": 409,
                            "message": "File already exists in storage.",
                        }
                    )

        return error_info

    def _handle_azure_error(
        self, e: "azure.storage.StorageError"
    ) -> Dict[str, Any]:
        """Handle Azure Storage errors."""
        error_info = {
            "level": "ERROR",
            "http_status_code": 503,
            "message": "Azure storage error occurred.",
            "error_type": type(e).__name__,
        }

        if hasattr(e, "status_code"):
            if e.status_code == 404:
                error_info.update(
                    {
                        "http_status_code": 404,
                        "message": "File not found in Azure storage.",
                    }
                )
            elif e.status_code == 403:
                error_info.update(
                    {
                        "http_status_code": 403,
                        "message": "Access denied to Azure storage resource.",
                    }
                )
            elif e.status_code == 409:
                error_info.update(
                    {
                        "http_status_code": 409,
                        "message": "File already exists in Azure storage.",
                    }
                )

        return error_info

    def _handle_gcs_error(
        self, e: "gcs_exceptions.GoogleAPIError"
    ) -> Dict[str, Any]:
        """Handle Google Cloud Storage errors."""
        error_info = {
            "level": "ERROR",
            "http_status_code": 503,
            "message": "Google Cloud Storage error occurred.",
            "error_type": type(e).__name__,
        }

        if hasattr(e, "code"):
            if e.code == 404:
                error_info.update(
                    {
                        "http_status_code": 404,
                        "message": "File not found in Google Cloud Storage.",
                    }
                )
            elif e.code == 403:
                error_info.update(
                    {
                        "http_status_code": 403,
                        "message": "Access denied to Google Cloud Storage resource.",
                    }
                )
            elif e.code == 409:
                error_info.update(
                    {
                        "http_status_code": 409,
                        "message": "File already exists in Google Cloud Storage.",
                    }
                )

        return error_info

    def _handle_minio_error(
        self, e: "minio.error.MinioException"
    ) -> Dict[str, Any]:
        """Handle MinIO errors."""
        error_info = {
            "level": "ERROR",
            "http_status_code": 503,
            "message": "MinIO storage error occurred.",
            "error_type": type(e).__name__,
        }

        if hasattr(e, "code"):
            if e.code == "NoSuchKey":
                error_info.update(
                    {
                        "http_status_code": 404,
                        "message": "File not found in MinIO storage.",
                    }
                )
            elif e.code == "AccessDenied":
                error_info.update(
                    {
                        "http_status_code": 403,
                        "message": "Access denied to MinIO storage resource.",
                    }
                )
            elif e.code == "BucketAlreadyExists":
                error_info.update(
                    {
                        "http_status_code": 409,
                        "message": "Bucket already exists in MinIO storage.",
                    }
                )

        return error_info

    def _handle_generic_file_error(self, e: Exception) -> Dict[str, Any]:
        """Handle generic file and storage errors."""
        error_info = {
            "level": "ERROR",
            "http_status_code": 500,
            "message": "File operation error occurred.",
            "error_type": type(e).__name__,
        }

        # Handle standard library file errors
        if isinstance(e, FileNotFoundError):
            error_info.update(
                {
                    "http_status_code": 404,
                    "message": "File not found.",
                }
            )
        elif isinstance(e, PermissionError):
            error_info.update(
                {
                    "http_status_code": 403,
                    "message": "Permission denied for file operation.",
                }
            )
        elif isinstance(e, IsADirectoryError):
            error_info.update(
                {
                    "http_status_code": 400,
                    "message": "Expected a file but found a directory.",
                }
            )
        elif isinstance(e, NotADirectoryError):
            error_info.update(
                {
                    "http_status_code": 400,
                    "message": "Expected a directory but found a file.",
                }
            )
        elif isinstance(e, OSError):
            if e.errno == 28:  # No space left on device
                error_info.update(
                    {
                        "http_status_code": 507,
                        "message": "Insufficient storage space.",
                    }
                )
            elif e.errno == 2:  # No such file or directory
                error_info.update(
                    {
                        "http_status_code": 404,
                        "message": "File or directory not found.",
                    }
                )
            elif e.errno == 13:  # Permission denied
                error_info.update(
                    {
                        "http_status_code": 403,
                        "message": "Permission denied for file operation.",
                    }
                )
            else:
                error_info.update(
                    {
                        "message": f"File system error: {e.strerror or 'Unknown file system error'}",
                    }
                )

        return error_info
