import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.analysis_pipeline import ContractTextValidationError, run_analysis_pipeline
from app.config import get_settings
from app.schemas import CommercialEvaluationResponse, CoverageStatus, EvidenceStatus, ProvisionCategory, RecommendationValue


SAMPLE_TEXT = "Sample SPA text with pricing, delivery, volume, credit, and commercial terms. " * 3


def _mock_response(monkeypatch) -> CommercialEvaluationResponse:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
    return run_analysis_pipeline(SAMPLE_TEXT)


def test_mock_pipeline_returns_valid_response_without_api_key(monkeypatch) -> None:
    response = _mock_response(monkeypatch)

    assert isinstance(response, CommercialEvaluationResponse)
    assert response.deal_recommendation.recommendation == RecommendationValue.INSUFFICIENT_EVIDENCE
    assert response.recommendation is not None
    assert response.recommendation.recommendation == RecommendationValue.INSUFFICIENT_EVIDENCE
    assert response.market_context_assessment.evidence_status == EvidenceStatus.MARKET_ASSUMPTION_REQUIRED
    assert response.portfolio_fit_assessment.evidence_status == EvidenceStatus.PORTFOLIO_ASSUMPTION_REQUIRED
    assert response.contract_summary.evidence[0].status == EvidenceStatus.EXTRACTED_FROM_CONTRACT
    assert response.clause_coverage
    assert response.provision_register
    assert response.provision_register[0].title
    assert response.provision_register[0].commercial_meaning
    assert response.provision_register[0].interpretation == response.provision_register[0].commercial_meaning
    assert response.optionality_register


def test_pipeline_rejects_too_short_contract_text(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()

    try:
        run_analysis_pipeline("short")
    except ContractTextValidationError as exc:
        assert "too short" in str(exc)
    else:
        raise AssertionError("Short contract text should be rejected")


def test_clause_coverage_includes_every_category_once(monkeypatch) -> None:
    response = _mock_response(monkeypatch)
    categories = [item.category for item in response.clause_coverage]

    assert set(categories) == set(ProvisionCategory)
    assert len(categories) == len(set(categories)) == len(ProvisionCategory)


def test_clause_coverage_demonstrates_present_weak_and_not_identified(monkeypatch) -> None:
    response = _mock_response(monkeypatch)
    statuses = {item.status for item in response.clause_coverage}

    assert CoverageStatus.PRESENT in statuses
    assert CoverageStatus.WEAK_UNCLEAR in statuses
    assert CoverageStatus.NOT_IDENTIFIED in statuses


def test_clause_coverage_evidence_rules(monkeypatch) -> None:
    response = _mock_response(monkeypatch)

    for item in response.clause_coverage:
        if item.status in {CoverageStatus.PRESENT, CoverageStatus.WEAK_UNCLEAR}:
            assert item.evidence_summary or item.provision_ids
        if item.status == CoverageStatus.NOT_IDENTIFIED:
            assert item.evidence_summary
            assert any(term in item.evidence_summary.lower() for term in ["no supporting", "not identified", "not found"])


def test_limitations_include_no_full_valuation_guardrail(monkeypatch) -> None:
    response = _mock_response(monkeypatch)
    limitations = " ".join(response.limitations).lower()

    assert "no full valuation" in limitations
    assert "dcf" in limitations
    assert "option valuation" in limitations


def test_limitations_include_manual_market_portfolio_assumption_warning(monkeypatch) -> None:
    response = _mock_response(monkeypatch)
    limitations = " ".join(response.limitations).lower()

    assert "market" in limitations
    assert "portfolio" in limitations
    assert "manual assumptions" in limitations


def test_insufficient_evidence_provisions_include_warnings(monkeypatch) -> None:
    response = _mock_response(monkeypatch)
    insufficient_items = [
        item for item in response.provision_register if item.evidence_status == EvidenceStatus.INSUFFICIENT_EVIDENCE
    ]

    assert insufficient_items
    assert all(item.warnings for item in insufficient_items)
    assert all(any("insufficient" in warning.lower() for warning in item.warnings) for item in insufficient_items)


def test_low_confidence_provisions_include_warnings(monkeypatch) -> None:
    response = _mock_response(monkeypatch)
    low_confidence_items = [item for item in response.provision_register if item.confidence == "low"]

    assert low_confidence_items
    assert all(item.warnings for item in low_confidence_items)
