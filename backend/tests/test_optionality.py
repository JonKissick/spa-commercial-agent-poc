import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.analysis_pipeline import run_analysis_pipeline
from app.config import get_settings
from app.optionality import OPTION_TYPE_TO_METHOD
from app.schemas import EvidenceStatus, OptionType, SuggestedValuationMethod, ValuationImpact
from app.validation import validate_commercial_evaluation


SAMPLE_TEXT = "Sample SPA text with pricing, delivery, volume, credit, and commercial flexibility terms. " * 3


def _mock_response(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
    return run_analysis_pipeline(SAMPLE_TEXT)


def test_optionality_register_present_in_mock_fallback(monkeypatch) -> None:
    response = _mock_response(monkeypatch)

    assert response.optionality_register
    assert len(response.optionality_register) >= 3


def test_optionality_items_support_source_provision_id_linkage(monkeypatch) -> None:
    response = _mock_response(monkeypatch)
    linked_items = [item for item in response.optionality_register if item.source_provision_ids]

    assert linked_items
    assert any("PR-002" in item.source_provision_ids for item in linked_items)
    assert any("PR-004" in item.source_provision_ids for item in linked_items)


def test_allowed_option_types_and_methods_are_populated(monkeypatch) -> None:
    response = _mock_response(monkeypatch)

    for item in response.optionality_register:
        assert item.option_type in set(OptionType)
        assert item.suggested_valuation_method in set(SuggestedValuationMethod)


def test_low_confidence_optionality_items_have_warnings(monkeypatch) -> None:
    response = _mock_response(monkeypatch)
    low_confidence_items = [item for item in response.optionality_register if item.confidence == "low"]

    assert low_confidence_items
    assert all(item.warnings for item in low_confidence_items)


def test_insufficient_evidence_optionality_items_have_warnings(monkeypatch) -> None:
    response = _mock_response(monkeypatch)
    insufficient_items = [
        item for item in response.optionality_register if item.evidence_status == EvidenceStatus.INSUFFICIENT_EVIDENCE
    ]

    assert insufficient_items
    assert all(any("insufficient" in warning.lower() for warning in item.warnings) for item in insufficient_items)


def test_prohibited_option_valuation_claims_are_sanitized(monkeypatch) -> None:
    response = _mock_response(monkeypatch)
    response.optionality_register[0].economic_value_logic = "Option value is USD 5 million"

    validate_commercial_evaluation(response)

    assert response.optionality_register[0].economic_value_logic == (
        "Option valuation result claim removed; Stage 4 only identifies optionality and method/data needs."
    )
    assert any("prohibited option valuation-result" in warning.lower() for warning in response.optionality_register[0].warnings)


def test_optionality_impact_provision_is_represented_or_guardrail_item_created(monkeypatch) -> None:
    response = _mock_response(monkeypatch)
    optionality_provision_ids = {
        provision.id for provision in response.provision_register if provision.valuation_impact == ValuationImpact.OPTIONALITY
    }
    represented_ids = {
        provision_id for item in response.optionality_register for provision_id in item.source_provision_ids
    }

    assert optionality_provision_ids.issubset(represented_ids)


def test_optionality_required_data_categories_are_explicit(monkeypatch) -> None:
    response = _mock_response(monkeypatch)

    for item in response.optionality_register:
        assert item.required_market_data
        assert item.required_operational_data
        assert item.required_portfolio_data
        assert item.required_analyst_assumptions


def test_limitations_include_no_quantitative_option_valuation(monkeypatch) -> None:
    response = _mock_response(monkeypatch)
    limitations = " ".join(response.limitations).lower()

    assert "no full valuation" in limitations
    assert "quantitative option valuation" in limitations
    assert "market" in limitations
    assert "portfolio" in limitations
