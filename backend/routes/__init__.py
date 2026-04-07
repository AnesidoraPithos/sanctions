"""
API Routes Module

Exports route modules for FastAPI.
"""

from . import health_routes
from . import search_routes
from . import results_routes

__all__ = ['health_routes', 'search_routes', 'results_routes']
