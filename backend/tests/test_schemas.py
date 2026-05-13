import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.analysis_pipeline import ContractTextValidationError, run_analysis_pipeline
from app.config import get_settings
from app.schemas import CommercialEvaluationResponse, EvidenceStatus, RecommendationValue


SAMPLE_TEXT = "Sample SPA text with pricing, delivery, volume, credit, and commercial terms. " * 3


def test_mock_pipeline_returns_valid_response_without_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()

    response = run_analysis_pipeline(SAMPLE_TEXT)

    assert isinstance(response, CommercialEvaluationResponse)
    assert response.deal_recommendation.recommendation == RecommendationValue.INSUFFICIENT_EVIDENCE
    assert response.recommendation is not None
    assert response.recommendation.recommendation == RecommendationValue.INSUFFICIENT_EVIDENCE
    assert response.market_context_assessment.evidence_status == EvidenceStatus.MARKET_ASSUMPTION_REQUIRED
    assert response.portfolio_fit_assessment.evidence_status == EvidenceStatus.PORTFOLIO_ASSUMPTION_REQUIRED
    assert response.contract_summary.evidence[0].status == EvidenceStatus.EXTRACTED_FROM_CONTRACT
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


def test_limitations_include_no_full_valuation_guardrail(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()

    response = run_analysis_pipeline(SAMPLE_TEXT)
    limitations = " ".join(response.limitations).lower()

    assert "no full valuation" in limitations
    assert "dcf" in limitations
    assert "option valuation" in limitations


def test_limitations_include_manual_market_portfolio_assumption_warning(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()

    response = run_analysis_pipeline(SAMPLE_TEXT)
    limitations = " ".join(response.limitations).lower()

    assert "market" in limitations
    assert "portfolio" in limitations
    assert "manual assumptions" in limitations


def test_insufficient_evidence_provisions_include_warnings(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()

    response = run_analysis_pipeline(SAMPLE_TEXT)
    insufficient_items = [
        item for item in response.provision_register if item.evidence_status == EvidenceStatus.INSUFFICIENT_EVIDENCE
    ]

    assert insufficient_items
    assert all(item.warnings for item in insufficient_items)
    assert all(any("insufficient" in warning.lower() for warning in item.warnings) for item in insufficient_items)
