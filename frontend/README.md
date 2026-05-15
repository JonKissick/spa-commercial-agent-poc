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

## Stage 7C Analysis-to-NPV Prefill

The Analyze Contract tab can now send the latest analysis result to the NPV Calculator through `Use in NPV Calculator`. The NPV Calculator also has an `Apply prefill` panel that reads the latest analysis result.

Prefill only suggests structural fields such as buyer/seller role, DES/FOB delivery basis, currency when clearly available, unit defaults, and scenario notes. It does not calculate NPV, does not use AI or RAG for valuation, and does not automatically populate pricing, volume, market price, freight, discount rate, or cost assumptions.

Analysts must review and confirm all assumptions before pressing `Calculate Scenario NPVs`. If role or delivery basis is unclear or low-confidence, the UI warning-marks the prefill and requires manual selection.

## Stage 7D Sensitivities and Break-even Tables

The NPV Calculator tab now includes sensitivity settings for market price, contract price, freight cost, and discount rate shifts. Results display simple tables grouped by scenario and variable.

The tab also displays break-even outputs by scenario. These outputs use flat annual margin assumptions and manual inputs only. No charts, stochastic simulation, live market data, AI/RAG calculation, or quantitative optionality value is included.
