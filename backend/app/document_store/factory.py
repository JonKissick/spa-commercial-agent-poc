from pathlib import Path

from app.config import Settings
from app.document_store.base import DocumentStore, DocumentStoreConfigurationError
from app.document_store.local_store import LocalDocumentStore
from app.document_store.s3_store import S3DocumentStore

VALID_DOCUMENT_STORE_PROVIDERS = {"local", "s3"}


def create_document_store(settings: Settings) -> DocumentStore:
    provider = settings.document_store_provider.strip().lower()
    if provider == "local":
        return LocalDocumentStore(
            base_dir=Path(settings.local_document_dir),
            retention_policy=settings.document_retention_policy,
        )
    if provider == "s3":
        return S3DocumentStore(
            bucket_name=settings.s3_bucket_name,
            prefix=settings.s3_prefix,
            region_name=settings.aws_region,
            kms_key_id=settings.kms_key_id,
            retention_policy=settings.document_retention_policy,
        )
    raise DocumentStoreConfigurationError(
        f"Unsupported DOCUMENT_STORE_PROVIDER '{settings.document_store_provider}'. Expected one of: {', '.join(sorted(VALID_DOCUMENT_STORE_PROVIDERS))}."
    )
