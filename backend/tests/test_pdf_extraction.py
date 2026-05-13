import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.pdf_extraction import extract_text_from_pdf


def test_extract_text_from_pdf_rejects_invalid_pdf_bytes() -> None:
    try:
        extract_text_from_pdf(b"not a pdf")
    except Exception as exc:
        assert exc is not None
    else:
        raise AssertionError("Invalid PDF bytes should raise an exception")
