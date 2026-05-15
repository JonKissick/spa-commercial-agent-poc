# Backend

FastAPI backend for the SPA Commercial Evaluation Agent POC.

Stage 5D extracts embedded PDF text with `pypdf`, stores the uploaded document through the document store, optionally retrieves local RAG guidance, sends the contract text to the configured LLM provider, validates the result with Pydantic, and returns a `CommercialEvaluationResponse` with a taxonomy-driven provision register, clause coverage map, structured valuation input pack, optionality register, document metadata, and optional RAG context summary.

The backend uses a swappable LLM provider layer. `LLM_PROVIDER=mock` is the default and requires no external API. OpenAI and AWS Bedrock providers are available for local analysis configuration. The project includes local document storage, an S3 scaffold, and local keyword RAG, but it does not include AWS deployment, Bedrock Knowledge Bases, auth, or database infrastructure.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment

Create a local `.env` file or export variables in your shell:

```bash
LLM_PROVIDER=mock
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4.1
AWS_REGION=ap-southeast-2
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
MAX_CONTRACT_CHARS=120000
RAG_ENABLED=false
RAG_TOP_K=5
RAG_ANALYSIS_SECTIONS=pricing,valuation_input_pack,optionality,risk,recommendation
RAG_ALLOWED_KNOWLEDGE_TYPES=internal_procedure,valuation_methodology,market_fundamentals,portfolio_strategy,good_analysis_example,corrected_analysis_example,reviewer_feedback,taxonomy_guidance,model_input_mapping_rule,negotiation_playbook,glossary,risk_policy
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:3002,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:3002
```

`LLM_PROVIDER` may be `mock`, `openai`, or `bedrock`. The default is `mock`. If `LLM_PROVIDER=openai` but `OPENAI_API_KEY` is missing, the backend falls back to mock mode. `OPENAI_MODEL` should be a structured-output capable OpenAI model. `AWS_REGION` and `BEDROCK_MODEL_ID` are used when `LLM_PROVIDER=bedrock`.

## Run

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000` unless that port is already in use.

## Endpoints

- `GET /health`: returns `{ "status": "ok" }`.
- `POST /analyze`: accepts a text-based PDF upload as multipart form data and returns a structured commercial evaluation.
- `GET /system/status`: returns non-secret local POC status for the frontend workbench.

## Test `/analyze`

```bash
curl -X POST http://localhost:8000/analyze   -F "file=@/path/to/spa-contract.pdf"
```


## LLM Providers

The analysis pipeline depends on `app/llm_providers/factory.py`, not directly on OpenAI. Providers live under `app/llm_providers/`:

- `mock`: deterministic local fallback used by default and in tests.
- `openai`: uses the official OpenAI Python SDK with structured output where available.
- `bedrock`: uses AWS Bedrock Runtime locally via `boto3` and validates returned JSON through the same Pydantic schema.

Tests do not make real OpenAI or Bedrock calls. Bedrock support is an API-layer refactor only; no AWS deployment, S3 storage, RAG, IAM design, or production security wrapper is included yet.


## Stage 5B Document Handling

The backend now stores uploaded PDFs through a document store abstraction before analysis. This prepares the project for secure commercial document handling without adding AWS deployment, RAG, auth, a database, OCR, or report export.

Document store providers live under `app/document_store/`:

- `local`: default development store. Files are saved under `backend/.local_documents/`, which is ignored by git.
- `s3`: scaffold for later secure AWS use. It uses `boto3` S3 client, supports KMS server-side encryption when `KMS_KEY_ID` is configured, and stores only non-sensitive object metadata.

Configuration:

```bash
DOCUMENT_STORE_PROVIDER=local
LOCAL_DOCUMENT_DIR=.local_documents
S3_BUCKET_NAME=
S3_PREFIX=spa-commercial-agent-poc/
KMS_KEY_ID=
DOCUMENT_RETENTION_POLICY=local_dev_delete_manually
```

`/analyze` returns non-sensitive `document_metadata` with document id, sanitized filename, content type, size, checksum, storage provider, created timestamp, encryption status, and retention policy. Local filesystem paths and extracted contract text are not exposed in the API response metadata.

Safety notes:

- Raw PDF bytes are not logged.
- Extracted contract text is not logged or stored in document metadata.
- API keys, prompts, storage paths, and stack traces are not exposed in error responses.
- Local storage is for development only; S3/KMS is scaffolded for a later secure AWS stage.


## Stage 5C Local RAG Ingestion

The backend now includes a local, deterministic RAG ingestion foundation under `app/rag/`. This is not connected to `/analyze` yet. It prepares the project for future production RAG, such as Amazon Bedrock Knowledge Bases, while staying local and testable.

Knowledge libraries include contract references, internal procedures, valuation methodology, market fundamentals, portfolio strategy, good/bad/corrected analysis examples, reviewer feedback, taxonomy guidance, model input mapping rules, negotiation playbooks, glossary terms, risk policy, and other approved references.

Each ingested item carries metadata such as title, knowledge type, source filename/document id, version, effective date, owner, confidentiality, approval status, jurisdiction, commodity, contract type, deal type, analysis section, quality label, tags, approval flag, warnings, and created timestamp. Raw source text is not stored in metadata; chunk text is stored only in the local RAG index.

Local config:

```bash
RAG_PROVIDER=local
LOCAL_RAG_DIR=.local_rag
RAG_DEFAULT_CHUNK_SIZE=1200
RAG_DEFAULT_CHUNK_OVERLAP=150
RAG_REQUIRE_APPROVED_FOR_RAG=true
BEDROCK_KNOWLEDGE_BASE_ID=
BEDROCK_KNOWLEDGE_BASE_REGION=
```

Local dev endpoints:

- `POST /rag/ingest-text`: accepts text and metadata, chunks it, and writes to the local JSONL index.
- `POST /rag/retrieve`: deterministic keyword retrieval with metadata filters.
- `GET /rag/knowledge`: metadata-only listing of ingested knowledge documents.

Example ingest payload:

```json
{
  "text": "Pricing formula guidance should map clauses to model input candidates only.",
  "metadata": {
    "title": "Pricing Input Mapping Rule",
    "knowledge_type": "model_input_mapping_rule",
    "approval_status": "approved",
    "approved_for_rag": true,
    "commodity": "lng",
    "contract_type": "spa",
    "analysis_section": "valuation_input_pack",
    "tags": ["pricing", "model-inputs"]
  }
}
```

Example retrieval payload:

```json
{
  "query": "pricing formula model input",
  "filters": {"knowledge_type": "model_input_mapping_rule", "commodity": "lng"},
  "top_k": 5
}
```

Bad analysis examples are retrievable for critique/comparison but return warnings. Draft, deprecated, superseded, or unapproved material also returns warnings and may be rejected at ingestion when `RAG_REQUIRE_APPROVED_FOR_RAG=true`.

Stage 5C does not call external embedding APIs, OpenAI, Bedrock, Bedrock Knowledge Bases, AWS services, databases, or vector stores. It does not inject retrieval into `/analyze`.

## Stage 5D RAG-Aware Analysis

`/analyze` can now use local RAG guidance when explicitly enabled with `RAG_ENABLED=true`. RAG remains disabled by default, so the Stage 5A/5B/5C behavior is preserved unless opted in.

RAG guidance is methodology context only. The uploaded contract text remains the only source of contractual truth. The prompt and response summary both state that RAG must not be used as evidence that a clause exists. RAG can improve classification, valuation input mapping, optionality framing, risk warnings, assumptions, and recommendation structure.

Analysis RAG config:

```bash
RAG_ENABLED=false
RAG_TOP_K=5
RAG_ANALYSIS_SECTIONS=pricing,valuation_input_pack,optionality,risk,recommendation
RAG_ALLOWED_KNOWLEDGE_TYPES=internal_procedure,valuation_methodology,market_fundamentals,portfolio_strategy,good_analysis_example,corrected_analysis_example,reviewer_feedback,taxonomy_guidance,model_input_mapping_rule,negotiation_playbook,glossary,risk_policy
```

When enabled, the pipeline builds focused local keyword queries, retrieves approved chunks from `.local_rag`, deduplicates them, filters to allowed knowledge types, passes a compact guidance block to the selected LLM provider, and attaches a non-sensitive `rag_context_summary` to the response. The summary includes citation-style metadata and excerpts, not the full prompt.

Bad analysis examples are excluded from analysis context by default. Draft, deprecated, superseded, or unapproved materials are excluded or warning-marked according to metadata and config. This stage does not add embeddings, Bedrock Knowledge Bases, external retrieval, auth, a database, or production access controls.

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


## Stage 4 Optionality Register

The response includes a structured `optionality_register` for embedded contractual options and flexibilities. It identifies possible rights such as destination flexibility, volume flexibility, timing flexibility, price reopeners, make-up rights, carry-forward rights, take-or-pay downside mechanics, termination rights, credit support effects, and operational flexibility.

Each optionality item can include:

- option type
- source provision IDs
- source clause reference
- extracted contractual right
- inferred economic logic
- suggested valuation method
- required market data
- required operational data
- required portfolio data
- required analyst assumptions
- value drivers, risks, constraints, confidence, evidence status, and warnings

Suggested valuation methods are only method labels, such as `scenario_analysis`, `spread_option`, `swing_option`, `deferral_option`, `make_up_value`, `termination_downside_protection`, `credit_risk_adjustment`, `operational_constraint_analysis`, `analyst_judgement_required`, or `insufficient_evidence`.

Stage 4 does not calculate option value or any other quantitative result. It only identifies optionality and the method/data that a later analyst workflow might need.



## Stage 7B Manual Scenario NPV Calculator

The backend exposes `POST /calculators/npv`, a deterministic calculator for manually entered scenario assumptions. It does not call LLMs, RAG, live market data, document storage, or external services.

Supported roles are `buyer` and `seller`. Supported delivery bases are `des`, `fob`, `ex_ship`, `delivered`, `free_on_board`, and `unclear`. Scenario names are `base`, `upside`, `downside`, and `stress`.

The calculator applies simple annual margin formulas:

- Buyer FOB/free-on-board: market price minus contract price minus freight, boil-off, port/canal, regas/terminal, downstream, and other costs.
- Buyer DES/ex-ship/delivered: market price minus contract price minus regas/terminal, downstream, and other costs.
- Seller FOB/free-on-board: contract price minus supply cost, port/canal cost, and other costs.
- Seller DES/ex-ship/delivered: contract price minus supply, freight, boil-off, port/canal, regas/terminal, downstream, and other costs.

Annual cash flow equals annual unit margin times annual volume minus annual fixed costs. NPV discounts that flat annual cash flow over the entered contract years, with optional midyear discounting. Missing optional costs default to zero and are warning-marked.

Limitations: all numbers are manual assumptions; no live market data is used; no optionality value is included; outputs are preliminary and require analyst validation.

## Stage 7A Commercial Model Framework

The backend now adds deterministic `analysis_model_outputs` after extraction, taxonomy coverage, valuation input mapping, and optionality routing. This framework does not call an LLM and does not calculate value. It determines the future commercial model route and the missing inputs required before a later manual scenario NPV calculator can be used.

Outputs include:

- `deal_structure`: buyer/seller/swap/tolling/portfolio role, DES/FOB/delivered basis, origin, destination, title/risk transfer, and logistics responsibility where supported.
- `npv_readiness`: whether enough contract, market, logistics, portfolio, and manual assumptions exist to calculate later. `can_calculate_npv_now` remains false in this stage unless all critical inputs are supplied and validated.
- `landed_value_or_netback`: deterministic model selector for DES purchase, FOB purchase, DES sale, FOB sale, netback, landed cost, or unclear.
- `scenario_model_requirements`: base, upside, downside, stress, sensitivity, and break-even input requirements.
- `optionality_model_routing`: maps embedded options to future methods such as spread option, swing option, make-up value, scenario analysis, credit risk adjustment, or operational constraint analysis.
- `portfolio_impact_requirements`: portfolio exposure, concentration, hedge, liquidity, operational capacity, and risk appetite inputs needed before portfolio impact can be assessed.

DES/FOB logic is evidence-constrained. DES/ex-ship/delivered terms route toward destination value and terminal/downstream assumptions. FOB/free-on-board terms route toward origin/loading port, destination, freight, boil-off, port/canal, shipping duration, and terminal assumptions. If role, basis, origin, or destination are unclear, the framework marks them unclear and requests analyst validation.

Stage 7A does not calculate NPV, IRR, fair value, quantitative option valuation, expected profit, margin, trade P&L, or investment conclusions.

## Tests

```bash
pytest -q
```

No test requires a real OpenAI API call.

## Stage 4 Limitations

- Text extraction only supports embedded PDF text. Scanned PDFs require OCR in a later stage.
- The OpenAI analysis is a first-pass extraction and commercial interpretation workflow, not legal advice.
- No final valuation, DCF model, NPV, IRR, option value, fair value, expected profit, margin, trade P&L, quantitative option valuation, or portfolio optimization is performed.
- Market and portfolio conclusions require manual assumptions unless those assumptions are supplied in the uploaded document.
- Clause coverage is evidence-constrained and depends on the quality of extracted PDF text.
- Local document storage is for development only and must be replaced with a production retention, encryption, and access-control design before real sensitive use.
- No database, auth, deployment, Docker, report export, vector embeddings, Bedrock Knowledge Bases, production RAG service, or multi-agent orchestration is included.
