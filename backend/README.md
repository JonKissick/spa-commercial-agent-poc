# Backend

FastAPI backend for the SPA Commercial Evaluation Agent POC.

Stage 1 extracts embedded PDF text with `pypdf`, optionally sends that text to OpenAI for structured commercial analysis, validates the result with Pydantic, and returns a `CommercialEvaluationResponse`.

If `OPENAI_API_KEY` is not set, the backend keeps working with the local mock fallback.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment

Create a local `.env` file or export variables in your shell:

```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4.1
MAX_CONTRACT_CHARS=120000
ALLOWED_ORIGINS=http://localhost:3000
```

`OPENAI_API_KEY` is optional for local fallback mode. `OPENAI_MODEL` should be a structured-output capable OpenAI model.

## Run

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## Endpoints

- `GET /health`: returns `{ "status": "ok" }`.
- `POST /analyze`: accepts a text-based PDF upload as multipart form data and returns a structured commercial evaluation.

## Test `/analyze`

```bash
curl -X POST http://localhost:8000/analyze   -F "file=@/path/to/spa-contract.pdf"
```

## Tests

```bash
pytest
```

## Stage 1 Limitations

- Text extraction only supports embedded PDF text. Scanned PDFs require OCR in a later stage.
- The OpenAI analysis is a first-pass extraction and commercial interpretation workflow, not legal advice.
- No final valuation, DCF model, quantitative option valuation, or portfolio optimization is performed.
- Market and portfolio conclusions require manual assumptions unless those assumptions are supplied in the uploaded document.
- No database, auth, deployment, Docker, report export, or multi-agent orchestration is included.
