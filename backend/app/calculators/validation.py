from app.calculators.npv import calculate_npv
from app.calculators.schemas import NpvCalculationRequest, NpvCalculationResponse


def validate_and_calculate_npv(request: NpvCalculationRequest) -> NpvCalculationResponse:
    return calculate_npv(request)
