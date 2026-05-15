from app.analysis_models.schemas import PortfolioImpactRequirements, PortfolioRelevance
from app.schemas import CommercialEvaluationResponse, ValuationImpact


def assess_portfolio_impact_requirements(response: CommercialEvaluationResponse) -> PortfolioImpactRequirements:
    has_portfolio_impact = any(provision.valuation_impact == ValuationImpact.PORTFOLIO for provision in response.provision_register)
    has_optionality = bool(response.optionality_register)
    relevance = PortfolioRelevance.MEDIUM if has_portfolio_impact or has_optionality else PortfolioRelevance.UNCLEAR

    return PortfolioImpactRequirements(
        portfolio_relevance=relevance,
        required_portfolio_inputs=[
            "current long/short exposure",
            "geography exposure",
            "counterparty exposure",
            "tenor exposure",
            "delivery location exposure",
            "operational capacity",
            "liquidity needs",
            "hedge value",
            "concentration limits",
            "risk appetite thresholds",
        ],
        potential_diversification_effects=[
            "Potential diversification can be assessed once existing geography, tenor, and delivery exposure is supplied."
        ],
        potential_concentration_risks=[
            "Counterparty, location, tenor, and commodity concentration require portfolio data before assessment."
        ],
        potential_hedge_value=[
            "Hedge value depends on existing exposures, liquidity, correlation, and hedge instrument availability."
        ],
        liquidity_or_operational_constraints=[
            "Operational capacity, scheduling, storage, terminal, shipping, and liquidity constraints must be supplied manually."
        ],
        warnings=["Portfolio impact is requirements-only in Stage 7A because no portfolio data is supplied."],
    )
