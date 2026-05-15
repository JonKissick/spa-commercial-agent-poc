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

## Stage 7B NPV Calculator

The workbench includes an `NPV Calculator` tab for manual scenario assumptions. Users can enter buyer/seller role, DES/FOB basis, discount rate, contract years, currency, unit, and base/upside/downside/stress inputs. The tab displays scenario NPVs, annual unit margin, annual cash flow, formulas, warnings, limitations, sensitivities, and break-even candidates.

The calculator uses manual assumptions only. It does not use AI, RAG, live market data, or quantitative optionality valuation. Results are preliminary and require analyst validation.
