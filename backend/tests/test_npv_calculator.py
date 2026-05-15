import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.calculators.npv import calculate_npv
from app.calculators.schemas import NpvCalculationRequest, ScenarioAssumptions
from app.main import app


def _request(role="buyer", basis="fob", **scenario_overrides):
    scenario = {
        "scenario_name": "base",
        "annual_volume": 100.0,
        "contract_price": 8.0,
        "market_price": 12.0,
        "supply_cost": 5.0,
        "freight_cost": 1.0,
        "boil_off_cost": 0.2,
        "port_canal_cost": 0.1,
        "regas_terminal_cost": 0.4,
        "downstream_cost": 0.3,
        "other_costs": 0.0,
        "annual_fixed_costs": 10.0,
    }
    scenario.update(scenario_overrides)
    return NpvCalculationRequest(
        contract_role=role,
        delivery_basis=basis,
        discount_rate=0.1,
        contract_years=2,
        currency="USD",
        unit="MMBtu",
        scenarios=[ScenarioAssumptions(**scenario)],
    )


def test_buyer_fob_calculation_works() -> None:
    response = calculate_npv(_request(role="buyer", basis="fob"))
    result = response.scenario_results[0]

    assert response.calculation_status == "calculated"
    assert result.annual_unit_margin == 2.0
    assert result.annual_cash_flow == 190.0
    assert result.npv == 329.75
    assert "freight_cost" in result.included_costs


def test_buyer_des_calculation_works() -> None:
    response = calculate_npv(_request(role="buyer", basis="des"))
    result = response.scenario_results[0]

    assert result.annual_unit_margin == 3.3
    assert result.annual_cash_flow == 320.0
    assert "freight_cost" not in result.included_costs


def test_seller_fob_calculation_works() -> None:
    response = calculate_npv(_request(role="seller", basis="fob"))
    result = response.scenario_results[0]

    assert result.annual_unit_margin == 2.9
    assert result.annual_cash_flow == 280.0
    assert "supply_cost" in result.included_costs


def test_seller_des_calculation_works() -> None:
    response = calculate_npv(_request(role="seller", basis="des"))
    result = response.scenario_results[0]

    assert result.annual_unit_margin == 1.0
    assert result.annual_cash_flow == 90.0
    assert "freight_cost" in result.included_costs


def test_missing_optional_costs_default_to_zero_with_warnings() -> None:
    response = calculate_npv(_request(role="buyer", basis="fob", freight_cost=None, boil_off_cost=None))
    result = response.scenario_results[0]

    assert "freight_cost" in result.excluded_costs
    warnings = " ".join(result.warnings).lower()
    assert "defaulted to 0" in warnings
    assert "fob buyer" in warnings


def test_unclear_delivery_basis_returns_invalid() -> None:
    response = calculate_npv(_request(role="buyer", basis="unclear"))

    assert response.calculation_status == "invalid"
    assert response.scenario_results == []
    assert "delivery basis is unclear" in " ".join(response.warnings).lower()


def test_discount_rate_validation_works() -> None:
    with pytest.raises(ValidationError):
        NpvCalculationRequest(
            contract_role="buyer",
            delivery_basis="fob",
            discount_rate=1.2,
            contract_years=2,
            scenarios=[ScenarioAssumptions(scenario_name="base", annual_volume=1, contract_price=1, market_price=2)],
        )


def test_no_optionality_value_is_included() -> None:
    response = calculate_npv(_request())

    payload = response.model_dump_json().lower()
    assert "no optionality value" in payload
    assert "rag" in payload
    assert all("option" not in result.formula_used.lower() for result in response.scenario_results)


def test_endpoint_post_calculators_npv_works() -> None:
    client = TestClient(app)
    payload = _request().model_dump(mode="json")

    response = client.post("/calculators/npv", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["calculation_status"] == "calculated"
    assert body["scenario_results"][0]["npv"] == 329.75
    assert "No LLM or RAG system is used to calculate NPV." in body["limitations"]
