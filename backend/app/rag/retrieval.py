from typing import Any

from app.config import get_settings
from app.rag.factory import create_rag_index
from app.rag.schemas import RetrievalResult


def retrieve_knowledge(query: str, filters: dict[str, Any] | None = None, top_k: int = 5) -> list[RetrievalResult]:
    return create_rag_index(get_settings()).retrieve(query=query, filters=filters, top_k=top_k)
