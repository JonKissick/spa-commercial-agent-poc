import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_returns_clear_error_when_pdf_has_no_extractable_text(monkeypatch) -> None:
    client = TestClient(app)

    monkeypatch.setattr("app.main.extract_text_from_pdf", lambda _: "")
    response = client.post(
        "/analyze",
        files={"file": ("blank.pdf", b"%PDF-1.4", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "No extractable text found. This POC currently supports text-based PDFs only; scanned PDFs will require OCR in a later stage."
    )


def test_analyze_in_mock_mode_includes_document_metadata(monkeypatch, tmp_path) -> None:
    from app.config import get_settings

    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("DOCUMENT_STORE_PROVIDER", "local")
    monkeypatch.setenv("LOCAL_DOCUMENT_DIR", str(tmp_path))
    get_settings.cache_clear()

    client = TestClient(app)
    monkeypatch.setattr(
        "app.main.extract_text_from_pdf",
        lambda _: "Sample SPA text with pricing, delivery, volume, credit, and commercial terms. " * 3,
    )

    response = client.post(
        "/analyze",
        files={"file": ("../Sensitive SPA #1.pdf", b"%PDF-1.4 text pdf", "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract_summary"]
    assert payload["clause_coverage"]
    metadata = payload["document_metadata"]
    assert metadata["document_id"]
    assert metadata["original_filename"] == "Sensitive_SPA_1.pdf"
    assert metadata["content_type"] == "application/pdf"
    assert metadata["size_bytes"] == len(b"%PDF-1.4 text pdf")
    assert metadata["storage_provider"] == "local"
    assert metadata["storage_uri"] is None
    assert "Sample SPA text" not in str(metadata)


def test_system_status_endpoint_exposes_only_non_secret_status(monkeypatch) -> None:
    from app.config import get_settings

    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("DOCUMENT_STORE_PROVIDER", "local")
    monkeypatch.setenv("RAG_PROVIDER", "local")
    monkeypatch.setenv("RAG_ENABLED", "true")
    get_settings.cache_clear()
    client = TestClient(app)

    response = client.get("/system/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["llm_provider"] == "mock"
    assert payload["document_store_provider"] == "local"
    assert payload["rag_provider"] == "local"
    assert payload["rag_enabled"] is True
    serialized = str(payload).lower()
    assert "api_key" not in serialized
    assert "bucket" not in serialized
    assert "local_document_dir" not in serialized
    assert "prompt" not in serialized


def test_cors_preflight_allows_localhost_3001() -> None:
    client = TestClient(app)

    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3001",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3001"
    assert "GET" in response.headers["access-control-allow-methods"]


def test_cors_preflight_allows_loopback_3001() -> None:
    client = TestClient(app)

    response = client.options(
        "/system/status",
        headers={
            "Origin": "http://127.0.0.1:3001",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3001"
