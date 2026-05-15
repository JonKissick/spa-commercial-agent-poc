import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.analysis_models.deal_structure import assess_deal_structure
from app.analysis_models.landed_value import select_landed_value_or_netback_model
from app.analysis_models.npv_readiness import assess_npv_readiness
from app.analysis_models.optionality_routing import route_optionality_models
from app.analysis_models.schemas import ApplicableModel, ContractRole, DealStructureAssessment, DeliveryBasis
from app.analysis_pipeline import _build_mock_response, run_analysis_pipeline


def test_analysis_model_outputs_exist_in_mock_pipeline(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    response = run_analysis_pipeline("Buyer purchases LNG on a DES delivered basis at discharge port Tokyo Bay with pricing and volume terms. " * 3)

    assert response.analysis_model_outputs is not None
    assert response.analysis_model_outputs.deal_structure
    assert response.analysis_model_outputs.npv_readiness.can_calculate_npv_now is False


def test_deal_structure_classifier_detects_des_ex_ship_delivered_text() -> None:
    response = _build_mock_response("Buyer purchase LNG DES ex-ship delivered at destination discharge port Tokyo Bay. Seller bears delivery. " * 3)

    assessment = assess_deal_structure(response)

    assert assessment.delivery_basis in {DeliveryBasis.DES, DeliveryBasis.EX_SHIP, DeliveryBasis.DELIVERED}
    assert assessment.shipping_responsibility == "seller"


def test_deal_structure_classifier_detects_fob_free_on_board_text() -> None:
    response = _build_mock_response("Buyer purchase LNG FOB free on board at loading port Bonny. Buyer arranges freight to destination. " * 3)

    assessment = assess_deal_structure(response)

    assert assessment.delivery_basis in {DeliveryBasis.FOB, DeliveryBasis.FREE_ON_BOARD}
    assert assessment.shipping_responsibility == "buyer"


def test_npv_readiness_is_not_ready_or_partial_when_core_inputs_missing() -> None:
    response = _build_mock_response("SPA text with pricing but missing term discount rate market reference and logistics detail. " * 3)
    deal_structure = assess_deal_structure(response)

    readiness = assess_npv_readiness(response, deal_structure)

    assert readiness.readiness in {"partial", "not_ready"}
    assert readiness.can_calculate_npv_now is False
    assert readiness.missing_contract_inputs
    assert readiness.required_manual_assumptions


def test_fob_readiness_requires_logistics_inputs() -> None:
    response = _build_mock_response("Buyer purchase LNG FOB loading port Freeport with pricing and volume. " * 3)
    deal_structure = assess_deal_structure(response)

    readiness = assess_npv_readiness(response, deal_structure)

    logistics = " ".join(readiness.required_logistics_data).lower()
    assert "freight" in logistics
    assert "boil-off" in logistics
    assert "origin/loading port" in logistics
    assert "destination" in logistics


def test_des_readiness_requires_destination_terminal_downstream_inputs() -> None:
    response = _build_mock_response("Buyer purchase LNG DES delivered discharge point Tokyo with pricing and volume. " * 3)
    deal_structure = assess_deal_structure(response)

    readiness = assess_npv_readiness(response, deal_structure)

    logistics = " ".join(readiness.required_logistics_data).lower()
    assert "destination" in logistics
    assert "terminal" in logistics or "downstream" in logistics


def test_landed_value_selector_picks_fob_purchase_for_buyer_fob() -> None:
    assessment = DealStructureAssessment(contract_role=ContractRole.BUYER, delivery_basis=DeliveryBasis.FOB)

    selected = select_landed_value_or_netback_model(assessment)

    assert selected.applicable_model == ApplicableModel.FOB_PURCHASE
    assert "freight" in " ".join(selected.required_logistics_inputs).lower()


def test_landed_value_selector_picks_des_purchase_for_buyer_des() -> None:
    assessment = DealStructureAssessment(contract_role=ContractRole.BUYER, delivery_basis=DeliveryBasis.DES)

    selected = select_landed_value_or_netback_model(assessment)

    assert selected.applicable_model == ApplicableModel.DES_PURCHASE
    assert "destination" in selected.economic_logic.lower()


def test_optionality_routing_maps_volume_and_destination_flex() -> None:
    response = _build_mock_response("Buyer purchase LNG with destination flexibility and volume flexibility. " * 3)

    routing = route_optionality_models(response)

    by_type = {item.option_type: item.suggested_model for item in routing.routed_options}
    assert by_type["volume_flex"] == "swing_option"
    assert by_type["destination_flex"] == "spread_option"


def test_model_outputs_do_not_include_numeric_valuation_claims(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    response = run_analysis_pipeline("Buyer purchase LNG FOB with pricing, volume, delivery, and optionality terms. " * 3)

    payload = response.analysis_model_outputs.model_dump_json().lower()

    assert "npv is" not in payload
    assert "irr is" not in payload
    assert "fair value is" not in payload
    assert "option value is" not in payload
    assert "final valuation" not in payload
    assert response.analysis_model_outputs.npv_readiness.can_calculate_npv_now is False
