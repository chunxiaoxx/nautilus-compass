"""
Enhanced security validation utilities with OAuth and optional features support.
"""
import os
import re
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


def validate_environment_variables_enhanced() -> Dict[str, Any]:
    """
    Enhanced validation of environment variables at startup.
    Includes support for optional features like OAuth, Redis, Blockchain, etc.

    Returns:
        Dict with validation results including optional features status

    Raises:
        ValueError: If critical security requirements are not met
    """
    errors = []
    warnings = []
    optional_features = {}

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

    # Check OAuth configurations (optional features)
    github_client_id = os.getenv("GITHUB_CLIENT_ID")
    github_client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    github_redirect_uri = os.getenv("GITHUB_REDIRECT_URI")

    if github_client_id and github_client_secret and github_redirect_uri:
        optional_features["github_oauth"] = True
        logger.info("✅ GitHub OAuth is configured and enabled")
    else:
        optional_features["github_oauth"] = False
        if github_client_id or github_client_secret or github_redirect_uri:
            warnings.append("GitHub OAuth is partially configured. All three variables (GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, GITHUB_REDIRECT_URI) are required")
        else:
            logger.info("ℹ️  GitHub OAuth is not configured (optional feature)")

    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

    if google_client_id and google_client_secret and google_redirect_uri:
        optional_features["google_oauth"] = True
        logger.info("✅ Google OAuth is configured and enabled")
    else:
        optional_features["google_oauth"] = False
        if google_client_id or google_client_secret or google_redirect_uri:
            warnings.append("Google OAuth is partially configured. All three variables (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI) are required")
        else:
            logger.info("ℹ️  Google OAuth is not configured (optional feature)")

    # Check Redis configuration (optional but recommended)
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        optional_features["redis_cache"] = True
        logger.info("✅ Redis cache is configured and enabled")
    else:
        optional_features["redis_cache"] = False
        warnings.append("Redis is not configured. Caching will be disabled, which may impact performance")

    # Check Blockchain configuration (optional)
    sepolia_rpc = os.getenv("SEPOLIA_RPC_URL", "")
    ethereum_rpc = os.getenv("ETHEREUM_RPC_URL", "")

    if sepolia_rpc or ethereum_rpc:
        optional_features["blockchain"] = True
        if "c84e7bf6be0f481898e4bfd3c062fd2b" in sepolia_rpc:
            warnings.append("Using example Infura project ID, please replace with your own")
        logger.info("✅ Blockchain integration is configured and enabled")
    else:
        optional_features["blockchain"] = False
        logger.info("ℹ️  Blockchain integration is not configured (optional feature)")

    # Check LLM API keys (optional)
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if openai_key and openai_key != "your_openai_api_key_here":
        optional_features["openai"] = True
        logger.info("✅ OpenAI API is configured and enabled")
    else:
        optional_features["openai"] = False
        logger.info("ℹ️  OpenAI API is not configured (optional feature)")

    if anthropic_key and anthropic_key != "your_anthropic_api_key_here":
        optional_features["anthropic"] = True
        logger.info("✅ Anthropic API is configured and enabled")
    else:
        optional_features["anthropic"] = False
        logger.info("ℹ️  Anthropic API is not configured (optional feature)")

    # Check encryption password
    key_encryption_password = os.getenv("KEY_ENCRYPTION_PASSWORD", "")
    if key_encryption_password and key_encryption_password == "SecureTestPassword2024!@#":
        warnings.append("Using example encryption password, please replace with a strong random password")

    # Log results
    if errors:
        error_msg = "Security validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        logger.error(error_msg)
        raise ValueError(error_msg)

    if warnings:
        warning_msg = "Security warnings:\n" + "\n".join(f"  - {w}" for w in warnings)
        logger.warning(warning_msg)

    logger.info("✅ Environment security validation passed")
    logger.info(f"📊 Optional features status: {optional_features}")

    return {
        "status": "passed",
        "errors": errors,
        "warnings": warnings,
        "environment": environment,
        "debug": debug,
        "force_https": force_https,
        "optional_features": optional_features
    }


def get_optional_features() -> Dict[str, bool]:
    """
    Get the status of optional features without full validation.

    Returns:
        Dict with feature names and their enabled status
    """
    features = {}

    # GitHub OAuth
    features["github_oauth"] = all([
        os.getenv("GITHUB_CLIENT_ID"),
        os.getenv("GITHUB_CLIENT_SECRET"),
        os.getenv("GITHUB_REDIRECT_URI")
    ])

    # Google OAuth
    features["google_oauth"] = all([
        os.getenv("GOOGLE_CLIENT_ID"),
        os.getenv("GOOGLE_CLIENT_SECRET"),
        os.getenv("GOOGLE_REDIRECT_URI")
    ])

    # Redis
    features["redis_cache"] = bool(os.getenv("REDIS_URL"))

    # Blockchain
    features["blockchain"] = bool(
        os.getenv("SEPOLIA_RPC_URL") or os.getenv("ETHEREUM_RPC_URL")
    )

    # OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    features["openai"] = bool(openai_key and openai_key != "your_openai_api_key_here")

    # Anthropic
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    features["anthropic"] = bool(anthropic_key and anthropic_key != "your_anthropic_api_key_here")

    return features


def validate_wallet_address(address: str) -> bool:
    """
    Validate Ethereum wallet address format.

    Args:
        address: Wallet address to validate

    Returns:
        True if valid, False otherwise
    """
    if not address:
        return False

    # Must start with 0x and be 42 characters total (0x + 40 hex chars)
    pattern = r'^0x[a-fA-F0-9]{40}$'
    return bool(re.match(pattern, address))


def sanitize_error_message(error: Exception, include_details: bool = False) -> str:
    """
    Sanitize error messages to prevent information leakage.

    Args:
        error: The exception to sanitize
        include_details: Whether to include error details (only in development)

    Returns:
        Sanitized error message
    """
    error_str = str(error)

    # In production, return generic messages
    if not include_details:
        # Map specific error types to generic messages
        if "database" in error_str.lower() or "sql" in error_str.lower():
            return "Database operation failed"
        elif "connection" in error_str.lower():
            return "Connection error occurred"
        elif "timeout" in error_str.lower():
            return "Operation timed out"
        elif "permission" in error_str.lower() or "forbidden" in error_str.lower():
            return "Permission denied"
        elif "not found" in error_str.lower():
            return "Resource not found"
        else:
            return "An error occurred while processing your request"

    # In development, sanitize but keep some details
    from utils.security_validators import sanitize_log_data
    return sanitize_log_data(error_str)


def validate_input_length(
    value: str,
    field_name: str,
    min_length: int = 0,
    max_length: int = 1000
) -> None:
    """
    Validate input string length.

    Args:
        value: String to validate
        field_name: Name of the field (for error messages)
        min_length: Minimum allowed length
        max_length: Maximum allowed length

    Raises:
        ValueError: If validation fails
    """
    if not value:
        if min_length > 0:
            raise ValueError(f"{field_name} is required")
        return

    length = len(value)

    if length < min_length:
        raise ValueError(f"{field_name} must be at least {min_length} characters")

    if length > max_length:
        raise ValueError(f"{field_name} must not exceed {max_length} characters")


def validate_numeric_range(
    value: int | float,
    field_name: str,
    min_value: int | float = None,
    max_value: int | float = None
) -> None:
    """
    Validate numeric value range.

    Args:
        value: Number to validate
        field_name: Name of the field (for error messages)
      min_value: Minimum allowed value
        max_value: Maximum allowed value

  Raises:
        ValueError: If validation fails
    """
    if min_value is not None and value < min_value:
        raise ValueError(f"{field_name} must be at least {min_value}")

    if max_value is not None and value > max_value:
        raise ValueError(f"{field_name} must not exceed {max_value}")
