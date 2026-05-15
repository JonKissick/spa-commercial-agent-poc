from app.schemas import CommercialEvaluationResponse, Confidence, CoverageStatus, EvidenceStatus
from app.taxonomy import SPA_TAXONOMY, taxonomy_categories
from app.valuation_inputs import normalize_valuation_input_pack

NO_FULL_VALUATION_LIMITATION = "No full valuation calculation, DCF model, or quantitative option valuation has been performed in this Stage 2 analysis."
MARKET_PORTFOLIO_LIMITATION = "Market and portfolio conclusions require manual assumptions unless those assumptions are explicitly supplied in the uploaded document."


class CommercialEvaluationValidationError(ValueError):
    pass


def validate_commercial_evaluation(response: CommercialEvaluationResponse) -> CommercialEvaluationResponse:
    _validate_clause_coverage(response)
    _validate_provisions(response)
    normalize_valuation_input_pack(response)

    _ensure_limitation(response, NO_FULL_VALUATION_LIMITATION, ["no full valuation", "dcf", "option valuation"])
    _ensure_limitation(response, MARKET_PORTFOLIO_LIMITATION, ["market", "portfolio", "manual assumptions"])

    return response


def _validate_clause_coverage(response: CommercialEvaluationResponse) -> None:
    expected_categories = taxonomy_categories()
    actual_categories = [item.category for item in response.clause_coverage]

    if len(actual_categories) != len(set(actual_categories)):
        raise CommercialEvaluationValidationError("Clause coverage contains duplicate taxonomy categories.")

    missing = [category.value for category in expected_categories if category not in actual_categories]
    extra = [category.value for category in actual_categories if category not in SPA_TAXONOMY]
    if missing or extra:
        raise CommercialEvaluationValidationError(
            f"Clause coverage must include every taxonomy category exactly once. Missing={missing}; extra={extra}."
        )

    for item in response.clause_coverage:
        if item.status in {CoverageStatus.PRESENT, CoverageStatus.WEAK_UNCLEAR}:
            if not (item.evidence_summary and item.evidence_summary.strip()) and not item.provision_ids:
                raise CommercialEvaluationValidationError(
                    f"Coverage item {item.category.value} needs evidence_summary or provision_ids when status is {item.status.value}."
                )
            if item.status == CoverageStatus.WEAK_UNCLEAR and not item.warnings:
                item.warnings.append("Evidence is partial, ambiguous, or indirect; analyst validation is required.")
        if item.status == CoverageStatus.NOT_IDENTIFIED:
            if not item.evidence_summary or not _sounds_like_missing_evidence(item.evidence_summary):
                item.evidence_summary = "No supporting clause was identified in the extracted contract text."


def _validate_provisions(response: CommercialEvaluationResponse) -> None:
    provision_ids = {provision.id for provision in response.provision_register}
    for coverage in response.clause_coverage:
        unknown_ids = [provision_id for provision_id in coverage.provision_ids if provision_id not in provision_ids]
        if unknown_ids:
            raise CommercialEvaluationValidationError(
                f"Coverage item {coverage.category.value} references unknown provision ids: {unknown_ids}."
            )

    for index, provision in enumerate(response.provision_register, start=1):
        if provision.category not in SPA_TAXONOMY:
            raise CommercialEvaluationValidationError(f"Provision {provision.id} category is not in the SPA taxonomy.")
        if not provision.id.strip():
            raise CommercialEvaluationValidationError(f"Provision {index} is missing an id.")
        if not provision.title.strip():
            raise CommercialEvaluationValidationError(f"Provision {provision.id} is missing a title.")
        if provision.evidence_status == EvidenceStatus.INSUFFICIENT_EVIDENCE:
            warning = "Insufficient contract evidence supports this provision; analyst review is required."
            if not any("insufficient" in item.lower() or "missing" in item.lower() for item in provision.warnings):
                provision.warnings.append(warning)
        if provision.confidence == Confidence.LOW and not provision.warnings:
            provision.warnings.append("Low confidence extraction; analyst validation is required before commercial reliance.")


def _sounds_like_missing_evidence(summary: str) -> bool:
    lowered = summary.lower()
    return any(term in lowered for term in ["no supporting", "not identified", "not found", "no clause", "insufficient evidence"])


def _ensure_limitation(response: CommercialEvaluationResponse, limitation: str, required_terms: list[str]) -> None:
    limitations_text = " ".join(response.limitations).lower()
    if not all(term in limitations_text for term in required_terms):
        response.limitations.append(limitation)
