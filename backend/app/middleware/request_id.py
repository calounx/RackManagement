"""
Request ID middleware for tracing requests through the system.
Adds unique request ID to each request for logging and debugging.
"""
import uuid
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add unique request ID to each request.

    The request ID is:
    - Generated for each incoming request
    - Stored in request.state for access by handlers
    - Included in response headers
    - Used for log correlation
    """

    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Store in request state for access by exception handlers
        request.state.request_id = request_id

        # Add to logger context (requires structlog or similar)
        # For now, we'll just include it in log messages

        # Log request start
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else None
            }
        )

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        # Log request completion
        logger.info(
            f"Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code
            }
        )

        return response
