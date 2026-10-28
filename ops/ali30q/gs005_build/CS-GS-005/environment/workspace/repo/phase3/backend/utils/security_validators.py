"""
Security validation utilities.
"""
import os
import re
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


def validate_environment_variables() -> Dict[str, Any]:
    """
    Validate critical environment variables at startup.

    Returns:
        Dict with validation results

    Raises:
        ValueError: If critical security requirements are not met
    """
    errors = []
    warnings = []

    # Check JWT_SECRET
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        errors.append("JWT_SECRET environment variable is required")
    elif len(jwt_secret) < 32:
        errors.append("JWT_SECRET must be at least 32 characters long")
    elif jwt_secret in ["your-secret-key-change-in-production", "secret", "changeme", "test"]:
        errors.append("JWT_SECRET cannot use default or weak values")

    # Check CSRF_SECRET_KEY
    csrf_secret = os.getenv("CSRF_SECRET_KEY")
    if not csrf_secret:
        errors.append("CSRF_SECRET_KEY environment variable is required")
    elif len(csrf_secret) < 32:
        errors.append("CSRF_SECRET_KEY must be at least 32 characters long")
    elif csrf_secret in ["your-csrf-secret-key-change-in-production", "secret", "changeme", "test"]:
        errors.append("CSRF_SECRET_KEY cannot use default or weak values")

    # Check ENVIRONMENT
    environment = os.getenv("ENVIRONMENT", "development")
    if environment not in ["development", "staging", "production"]:
        warnings.append(f"ENVIRONMENT '{environment}' is not standard (use: development, staging, production)")

    # Check DEBUG mode in production
    debug = os.getenv("DEBUG", "false").lower() == "true"
    if environment == "production" and debug:
        errors.append("DEBUG mode must be disabled in production environment")

    # Check FORCE_HTTPS in production
    force_https = os.getenv("FORCE_HTTPS", "false").lower() == "true"
    if environment == "production" and not force_https:
        warnings.append("FORCE_HTTPS should be enabled in production environment")

    # Check DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        errors.append("DATABASE_URL environment variable is required")
    elif "postgres:postgres@" in database_url:
        warnings.append("Database is using default password 'postgres', please use a strong password")

    # Check CORS_ORIGINS in production
    cors_origins = os.getenv("CORS_ORIGINS", "")
    if environment == "production" and ("*" in cors_origins or not cors_origins):
        warnings.append("CORS_ORIGINS should be restricted to specific domains in production")

    # Check Infura/RPC URLs
    sepolia_rpc = os.getenv("SEPOLIA_RPC_URL", "")
    if "c84e7bf6be0f481898e4bfd3c062fd2b" in sepolia_rpc:
        warnings.append("Using example Infura project ID, please replace with your own")

    # Check encryption password
    key_encryption_password = os.getenv("KEY_ENCRYPTION_PASSWORD", "")
    if key_encryption_password == "SecureTestPassword2024!@#":
        warnings.append("Using example encryption password, please replace with a strong random password")

    # Log results
    if errors:
        error_msg = "Security validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        logger.error(error_msg)
        raise ValueError(error_msg)

    if warnings:
        warning_msg = "Security warnings:\n" + "\n".join(f"  - {w}" for w in warnings)
        logger.warning(warning_msg)

    logger.info("Environment security validation passed")

    return {
        "status": "passed",
        "errors": errors,
        "warnings": warnings,
        "environment": environment,
        "debug": debug,
        "force_https": force_https
    }


def sanitize_log_data(data: Any) -> Any:
    """
    Sanitize sensitive information from log data.

    Args:
        data: Data to sanitize (str, dict, list, etc.)

    Returns:
        Sanitized data with sensitive information masked
    """
    if isinstance(data, str):
        return _sanitize_string(data)
    elif isinstance(data, dict):
        return {k: sanitize_log_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_log_data(item) for item in data]
    else:
        return data


def _sanitize_string(text: str) -> str:
    """
    Sanitize sensitive patterns in strings.

    Args:
        text: String to sanitize

    Returns:
        Sanitized string with sensitive data masked
    """
    # Mask JWT tokens
    text = re.sub(
        r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*',
        '[JWT_TOKEN_REDACTED]',
        text
    )

    # Mask API keys (nau_xxx format)
    text = re.sub(
        r'nau_[a-f0-9]{32,}',
        '[API_KEY_REDACTED]',
        text
    )

    # Mask private keys (0x followed by 64 hex chars)
    text = re.sub(
        r'0x[a-fA-F0-9]{64}',
        '[PRIVATE_KEY_REDACTED]',
        text
    )

    # Mask passwords in URLs
    text = re.sub(
        r'://([^:]+):([^@]+)@',
        r'://\1:[PASSWORD_REDACTED]@',
        text
    )

    # Mask email addresses (partial)
    text = re.sub(
        r'([a-zA-Z0-9._%+-]{1,3})[a-zA-Z0-9._%+-]*@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        r'\1***@\2',
        text
    )

    # Mask credit card numbers
    text = re.sub(
        r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        '[CARD_NUMBER_REDACTED]',
        text
    )

    # Mask common secret patterns
    sensitive_keys = [
        'password', 'secret', 'token', 'key', 'api_key', 'apikey',
        'private_key', 'privatekey', 'access_token', 'refresh_token'
    ]

    for key in sensitive_keys:
        # Match patterns like "password": "value" or password=value
        text = re.sub(
            rf'({key}["\']?\s*[:=]\s*["\']?)([^"\',\s}}]+)',
            r'\1[REDACTED]',
            text,
            flags=re.IGNORECASE
        )

    return text


def validate_json_depth(data: Any, max_depth: int = 10, current_depth: int = 0) -> bool:
    """
    Validate JSON depth to prevent DoS attacks.

    Args:
        data: JSON data to validate
        max_depth: Maximum allowed nesting depth
        current_depth: Current depth (used internally)

    Returns:
        True if valid, False if exceeds max depth

    Raises:
        ValueError: If depth exceeds maximum
    """
    if current_depth > max_depth:
        raise ValueError(f"JSON depth exceeds maximum allowed depth of {max_depth}")

    if isinstance(data, dict):
        for value in data.values():
            validate_json_depth(value, max_depth, current_depth + 1)
    elif isinstance(data, list):
        for item in data:
            validate_json_depth(item, max_depth, current_depth + 1)

    return True


def validate_json_size(data: Any, max_items: int = 1000) -> bool:
    """
    Validate JSON array/object size to prevent DoS attacks.

    Args:
        data: JSON data to validate
        max_items: Maximum allowed items in arrays/objects

    Returns:
        True if valid

    Raises:
        ValueError: If size exceeds maximum
    """
    if isinstance(data, dict):
        if len(data) > max_items:
            raise ValueError(f"JSON object size exceeds maximum of {max_items} items")
        for value in data.values():
            validate_json_size(value, max_items)
    elif isinstance(data, list):
        if len(data) > max_items:
            raise ValueError(f"JSON array size exceeds maximum of {max_items} items")
        for item in data:
            validate_json_size(item, max_items)

    return True


def validate_file_upload(
    filename: str,
    content_type: str,
    file_size: int,
    allowed_extensions: list = None,
    max_size: int = 10 * 1024 * 1024  # 10MB default
) -> Dict[str, Any]:
    """
    Validate file upload parameters.

    Args:
        filename: Name of the uploaded file
        content_type: MIME type of the file
        file_size: Size of the file in bytes
        allowed_extensions: List of allowed file extensions
        max_size: Maximum allowed file size in bytes

    Returns:
        Dict with validation results

    Raises:
        ValueError: If validation fails
    """
    if allowed_extensions is None:
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.txt', '.csv']

    # Check file size
    if file_size > max_size:
        raise ValueError(f"File size {file_size} bytes exceeds maximum of {max_size} bytes")

    # Check file extension
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise ValueError(f"File extension {file_ext} not allowed. Allowed: {', '.join(allowed_extensions)}")

    # Sanitize filename
    safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        raise ValueError("Invalid filename: path traversal detected")

    return {
        "valid": True,
        "original_filename": filename,
        "safe_filename": safe_filename,
        "extension": file_ext,
        "content_type": content_type,
        "size": file_size
    }
