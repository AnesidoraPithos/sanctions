"""
API Request Models

Pydantic models for validating incoming API requests.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal


class SearchRequest(BaseModel):
    """Request model for entity search"""

    entity_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Name of entity to search",
        examples=["Huawei Technologies", "Kaspersky Lab"]
    )

    country: Optional[str] = Field(
        None,
        max_length=100,
        description="Country filter for sanctions search",
        examples=["China", "Russia", "Iran"]
    )

    fuzzy_threshold: int = Field(
        default=80,
        ge=0,
        le=100,
        description="Fuzzy matching threshold (0-100, higher = stricter)",
        examples=[80, 90, 70]
    )

    tier: Literal["base", "network", "deep"] = Field(
        default="base",
        description="Research tier: base (30-60s), network (2-10min), deep (5-15min)"
    )

    # Network tier parameters (Phase 2)
    network_depth: int = Field(
        default=1,
        ge=1,
        le=3,
        description="Network tier: Search depth for subsidiaries (1-3 levels)"
    )

    ownership_threshold: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Network tier: Minimum ownership percentage to include (0-100)"
    )

    include_sisters: bool = Field(
        default=True,
        description="Network tier: Whether to include sister companies"
    )

    # Network tier: Search limits (Phase 2 enhancement)
    max_level_2_searches: int = Field(
        default=20,
        ge=5,
        le=50,
        description="Network tier: Max subsidiaries to search for level 2 (prevents timeout)"
    )

    max_level_3_searches: int = Field(
        default=10,
        ge=5,
        le=30,
        description="Network tier: Max subsidiaries to search for level 3 (prevents timeout)"
    )

    @field_validator('entity_name')
    @classmethod
    def validate_entity_name(cls, v: str) -> str:
        """Validate and clean entity name"""
        # Strip whitespace
        v = v.strip()

        if not v:
            raise ValueError("Entity name cannot be empty")

        # Prevent injection attempts
        dangerous_chars = ['<', '>', ';', '`', '|', '&']
        if any(char in v for char in dangerous_chars):
            raise ValueError("Entity name contains invalid characters")

        return v

    @field_validator('country')
    @classmethod
    def validate_country(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean country name"""
        if v:
            v = v.strip()
            return v if v else None
        return None

    @field_validator('tier')
    @classmethod
    def validate_tier(cls, v: str) -> str:
        """Validate tier is supported"""
        # Phase 1: base tier
        # Phase 2: network tier
        # Phase 3: deep tier (not yet implemented)
        if v == "deep":
            raise ValueError("Deep tier is not yet implemented (Phase 3 feature)")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "entity_name": "Huawei Technologies",
                    "country": "China",
                    "fuzzy_threshold": 80,
                    "tier": "base"
                },
                {
                    "entity_name": "Apple Inc.",
                    "country": "USA",
                    "fuzzy_threshold": 80,
                    "tier": "network",
                    "network_depth": 2,
                    "ownership_threshold": 50,
                    "include_sisters": True
                }
            ]
        }


class ExportRequest(BaseModel):
    """Request model for exporting search results"""

    search_id: str = Field(
        ...,
        description="Search ID to export",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )

    format: Literal["pdf", "excel", "json"] = Field(
        default="pdf",
        description="Export format"
    )

    include_intelligence_report: bool = Field(
        default=True,
        description="Include LLM intelligence report in export"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "search_id": "550e8400-e29b-41d4-a716-446655440000",
                "format": "pdf",
                "include_intelligence_report": True
            }
        }
