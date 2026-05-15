from typing import Protocol

from app.schemas import CommercialEvaluationResponse


class LLMProviderError(RuntimeError):
    pass


class LLMProviderConfigurationError(LLMProviderError):
    pass


class LLMProviderSchemaError(LLMProviderError):
    pass


class LLMProvider(Protocol):
    def analyze_contract(self, contract_text: str, rag_context: str | None = None) -> CommercialEvaluationResponse:
        ...
