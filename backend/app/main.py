"""
HomeRack - Network Rack Optimization System
Main FastAPI application
"""
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import device_specs, devices, racks, connections, health, device_types, brands, models, dcim, auth
from .config import settings
from .middleware.error_handlers import register_exception_handlers
from .middleware.request_id import RequestIDMiddleware

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="Network device rack optimization and cable management system",
    version=settings.VERSION,
    debug=settings.DEBUG
)

# Register exception handlers for consistent error responses
register_exception_handlers(app)

# Add request ID middleware for tracing
app.add_middleware(RequestIDMiddleware)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

# Include API routers

# Authentication (public endpoints)
app.include_router(
    auth.router,
    prefix="/api",
    tags=["Authentication"]
)

# Device management
app.include_router(
    device_specs.router,
    prefix="/api/device-specs",
    tags=["Device Specifications"]
)
app.include_router(
    devices.router,
    prefix="/api/devices",
    tags=["Devices"]
)
app.include_router(
    racks.router,
    prefix="/api/racks",
    tags=["Racks"]
)
app.include_router(
    connections.router,
    prefix="/api/connections",
    tags=["Connections"]
)
app.include_router(
    health.router,
    prefix="/api"
)

# Catalog Management (Phase 1 - New)
app.include_router(
    device_types.router,
    prefix="/api/device-types",
    tags=["Device Types"]
)
app.include_router(
    brands.router,
    prefix="/api/brands",
    tags=["Brands"]
)
app.include_router(
    models.router,
    prefix="/api/models",
    tags=["Models"]
)

# DCIM Integration (Phase 4 - NetBox)
app.include_router(
    dcim.router,
    prefix="/api"
)

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "HomeRack API",
        "version": "1.0.0",
        "description": "Network rack optimization system",
        "authentication": "JWT Bearer Token" if settings.REQUIRE_AUTH else "Optional",
        "endpoints": {
            "docs": "/docs",
            "auth": "/api/auth/login",
            "device_specs": "/api/device-specs",
            "devices": "/api/devices",
            "racks": "/api/racks",
            "optimize": "/api/racks/{id}/optimize",
            "bom": "/api/racks/{id}/bom"
        }
    }

@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Authentication required: {settings.REQUIRE_AUTH}")
    logger.info(f"Circuit breaker enabled: {settings.CIRCUIT_BREAKER_ENABLED}")
    logger.info(f"Rate limiting enabled: {settings.RATE_LIMIT_ENABLED}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info(f"Shutting down {settings.APP_NAME}")


@app.get("/health")
async def health_check():
    """
    Basic health check endpoint (liveness probe).
    Returns 200 if application is running.
    """
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "auth_required": settings.REQUIRE_AUTH
    }
