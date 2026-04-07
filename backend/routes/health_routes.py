"""
Health Check Routes

Simple endpoints to verify API is operational and check dependencies.
"""

from fastapi import APIRouter
from pydantic import BaseModel
import os
import sys

# Import from backend config (not parent directory)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from config import settings, validate_settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    version: str
    database_accessible: bool
    warnings: list[str]


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint

    Returns:
        Health status with database accessibility and configuration warnings
    """
    # Check database accessibility
    db_accessible = os.path.exists(settings.DATABASE_PATH)

    # Get configuration warnings
    warnings = validate_settings()

    return HealthResponse(
        status="healthy" if db_accessible else "degraded",
        version="1.0.0",
        database_accessible=db_accessible,
        warnings=warnings
    )


@router.get("/ping")
async def ping():
    """Simple ping endpoint for basic connectivity check"""
    return {"status": "pong"}
