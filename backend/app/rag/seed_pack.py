from pydantic import BaseModel, Field

from app.config import get_settings
from app.rag.factory import create_rag_index
from app.rag.ingestion import ingest_knowledge_text
from app.rag.schemas import IngestionResult, KnowledgeDocumentMetadata


class SeedKnowledgeEntry(BaseModel):
    text: str
    metadata: KnowledgeDocumentMetadata


class SeedPackResult(BaseModel):
    entries_attempted: int
    entries_ingested: int
    duplicates_skipped: int
    warnings: list[str] = Field(default_factory=list)
    ingested: list[IngestionResult] = Field(default_factory=list)
    skipped_titles: list[str] = Field(default_factory=list)


BASE_METADATA = {
    "approval_status": "approved",
    "approved_for_rag": True,
    "owner": "commercial",
    "confidentiality": "internal",
    "commodity": "lng",
    "contract_type": "spa",
    "deal_type": "term",
    "version": "v1",
}


def _metadata(**overrides: object) -> KnowledgeDocumentMetadata:
    data = dict(BASE_METADATA)
    data.update(overrides)
    return KnowledgeDocumentMetadata(**data)


SEED_KNOWLEDGE_ENTRIES: list[SeedKnowledgeEntry] = [
    SeedKnowledgeEntry(
        text=(
            "Pricing mapping rule: identify the contract price index, slope, constant or premium, currency, averaging period, "
            "review dates, caps, floors, and escalation mechanics where explicitly supported by contract text. Map supported terms to "
            "DCF price input candidates. Missing formula components must be analyst assumptions. Do not claim final valuation, fair value, "
            "NPV, IRR, or margin from extraction alone."
        ),
        metadata=_metadata(
            title="LNG SPA Pricing Mapping Rule",
            knowledge_type="model_input_mapping_rule",
            analysis_section="pricing",
            quality_label="good",
            tags=["pricing", "index", "slope", "dcf", "model-inputs"],
        ),
    ),
    SeedKnowledgeEntry(
        text=(
            "DES vs FOB modelling rule: DES buyer logic compares destination market value against DES contract price and buyer-side "
            "terminal/downstream costs. FOB buyer logic compares destination value against FOB price plus freight, boil-off, port/canal, "
            "regas/terminal, and other logistics costs. DES seller logic compares DES price against supply and delivery costs. FOB seller "
            "logic compares FOB price against supply and loading costs. Treat origin, destination, title/risk transfer, and logistics "
            "responsibility as core modelling inputs."
        ),
        metadata=_metadata(
            title="DES FOB Commercial Modelling Rule",
            knowledge_type="valuation_methodology",
            analysis_section="valuation_input_pack",
            quality_label="good",
            tags=["des", "fob", "landed-value", "netback", "logistics"],
        ),
    ),
    SeedKnowledgeEntry(
        text=(
            "Volume and take-or-pay rule: identify ACQ, DCQ, cargo quantity, minimum take, take-or-pay percentage or quantity, deficiency "
            "payments, make-up rights, carry-forward rights, nomination windows, and tolerance bands. Map ACQ/DCQ to volume inputs, TOP "
            "to downside exposure, and make-up/carry-forward to optionality inputs. Unclear quantity language requires analyst validation."
        ),
        metadata=_metadata(
            title="Volume ACQ DCQ Take-or-Pay Mapping Rule",
            knowledge_type="model_input_mapping_rule",
            analysis_section="volume",
            quality_label="good",
            tags=["volume", "acq", "dcq", "take-or-pay", "make-up"],
        ),
    ),
    SeedKnowledgeEntry(
        text=(
            "Destination flexibility rule: identify diversion rights, destination restrictions, resale rights, destination nomination rights, "
            "alternate discharge ports, diversion notice periods, and consent requirements. Supported flexibility may route to spread option "
            "or scenario analysis. Required data includes destination price spreads, freight, port access, vessel constraints, scheduling, "
            "and portfolio demand. Do not infer destination flexibility merely because it is common in LNG SPAs."
        ),
        metadata=_metadata(
            title="Destination Flexibility Analysis Rule",
            knowledge_type="valuation_methodology",
            analysis_section="optionality",
            quality_label="good",
            tags=["destination-flexibility", "spread-option", "diversion", "resale"],
        ),
    ),
    SeedKnowledgeEntry(
        text=(
            "Make-up and carry-forward rule: identify rights to recover paid-for but untaken quantities, carry-forward of surplus or shortfall, "
            "expiry, priority, notice, scheduling, and deliverability constraints. Route confirmed rights to make-up value or scenario analysis. "
            "Required assumptions include timing, market spread at recovery date, operational feasibility, and whether rights survive termination."
        ),
        metadata=_metadata(
            title="Make-up Carry-forward Rights Rule",
            knowledge_type="valuation_methodology",
            analysis_section="optionality",
            quality_label="good",
            tags=["make-up", "carry-forward", "optionality", "take-or-pay"],
        ),
    ),
    SeedKnowledgeEntry(
        text=(
            "Price review and reopener rule: identify review trigger, review timing, benchmark basket, market change threshold, negotiation period, "
            "expert determination, arbitration or dispute mechanism, and whether revised price applies prospectively or retroactively. Route to "
            "scenario analysis and renegotiation risk. Do not assume a price reopener exists without text support."
        ),
        metadata=_metadata(
            title="Price Review Reopener Analysis Rule",
            knowledge_type="taxonomy_guidance",
            analysis_section="pricing",
            quality_label="good",
            tags=["price-review", "reopener", "renegotiation", "pricing"],
        ),
    ),
    SeedKnowledgeEntry(
        text=(
            "Credit support rule: identify parent guarantees, letters of credit, collateral, payment security, payment timing, cure rights, "
            "credit rating triggers, suspension rights, and termination rights for non-payment. Map to credit risk adjustment, downside risk, "
            "and conditions precedent. Missing counterparty credit data remains an external assumption."
        ),
        metadata=_metadata(
            title="Credit Support Payment Risk Rule",
            knowledge_type="risk_policy",
            analysis_section="risk",
            quality_label="good",
            tags=["credit", "letter-of-credit", "guarantee", "payment-risk"],
        ),
    ),
    SeedKnowledgeEntry(
        text=(
            "Force majeure and interruption rule: identify qualifying events, exclusions, notice requirements, mitigation duties, suspension of "
            "delivery/payment, prolonged force majeure termination rights, and allocation of interruption risk. Map to downside scenarios, supply "
            "interruption risk, operational constraints, and termination conditions."
        ),
        metadata=_metadata(
            title="Force Majeure Interruption Risk Rule",
            knowledge_type="risk_policy",
            analysis_section="risk",
            quality_label="good",
            tags=["force-majeure", "interruption", "termination", "downside"],
        ),
    ),
    SeedKnowledgeEntry(
        text=(
            "Portfolio fit rule: request current long/short exposure, geography exposure, counterparty exposure, tenor exposure, delivery location "
            "exposure, operational capacity, liquidity needs, hedge value, concentration limits, and risk appetite thresholds. Do not claim "
            "portfolio fit without supplied portfolio data."
        ),
        metadata=_metadata(
            title="Portfolio Fit Assessment Rule",
            knowledge_type="portfolio_strategy",
            analysis_section="portfolio",
            quality_label="good",
            tags=["portfolio", "exposure", "concentration", "hedge", "capacity"],
        ),
    ),
    SeedKnowledgeEntry(
        text=(
            "Trader-ready recommendation checklist: summarize value drivers, risk drivers, key sensitivities, missing information, negotiation "
            "points, required analyst validation, and go/no-go conditions. Separate extracted contract evidence from inferred implications and "
            "external assumptions. Do not issue a final investment recommendation when evidence or model inputs are incomplete."
        ),
        metadata=_metadata(
            title="Trader-ready Recommendation Checklist",
            knowledge_type="negotiation_playbook",
            analysis_section="recommendation",
            quality_label="good",
            tags=["recommendation", "trader", "checklist", "negotiation"],
        ),
    ),
    SeedKnowledgeEntry(
        text=(
            "Good analysis example: The SPA contains an FOB delivery clause at the loading port and buyer-arranged shipping. This supports FOB "
            "purchase model routing. Pricing formula and ACQ are partially extracted, but freight, boil-off, destination market value, terminal "
            "costs, and discount rate remain manual assumptions. No NPV has been calculated."
        ),
        metadata=_metadata(
            title="Good Evidence-constrained Analysis Example",
            knowledge_type="good_analysis_example",
            analysis_section="recommendation",
            quality_label="good",
            tags=["good-example", "evidence", "fob", "npv-readiness"],
        ),
    ),
    SeedKnowledgeEntry(
        text=(
            "Bad analysis example: This contract is clearly worth 50 million dollars of NPV because LNG SPAs usually include destination "
            "flexibility and make-up rights. Proceed immediately. Problems: invents clauses, claims unsupported NPV, ignores missing market and "
            "portfolio data, and gives a final recommendation without evidence. Use only for critique."
        ),
        metadata=_metadata(
            title="Bad Unsupported Valuation Claim Example",
            knowledge_type="bad_analysis_example",
            analysis_section="recommendation",
            quality_label="bad",
            tags=["bad-example", "unsupported-valuation", "invented-clause"],
            warnings=["Use for critique only; do not treat as positive guidance."],
        ),
    ),
    SeedKnowledgeEntry(
        text=(
            "Corrected analysis example: Instead of claiming NPV, state that destination flexibility was not identified unless the clause text "
            "supports it. If FOB delivery is extracted, route to FOB purchase/sale logic depending on role. List missing market price, freight, "
            "boil-off, terminal costs, discount rate, and portfolio exposure before any calculation."
        ),
        metadata=_metadata(
            title="Corrected Evidence-constrained Analysis Example",
            knowledge_type="corrected_analysis_example",
            analysis_section="recommendation",
            quality_label="corrected",
            tags=["corrected-example", "evidence", "valuation-guardrail"],
        ),
    ),
    SeedKnowledgeEntry(
        text=(
            "No unsupported valuation claims policy: Do not state NPV, IRR, fair value, option value, expected profit, margin, trade P&L, or "
            "final valuation unless a deterministic calculator or approved model produced that value from documented assumptions. Extraction "
            "outputs may identify model inputs and readiness only."
        ),
        metadata=_metadata(
            title="No Unsupported Valuation Claims Policy",
            knowledge_type="risk_policy",
            analysis_section="risk",
            quality_label="good",
            tags=["valuation-claims", "npv", "guardrail", "policy"],
        ),
    ),
    SeedKnowledgeEntry(
        text=(
            "LNG SPA glossary: DES means delivered ex ship or delivered destination-style delivery. FOB means free on board at loading point. "
            "ACQ is annual contract quantity. DCQ is daily contract quantity. Take-or-pay is a minimum payment/take obligation. Make-up is a "
            "right to recover paid-for untaken quantities. Carry-forward moves excess/shortfall quantities to later periods. Destination flexibility "
            "is the ability to redirect, divert, resell, or nominate destinations. JKM, TTF, and Brent slope are pricing references. Boil-off is "
            "cargo loss or fuel use during shipping. Regas is conversion of LNG back to gas at terminal."
        ),
        metadata=_metadata(
            title="LNG SPA Commercial Glossary",
            knowledge_type="glossary",
            analysis_section="taxonomy",
            quality_label="reference",
            tags=["glossary", "des", "fob", "acq", "dcq", "jkm", "ttf", "brent", "boil-off", "regas"],
        ),
    ),
    SeedKnowledgeEntry(
        text=(
            "Market fundamentals guidance: LNG SPA analysis often requires destination gas or LNG prices, oil-linked formula references, FX, "
            "freight, shipping duration, boil-off, terminal charges, basis spreads, liquidity, volatility, seasonality, and regulatory costs. "
            "Do not imply these market inputs are known unless supplied by the analyst or visible in the document."
        ),
        metadata=_metadata(
            title="LNG Market Fundamentals Input Checklist",
            knowledge_type="market_fundamentals",
            analysis_section="valuation_input_pack",
            quality_label="good",
            tags=["market", "freight", "basis", "volatility", "terminal"],
        ),
    ),
    SeedKnowledgeEntry(
        text=(
            "Internal procedure: first extract contract evidence, then map to taxonomy, then map to valuation input candidates, then route the "
            "commercial model, then request manual assumptions before calculation. RAG guidance is methodology only and must never be cited as "
            "contract evidence."
        ),
        metadata=_metadata(
            title="SPA Commercial Review Procedure",
            knowledge_type="internal_procedure",
            analysis_section="recommendation",
            quality_label="good",
            tags=["procedure", "taxonomy", "rag", "evidence"],
        ),
    ),
]


def seed_starter_knowledge_pack() -> SeedPackResult:
    settings = get_settings()
    index = create_rag_index(settings)
    existing = {
        (doc.title, doc.knowledge_type.value, doc.version or "")
        for doc in index.list_knowledge_documents()
    }
    ingested: list[IngestionResult] = []
    skipped_titles: list[str] = []
    warnings: list[str] = []

    for entry in SEED_KNOWLEDGE_ENTRIES:
        key = (entry.metadata.title, entry.metadata.knowledge_type.value, entry.metadata.version or "")
        if key in existing:
            skipped_titles.append(entry.metadata.title)
            continue
        result = ingest_knowledge_text(entry.text, entry.metadata)
        ingested.append(result)
        warnings.extend(result.warnings)
        existing.add(key)

    return SeedPackResult(
        entries_attempted=len(SEED_KNOWLEDGE_ENTRIES),
        entries_ingested=len(ingested),
        duplicates_skipped=len(skipped_titles),
        warnings=_dedupe(warnings),
        ingested=ingested,
        skipped_titles=skipped_titles,
    )


def _dedupe(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value and value not in output:
            output.append(value)
    return output
