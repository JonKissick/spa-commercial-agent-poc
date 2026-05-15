from app.calculators.schemas import (
    CalculationStatus,
    CalculatorContractRole,
    CalculatorDeliveryBasis,
    NpvCalculationRequest,
    NpvCalculationResponse,
    ScenarioAssumptions,
    ScenarioNpvResult,
)

FOB_BASES = {CalculatorDeliveryBasis.FOB, CalculatorDeliveryBasis.FREE_ON_BOARD}
DES_BASES = {CalculatorDeliveryBasis.DES, CalculatorDeliveryBasis.EX_SHIP, CalculatorDeliveryBasis.DELIVERED}
OPTIONAL_COST_FIELDS = [
    "supply_cost",
    "freight_cost",
    "boil_off_cost",
    "port_canal_cost",
    "regas_terminal_cost",
    "downstream_cost",
    "other_costs",
    "annual_fixed_costs",
]

LIMITATIONS = [
    "Manual assumptions only; no live market data is used.",
    "No LLM or RAG system is used to calculate NPV.",
    "No optionality value, quantitative option valuation, or portfolio optimization is included.",
    "Results are preliminary and require analyst validation before commercial reliance.",
]


def calculate_npv(request: NpvCalculationRequest) -> NpvCalculationResponse:
    warnings: list[str] = []
    if request.delivery_basis == CalculatorDeliveryBasis.UNCLEAR:
        warnings.append("Delivery basis is unclear; NPV cannot be calculated until DES/FOB/delivered basis is selected.")
        return _response(request, CalculationStatus.INVALID, [], warnings)

    results = [_calculate_scenario(request, scenario) for scenario in request.scenarios]
    response_warnings = _dedupe(warnings + [warning for result in results for warning in result.warnings])
    return _response(request, CalculationStatus.CALCULATED, results, response_warnings)


def _calculate_scenario(request: NpvCalculationRequest, scenario: ScenarioAssumptions) -> ScenarioNpvResult:
    costs = _costs(scenario)
    warnings = _missing_cost_warnings(scenario, request.delivery_basis, request.contract_role)
    included_costs: list[str] = []
    excluded_costs = [field for field in OPTIONAL_COST_FIELDS if getattr(scenario, field) is None]

    if request.contract_role == CalculatorContractRole.BUYER and request.delivery_basis in FOB_BASES:
        annual_unit_margin = scenario.market_price - scenario.contract_price - _sum_costs(
            costs,
            ["freight_cost", "boil_off_cost", "port_canal_cost", "regas_terminal_cost", "downstream_cost", "other_costs"],
            included_costs,
        )
        formula = "market_price - contract_price - freight_cost - boil_off_cost - port_canal_cost - regas_terminal_cost - downstream_cost - other_costs"
    elif request.contract_role == CalculatorContractRole.BUYER and request.delivery_basis in DES_BASES:
        annual_unit_margin = scenario.market_price - scenario.contract_price - _sum_costs(
            costs,
            ["regas_terminal_cost", "downstream_cost", "other_costs"],
            included_costs,
        )
        formula = "market_price - contract_price - regas_terminal_cost - downstream_cost - other_costs"
    elif request.contract_role == CalculatorContractRole.SELLER and request.delivery_basis in FOB_BASES:
        annual_unit_margin = scenario.contract_price - _sum_costs(
            costs,
            ["supply_cost", "port_canal_cost", "other_costs"],
            included_costs,
        )
        formula = "contract_price - supply_cost - port_canal_cost - other_costs"
    else:
        annual_unit_margin = scenario.contract_price - _sum_costs(
            costs,
            ["supply_cost", "freight_cost", "boil_off_cost", "port_canal_cost", "regas_terminal_cost", "downstream_cost", "other_costs"],
            included_costs,
        )
        formula = "contract_price - supply_cost - freight_cost - boil_off_cost - port_canal_cost - regas_terminal_cost - downstream_cost - other_costs"

    annual_cash_flow = annual_unit_margin * scenario.annual_volume - costs["annual_fixed_costs"]
    npv = _discounted_cash_flow(annual_cash_flow, request.discount_rate, request.contract_years, request.include_midyear_discounting)
    undiscounted = annual_cash_flow * request.contract_years

    return ScenarioNpvResult(
        scenario_name=scenario.scenario_name,
        annual_unit_margin=round(annual_unit_margin, 6),
        annual_cash_flow=round(annual_cash_flow, 2),
        npv=round(npv, 2),
        undiscounted_total_cash_flow=round(undiscounted, 2),
        formula_used=formula,
        included_costs=_dedupe(included_costs),
        excluded_costs=excluded_costs,
        warnings=warnings,
        break_even_candidates=_break_even_candidates(request, scenario, costs),
    )


def _costs(scenario: ScenarioAssumptions) -> dict[str, float]:
    return {field: float(getattr(scenario, field) or 0) for field in OPTIONAL_COST_FIELDS}


def _sum_costs(costs: dict[str, float], fields: list[str], included_costs: list[str]) -> float:
    total = 0.0
    for field in fields:
        total += costs[field]
        included_costs.append(field)
    return total


def _discounted_cash_flow(annual_cash_flow: float, discount_rate: float, years: int, midyear: bool) -> float:
    total = 0.0
    for year in range(1, years + 1):
        exponent = year - 0.5 if midyear else year
        total += annual_cash_flow / ((1 + discount_rate) ** exponent)
    return total


def _missing_cost_warnings(scenario: ScenarioAssumptions, basis: CalculatorDeliveryBasis, role: CalculatorContractRole) -> list[str]:
    warnings = []
    for field in OPTIONAL_COST_FIELDS:
        if getattr(scenario, field) is None:
            warnings.append(f"{field} was not supplied and defaulted to 0.")
    if role == CalculatorContractRole.BUYER and basis in FOB_BASES and scenario.freight_cost is None:
        warnings.append("FOB buyer calculation normally requires freight cost; defaulting to 0 may materially overstate value.")
    if role == CalculatorContractRole.SELLER and basis in DES_BASES and scenario.freight_cost is None:
        warnings.append("DES seller calculation normally requires freight cost; defaulting to 0 may materially overstate value.")
    warnings.append("No optionality value is included in this scenario NPV.")
    return _dedupe(warnings)


def _break_even_candidates(request: NpvCalculationRequest, scenario: ScenarioAssumptions, costs: dict[str, float]) -> dict[str, float | None]:
    if request.contract_role == CalculatorContractRole.BUYER:
        buyer_non_contract_costs = sum(costs[field] for field in ["freight_cost", "boil_off_cost", "port_canal_cost", "regas_terminal_cost", "downstream_cost", "other_costs"])
        result = {
            "break_even_contract_price": round(scenario.market_price - buyer_non_contract_costs, 6),
            "break_even_market_price": round(scenario.contract_price + buyer_non_contract_costs, 6),
        }
        if request.delivery_basis in FOB_BASES:
            result["break_even_freight_cost"] = round(scenario.market_price - scenario.contract_price - sum(costs[field] for field in ["boil_off_cost", "port_canal_cost", "regas_terminal_cost", "downstream_cost", "other_costs"]), 6)
        return result

    seller_non_price_costs = sum(costs[field] for field in ["supply_cost", "freight_cost", "boil_off_cost", "port_canal_cost", "regas_terminal_cost", "downstream_cost", "other_costs"])
    result = {"break_even_contract_price": round(seller_non_price_costs, 6)}
    if request.delivery_basis in DES_BASES:
        result["break_even_freight_cost"] = round(scenario.contract_price - sum(costs[field] for field in ["supply_cost", "boil_off_cost", "port_canal_cost", "regas_terminal_cost", "downstream_cost", "other_costs"]), 6)
    return result


def _response(
    request: NpvCalculationRequest,
    status: CalculationStatus,
    results: list[ScenarioNpvResult],
    warnings: list[str],
) -> NpvCalculationResponse:
    return NpvCalculationResponse(
        calculation_status=status,
        contract_role=request.contract_role,
        delivery_basis=request.delivery_basis,
        currency=request.currency,
        unit=request.unit,
        discount_rate=request.discount_rate,
        contract_years=request.contract_years,
        scenario_results=results,
        key_sensitivities=[
            "contract price",
            "market price",
            "annual volume",
            "discount rate",
            "freight cost",
            "boil-off cost",
            "terminal/downstream costs",
            "contract tenor",
        ],
        break_even_candidates=[
            "break-even contract price",
            "break-even market price for buyer cases",
            "break-even freight cost for FOB buyer or DES seller cases",
        ],
        warnings=_dedupe(warnings),
        limitations=LIMITATIONS,
    )


def _dedupe(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value and value not in output:
            output.append(value)
    return output
