from app.analysis_models.schemas import DealStructureAssessment, DeliveryBasis, NpvReadiness, NpvReadinessAssessment
from app.analysis_models.utils import unique
from app.schemas import CommercialEvaluationResponse

BASE_REQUIRED_INPUTS = [
    "contract role",
    "delivery basis",
    "price basis or formula",
    "volume or quantity",
    "term or delivery schedule",
    "discount rate",
    "market reference price or destination value",
    "currency and FX assumptions where relevant",
]


def assess_npv_readiness(response: CommercialEvaluationResponse, deal_structure: DealStructureAssessment) -> NpvReadinessAssessment:
    available = _available_contract_inputs(response, deal_structure)
    required = list(BASE_REQUIRED_INPUTS)
    logistics = _logistics_requirements(deal_structure.delivery_basis)
    missing = [item for item in required if item not in available]

    if deal_structure.delivery_basis == DeliveryBasis.UNCLEAR and "delivery basis" not in missing:
        missing.append("delivery basis")
    if deal_structure.contract_role.value == "unclear" and "contract role" not in missing:
        missing.append("contract role")

    critical_missing = missing + logistics
    readiness = NpvReadiness.PARTIAL if len(available) >= 3 else NpvReadiness.NOT_READY
    if critical_missing:
        readiness = NpvReadiness.PARTIAL if available else NpvReadiness.NOT_READY

    warnings = ["No NPV has been calculated; this is a readiness assessment only."]
    if critical_missing:
        warnings.append("Critical valuation inputs are missing or require manual assumptions before calculation.")

    return NpvReadinessAssessment(
        readiness=readiness,
        required_contract_inputs=required,
        available_contract_inputs=available,
        missing_contract_inputs=unique(missing),
        required_manual_assumptions=[
            "Discount rate / WACC or hurdle rate.",
            "Manual confirmation of extracted pricing, volume, term, delivery, and cost inputs.",
            "Scenario assumptions for base, upside, downside, and stress cases.",
        ],
        required_market_data=[
            "Relevant destination market price or netback reference.",
            "Forward curves, basis spreads, liquidity, volatility, inflation, and FX where relevant.",
        ],
        required_logistics_data=unique(logistics),
        required_portfolio_data=[
            "Current portfolio long/short exposure by geography, tenor, counterparty, and delivery location.",
            "Operational capacity and concentration limits.",
        ],
        can_calculate_npv_now=False,
        reason_not_ready="NPV cannot be calculated in Stage 7A because required market, logistics, portfolio, discount-rate, and manually validated contract inputs are not all supplied.",
        source_sections=["contract_summary", "clause_coverage", "provision_register", "valuation_input_pack", "analysis_model_outputs.deal_structure"],
        warnings=unique(warnings),
    )


def _available_contract_inputs(response: CommercialEvaluationResponse, deal_structure: DealStructureAssessment) -> list[str]:
    pack = response.valuation_input_pack
    available: list[str] = []
    if deal_structure.contract_role.value != "unclear":
        available.append("contract role")
    if deal_structure.delivery_basis.value != "unclear":
        available.append("delivery basis")
    if pack.price_basis or pack.pricing_formula or pack.price_index:
        available.append("price basis or formula")
    if pack.volume_obligation or pack.volume_range or pack.annual_contract_quantity:
        available.append("volume or quantity")
    if pack.duration or pack.start_date or pack.end_date:
        available.append("term or delivery schedule")
    if pack.currency:
        available.append("currency and FX assumptions where relevant")
    return unique(available)


def _logistics_requirements(delivery_basis: DeliveryBasis) -> list[str]:
    if delivery_basis in {DeliveryBasis.FOB, DeliveryBasis.FREE_ON_BOARD}:
        return [
            "origin/loading port",
            "destination/discharge market or terminal",
            "freight",
            "boil-off",
            "shipping duration",
            "port/canal costs",
            "regas/terminal costs if relevant",
        ]
    if delivery_basis in {DeliveryBasis.DES, DeliveryBasis.EX_SHIP, DeliveryBasis.DELIVERED}:
        return [
            "destination/discharge point",
            "regas/terminal/downstream costs if buyer-side",
            "confirmation whether shipping is included in contract price",
            "demurrage and operational cost exposure if relevant",
        ]
    return [
        "confirmed DES/FOB/delivered basis",
        "origin/loading point",
        "destination/discharge point",
        "freight, boil-off, port/canal, terminal, and downstream cost assumptions as applicable",
    ]
