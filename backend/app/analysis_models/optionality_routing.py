from app.analysis_models.schemas import NpvReadiness, OptionalityModelRoutingAssessment, RoutedOption
from app.analysis_models.utils import unique
from app.schemas import CommercialEvaluationResponse

OPTION_MODEL_MAP = {
    "destination_flex": "spread_option",
    "volume_flex": "swing_option",
    "timing_flex": "scenario_analysis",
    "price_reopener": "scenario_analysis",
    "make_up": "make_up_value",
    "carry_forward": "make_up_value",
    "take_or_pay_downside": "downside_scenario_analysis",
    "termination": "termination_downside_protection",
    "credit_support": "credit_risk_adjustment",
    "operational_flex": "operational_constraint_analysis",
    "other": "analyst_judgement_required",
}


def route_optionality_models(response: CommercialEvaluationResponse) -> OptionalityModelRoutingAssessment:
    routed: list[RoutedOption] = []
    required_market: list[str] = []
    required_operational: list[str] = []
    required_portfolio: list[str] = []
    not_ready: list[str] = []
    warnings: list[str] = []

    for item in response.optionality_register:
        option_type = item.option_type.value
        suggested_model = OPTION_MODEL_MAP.get(option_type, "analyst_judgement_required")
        missing = unique(item.required_market_data + item.required_operational_data + item.required_portfolio_data + item.required_analyst_assumptions)
        readiness = NpvReadiness.PARTIAL if item.source_provision_ids and item.confidence.value != "low" else NpvReadiness.NOT_READY
        if missing:
            not_ready.append(f"{item.id}: requires market, operational, portfolio, and analyst inputs before modelling.")
        routed.append(
            RoutedOption(
                option_type=option_type,
                source_optionality_ids=[item.id],
                suggested_model=suggested_model,
                readiness=readiness,
                missing_inputs=missing,
                warnings=item.warnings + ["No quantitative option valuation is performed in Stage 7A."],
            )
        )
        required_market.extend(item.required_market_data)
        required_operational.extend(item.required_operational_data)
        required_portfolio.extend(item.required_portfolio_data)
        warnings.extend(item.warnings)

    if not routed:
        warnings.append("No optionality items were available for future model routing.")

    return OptionalityModelRoutingAssessment(
        routed_options=routed,
        recommended_future_models=unique([item.suggested_model for item in routed]),
        required_market_data=unique(required_market),
        required_operational_data=unique(required_operational),
        required_portfolio_data=unique(required_portfolio),
        not_ready_reasons=unique(not_ready),
        warnings=unique(warnings + ["Optionality routing identifies future methods only; no option valuation has been performed."]),
    )
