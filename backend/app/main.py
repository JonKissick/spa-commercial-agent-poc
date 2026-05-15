from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.analysis_pipeline import AnalysisPipelineError, ContractTextValidationError, run_analysis_pipeline
from app.config import get_settings
from app.document_store.base import DocumentStoreError, StoredDocument
from app.document_store.factory import create_document_store
from app.pdf_extraction import extract_text_from_pdf
from app.schemas import CommercialEvaluationResponse, DocumentMetadata
from app.validation import CommercialEvaluationValidationError


settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=CommercialEvaluationResponse)
async def analyze(file: UploadFile = File(...)) -> CommercialEvaluationResponse:
    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")

    try:
        stored_document = create_document_store(settings).save_document(
            file_bytes=pdf_bytes,
            filename=file.filename or "uploaded-document.pdf",
            content_type=file.content_type or "application/pdf",
        )
    except DocumentStoreError as exc:
        raise HTTPException(status_code=500, detail="Unable to securely store uploaded document.") from exc

    try:
        contract_text = extract_text_from_pdf(pdf_bytes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Unable to extract text from PDF.") from exc

    if not contract_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No extractable text found. This POC currently supports text-based PDFs only; scanned PDFs will require OCR in a later stage.",
        )

    try:
        response = run_analysis_pipeline(contract_text)
        response.document_metadata = _to_document_metadata(stored_document)
        return response
    except ContractTextValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CommercialEvaluationValidationError as exc:
        raise HTTPException(status_code=500, detail=f"Commercial evaluation validation failed: {exc}") from exc
    except AnalysisPipelineError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _to_document_metadata(stored_document: StoredDocument) -> DocumentMetadata:
    # Do not expose local filesystem paths or raw extracted text in API metadata.
    storage_uri = stored_document.storage_uri if stored_document.storage_provider != "local" else None
    return DocumentMetadata(
        document_id=stored_document.document_id,
        original_filename=stored_document.original_filename,
        content_type=stored_document.content_type,
        size_bytes=stored_document.size_bytes,
        checksum_sha256=stored_document.checksum_sha256,
        storage_provider=stored_document.storage_provider,
        created_at=stored_document.created_at,
        encryption_status=stored_document.encryption_status,
        retention_policy=stored_document.retention_policy,
        storage_uri=storage_uri,
    )
