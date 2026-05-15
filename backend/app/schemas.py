from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


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


class CoverageStatus(StrEnum):
    PRESENT = "present"
    WEAK_UNCLEAR = "weak_unclear"
    NOT_IDENTIFIED = "not_identified"


class EvidenceStatus(StrEnum):
    EXTRACTED_FROM_CONTRACT = "extracted_from_contract"
    INFERRED_FROM_CONTRACT = "inferred_from_contract"
    ANALYST_ASSUMPTION_REQUIRED = "analyst_assumption_required"
    MARKET_ASSUMPTION_REQUIRED = "market_assumption_required"
    PORTFOLIO_ASSUMPTION_REQUIRED = "portfolio_assumption_required"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class OptionType(StrEnum):
    DESTINATION_FLEX = "destination_flex"
    VOLUME_FLEX = "volume_flex"
    TIMING_FLEX = "timing_flex"
    PRICE_REOPENER = "price_reopener"
    MAKE_UP = "make_up"
    CARRY_FORWARD = "carry_forward"
    TAKE_OR_PAY_DOWNSIDE = "take_or_pay_downside"
    TERMINATION = "termination"
    CREDIT_SUPPORT = "credit_support"
    OPERATIONAL_FLEX = "operational_flex"
    OTHER = "other"


class SuggestedValuationMethod(StrEnum):
    SCENARIO_ANALYSIS = "scenario_analysis"
    SPREAD_OPTION = "spread_option"
    SWING_OPTION = "swing_option"
    DEFERRAL_OPTION = "deferral_option"
    MAKE_UP_VALUE = "make_up_value"
    TERMINATION_DOWNSIDE_PROTECTION = "termination_downside_protection"
    CREDIT_RISK_ADJUSTMENT = "credit_risk_adjustment"
    OPERATIONAL_CONSTRAINT_ANALYSIS = "operational_constraint_analysis"
    ANALYST_JUDGEMENT_REQUIRED = "analyst_judgement_required"
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
    category: ProvisionCategory
    title: str
    clause_reference: str | None = None
    extracted_text: str | None = None
    commercial_meaning: str
    valuation_impact: ValuationImpact
    model_input: str | None = None
    evidence_status: EvidenceStatus
    confidence: Confidence
    warnings: list[str] = Field(default_factory=list)
    analyst_validation_needed: bool = True
    # Compatibility fields consumed by the current frontend shell.
    interpretation: str | None = None
    assumption_required: str | None = None

    @model_validator(mode="after")
    def populate_compatibility_fields(self) -> "ProvisionRegisterItem":
        if self.interpretation is None:
            self.interpretation = self.commercial_meaning
        if self.assumption_required is None and self.analyst_validation_needed:
            self.assumption_required = self.model_input
        return self


class ClauseCoverageItem(BaseModel):
    category: ProvisionCategory
    label: str
    status: CoverageStatus
    evidence_summary: str | None = None
    provision_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ValuationInputItem(BaseModel):
    name: str
    value: str | list[str] | dict[str, str] | None = None
    source_provision_ids: list[str] = Field(default_factory=list)
    evidence_status: EvidenceStatus
    confidence: Confidence
    analyst_assumption_needed: bool = False
    warnings: list[str] = Field(default_factory=list)


class ValuationInputPack(BaseModel):
    price_basis: list[ValuationInputItem] = Field(default_factory=list)
    pricing_formula: list[ValuationInputItem] = Field(default_factory=list)
    price_index: list[ValuationInputItem] = Field(default_factory=list)
    price_adjustments: list[ValuationInputItem] = Field(default_factory=list)
    currency: list[ValuationInputItem] = Field(default_factory=list)
    volume_obligation: list[ValuationInputItem] = Field(default_factory=list)
    volume_range: list[ValuationInputItem] = Field(default_factory=list)
    annual_contract_quantity: list[ValuationInputItem] = Field(default_factory=list)
    take_or_pay_obligation: list[ValuationInputItem] = Field(default_factory=list)
    delivery_point: list[ValuationInputItem] = Field(default_factory=list)
    delivery_terms: list[ValuationInputItem] = Field(default_factory=list)
    duration: list[ValuationInputItem] = Field(default_factory=list)
    start_date: list[ValuationInputItem] = Field(default_factory=list)
    end_date: list[ValuationInputItem] = Field(default_factory=list)
    extension_rights: list[ValuationInputItem] = Field(default_factory=list)
    destination_flexibility: list[ValuationInputItem] = Field(default_factory=list)
    volume_flexibility: list[ValuationInputItem] = Field(default_factory=list)
    make_up_rights: list[ValuationInputItem] = Field(default_factory=list)
    carry_forward_rights: list[ValuationInputItem] = Field(default_factory=list)
    price_review_or_reopener: list[ValuationInputItem] = Field(default_factory=list)
    penalties_or_liquidated_damages: list[ValuationInputItem] = Field(default_factory=list)
    credit_support: list[ValuationInputItem] = Field(default_factory=list)
    quality_specifications: list[ValuationInputItem] = Field(default_factory=list)
    tax_or_change_in_law_exposure: list[ValuationInputItem] = Field(default_factory=list)
    operational_constraints: list[ValuationInputItem] = Field(default_factory=list)
    termination_economics: list[ValuationInputItem] = Field(default_factory=list)
    dcf_relevant_inputs: list[ValuationInputItem] = Field(default_factory=list)
    optionality_relevant_inputs: list[ValuationInputItem] = Field(default_factory=list)
    risk_adjustment_inputs: list[ValuationInputItem] = Field(default_factory=list)
    portfolio_relevant_inputs: list[ValuationInputItem] = Field(default_factory=list)
    missing_analyst_assumptions: list[str] = Field(default_factory=list)
    missing_market_data: list[str] = Field(default_factory=list)
    missing_portfolio_data: list[str] = Field(default_factory=list)
    valuation_warnings: list[str] = Field(default_factory=list)
    evidence_status: EvidenceStatus = EvidenceStatus.ANALYST_ASSUMPTION_REQUIRED
    # Compatibility fields consumed by the current frontend shell.
    pricing_inputs: list[str] = Field(default_factory=list)
    volume_inputs: list[str] = Field(default_factory=list)
    timing_inputs: list[str] = Field(default_factory=list)
    risk_inputs: list[str] = Field(default_factory=list)
    required_analyst_assumptions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def populate_compatibility_fields(self) -> "ValuationInputPack":
        if not self.pricing_inputs:
            self.pricing_inputs = _summarize_input_items(self.price_basis + self.pricing_formula + self.price_index)
        if not self.volume_inputs:
            self.volume_inputs = _summarize_input_items(self.volume_obligation + self.volume_range + self.annual_contract_quantity)
        if not self.timing_inputs:
            self.timing_inputs = _summarize_input_items(self.duration + self.start_date + self.end_date + self.extension_rights)
        if not self.risk_inputs:
            self.risk_inputs = _summarize_input_items(
                self.credit_support
                + self.penalties_or_liquidated_damages
                + self.tax_or_change_in_law_exposure
                + self.operational_constraints
                + self.termination_economics
            )
        if not self.required_analyst_assumptions:
            self.required_analyst_assumptions = list(self.missing_analyst_assumptions)
        return self


def _summarize_input_items(items: list[ValuationInputItem]) -> list[str]:
    summaries: list[str] = []
    for item in items:
        value = item.value
        if isinstance(value, list):
            value_text = ", ".join(value)
        elif isinstance(value, dict):
            value_text = ", ".join(f"{key}: {val}" for key, val in value.items())
        elif value is None:
            value_text = "not extracted"
        else:
            value_text = value
        summaries.append(f"{item.name}: {value_text}")
    return summaries


class OptionalityRegisterItem(BaseModel):
    id: str
    option_name: str
    option_type: OptionType = OptionType.OTHER
    source_category: ProvisionCategory | None = None
    source_provision_ids: list[str] = Field(default_factory=list)
    source_clause_reference: str | None = None
    extracted_right: str | None = None
    commercial_description: str
    economic_value_logic: str | None = None
    suggested_valuation_method: SuggestedValuationMethod = SuggestedValuationMethod.ANALYST_JUDGEMENT_REQUIRED
    required_market_data: list[str] = Field(default_factory=list)
    required_operational_data: list[str] = Field(default_factory=list)
    required_portfolio_data: list[str] = Field(default_factory=list)
    required_analyst_assumptions: list[str] = Field(default_factory=list)
    key_value_drivers: list[str] = Field(default_factory=list)
    key_risks_or_constraints: list[str] = Field(default_factory=list)
    valuation_impact: ValuationImpact
    evidence_status: EvidenceStatus
    confidence: Confidence
    warnings: list[str] = Field(default_factory=list)
    analyst_validation_needed: bool = True
    # Compatibility field consumed by the current frontend shell.
    assumption_required: str | None = None

    @model_validator(mode="after")
    def populate_compatibility_fields(self) -> "OptionalityRegisterItem":
        if self.assumption_required is None and self.required_analyst_assumptions:
            self.assumption_required = self.required_analyst_assumptions[0]
        return self


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


class DocumentMetadata(BaseModel):
    document_id: str
    original_filename: str
    content_type: str
    size_bytes: int
    checksum_sha256: str
    storage_provider: str
    created_at: str
    encryption_status: str
    retention_policy: str
    storage_uri: str | None = None


class CommercialEvaluationResponse(BaseModel):
    contract_summary: ContractSummary
    clause_coverage: list[ClauseCoverageItem]
    provision_register: list[ProvisionRegisterItem]
    valuation_input_pack: ValuationInputPack
    optionality_register: list[OptionalityRegisterItem]
    market_context_assessment: MarketContextAssessment
    portfolio_fit_assessment: PortfolioFitAssessment
    deal_recommendation: DealRecommendation
    limitations: list[str] = Field(default_factory=list)
    document_metadata: DocumentMetadata | None = None
    # Compatibility fields consumed by the current frontend shell.
    market_context: MarketContextAssessment | None = None
    portfolio_fit: PortfolioFitAssessment | None = None
    recommendation: DealRecommendation | None = None

    @model_validator(mode="after")
    def populate_compatibility_fields(self) -> "CommercialEvaluationResponse":
        if self.market_context is None:
            self.market_context = self.market_context_assessment
        if self.portfolio_fit is None:
            self.portfolio_fit = self.portfolio_fit_assessment
        if self.recommendation is None:
            self.recommendation = self.deal_recommendation
        return self
