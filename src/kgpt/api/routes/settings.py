"""Settings API routes."""

from fastapi import APIRouter
from loguru import logger

from kgpt.api.schemas import SettingsResponse, SettingsUpdateRequest
from kgpt.config import settings
from kgpt.db import get_db
from kgpt.vectorstore import reset_vectorstore

router = APIRouter(prefix="/settings", tags=["settings"])


def get_setting_with_fallback(db, key: str, env_value: str | None) -> str | None:
    """Get setting from DB first, fall back to env."""
    db_value = db.get_setting(key)
    if db_value:
        return db_value
    return env_value


@router.get("", response_model=SettingsResponse)
async def get_settings() -> SettingsResponse:
    """Get current application settings."""
    db = get_db()

    # Get provider settings (DB overrides env)
    llm_provider = get_setting_with_fallback(db, "llm_provider", settings.llm_provider.value)
    llm_model = get_setting_with_fallback(db, "llm_model", settings.llm_model)
    embedding_provider = get_setting_with_fallback(
        db, "embedding_provider", settings.embedding_provider.value
    )
    embedding_model = get_setting_with_fallback(db, "embedding_model", settings.embedding_model)
    ollama_host = get_setting_with_fallback(db, "ollama_host", settings.ollama_host)

    # Check for API keys (in DB or env)
    has_openai = bool(db.get_setting("openai_api_key") or settings.openai_api_key)
    has_anthropic = bool(db.get_setting("anthropic_api_key") or settings.anthropic_api_key)
    has_openrouter = bool(db.get_setting("openrouter_api_key") or settings.openrouter_api_key)
    has_cohere = bool(db.get_setting("cohere_api_key") or settings.cohere_api_key)
    has_huggingface = bool(db.get_setting("huggingface_token"))

    return SettingsResponse(
        llm_provider=llm_provider,
        llm_model=llm_model,
        embedding_provider=embedding_provider,
        embedding_model=embedding_model,
        qdrant_url=settings.qdrant_url,
        qdrant_collection=settings.qdrant_collection,
        ollama_host=ollama_host,
        has_openai_key=has_openai,
        has_anthropic_key=has_anthropic,
        has_openrouter_key=has_openrouter,
        has_cohere_key=has_cohere,
        has_huggingface_token=has_huggingface,
    )


@router.put("", response_model=SettingsResponse)
async def update_settings(request: SettingsUpdateRequest) -> SettingsResponse:
    """Update application settings."""
    db = get_db()

    # Update only provided fields
    if request.llm_provider is not None:
        db.set_setting("llm_provider", request.llm_provider)
        logger.info(f"Updated LLM provider to: {request.llm_provider}")

    if request.llm_model is not None:
        db.set_setting("llm_model", request.llm_model)
        logger.info(f"Updated LLM model to: {request.llm_model}")

    if request.embedding_provider is not None:
        db.set_setting("embedding_provider", request.embedding_provider)

    if request.embedding_model is not None:
        db.set_setting("embedding_model", request.embedding_model)

    if request.ollama_host is not None:
        db.set_setting("ollama_host", request.ollama_host)

    # Store API keys securely
    if request.openai_api_key is not None:
        db.set_setting("openai_api_key", request.openai_api_key)
        logger.info("Updated OpenAI API key")

    if request.anthropic_api_key is not None:
        db.set_setting("anthropic_api_key", request.anthropic_api_key)
        logger.info("Updated Anthropic API key")

    if request.openrouter_api_key is not None:
        db.set_setting("openrouter_api_key", request.openrouter_api_key)
        logger.info("Updated OpenRouter API key")

    if request.cohere_api_key is not None:
        db.set_setting("cohere_api_key", request.cohere_api_key)
        logger.info("Updated Cohere API key")

    if request.huggingface_token is not None:
        db.set_setting("huggingface_token", request.huggingface_token)
        logger.info("Updated Hugging Face token")

    # Clear vectorstore cache if embedding settings changed
    if any(
        [
            request.embedding_provider is not None,
            request.embedding_model is not None,
            request.openai_api_key is not None,
            request.cohere_api_key is not None,
            request.huggingface_token is not None,
            request.ollama_host is not None,
        ]
    ):
        reset_vectorstore()
        logger.info("Cleared vectorstore cache due to embedding-related settings change")

    # Return updated settings
    return await get_settings()


@router.get("/models/{provider}")
async def get_available_models(provider: str) -> dict:
    """Get available models for a provider."""
    from kgpt.config import LLMProvider
    from kgpt.llm import get_available_models

    try:
        provider_enum = LLMProvider(provider)
        db = get_db()

        # Get API key from DB if available
        api_key = None
        if provider == "openai":
            api_key = db.get_setting("openai_api_key") or settings.openai_api_key
        elif provider == "openrouter":
            api_key = db.get_setting("openrouter_api_key") or settings.openrouter_api_key

        models = get_available_models(provider_enum, api_key=api_key, use_cache=False)
        return {"provider": provider, "models": models}

    except ValueError:
        return {"provider": provider, "models": [], "error": f"Unknown provider: {provider}"}


@router.post("/models/refresh")
async def refresh_models() -> dict:
    """Refresh the cached model lists."""
    from kgpt.llm import clear_models_cache

    clear_models_cache()
    return {"status": "cache_cleared"}
