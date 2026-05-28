import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.analysis_pipeline import _build_mock_response
from app.calculators.npv import calculate_npv
from app.calculators.schemas import NpvCalculationRequest, ScenarioAssumptions
from app.main import app


def _analysis_payload() -> dict:
    analysis = _build_mock_response("Sample LNG SPA text with pricing, volume, delivery, destination, and credit terms. " * 3)
    return analysis.model_dump(mode="json")


def _npv_payload() -> dict:
    request = NpvCalculationRequest(
        contract_role="buyer",
        delivery_basis="fob",
        discount_rate=0.1,
        contract_years=2,
        currency="USD",
        unit="MMBtu",
        scenarios=[
            ScenarioAssumptions(
                scenario_name="base",
                annual_volume=100,
                contract_price=8,
                market_price=12,
                freight_cost=1,
                boil_off_cost=0.2,
                port_canal_cost=0.1,
                regas_terminal_cost=0.4,
                downstream_cost=0.3,
                annual_fixed_costs=10,
            )
        ],
    )
    return calculate_npv(request).model_dump(mode="json")


def test_board_paper_draft_endpoint_is_grounded_and_draft_marked() -> None:
    client = TestClient(app)

    response = client.post(
        "/agents/board-paper/draft",
        json={"analysis": _analysis_payload(), "npv": _npv_payload()},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "mock_bedrock_rag"
    assert payload["grounding_status"] == "draft_requires_review"
    assert payload["valuation_summary"]
    assert any(citation.startswith("provision:") for citation in payload["citations"])
    assert "external Bedrock" in " ".join(payload["limitations"])


def test_management_slide_pack_endpoint_returns_exactly_five_slides() -> None:
    client = TestClient(app)

    response = client.post(
        "/agents/management-slides/draft",
        json={"analysis": _analysis_payload(), "npv": _npv_payload()},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "mock_bedrock_rag"
    assert len(payload["slides"]) == 5
    assert [slide["slide_number"] for slide in payload["slides"]] == [1, 2, 3, 4, 5]
    assert payload["human_review_required"]
