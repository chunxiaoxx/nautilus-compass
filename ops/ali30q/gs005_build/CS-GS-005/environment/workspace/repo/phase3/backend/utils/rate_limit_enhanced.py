"""
Enhanced rate limiting utilities with IP blacklist and dynamic limits.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request, HTTPException, status
from typing import Dict, Set, Optional
import time
import logging
import os

logger = logging.getLogger(__name__)

# IP Blacklist (in-memory, should use Redis in production)
_ip_blacklist: Set[str] = set()
_ip_violation_count: Dict[str, int] = {}
_ip_violation_timestamp: Dict[str, float] = {}

# Configuration
MAX_VIOLATIONS = int(os.getenv("RATE_LIMIT_MAX_VIOLATIONS", "5"))
BLACKLIST_DURATION = int(os.getenv("RATE_LIMIT_BLACKLIST_DURATION", "3600"))  # 1 hour
VIOLATION_RESET_TIME = int(os.getenv("RATE_LIMIT_VIOLATION_RESET", "300"))  # 5 minutes


def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request.
    Handles X-Forwarded-For header for proxied requests.

    Args:
    request: FastAPI request object

    Returns:
        Client IP address
    """
    # Check X-Forwarded-For header (for proxied requests)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP in the chain
        return forwarded.split(",")[0].strip()

    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct connection IP
    return request.client.host if request.client else "unknown"


def is_ip_blacklisted(ip: str) -> bool:
    """
    Check if IP is blacklisted.

    Args:
        ip: IP address to check

    Returns:
        True if blacklisted, False otherwise
    """
    if ip in _ip_blacklist:
        # Check if blacklist duration has expired
        if ip in _ip_violation_timestamp:
            elapsed = time.time() - _ip_violation_timestamp[ip]
            if elapsed > BLACKLIST_DURATION:
                # Remove from blacklist
                _ip_blacklist.discard(ip)
                _ip_violation_count.pop(ip, None)
                _ip_violation_timestamp.pop(ip, None)
                logger.info(f"IP {ip} removed from blacklist after {elapsed:.0f} seconds")
                return False
        return True
    return False


def record_rate_limit_violation(ip: str) -> None:
    """
    Record a rate limit violation for an IP.
    Blacklist IP if violations exceed threshold.

    Args:
        ip: IP address that violated rate limit
    """
    current_time = time.time()

    # Reset violation count if enough time has passed
    if ip in _ip_violation_timestamp:
        elapsed = current_time - _ip_violation_timestamp[ip]
        if elapsed > VIOLATION_RESET_TIME:
            _ip_violation_count[ip] = 0

    # Increment violation count
    _ip_violation_count[ip] = _ip_violation_count.get(ip, 0) + 1
    _ip_violation_timestamp[ip] = current_time

    violations = _ip_violation_count[ip]
    logger.warning(f"Rate limit violation from IP {ip} (count: {violations})")

    # Blacklist if threshold exceeded
    if violations >= MAX_VIOLATIONS:
        _ip_blacklist.add(ip)
        logger.error(f"IP {ip} blacklisted after {violations} violations")


def check_ip_blacklist(request: Request) -> None:
    """
    Middleware function to check IP blacklist.

    Args:
        request: FastAPI request object

    Raises:
        HTTPException: If IP is blacklisted
    """
    ip = get_client_ip(request)

    if is_ip_blacklisted(ip):
        logger.warning(f"Blocked request from blacklisted IP: {ip}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Access denied",
                "error_code": "IP_BLACKLISTED"
            }
        )


def get_blacklist_stats() -> Dict:
    """
    Get blacklist statistics.

    Returns:
        Dict with blacklist stats
    """
    return {
        "blacklisted_ips": len(_ip_blacklist),
        "ips_with_violations": len(_ip_violation_count),
        "total_violations": sum(_ip_violation_count.values())
    }

def clear_blacklist() -> None:
    """
    Clear all blacklisted IPs (admin function).
    """
    _ip_blacklist.clear()
    _ip_violation_count.clear()
    _ip_violation_timestamp.clear()
    logger.info("IP blacklist cleared")


def manually_blacklist_ip(ip: str, duration: Optional[int] = None) -> None:
    """
    Manually blacklist an IP address.

    Args:
        ip: IP address to blacklist
        duration: Optional custom duration in seconds
    """
    _ip_blacklist.add(ip)
    _ip_violation_timestamp[ip] = time.time()
    if duration:
        # Store custom duration (would need additional data structure)
        pass
    logger.warning(f"IP {ip} manually blacklisted")


def manually_whitelist_ip(ip: str) -> None:
    """
    Manually remove an IP from blacklist.

    Args:
        ip: IP address to whitelist
    """
    _ip_blacklist.discard(ip)
    _ip_violation_count.pop(ip, None)
    _ip_violation_timestamp.pop(ip, None)
    logger.info(f"IP {ip} manually whitelisted")


# Rate limit configurations for different endpoint types
class RateLimits:
    """Standard rate limits for different endpoint types."""

    # Authentication endpoints (strict)
    AUTH_LOGIN = "5/minute"
    AUTH_REGISTER = "3/minute"
    AUTH_PASSWORD_RESET = "3/hour"

    # Admin endpoints (very strict)
    ADMIN_WRITE = "5/hour"
    ADMIN_READ = "30/hour"

    # Public read endpoints
    PUBLIC_READ = "100/minute"
    PUBLIC_LIST = "50/minute"

    # Authenticated write endpoints
    AUTHENTICATED_WRITE = "30/minute"
    AUTHENTICATED_READ = "100/minute"

    # Health and monitoring
    HEALTH_CHECK = "30/minute"
    METRICS = "30/minute"

    # CSRF token
    CSRF_TOKEN = "20/minute"

    # Cache management
    CACHE_CLEAR = "5/hour"
    CACHE_STATS = "30/minute"

    # Blockchain operations (expensive)
    BLOCKCHAIN_WRITE = "10/minute"
    BLOCKCHAIN_READ = "50/minute"


def create_limiter(enabled: bool = True) -> Limiter:
    """
    Create a rate limiter instance.

    Args:
        enabled: Whether rate limiting is enabled

    Returns:
        Limiter instance
    """
    return Limiter(
        key_func=get_remote_address,
        default_limits=["200/hour"],
        enabled=enabled,
        headers_enabled=True,
        swallow_errors=False
    )


def get_rate_limit_headers(request: Request) -> Dict[str, str]:
    """
    Get rate limit headers for response.

    Args:
        request: FastAPI request object

    Returns:
        Dict of rate limit headers
    """
    # These would be populated by SlowAPI middleware
    return {
        "X-RateLimit-Limit": request.state.view_rate_limit if hasattr(request.state, "view_rate_limit") else "unknown",
        "X-RateLimit-Remaining": str(request.state.view_rate_remaining) if hasattr(request.state, "view_rate_remaining") else "unknown",
        "X-RateLimit-Reset": str(request.state.view_rate_reset) if hasattr(request.state, "view_rate_reset") else "unknown"
    }


# Example usage:
"""
from fastapi import APIRouter, Request, Depends
from slowapi import Limiter
from utils.rate_limit_enhanced import (
    RateLimits,
    check_ip_blacklist,
    record_rate_limit_violation
)
from utils.auth import get_current_admin_user

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
@router.post("/admin/cache/clear")
@limiter.limit(RateLimits.ADMIN_WRITE)
async def clear_cache(
    request: Request,
    admin: User = Depends(get_current_admin_user)
):
    # Check IP blacklist
    check_ip_blacklist(request)

    # Clear cache logic
    ...
"""
