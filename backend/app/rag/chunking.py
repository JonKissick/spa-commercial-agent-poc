import hashlib
from uuid import uuid4

from app.rag.schemas import KnowledgeChunk, KnowledgeDocumentMetadata


def chunk_text(
    text: str,
    metadata: KnowledgeDocumentMetadata,
    chunk_size: int = 1200,
    chunk_overlap: int = 150,
) -> list[KnowledgeChunk]:
    cleaned = text.replace("\r\n", "\n").strip()
    if not cleaned:
        return []
    chunk_size = max(chunk_size, 200)
    chunk_overlap = max(0, min(chunk_overlap, chunk_size // 2))
    paragraphs = [part.strip() for part in cleaned.split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_split_long_text(paragraph, chunk_size, chunk_overlap))
            continue
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            chunks.append(current.strip())
            overlap = current[-chunk_overlap:] if chunk_overlap else ""
            current = f"{overlap}\n\n{paragraph}".strip() if overlap else paragraph
    if current.strip():
        chunks.append(current.strip())
    return [_build_chunk(chunk, metadata, index) for index, chunk in enumerate(chunks) if chunk.strip()]


def checksum_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _split_long_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - chunk_overlap, start + 1)
    return chunks


def _build_chunk(text: str, metadata: KnowledgeDocumentMetadata, chunk_index: int) -> KnowledgeChunk:
    return KnowledgeChunk(
        chunk_id=uuid4().hex,
        knowledge_id=metadata.knowledge_id,
        chunk_index=chunk_index,
        text=text,
        metadata=metadata,
        checksum_sha256=checksum_text(text),
    )
