# Backend

FastAPI backend for the SPA Commercial Evaluation Agent POC.

Stage 3 extracts embedded PDF text with `pypdf`, optionally sends that text to OpenAI for structured commercial analysis, validates the result with Pydantic, and returns a `CommercialEvaluationResponse` with a taxonomy-driven provision register, clause coverage map, and structured valuation input pack.

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

The API will be available at `http://localhost:8000` unless that port is already in use.

## Endpoints

- `GET /health`: returns `{ "status": "ok" }`.
- `POST /analyze`: accepts a text-based PDF upload as multipart form data and returns a structured commercial evaluation.

## Test `/analyze`

```bash
curl -X POST http://localhost:8000/analyze   -F "file=@/path/to/spa-contract.pdf"
```

## Stage 2 Taxonomy

The backend includes a deterministic SPA commercial taxonomy in `app/taxonomy.py`. It covers:

- pricing
- volume
- take_or_pay
- delivery
- destination_flexibility
- volume_flexibility
- make_up
- price_review
- force_majeure
- termination
- credit
- quality
- tax
- change_in_law
- penalties
- operational_constraints
- assignment_change_of_control
- other

Each taxonomy item includes a label, description, what to look for, common clause signals, commercial importance, and typical valuation impact candidates.

## Clause Coverage Map

Responses include top-level `clause_coverage`. Each item maps one taxonomy category to a coverage status:

- `present`: directly supported by extracted contract text.
- `weak_unclear`: partial, ambiguous, indirect, or low-confidence support.
- `not_identified`: no supporting extracted text was identified.

The validator requires every taxonomy category exactly once. Present and weak/unclear items must include evidence summary or linked provision IDs. Not-identified items must state that supporting evidence was not identified.

## Evidence Statuses

Provision outputs use evidence statuses to separate contract evidence from assumptions:

- `extracted_from_contract`
- `inferred_from_contract`
- `analyst_assumption_required`
- `market_assumption_required`
- `portfolio_assumption_required`
- `insufficient_evidence`

Low-confidence provisions and insufficient-evidence provisions must include warnings.


## Stage 3 Valuation Input Pack

The response includes a structured `valuation_input_pack` that translates extracted SPA provisions into model input candidates for later analyst work. It does not calculate value.

The pack separates:

- contract-extracted or contract-inferred inputs
- analyst assumptions required
- missing market data
- missing portfolio data
- valuation warnings
- source provision ID links where practical

Structured fields include pricing, volume, delivery, duration, flexibility, make-up rights, price review, penalties, credit support, quality, tax/change-in-law exposure, operational constraints, termination economics, and grouped DCF/optionality/risk/portfolio input candidates.

The backend deliberately does not calculate NPV, IRR, option value, fair value, expected margin, trade P&L, or final valuation. Deterministic validation removes prohibited valuation-result claims from valuation input fields and adds a warning.

## Tests

```bash
pytest -q
```

No test requires a real OpenAI API call.

## Stage 3 Limitations

- Text extraction only supports embedded PDF text. Scanned PDFs require OCR in a later stage.
- The OpenAI analysis is a first-pass extraction and commercial interpretation workflow, not legal advice.
- No final valuation, DCF model, NPV, IRR, option value, fair value, expected margin, trade P&L, quantitative option valuation, or portfolio optimization is performed.
- Market and portfolio conclusions require manual assumptions unless those assumptions are supplied in the uploaded document.
- Clause coverage is evidence-constrained and depends on the quality of extracted PDF text.
- No database, auth, deployment, Docker, report export, or multi-agent orchestration is included.
