from app.config import get_settings
from app.rag.chunking import chunk_text
from app.rag.factory import create_rag_index
from app.rag.knowledge_types import KnowledgeType
from app.rag.schemas import IngestionResult, KnowledgeDocumentMetadata


def ingest_knowledge_text(
    text: str,
    metadata: KnowledgeDocumentMetadata,
    allow_unapproved: bool = False,
) -> IngestionResult:
    settings = get_settings()
    warnings = _metadata_warnings(metadata)
    if settings.rag_require_approved_for_rag and not metadata.approved_for_rag and not allow_unapproved:
        raise ValueError("Knowledge document is not approved for RAG ingestion.")
    metadata.warnings = _dedupe(metadata.warnings + warnings)
    chunks = chunk_text(
        text,
        metadata,
        chunk_size=settings.rag_default_chunk_size,
        chunk_overlap=settings.rag_default_chunk_overlap,
    )
    create_rag_index(settings).add_chunks(chunks)
    return IngestionResult(
        knowledge_id=metadata.knowledge_id,
        title=metadata.title,
        knowledge_type=metadata.knowledge_type,
        chunks_created=len(chunks),
        warnings=metadata.warnings,
    )


def _metadata_warnings(metadata: KnowledgeDocumentMetadata) -> list[str]:
    warnings: list[str] = []
    if metadata.approval_status in {"draft", "deprecated", "superseded"}:
        warnings.append(f"Knowledge document approval status is {metadata.approval_status}; use with caution.")
    if metadata.knowledge_type == KnowledgeType.BAD_ANALYSIS_EXAMPLE:
        warnings.append("Bad analysis example is for critique/comparison only; do not treat as positive guidance.")
    if metadata.knowledge_type == KnowledgeType.GLOSSARY:
        warnings.append("Glossary material is for definitions, not commercial conclusions.")
    return warnings


def _dedupe(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value not in output:
            output.append(value)
    return output
