from app.schemas import (
    CommercialEvaluationResponse,
    Confidence,
    EvidenceStatus,
    OptionalityRegisterItem,
    OptionType,
    ProvisionCategory,
    SuggestedValuationMethod,
    ValuationImpact,
)
from app.valuation_inputs import PROHIBITED_VALUATION_PHRASES

OPTION_TYPE_DEFINITIONS: dict[OptionType, str] = {
    OptionType.DESTINATION_FLEX: "Right or practical ability to redirect, divert, or choose destination.",
    OptionType.VOLUME_FLEX: "Right or practical ability to vary quantities, nominations, or cargo count.",
    OptionType.TIMING_FLEX: "Right or practical ability to shift delivery timing or scheduling.",
    OptionType.PRICE_REOPENER: "Right to reopen, review, renegotiate, or reset pricing.",
    OptionType.MAKE_UP: "Right to recover paid-for but untaken quantities later.",
    OptionType.CARRY_FORWARD: "Right to carry surplus or shortfall quantities forward.",
    OptionType.TAKE_OR_PAY_DOWNSIDE: "Downside protection or exposure created by take-or-pay mechanics.",
    OptionType.TERMINATION: "Right to exit, terminate, or protect downside under defined conditions.",
    OptionType.CREDIT_SUPPORT: "Credit support mechanics that alter counterparty exposure or downside risk.",
    OptionType.OPERATIONAL_FLEX: "Operational rights or constraints affecting practical flexibility.",
    OptionType.OTHER: "Other commercially relevant optionality or flexibility.",
}

CATEGORY_TO_OPTION_TYPE: dict[ProvisionCategory, OptionType] = {
    ProvisionCategory.DESTINATION_FLEXIBILITY: OptionType.DESTINATION_FLEX,
    ProvisionCategory.VOLUME_FLEXIBILITY: OptionType.VOLUME_FLEX,
    ProvisionCategory.MAKE_UP: OptionType.MAKE_UP,
    ProvisionCategory.PRICE_REVIEW: OptionType.PRICE_REOPENER,
    ProvisionCategory.TERMINATION: OptionType.TERMINATION,
    ProvisionCategory.DELIVERY: OptionType.TIMING_FLEX,
    ProvisionCategory.TAKE_OR_PAY: OptionType.TAKE_OR_PAY_DOWNSIDE,
    ProvisionCategory.CREDIT: OptionType.CREDIT_SUPPORT,
    ProvisionCategory.OPERATIONAL_CONSTRAINTS: OptionType.OPERATIONAL_FLEX,
}

OPTION_TYPE_TO_METHOD: dict[OptionType, SuggestedValuationMethod] = {
    OptionType.DESTINATION_FLEX: SuggestedValuationMethod.SPREAD_OPTION,
    OptionType.VOLUME_FLEX: SuggestedValuationMethod.SWING_OPTION,
    OptionType.TIMING_FLEX: SuggestedValuationMethod.DEFERRAL_OPTION,
    OptionType.PRICE_REOPENER: SuggestedValuationMethod.SCENARIO_ANALYSIS,
    OptionType.MAKE_UP: SuggestedValuationMethod.MAKE_UP_VALUE,
    OptionType.CARRY_FORWARD: SuggestedValuationMethod.SCENARIO_ANALYSIS,
    OptionType.TAKE_OR_PAY_DOWNSIDE: SuggestedValuationMethod.SCENARIO_ANALYSIS,
    OptionType.TERMINATION: SuggestedValuationMethod.TERMINATION_DOWNSIDE_PROTECTION,
    OptionType.CREDIT_SUPPORT: SuggestedValuationMethod.CREDIT_RISK_ADJUSTMENT,
    OptionType.OPERATIONAL_FLEX: SuggestedValuationMethod.OPERATIONAL_CONSTRAINT_ANALYSIS,
    OptionType.OTHER: SuggestedValuationMethod.ANALYST_JUDGEMENT_REQUIRED,
}

OPTIONALITY_RELEVANT_CATEGORIES = set(CATEGORY_TO_OPTION_TYPE)


def normalize_optionality_register(response: CommercialEvaluationResponse) -> CommercialEvaluationResponse:
    if response.optionality_register is None:
        response.optionality_register = []

    provision_ids = {provision.id for provision in response.provision_register}
    provision_by_id = {provision.id: provision for provision in response.provision_register}

    normalized: list[OptionalityRegisterItem] = []
    for index, item in enumerate(response.optionality_register, start=1):
        if not item.id.strip():
            item.id = f"OP-{index:03d}"
        _normalize_item(item, provision_ids, provision_by_id)
        normalized.append(item)

    response.optionality_register = normalized
    _ensure_optionality_impact_provisions_represented(response)
    return response


def _normalize_item(
    item: OptionalityRegisterItem,
    provision_ids: set[str],
    provision_by_id: dict[str, object],
) -> None:
    if item.source_category and item.option_type == OptionType.OTHER:
        item.option_type = CATEGORY_TO_OPTION_TYPE.get(item.source_category, OptionType.OTHER)
    if item.suggested_valuation_method == SuggestedValuationMethod.ANALYST_JUDGEMENT_REQUIRED:
        item.suggested_valuation_method = OPTION_TYPE_TO_METHOD.get(item.option_type, item.suggested_valuation_method)

    item.source_provision_ids = [provision_id for provision_id in item.source_provision_ids if provision_id in provision_ids]
    if not item.source_category and item.source_provision_ids:
        provision = provision_by_id.get(item.source_provision_ids[0])
        item.source_category = getattr(provision, "category", None)

    item.commercial_description = _sanitize_text(item.commercial_description, item.warnings)
    item.extracted_right = _sanitize_optional_text(item.extracted_right, item.warnings)
    item.economic_value_logic = _sanitize_optional_text(item.economic_value_logic, item.warnings)
    item.required_market_data = [_sanitize_text(value, item.warnings) for value in item.required_market_data]
    item.required_operational_data = [_sanitize_text(value, item.warnings) for value in item.required_operational_data]
    item.required_portfolio_data = [_sanitize_text(value, item.warnings) for value in item.required_portfolio_data]
    item.required_analyst_assumptions = [_sanitize_text(value, item.warnings) for value in item.required_analyst_assumptions]
    item.key_value_drivers = [_sanitize_text(value, item.warnings) for value in item.key_value_drivers]
    item.key_risks_or_constraints = [_sanitize_text(value, item.warnings) for value in item.key_risks_or_constraints]

    if not item.required_market_data:
        item.required_market_data.append("Market price curves, spreads, volatility, liquidity, and scenario assumptions required before valuation.")
    if not item.required_operational_data:
        item.required_operational_data.append("Operational constraints, capacity, scheduling, and deliverability assumptions required before valuation.")
    if not item.required_portfolio_data:
        item.required_portfolio_data.append("Portfolio exposure, concentration, and optimization constraints required before portfolio analysis.")
    if not item.required_analyst_assumptions:
        item.required_analyst_assumptions.append("Analyst must validate the contractual right and map it to a later valuation method.")
    if item.confidence == Confidence.LOW and not item.warnings:
        item.warnings.append("Low confidence optionality extraction; analyst validation is required.")
    if item.evidence_status == EvidenceStatus.INSUFFICIENT_EVIDENCE and not any("insufficient" in warning.lower() for warning in item.warnings):
        item.warnings.append("Insufficient evidence supports this optionality item; do not value without contract validation.")
    if item.valuation_impact != ValuationImpact.OPTIONALITY and item.option_type in {OptionType.DESTINATION_FLEX, OptionType.VOLUME_FLEX, OptionType.MAKE_UP, OptionType.PRICE_REOPENER}:
        item.warnings.append("Option-like right was identified but valuation impact was not marked optionality; analyst review required.")


def _ensure_optionality_impact_provisions_represented(response: CommercialEvaluationResponse) -> None:
    represented_ids = {
        provision_id
        for item in response.optionality_register
        for provision_id in item.source_provision_ids
    }
    next_index = len(response.optionality_register) + 1
    for provision in response.provision_register:
        if provision.valuation_impact != ValuationImpact.OPTIONALITY:
            continue
        if provision.id in represented_ids:
            continue
        option_type = CATEGORY_TO_OPTION_TYPE.get(provision.category, OptionType.OTHER)
        method = OPTION_TYPE_TO_METHOD.get(option_type, SuggestedValuationMethod.ANALYST_JUDGEMENT_REQUIRED)
        response.optionality_register.append(
            OptionalityRegisterItem(
                id=f"OP-{next_index:03d}",
                option_name=f"Analyst validation optionality item for {provision.title}",
                option_type=option_type,
                source_category=provision.category,
                source_provision_ids=[provision.id],
                source_clause_reference=provision.clause_reference,
                extracted_right=provision.extracted_text,
                commercial_description=provision.commercial_meaning,
                economic_value_logic="Provision has optionality valuation impact but was not otherwise represented in the optionality register.",
                suggested_valuation_method=method,
                required_market_data=["Market scenarios and price/spread data required before valuation."],
                required_operational_data=["Operational feasibility assumptions required before valuation."],
                required_portfolio_data=["Portfolio fit and exposure data required before valuation."],
                required_analyst_assumptions=["Validate that the provision creates a real contractual option before valuation."],
                key_value_drivers=[],
                key_risks_or_constraints=list(provision.warnings),
                valuation_impact=ValuationImpact.OPTIONALITY,
                evidence_status=provision.evidence_status,
                confidence=provision.confidence,
                warnings=["Created by deterministic guardrail because an optionality-impact provision lacked an optionality register item."],
                analyst_validation_needed=True,
            )
        )
        next_index += 1


def _sanitize_optional_text(value: str | None, warnings: list[str]) -> str | None:
    if value is None:
        return None
    return _sanitize_text(value, warnings)


def _sanitize_text(text: str, warnings: list[str]) -> str:
    lowered = text.lower()
    if any(phrase in lowered for phrase in PROHIBITED_VALUATION_PHRASES):
        warning = "A prohibited option valuation-result claim was removed; Stage 4 only identifies optionality and method/data needs."
        if warning not in warnings:
            warnings.append(warning)
        return "Option valuation result claim removed; Stage 4 only identifies optionality and method/data needs."
    return text
