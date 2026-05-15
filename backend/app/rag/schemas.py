from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from app.rag.knowledge_types import KnowledgeType


class KnowledgeDocumentMetadata(BaseModel):
    knowledge_id: str = Field(default_factory=lambda: uuid4().hex)
    title: str
    knowledge_type: KnowledgeType
    source_filename: str | None = None
    source_document_id: str | None = None
    version: str | None = None
    effective_date: str | None = None
    owner: str | None = None
    confidentiality: str = "internal"
    approval_status: str = "draft"
    jurisdiction: str | None = None
    commodity: str | None = None
    contract_type: str | None = None
    deal_type: str | None = None
    analysis_section: str | None = None
    quality_label: str | None = None
    tags: list[str] = Field(default_factory=list)
    approved_for_rag: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def normalize_metadata(self) -> "KnowledgeDocumentMetadata":
        self.approval_status = self.approval_status.strip().lower()
        self.confidentiality = self.confidentiality.strip().lower()
        if self.quality_label:
            self.quality_label = self.quality_label.strip().lower()
        self.tags = [tag.strip().lower() for tag in self.tags if tag.strip()]
        return self


class KnowledgeChunk(BaseModel):
    chunk_id: str
    knowledge_id: str
    chunk_index: int
    text: str
    metadata: KnowledgeDocumentMetadata
    checksum_sha256: str


class IngestionResult(BaseModel):
    knowledge_id: str
    title: str
    knowledge_type: KnowledgeType
    chunks_created: int
    warnings: list[str] = Field(default_factory=list)


class RetrievalResult(BaseModel):
    chunk_id: str
    knowledge_id: str
    title: str
    knowledge_type: KnowledgeType
    text: str
    metadata: KnowledgeDocumentMetadata
    score: float
    warnings: list[str] = Field(default_factory=list)


class IngestTextRequest(BaseModel):
    text: str
    metadata: KnowledgeDocumentMetadata
    allow_unapproved: bool = False


class RetrieveRequest(BaseModel):
    query: str
    filters: dict[str, Any] | None = None
    top_k: int = 5


class RagContextItem(BaseModel):
    chunk_id: str
    knowledge_id: str
    title: str
    knowledge_type: KnowledgeType
    analysis_section: str | None = None
    text_excerpt: str
    score: float
    warnings: list[str] = Field(default_factory=list)


class RagContextBundle(BaseModel):
    enabled: bool = False
    items_used: list[RagContextItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    note: str = "RAG guidance is not contract evidence and must not be used to infer missing contractual provisions."
    prompt_context: str = ""
