import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.analysis_pipeline import run_analysis_pipeline
from app.config import get_settings
from app.llm_providers.mock_provider import MockProvider
from app.main import app
from app.rag.context_builder import build_analysis_rag_context
from app.rag.ingestion import ingest_knowledge_text
from app.rag.knowledge_types import KnowledgeType
from app.rag.schemas import KnowledgeDocumentMetadata


CONTRACT_TEXT = "SPA pricing formula volume flexibility destination optionality risk recommendation terms. " * 4


def _metadata(**overrides) -> KnowledgeDocumentMetadata:
    data = {
        "title": "Pricing Mapping Rule",
        "knowledge_type": "model_input_mapping_rule",
        "source_filename": "pricing-rule.md",
        "version": "v1",
        "owner": "commercial analytics",
        "approval_status": "approved",
        "commodity": "lng",
        "contract_type": "spa",
        "analysis_section": "pricing",
        "quality_label": "good",
        "tags": ["pricing", "valuation"],
        "approved_for_rag": True,
    }
    data.update(overrides)
    return KnowledgeDocumentMetadata(**data)


def _reset_settings(monkeypatch, tmp_path, rag_enabled: bool = True) -> None:
    monkeypatch.setenv("LOCAL_RAG_DIR", str(tmp_path))
    monkeypatch.setenv("RAG_ENABLED", "true" if rag_enabled else "false")
    monkeypatch.setenv("RAG_REQUIRE_APPROVED_FOR_RAG", "true")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    get_settings.cache_clear()


def test_analyze_with_rag_disabled_remains_valid_without_context(monkeypatch, tmp_path) -> None:
    _reset_settings(monkeypatch, tmp_path, rag_enabled=False)
    monkeypatch.setenv("DOCUMENT_STORE_PROVIDER", "local")
    monkeypatch.setenv("LOCAL_DOCUMENT_DIR", str(tmp_path / "docs"))
    get_settings.cache_clear()
    monkeypatch.setattr("app.main.extract_text_from_pdf", lambda _: CONTRACT_TEXT)
    client = TestClient(app)

    response = client.post("/analyze", files={"file": ("spa.pdf", b"%PDF-1.4", "application/pdf")})

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract_summary"]
    assert payload.get("rag_context_summary") is None


def test_analyze_with_rag_enabled_in_mock_mode_includes_context_summary(monkeypatch, tmp_path) -> None:
    _reset_settings(monkeypatch, tmp_path, rag_enabled=True)
    monkeypatch.setenv("DOCUMENT_STORE_PROVIDER", "local")
    monkeypatch.setenv("LOCAL_DOCUMENT_DIR", str(tmp_path / "docs"))
    get_settings.cache_clear()
    ingest_knowledge_text(
        "Pricing formula guidance maps index, currency, escalation, and missing market data to valuation input candidates.",
        _metadata(),
    )
    monkeypatch.setattr("app.main.extract_text_from_pdf", lambda _: CONTRACT_TEXT)
    client = TestClient(app)

    response = client.post("/analyze", files={"file": ("spa.pdf", b"%PDF-1.4", "application/pdf")})

    assert response.status_code == 200
    summary = response.json()["rag_context_summary"]
    assert summary["enabled"] is True
    assert summary["items_used"]
    assert "not contract evidence" in summary["note"].lower()
    assert summary["prompt_context"] == ""


def test_context_builder_retrieves_and_deduplicates_relevant_chunks(monkeypatch, tmp_path) -> None:
    _reset_settings(monkeypatch, tmp_path, rag_enabled=True)
    ingest_knowledge_text(
        "Pricing formula guidance. Pricing formula guidance. Use contract text as source of truth.",
        _metadata(),
    )

    bundle = build_analysis_rag_context(CONTRACT_TEXT, ["pricing", "valuation_input_pack"], top_k=5)

    assert bundle.enabled is True
    assert bundle.items_used
    chunk_ids = [item.chunk_id for item in bundle.items_used]
    assert len(chunk_ids) == len(set(chunk_ids))
    assert "not contract evidence" in bundle.note.lower()
    assert "RAG GUIDANCE CONTEXT" in bundle.prompt_context


def test_bad_analysis_example_is_excluded_by_default_with_warning(monkeypatch, tmp_path) -> None:
    _reset_settings(monkeypatch, tmp_path, rag_enabled=True)
    ingest_knowledge_text(
        "pricing formula bad analysis example optionality recommendation",
        _metadata(title="Bad Example", knowledge_type="bad_analysis_example", quality_label="bad"),
        allow_unapproved=True,
    )

    bundle = build_analysis_rag_context(CONTRACT_TEXT, ["pricing"], top_k=5)

    assert all(item.knowledge_type != KnowledgeType.BAD_ANALYSIS_EXAMPLE for item in bundle.items_used)
    assert "bad analysis example" in " ".join(bundle.warnings).lower()


def test_deprecated_and_draft_materials_are_warning_marked_and_excluded(monkeypatch, tmp_path) -> None:
    _reset_settings(monkeypatch, tmp_path, rag_enabled=True)
    ingest_knowledge_text(
        "pricing formula deprecated methodology",
        _metadata(title="Deprecated Method", approval_status="deprecated"),
    )

    bundle = build_analysis_rag_context(CONTRACT_TEXT, ["pricing"], top_k=5)

    assert not bundle.items_used
    assert "deprecated" in " ".join(bundle.warnings).lower()


def test_provider_interface_accepts_optional_rag_context() -> None:
    response = MockProvider().analyze_contract(CONTRACT_TEXT, rag_context="internal guidance only")

    assert response.contract_summary
