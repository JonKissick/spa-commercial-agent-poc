import json
import re
from pathlib import Path
from typing import Any

from app.rag.knowledge_types import KnowledgeType
from app.rag.schemas import KnowledgeChunk, KnowledgeDocumentMetadata, RetrievalResult


class LocalRAGIndex:
    def __init__(self, index_dir: str | Path) -> None:
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.index_dir / "chunks.jsonl"

    def add_chunks(self, chunks: list[KnowledgeChunk]) -> None:
        with self.index_file.open("a", encoding="utf-8") as handle:
            for chunk in chunks:
                handle.write(chunk.model_dump_json() + "\n")

    def list_knowledge_documents(self) -> list[KnowledgeDocumentMetadata]:
        documents: dict[str, KnowledgeDocumentMetadata] = {}
        for chunk in self._load_chunks():
            documents[chunk.knowledge_id] = chunk.metadata
        return sorted(documents.values(), key=lambda item: item.created_at)

    def retrieve(self, query: str, filters: dict[str, Any] | None = None, top_k: int = 5) -> list[RetrievalResult]:
        terms = _tokenize(query)
        if not terms:
            return []
        results: list[RetrievalResult] = []
        for chunk in self._load_chunks():
            if not _matches_filters(chunk.metadata, filters or {}):
                continue
            score = _score_chunk(chunk.text, terms)
            if score <= 0:
                continue
            results.append(
                RetrievalResult(
                    chunk_id=chunk.chunk_id,
                    knowledge_id=chunk.knowledge_id,
                    title=chunk.metadata.title,
                    knowledge_type=chunk.metadata.knowledge_type,
                    text=chunk.text,
                    metadata=chunk.metadata,
                    score=score,
                    warnings=_retrieval_warnings(chunk.metadata),
                )
            )
        results.sort(key=lambda item: item.score, reverse=True)
        return results[: max(1, top_k)]

    def _load_chunks(self) -> list[KnowledgeChunk]:
        if not self.index_file.exists():
            return []
        chunks: list[KnowledgeChunk] = []
        with self.index_file.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    chunks.append(KnowledgeChunk.model_validate_json(line))
        return chunks


def _tokenize(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-zA-Z0-9_]+", text.lower()) if len(token) > 2]


def _score_chunk(text: str, terms: list[str]) -> float:
    lowered = text.lower()
    return float(sum(lowered.count(term) for term in terms))


def _matches_filters(metadata: KnowledgeDocumentMetadata, filters: dict[str, Any]) -> bool:
    for key, expected in filters.items():
        actual = getattr(metadata, key, None)
        if isinstance(actual, KnowledgeType):
            actual = actual.value
        if isinstance(expected, list):
            if actual not in expected:
                return False
        elif actual != expected:
            return False
    return True


def _retrieval_warnings(metadata: KnowledgeDocumentMetadata) -> list[str]:
    warnings = list(metadata.warnings)
    if metadata.knowledge_type == KnowledgeType.BAD_ANALYSIS_EXAMPLE:
        warnings.append("Bad analysis example is for critique/comparison only; do not treat as positive guidance.")
    if metadata.approval_status in {"draft", "deprecated", "superseded"}:
        warnings.append(f"Retrieved material approval status is {metadata.approval_status}; use with caution.")
    if not metadata.approved_for_rag:
        warnings.append("Retrieved material is not approved for RAG use.")
    return _dedupe(warnings)


def _dedupe(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value not in output:
            output.append(value)
    return output
