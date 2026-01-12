"""
Database configuration and session management with PostgreSQL support
"""
from sqlalchemy import create_engine, text, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy.exc import OperationalError
import time
import logging
from .config import settings

logger = logging.getLogger(__name__)

# Database URL from settings
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Determine database type
is_sqlite = SQLALCHEMY_DATABASE_URL.startswith("sqlite")
is_postgresql = SQLALCHEMY_DATABASE_URL.startswith("postgresql")

# Engine configuration
engine_kwargs = {
    "echo": settings.DB_ECHO,
}

# Configure pooling based on database type
if is_sqlite:
    # SQLite: Disable pooling and add thread check
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    engine_kwargs["poolclass"] = NullPool
    logger.info("Configured SQLite database with NullPool")
else:
    # PostgreSQL: Enable connection pooling
    engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_recycle": settings.DB_POOL_RECYCLE,
        "pool_pre_ping": settings.DB_POOL_PRE_PING,
        "poolclass": QueuePool,
    })
    logger.info(
        f"Configured PostgreSQL database with connection pool "
        f"(size={settings.DB_POOL_SIZE}, max_overflow={settings.DB_MAX_OVERFLOW})"
    )


def test_connection_with_retry(engine, max_attempts=None, delay=None):
    """
    Test database connection with retry logic.

    Args:
        engine: SQLAlchemy engine
        max_attempts: Maximum retry attempts (defaults to settings)
        delay: Delay between retries in seconds (defaults to settings)

    Returns:
        bool: True if connection successful

    Raises:
        OperationalError: If connection fails after all retries
    """
    max_attempts = max_attempts or settings.DB_CONNECT_RETRY_MAX_ATTEMPTS
    delay = delay or settings.DB_CONNECT_RETRY_DELAY

    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as conn:
                # Test the connection
                if is_sqlite:
                    conn.execute(text("SELECT 1"))
                else:
                    conn.execute(text("SELECT 1 as health"))
                logger.info(f"Database connection successful (attempt {attempt}/{max_attempts})")
                return True
        except OperationalError as e:
            if attempt < max_attempts:
                logger.warning(
                    f"Database connection failed (attempt {attempt}/{max_attempts}): {e}. "
                    f"Retrying in {delay} seconds..."
                )
                time.sleep(delay)
            else:
                logger.error(f"Database connection failed after {max_attempts} attempts: {e}")
                raise

    return False


# Create engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_kwargs)

# Test connection on startup with retry
try:
    test_connection_with_retry(engine)
except OperationalError as e:
    logger.error(f"Failed to establish database connection: {e}")
    raise


# Add event listeners for PostgreSQL
if is_postgresql:
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Event listener for new connections"""
        logger.debug("New database connection established")

    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """Event listener for connection checkout from pool"""
        logger.debug("Connection checked out from pool")

    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_conn, connection_record):
        """Event listener for connection checkin to pool"""
        logger.debug("Connection checked in to pool")


# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Dependency for getting DB session
def get_db():
    """
    Get database session with automatic cleanup.

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def health_check():
    """
    Perform database health check.

    Returns:
        dict: Health check result with status and details
    """
    try:
        with engine.connect() as conn:
            start_time = time.time()
            if is_sqlite:
                conn.execute(text("SELECT 1"))
            else:
                conn.execute(text("SELECT 1 as health"))
            query_time = time.time() - start_time

            # Get pool statistics for PostgreSQL
            pool_info = {}
            if is_postgresql:
                pool = engine.pool
                pool_info = {
                    "pool_size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "total_connections": pool.size() + pool.overflow(),
                }

            return {
                "status": "healthy",
                "database_type": "postgresql" if is_postgresql else "sqlite",
                "query_time_ms": round(query_time * 1000, 2),
                "pool_info": pool_info if pool_info else None,
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }
