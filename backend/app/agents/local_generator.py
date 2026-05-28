from app.agents.schemas import (
    BoardPaperDraftRequest,
    BoardPaperDraftResponse,
    ManagementSlidePackRequest,
    ManagementSlidePackResponse,
    SlideDraft,
)


def draft_board_paper(request: BoardPaperDraftRequest) -> BoardPaperDraftResponse:
    analysis = request.analysis
    npv = request.npv
    recommendation = analysis.deal_recommendation
    title = _contract_title(analysis.contract_summary.summary, "SPA Commercial Valuation Board Paper")

    valuation_summary = [
        f"Recommendation: {recommendation.recommendation.value}.",
        f"Portfolio fit: {analysis.portfolio_fit_assessment.summary}",
        f"Market context: {analysis.market_context_assessment.summary}",
    ]
    if npv and npv.scenario_results:
        valuation_summary.extend(
            f"{result.scenario_name.value} NPV: {npv.currency} {result.npv:,.2f} using {result.formula_used}."
            for result in npv.scenario_results
        )
    else:
        valuation_summary.append("No scenario NPV result was supplied to the board-paper agent.")

    human_review_required = _human_review_items(analysis)
    citations = _analysis_citations(analysis)
    return BoardPaperDraftResponse(
        title=title,
        executive_summary=(
            "Draft board paper generated from structured SPA analysis outputs, local RAG metadata, "
            "and optional deterministic NPV results. It is not legal, financial, or investment advice."
        ),
        recommendation=recommendation.memo,
        valuation_summary=valuation_summary,
        commercial_risks=_dedupe(recommendation.key_risks + analysis.valuation_input_pack.valuation_warnings),
        key_conditions=recommendation.key_conditions,
        human_review_required=human_review_required,
        citations=citations,
        limitations=[
            "Mock Bedrock/RAG scaffold only; no external Bedrock call is made.",
            "RAG citations are methodology context only and are not evidence that a contract clause exists.",
            "Draft requires human commercial, legal, and valuation review before reliance.",
        ],
    )


def draft_management_slide_pack(request: ManagementSlidePackRequest) -> ManagementSlidePackResponse:
    analysis = request.analysis
    npv = request.npv
    citations = _analysis_citations(analysis)
    npv_bullets = _npv_bullets(npv)

    slides = [
        SlideDraft(
            slide_number=1,
            title="Deal Snapshot",
            headline=analysis.contract_summary.summary,
            bullets=[
                f"Recommendation: {analysis.deal_recommendation.recommendation.value}",
                f"Confidence: {analysis.deal_recommendation.confidence.value}",
                "Draft output; analyst validation required before reliance.",
            ],
            speaker_notes="Open with the structured SPA summary and confirm this is a controlled local POC draft.",
            citations=citations[:3],
        ),
        SlideDraft(
            slide_number=2,
            title="Valuation Inputs",
            headline="DCF-ready fields are identified, but missing assumptions remain.",
            bullets=_dedupe(
                analysis.valuation_input_pack.pricing_inputs
                + analysis.valuation_input_pack.volume_inputs
                + analysis.valuation_input_pack.required_analyst_assumptions
            )[:6],
            speaker_notes="Use this slide to assign missing market, volume, timing, and pricing assumptions.",
            citations=citations,
        ),
        SlideDraft(
            slide_number=3,
            title="Scenario Economics",
            headline="Manual scenario NPV outputs are available when supplied.",
            bullets=npv_bullets,
            speaker_notes="These figures come from the deterministic calculator, not from an LLM or live market data.",
            citations=[],
        ),
        SlideDraft(
            slide_number=4,
            title="Optionality and Portfolio Fit",
            headline="Optionality is routed for modelling, not quantitatively valued.",
            bullets=_optionality_bullets(analysis),
            speaker_notes="Discuss which rights need spread, swing, or analyst-judgement modelling after clause validation.",
            citations=citations,
        ),
        SlideDraft(
            slide_number=5,
            title="Decision Path",
            headline=analysis.deal_recommendation.memo,
            bullets=_dedupe(analysis.deal_recommendation.key_conditions + analysis.deal_recommendation.key_risks),
            speaker_notes="Close with conditions, gaps, and human review actions required before commercial sign-off.",
            citations=citations,
        ),
    ]
    return ManagementSlidePackResponse(
        title="SPA Commercial Management Pack",
        slides=slides,
        human_review_required=_human_review_items(analysis),
        limitations=[
            "Exactly five draft slides are generated for local review.",
            "Mock Bedrock/RAG scaffold only; no external Bedrock call is made.",
            "Draft requires human review and formatting before management use.",
        ],
    )


def _contract_title(summary: str, fallback: str) -> str:
    if not summary:
        return fallback
    return fallback


def _npv_bullets(npv) -> list[str]:
    if not npv or not npv.scenario_results:
        return ["No NPV response was supplied.", "Run the manual NPV calculator before using this slide for economics."]
    return [
        f"{result.scenario_name.value}: NPV {npv.currency} {result.npv:,.2f}; annual unit margin {result.annual_unit_margin:,.4f} {npv.currency}/{npv.unit}."
        for result in npv.scenario_results
    ]


def _optionality_bullets(analysis) -> list[str]:
    bullets = [
        f"{item.option_name}: {item.suggested_valuation_method.value}; confidence {item.confidence.value}."
        for item in analysis.optionality_register
    ]
    bullets.extend(analysis.portfolio_fit_assessment.required_portfolio_assumptions)
    return _dedupe(bullets)[:6]


def _human_review_items(analysis) -> list[str]:
    review_items = [
        "Validate all extracted clause references against the source SPA.",
        "Confirm all market, portfolio, credit, and operational assumptions.",
        "Review legal interpretation separately before any commercial reliance.",
    ]
    review_items.extend(analysis.valuation_input_pack.missing_analyst_assumptions)
    review_items.extend(analysis.valuation_input_pack.missing_market_data)
    review_items.extend(analysis.valuation_input_pack.missing_portfolio_data)
    return _dedupe(review_items)


def _analysis_citations(analysis) -> list[str]:
    citations = [f"provision:{item.id}:{item.category.value}" for item in analysis.provision_register]
    if analysis.rag_context_summary:
        citations.extend(f"rag:{item.title}:{item.knowledge_type}" for item in analysis.rag_context_summary.items_used)
    return _dedupe(citations)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item and item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped
