from fastapi import APIRouter
from app.config import get_settings

router = APIRouter()
settings = get_settings()

@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "online",
        "app": settings.app_name,
        "version": settings.version,
        "docs": "/docs"
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.environment
    }
