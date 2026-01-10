"""
Circuit breaker implementation for fault tolerance.
Prevents cascading failures by opening circuit after repeated failures.
"""
import logging
from pybreaker import CircuitBreaker, CircuitBreakerListener
from app.config import settings
from app.exceptions import CircuitBreakerOpenError

logger = logging.getLogger(__name__)


class LoggingListener(CircuitBreakerListener):
    """Circuit breaker listener that logs state changes."""

    def state_change(self, cb, old_state, new_state):
        """Log circuit breaker state transitions."""
        logger.warning(
            f"Circuit breaker '{cb.name}' state changed: {old_state.name} -> {new_state.name}"
        )

    def failure(self, cb, exc):
        """Log circuit breaker failures."""
        logger.error(
            f"Circuit breaker '{cb.name}' recorded failure: {type(exc).__name__}: {str(exc)}"
        )

    def success(self, cb):
        """Log circuit breaker successes."""
        logger.debug(f"Circuit breaker '{cb.name}' recorded success")


# Global circuit breakers for different services

database_breaker = CircuitBreaker(
    fail_max=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
    timeout_duration=settings.CIRCUIT_BREAKER_TIMEOUT,
    expected_exception=Exception,
    name="database",
    listeners=[LoggingListener()]
) if settings.CIRCUIT_BREAKER_ENABLED else None


thermal_calculation_breaker = CircuitBreaker(
    fail_max=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
    timeout_duration=settings.CIRCUIT_BREAKER_TIMEOUT,
    expected_exception=Exception,
    name="thermal_calculation",
    listeners=[LoggingListener()]
) if settings.CIRCUIT_BREAKER_ENABLED else None


external_api_breaker = CircuitBreaker(
    fail_max=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
    timeout_duration=settings.CIRCUIT_BREAKER_TIMEOUT,
    expected_exception=Exception,
    name="external_api",
    listeners=[LoggingListener()]
) if settings.CIRCUIT_BREAKER_ENABLED else None


def get_circuit_breaker_status(breaker: CircuitBreaker) -> dict:
    """
    Get status information for a circuit breaker.

    Returns:
        dict: Circuit breaker status including state, failure count, etc.
    """
    if not breaker:
        return {"enabled": False}

    return {
        "enabled": True,
        "name": breaker.name,
        "state": breaker.current_state.name,
        "failure_count": breaker.fail_counter,
        "failure_threshold": breaker.fail_max,
        "timeout_duration": breaker.timeout_duration,
        "last_failure_time": str(breaker.last_failure_time) if breaker.last_failure_time else None
    }


def get_all_circuit_breakers_status() -> dict:
    """
    Get status of all circuit breakers.

    Returns:
        dict: Status of all configured circuit breakers
    """
    return {
        "database": get_circuit_breaker_status(database_breaker),
        "thermal_calculation": get_circuit_breaker_status(thermal_calculation_breaker),
        "external_api": get_circuit_breaker_status(external_api_breaker)
    }


def execute_with_breaker(breaker: CircuitBreaker, func, *args, **kwargs):
    """
    Execute a function with circuit breaker protection.

    Args:
        breaker: Circuit breaker instance
        func: Function to execute
        *args, **kwargs: Function arguments

    Raises:
        CircuitBreakerOpenError: If circuit breaker is open

    Returns:
        Function result
    """
    if not breaker or not settings.CIRCUIT_BREAKER_ENABLED:
        # Circuit breaker disabled, execute directly
        return func(*args, **kwargs)

    try:
        return breaker.call(func, *args, **kwargs)
    except Exception as e:
        if breaker.current_state.name == "open":
            raise CircuitBreakerOpenError(
                service=breaker.name,
                message="Too many failures, circuit breaker is open",
                details={
                    "failure_count": breaker.fail_counter,
                    "last_failure": str(e)
                }
            )
        raise
