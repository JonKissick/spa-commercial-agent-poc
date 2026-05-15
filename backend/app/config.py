from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()


class Settings(BaseSettings):
    app_name: str = "SPA Commercial Evaluation Agent"
    allowed_origins: str = "http://localhost:3000"
    llm_provider: str = "mock"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1"
    aws_region: str | None = None
    bedrock_model_id: str | None = None
    max_contract_chars: int = 120000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
