"""
Global exception handlers for HomeRack API.
Provides consistent error responses and logging for all exceptions.
"""
import logging
import uuid
from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.exceptions import HomeRackBaseException

logger = logging.getLogger(__name__)


async def homerack_exception_handler(request: Request, exc: HomeRackBaseException) -> JSONResponse:
    """
    Handle custom HomeRack exceptions.

    Returns structured error response with request ID for tracing.
    """
    request_id = request.state.request_id if hasattr(request.state, "request_id") else str(uuid.uuid4())

    logger.error(
        f"HomeRack exception",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_code": exc.error_code,
            "error_message": exc.message,
            "status_code": exc.status_code,
            "details": exc.details
        }
    )

    response_body = {
        "error": {
            "message": exc.message,
            "code": exc.error_code,
            "details": exc.details,
            "request_id": request_id
        }
    }

    return JSONResponse(
        status_code=exc.status_code,
        content=response_body
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Returns detailed field-level validation errors.
    """
    request_id = request.state.request_id if hasattr(request.state, "request_id") else str(uuid.uuid4())

    # Extract field errors
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:])  # Skip 'body' prefix
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(
        f"Validation error",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "validation_errors": errors
        }
    )

    response_body = {
        "error": {
            "message": "Validation failed",
            "code": "VALIDATION_ERROR",
            "details": {
                "errors": errors
            },
            "request_id": request_id
        }
    }

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_body
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handle SQLAlchemy database errors.

    Converts database exceptions to consistent error responses.
    """
    request_id = request.state.request_id if hasattr(request.state, "request_id") else str(uuid.uuid4())

    logger.error(
        f"Database error",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
            "error_message": str(exc)
        },
        exc_info=True
    )

    # Don't expose internal database errors to clients
    response_body = {
        "error": {
            "message": "Database operation failed",
            "code": "DATABASE_ERROR",
            "details": {
                "type": type(exc).__name__
            },
            "request_id": request_id
        }
    }

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=response_body
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Logs full stack trace but returns sanitized error to client.
    """
    request_id = request.state.request_id if hasattr(request.state, "request_id") else str(uuid.uuid4())

    logger.critical(
        f"Unhandled exception",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
            "error_message": str(exc)
        },
        exc_info=True
    )

    # Don't expose internal errors in production
    from app.config import settings
    error_message = str(exc) if settings.DEBUG else "An unexpected error occurred"

    response_body = {
        "error": {
            "message": error_message,
            "code": "INTERNAL_ERROR",
            "details": {},
            "request_id": request_id
        }
    }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_body
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(HomeRackBaseException, homerack_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered")
