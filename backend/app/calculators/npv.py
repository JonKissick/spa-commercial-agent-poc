from app.calculators.schemas import (
    BreakEvenResult,
    CalculationStatus,
    CalculatorContractRole,
    CalculatorDeliveryBasis,
    NpvCalculationRequest,
    NpvCalculationResponse,
    ScenarioAssumptions,
    ScenarioNpvResult,
    SensitivityInput,
    SensitivityPoint,
    SensitivityTable,
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
    "Sensitivity tables are deterministic one-variable-at-a-time sensitivities using manual assumptions only.",
    "Break-even outputs use flat annual margin assumptions and do not include probability weighting, correlations, stochastic simulation, or option valuation.",
]


def calculate_npv(request: NpvCalculationRequest) -> NpvCalculationResponse:
    warnings: list[str] = []
    if request.delivery_basis == CalculatorDeliveryBasis.UNCLEAR:
        warnings.append("Delivery basis is unclear; NPV cannot be calculated until DES/FOB/delivered basis is selected.")
        return _response(request, CalculationStatus.INVALID, [], warnings, [], [])

    results = [_calculate_scenario(request, scenario) for scenario in request.scenarios]
    sensitivity_input = request.sensitivity or SensitivityInput()
    sensitivity_tables: list[SensitivityTable] = []
    break_even_results: list[BreakEvenResult] = []
    if sensitivity_input.enabled:
        sensitivity_tables, sensitivity_warnings = _build_sensitivity_tables(request, sensitivity_input)
        warnings.extend(sensitivity_warnings)

    for scenario, result in zip(request.scenarios, results, strict=True):
        break_even = _break_even_result(request, scenario, result)
        break_even_results.append(break_even)
        warnings.extend(break_even.warnings)

    response_warnings = _dedupe(warnings + [warning for result in results for warning in result.warnings])
    return _response(request, CalculationStatus.CALCULATED, results, response_warnings, sensitivity_tables, break_even_results)


def _calculate_scenario(
    request: NpvCalculationRequest,
    scenario: ScenarioAssumptions,
    discount_rate_override: float | None = None,
    include_warnings: bool = True,
) -> ScenarioNpvResult:
    costs = _costs(scenario)
    warnings = _missing_cost_warnings(scenario, request.delivery_basis, request.contract_role) if include_warnings else []
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
    discount_rate = request.discount_rate if discount_rate_override is None else discount_rate_override
    npv = _discounted_cash_flow(annual_cash_flow, discount_rate, request.contract_years, request.include_midyear_discounting)
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
        break_even_candidates=_legacy_break_even_candidates(request, scenario, costs),
    )


def _build_sensitivity_tables(
    request: NpvCalculationRequest,
    sensitivity: SensitivityInput,
) -> tuple[list[SensitivityTable], list[str]]:
    tables: list[SensitivityTable] = []
    warnings: list[str] = []
    for scenario in request.scenarios:
        for variable, shifts in [
            ("market_price", sensitivity.market_price_shifts),
            ("contract_price", sensitivity.contract_price_shifts),
            ("freight_cost", sensitivity.freight_cost_shifts),
            ("discount_rate", sensitivity.discount_rate_shifts),
        ]:
            applicable, note = _sensitivity_applicability(request, variable)
            if not applicable:
                warnings.append(note or f"{variable} sensitivity is not applicable for this role/basis.")
                if variable == "market_price" and request.contract_role == CalculatorContractRole.SELLER:
                    tables.append(_non_applicable_table(scenario, variable, note or "Market price is not directly used in seller margin formula."))
                continue
            points: list[SensitivityPoint] = []
            for shift in shifts:
                shifted_scenario = scenario.model_copy(deep=True)
                shifted_rate = request.discount_rate
                point_note = None
                if variable == "discount_rate":
                    shifted_rate = request.discount_rate + shift
                    if shifted_rate < 0:
                        point_note = "Discount rate shift would go below zero; clamped to 0."
                        warnings.append(point_note)
                        shifted_rate = 0
                else:
                    current_value = getattr(shifted_scenario, variable) or 0
                    setattr(shifted_scenario, variable, current_value + shift)
                result = _calculate_scenario(request, shifted_scenario, discount_rate_override=shifted_rate, include_warnings=False)
                points.append(
                    SensitivityPoint(
                        variable=variable,
                        shift=shift,
                        scenario_name=scenario.scenario_name,
                        resulting_npv=result.npv,
                        resulting_annual_unit_margin=result.annual_unit_margin,
                        note=point_note,
                    )
                )
            tables.append(SensitivityTable(scenario_name=scenario.scenario_name, variable=variable, points=points))
    return tables, _dedupe(warnings)


def _sensitivity_applicability(request: NpvCalculationRequest, variable: str) -> tuple[bool, str | None]:
    if variable == "market_price" and request.contract_role == CalculatorContractRole.SELLER:
        return False, "Market price is not directly used in seller margin formula; seller sensitivities should focus on contract price and cost assumptions."
    if variable == "freight_cost":
        if request.contract_role == CalculatorContractRole.BUYER and request.delivery_basis in FOB_BASES:
            return True, None
        if request.contract_role == CalculatorContractRole.SELLER and request.delivery_basis in DES_BASES:
            return True, None
        return False, "Freight cost sensitivity is not applicable because freight is not included in the selected role/basis formula."
    return True, None


def _non_applicable_table(scenario: ScenarioAssumptions, variable: str, note: str) -> SensitivityTable:
    return SensitivityTable(
        scenario_name=scenario.scenario_name,
        variable=variable,
        points=[
            SensitivityPoint(
                variable=variable,
                shift=0,
                scenario_name=scenario.scenario_name,
                resulting_npv=0,
                resulting_annual_unit_margin=0,
                note=note,
            )
        ],
    )


def _break_even_result(request: NpvCalculationRequest, scenario: ScenarioAssumptions, result: ScenarioNpvResult) -> BreakEvenResult:
    costs = _costs(scenario)
    fixed_per_unit, fixed_notes, warnings = _fixed_cost_per_unit(scenario)
    break_even_market_price: float | None = None
    break_even_contract_price: float | None = None
    break_even_freight_cost: float | None = None

    if request.contract_role == CalculatorContractRole.BUYER and request.delivery_basis in FOB_BASES:
        non_contract_costs = sum(costs[field] for field in ["freight_cost", "boil_off_cost", "port_canal_cost", "regas_terminal_cost", "downstream_cost", "other_costs"])
        break_even_market_price = scenario.contract_price + non_contract_costs + fixed_per_unit
        break_even_contract_price = scenario.market_price - non_contract_costs - fixed_per_unit
        break_even_freight_cost = scenario.market_price - scenario.contract_price - sum(costs[field] for field in ["boil_off_cost", "port_canal_cost", "regas_terminal_cost", "downstream_cost", "other_costs"]) - fixed_per_unit
    elif request.contract_role == CalculatorContractRole.BUYER and request.delivery_basis in DES_BASES:
        buyer_costs = sum(costs[field] for field in ["regas_terminal_cost", "downstream_cost", "other_costs"])
        break_even_market_price = scenario.contract_price + buyer_costs + fixed_per_unit
        break_even_contract_price = scenario.market_price - buyer_costs - fixed_per_unit
    elif request.contract_role == CalculatorContractRole.SELLER and request.delivery_basis in FOB_BASES:
        break_even_contract_price = sum(costs[field] for field in ["supply_cost", "port_canal_cost", "other_costs"]) + fixed_per_unit
    elif request.contract_role == CalculatorContractRole.SELLER and request.delivery_basis in DES_BASES:
        seller_costs = sum(costs[field] for field in ["supply_cost", "freight_cost", "boil_off_cost", "port_canal_cost", "regas_terminal_cost", "downstream_cost", "other_costs"])
        break_even_contract_price = seller_costs + fixed_per_unit
        break_even_freight_cost = scenario.contract_price - sum(costs[field] for field in ["supply_cost", "boil_off_cost", "port_canal_cost", "regas_terminal_cost", "downstream_cost", "other_costs"]) - fixed_per_unit

    break_even_volume: float | None = None
    notes = fixed_notes
    if scenario.annual_volume == 0:
        notes.append("Break-even annual volume is not calculated when annual volume is zero in the submitted scenario.")
    elif costs["annual_fixed_costs"] == 0:
        notes.append("Break-even annual volume is not meaningful because annual fixed costs are zero under the flat margin model.")
    elif result.annual_unit_margin > 0:
        break_even_volume = costs["annual_fixed_costs"] / result.annual_unit_margin
    else:
        warnings.append("No positive annual volume can recover fixed costs because annual unit margin is zero or negative.")

    return BreakEvenResult(
        scenario_name=scenario.scenario_name,
        break_even_market_price=_round_optional(break_even_market_price),
        break_even_contract_price=_round_optional(break_even_contract_price),
        break_even_freight_cost=_round_optional(break_even_freight_cost),
        break_even_annual_volume=_round_optional(break_even_volume),
        notes=_dedupe(notes),
        warnings=_dedupe(warnings),
    )


def _fixed_cost_per_unit(scenario: ScenarioAssumptions) -> tuple[float, list[str], list[str]]:
    fixed_costs = float(scenario.annual_fixed_costs or 0)
    if scenario.annual_volume == 0:
        return 0, [], ["Annual volume is zero; fixed cost per unit and volume break-even outputs are not meaningful."]
    return fixed_costs / scenario.annual_volume, ["Break-even values include annual fixed costs spread over annual volume."] if fixed_costs else [], []


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
    if scenario.annual_volume == 0:
        warnings.append("Annual volume is zero; annual cash flow and break-even volume outputs may not be meaningful.")
    if role == CalculatorContractRole.BUYER and basis in FOB_BASES and scenario.freight_cost is None:
        warnings.append("FOB buyer calculation normally requires freight cost; defaulting to 0 may materially overstate value.")
    if role == CalculatorContractRole.SELLER and basis in DES_BASES and scenario.freight_cost is None:
        warnings.append("DES seller calculation normally requires freight cost; defaulting to 0 may materially overstate value.")
    warnings.append("No optionality value is included in this scenario NPV.")
    return _dedupe(warnings)


def _legacy_break_even_candidates(request: NpvCalculationRequest, scenario: ScenarioAssumptions, costs: dict[str, float]) -> dict[str, float | None]:
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
    sensitivity_tables: list[SensitivityTable],
    break_even_results: list[BreakEvenResult],
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
            "break-even annual volume where fixed costs and positive unit margin make it meaningful",
        ],
        warnings=_dedupe(warnings),
        limitations=LIMITATIONS,
        sensitivity_tables=sensitivity_tables,
        break_even_results=break_even_results,
    )


def _round_optional(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def _dedupe(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value and value not in output:
            output.append(value)
    return output
