"""
FastAPI Backend for Entity Background Research Agent

This is the main entry point for the REST API backend that replaces the Streamlit frontend.
Provides endpoints for sanctions screening, OSINT research, and intelligence reporting.
"""

import os
import sys

# CRITICAL: Set up Python path BEFORE any other imports
# This ensures all backend modules and parent project modules are accessible
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(backend_dir)

# Add paths for backend modules
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Add paths for existing project modules (agents, core, etc.)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'core'))
sys.path.insert(0, os.path.join(project_root, 'agents'))

# NOW import FastAPI and backend modules
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from routes import search_routes, results_routes, health_routes
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Entity Background Research API",
    description="REST API for sanctions screening, network analysis, and intelligence reporting",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health_routes.router, prefix="/api", tags=["Health"])
app.include_router(search_routes.router, prefix="/api/search", tags=["Search"])
app.include_router(results_routes.router, prefix="/api/results", tags=["Results"])

@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "name": "Entity Background Research API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.get("/favicon.ico")
async def favicon():
    """Favicon endpoint to suppress 404 warnings"""
    return JSONResponse(status_code=204, content=None)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
