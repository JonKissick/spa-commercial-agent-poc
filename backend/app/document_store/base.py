from typing import Protocol

from pydantic import BaseModel, Field


class DocumentStoreError(RuntimeError):
    pass


class DocumentStoreConfigurationError(DocumentStoreError):
    pass


class StoredDocument(BaseModel):
    document_id: str
    original_filename: str
    content_type: str
    storage_provider: str
    storage_uri: str
    size_bytes: int
    checksum_sha256: str
    created_at: str
    encryption_status: str
    retention_policy: str
    metadata: dict[str, str] = Field(default_factory=dict)


class DocumentStore(Protocol):
    def save_document(self, file_bytes: bytes, filename: str, content_type: str) -> StoredDocument:
        ...

    def get_document(self, document_id: str) -> bytes:
        ...

    def delete_document(self, document_id: str) -> None:
        ...
