import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.analysis_pipeline import run_analysis_pipeline
from app.config import get_settings
from app.schemas import CoverageStatus, ProvisionCategory
from app.validation import validate_commercial_evaluation


SAMPLE_TEXT = "Sample SPA text with pricing, delivery, volume, credit, and commercial terms. " * 3


def _mock_response(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
    return run_analysis_pipeline(SAMPLE_TEXT)


def test_valuation_input_pack_has_stage_3_structured_fields(monkeypatch) -> None:
    pack = _mock_response(monkeypatch).valuation_input_pack

    assert pack.price_basis
    assert pack.pricing_formula
    assert pack.volume_obligation
    assert pack.volume_flexibility
    assert pack.credit_support
    assert pack.dcf_relevant_inputs
    assert pack.optionality_relevant_inputs


def test_missing_assumption_and_warning_buckets_are_lists(monkeypatch) -> None:
    pack = _mock_response(monkeypatch).valuation_input_pack

    assert isinstance(pack.missing_analyst_assumptions, list)
    assert isinstance(pack.missing_market_data, list)
    assert isinstance(pack.missing_portfolio_data, list)
    assert isinstance(pack.valuation_warnings, list)


def test_valuation_inputs_support_source_provision_id_linkage(monkeypatch) -> None:
    pack = _mock_response(monkeypatch).valuation_input_pack

    assert pack.pricing_formula[0].source_provision_ids == ["PR-001"]
    assert pack.volume_flexibility[0].source_provision_ids == ["PR-002"]
    assert pack.credit_support[0].source_provision_ids == ["PR-003"]


def test_missing_pricing_coverage_creates_valuation_warning(monkeypatch) -> None:
    response = _mock_response(monkeypatch)
    for item in response.clause_coverage:
        if item.category == ProvisionCategory.PRICING:
            item.status = CoverageStatus.NOT_IDENTIFIED
            item.evidence_summary = "No supporting clause was identified in the extracted contract text."
            item.provision_ids = []

    validate_commercial_evaluation(response)

    warnings = " ".join(response.valuation_input_pack.valuation_warnings).lower()
    assert "missing pricing support" in warnings


def test_missing_volume_coverage_creates_valuation_warning(monkeypatch) -> None:
    response = _mock_response(monkeypatch)
    warnings = " ".join(response.valuation_input_pack.valuation_warnings).lower()

    assert "missing volume support" in warnings


def test_prohibited_final_valuation_phrases_are_sanitized(monkeypatch) -> None:
    response = _mock_response(monkeypatch)
    response.valuation_input_pack.price_basis[0].value = "NPV is USD 10 million"

    validate_commercial_evaluation(response)

    value = response.valuation_input_pack.price_basis[0].value
    warnings = " ".join(response.valuation_input_pack.valuation_warnings).lower()
    assert value == "Valuation result claim removed; Stage 3 only prepares valuation input candidates."
    assert "prohibited valuation-result claim" in warnings


def test_valuation_limitations_remain(monkeypatch) -> None:
    response = _mock_response(monkeypatch)
    limitations = " ".join(response.limitations).lower()

    assert "no full valuation" in limitations
    assert "market" in limitations
    assert "portfolio" in limitations
    assert "manual assumptions" in limitations
