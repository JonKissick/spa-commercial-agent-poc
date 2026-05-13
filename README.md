# SPA Commercial Evaluation Agent POC

This is a clean standalone proof of concept for an SPA Commercial Evaluation Agent. It is intentionally separate from any legal dashboard, prior agent project, deployment stack, or production valuation workflow.

## Purpose

The POC demonstrates the shape of an application that can accept a Sales and Purchase Agreement PDF, extract text, run a commercial evaluation pipeline, and return structured outputs for commercial review.

## Local Architecture

- `backend/`: FastAPI API, Pydantic schemas, PDF text extraction, placeholder AI client, validation helpers, and mock analysis pipeline.
- `frontend/`: Next.js single-page shell for uploading a PDF and displaying the structured evaluation response.

## What V1 Does

- Starts a FastAPI backend.
- Provides `GET /health`.
- Provides `POST /analyze` for multipart PDF uploads.
- Extracts PDF text using `pypdf`.
- Returns a strongly typed mock commercial evaluation response.
- Starts a Next.js frontend that uploads a PDF and renders the mock response.

## What V1 Deliberately Does Not Do

- No real OpenAI API calls.
- No full valuation calculation.
- No OCR.
- No database.
- No authentication.
- No AWS deployment.
- No Docker.
- No report export.

## Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.
