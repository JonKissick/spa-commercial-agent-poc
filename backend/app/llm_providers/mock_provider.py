from app.schemas import CommercialEvaluationResponse


class MockProvider:
    provider_name = "mock"

    def analyze_contract(self, contract_text: str, rag_context: str | None = None) -> CommercialEvaluationResponse:
        # Lazy import avoids a circular dependency while keeping the Stage 1-4 mock response stable.
        from app.analysis_pipeline import _build_mock_response

        return _build_mock_response(contract_text)
