from app.schemas import CommercialEvaluationResponse, EvidenceStatus

NO_FULL_VALUATION_LIMITATION = "No full valuation calculation, DCF model, or quantitative option valuation has been performed in this Stage 1 analysis."
MARKET_PORTFOLIO_LIMITATION = "Market and portfolio conclusions require manual assumptions unless those assumptions are explicitly supplied in the uploaded document."


class CommercialEvaluationValidationError(ValueError):
    pass


def validate_commercial_evaluation(response: CommercialEvaluationResponse) -> CommercialEvaluationResponse:
    for index, provision in enumerate(response.provision_register, start=1):
        if not provision.id.strip():
            raise CommercialEvaluationValidationError(f"Provision {index} is missing an id.")
        if not provision.title.strip():
            raise CommercialEvaluationValidationError(f"Provision {provision.id} is missing a title.")
        if provision.evidence_status == EvidenceStatus.INSUFFICIENT_EVIDENCE:
            warning = "Insufficient contract evidence supports this provision; analyst review is required."
            if not any("insufficient" in item.lower() for item in provision.warnings):
                provision.warnings.append(warning)

    _ensure_limitation(response, NO_FULL_VALUATION_LIMITATION, ["no full valuation", "dcf", "option valuation"])
    _ensure_limitation(response, MARKET_PORTFOLIO_LIMITATION, ["market", "portfolio", "manual assumptions"])

    return response


def _ensure_limitation(response: CommercialEvaluationResponse, limitation: str, required_terms: list[str]) -> None:
    limitations_text = " ".join(response.limitations).lower()
    if not all(term in limitations_text for term in required_terms):
        response.limitations.append(limitation)
