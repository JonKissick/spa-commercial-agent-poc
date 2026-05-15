from enum import StrEnum

from pydantic import BaseModel, Field


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


class ContractRole(StrEnum):
    BUYER = "buyer"
    SELLER = "seller"
    SWAP = "swap"
    TOLLING = "tolling"
    PORTFOLIO_TRADE = "portfolio_trade"
    UNCLEAR = "unclear"


class DeliveryBasis(StrEnum):
    DES = "des"
    FOB = "fob"
    EX_SHIP = "ex_ship"
    DELIVERED = "delivered"
    FREE_ON_BOARD = "free_on_board"
    UNCLEAR = "unclear"


class Responsibility(StrEnum):
    BUYER = "buyer"
    SELLER = "seller"
    SHARED = "shared"
    UNCLEAR = "unclear"


class NpvReadiness(StrEnum):
    READY = "ready"
    PARTIAL = "partial"
    NOT_READY = "not_ready"


class ApplicableModel(StrEnum):
    DES_PURCHASE = "des_purchase"
    FOB_PURCHASE = "fob_purchase"
    DES_SALE = "des_sale"
    FOB_SALE = "fob_sale"
    NETBACK = "netback"
    LANDED_COST = "landed_cost"
    UNCLEAR = "unclear"


class PortfolioRelevance(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCLEAR = "unclear"


class RoutedOption(BaseModel):
    option_type: str
    source_optionality_ids: list[str] = Field(default_factory=list)
    suggested_model: str
    readiness: NpvReadiness = NpvReadiness.NOT_READY
    missing_inputs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DealStructureAssessment(BaseModel):
    contract_role: ContractRole = ContractRole.UNCLEAR
    delivery_basis: DeliveryBasis = DeliveryBasis.UNCLEAR
    commodity: str | None = None
    origin: str | None = None
    destination: str | None = None
    loading_port: str | None = None
    discharge_port: str | None = None
    title_transfer_point: str | None = None
    risk_transfer_point: str | None = None
    shipping_responsibility: Responsibility = Responsibility.UNCLEAR
    logistics_cost_responsibility: Responsibility = Responsibility.UNCLEAR
    source_provision_ids: list[str] = Field(default_factory=list)
    evidence_status: EvidenceStatus = EvidenceStatus.INSUFFICIENT_EVIDENCE
    confidence: Confidence = Confidence.LOW
    warnings: list[str] = Field(default_factory=list)


class NpvReadinessAssessment(BaseModel):
    readiness: NpvReadiness = NpvReadiness.NOT_READY
    required_contract_inputs: list[str] = Field(default_factory=list)
    available_contract_inputs: list[str] = Field(default_factory=list)
    missing_contract_inputs: list[str] = Field(default_factory=list)
    required_manual_assumptions: list[str] = Field(default_factory=list)
    required_market_data: list[str] = Field(default_factory=list)
    required_logistics_data: list[str] = Field(default_factory=list)
    required_portfolio_data: list[str] = Field(default_factory=list)
    can_calculate_npv_now: bool = False
    reason_not_ready: str
    source_sections: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class LandedValueOrNetbackAssessment(BaseModel):
    applicable_model: ApplicableModel = ApplicableModel.UNCLEAR
    economic_logic: str
    value_formula_description: str
    required_price_inputs: list[str] = Field(default_factory=list)
    required_volume_inputs: list[str] = Field(default_factory=list)
    required_logistics_inputs: list[str] = Field(default_factory=list)
    required_cost_inputs: list[str] = Field(default_factory=list)
    required_tax_or_fee_inputs: list[str] = Field(default_factory=list)
    origin_destination_relevance: str
    des_fob_notes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ScenarioModelRequirements(BaseModel):
    base_case_inputs_required: list[str] = Field(default_factory=list)
    upside_case_inputs_required: list[str] = Field(default_factory=list)
    downside_case_inputs_required: list[str] = Field(default_factory=list)
    stress_case_inputs_required: list[str] = Field(default_factory=list)
    key_sensitivities: list[str] = Field(default_factory=list)
    break_even_candidates: list[str] = Field(default_factory=list)
    manual_inputs_required_before_calculation: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class OptionalityModelRoutingAssessment(BaseModel):
    routed_options: list[RoutedOption] = Field(default_factory=list)
    recommended_future_models: list[str] = Field(default_factory=list)
    required_market_data: list[str] = Field(default_factory=list)
    required_operational_data: list[str] = Field(default_factory=list)
    required_portfolio_data: list[str] = Field(default_factory=list)
    not_ready_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PortfolioImpactRequirements(BaseModel):
    portfolio_relevance: PortfolioRelevance = PortfolioRelevance.UNCLEAR
    required_portfolio_inputs: list[str] = Field(default_factory=list)
    potential_diversification_effects: list[str] = Field(default_factory=list)
    potential_concentration_risks: list[str] = Field(default_factory=list)
    potential_hedge_value: list[str] = Field(default_factory=list)
    liquidity_or_operational_constraints: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AnalysisModelOutputs(BaseModel):
    deal_structure: DealStructureAssessment
    npv_readiness: NpvReadinessAssessment
    landed_value_or_netback: LandedValueOrNetbackAssessment
    scenario_model_requirements: ScenarioModelRequirements
    optionality_model_routing: OptionalityModelRoutingAssessment
    portfolio_impact_requirements: PortfolioImpactRequirements
    commercial_model_warnings: list[str] = Field(default_factory=list)
