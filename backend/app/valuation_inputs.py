from app.schemas import (
    ClauseCoverageItem,
    CommercialEvaluationResponse,
    CoverageStatus,
    EvidenceStatus,
    ProvisionCategory,
    ValuationInputItem,
    ValuationInputPack,
)

PROHIBITED_VALUATION_PHRASES = [
    "npv is",
    "irr is",
    "fair value is",
    "option value is",
    "expected profit is",
    "final valuation",
    "calculated value",
    "dcf result",
    "monte carlo result",
]

STRUCTURED_INPUT_FIELDS = [
    "price_basis",
    "pricing_formula",
    "price_index",
    "price_adjustments",
    "currency",
    "volume_obligation",
    "volume_range",
    "annual_contract_quantity",
    "take_or_pay_obligation",
    "delivery_point",
    "delivery_terms",
    "duration",
    "start_date",
    "end_date",
    "extension_rights",
    "destination_flexibility",
    "volume_flexibility",
    "make_up_rights",
    "carry_forward_rights",
    "price_review_or_reopener",
    "penalties_or_liquidated_damages",
    "credit_support",
    "quality_specifications",
    "tax_or_change_in_law_exposure",
    "operational_constraints",
    "termination_economics",
    "dcf_relevant_inputs",
    "optionality_relevant_inputs",
    "risk_adjustment_inputs",
    "portfolio_relevant_inputs",
]


def normalize_valuation_input_pack(response: CommercialEvaluationResponse) -> CommercialEvaluationResponse:
    pack = response.valuation_input_pack
    coverage_by_category = {item.category: item for item in response.clause_coverage}
    provision_ids = {provision.id for provision in response.provision_register}

    _ensure_lists(pack)
    _ensure_missing_data_buckets(pack)
    _ensure_coverage_warnings(pack, coverage_by_category)
    _sanitize_structured_items(pack, provision_ids)
    _sanitize_string_lists(pack)

    return response


def _ensure_lists(pack: ValuationInputPack) -> None:
    for field in STRUCTURED_INPUT_FIELDS:
        value = getattr(pack, field)
        if value is None:
            setattr(pack, field, [])
        elif not isinstance(value, list):
            setattr(pack, field, [value])

    for field in [
        "missing_analyst_assumptions",
        "missing_market_data",
        "missing_portfolio_data",
        "valuation_warnings",
        "pricing_inputs",
        "volume_inputs",
        "timing_inputs",
        "risk_inputs",
        "required_analyst_assumptions",
    ]:
        value = getattr(pack, field)
        if value is None:
            setattr(pack, field, [])
        elif not isinstance(value, list):
            setattr(pack, field, [str(value)])


def _ensure_missing_data_buckets(pack: ValuationInputPack) -> None:
    _append_unique(
        pack.missing_market_data,
        "Forward curves, basis differentials, volatility, liquidity, FX, and other market data must be supplied before valuation.",
    )
    _append_unique(
        pack.missing_portfolio_data,
        "Current portfolio exposure, constraints, concentration limits, and operational capacity must be supplied before portfolio analysis.",
    )
    if not pack.missing_analyst_assumptions:
        pack.missing_analyst_assumptions.append(
            "Analyst must confirm extracted contract terms and map them to the intended commercial model inputs."
        )


def _ensure_coverage_warnings(pack: ValuationInputPack, coverage_by_category: dict[ProvisionCategory, ClauseCoverageItem]) -> None:
    pricing_coverage = coverage_by_category.get(ProvisionCategory.PRICING)
    if pricing_coverage is None or pricing_coverage.status != CoverageStatus.PRESENT:
        _append_unique(pack.valuation_warnings, "Missing pricing support: pricing coverage is not present in the extracted contract text.")

    volume_coverage = coverage_by_category.get(ProvisionCategory.VOLUME)
    if volume_coverage is None or volume_coverage.status != CoverageStatus.PRESENT:
        _append_unique(pack.valuation_warnings, "Missing volume support: volume coverage is not present in the extracted contract text.")


def _sanitize_structured_items(pack: ValuationInputPack, provision_ids: set[str]) -> None:
    for field in STRUCTURED_INPUT_FIELDS:
        sanitized_items: list[ValuationInputItem] = []
        for item in getattr(pack, field):
            if not isinstance(item, ValuationInputItem):
                item = ValuationInputItem(
                    name=field,
                    value=str(item),
                    source_provision_ids=[],
                    evidence_status=EvidenceStatus.ANALYST_ASSUMPTION_REQUIRED,
                    confidence="low",
                    analyst_assumption_needed=True,
                    warnings=["Input was normalized from an unstructured value."],
                )
            item.source_provision_ids = [provision_id for provision_id in item.source_provision_ids if provision_id in provision_ids]
            item.value = _sanitize_value(item.value, pack.valuation_warnings)
            item.warnings = [_sanitize_text(warning, pack.valuation_warnings) for warning in item.warnings]
            if item.evidence_status == EvidenceStatus.INSUFFICIENT_EVIDENCE and not item.warnings:
                item.warnings.append("Insufficient evidence supports this valuation input; analyst validation is required.")
            sanitized_items.append(item)
        setattr(pack, field, sanitized_items)


def _sanitize_string_lists(pack: ValuationInputPack) -> None:
    for field in [
        "missing_analyst_assumptions",
        "missing_market_data",
        "missing_portfolio_data",
        "valuation_warnings",
        "pricing_inputs",
        "volume_inputs",
        "timing_inputs",
        "risk_inputs",
        "required_analyst_assumptions",
    ]:
        sanitized = [_sanitize_text(str(item), pack.valuation_warnings) for item in getattr(pack, field)]
        setattr(pack, field, _dedupe(sanitized))


def _sanitize_value(value: str | list[str] | dict[str, str] | None, warnings: list[str]) -> str | list[str] | dict[str, str] | None:
    if isinstance(value, list):
        return [_sanitize_text(str(item), warnings) for item in value]
    if isinstance(value, dict):
        return {str(key): _sanitize_text(str(val), warnings) for key, val in value.items()}
    if isinstance(value, str):
        return _sanitize_text(value, warnings)
    return value


def _sanitize_text(text: str, warnings: list[str]) -> str:
    lowered = text.lower()
    if any(phrase in lowered for phrase in PROHIBITED_VALUATION_PHRASES):
        _append_unique(
            warnings,
            "A prohibited valuation-result claim was removed; Stage 3 only prepares valuation input candidates.",
        )
        return "Valuation result claim removed; Stage 3 only prepares valuation input candidates."
    return text


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _dedupe(items: list[str]) -> list[str]:
    deduped: list[str] = []
    for item in items:
        if item not in deduped:
            deduped.append(item)
    return deduped
