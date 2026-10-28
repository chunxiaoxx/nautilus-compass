"""
JSON validation middleware for FastAPI.
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from utils.security_validators import validate_json_depth, validate_json_size
import json
import logging

logger = logging.getLogger(__name__)


class JSONValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate JSON request depth and size.
    Prevents DoS attacks via deeply nested or large JSON payloads.
    """

    def __init__(self, app, max_depth: int = 10, max_items: int = 1000, max_body_size: int = 10 * 1024 * 1024):
        """
        Initialize JSON validation middleware.

        Args:
            app: FastAPI application
            max_depth: Maximum JSON nesting depth
            max_items: Maximum items in arrays/objects
            max_body_size: Maximum request body size in bytes (default 10MB)
        """
        super().__init__(app)
        self.max_depth = max_depth
        self.max_items = max_items
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next):
        """
        Process request and validate JSON if present.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response from next handler
        """
        # Only validate JSON requests
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type.lower():
            return await call_next(request)

        # Check content length
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                if length > self.max_body_size:
                    logger.warning(f"Request body too large: {length} bytes (max: {self.max_body_size})")
                    raise HTTPException(
                        status_code=413,
                        detail=f"Request body too large. Maximum size: {self.max_body_size} bytes"
                    )
            except ValueError:
                pass

        # Read and validate JSON body
        try:
            body = await request.body()

            # Check actual body size
            if len(body) > self.max_body_size:
                logger.warning(f"Request body too large: {len(body)} bytes (max: {self.max_body_size})")
                raise HTTPException(
                    status_code=413,
                    detail=f"Request body too large. Maximum size: {self.max_body_size} bytes"
                )

            if body:
                try:
                    data = json.loads(body)

                    # Validate JSON depth
                    validate_json_depth(data, self.max_depth)

                    # Validate JSON size
                    validate_json_size(data, self.max_items)

                except json.JSONDecodeError:
                    # Let FastAPI handle JSON decode errors
                    pass
                except ValueError as e:
                    logger.warning(f"JSON validation failed: {e}")
                    raise HTTPException(
                        status_code=400,
                        detail=str(e)
                    )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in JSON validation middleware: {e}")

        return await call_next(request)
