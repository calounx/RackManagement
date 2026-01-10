"""
Custom exception hierarchy for HomeRack API.
Provides structured error handling with appropriate HTTP status codes.
"""
from typing import Any, Dict, Optional


class HomeRackBaseException(Exception):
    """Base exception for all HomeRack custom exceptions."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error": {
                "message": self.message,
                "code": self.error_code,
                "details": self.details
            }
        }


class DatabaseError(HomeRackBaseException):
    """Database connection or query failures."""

    def __init__(self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=503,
            error_code="DATABASE_ERROR",
            details=details
        )


class ResourceNotFoundError(HomeRackBaseException):
    """Resource not found (404)."""

    def __init__(self, resource: str, identifier: Any, details: Optional[Dict[str, Any]] = None):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(
            message=message,
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details=details or {"resource": resource, "identifier": str(identifier)}
        )


class ResourceConflictError(HomeRackBaseException):
    """Resource conflict (409) - duplicate, overlap, etc."""

    def __init__(self, message: str, conflict_type: str = "duplicate", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=409,
            error_code="RESOURCE_CONFLICT",
            details=details or {"conflict_type": conflict_type}
        )


class ValidationError(HomeRackBaseException):
    """Enhanced validation error (422)."""

    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details or {"field": field} if field else details
        )


class ExternalServiceError(HomeRackBaseException):
    """External API or service failures."""

    def __init__(
        self,
        service: str,
        message: str = "External service unavailable",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"{service}: {message}",
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details or {"service": service}
        )


class RateLimitExceededError(HomeRackBaseException):
    """Rate limit violation (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details or {"retry_after": retry_after}
        )


class CircuitBreakerOpenError(HomeRackBaseException):
    """Circuit breaker is open, service temporarily unavailable."""

    def __init__(
        self,
        service: str,
        message: str = "Service temporarily unavailable",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"{service} circuit breaker is open: {message}",
            status_code=503,
            error_code="CIRCUIT_BREAKER_OPEN",
            details=details or {"service": service}
        )


class TimeoutError(HomeRackBaseException):
    """Request timeout (408)."""

    def __init__(
        self,
        operation: str,
        timeout_seconds: int,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Operation '{operation}' timed out after {timeout_seconds} seconds"
        super().__init__(
            message=message,
            status_code=408,
            error_code="REQUEST_TIMEOUT",
            details=details or {"operation": operation, "timeout_seconds": timeout_seconds}
        )


class ThermalAnalysisError(HomeRackBaseException):
    """Thermal analysis calculation failures."""

    def __init__(self, message: str = "Thermal analysis failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="THERMAL_ANALYSIS_ERROR",
            details=details
        )


class CableValidationError(HomeRackBaseException):
    """Cable routing or specification validation failures."""

    def __init__(self, message: str, validation_type: str = "general", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="CABLE_VALIDATION_ERROR",
            details=details or {"validation_type": validation_type}
        )


class RackCapacityError(HomeRackBaseException):
    """Rack capacity exceeded (weight, power, U-space)."""

    def __init__(
        self,
        capacity_type: str,
        current_value: float,
        max_value: float,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{capacity_type} capacity exceeded: {current_value} / {max_value}"
        super().__init__(
            message=message,
            status_code=422,
            error_code="RACK_CAPACITY_ERROR",
            details=details or {
                "capacity_type": capacity_type,
                "current": current_value,
                "maximum": max_value
            }
        )
