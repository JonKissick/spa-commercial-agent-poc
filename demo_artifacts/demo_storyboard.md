# Demo Storyboard

1. Load the local workbench and confirm system status is mock/local.
2. Review `samples/synthetic_lng_spa_terms.md` as approved synthetic input material.
3. Upload a text-based PDF version of synthetic terms or use mocked extraction in local tests.
4. Inspect clause coverage, valuation input pack, optionality register, portfolio requirements, and recommendation memo.
5. Run the manual NPV calculator with `samples/synthetic_npv_request.json`.
6. Export the draft Excel workbook from `POST /calculators/npv/workbook`.
7. Generate draft board-paper content through `POST /agents/board-paper/draft`.
8. Generate the five-slide management pack through `POST /agents/management-slides/draft`.
9. Close with known limitations: synthetic data only, no production access, no external Bedrock call, no legal or financial reliance without human review.
