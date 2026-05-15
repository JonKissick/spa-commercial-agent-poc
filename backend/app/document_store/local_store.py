import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.document_store.base import DocumentStoreError, StoredDocument

_SAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(filename: str | None) -> str:
    candidate = (filename or "uploaded-document.pdf").split("/")[-1].split("\\")[-1].strip()
    candidate = _SAFE_FILENAME.sub("_", candidate).strip("._")
    return candidate or "uploaded-document.pdf"


class LocalDocumentStore:
    provider_name = "local"

    def __init__(self, base_dir: str | Path, retention_policy: str) -> None:
        self.base_dir = Path(base_dir)
        self.retention_policy = retention_policy
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_document(self, file_bytes: bytes, filename: str, content_type: str) -> StoredDocument:
        document_id = uuid4().hex
        safe_filename = sanitize_filename(filename)
        checksum = hashlib.sha256(file_bytes).hexdigest()
        document_dir = self.base_dir / document_id
        document_dir.mkdir(parents=True, exist_ok=False)
        file_path = document_dir / safe_filename
        file_path.write_bytes(file_bytes)
        created_at = datetime.now(UTC).isoformat()
        return StoredDocument(
            document_id=document_id,
            original_filename=safe_filename,
            content_type=content_type,
            storage_provider=self.provider_name,
            storage_uri=f"local://{document_id}/{safe_filename}",
            size_bytes=len(file_bytes),
            checksum_sha256=checksum,
            created_at=created_at,
            encryption_status="local_filesystem_unencrypted",
            retention_policy=self.retention_policy,
            metadata={
                "project": "spa-commercial-agent-poc",
                "checksum_sha256": checksum,
                "content_type": content_type,
            },
        )

    def get_document(self, document_id: str) -> bytes:
        path = self._resolve_document_path(document_id)
        return path.read_bytes()

    def delete_document(self, document_id: str) -> None:
        path = self._resolve_document_path(document_id)
        parent = path.parent
        path.unlink(missing_ok=True)
        try:
            parent.rmdir()
        except OSError:
            pass

    def _resolve_document_path(self, document_id: str) -> Path:
        if not re.fullmatch(r"[a-f0-9]{32}", document_id):
            raise DocumentStoreError("Invalid document id.")
        document_dir = self.base_dir / document_id
        matches = [path for path in document_dir.iterdir() if path.is_file()] if document_dir.exists() else []
        if not matches:
            raise DocumentStoreError("Document not found.")
        return matches[0]
