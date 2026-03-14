/**
 * TypeScript Type Definitions
 *
 * Shared types for API communication and component props.
 */

// Risk levels
export type RiskLevel = "SAFE" | "LOW" | "MID" | "HIGH" | "VERY_HIGH";

// Research tiers
export type ResearchTier = "base" | "network" | "deep";

// Search status
export type SearchStatus = "completed" | "failed" | "processing";

// Match quality
export type MatchQuality = "EXACT" | "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN";

/**
 * API Request Types
 */

export interface SearchRequest {
  entity_name: string;
  country?: string;
  fuzzy_threshold?: number;
  tier: ResearchTier;
}

/**
 * API Response Types
 */

export interface SanctionsHit {
  name: string;
  list: string;
  type: string;
  address: string;
  remark: string;
  link?: string;
  api_score?: number;
  local_score?: number;
  combined_score: number;
  match_quality: MatchQuality;
  similarity_breakdown?: Record<string, number>;
}

export interface MediaHit {
  title: string;
  url: string;
  snippet: string;
  source: string;
  source_type?: string;
  date?: string;
  relevance_score?: number;
  relevance?: string;
}

export interface SearchResponse {
  search_id: string;
  status: SearchStatus;
  tier: ResearchTier;
  entity_name: string;
  risk_level: RiskLevel;
  sanctions_hits: number;
  media_hits: number;
  intelligence_report?: string;
  timestamp: string;
  sanctions_data?: SanctionsHit[];
  media_data?: MediaHit[];
  metadata?: Record<string, unknown>;
}

export interface ResultsResponse {
  search_id: string;
  entity_name: string;
  tier: ResearchTier;
  risk_level: RiskLevel;
  sanctions_hits: number;
  sanctions_data: SanctionsHit[];
  research_data: {
    media_intelligence?: {
      official_sources?: MediaHit[];
      general_media?: MediaHit[];
      total_hits?: number;
    };
    media_data?: MediaHit[];
  };
  intelligence_report?: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface HistoryEntry {
  search_id: string;
  entity_name: string;
  tier: ResearchTier;
  risk_level: RiskLevel;
  sanctions_hits: number;
  timestamp: string;
}

export interface HistoryResponse {
  entries: HistoryEntry[];
  total: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  database_accessible: boolean;
  warnings: string[];
}

/**
 * Component Props Types
 */

export interface SearchFormProps {
  onSearch: (request: SearchRequest) => void;
  isLoading: boolean;
}

export interface RiskBadgeProps {
  level: RiskLevel;
  size?: "sm" | "md" | "lg";
}

export interface TierBadgeProps {
  tier: ResearchTier;
  size?: "sm" | "md";
}
