from app.config import get_settings
from app.rag.factory import create_rag_index
from app.rag.knowledge_types import KnowledgeType
from app.rag.schemas import RagContextBundle, RagContextItem, RetrievalResult

SECTION_QUERIES = {
    "pricing": "pricing formula index escalation currency model input mapping",
    "volume": "volume annual contract quantity take or pay nomination tolerance",
    "valuation_input_pack": "valuation methodology model input mapping assumptions missing market data",
    "optionality": "destination flexibility volume flexibility make-up price review optionality method",
    "risk": "risk policy credit termination force majeure penalties operational constraints",
    "recommendation": "recommendation memo conditions risks reviewer feedback negotiation playbook",
}


def build_analysis_rag_context(
    contract_text: str,
    analysis_sections: list[str],
    top_k: int,
) -> RagContextBundle:
    settings = get_settings()
    if not settings.rag_enabled:
        return RagContextBundle(enabled=False)

    index = create_rag_index(settings)
    allowed_types = set(settings.rag_allowed_types)
    seen_chunks: set[str] = set()
    items: list[RagContextItem] = []
    warnings: list[str] = []

    for section in analysis_sections:
        query = _build_query(section, contract_text)
        filters = {"approved_for_rag": True}
        results = index.retrieve(query=query, filters=filters, top_k=max(1, top_k))
        for result in results:
            if result.chunk_id in seen_chunks:
                continue
            if result.knowledge_type.value not in allowed_types:
                if result.knowledge_type == KnowledgeType.BAD_ANALYSIS_EXAMPLE:
                    warnings.append("Bad analysis example was excluded from analysis RAG context by default.")
                continue
            if result.metadata.approval_status in {"deprecated", "draft", "superseded"}:
                warnings.extend(result.warnings)
                continue
            seen_chunks.add(result.chunk_id)
            items.append(_to_context_item(result, section))
            warnings.extend(result.warnings)
            if len(items) >= top_k:
                break
        if len(items) >= top_k:
            break

    return RagContextBundle(
        enabled=True,
        items_used=items,
        warnings=_dedupe(warnings),
        prompt_context=_format_prompt_context(items),
    )


def _build_query(section: str, contract_text: str) -> str:
    base_query = SECTION_QUERIES.get(section, section)
    contract_terms = " ".join(contract_text.split()[:80])
    return f"{base_query} {contract_terms}"


def _to_context_item(result: RetrievalResult, section: str) -> RagContextItem:
    excerpt = result.text.strip().replace("\n", " ")[:700]
    return RagContextItem(
        chunk_id=result.chunk_id,
        knowledge_id=result.knowledge_id,
        title=result.title,
        knowledge_type=result.knowledge_type,
        analysis_section=section,
        text_excerpt=excerpt,
        score=result.score,
        warnings=result.warnings,
    )


def _format_prompt_context(items: list[RagContextItem]) -> str:
    if not items:
        return ""
    lines = [
        "RAG GUIDANCE CONTEXT - internal methodology only, not contract evidence:",
        "Use this to improve classification, methodology, assumptions, warnings, and recommendation quality.",
        "Never cite this context as proof that a contract clause exists.",
    ]
    for index, item in enumerate(items, start=1):
        warning_text = f" Warnings: {'; '.join(item.warnings)}" if item.warnings else ""
        lines.append(
            f"[{index}] {item.title} ({item.knowledge_type.value}, section={item.analysis_section}, score={item.score}): {item.text_excerpt}{warning_text}"
        )
    return "\n".join(lines)


def _dedupe(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value and value not in output:
            output.append(value)
    return output
