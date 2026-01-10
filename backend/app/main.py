"""
HomeRack - Network Rack Optimization System
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import device_specs, devices, racks, connections

app = FastAPI(
    title="HomeRack API",
    description="Network device rack optimization and cable management system",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
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

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "HomeRack API",
        "version": "1.0.0",
        "description": "Network rack optimization system",
        "endpoints": {
            "docs": "/docs",
            "device_specs": "/api/device-specs",
            "devices": "/api/devices",
            "racks": "/api/racks",
            "optimize": "/api/racks/{id}/optimize",
            "bom": "/api/racks/{id}/bom"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
