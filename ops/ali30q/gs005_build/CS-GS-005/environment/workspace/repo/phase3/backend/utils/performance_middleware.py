"""
Performance monitoring middleware for FastAPI.
Tracks request/response times and logs slow requests.
"""
import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

logger = logging.getLogger(__name__)


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware to monitor API performance.

    Features:
    - Track request/response times
    - Log slow requests
    - Add performance headers to responses
    """

    def __init__(self, app, slow_threshold: float = 1.0):
        """
        Initialize middleware.

        Args:
            app: FastAPI application
            slow_threshold: Threshold in seconds for slow request warning (default: 1.0s)
        """
        super().__init__(app)
        self.slow_threshold = slow_threshold

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and measure performance."""

        # Start timer
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate elapsed time
        elapsed = time.time() - start_time
        elapsed_ms = elapsed * 1000

        # Add performance header
        response.headers["X-Response-Time"] = f"{elapsed_ms:.2f}ms"

        # Log request details
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": f"{elapsed_ms:.2f}",
        }

        # Log slow requests
        if elapsed > self.slow_threshold:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {elapsed_ms:.2f}ms (status: {response.status_code})"
            )
        else:
            logger.info(
                f"{request.method} {request.url.path} "
                f"- {response.status_code} - {elapsed_ms:.2f}ms"
            )

        return response


class RequestCounterMiddleware(BaseHTTPMiddleware):
    """
    Middleware to count requests per endpoint.
    Useful for identifying hot paths.
    """

    def __init__(self, app):
        super().__init__(app)
        self.request_counts = {}
        self.total_time = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Count requests and track total time per endpoint."""

        endpoint = f"{request.method} {request.url.path}"

        # Start timer
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate elapsed time
        elapsed = time.time() - start_time

        # Update counters
        if endpoint not in self.request_counts:
            self.request_counts[endpoint] = 0
            self.total_time[endpoint] = 0.0

        self.request_counts[endpoint] += 1
        self.total_time[endpoint] += elapsed

        return response

    def get_stats(self):
        """Get request statistics."""
        stats = []
        for endpoint, count in self.request_counts.items():
            avg_time = self.total_time[endpoint] / count if count > 0 else 0
            stats.append({
                "endpoint": endpoint,
                "count": count,
                "total_time": f"{self.total_time[endpoint]:.2f}s",
                "avg_time": f"{avg_time * 1000:.2f}ms"
            })

        # Sort by count descending
        stats.sort(key=lambda x: x["count"], reverse=True)
        return stats

    def reset_stats(self):
        """Reset all statistics."""
        self.request_counts.clear()
        self.total_time.clear()


# Global instance for request counter
_request_counter = None


def get_request_counter() -> RequestCounterMiddleware:
    """Get global request counter instance."""
    return _request_counter


def set_request_counter(counter: RequestCounterMiddleware):
    """Set global request counter instance."""
    global _request_counter
    _request_counter = counter
