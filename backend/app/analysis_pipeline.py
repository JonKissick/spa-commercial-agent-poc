from app.ai_client import AIClient, MissingAPIKeyError
from app.config import get_settings
from app.schemas import (
    ClauseCoverageItem,
    CommercialEvaluationResponse,
    Confidence,
    CoverageStatus,
    ContractSummary,
    DealRecommendation,
    EvidenceNote,
    EvidenceStatus,
    MarketContextAssessment,
    OptionalityRegisterItem,
    PortfolioFitAssessment,
    ProvisionCategory,
    ProvisionRegisterItem,
    RecommendationValue,
    ValuationImpact,
    ValuationInputPack,
)
from app.taxonomy import SPA_TAXONOMY, taxonomy_categories
from app.validation import validate_commercial_evaluation

MIN_USEFUL_CONTRACT_CHARS = 40


class ContractTextValidationError(ValueError):
    pass


class AnalysisPipelineError(RuntimeError):
    pass


def run_analysis_pipeline(contract_text: str) -> CommercialEvaluationResponse:
    cleaned_text = _normalize_contract_text(contract_text)
    settings = get_settings()
    bounded_text = cleaned_text[: settings.max_contract_chars]

    if settings.openai_api_key:
        try:
            response = AIClient(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
            ).analyze_contract_text(bounded_text)
            return validate_commercial_evaluation(response)
        except MissingAPIKeyError:
            pass
        except Exception as exc:
            raise AnalysisPipelineError("OpenAI structured analysis failed or returned an invalid schema.") from exc

    return validate_commercial_evaluation(_build_mock_response(bounded_text))


def _normalize_contract_text(contract_text: str) -> str:
    cleaned_text = "\n".join(line.strip() for line in contract_text.splitlines() if line.strip())
    if len(cleaned_text) < MIN_USEFUL_CONTRACT_CHARS:
        raise ContractTextValidationError("Extracted contract text is empty or too short for analysis.")
    return cleaned_text


def _build_mock_response(contract_text: str) -> CommercialEvaluationResponse:
    excerpt = contract_text[:280].strip() if contract_text.strip() else None

    clause_coverage = _build_mock_clause_coverage()

    market_context = MarketContextAssessment(
        summary="Market context is not evaluated in Stage 2 without supplied market data. External price curves, liquidity, and spread assumptions are required.",
        required_market_assumptions=[
            "Relevant commodity forward curve.",
            "Regional basis differentials.",
            "Liquidity and deliverability constraints.",
        ],
        evidence_status=EvidenceStatus.MARKET_ASSUMPTION_REQUIRED,
        confidence=Confidence.LOW,
    )
    portfolio_fit = PortfolioFitAssessment(
        summary="Portfolio fit is not evaluated in Stage 2 without supplied portfolio data. Existing book exposure, concentration, and operational capacity must be supplied separately.",
        required_portfolio_assumptions=[
            "Current portfolio exposure by tenor and location.",
            "Operational capacity and delivery constraints.",
            "Counterparty concentration limits.",
        ],
        evidence_status=EvidenceStatus.PORTFOLIO_ASSUMPTION_REQUIRED,
        confidence=Confidence.LOW,
    )
    recommendation = DealRecommendation(
        recommendation=RecommendationValue.INSUFFICIENT_EVIDENCE,
        memo="Stage 2 fallback returns a placeholder recommendation only. Proceeding requires validated clause extraction, commercial validation, market assumptions, and portfolio review.",
        key_conditions=[
            "Complete validated clause extraction.",
            "Confirm valuation model inputs.",
            "Review optionality, credit, and termination provisions.",
        ],
        key_risks=[
            "Mock analysis may omit material provisions.",
            "No valuation engine or market data integration has been applied.",
        ],
        confidence=Confidence.LOW,
        evidence_status=EvidenceStatus.INSUFFICIENT_EVIDENCE,
    )

    return CommercialEvaluationResponse(
        contract_summary=ContractSummary(
            seller=None,
            buyer=None,
            commodity=None,
            contract_term=None,
            governing_law=None,
            summary="Mock summary generated from uploaded PDF text. Party, term, commodity, and governing law extraction are placeholders when OPENAI_API_KEY is not configured.",
            evidence=[
                EvidenceNote(
                    status=EvidenceStatus.EXTRACTED_FROM_CONTRACT,
                    note="PDF text was extracted and passed into the placeholder pipeline.",
                    source_excerpt=excerpt,
                ),
                EvidenceNote(
                    status=EvidenceStatus.ANALYST_ASSUMPTION_REQUIRED,
                    note="Analyst review is required before relying on any commercial interpretation.",
                ),
            ],
        ),
        clause_coverage=clause_coverage,
        provision_register=[
            ProvisionRegisterItem(
                id="PR-001",
                title="Pricing terms",
                category=ProvisionCategory.PRICING,
                clause_reference=None,
                extracted_text=excerpt,
                commercial_meaning="Pricing terms appear commercially material, but detailed extraction requires real OpenAI analysis or analyst review.",
                valuation_impact=ValuationImpact.DCF,
                model_input="Confirm price formula, index linkage, escalation mechanics, and any review dates.",
                evidence_status=EvidenceStatus.INFERRED_FROM_CONTRACT,
                confidence=Confidence.LOW,
                warnings=["Low confidence mock extraction; validate pricing clause references before commercial reliance."],
                analyst_validation_needed=True,
            ),
            ProvisionRegisterItem(
                id="PR-002",
                title="Volume flexibility",
                category=ProvisionCategory.VOLUME_FLEXIBILITY,
                clause_reference=None,
                extracted_text=None,
                commercial_meaning="Volume flexibility may affect downside protection and upside participation.",
                valuation_impact=ValuationImpact.OPTIONALITY,
                model_input="Identify minimum, maximum, make-up, carry-forward, and nomination rights.",
                evidence_status=EvidenceStatus.ANALYST_ASSUMPTION_REQUIRED,
                confidence=Confidence.LOW,
                warnings=["Volume flexibility evidence is weak or indirect in mock fallback mode."],
                analyst_validation_needed=True,
            ),
            ProvisionRegisterItem(
                id="PR-003",
                title="Credit support",
                category=ProvisionCategory.CREDIT,
                clause_reference=None,
                extracted_text=None,
                commercial_meaning="Counterparty credit support should be checked before commercial approval.",
                valuation_impact=ValuationImpact.RISK_ADJUSTMENT,
                model_input="Confirm parent guarantees, letters of credit, collateral, and payment security.",
                evidence_status=EvidenceStatus.INSUFFICIENT_EVIDENCE,
                confidence=Confidence.LOW,
                warnings=["Insufficient contract evidence supports the credit support conclusion in mock fallback mode."],
                analyst_validation_needed=True,
            ),
        ],
        valuation_input_pack=ValuationInputPack(
            pricing_inputs=[
                "Contract price formula or fixed price schedule.",
                "Index, FX, inflation, and escalation assumptions.",
            ],
            volume_inputs=[
                "Annual contract quantity.",
                "Minimum take, maximum take, and tolerance bands.",
            ],
            timing_inputs=["Start date, end date, delivery schedule, and review windows."],
            risk_inputs=["Credit support, termination triggers, force majeure scope, and penalties."],
            required_analyst_assumptions=[
                "Map extracted clauses to financial model inputs.",
                "Confirm whether missing data is absent from the contract or not yet extracted.",
            ],
            evidence_status=EvidenceStatus.ANALYST_ASSUMPTION_REQUIRED,
        ),
        optionality_register=[
            OptionalityRegisterItem(
                id="OP-001",
                option_name="Destination flexibility",
                commercial_description="Potential value from redirecting deliveries across markets or assets.",
                valuation_impact=ValuationImpact.OPTIONALITY,
                evidence_status=EvidenceStatus.MARKET_ASSUMPTION_REQUIRED,
                confidence=Confidence.LOW,
                assumption_required="Assess destination rights, diversion constraints, and market spread scenarios.",
            ),
            OptionalityRegisterItem(
                id="OP-002",
                option_name="Volume flexibility",
                commercial_description="Potential value from adjusting nominations within contractual bands.",
                valuation_impact=ValuationImpact.OPTIONALITY,
                evidence_status=EvidenceStatus.ANALYST_ASSUMPTION_REQUIRED,
                confidence=Confidence.LOW,
                assumption_required="Quantify flexibility bands and operational constraints.",
            ),
        ],
        market_context_assessment=market_context,
        portfolio_fit_assessment=portfolio_fit,
        deal_recommendation=recommendation,
        limitations=[
            "No full valuation calculation, DCF model, or quantitative option valuation has been performed in this Stage 2 analysis.",
            "Market and portfolio conclusions require manual assumptions unless those assumptions are explicitly supplied in the uploaded document.",
        ],
    )


def _build_mock_clause_coverage() -> list[ClauseCoverageItem]:
    coverage: list[ClauseCoverageItem] = []
    for category in taxonomy_categories():
        taxonomy_item = SPA_TAXONOMY[category]
        label = str(taxonomy_item["label"])
        if category == ProvisionCategory.PRICING:
            coverage.append(
                ClauseCoverageItem(
                    category=category,
                    label=label,
                    status=CoverageStatus.PRESENT,
                    evidence_summary="Pricing language is present in the extracted text sample and is mapped to PR-001.",
                    provision_ids=["PR-001"],
                    warnings=[],
                )
            )
        elif category == ProvisionCategory.VOLUME_FLEXIBILITY:
            coverage.append(
                ClauseCoverageItem(
                    category=category,
                    label=label,
                    status=CoverageStatus.WEAK_UNCLEAR,
                    evidence_summary="Volume flexibility is included as a weak illustrative extraction in mock fallback mode; analyst confirmation is required.",
                    provision_ids=["PR-002"],
                    warnings=["Evidence is partial or indirect in mock fallback mode."],
                )
            )
        elif category == ProvisionCategory.CREDIT:
            coverage.append(
                ClauseCoverageItem(
                    category=category,
                    label=label,
                    status=CoverageStatus.WEAK_UNCLEAR,
                    evidence_summary="Credit support is flagged for review, but the mock fallback does not establish a definitive credit support clause.",
                    provision_ids=["PR-003"],
                    warnings=["Insufficient evidence means credit support must be validated against the contract."],
                )
            )
        else:
            coverage.append(
                ClauseCoverageItem(
                    category=category,
                    label=label,
                    status=CoverageStatus.NOT_IDENTIFIED,
                    evidence_summary="No supporting clause was identified in the extracted contract text.",
                    provision_ids=[],
                    warnings=[],
                )
            )
    return coverage
