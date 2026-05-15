from app.llm_providers.base import LLMProviderConfigurationError, LLMProviderError, LLMProviderSchemaError
from app.llm_providers.openai_provider import OpenAIProvider
from app.schemas import CommercialEvaluationResponse


class MissingAPIKeyError(RuntimeError):
    pass


class AIClientError(RuntimeError):
    pass


class AISchemaError(AIClientError):
    pass


class AIClient:
    """Backward-compatible wrapper around the OpenAI provider.

    New pipeline code should use app.llm_providers.factory.create_llm_provider.
    """

    def __init__(self, api_key: str | None, model: str) -> None:
        self.provider = OpenAIProvider(api_key=api_key, model=model)

    def analyze_contract_text(self, contract_text: str, rag_context: str | None = None) -> CommercialEvaluationResponse:
        try:
            return self.provider.analyze_contract(contract_text, rag_context=rag_context)
        except LLMProviderConfigurationError as exc:
            raise MissingAPIKeyError(str(exc)) from exc
        except LLMProviderSchemaError as exc:
            raise AISchemaError(str(exc)) from exc
        except LLMProviderError as exc:
            raise AIClientError(str(exc)) from exc
