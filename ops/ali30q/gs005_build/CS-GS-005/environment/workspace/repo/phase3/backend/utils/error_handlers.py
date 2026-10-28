"""
Unified error handling utilities to prevent information leakage.
"""
from fastapi import HTTPException, status
from typing import Optional, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)

# Get environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"


class SecureHTTPException(HTTPException):
    """
    HTTP Exception that sanitizes error details in production.
    """
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        internal_detail: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        """
        Args:
            status_code: HTTP status code
            detail: User-facing error message
            error_code: Machine-readable error code
            internal_detail: Internal error details (logged but not exposed)
            headers: Optional HTTP headers
        """
        # Log internal details
        if internal_detail:
            logger.error(f"Error [{error_code}]: {internal_detail}")

        # In production, use generic messages
        if ENVIRONMENT == "production" and not DEBUG:
            detail = self._sanitize_detail(status_code, detail)

        # Build response detail
        response_detail = {"message": detail}
        if error_code:
            response_detail["error_code"] = error_code

        super().__init__(status_code=status_code, detail=response_detail, headers=headers)

    @staticmethod
    def _sanitize_detail(status_code: int, detail: str) -> str:
        """Sanitize error detail based on status code."""
        generic_messages = {
            400: "Invalid request",
            401: "Authentication required",
            403: "Access denied",
            404: "Resource not found",
            409: "Resource conflict",
            422: "Invalid input data",
            429: "Too many requests",
            500: "Internal server error",
            502: "Bad gateway",
            503: "Service unavailable",
            504: "Gateway timeout"
        }
        return generic_messages.get(status_code, "An error occurred")


def handle_database_error(error: Exception, operation: str = "database operation") -> HTTPException:
    """
    Handle database errors safely.

    Args:
        error: The database exception
        operation: Description of the operation that failed

    Returns:
        HTTPException with sanitized message
    """
    error_str = str(error).lower()

    # Log full error internally
    logger.error(f"Database error during {operation}: {error}")

    # Determine specific error type
    if "unique" in error_str or "duplicate" in error_str:
        return SecureHTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resource already exists",
            error_code="DUPLICATE_RESOURCE",
            internal_detail=str(error)
        )
    elif "foreign key" in error_str or "constraint" in error_str:
        return SecureHTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reference to related resource",
            error_code="CONSTRAINT_VIOLATION",
            internal_detail=str(error)
        )
    elif "not found" in error_str:
        return SecureHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found",
            error_code="NOT_FOUND",
            internal_detail=str(error)
        )
    elif "timeout" in error_str:
        return SecureHTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Database operation timed out",
            error_code="TIMEOUT",
            internal_detail=str(error)
        )
    else:
        return SecureHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed",
            error_code="DATABASE_ERROR",
            internal_detail=str(error)
        )


def handle_blockchain_error(error: Exception, operation: str = "blockchain operation") -> HTTPException:
    """
    Handle blockchain errors safely.

    Args:
        error: The blockchain exception
        operation: Description of the operation that failed

    Returns:
        HTTPException with sanitized message
    """
    error_str = str(error).lower()

    # Log full error internally
    logger.error(f"Blockchain error during {operation}: {error}")

    # Determine specific error type
    if "insufficient funds" in error_str or "balance" in error_str:
        return SecureHTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds for transaction",
            error_code="INSUFFICIENT_FUNDS",
            internal_detail=str(error)
        )
    elif "gas" in error_str:
        return SecureHTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gas estimation failed",
            error_code="GAS_ERROR",
            internal_detail=str(error)
        )
    elif "revert" in error_str:
        return SecureHTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction reverted",
            error_code="TRANSACTION_REVERTED",
            internal_detail=str(error)
        )
    elif "timeout" in error_str or "connection" in error_str:
        return SecureHTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Blockchain service temporarily unavailable",
            error_code="BLOCKCHAIN_UNAVAILABLE",
            internal_detail=str(error)
        )
    else:
        return SecureHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Blockchain operation failed",
            error_code="BLOCKCHAIN_ERROR",
            internal_detail=str(error)
        )


def handle_validation_error(error: Exception, field: Optional[str] = None) -> HTTPException:
    """
    Handle validation errors safely.

    Args:
        error: The validation exception
        field: Optional field name that failed validation

    Returns:
        HTTPException with sanitized message
    """
    error_str = str(error)

    # Log validation error
    logger.warning(f"Validation error{f' for field {field}' if field else ''}: {error_str}")

    # Sanitize error message
    detail = error_str if len(error_str) < 200 else "Validation failed"

    return SecureHTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=detail,
        error_code="VALIDATION_ERROR",
        internal_detail=error_str
    )


def handle_authentication_error(reason: str = "Invalid credentials") -> HTTPException:
    """
    Handle authentication errors safely.

    Args:
        reason: Internal reason for authentication failure

    Returns:
        HTTPException with generic message
    """
    # Log internal reason
    logger.warning(f"Authentication failed: {reason}")

    # Always return generic message to prevent user enumeration
    return SecureHTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication failed",
        error_code="AUTH_FAILED",
        internal_detail=reason,
        headers={"WWW-Authenticate": "Bearer"}
    )


def handle_authorization_error(reason: str = "Insufficient permissions") -> HTTPException:
    """
    Handle authorization errors safely.

    Args:
        reason: Internal reason for authorization failure

    Returns:
        HTTPException with sanitized message
    """
    # Log internal reason
    logger.warning(f"Authorization failed: {reason}")

    return SecureHTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied",
        error_code="ACCESS_DENIED",
        internal_detail=reason
    )


def handle_rate_limit_error(retry_after: Optional[int] = None) -> HTTPException:
    """
    Handle rate limit errors.

    Args:
        retry_after: Seconds until rate limit resets

    Returns:
        HTTPException with rate limit message
    """
    headers = {}
    if retry_after:
        headers["Retry-After"] = str(retry_after)

    return SecureHTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Rate limit exceeded. Please try again later.",
        error_code="RATE_LIMIT_EXCEEDED",
        headers=headers
    )

def handle_external_api_error(service: str, error: Exception) -> HTTPException:
    """
    Handle external API errors safely.

    Args:
        service: Name of the external service
        error: The exception from the external API

    Returns:
        HTTPException with sanitized message
    """
    # Log full error internally
    logger.error(f"External API error ({service}): {error}")

    return SecureHTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"External service temporarily unavailable",
        error_code="EXTERNAL_SERVICE_ERROR",
        internal_detail=f"{service}: {str(error)}"
    )


def handle_generic_error(error: Exception, operation: str = "operation") -> HTTPException:
    """
    Handle generic errors safely.

    Args:
        error: The exception
        operation: Description of the operation that failed

    Returns:
        HTTPException with sanitized message
    """
    # Log full error internally
    logger.error(f"Error during {operation}: {error}", exc_info=True)

    return SecureHTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An error occurred while processing your request",
        error_code="INTERNAL_ERROR",
        internal_detail=str(error)
    )


# Error code constants
class ErrorCodes:
    """Standard error codes for the API."""

    # Authentication & Authorization
    AUTH_FAILED = "AUTH_FAILED"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    ACCESS_DENIED = "ACCESS_DENIED"

    # Validation
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_FIELD = "MISSING_FIELD"

    # Database
    DATABASE_ERROR = "DATABASE_ERROR"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"
    NOT_FOUND = "NOT_FOUND"

    # Blockchain
    BLOCKCHAIN_ERROR = "BLOCKCHAIN_ERROR"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    GAS_ERROR = "GAS_ERROR"
    TRANSACTION_REVERTED = "TRANSACTION_REVERTED"
    BLOCKCHAIN_UNAVAILABLE = "BLOCKCHAIN_UNAVAILABLE"

    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    # External Services
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"

    # Generic
    INTERNAL_ERROR = "INTERNAL_ERROR"
    TIMEOUT = "TIMEOUT"
