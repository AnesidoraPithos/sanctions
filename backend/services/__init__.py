"""
Services Module

Business logic layer for sanctions screening and research.
"""

# CRITICAL: Set up paths BEFORE importing any service modules
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(backend_dir)

# Add project root to path so we can import core, agents, visualizations as packages
sys.path.insert(0, os.path.abspath(project_root))
# Also add core directory so existing code can import matching_utils directly
sys.path.insert(0, os.path.abspath(os.path.join(project_root, 'core')))

# NOW import service modules (after paths are set up)
from .sanctions_service import SanctionsService, get_sanctions_service
from .research_service import ResearchService, get_research_service
from .conglomerate_service import ConglomerateService, get_conglomerate_service
from .network_service import NetworkService, get_network_service
from .risk_assessment_service import RiskAssessmentService, get_risk_assessment_service

__all__ = [
    'SanctionsService',
    'get_sanctions_service',
    'ResearchService',
    'get_research_service',
    'ConglomerateService',
    'get_conglomerate_service',
    'NetworkService',
    'get_network_service',
    'RiskAssessmentService',
    'get_risk_assessment_service'
]
