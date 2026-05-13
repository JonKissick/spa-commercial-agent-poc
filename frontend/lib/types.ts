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

export type ValuationImpact =
  | "dcf"
  | "optionality"
  | "risk_adjustment"
  | "portfolio"
  | "none"
  | "unclear";

export type Confidence = "high" | "medium" | "low";

export type EvidenceStatus =
  | "extracted_from_contract"
  | "inferred_from_contract"
  | "analyst_assumption_required"
  | "market_assumption_required"
  | "portfolio_assumption_required"
  | "insufficient_evidence";

export type RecommendationValue =
  | "proceed"
  | "proceed_with_conditions"
  | "renegotiate"
  | "reject"
  | "insufficient_evidence";

export interface EvidenceNote {
  status: EvidenceStatus;
  note: string;
  source_excerpt?: string | null;
}

export interface ContractSummary {
  seller?: string | null;
  buyer?: string | null;
  commodity?: string | null;
  contract_term?: string | null;
  governing_law?: string | null;
  summary: string;
  evidence: EvidenceNote[];
}

export interface ProvisionRegisterItem {
  id: string;
  category: ProvisionCategory;
  clause_reference?: string | null;
  extracted_text?: string | null;
  interpretation: string;
  valuation_impact: ValuationImpact;
  evidence_status: EvidenceStatus;
  confidence: Confidence;
  assumption_required?: string | null;
}

export interface ValuationInputPack {
  pricing_inputs: string[];
  volume_inputs: string[];
  timing_inputs: string[];
  risk_inputs: string[];
  required_analyst_assumptions: string[];
  evidence_status: EvidenceStatus;
}

export interface OptionalityRegisterItem {
  id: string;
  option_name: string;
  commercial_description: string;
  valuation_impact: ValuationImpact;
  evidence_status: EvidenceStatus;
  confidence: Confidence;
  assumption_required?: string | null;
}

export interface MarketContextAssessment {
  summary: string;
  required_market_assumptions: string[];
  evidence_status: EvidenceStatus;
  confidence: Confidence;
}

export interface PortfolioFitAssessment {
  summary: string;
  required_portfolio_assumptions: string[];
  evidence_status: EvidenceStatus;
  confidence: Confidence;
}

export interface DealRecommendation {
  recommendation: RecommendationValue;
  memo: string;
  key_conditions: string[];
  key_risks: string[];
  confidence: Confidence;
  evidence_status: EvidenceStatus;
}

export interface CommercialEvaluationResponse {
  contract_summary: ContractSummary;
  provision_register: ProvisionRegisterItem[];
  valuation_input_pack: ValuationInputPack;
  optionality_register: OptionalityRegisterItem[];
  market_context: MarketContextAssessment;
  portfolio_fit: PortfolioFitAssessment;
  recommendation: DealRecommendation;
}
