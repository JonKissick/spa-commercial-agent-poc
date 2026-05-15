import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.rag.chunking import checksum_text, chunk_text
from app.rag.ingestion import ingest_knowledge_text
from app.rag.knowledge_types import KNOWLEDGE_TYPE_REGISTRY, KnowledgeType
from app.rag.local_index import LocalRAGIndex
from app.rag.retrieval import retrieve_knowledge
from app.rag.schemas import KnowledgeDocumentMetadata


def _metadata(**overrides) -> KnowledgeDocumentMetadata:
    data = {
        "title": "Valuation Method Note",
        "knowledge_type": "valuation_methodology",
        "source_filename": "method.md",
        "version": "v1",
        "owner": "commercial analytics",
        "approval_status": "approved",
        "commodity": "lng",
        "contract_type": "spa",
        "analysis_section": "valuation_input_pack",
        "quality_label": "good",
        "tags": ["pricing", "volume"],
        "approved_for_rag": True,
    }
    data.update(overrides)
    return KnowledgeDocumentMetadata(**data)


def test_knowledge_type_registry_includes_required_types() -> None:
    expected = {
        "contract_reference",
        "internal_procedure",
        "valuation_methodology",
        "market_fundamentals",
        "portfolio_strategy",
        "good_analysis_example",
        "bad_analysis_example",
        "corrected_analysis_example",
        "reviewer_feedback",
        "taxonomy_guidance",
        "model_input_mapping_rule",
        "negotiation_playbook",
        "glossary",
        "risk_policy",
        "other",
    }
    assert {item.value for item in KNOWLEDGE_TYPE_REGISTRY} == expected
    for item in KNOWLEDGE_TYPE_REGISTRY.values():
        assert item["label"]
        assert item["description"]
        assert item["intended_use"]
        assert isinstance(item["allowed_in_analysis_context"], bool)
        assert item["caution"]


def test_metadata_validation_normalizes_fields() -> None:
    metadata = _metadata(approval_status="Approved", tags=[" Pricing ", "Volume"])

    assert metadata.approval_status == "approved"
    assert metadata.tags == ["pricing", "volume"]


def test_chunking_creates_non_empty_overlapping_stable_chunks() -> None:
    metadata = _metadata()
    text = "A" * 900 + "\n\n" + "B" * 900

    chunks = chunk_text(text, metadata, chunk_size=1000, chunk_overlap=100)

    assert len(chunks) >= 2
    assert all(chunk.text for chunk in chunks)
    assert chunks[1].text.startswith("A" * 100) or chunks[1].text.startswith("B")
    assert checksum_text(chunks[0].text) == chunks[0].checksum_sha256


def test_local_index_adds_retrieves_and_filters(tmp_path) -> None:
    index = LocalRAGIndex(tmp_path)
    lng_metadata = _metadata(commodity="lng", knowledge_type="valuation_methodology")
    oil_metadata = _metadata(title="Oil note", commodity="oil", knowledge_type="market_fundamentals")
    chunks = chunk_text("pricing formula index volume methodology", lng_metadata)
    chunks += chunk_text("oil market freight curve", oil_metadata)
    index.add_chunks(chunks)

    results = index.retrieve("pricing methodology", filters={"commodity": "lng"}, top_k=5)

    assert results
    assert all(result.metadata.commodity == "lng" for result in results)
    assert index.list_knowledge_documents()


def test_ingestion_rejects_unapproved_when_required(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("LOCAL_RAG_DIR", str(tmp_path))
    monkeypatch.setenv("RAG_REQUIRE_APPROVED_FOR_RAG", "true")
    get_settings.cache_clear()
    metadata = _metadata(approved_for_rag=False)

    try:
        ingest_knowledge_text("pricing guidance", metadata)
    except ValueError as exc:
        assert "not approved" in str(exc)
    else:
        raise AssertionError("Unapproved RAG material should be rejected")


def test_ingestion_warnings_for_draft_deprecated_and_bad_examples(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("LOCAL_RAG_DIR", str(tmp_path))
    monkeypatch.setenv("RAG_REQUIRE_APPROVED_FOR_RAG", "true")
    get_settings.cache_clear()
    metadata = _metadata(
        title="Bad draft",
        knowledge_type="bad_analysis_example",
        approval_status="deprecated",
        approved_for_rag=True,
    )

    result = ingest_knowledge_text("bad pricing analysis example", metadata)

    warnings = " ".join(result.warnings).lower()
    assert "deprecated" in warnings
    assert "bad analysis example" in warnings


def test_retrieval_returns_warnings_for_bad_and_deprecated(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("LOCAL_RAG_DIR", str(tmp_path))
    monkeypatch.setenv("RAG_REQUIRE_APPROVED_FOR_RAG", "true")
    get_settings.cache_clear()
    metadata = _metadata(
        title="Bad deprecated analysis",
        knowledge_type="bad_analysis_example",
        approval_status="deprecated",
        approved_for_rag=True,
    )
    ingest_knowledge_text("bad pricing analysis example", metadata)

    results = retrieve_knowledge("pricing analysis", top_k=3)

    assert results
    warnings = " ".join(results[0].warnings).lower()
    assert "bad analysis example" in warnings
    assert "deprecated" in warnings


def test_rag_endpoints_work(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("LOCAL_RAG_DIR", str(tmp_path))
    monkeypatch.setenv("RAG_REQUIRE_APPROVED_FOR_RAG", "true")
    get_settings.cache_clear()
    client = TestClient(app)
    payload = {
        "text": "Pricing formula should map to model input candidates only.",
        "metadata": _metadata(title="Endpoint note").model_dump(mode="json"),
    }

    ingest_response = client.post("/rag/ingest-text", json=payload)
    assert ingest_response.status_code == 200
    assert ingest_response.json()["chunks_created"] >= 1

    retrieve_response = client.post("/rag/retrieve", json={"query": "pricing formula", "filters": {"knowledge_type": "valuation_methodology"}, "top_k": 2})
    assert retrieve_response.status_code == 200
    assert retrieve_response.json()

    knowledge_response = client.get("/rag/knowledge")
    assert knowledge_response.status_code == 200
    assert knowledge_response.json()[0]["title"] == "Endpoint note"
    assert "text" not in knowledge_response.json()[0]


def test_local_rag_is_ignored_by_git() -> None:
    gitignore = Path(__file__).resolve().parents[2] / ".gitignore"
    assert "backend/.local_rag/" in gitignore.read_text()
