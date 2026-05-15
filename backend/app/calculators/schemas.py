from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class ScenarioName(StrEnum):
    BASE = "base"
    UPSIDE = "upside"
    DOWNSIDE = "downside"
    STRESS = "stress"


class CalculatorContractRole(StrEnum):
    BUYER = "buyer"
    SELLER = "seller"


class CalculatorDeliveryBasis(StrEnum):
    DES = "des"
    FOB = "fob"
    EX_SHIP = "ex_ship"
    DELIVERED = "delivered"
    FREE_ON_BOARD = "free_on_board"
    UNCLEAR = "unclear"


class CalculationStatus(StrEnum):
    CALCULATED = "calculated"
    PARTIAL = "partial"
    INVALID = "invalid"


class ScenarioAssumptions(BaseModel):
    scenario_name: ScenarioName
    annual_volume: float
    contract_price: float
    market_price: float
    supply_cost: float | None = None
    freight_cost: float | None = None
    boil_off_cost: float | None = None
    port_canal_cost: float | None = None
    regas_terminal_cost: float | None = None
    downstream_cost: float | None = None
    other_costs: float | None = None
    annual_fixed_costs: float | None = None
    notes: str | None = None

    @field_validator("annual_volume")
    @classmethod
    def annual_volume_must_be_non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("annual_volume must be non-negative")
        return value


class NpvCalculationRequest(BaseModel):
    contract_role: CalculatorContractRole
    delivery_basis: CalculatorDeliveryBasis
    discount_rate: float
    contract_years: int
    currency: str = "USD"
    unit: str = "MMBtu"
    scenarios: list[ScenarioAssumptions]
    include_midyear_discounting: bool = False

    @field_validator("discount_rate")
    @classmethod
    def discount_rate_must_be_reasonable(cls, value: float) -> float:
        if value < 0 or value >= 1:
            raise ValueError("discount_rate must be greater than or equal to 0 and less than 1")
        return value

    @field_validator("contract_years")
    @classmethod
    def contract_years_must_be_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("contract_years must be positive")
        return value

    @field_validator("scenarios")
    @classmethod
    def scenarios_required(cls, value: list[ScenarioAssumptions]) -> list[ScenarioAssumptions]:
        if not value:
            raise ValueError("At least one scenario is required")
        return value


class ScenarioNpvResult(BaseModel):
    scenario_name: ScenarioName
    annual_unit_margin: float
    annual_cash_flow: float
    npv: float
    undiscounted_total_cash_flow: float
    formula_used: str
    included_costs: list[str] = Field(default_factory=list)
    excluded_costs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    break_even_candidates: dict[str, float | None] = Field(default_factory=dict)


class NpvCalculationResponse(BaseModel):
    calculation_status: CalculationStatus
    contract_role: CalculatorContractRole
    delivery_basis: CalculatorDeliveryBasis
    currency: str
    unit: str
    discount_rate: float
    contract_years: int
    scenario_results: list[ScenarioNpvResult] = Field(default_factory=list)
    key_sensitivities: list[str] = Field(default_factory=list)
    break_even_candidates: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
