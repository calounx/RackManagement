"""
Comprehensive health check endpoints for monitoring and observability.
Provides liveness, readiness, startup, and detailed health checks.
"""
import logging
import os
import psutil
import shutil
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..api.dependencies import get_db
from ..config import settings
from ..utils.circuit_breaker import get_all_circuit_breakers_status
from ..cache import get_redis_cache

logger = logging.getLogger(__name__)
router = APIRouter()


def check_redis_connection() -> Dict[str, Any]:
    """Check Redis connectivity and return status."""
    if not settings.CACHE_ENABLED or not settings.REDIS_ENABLED:
        return {
            "status": "disabled",
            "message": "Redis caching is disabled"
        }

    try:
        cache = get_redis_cache()
        if cache.health_check():
            stats = cache.get_stats()
            return {
                "status": "up",
                "message": "Redis connection successful",
                **stats
            }
        else:
            return {
                "status": "down",
                "message": "Redis health check failed"
            }
    except Exception as e:
        return {
            "status": "down",
            "error": str(e),
            "message": "Redis connection failed"
        }


def check_disk_space() -> Dict[str, Any]:
    """Check available disk space."""
    try:
        # Check disk space for the application directory
        usage = shutil.disk_usage("/app")
        total_gb = usage.total / (1024 ** 3)
        used_gb = usage.used / (1024 ** 3)
        free_gb = usage.free / (1024 ** 3)
        percent_used = (usage.used / usage.total) * 100

        status_value = "healthy"
        if percent_used > 90:
            status_value = "critical"
        elif percent_used > 80:
            status_value = "warning"

        return {
            "status": status_value,
            "total_gb": round(total_gb, 2),
            "used_gb": round(used_gb, 2),
            "free_gb": round(free_gb, 2),
            "percent_used": round(percent_used, 2),
            "message": f"Disk space: {round(percent_used, 1)}% used"
        }
    except Exception as e:
        return {
            "status": "unknown",
            "error": str(e),
            "message": "Unable to check disk space"
        }


def check_memory_usage() -> Dict[str, Any]:
    """Check system memory usage."""
    try:
        memory = psutil.virtual_memory()
        total_gb = memory.total / (1024 ** 3)
        available_gb = memory.available / (1024 ** 3)
        used_gb = memory.used / (1024 ** 3)
        percent_used = memory.percent

        status_value = "healthy"
        if percent_used > 90:
            status_value = "critical"
        elif percent_used > 80:
            status_value = "warning"

        return {
            "status": status_value,
            "total_gb": round(total_gb, 2),
            "used_gb": round(used_gb, 2),
            "available_gb": round(available_gb, 2),
            "percent_used": round(percent_used, 2),
            "message": f"Memory: {round(percent_used, 1)}% used"
        }
    except Exception as e:
        return {
            "status": "unknown",
            "error": str(e),
            "message": "Unable to check memory usage"
        }


def check_database_detailed(db: Session) -> Dict[str, Any]:
    """Perform detailed database health check."""
    try:
        import time
        start_time = time.time()
        db.execute(text("SELECT 1"))
        latency_ms = (time.time() - start_time) * 1000

        # Extract database type and location
        db_url = settings.DATABASE_URL
        db_info = "sqlite"
        if "postgresql" in db_url:
            db_info = db_url.split("@")[-1] if "@" in db_url else "postgresql"

        return {
            "status": "up",
            "latency_ms": round(latency_ms, 2),
            "type": "postgresql" if "postgresql" in db_url else "sqlite",
            "location": db_info,
            "pool_size": settings.DB_POOL_SIZE if hasattr(settings, "DB_POOL_SIZE") else "N/A",
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "down",
            "error": str(e),
            "message": "Database connection failed"
        }


@router.get("/health", tags=["Health"])
async def basic_health_check():
    """
    Basic health check - returns simple status.
    Use this for basic uptime monitoring and frontend health checks.
    """
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/health/live", tags=["Health"])
async def liveness_check():
    """
    Liveness probe - checks if application is alive.

    Returns 200 if the application process is running.
    Use this for Kubernetes liveness probes.
    Does not check dependencies.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/startup", tags=["Health"])
async def startup_check(db: Session = Depends(get_db)):
    """
    Startup probe - checks if application has started successfully.

    Verifies critical dependencies are available:
    - Database connectivity

    Returns 200 if started, 503 if not ready.
    Use this for Kubernetes startup probes.
    """
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "started",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Application started successfully"
        }
    except Exception as e:
        logger.error(f"Startup check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "starting",
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Application still starting: {str(e)}"
            }
        )


@router.get("/health/ready", tags=["Health"])
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness probe - checks if application is ready to serve traffic.

    Verifies:
    - Database connectivity
    - Circuit breaker states

    Returns 200 if ready, 503 if not ready.
    Use this for Kubernetes readiness probes.
    """
    is_ready = True
    checks = {}

    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = {
            "status": "up",
            "message": "Database connection successful"
        }
    except Exception as e:
        is_ready = False
        checks["database"] = {
            "status": "down",
            "message": f"Database connection failed: {str(e)}"
        }
        logger.error(f"Readiness check failed - database: {e}")

    # Check circuit breakers
    circuit_breakers = get_all_circuit_breakers_status()
    open_breakers = [
        name for name, status in circuit_breakers.items()
        if status.get("enabled") and status.get("state") == "open"
    ]

    if open_breakers:
        is_ready = False
        checks["circuit_breakers"] = {
            "status": "degraded",
            "message": f"Circuit breakers open: {', '.join(open_breakers)}"
        }
    else:
        checks["circuit_breakers"] = {
            "status": "healthy",
            "message": "All circuit breakers closed"
        }

    response_body = {
        "status": "ready" if is_ready else "not_ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }

    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content=response_body
    )


@router.get("/health/detailed", tags=["Health"])
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check with comprehensive system status.

    Provides detailed information about:
    - Database connectivity and query latency
    - Redis connectivity (if enabled)
    - Disk space usage
    - Memory usage
    - Circuit breaker states and statistics
    - Configuration status
    - System information

    Returns detailed health metrics for monitoring dashboards.
    """
    checks: Dict[str, Any] = {}
    overall_status = "healthy"

    # Database check with detailed information
    checks["database"] = check_database_detailed(db)
    if checks["database"]["status"] != "up":
        overall_status = "unhealthy"

    # Redis check
    checks["redis"] = check_redis_connection()
    if checks["redis"]["status"] == "down":
        overall_status = "degraded"

    # Disk space check
    checks["disk"] = check_disk_space()
    if checks["disk"]["status"] == "critical":
        overall_status = "unhealthy"
    elif checks["disk"]["status"] == "warning" and overall_status == "healthy":
        overall_status = "degraded"

    # Memory usage check
    checks["memory"] = check_memory_usage()
    if checks["memory"]["status"] == "critical":
        overall_status = "unhealthy"
    elif checks["memory"]["status"] == "warning" and overall_status == "healthy":
        overall_status = "degraded"

    # Circuit breaker status
    circuit_breakers = get_all_circuit_breakers_status()
    checks["circuit_breakers"] = circuit_breakers

    # Check if any breakers are open
    open_breakers = [
        name for name, cb_status in circuit_breakers.items()
        if cb_status.get("enabled") and cb_status.get("state") == "open"
    ]
    if open_breakers:
        overall_status = "degraded"

    # Configuration status
    checks["configuration"] = {
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "rate_limiting_enabled": settings.RATE_LIMIT_ENABLED,
        "circuit_breaker_enabled": settings.CIRCUIT_BREAKER_ENABLED,
        "retry_enabled": settings.RETRY_ENABLED,
        "cache_enabled": settings.CACHE_ENABLED,
        "spec_fetch_enabled": settings.SPEC_FETCH_ENABLED
    }

    # Feature flags
    checks["features"] = {
        "api_reliability_patterns": True,
        "web_spec_fetching": settings.SPEC_FETCH_ENABLED,
        "cable_validation": True,
        "rack_validation": True,
        "thermal_analysis": True
    }

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": checks
    }


@router.get("/health/circuit-breakers", tags=["Health"])
async def circuit_breaker_status():
    """
    Get detailed circuit breaker status for all services.

    Returns state, failure counts, and configuration for each circuit breaker.
    Useful for monitoring and alerting.
    """
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "circuit_breakers": get_all_circuit_breakers_status()
    }


@router.get("/health/cache/stats", tags=["Health", "Cache"])
async def cache_stats():
    """
    Get Redis cache statistics.

    Returns:
    - Cache hit/miss rates
    - Memory usage
    - Connected clients
    - Cache availability status
    """
    try:
        cache = get_redis_cache()
        stats = cache.get_stats()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cache": stats
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cache statistics: {str(e)}"
        )


@router.post("/health/cache/clear", tags=["Health", "Cache"])
async def clear_cache():
    """
    Clear all cache entries (DANGEROUS - use with caution).

    This endpoint clears the entire Redis cache.
    Use this for testing or after major data changes.

    Note: This should be restricted to admin users in production.
    """
    try:
        cache = get_redis_cache()

        if not cache.is_enabled():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cache is not enabled or unavailable"
            )

        success = cache.clear_all()

        if success:
            logger.warning("Cache cleared via API endpoint")
            return {
                "status": "success",
                "message": "All cache entries cleared",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to clear cache"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.delete("/health/cache/invalidate/{pattern}", tags=["Health", "Cache"])
async def invalidate_cache_pattern(pattern: str):
    """
    Invalidate cache entries matching a pattern.

    Examples:
    - `thermal:rack:*` - Invalidate all thermal analysis cache
    - `thermal:rack:1:*` - Invalidate thermal cache for rack 1
    - `optimization:*` - Invalidate all optimization cache
    - `search:*` - Invalidate all search cache

    Args:
        pattern: Redis key pattern to match
    """
    try:
        cache = get_redis_cache()

        if not cache.is_enabled():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cache is not enabled or unavailable"
            )

        deleted_count = cache.delete_pattern(pattern)

        logger.info(f"Invalidated {deleted_count} cache entries matching pattern: {pattern}")

        return {
            "status": "success",
            "pattern": pattern,
            "deleted_count": deleted_count,
            "message": f"Invalidated {deleted_count} cache entries",
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to invalidate cache pattern {pattern}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invalidate cache: {str(e)}"
        )
