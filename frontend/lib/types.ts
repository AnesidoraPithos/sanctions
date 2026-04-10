/**
 * TypeScript Type Definitions
 *
 * Shared types for API communication and component props.
 */

// Risk levels (system-computed)
export type RiskLevel = "SAFE" | "LOW" | "MID" | "HIGH" | "VERY_HIGH";

// Staff-assigned manual risk tiers
export type ManualRiskLevel = "LOW" | "MODERATE" | "HIGH" | "CRITICAL";

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
  // Network tier parameters (Phase 2)
  network_depth?: number; // 1-3 levels
  ownership_threshold?: number; // 0-100%
  include_sisters?: boolean;
  // Network tier: Configurable search limits (Phase 2 enhancement)
  max_level_2_searches?: number; // 5-50, default: 20
  max_level_3_searches?: number; // 5-30, default: 10
  // Deep tier: pre-generated UUID for WebSocket progress tracking (Phase 3)
  client_search_id?: string;
  // Phase 4 toggles (deep tier only)
  include_director_pivot?: boolean;
  include_infrastructure?: boolean;
  include_beneficial_ownership?: boolean;
}

/**
 * API Response Types
 */

export interface RiskExplanation {
  sanctions_signal: string;
  intelligence_signal: string;
  intelligence_score: number | null;       // deprecated, always null for new records
  intelligence_breakdown: string | null;   // deprecated, always null for new records
  final_reasoning: string;
  yes_count: number | null;
  total_count: number | null;
  indicator_results: Array<{ indicator: string; flagged: boolean }> | null;
}

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

/**
 * Network Tier Types (Phase 2)
 */

export interface Warning {
  source: string;
  message: string;
  severity: "info" | "warning" | "error";
}

export interface NetworkNode {
  data: {
    id: string;
    label: string;
    node_type: "parent" | "subsidiary" | "sister" | "director" | "shareholder";
    entity_type: "company" | "person";
    size?: number;
    color?: string;
    jurisdiction?: string;
    status?: string;
    ownership_pct?: number;
    title?: string;
    nationality?: string;
    sanctions_hit?: number;
    [key: string]: unknown;
  };
}

export interface NetworkEdge {
  data: {
    id: string;
    source: string;
    target: string;
    relationship: "owns" | "director_of" | "shareholder_of" | "transacted_with" | "sibling_of";
    ownership_pct?: number;
    edge_color?: string;
    edge_width?: number;
    [key: string]: unknown;
  };
}

export interface NetworkData {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  statistics: {
    total_nodes: number;
    total_edges: number;
    companies: number;
    people: number;
    num_countries?: number;
    countries?: string[];
    most_connected?: string;
    most_connected_degree?: number;
    // Level breakdown for subsidiaries
    level_1_count?: number;
    level_2_count?: number;
    level_3_count?: number;
  };
  parent_info?: ParentInfo;
  subsidiaries?: Subsidiary[];
  sisters?: Subsidiary[];
}

export interface Subsidiary {
  name: string;
  jurisdiction?: string;
  status?: string;
  ownership_percentage?: number;
  level?: number;
  relationship?: string;
  sanctions_hits?: number;
  sanctions_data?: SanctionsHit[];
  source?: string;              // Data source: 'sec_edgar', 'opencorporates_api', 'wikipedia', 'duckduckgo'
  reference_url?: string;       // URL to source document
}

export interface ParentInfo {
  name: string;
  jurisdiction?: string;
  relationship: 'parent';
  confidence?: 'high' | 'medium' | 'low';
  source?: string;
  reference_url?: string;
}

export interface Director {
  id: number;
  company_name: string;
  cik?: string;
  name: string;
  title?: string;
  nationality?: string;
  biography?: string;
  other_positions?: string;
  filing_type?: string;
  filing_date?: string;
  source_url?: string;
  sanctions_hit?: number;
  sanctions_hits?: number;
  sanctions_data?: SanctionsHit[];
  date_added?: string;
  last_updated?: string;
}

export interface Shareholder {
  id: number;
  company_name: string;
  cik?: string;
  name: string;
  type?: string;
  ownership_percentage?: number;
  voting_rights?: number;
  jurisdiction?: string;
  filing_type?: string;
  filing_date?: string;
  source_url?: string;
  sanctions_hit?: number;
  sanctions_hits?: number;
  sanctions_data?: SanctionsHit[];
  date_added?: string;
  last_updated?: string;
}

export interface Transaction {
  id: number;
  company_name: string;
  cik?: string;
  transaction_type?: string;
  counterparty?: string;
  relationship?: string;
  amount?: number;
  currency?: string;
  transaction_date?: string;
  purpose?: string;
  terms?: string;
  filing_type?: string;
  filing_date?: string;
  source_url?: string;
  date_added?: string;
  last_updated?: string;
}

export interface FinancialIntelligence {
  directors: Director[];
  shareholders: Shareholder[];
  transactions: Transaction[];
}

/**
 * Phase 4 Types — Advanced Corporate Intelligence
 */

export interface DirectorCompany {
  company_name: string;
  role?: string;
  filing_date?: string;
  source_url?: string;
}

export interface DirectorPivot {
  director_name: string;
  title?: string;
  companies: DirectorCompany[];
}

export interface InfrastructureHit {
  domain: string;
  registrant_org?: string;
  registrar?: string;
  creation_date?: string;
  nameservers?: string[];
  related_entities: string[];
}

export interface BeneficialOwner {
  name: string;
  nationality?: string;
  ownership_pct?: number;
  source: string;
  source_url?: string;
  verification_date?: string;
}

export interface AdvancedOsintData {
  littlesis_results: Record<string, unknown>[];
  dork_results: Record<string, unknown>[];
}

/**
 * Deep Tier Types (Phase 3)
 */

export interface FinancialFlow {
  source: string;
  target: string;
  amount?: number;
  currency?: string;
  type: string;
  date?: string;
}

export interface SearchResponse {
  search_id: string;
  status: SearchStatus;
  tier: ResearchTier;
  entity_name: string;
  risk_level: RiskLevel;
  risk_explanation?: RiskExplanation;
  sanctions_hits: number;
  media_hits: number;
  intelligence_report?: string;
  timestamp: string;
  sanctions_data?: SanctionsHit[];
  media_data?: MediaHit[];
  metadata?: Record<string, unknown>;
  // Network tier fields (Phase 2)
  network_data?: NetworkData;
  financial_intelligence?: FinancialIntelligence;
  subsidiaries?: Subsidiary[];
  warnings?: Warning[];
  data_sources_used?: string[];
  // Deep tier fields (Phase 3)
  financial_flows?: FinancialFlow[];
  // Phase 4 fields
  director_pivots?: DirectorPivot[];
  infrastructure?: InfrastructureHit[];
  beneficial_owners?: BeneficialOwner[];
  advanced_osint?: AdvancedOsintData;
}

export interface ResultsResponse {
  search_id: string;
  entity_name: string;
  tier: ResearchTier;
  risk_level: RiskLevel;
  risk_explanation?: RiskExplanation;
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
  // Network tier fields (Phase 2)
  network_data?: NetworkData | Record<string, unknown>;
  financial_intelligence?: FinancialIntelligence | Record<string, unknown>;
  subsidiaries?: Subsidiary[];
  warnings?: Warning[];
  data_sources_used?: string[];
  // Deep tier fields (Phase 3)
  financial_flows?: FinancialFlow[];
  // Phase 4 fields
  director_pivots?: DirectorPivot[];
  infrastructure?: InfrastructureHit[];
  beneficial_owners?: BeneficialOwner[];
  advanced_osint?: AdvancedOsintData;
  // Bookmark fields
  is_saved?: boolean;
  save_label?: string;
  manual_risk?: ManualRiskLevel | null;
}

export interface HistoryEntry {
  search_id: string;
  entity_name: string;
  tier: ResearchTier;
  risk_level: RiskLevel;
  sanctions_hits: number;
  timestamp: string;
  is_saved?: boolean;
  save_label?: string;
  saved_at?: string;
}

export interface SaveRequest {
  label?: string;
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
  explanation?: RiskExplanation;
}

export interface TierBadgeProps {
  tier: ResearchTier;
  size?: "sm" | "md";
}

/**
 * Network Tier Component Props (Phase 2)
 */

export interface TierSelectorProps {
  selectedTier: ResearchTier;
  onTierChange: (tier: ResearchTier) => void;
  networkDepth?: number;
  onNetworkDepthChange?: (depth: number) => void;
  ownershipThreshold?: number;
  onOwnershipThresholdChange?: (threshold: number) => void;
  includeSisters?: boolean;
  onIncludeSistersChange?: (include: boolean) => void;
  // Search limit controls (Phase 2 enhancement)
  maxLevel2Searches?: number;
  onMaxLevel2SearchesChange?: (max: number) => void;
  maxLevel3Searches?: number;
  onMaxLevel3SearchesChange?: (max: number) => void;
  // Deep tier controls (Phase 3)
  includeFinancialFlows?: boolean;
  onIncludeFinancialFlowsChange?: (include: boolean) => void;
  // Phase 4 toggles
  includeDirectorPivot?: boolean;
  onIncludeDirectorPivotChange?: (include: boolean) => void;
  includeInfrastructure?: boolean;
  onIncludeInfrastructureChange?: (include: boolean) => void;
  includeBeneficialOwnership?: boolean;
  onIncludeBeneficialOwnershipChange?: (include: boolean) => void;
}

export interface NetworkGraphProps {
  networkData: NetworkData;
  height?: number;
  onNodeClick?: (nodeId: string) => void;
}

export interface FinancialIntelligenceProps {
  financial_intelligence: FinancialIntelligence;
}

export interface SubsidiariesListProps {
  subsidiaries: Subsidiary[];
  onSubsidiaryClick?: (subsidiary: Subsidiary) => void;
}
