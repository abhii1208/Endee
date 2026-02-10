from functools import lru_cache
from pydantic import BaseSettings, AnyHttpUrl, Field
from typing import Optional


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables or a .env file.
    """

    app_name: str = "Endee Support Copilot"
    environment: str = Field("local", description="Environment name (local/dev/prod)")

    endee_base_url: AnyHttpUrl = Field(
        "http://localhost:8080/api/v1",
        description="Base URL for Endee server, including /api/v1 prefix",
    )
    endee_auth_token: str = Field(
        "",
        description="Optional auth token for Endee; leave empty for open mode",
    )
    endee_index_name: str = Field(
        "support_knowledge",
        description="Primary Endee index name for support content",
    )

    embedding_model_name: str = Field(
        "sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace / sentence-transformers model name",
    )

    llm_provider: str = Field(
        "openai",
        description="LLM provider identifier (e.g. 'openai'); unused if llm_api_key is empty",
    )
    llm_model: str = Field(
        "gpt-4o-mini",
        description="LLM model name for answer generation",
    )
    llm_api_key: Optional[str] = Field(
        default=None,
        description="API key for the configured LLM provider. If unset, LLM is disabled.",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Cached accessor for application settings.
    """

    return Settings()

