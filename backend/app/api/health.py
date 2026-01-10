"""
Comprehensive health check endpoints for monitoring and observability.
Provides liveness, readiness, and detailed health checks.
"""
import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..api.dependencies import get_db
from ..config import settings
from ..utils.circuit_breaker import get_all_circuit_breakers_status

logger = logging.getLogger(__name__)
router = APIRouter()


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
    - Circuit breaker states and statistics
    - Configuration status
    - System information

    Returns detailed health metrics for monitoring dashboards.
    """
    checks: Dict[str, Any] = {}
    overall_status = "healthy"

    # Database check with latency measurement
    try:
        import time
        start_time = time.time()
        db.execute(text("SELECT 1"))
        latency_ms = (time.time() - start_time) * 1000

        checks["database"] = {
            "status": "up",
            "latency_ms": round(latency_ms, 2),
            "url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "sqlite",
            "pool_size": settings.DB_POOL_SIZE,
            "message": "Connection successful"
        }
    except Exception as e:
        overall_status = "unhealthy"
        checks["database"] = {
            "status": "down",
            "error": str(e),
            "message": "Connection failed"
        }
        logger.error(f"Database health check failed: {e}")

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
