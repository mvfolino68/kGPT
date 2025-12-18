"""Tests for configuration module."""

from kgpt.config import EmbeddingProvider, LLMProvider, Settings


def test_default_settings():
    """Test default settings values."""
    settings = Settings()

    assert settings.app_name == "kGPT"
    assert settings.app_version == "2.0.0"
    assert settings.llm_provider == LLMProvider.OPENROUTER
    assert settings.embedding_provider == EmbeddingProvider.OPENAI


def test_llm_provider_enum():
    """Test LLM provider enum values."""
    assert LLMProvider.OPENAI.value == "openai"
    assert LLMProvider.ANTHROPIC.value == "anthropic"
    assert LLMProvider.OLLAMA.value == "ollama"
    assert LLMProvider.OPENROUTER.value == "openrouter"


def test_embedding_provider_enum():
    """Test embedding provider enum values."""
    assert EmbeddingProvider.OPENAI.value == "openai"
    assert EmbeddingProvider.FASTEMBED.value == "fastembed"
    assert EmbeddingProvider.OLLAMA.value == "ollama"
    assert EmbeddingProvider.COHERE.value == "cohere"
