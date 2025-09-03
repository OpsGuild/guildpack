from typing import Any, Dict

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None

try:
    import urllib3

    URLLIB3_AVAILABLE = True
except ImportError:
    URLLIB3_AVAILABLE = False
    urllib3 = None


class NetworkErrorHandler:
    """Handler for network-related errors."""

    def __init__(self, logger):
        self.logger = logger

    def _is_network_error(self, e: Exception) -> bool:
        """Check if the exception is a network-related error."""
        if REQUESTS_AVAILABLE and isinstance(e, requests.RequestException):
            return True
        elif AIOHTTP_AVAILABLE and isinstance(e, aiohttp.ClientError):
            return True
        elif HTTPX_AVAILABLE and isinstance(e, httpx.HTTPError):
            return True
        elif URLLIB3_AVAILABLE and isinstance(e, urllib3.exceptions.HTTPError):
            return True
        elif isinstance(e, (ConnectionError, TimeoutError)):
            return True
        elif isinstance(e, OSError) and hasattr(e, "errno"):
            network_errnos = {
                111,
                110,
                113,
            }  # Connection refused, timed out, no route to host
            return e.errno in network_errnos
        return False

    def handle_error(self, e: Exception) -> Dict[str, Any]:
        """Handle network-related errors and return error details."""
        if REQUESTS_AVAILABLE and isinstance(e, requests.RequestException):
            return self._handle_requests_error(e)
        elif AIOHTTP_AVAILABLE and isinstance(e, aiohttp.ClientError):
            return self._handle_aiohttp_error(e)
        elif HTTPX_AVAILABLE and isinstance(e, httpx.HTTPError):
            return self._handle_httpx_error(e)
        elif URLLIB3_AVAILABLE and isinstance(e, urllib3.exceptions.HTTPError):
            return self._handle_urllib3_error(e)
        else:
            return self._handle_generic_network_error(e)

    def _handle_requests_error(
        self, e: "requests.RequestException"
    ) -> Dict[str, Any]:
        """Handle requests library errors."""
        error_info = {
            "level": "ERROR",
            "http_status_code": 503,
            "message": "Network request failed.",
            "error_type": type(e).__name__,
        }

        if isinstance(e, requests.ConnectionError):
            error_info.update(
                {
                    "message": "Failed to establish connection to the server.",
                }
            )
        elif isinstance(e, requests.Timeout):
            error_info.update(
                {
                    "http_status_code": 408,
                    "message": "Request timeout occurred.",
                }
            )
        elif isinstance(e, requests.HTTPError):
            error_info.update(
                {
                    "http_status_code": (
                        e.response.status_code if e.response else 500
                    ),
                    "message": f"HTTP error: {e.response.reason if e.response else 'Unknown error'}",
                }
            )
        elif isinstance(e, requests.TooManyRedirects):
            error_info.update(
                {
                    "message": "Too many redirects occurred.",
                }
            )
        elif isinstance(e, requests.URLRequired):
            error_info.update(
                {
                    "http_status_code": 400,
                    "message": "A valid URL is required.",
                }
            )
        elif isinstance(e, requests.RequestException):
            error_info.update(
                {
                    "message": "Request failed due to an error.",
                }
            )

        return error_info

    def _handle_aiohttp_error(
        self, e: "aiohttp.ClientError"
    ) -> Dict[str, Any]:
        """Handle aiohttp library errors."""
        error_info = {
            "level": "ERROR",
            "http_status_code": 503,
            "message": "Network request failed.",
            "error_type": type(e).__name__,
        }

        if isinstance(e, aiohttp.ClientConnectionError):
            error_info.update(
                {
                    "message": "Failed to establish connection to the server.",
                }
            )
        elif isinstance(e, aiohttp.ClientTimeout):
            error_info.update(
                {
                    "http_status_code": 408,
                    "message": "Request timeout occurred.",
                }
            )
        elif isinstance(e, aiohttp.ClientResponseError):
            error_info.update(
                {
                    "http_status_code": e.status,
                    "message": f"HTTP error: {e.message}",
                }
            )
        elif isinstance(e, aiohttp.ClientError):
            error_info.update(
                {
                    "message": "Client error occurred during request.",
                }
            )

        return error_info

    def _handle_httpx_error(self, e: "httpx.HTTPError") -> Dict[str, Any]:
        """Handle httpx library errors."""
        error_info = {
            "level": "ERROR",
            "http_status_code": 503,
            "message": "Network request failed.",
            "error_type": type(e).__name__,
        }

        if isinstance(e, httpx.ConnectError):
            error_info.update(
                {
                    "message": "Failed to establish connection to the server.",
                }
            )
        elif isinstance(e, httpx.TimeoutException):
            error_info.update(
                {
                    "http_status_code": 408,
                    "message": "Request timeout occurred.",
                }
            )
        elif isinstance(e, httpx.HTTPStatusError):
            error_info.update(
                {
                    "http_status_code": e.response.status_code,
                    "message": f"HTTP error: {e.response.reason_phrase}",
                }
            )
        elif isinstance(e, httpx.HTTPError):
            error_info.update(
                {
                    "message": "HTTP error occurred during request.",
                }
            )

        return error_info

    def _handle_urllib3_error(
        self, e: "urllib3.exceptions.HTTPError"
    ) -> Dict[str, Any]:
        """Handle urllib3 library errors."""
        error_info = {
            "level": "ERROR",
            "http_status_code": 503,
            "message": "Network request failed.",
            "error_type": type(e).__name__,
        }

        if isinstance(e, urllib3.exceptions.ConnectionError):
            error_info.update(
                {
                    "message": "Failed to establish connection to the server.",
                }
            )
        elif isinstance(e, urllib3.exceptions.TimeoutError):
            error_info.update(
                {
                    "http_status_code": 408,
                    "message": "Request timeout occurred.",
                }
            )
        elif isinstance(e, urllib3.exceptions.HTTPError):
            error_info.update(
                {
                    "message": "HTTP error occurred during request.",
                }
            )

        return error_info

    def _handle_generic_network_error(self, e: Exception) -> Dict[str, Any]:
        """Handle generic network-related errors."""
        error_info = {
            "level": "ERROR",
            "http_status_code": 503,
            "message": "Network error occurred.",
            "error_type": type(e).__name__,
        }

        if isinstance(e, ConnectionError):
            error_info.update(
                {
                    "message": "Connection error occurred.",
                }
            )
        elif isinstance(e, TimeoutError):
            error_info.update(
                {
                    "http_status_code": 408,
                    "message": "Network timeout occurred.",
                }
            )
        elif isinstance(e, OSError) and hasattr(e, "errno"):
            if e.errno == 111:  # Connection refused
                error_info.update(
                    {
                        "message": "Connection refused by the server.",
                    }
                )
            elif e.errno == 110:  # Connection timed out
                error_info.update(
                    {
                        "http_status_code": 408,
                        "message": "Connection timed out.",
                    }
                )
            elif e.errno == 113:  # No route to host
                error_info.update(
                    {
                        "message": "No route to host.",
                    }
                )
            else:
                error_info.update(
                    {
                        "message": f"Network error: {e.strerror or 'Unknown network error'}",
                    }
                )

        return error_info
