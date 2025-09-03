from typing import Any, Dict

try:
    import jwt

    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    jwt = None

try:
    from authlib.oauth2.rfc6749.errors import OAuth2Error as AuthlibOAuth2Error

    AUTHLIB_AVAILABLE = True
except ImportError:
    AUTHLIB_AVAILABLE = False
    AuthlibOAuth2Error = None

try:
    from oauthlib.oauth2.rfc6749.errors import \
        OAuth2Error as OauthlibOAuth2Error

    OAUTHLIB_AVAILABLE = True
except ImportError:
    OAUTHLIB_AVAILABLE = False
    OauthlibOAuth2Error = None


class AuthenticationErrorHandler:
    """Handler for authentication and authorization errors."""

    def __init__(self, logger):
        self.logger = logger

    def _is_auth_error(self, e: Exception) -> bool:
        """Check if the exception is an authentication-related error."""
        if JWT_AVAILABLE and isinstance(e, jwt.InvalidTokenError):
            return True
        elif AUTHLIB_AVAILABLE and isinstance(e, AuthlibOAuth2Error):
            return True
        elif OAUTHLIB_AVAILABLE and isinstance(e, OauthlibOAuth2Error):
            return True
        else:
            error_msg = str(e).lower()
            auth_keywords = [
                "token",
                "auth",
                "unauthorized",
                "forbidden",
                "permission",
                "credential",
                "login",
                "password",
                "jwt",
                "oauth",
                "bearer",
            ]
            return any(keyword in error_msg for keyword in auth_keywords)

    def handle_error(self, e: Exception) -> Dict[str, Any]:
        """Handle authentication-related errors and return error details."""
        if JWT_AVAILABLE and isinstance(e, jwt.InvalidTokenError):
            return self._handle_jwt_error(e)
        elif AUTHLIB_AVAILABLE and isinstance(e, AuthlibOAuth2Error):
            return self._handle_authlib_error(e)
        elif OAUTHLIB_AVAILABLE and isinstance(e, OauthlibOAuth2Error):
            return self._handle_oauthlib_error(e)
        else:
            return self._handle_generic_auth_error(e)

    def _handle_jwt_error(self, e: "jwt.InvalidTokenError") -> Dict[str, Any]:
        """Handle JWT token errors."""
        error_info = {
            "level": "WARNING",
            "http_status_code": 401,
            "message": "Invalid authentication token.",
            "error_type": type(e).__name__,
        }

        if isinstance(e, jwt.ExpiredSignatureError):
            error_info.update(
                {
                    "message": "Authentication token has expired.",
                }
            )
        elif isinstance(e, jwt.InvalidSignatureError):
            error_info.update(
                {
                    "message": "Invalid token signature.",
                }
            )
        elif isinstance(e, jwt.DecodeError):
            error_info.update(
                {
                    "message": "Token could not be decoded.",
                }
            )
        elif isinstance(e, jwt.InvalidKeyError):
            error_info.update(
                {
                    "message": "Invalid key for token verification.",
                }
            )
        elif isinstance(e, jwt.InvalidAlgorithmError):
            error_info.update(
                {
                    "message": "Invalid algorithm for token verification.",
                }
            )

        return error_info

    def _handle_authlib_error(self, e: AuthlibOAuth2Error) -> Dict[str, Any]:
        """Handle Authlib OAuth2 errors."""
        error_info = {
            "level": "WARNING",
            "http_status_code": 401,
            "message": "OAuth2 authentication error.",
            "error_type": type(e).__name__,
        }

        if hasattr(e, "error") and e.error == "invalid_client":
            error_info.update(
                {
                    "http_status_code": 401,
                    "message": "Invalid client credentials.",
                }
            )
        elif hasattr(e, "error") and e.error == "invalid_grant":
            error_info.update(
                {
                    "http_status_code": 401,
                    "message": "Invalid authorization grant.",
                }
            )
        elif hasattr(e, "error") and e.error == "unauthorized_client":
            error_info.update(
                {
                    "http_status_code": 403,
                    "message": "Client is not authorized to use this grant type.",
                }
            )
        elif hasattr(e, "error") and e.error == "unsupported_grant_type":
            error_info.update(
                {
                    "http_status_code": 400,
                    "message": "Unsupported grant type.",
                }
            )
        elif hasattr(e, "error") and e.error == "invalid_scope":
            error_info.update(
                {
                    "http_status_code": 400,
                    "message": "Invalid scope requested.",
                }
            )

        return error_info

    def _handle_oauthlib_error(self, e: OauthlibOAuth2Error) -> Dict[str, Any]:
        """Handle OAuthlib OAuth2 errors."""
        error_info = {
            "level": "WARNING",
            "http_status_code": 401,
            "message": "OAuth2 authentication error.",
            "error_type": type(e).__name__,
        }

        if hasattr(e, "error") and e.error == "invalid_client":
            error_info.update(
                {
                    "http_status_code": 401,
                    "message": "Invalid client credentials.",
                }
            )
        elif hasattr(e, "error") and e.error == "invalid_grant":
            error_info.update(
                {
                    "http_status_code": 401,
                    "message": "Invalid authorization grant.",
                }
            )
        elif hasattr(e, "error") and e.error == "unauthorized_client":
            error_info.update(
                {
                    "http_status_code": 403,
                    "message": "Client is not authorized to use this grant type.",
                }
            )
        elif hasattr(e, "error") and e.error == "unsupported_grant_type":
            error_info.update(
                {
                    "http_status_code": 400,
                    "message": "Unsupported grant type.",
                }
            )
        elif hasattr(e, "error") and e.error == "invalid_scope":
            error_info.update(
                {
                    "http_status_code": 400,
                    "message": "Invalid scope requested.",
                }
            )

        return error_info

    def _handle_generic_auth_error(self, e: Exception) -> Dict[str, Any]:
        """Handle generic authentication errors."""
        error_info = {
            "level": "WARNING",
            "http_status_code": 401,
            "message": "Authentication error occurred.",
            "error_type": type(e).__name__,
        }

        error_msg = str(e).lower()

        if "token" in error_msg and "expired" in error_msg:
            error_info.update(
                {
                    "message": "Authentication token has expired.",
                }
            )
        elif "token" in error_msg and "invalid" in error_msg:
            error_info.update(
                {
                    "message": "Invalid authentication token.",
                }
            )
        elif "unauthorized" in error_msg:
            error_info.update(
                {
                    "message": "Unauthorized access.",
                }
            )
        elif "forbidden" in error_msg:
            error_info.update(
                {
                    "http_status_code": 403,
                    "message": "Access forbidden.",
                }
            )
        elif "permission" in error_msg:
            error_info.update(
                {
                    "http_status_code": 403,
                    "message": "Insufficient permissions.",
                }
            )
        elif "credentials" in error_msg:
            error_info.update(
                {
                    "message": "Invalid credentials provided.",
                }
            )

        return error_info
