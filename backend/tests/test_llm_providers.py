import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.analysis_pipeline import run_analysis_pipeline
from app.config import Settings, get_settings
from app.llm_providers.bedrock_provider import BedrockProvider
from app.llm_providers.factory import create_llm_provider
from app.llm_providers.mock_provider import MockProvider
from app.llm_providers.openai_provider import OpenAIProvider


SAMPLE_TEXT = "Sample SPA text with pricing, volume flexibility, destination flexibility, and credit support. " * 3


def test_default_provider_is_mock() -> None:
    settings = Settings()

    assert settings.llm_provider == "mock"
    assert isinstance(create_llm_provider(settings), MockProvider)


def test_openai_provider_selected_when_key_is_configured() -> None:
    settings = Settings(llm_provider="openai", openai_api_key="test-key", openai_model="gpt-test")

    provider = create_llm_provider(settings)

    assert isinstance(provider, OpenAIProvider)


def test_openai_missing_key_uses_mock_provider() -> None:
    settings = Settings(llm_provider="openai", openai_api_key=None)

    provider = create_llm_provider(settings)

    assert isinstance(provider, MockProvider)


def test_bedrock_provider_selected_without_network_call() -> None:
    settings = Settings(
        llm_provider="bedrock",
        aws_region="ap-southeast-2",
        bedrock_model_id="anthropic.claude-test",
    )

    provider = create_llm_provider(settings)

    assert isinstance(provider, BedrockProvider)


def test_pipeline_default_mock_does_not_require_real_llm(monkeypatch) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()

    response = run_analysis_pipeline(SAMPLE_TEXT)

    assert response.contract_summary
    assert response.clause_coverage
    assert response.optionality_register
