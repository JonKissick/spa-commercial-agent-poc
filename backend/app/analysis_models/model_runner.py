from app.analysis_models.deal_structure import assess_deal_structure
from app.analysis_models.landed_value import select_landed_value_or_netback_model
from app.analysis_models.npv_readiness import assess_npv_readiness
from app.analysis_models.optionality_routing import route_optionality_models
from app.analysis_models.portfolio_impact import assess_portfolio_impact_requirements
from app.analysis_models.scenario_requirements import build_scenario_requirements
from app.analysis_models.schemas import AnalysisModelOutputs
from app.analysis_models.utils import unique
from app.schemas import CommercialEvaluationResponse

PROHIBITED_MODEL_CLAIMS = [
    "npv is",
    "irr is",
    "fair value is",
    "option value is",
    "expected profit is",
    "expected margin is",
    "trade p&l is",
    "final valuation",
    "calculated value",
]


def run_analysis_models(response: CommercialEvaluationResponse) -> AnalysisModelOutputs:
    deal_structure = assess_deal_structure(response)
    npv_readiness = assess_npv_readiness(response, deal_structure)
    landed_value = select_landed_value_or_netback_model(deal_structure)
    scenario_requirements = build_scenario_requirements(response, deal_structure)
    optionality_routing = route_optionality_models(response)
    portfolio_requirements = assess_portfolio_impact_requirements(response)

    warnings = unique(
        deal_structure.warnings
        + npv_readiness.warnings
        + landed_value.warnings
        + scenario_requirements.warnings
        + optionality_routing.warnings
        + portfolio_requirements.warnings
        + ["Stage 7A selects model framework and missing inputs only; it does not calculate quantitative valuation results or investment conclusions."]
    )

    outputs = AnalysisModelOutputs(
        deal_structure=deal_structure,
        npv_readiness=npv_readiness,
        landed_value_or_netback=landed_value,
        scenario_model_requirements=scenario_requirements,
        optionality_model_routing=optionality_routing,
        portfolio_impact_requirements=portfolio_requirements,
        commercial_model_warnings=warnings,
    )
    _guard_no_prohibited_claims(outputs)
    return outputs


def _guard_no_prohibited_claims(outputs: AnalysisModelOutputs) -> None:
    text = outputs.model_dump_json().lower()
    if any(phrase in text for phrase in PROHIBITED_MODEL_CLAIMS):
        outputs.commercial_model_warnings.append(
            "A prohibited valuation-result claim was detected in model outputs; Stage 7A does not calculate valuation results."
        )
