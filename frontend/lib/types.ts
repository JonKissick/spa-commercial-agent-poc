export type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };

export type ProvisionCategory =
  | "pricing"
  | "volume"
  | "take_or_pay"
  | "delivery"
  | "destination_flexibility"
  | "volume_flexibility"
  | "make_up"
  | "price_review"
  | "force_majeure"
  | "termination"
  | "credit"
  | "quality"
  | "tax"
  | "change_in_law"
  | "penalties"
  | "operational_constraints"
  | "assignment_change_of_control"
  | "other";

export type ValuationImpact = "dcf" | "optionality" | "risk_adjustment" | "portfolio" | "none" | "unclear";
export type Confidence = "high" | "medium" | "low";
export type EvidenceStatus =
  | "extracted_from_contract"
  | "inferred_from_contract"
  | "analyst_assumption_required"
  | "market_assumption_required"
  | "portfolio_assumption_required"
  | "insufficient_evidence";
export type RecommendationValue = "proceed" | "proceed_with_conditions" | "renegotiate" | "reject" | "insufficient_evidence";
export type CoverageStatus = "present" | "weak_unclear" | "not_identified";

export interface EvidenceNote {
  status: EvidenceStatus;
  note: string;
  source_excerpt?: string | null;
  [key: string]: unknown;
}

export interface ContractSummary {
  seller?: string | null;
  buyer?: string | null;
  commodity?: string | null;
  contract_term?: string | null;
  governing_law?: string | null;
  summary: string;
  evidence?: EvidenceNote[];
  [key: string]: unknown;
}

export interface ClauseCoverageItem {
  category: ProvisionCategory;
  label: string;
  status: CoverageStatus;
  evidence_summary: string;
  provision_ids: string[];
  warnings: string[];
  [key: string]: unknown;
}

export interface ProvisionRegisterItem {
  id: string;
  category: ProvisionCategory;
  title?: string;
  clause_reference?: string | null;
  extracted_text?: string | null;
  commercial_meaning?: string;
  interpretation?: string;
  valuation_impact: ValuationImpact;
  model_input?: string | null;
  evidence_status: EvidenceStatus;
  confidence: Confidence;
  warnings?: string[];
  analyst_validation_needed?: boolean;
  assumption_required?: string | null;
  [key: string]: unknown;
}

export interface ValuationInputItem {
  name: string;
  value?: unknown;
  source_provision_ids?: string[];
  evidence_status?: EvidenceStatus;
  confidence?: Confidence;
  analyst_assumption_needed?: boolean;
  warnings?: string[];
  [key: string]: unknown;
}

export interface ValuationInputPack {
  missing_analyst_assumptions?: string[];
  missing_market_data?: string[];
  missing_portfolio_data?: string[];
  valuation_warnings?: string[];
  evidence_status?: EvidenceStatus;
  [key: string]: unknown;
}

export interface OptionalityRegisterItem {
  id: string;
  option_name: string;
  option_type?: string;
  source_category?: ProvisionCategory;
  source_provision_ids?: string[];
  source_clause_reference?: string | null;
  extracted_right?: string | null;
  commercial_description: string;
  economic_value_logic?: string;
  suggested_valuation_method?: string;
  required_market_data?: string[];
  required_operational_data?: string[];
  required_portfolio_data?: string[];
  required_analyst_assumptions?: string[];
  key_value_drivers?: string[];
  key_risks_or_constraints?: string[];
  valuation_impact: ValuationImpact;
  evidence_status: EvidenceStatus;
  confidence: Confidence;
  warnings?: string[];
  analyst_validation_needed?: boolean;
  [key: string]: unknown;
}

export interface MarketContextAssessment {
  summary: string;
  required_market_assumptions: string[];
  evidence_status: EvidenceStatus;
  confidence: Confidence;
  [key: string]: unknown;
}

export interface PortfolioFitAssessment {
  summary: string;
  required_portfolio_assumptions: string[];
  evidence_status: EvidenceStatus;
  confidence: Confidence;
  [key: string]: unknown;
}

export interface DealRecommendation {
  recommendation: RecommendationValue;
  memo: string;
  key_conditions: string[];
  key_risks: string[];
  confidence: Confidence;
  evidence_status: EvidenceStatus;
  [key: string]: unknown;
}

export interface DocumentMetadata {
  document_id: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  checksum_sha256: string;
  storage_provider: string;
  created_at: string;
  encryption_status: string;
  retention_policy: string;
  storage_uri?: string | null;
  [key: string]: unknown;
}

export interface RagContextItem {
  chunk_id: string;
  knowledge_id: string;
  title: string;
  knowledge_type: string;
  analysis_section?: string | null;
  text_excerpt: string;
  score: number;
  warnings: string[];
}

export interface RagContextSummary {
  enabled: boolean;
  items_used: RagContextItem[];
  warnings: string[];
  note: string;
  prompt_context?: string;
}

export interface CommercialEvaluationResponse {
  contract_summary: ContractSummary;
  clause_coverage?: ClauseCoverageItem[];
  provision_register: ProvisionRegisterItem[];
  valuation_input_pack: ValuationInputPack;
  optionality_register: OptionalityRegisterItem[];
  market_context_assessment?: MarketContextAssessment;
  portfolio_fit_assessment?: PortfolioFitAssessment;
  deal_recommendation?: DealRecommendation;
  market_context?: MarketContextAssessment;
  portfolio_fit?: PortfolioFitAssessment;
  recommendation?: DealRecommendation;
  limitations?: string[];
  document_metadata?: DocumentMetadata | null;
  rag_context_summary?: RagContextSummary | null;
  [key: string]: unknown;
}

export interface KnowledgeDocumentMetadata {
  knowledge_id: string;
  title: string;
  knowledge_type: string;
  source_filename?: string | null;
  source_document_id?: string | null;
  version?: string | null;
  effective_date?: string | null;
  owner?: string | null;
  confidentiality: string;
  approval_status: string;
  jurisdiction?: string | null;
  commodity?: string | null;
  contract_type?: string | null;
  deal_type?: string | null;
  analysis_section?: string | null;
  quality_label?: string | null;
  tags: string[];
  approved_for_rag: boolean;
  created_at: string;
  warnings: string[];
  [key: string]: unknown;
}

export interface IngestRagTextPayload {
  text: string;
  metadata: Partial<KnowledgeDocumentMetadata> & {
    title: string;
    knowledge_type: string;
  };
  allow_unapproved?: boolean;
}

export interface IngestionResult {
  knowledge_id: string;
  title: string;
  knowledge_type: string;
  chunks_created: number;
  warnings: string[];
}

export interface RetrieveRagPayload {
  query: string;
  filters?: Record<string, string | boolean>;
  top_k?: number;
}

export interface RetrievalResult {
  chunk_id: string;
  knowledge_id: string;
  title: string;
  knowledge_type: string;
  text: string;
  metadata: KnowledgeDocumentMetadata;
  score: number;
  warnings: string[];
}

export interface HealthResponse {
  status: string;
}

export interface SystemStatus {
  status: string;
  llm_provider: string;
  document_store_provider: string;
  rag_provider: string;
  rag_enabled: boolean;
  local_dev_mode: boolean;
  note: string;
}
