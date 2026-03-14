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
    sanctions_hits: int = Field(..., description="Number of sanctions hits")
    sanctions_data: List[Dict[str, Any]] = Field(..., description="Sanctions data")
    research_data: Dict[str, Any] = Field(..., description="Research/media data")
    intelligence_report: Optional[str] = Field(None, description="Intelligence report")
    timestamp: str = Field(..., description="Search timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")

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
