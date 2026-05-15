# Frontend

Next.js frontend for the SPA Commercial Evaluation Agent POC.

## Setup

```bash
npm install
```

## Run

```bash
npm run dev
```

The app will be available at `http://localhost:3000`.

Set `NEXT_PUBLIC_API_BASE_URL` if the backend is not running on `http://localhost:8000`.

## Stage 7A Commercial Model Outputs

The Analyze Contract tab displays backend `analysis_model_outputs`, including deal structure, NPV readiness, landed value/netback logic, scenario requirements, optionality model routing, portfolio impact requirements, and commercial model warnings. These outputs identify model route and missing inputs only; no NPV or valuation result is calculated.
