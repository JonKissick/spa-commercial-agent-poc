import hashlib
from datetime import UTC, datetime
from uuid import uuid4

from app.document_store.base import DocumentStoreConfigurationError, StoredDocument
from app.document_store.local_store import sanitize_filename


class S3DocumentStore:
    provider_name = "s3"

    def __init__(
        self,
        bucket_name: str | None,
        prefix: str,
        region_name: str | None,
        kms_key_id: str | None,
        retention_policy: str,
    ) -> None:
        if not bucket_name:
            raise DocumentStoreConfigurationError("S3_BUCKET_NAME is required for DOCUMENT_STORE_PROVIDER=s3.")
        if not region_name:
            raise DocumentStoreConfigurationError("AWS_REGION is required for DOCUMENT_STORE_PROVIDER=s3.")
        try:
            import boto3
        except ImportError as exc:
            raise DocumentStoreConfigurationError("boto3 is required for DOCUMENT_STORE_PROVIDER=s3.") from exc
        self.bucket_name = bucket_name
        self.prefix = prefix.strip("/")
        self.region_name = region_name
        self.kms_key_id = kms_key_id
        self.retention_policy = retention_policy
        self.client = boto3.client("s3", region_name=region_name)

    def save_document(self, file_bytes: bytes, filename: str, content_type: str) -> StoredDocument:
        document_id = uuid4().hex
        safe_filename = sanitize_filename(filename)
        key = self._key(document_id, safe_filename)
        checksum = hashlib.sha256(file_bytes).hexdigest()
        extra_args = {
            "Bucket": self.bucket_name,
            "Key": key,
            "Body": file_bytes,
            "ContentType": content_type,
            "Metadata": {
                "project": "spa-commercial-agent-poc",
                "document_id": document_id,
                "original_filename": safe_filename,
                "checksum_sha256": checksum,
                "content_type": content_type,
            },
        }
        encryption_status = "aws_kms" if self.kms_key_id else "sse_s3"
        if self.kms_key_id:
            extra_args["ServerSideEncryption"] = "aws:kms"
            extra_args["SSEKMSKeyId"] = self.kms_key_id
        else:
            extra_args["ServerSideEncryption"] = "AES256"
        self.client.put_object(**extra_args)
        created_at = datetime.now(UTC).isoformat()
        return StoredDocument(
            document_id=document_id,
            original_filename=safe_filename,
            content_type=content_type,
            storage_provider=self.provider_name,
            storage_uri=f"s3://{self.bucket_name}/{key}",
            size_bytes=len(file_bytes),
            checksum_sha256=checksum,
            created_at=created_at,
            encryption_status=encryption_status,
            retention_policy=self.retention_policy,
            metadata=extra_args["Metadata"],
        )

    def get_document(self, document_id: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket_name, Key=self._prefix_for_document(document_id))
        return response["Body"].read()

    def delete_document(self, document_id: str) -> None:
        self.client.delete_object(Bucket=self.bucket_name, Key=self._prefix_for_document(document_id))

    def _key(self, document_id: str, filename: str) -> str:
        base = f"{document_id}/{filename}"
        return f"{self.prefix}/{base}" if self.prefix else base

    def _prefix_for_document(self, document_id: str) -> str:
        # Later stages can persist exact keys. This scaffold assumes the document id is the key prefix.
        return f"{self.prefix}/{document_id}" if self.prefix else document_id
