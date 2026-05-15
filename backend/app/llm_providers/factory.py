from app.config import Settings
from app.llm_providers.base import LLMProvider, LLMProviderConfigurationError
from app.llm_providers.bedrock_provider import BedrockProvider
from app.llm_providers.mock_provider import MockProvider
from app.llm_providers.openai_provider import OpenAIProvider

VALID_LLM_PROVIDERS = {"mock", "openai", "bedrock"}


def create_llm_provider(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider.strip().lower()
    if provider == "mock":
        return MockProvider()
    if provider == "openai":
        if not settings.openai_api_key:
            return MockProvider()
        return OpenAIProvider(api_key=settings.openai_api_key, model=settings.openai_model)
    if provider == "bedrock":
        return BedrockProvider(region_name=settings.aws_region, model_id=settings.bedrock_model_id)
    raise LLMProviderConfigurationError(
        f"Unsupported LLM_PROVIDER '{settings.llm_provider}'. Expected one of: {', '.join(sorted(VALID_LLM_PROVIDERS))}."
    )
