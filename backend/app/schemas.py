from enum import StrEnum

from pydantic import BaseModel, Field


class ProvisionCategory(StrEnum):
    PRICING = "pricing"
    VOLUME = "volume"
    TAKE_OR_PAY = "take_or_pay"
    DELIVERY = "delivery"
    DESTINATION_FLEXIBILITY = "destination_flexibility"
    VOLUME_FLEXIBILITY = "volume_flexibility"
    MAKE_UP = "make_up"
    PRICE_REVIEW = "price_review"
    FORCE_MAJEURE = "force_majeure"
    TERMINATION = "termination"
    CREDIT = "credit"
    QUALITY = "quality"
    TAX = "tax"
    CHANGE_IN_LAW = "change_in_law"
    PENALTIES = "penalties"
    OPERATIONAL_CONSTRAINTS = "operational_constraints"
    ASSIGNMENT_CHANGE_OF_CONTROL = "assignment_change_of_control"
    OTHER = "other"


class ValuationImpact(StrEnum):
    DCF = "dcf"
    OPTIONALITY = "optionality"
    RISK_ADJUSTMENT = "risk_adjustment"
    PORTFOLIO = "portfolio"
    NONE = "none"
    UNCLEAR = "unclear"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EvidenceStatus(StrEnum):
    EXTRACTED_FROM_CONTRACT = "extracted_from_contract"
    INFERRED_FROM_CONTRACT = "inferred_from_contract"
    ANALYST_ASSUMPTION_REQUIRED = "analyst_assumption_required"
    MARKET_ASSUMPTION_REQUIRED = "market_assumption_required"
    PORTFOLIO_ASSUMPTION_REQUIRED = "portfolio_assumption_required"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class RecommendationValue(StrEnum):
    PROCEED = "proceed"
    PROCEED_WITH_CONDITIONS = "proceed_with_conditions"
    RENEGOTIATE = "renegotiate"
    REJECT = "reject"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class EvidenceNote(BaseModel):
    status: EvidenceStatus
    note: str
    source_excerpt: str | None = None


class ContractSummary(BaseModel):
    seller: str | None = None
    buyer: str | None = None
    commodity: str | None = None
    contract_term: str | None = None
    governing_law: str | None = None
    summary: str
    evidence: list[EvidenceNote]


class ProvisionRegisterItem(BaseModel):
    id: str
    title: str = "Untitled provision"
    category: ProvisionCategory
    clause_reference: str | None = None
    extracted_text: str | None = None
    interpretation: str
    valuation_impact: ValuationImpact
    evidence_status: EvidenceStatus
    confidence: Confidence
    assumption_required: str | None = None
    warnings: list[str] = Field(default_factory=list)


class ValuationInputPack(BaseModel):
    pricing_inputs: list[str] = Field(default_factory=list)
    volume_inputs: list[str] = Field(default_factory=list)
    timing_inputs: list[str] = Field(default_factory=list)
    risk_inputs: list[str] = Field(default_factory=list)
    required_analyst_assumptions: list[str] = Field(default_factory=list)
    evidence_status: EvidenceStatus


class OptionalityRegisterItem(BaseModel):
    id: str
    option_name: str
    commercial_description: str
    valuation_impact: ValuationImpact
    evidence_status: EvidenceStatus
    confidence: Confidence
    assumption_required: str | None = None


class MarketContextAssessment(BaseModel):
    summary: str
    required_market_assumptions: list[str] = Field(default_factory=list)
    evidence_status: EvidenceStatus
    confidence: Confidence


class PortfolioFitAssessment(BaseModel):
    summary: str
    required_portfolio_assumptions: list[str] = Field(default_factory=list)
    evidence_status: EvidenceStatus
    confidence: Confidence


class DealRecommendation(BaseModel):
    recommendation: RecommendationValue
    memo: str
    key_conditions: list[str] = Field(default_factory=list)
    key_risks: list[str] = Field(default_factory=list)
    confidence: Confidence
    evidence_status: EvidenceStatus


class CommercialEvaluationResponse(BaseModel):
    contract_summary: ContractSummary
    provision_register: list[ProvisionRegisterItem]
    valuation_input_pack: ValuationInputPack
    optionality_register: list[OptionalityRegisterItem]
    market_context: MarketContextAssessment
    portfolio_fit: PortfolioFitAssessment
    recommendation: DealRecommendation
    limitations: list[str] = Field(default_factory=list)
