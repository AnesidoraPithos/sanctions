"""
API Response Models

Pydantic models for API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class SanctionsHit(BaseModel):
    """Single sanctions hit result"""

    name: str = Field(..., description="Entity name from sanctions list")
    list: str = Field(..., description="Sanctions list source")
    type: Optional[str] = Field(None, description="Entity type")  # Can be None
    address: Optional[str] = Field(None, description="Entity address")  # Can be None
    remark: Optional[str] = Field(None, description="Additional remarks")  # Can be None
    link: Optional[str] = Field(None, description="Source URL")

    # Scoring information
    api_score: Optional[float] = Field(None, description="API relevance score")
    local_score: Optional[float] = Field(None, description="Local fuzzy match score")
    combined_score: float = Field(..., description="Combined match score")
    match_quality: str = Field(..., description="Match quality: EXACT/HIGH/MEDIUM/LOW")

    similarity_breakdown: Optional[Dict[str, float]] = Field(
        None,
        description="Detailed similarity scores (Levenshtein, token_set, etc.)"
    )


class MediaHit(BaseModel):
    """Single media intelligence hit"""

    title: str = Field(..., description="Article title")
    url: str = Field(..., description="Article URL")
    snippet: str = Field(..., description="Article excerpt")
    source: str = Field(..., description="News source")
    date: Optional[str] = Field(None, description="Publication date")
    relevance_score: Optional[float] = Field(None, description="Relevance score")


class Warning(BaseModel):
    """Warning message for API key limitations or errors"""

    source: str = Field(..., description="Source of the warning (opencorporates, sec_edgar, etc.)")
    message: str = Field(..., description="Warning message")
    severity: Literal["info", "warning", "error"] = Field(..., description="Severity level")


class NetworkNode(BaseModel):
    """Node in network graph"""

    id: str = Field(..., description="Node ID")
    label: str = Field(..., description="Node label")
    node_type: str = Field(..., description="Node type: parent|subsidiary|sister|director|shareholder")
    entity_type: str = Field(..., description="Entity type: company|person")


class NetworkEdge(BaseModel):
    """Edge in network graph"""

    id: str = Field(..., description="Edge ID")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    relationship: str = Field(..., description="Relationship type: owns|director_of|shareholder_of|transacted_with")


class NetworkData(BaseModel):
    """Network graph data for visualization"""

    nodes: List[Dict[str, Any]] = Field(..., description="Graph nodes")
    edges: List[Dict[str, Any]] = Field(..., description="Graph edges")
    statistics: Dict[str, Any] = Field(..., description="Graph statistics")


class FinancialIntelligence(BaseModel):
    """Financial intelligence data (directors, shareholders, transactions)"""

    directors: List[Dict[str, Any]] = Field(default_factory=list, description="Directors and officers")
    shareholders: List[Dict[str, Any]] = Field(default_factory=list, description="Major shareholders")
    transactions: List[Dict[str, Any]] = Field(default_factory=list, description="Related party transactions")


class FinancialFlow(BaseModel):
    """A single financial flow between two entities"""

    source: str = Field(..., description="Source entity name")
    target: str = Field(..., description="Target entity name")
    amount: Optional[float] = Field(None, description="Transaction amount")
    currency: Optional[str] = Field(None, description="Currency code (e.g. USD)")
    type: str = Field(..., description="Flow type: contract, grant, loan, procurement, etc.")
    date: Optional[str] = Field(None, description="Transaction date")


class DirectorCompany(BaseModel):
    """A company linked to a director via SEC EDGAR filings."""

    company_name: str
    role: Optional[str] = None
    filing_date: Optional[str] = None
    source_url: Optional[str] = None


class DirectorPivot(BaseModel):
    """Interlocking directorate pivot result."""

    director_name: str
    title: Optional[str] = None
    companies: List[DirectorCompany] = []


class InfrastructureHit(BaseModel):
    """WHOIS-enriched domain intelligence hit."""

    domain: str
    registrant_org: Optional[str] = None
    registrar: Optional[str] = None
    creation_date: Optional[str] = None
    nameservers: List[str] = []
    related_entities: List[str] = []


class BeneficialOwner(BaseModel):
    """Beneficial ownership record from public registries."""

    name: str
    nationality: Optional[str] = None
    ownership_pct: Optional[float] = None
    source: str
    source_url: Optional[str] = None
    verification_date: Optional[str] = None


class AdvancedOsintData(BaseModel):
    """LittleSis + dork query results."""

    littlesis_results: List[Dict[str, Any]] = []
    dork_results: List[Dict[str, Any]] = []


class SearchResponse(BaseModel):
    """Response model for entity search"""

    search_id: str = Field(..., description="Unique search identifier (UUID)")

    status: Literal["completed", "failed", "processing"] = Field(
        ...,
        description="Search status"
    )

    tier: Literal["base", "network", "deep"] = Field(
        ...,
        description="Research tier performed"
    )

    entity_name: str = Field(..., description="Entity name searched")

    risk_level: Literal["SAFE", "LOW", "MID", "HIGH", "VERY_HIGH"] = Field(
        ...,
        description="Calculated risk level"
    )

    risk_explanation: Optional[Dict[str, Any]] = Field(
        None,
        description="Detailed explanation of how risk level was determined",
        json_schema_extra={
            "example": {
                "sanctions_signal": "3 sanctions hit(s) → HIGH",
                "intelligence_signal": "AI assessment: HIGH (78/100)",
                "intelligence_score": 78,
                "intelligence_breakdown": "Criminal investigation (30 pts) | 8 official sources (25 pts) | National security (30 pts)",
                "final_reasoning": "Strong sanctions match (HIGH) | AI assessment confirms high risk"
            }
        }
    )

    sanctions_hits: int = Field(..., description="Number of sanctions matches found")

    media_hits: int = Field(..., description="Number of media intelligence hits")

    intelligence_report: Optional[str] = Field(
        None,
        description="LLM-generated intelligence report"
    )

    timestamp: datetime = Field(..., description="Search timestamp")

    # Optional detailed data (not included in initial response for performance)
    sanctions_data: Optional[List[SanctionsHit]] = Field(
        None,
        description="Detailed sanctions hit data"
    )

    media_data: Optional[List[MediaHit]] = Field(
        None,
        description="Detailed media intelligence data"
    )

    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata (search parameters, timing, etc.)"
    )

    # Network tier fields (Phase 2)
    network_data: Optional[NetworkData] = Field(
        None,
        description="Network graph data (network tier only)"
    )

    financial_intelligence: Optional[FinancialIntelligence] = Field(
        None,
        description="Directors, shareholders, transactions (network tier only)"
    )

    subsidiaries: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="List of discovered subsidiaries (network tier only)"
    )

    warnings: Optional[List[Warning]] = Field(
        None,
        description="Warnings about missing API keys or data source limitations"
    )

    data_sources_used: Optional[List[str]] = Field(
        None,
        description="List of data sources successfully used (sec_edgar, opencorporates, wikipedia, etc.)"
    )

    # Deep tier fields (Phase 3)
    financial_flows: Optional[List[FinancialFlow]] = Field(
        None,
        description="Financial flows between entities (deep tier only)"
    )

    # Phase 4 fields
    director_pivots: Optional[List[DirectorPivot]] = Field(
        None,
        description="Interlocking directorate pivot results (deep tier only)"
    )
    infrastructure: Optional[List[InfrastructureHit]] = Field(
        None,
        description="Digital infrastructure correlation results (deep tier only)"
    )
    beneficial_owners: Optional[List[BeneficialOwner]] = Field(
        None,
        description="Beneficial ownership records (deep tier only)"
    )
    bods_data: Optional[Dict[str, Any]] = Field(
        None,
        description="BODS-structured ownership data (deep tier only)"
    )
    advanced_osint: Optional[AdvancedOsintData] = Field(
        None,
        description="Advanced OSINT reconnaissance data (deep tier only)"
    )
    aleph_hits: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="OCCRP Aleph offshore leak database and PEP hits (deep tier only)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "search_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "tier": "base",
                "entity_name": "Huawei Technologies",
                "risk_level": "HIGH",
                "sanctions_hits": 12,
                "media_hits": 8,
                "intelligence_report": "Intelligence analysis summary...",
                "timestamp": "2026-03-14T10:30:00Z"
            }
        }


class ResultsResponse(BaseModel):
    """Response model for retrieving search results"""

    search_id: str = Field(..., description="Search identifier")
    entity_name: str = Field(..., description="Entity name")
    tier: str = Field(..., description="Research tier")
    risk_level: str = Field(..., description="Risk level")
    risk_explanation: Optional[Dict[str, Any]] = Field(None, description="Risk explanation")
    sanctions_hits: int = Field(..., description="Number of sanctions hits")
    sanctions_data: List[Dict[str, Any]] = Field(..., description="Sanctions data")
    research_data: Dict[str, Any] = Field(..., description="Research/media data")
    intelligence_report: Optional[str] = Field(None, description="Intelligence report")
    timestamp: str = Field(..., description="Search timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")

    # Network tier fields (Phase 2)
    network_data: Optional[Dict[str, Any]] = Field(None, description="Network graph data")
    financial_intelligence: Optional[Dict[str, Any]] = Field(None, description="Financial intelligence")
    subsidiaries: Optional[List[Dict[str, Any]]] = Field(None, description="Subsidiaries list")
    warnings: Optional[List[Dict[str, Any]]] = Field(None, description="Warnings")
    data_sources_used: Optional[List[str]] = Field(None, description="Data sources used")

    # Deep tier fields (Phase 3)
    financial_flows: Optional[List[Dict[str, Any]]] = Field(None, description="Financial flows (deep tier)")

    # Phase 4 fields
    director_pivots: Optional[List[Dict[str, Any]]] = Field(None, description="Director pivot results (deep tier)")
    infrastructure: Optional[List[Dict[str, Any]]] = Field(None, description="Infrastructure correlation (deep tier)")
    beneficial_owners: Optional[List[Dict[str, Any]]] = Field(None, description="Beneficial owners (deep tier)")
    bods_data: Optional[Dict[str, Any]] = Field(None, description="BODS-structured ownership data (deep tier only)")
    advanced_osint: Optional[Dict[str, Any]] = Field(None, description="Advanced OSINT data (deep tier)")
    aleph_hits: Optional[List[Dict[str, Any]]] = Field(None, description="OCCRP Aleph leak/PEP hits (deep tier)")

    # Bookmark fields
    is_saved: bool = Field(False, description="Whether this result has been bookmarked")
    save_label: Optional[str] = Field(None, description="User label for the bookmark")
    save_notes: Optional[str] = Field(None, description="Free-form notes for the bookmark")
    save_tags: Optional[str] = Field(None, description="Comma-separated tags for the bookmark")
    manual_risk: Optional[str] = Field(None, description="Staff-assigned manual risk tier")

    class Config:
        json_schema_extra = {
            "example": {
                "search_id": "550e8400-e29b-41d4-a716-446655440000",
                "entity_name": "Huawei Technologies",
                "tier": "base",
                "risk_level": "HIGH",
                "sanctions_hits": 12,
                "sanctions_data": [],
                "research_data": {},
                "intelligence_report": "Intelligence analysis...",
                "timestamp": "2026-03-14T10:30:00Z",
                "metadata": {}
            }
        }


class HistoryEntry(BaseModel):
    """Search history entry"""

    search_id: str
    entity_name: str
    tier: str
    risk_level: str
    sanctions_hits: int
    timestamp: str
    is_saved: bool = False
    save_label: Optional[str] = None
    saved_at: Optional[str] = None
    save_notes: Optional[str] = None
    save_tags: Optional[str] = None


class SaveResponse(BaseModel):
    """Response for save/unsave operations"""

    saved: bool
    search_id: str
    label: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[str] = None


class HistoryResponse(BaseModel):
    """Response model for search history"""

    entries: List[HistoryEntry] = Field(..., description="Search history entries")
    total: int = Field(..., description="Total number of entries")


class ErrorResponse(BaseModel):
    """Error response model"""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Entity name cannot be empty",
                "details": {"field": "entity_name"}
            }
        }
