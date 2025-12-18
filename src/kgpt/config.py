"""Configuration management using Pydantic Settings."""

from enum import Enum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"


class EmbeddingProvider(str, Enum):
    """Supported embedding providers."""

    OPENAI = "openai"
    FASTEMBED = "fastembed"
    OLLAMA = "ollama"
    COHERE = "cohere"


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application settings
    app_name: str = "kGPT"
    app_version: str = "2.0.0"
    debug: bool = False
    data_dir: Path = Field(default=Path("data"))

    # LLM settings
    llm_provider: LLMProvider = LLMProvider.OPENROUTER
    llm_model: str = "openai/gpt-4o-mini"
    llm_temperature: float = 0.0

    # OpenAI settings
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o"

    # Anthropic settings
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-7-sonnet-20250219"

    # OpenRouter settings
    openrouter_api_key: str | None = None
    openrouter_model: str = "anthropic/claude-3.7-sonnet"

    # Ollama settings
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.3"

    # Embedding settings
    embedding_provider: EmbeddingProvider = EmbeddingProvider.OPENAI
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Cohere settings
    cohere_api_key: str | None = None

    # Qdrant settings
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "kgpt_docs"

    # Database settings
    database_path: Path = Field(default=Path("data/kgpt.db"))

    # Kafka settings (optional cluster connection)
    kafka_bootstrap_servers: str | None = None
    kafka_security_protocol: str = "PLAINTEXT"
    kafka_sasl_mechanism: str | None = None
    kafka_sasl_username: str | None = None
    kafka_sasl_password: str | None = None

    def ensure_data_dir(self) -> Path:
        """Ensure data directory exists and return it."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir

    def get_database_path(self) -> Path:
        """Get database path, ensuring parent directory exists."""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        return self.database_path


# Global settings instance
settings = Settings()
