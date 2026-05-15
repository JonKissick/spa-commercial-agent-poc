from app.analysis_models.schemas import DealStructureAssessment, ScenarioModelRequirements
from app.schemas import CommercialEvaluationResponse


def build_scenario_requirements(response: CommercialEvaluationResponse, deal_structure: DealStructureAssessment) -> ScenarioModelRequirements:
    pack = response.valuation_input_pack
    return ScenarioModelRequirements(
        base_case_inputs_required=[
            "Validated contract price formula or manual price input",
            "Validated volume, term, delivery schedule, and currency",
            "Base destination market price / netback reference",
            "Base logistics, terminal, tax/fee, credit, and operational cost assumptions",
            "Discount rate",
        ],
        upside_case_inputs_required=[
            "Higher destination market price or favorable spread case",
            "Improved freight/logistics case",
            "Higher exercisable volume or flexibility utilization where contractually supported",
        ],
        downside_case_inputs_required=[
            "Lower destination market price or adverse spread case",
            "Higher freight/logistics and operational disruption case",
            "Take-or-pay, credit, termination, and penalty exposure assumptions",
        ],
        stress_case_inputs_required=[
            "Severe market dislocation case",
            "Counterparty credit stress",
            "Force majeure, delivery failure, demurrage, or operational constraint case",
            "Liquidity and hedge availability assumptions",
        ],
        key_sensitivities=[
            "destination market price",
            "contract price slope/formula",
            "volume",
            "freight",
            "boil-off",
            "FX",
            "discount rate",
            "term",
            "take-or-pay exposure",
            "destination spread",
            "price volatility",
            "credit risk",
            "termination risk",
        ],
        break_even_candidates=[
            "break-even contract price",
            "break-even freight",
            "break-even destination spread",
            "break-even volume",
            "break-even discount rate",
        ],
        manual_inputs_required_before_calculation=pack.missing_analyst_assumptions
        + ["Manual scenario values for base, upside, downside, and stress cases.", "Manual confirmation of DES/FOB model route."],
        warnings=["Scenario requirements are input specifications only; no scenario economics have been calculated."],
    )
