"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from backend.app.core.config import settings
from backend.app.models.schemas import HealthResponse
from backend.app.api.v1 import router as v1_router

# Create FastAPI app
app = FastAPI(
    title="AI Scheduling System",
    description="AI-powered intelligent scheduling assistant",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    Returns the service status and basic information.
    """
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(),
        version="0.1.0"
    )


# Include v1 API routes
app.include_router(v1_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI Scheduling System API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )

