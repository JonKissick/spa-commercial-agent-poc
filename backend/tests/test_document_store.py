import hashlib
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import Settings
from app.document_store.base import DocumentStoreConfigurationError
from app.document_store.factory import create_document_store
from app.document_store.local_store import LocalDocumentStore, sanitize_filename
from app.document_store.s3_store import S3DocumentStore


def test_local_document_store_saves_retrieves_and_deletes(tmp_path) -> None:
    store = LocalDocumentStore(base_dir=tmp_path, retention_policy="test_delete")
    file_bytes = b"commercial pdf bytes"

    stored = store.save_document(file_bytes, "../SPA Contract!.pdf", "application/pdf")

    assert stored.original_filename == "SPA_Contract_.pdf"
    assert stored.size_bytes == len(file_bytes)
    assert stored.checksum_sha256 == hashlib.sha256(file_bytes).hexdigest()
    assert store.get_document(stored.document_id) == file_bytes
    store.delete_document(stored.document_id)
    assert not (tmp_path / stored.document_id).exists()


def test_filename_sanitization() -> None:
    assert sanitize_filename("../../Sensitive SPA #1.pdf") == "Sensitive_SPA_1.pdf"
    assert sanitize_filename("") == "uploaded-document.pdf"


def test_local_document_metadata_does_not_include_raw_text(tmp_path) -> None:
    store = LocalDocumentStore(base_dir=tmp_path, retention_policy="test_delete")
    stored = store.save_document(b"raw bytes", "contract.pdf", "application/pdf")

    metadata_text = " ".join(stored.metadata.values()).lower()
    assert "raw bytes" not in metadata_text
    assert "contract text" not in metadata_text


def test_default_document_store_provider_is_local() -> None:
    settings = Settings()

    assert settings.document_store_provider == "local"


def test_invalid_document_store_provider_raises_clear_error() -> None:
    settings = Settings(document_store_provider="bad-provider")

    try:
        create_document_store(settings)
    except DocumentStoreConfigurationError as exc:
        assert "Unsupported DOCUMENT_STORE_PROVIDER" in str(exc)
    else:
        raise AssertionError("Invalid document store provider should raise")


def test_s3_store_can_be_constructed_with_mocked_boto3(monkeypatch) -> None:
    calls = []

    class FakeBoto3:
        def client(self, service_name, region_name=None):
            calls.append((service_name, region_name))
            return object()

    monkeypatch.setitem(sys.modules, "boto3", FakeBoto3())

    store = S3DocumentStore(
        bucket_name="test-bucket",
        prefix="prefix/",
        region_name="ap-southeast-2",
        kms_key_id="kms-key",
        retention_policy="retain",
    )

    assert store.bucket_name == "test-bucket"
    assert calls == [("s3", "ap-southeast-2")]


def test_gitignore_ignores_local_documents() -> None:
    gitignore = Path(__file__).resolve().parents[2] / ".gitignore"

    assert "backend/.local_documents/" in gitignore.read_text()
