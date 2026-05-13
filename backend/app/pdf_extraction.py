from io import BytesIO

from pypdf import PdfReader


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from a PDF byte stream using pypdf."""
    reader = PdfReader(BytesIO(pdf_bytes))
    pages: list[str] = []

    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text.strip())

    return "\n\n".join(pages)
