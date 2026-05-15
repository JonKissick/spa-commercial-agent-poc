import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.rag.retrieval import retrieve_knowledge
from app.rag.seed_pack import SEED_KNOWLEDGE_ENTRIES, seed_starter_knowledge_pack


def _use_tmp_rag(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("LOCAL_RAG_DIR", str(tmp_path))
    monkeypatch.setenv("RAG_REQUIRE_APPROVED_FOR_RAG", "true")
    get_settings.cache_clear()


def test_seed_pack_contains_required_guidance_areas() -> None:
    text = " ".join(f"{entry.metadata.title} {' '.join(entry.metadata.tags)} {entry.text}" for entry in SEED_KNOWLEDGE_ENTRIES).lower()
    required_terms = [
        "pricing",
        "des",
        "fob",
        "acq",
        "dcq",
        "take-or-pay",
        "destination flexibility",
        "make-up",
        "carry-forward",
        "price review",
        "credit",
        "force majeure",
        "portfolio",
        "recommendation",
        "good analysis",
        "bad analysis",
        "corrected",
        "unsupported valuation",
        "glossary",
    ]
    for term in required_terms:
        assert term in text


def test_seed_entries_have_valid_approved_metadata() -> None:
    assert len(SEED_KNOWLEDGE_ENTRIES) >= 15
    for entry in SEED_KNOWLEDGE_ENTRIES:
        metadata = entry.metadata
        assert entry.text.strip()
        assert metadata.title
        assert metadata.approved_for_rag is True
        assert metadata.approval_status == "approved"
        assert metadata.owner == "commercial"
        assert metadata.confidentiality == "internal"
        assert metadata.commodity == "lng"
        assert metadata.contract_type == "spa"
        assert metadata.version == "v1"

    bad_entries = [entry for entry in SEED_KNOWLEDGE_ENTRIES if entry.metadata.knowledge_type.value == "bad_analysis_example"]
    assert bad_entries
    assert all(entry.metadata.quality_label == "bad" for entry in bad_entries)


def test_seed_service_ingests_entries_and_skips_duplicates(monkeypatch, tmp_path) -> None:
    _use_tmp_rag(monkeypatch, tmp_path)

    first = seed_starter_knowledge_pack()
    second = seed_starter_knowledge_pack()

    assert first.entries_attempted == len(SEED_KNOWLEDGE_ENTRIES)
    assert first.entries_ingested == len(SEED_KNOWLEDGE_ENTRIES)
    assert first.duplicates_skipped == 0
    assert second.entries_ingested == 0
    assert second.duplicates_skipped == len(SEED_KNOWLEDGE_ENTRIES)


def test_seed_endpoint_ingests_and_lists_knowledge(monkeypatch, tmp_path) -> None:
    _use_tmp_rag(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.post("/rag/seed")
    knowledge = client.get("/rag/knowledge")

    assert response.status_code == 200
    assert response.json()["entries_ingested"] == len(SEED_KNOWLEDGE_ENTRIES)
    assert knowledge.status_code == 200
    assert len(knowledge.json()) == len(SEED_KNOWLEDGE_ENTRIES)


def test_seeded_retrieval_finds_pricing_des_fob_and_destination_guidance(monkeypatch, tmp_path) -> None:
    _use_tmp_rag(monkeypatch, tmp_path)
    seed_starter_knowledge_pack()

    pricing = retrieve_knowledge("pricing formula index slope currency", top_k=3)
    fob = retrieve_knowledge("FOB buyer freight boil-off destination market", top_k=3)
    destination = retrieve_knowledge("destination flexibility diversion spread option", top_k=3)

    assert any("Pricing" in result.title for result in pricing)
    assert any("DES FOB" in result.title for result in fob)
    assert any("Destination Flexibility" in result.title for result in destination)


def test_bad_analysis_seed_is_retrievable_with_warning(monkeypatch, tmp_path) -> None:
    _use_tmp_rag(monkeypatch, tmp_path)
    seed_starter_knowledge_pack()

    results = retrieve_knowledge("unsupported valuation invented clause bad analysis", filters={"knowledge_type": "bad_analysis_example"}, top_k=5)

    assert results
    warnings = " ".join(results[0].warnings).lower()
    assert "bad analysis example" in warnings
    assert "critique" in warnings
