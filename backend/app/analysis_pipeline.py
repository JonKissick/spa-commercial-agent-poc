from app.analysis_models.model_runner import run_analysis_models
from app.config import get_settings
from app.llm_providers.base import LLMProviderConfigurationError, LLMProviderError
from app.llm_providers.factory import create_llm_provider
from app.rag.context_builder import build_analysis_rag_context
from app.rag.schemas import RagContextBundle
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
    OptionType,
    PortfolioFitAssessment,
    ProvisionCategory,
    ProvisionRegisterItem,
    RecommendationValue,
    SuggestedValuationMethod,
    ValuationImpact,
    ValuationInputItem,
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
    rag_context_bundle = _build_optional_rag_context(bounded_text, settings)
    rag_prompt_context = rag_context_bundle.prompt_context if rag_context_bundle and rag_context_bundle.items_used else None

    try:
        provider = create_llm_provider(settings)
        response = provider.analyze_contract(bounded_text, rag_context=rag_prompt_context)
        return _validate_and_attach_rag_summary(response, rag_context_bundle)
    except LLMProviderConfigurationError as exc:
        if settings.llm_provider.strip().lower() == "openai" and not settings.openai_api_key:
            return _validate_and_attach_rag_summary(_build_mock_response(bounded_text), rag_context_bundle)
        raise AnalysisPipelineError("LLM provider is not configured correctly.") from exc
    except LLMProviderError as exc:
        raise AnalysisPipelineError("LLM provider analysis failed or returned an invalid schema.") from exc


def _build_optional_rag_context(contract_text: str, settings) -> RagContextBundle | None:
    if not settings.rag_enabled:
        return None
    return build_analysis_rag_context(
        contract_text,
        analysis_sections=settings.rag_sections,
        top_k=settings.rag_top_k,
    )


def _validate_and_attach_rag_summary(
    response: CommercialEvaluationResponse,
    rag_context_bundle: RagContextBundle | None,
) -> CommercialEvaluationResponse:
    validated = validate_commercial_evaluation(response)
    validated.analysis_model_outputs = run_analysis_models(validated)
    if rag_context_bundle is not None:
        # prompt_context can contain retrieved chunk text; the API response only exposes non-sensitive citations/summary.
        validated.rag_context_summary = rag_context_bundle.model_copy(update={"prompt_context": ""})
    return validate_commercial_evaluation(validated)


def _normalize_contract_text(contract_text: str) -> str:
    cleaned_text = "\n".join(line.strip() for line in contract_text.splitlines() if line.strip())
    if len(cleaned_text) < MIN_USEFUL_CONTRACT_CHARS:
        raise ContractTextValidationError("Extracted contract text is empty or too short for analysis.")
    return cleaned_text


def _build_mock_response(contract_text: str) -> CommercialEvaluationResponse:
    excerpt = contract_text[:280].strip() if contract_text.strip() else None

    clause_coverage = _build_mock_clause_coverage()

    market_context = MarketContextAssessment(
        summary="Market context is not evaluated in Stage 4 without supplied market data. External price curves, liquidity, and spread assumptions are required.",
        required_market_assumptions=[
            "Relevant commodity forward curve.",
            "Regional basis differentials.",
            "Liquidity and deliverability constraints.",
        ],
        evidence_status=EvidenceStatus.MARKET_ASSUMPTION_REQUIRED,
        confidence=Confidence.LOW,
    )
    portfolio_fit = PortfolioFitAssessment(
        summary="Portfolio fit is not evaluated in Stage 4 without supplied portfolio data. Existing book exposure, concentration, and operational capacity must be supplied separately.",
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
        memo="Stage 4 fallback returns a placeholder recommendation only. Proceeding requires validated clause extraction, commercial validation, market assumptions, and portfolio review.",
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
                id="PR-004",
                title="Destination flexibility",
                category=ProvisionCategory.DESTINATION_FLEXIBILITY,
                clause_reference=None,
                extracted_text=None,
                commercial_meaning="Potential destination flexibility is included as a weak illustrative optionality item in fallback mode.",
                valuation_impact=ValuationImpact.OPTIONALITY,
                model_input="Confirm whether the SPA permits diversion, destination nomination, resale, or alternate discharge ports.",
                evidence_status=EvidenceStatus.ANALYST_ASSUMPTION_REQUIRED,
                confidence=Confidence.LOW,
                warnings=["Destination flexibility is weak/unclear in mock fallback mode and must be validated against the contract."],
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
            price_basis=[
                ValuationInputItem(
                    name="Contract price basis",
                    value="Index-linked pricing basis identified in extracted text sample; exact formula requires analyst validation.",
                    source_provision_ids=["PR-001"],
                    evidence_status=EvidenceStatus.INFERRED_FROM_CONTRACT,
                    confidence=Confidence.LOW,
                    analyst_assumption_needed=True,
                    warnings=["Mock fallback does not extract a complete price formula."],
                )
            ],
            pricing_formula=[
                ValuationInputItem(
                    name="Pricing formula",
                    value="Pricing uses an index formula; full index, premium/discount, FX, and escalation mechanics are not extracted in fallback mode.",
                    source_provision_ids=["PR-001"],
                    evidence_status=EvidenceStatus.INFERRED_FROM_CONTRACT,
                    confidence=Confidence.LOW,
                    analyst_assumption_needed=True,
                    warnings=["Formula is incomplete and must be checked against the contract."],
                )
            ],
            volume_obligation=[
                ValuationInputItem(
                    name="Volume obligation",
                    value="Seller shall deliver crude oil volumes; exact quantity is not extracted in fallback mode.",
                    source_provision_ids=["PR-001"],
                    evidence_status=EvidenceStatus.EXTRACTED_FROM_CONTRACT,
                    confidence=Confidence.LOW,
                    analyst_assumption_needed=True,
                    warnings=["Exact ACQ/DCQ/cargo quantity must be confirmed."],
                )
            ],
            volume_flexibility=[
                ValuationInputItem(
                    name="Volume flexibility right",
                    value="Potential volume flexibility flagged as weak/unclear; no firm swing quantity extracted.",
                    source_provision_ids=["PR-002"],
                    evidence_status=EvidenceStatus.ANALYST_ASSUMPTION_REQUIRED,
                    confidence=Confidence.LOW,
                    analyst_assumption_needed=True,
                    warnings=["Source provision is weak/unclear and should not be valued without validation."],
                )
            ],
            credit_support=[
                ValuationInputItem(
                    name="Credit support",
                    value="Credit support requires review; fallback evidence is insufficient.",
                    source_provision_ids=["PR-003"],
                    evidence_status=EvidenceStatus.INSUFFICIENT_EVIDENCE,
                    confidence=Confidence.LOW,
                    analyst_assumption_needed=True,
                    warnings=["Insufficient evidence for credit support terms."],
                )
            ],
            dcf_relevant_inputs=[
                ValuationInputItem(
                    name="DCF input candidates",
                    value=["Price formula", "Volume obligation", "Delivery schedule", "Term"],
                    source_provision_ids=["PR-001"],
                    evidence_status=EvidenceStatus.ANALYST_ASSUMPTION_REQUIRED,
                    confidence=Confidence.LOW,
                    analyst_assumption_needed=True,
                    warnings=["Input candidates only; no DCF has been run."],
                )
            ],
            optionality_relevant_inputs=[
                ValuationInputItem(
                    name="Optionality input candidates",
                    value=["Volume flexibility", "Destination flexibility", "Make-up rights"],
                    source_provision_ids=["PR-002"],
                    evidence_status=EvidenceStatus.ANALYST_ASSUMPTION_REQUIRED,
                    confidence=Confidence.LOW,
                    analyst_assumption_needed=True,
                    warnings=["Input candidates only; no option valuation has been run."],
                )
            ],
            missing_analyst_assumptions=[
                "Confirm exact price formula, index, premium/discount, FX, and escalation mechanics.",
                "Confirm exact annual contract quantity, delivery schedule, term, tolerances, and take-or-pay mechanics.",
                "Confirm whether missing data is absent from the contract or not yet extracted.",
            ],
            missing_market_data=[
                "Forward curve for the relevant commodity and delivery location.",
                "Basis differentials, volatility, liquidity, FX, and inflation assumptions.",
            ],
            missing_portfolio_data=[
                "Current portfolio exposure by tenor and delivery location.",
                "Operational capacity, concentration limits, and counterparty exposure limits.",
            ],
            valuation_warnings=[
                "Stage 4 prepares valuation input candidates only; no NPV, IRR, fair value, option value, expected margin, or trade P&L has been calculated.",
                "Volume clause coverage is not present, so quantity inputs require analyst validation.",
            ],
            evidence_status=EvidenceStatus.ANALYST_ASSUMPTION_REQUIRED,
        ),
        optionality_register=[
            OptionalityRegisterItem(
                id="OP-001",
                option_name="Destination flexibility",
                option_type=OptionType.DESTINATION_FLEX,
                source_category=ProvisionCategory.DESTINATION_FLEXIBILITY,
                source_provision_ids=["PR-004"],
                source_clause_reference=None,
                extracted_right=None,
                commercial_description="Potential right to redirect or nominate destination is weak/unclear in fallback mode.",
                economic_value_logic="If contractually valid, destination flexibility could allow spread capture across markets or assets; no value is calculated.",
                suggested_valuation_method=SuggestedValuationMethod.SPREAD_OPTION,
                required_market_data=["Destination market spreads, freight, liquidity, and forward curves."],
                required_operational_data=["Vessel, port, scheduling, diversion, and deliverability constraints."],
                required_portfolio_data=["Portfolio demand, supply commitments, and capacity by destination."],
                required_analyst_assumptions=["Confirm diversion, resale, and destination nomination rights in the SPA."],
                key_value_drivers=["Market spread", "Diversion notice period", "Operational feasibility"],
                key_risks_or_constraints=["Destination right is weak/unclear in mock fallback mode."],
                valuation_impact=ValuationImpact.OPTIONALITY,
                evidence_status=EvidenceStatus.ANALYST_ASSUMPTION_REQUIRED,
                confidence=Confidence.LOW,
                warnings=["Weak evidence only; do not value destination flexibility without contract validation."],
                analyst_validation_needed=True,
            ),
            OptionalityRegisterItem(
                id="OP-002",
                option_name="Volume flexibility",
                option_type=OptionType.VOLUME_FLEX,
                source_category=ProvisionCategory.VOLUME_FLEXIBILITY,
                source_provision_ids=["PR-002"],
                source_clause_reference=None,
                extracted_right=None,
                commercial_description="Potential value from adjusting nominations within contractual bands.",
                economic_value_logic="If confirmed, volume flexibility may support swing-style scenario analysis; no quantitative result is calculated.",
                suggested_valuation_method=SuggestedValuationMethod.SWING_OPTION,
                required_market_data=["Price curves, volatility, liquidity, and downside/upside scenarios."],
                required_operational_data=["Nomination deadlines, min/max quantities, deliverability, and storage/logistics constraints."],
                required_portfolio_data=["Portfolio imbalance, demand flexibility, and concentration constraints."],
                required_analyst_assumptions=["Quantify flexibility bands and operational constraints."],
                key_value_drivers=["Quantity band", "Exercise frequency", "Market volatility", "Operational constraints"],
                key_risks_or_constraints=["Source provision is weak/unclear in mock fallback mode."],
                valuation_impact=ValuationImpact.OPTIONALITY,
                evidence_status=EvidenceStatus.ANALYST_ASSUMPTION_REQUIRED,
                confidence=Confidence.LOW,
                warnings=["Weak evidence only; do not value volume flexibility without contract validation."],
                analyst_validation_needed=True,
            ),
            OptionalityRegisterItem(
                id="OP-003",
                option_name="Unconfirmed make-up or carry-forward rights",
                option_type=OptionType.MAKE_UP,
                source_category=ProvisionCategory.MAKE_UP,
                source_provision_ids=[],
                source_clause_reference=None,
                extracted_right=None,
                commercial_description="Make-up or carry-forward optionality was not identified in the extracted text.",
                economic_value_logic="Could matter if present, but there is insufficient evidence to treat it as a contractual option.",
                suggested_valuation_method=SuggestedValuationMethod.INSUFFICIENT_EVIDENCE,
                required_market_data=["Market scenarios would be required only if the right is confirmed."],
                required_operational_data=["Future delivery feasibility would be required only if the right is confirmed."],
                required_portfolio_data=["Portfolio need for deferred quantities would be required only if the right is confirmed."],
                required_analyst_assumptions=["Confirm whether make-up or carry-forward rights exist."],
                key_value_drivers=[],
                key_risks_or_constraints=["No supporting clause was identified in fallback mode."],
                valuation_impact=ValuationImpact.UNCLEAR,
                evidence_status=EvidenceStatus.INSUFFICIENT_EVIDENCE,
                confidence=Confidence.LOW,
                warnings=["Insufficient evidence; this optionality item is a placeholder for analyst validation, not a claimed right."],
                analyst_validation_needed=True,
            ),
        ],
        market_context_assessment=market_context,
        portfolio_fit_assessment=portfolio_fit,
        deal_recommendation=recommendation,
        limitations=[
            "No full valuation calculation, DCF model, or quantitative option valuation has been performed in this Stage 4 analysis.",
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
        elif category == ProvisionCategory.DESTINATION_FLEXIBILITY:
            coverage.append(
                ClauseCoverageItem(
                    category=category,
                    label=label,
                    status=CoverageStatus.WEAK_UNCLEAR,
                    evidence_summary="Destination flexibility is included as a weak illustrative optionality extraction in mock fallback mode; analyst confirmation is required.",
                    provision_ids=["PR-004"],
                    warnings=["Evidence is partial or indirect in mock fallback mode."],
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
