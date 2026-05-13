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
