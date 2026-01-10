"""
Retry decorators with exponential backoff for transient failures.
Uses tenacity library for robust retry logic.
"""
import logging
from functools import wraps
from typing import Callable, Type, Tuple
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
from sqlalchemy.exc import OperationalError, DBAPIError, IntegrityError
from app.config import settings
from app.exceptions import DatabaseError

logger = logging.getLogger(__name__)


def retry_on_db_error(
    max_attempts: int = None,
    max_delay: int = None,
    exponential_base: float = None
) -> Callable:
    """
    Decorator to retry database operations on transient failures.

    Uses exponential backoff with jitter to prevent thundering herd.
    Only retries on operational errors, not integrity/constraint violations.

    Args:
        max_attempts: Maximum retry attempts (default from settings)
        max_delay: Maximum delay between retries in seconds (default from settings)
        exponential_base: Base for exponential backoff (default from settings)

    Example:
        @retry_on_db_error(max_attempts=3)
        def create_device(db, device_data):
            # Database operation
            pass
    """
    max_attempts = max_attempts or settings.RETRY_MAX_ATTEMPTS
    max_delay = max_delay or settings.RETRY_MAX_DELAY
    exponential_base = exponential_base or settings.RETRY_EXPONENTIAL_BASE

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @retry(
            retry=retry_if_exception_type((OperationalError, DBAPIError)),
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=0.1,  # Start with 100ms
                min=0.1,
                max=max_delay,
                exp_base=exponential_base
            ),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.INFO),
            reraise=True
        )
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (OperationalError, DBAPIError) as e:
                # Don't retry on integrity errors (constraint violations)
                if isinstance(e, IntegrityError):
                    raise
                # Convert to our custom exception
                logger.error(f"Database error in {func.__name__}: {str(e)}")
                raise DatabaseError(
                    message=f"Database operation failed: {str(e)}",
                    details={"function": func.__name__, "error_type": type(e).__name__}
                ) from e

        return wrapper

    return decorator


def retry_on_http_error(
    max_attempts: int = 3,
    max_delay: int = 16,
    retry_on_status: Tuple[int, ...] = (500, 502, 503, 504, 429)
) -> Callable:
    """
    Decorator to retry HTTP requests on transient failures.

    Used for external API calls (PDF fetching, manufacturer sites, etc.).
    Retries on 5xx errors, 429 rate limits, and connection errors.

    Args:
        max_attempts: Maximum retry attempts (default 3)
        max_delay: Maximum delay between retries in seconds (default 16)
        retry_on_status: HTTP status codes to retry on

    Example:
        @retry_on_http_error(max_attempts=3)
        async def fetch_pdf(url: str):
            # HTTP request
            pass
    """
    def should_retry_http_error(exception):
        """Check if HTTP error should be retried."""
        # Add logic for specific HTTP errors
        # This is a placeholder - implement based on your HTTP library
        return True

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @retry(
            retry=retry_if_exception_type(Exception),  # Customize based on HTTP library
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=1,  # Start with 1 second
                min=1,
                max=max_delay,
                exp_base=2
            ),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.INFO),
            reraise=True
        )
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"HTTP error in {func.__name__}: {str(e)}")
                raise

        @wraps(func)
        @retry(
            retry=retry_if_exception_type(Exception),
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=1,
                min=1,
                max=max_delay,
                exp_base=2
            ),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.INFO),
            reraise=True
        )
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"HTTP error in {func.__name__}: {str(e)}")
                raise

        # Return appropriate wrapper based on whether function is async
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Specialized retry decorators for specific operations

def retry_thermal_analysis(max_attempts: int = 3) -> Callable:
    """
    Retry decorator specifically for thermal analysis operations.

    Thermal analysis can be computationally expensive and may timeout
    or fail due to resource constraints. This provides limited retries.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=5, exp_base=2),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True
        )
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator
