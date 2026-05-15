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
    document_store_provider: str = "local"
    local_document_dir: str = ".local_documents"
    s3_bucket_name: str | None = None
    s3_prefix: str = "spa-commercial-agent-poc/"
    kms_key_id: str | None = None
    document_retention_policy: str = "local_dev_delete_manually"
    rag_provider: str = "local"
    local_rag_dir: str = ".local_rag"
    rag_default_chunk_size: int = 1200
    rag_default_chunk_overlap: int = 150
    rag_require_approved_for_rag: bool = True
    bedrock_knowledge_base_id: str | None = None
    bedrock_knowledge_base_region: str | None = None
    rag_enabled: bool = False
    rag_top_k: int = 5
    rag_analysis_sections: str = "pricing,valuation_input_pack,optionality,risk,recommendation"
    rag_allowed_knowledge_types: str = "internal_procedure,valuation_methodology,market_fundamentals,portfolio_strategy,good_analysis_example,corrected_analysis_example,reviewer_feedback,taxonomy_guidance,model_input_mapping_rule,negotiation_playbook,glossary,risk_policy"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def rag_sections(self) -> list[str]:
        return [section.strip() for section in self.rag_analysis_sections.split(",") if section.strip()]

    @property
    def rag_allowed_types(self) -> list[str]:
        return [item.strip() for item in self.rag_allowed_knowledge_types.split(",") if item.strip()]

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
