"""Settings API routes."""

from fastapi import APIRouter
from loguru import logger

from kgpt.api.schemas import (
    KeyStatus,
    SettingsResponse,
    SettingsUpdateRequest,
    ValidateKeyRequest,
    ValidateKeyResponse,
)
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


def get_key_status(db, db_key: str, env_value: str | None) -> KeyStatus:
    """Get the status of an API key including its source."""
    db_value = db.get_setting(db_key)

    if db_value:
        return KeyStatus(configured=True, source="db", valid=None)
    elif env_value:
        return KeyStatus(configured=True, source="env", valid=None)
    else:
        return KeyStatus(configured=False, source=None, valid=None)


def get_effective_key(db, db_key: str, env_value: str | None) -> str | None:
    """Get the effective API key (DB takes priority over env)."""
    return db.get_setting(db_key) or env_value


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

    # Get key status with source information
    openai_key = get_key_status(db, "openai_api_key", settings.openai_api_key)
    anthropic_key = get_key_status(db, "anthropic_api_key", settings.anthropic_api_key)
    openrouter_key = get_key_status(db, "openrouter_api_key", settings.openrouter_api_key)
    cohere_key = get_key_status(db, "cohere_api_key", settings.cohere_api_key)
    huggingface_token = get_key_status(db, "huggingface_token", None)  # HF only from DB

    return SettingsResponse(
        llm_provider=llm_provider,
        llm_model=llm_model,
        embedding_provider=embedding_provider,
        embedding_model=embedding_model,
        qdrant_url=settings.qdrant_url,
        qdrant_collection=settings.qdrant_collection,
        ollama_host=ollama_host,
        # New detailed key status
        openai_key=openai_key,
        anthropic_key=anthropic_key,
        openrouter_key=openrouter_key,
        cohere_key=cohere_key,
        huggingface_token=huggingface_token,
        # Legacy fields for backwards compatibility
        has_openai_key=openai_key.configured,
        has_anthropic_key=anthropic_key.configured,
        has_openrouter_key=openrouter_key.configured,
        has_cohere_key=cohere_key.configured,
        has_huggingface_token=huggingface_token.configured,
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


@router.post("/validate-key", response_model=ValidateKeyResponse)
async def validate_api_key(request: ValidateKeyRequest) -> ValidateKeyResponse:
    """Validate an API key and return available models if valid."""
    provider = request.provider.lower()
    api_key = request.api_key
    db = get_db()

    # Handle special value to use stored key
    if api_key == "__USE_STORED__":
        if provider == "openai":
            api_key = get_effective_key(db, "openai_api_key", settings.openai_api_key)
        elif provider == "anthropic":
            api_key = get_effective_key(db, "anthropic_api_key", settings.anthropic_api_key)
        elif provider == "openrouter":
            api_key = get_effective_key(db, "openrouter_api_key", settings.openrouter_api_key)

        if not api_key:
            return ValidateKeyResponse(
                valid=False,
                provider=provider,
                message="No API key configured",
            )

    try:
        if provider == "openai":
            return await _validate_openai_key(api_key)
        elif provider == "anthropic":
            return await _validate_anthropic_key(api_key)
        elif provider == "openrouter":
            return await _validate_openrouter_key(api_key)
        elif provider == "ollama":
            return await _validate_ollama(host=request.ollama_host)
        else:
            return ValidateKeyResponse(
                valid=False,
                provider=provider,
                message=f"Unknown provider: {provider}",
            )
    except Exception as e:
        logger.error(f"Error validating {provider} key: {e}")
        return ValidateKeyResponse(
            valid=False,
            provider=provider,
            message=str(e),
        )


async def _validate_openai_key(api_key: str) -> ValidateKeyResponse:
    """Validate OpenAI API key by fetching models."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )

            if response.status_code == 200:
                data = response.json()
                # Heuristic: surface likely chat-capable models without hardcoding a fixed list.
                # Prefer "newest first" using the provider's timestamps, then fall back to ids.
                raw = [m for m in data.get("data", []) if isinstance(m, dict)]
                chat_like = [
                    m
                    for m in raw
                    if isinstance(m.get("id"), str)
                    and (
                        m["id"].startswith("gpt-")
                        or m["id"].startswith("o1")
                        or m["id"].startswith("o3")
                        or m["id"].startswith("chatgpt-")
                    )
                ]
                chosen = chat_like or raw
                chosen.sort(key=lambda m: int(m.get("created") or 0), reverse=True)
                models = []
                seen = set()
                for m in chosen:
                    mid = m.get("id")
                    if isinstance(mid, str) and mid and mid not in seen:
                        seen.add(mid)
                        models.append(mid)

                return ValidateKeyResponse(
                    valid=True,
                    provider="openai",
                    message="API key is valid",
                    models=models[:50],  # keep UI usable
                )
            elif response.status_code == 401:
                return ValidateKeyResponse(
                    valid=False,
                    provider="openai",
                    message="Invalid API key",
                )
            else:
                return ValidateKeyResponse(
                    valid=False,
                    provider="openai",
                    message=f"API error: {response.status_code}",
                )
    except httpx.TimeoutException:
        return ValidateKeyResponse(
            valid=False,
            provider="openai",
            message="Request timed out",
        )
    except Exception as e:
        return ValidateKeyResponse(
            valid=False,
            provider="openai",
            message=f"Connection error: {str(e)}",
        )


async def _validate_anthropic_key(api_key: str) -> ValidateKeyResponse:
    """Validate Anthropic API key by fetching available models."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Prefer the official models listing endpoint so the UI always reflects what's available.
            response = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
            )

            # 200 means valid, 401 means invalid key
            if response.status_code == 200:
                data = response.json()
                raw = [m for m in data.get("data", []) if isinstance(m, dict)]
                # created_at is ISO8601; lexicographic sort works for full timestamps
                raw.sort(key=lambda m: str(m.get("created_at") or ""), reverse=True)
                models = []
                seen = set()
                for m in raw:
                    mid = m.get("id")
                    if isinstance(mid, str) and mid and mid not in seen:
                        seen.add(mid)
                        models.append(mid)
                return ValidateKeyResponse(
                    valid=True,
                    provider="anthropic",
                    message="API key is valid",
                    models=models[:50],
                )
            elif response.status_code == 401:
                return ValidateKeyResponse(
                    valid=False,
                    provider="anthropic",
                    message="Invalid API key",
                )
            else:
                return ValidateKeyResponse(
                    valid=False,
                    provider="anthropic",
                    message=f"API error: {response.status_code}",
                )
    except httpx.TimeoutException:
        return ValidateKeyResponse(
            valid=False,
            provider="anthropic",
            message="Request timed out",
        )
    except Exception as e:
        return ValidateKeyResponse(
            valid=False,
            provider="anthropic",
            message=f"Connection error: {str(e)}",
        )


async def _validate_openrouter_key(api_key: str) -> ValidateKeyResponse:
    """Validate OpenRouter API key by fetching models."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )

            if response.status_code == 200:
                data = response.json()
                ids = [m.get("id") for m in data.get("data", []) if isinstance(m, dict)]
                ids = [m for m in ids if isinstance(m, str) and m]
                # Keep provider ordering if any; de-dupe without re-sorting.
                models = []
                seen = set()
                for mid in ids:
                    if mid not in seen:
                        seen.add(mid)
                        models.append(mid)
                return ValidateKeyResponse(
                    valid=True,
                    provider="openrouter",
                    message="API key is valid",
                    models=models[:50],
                )
            elif response.status_code == 401:
                return ValidateKeyResponse(
                    valid=False,
                    provider="openrouter",
                    message="Invalid API key",
                )
            else:
                return ValidateKeyResponse(
                    valid=False,
                    provider="openrouter",
                    message=f"API error: {response.status_code}",
                )
    except httpx.TimeoutException:
        return ValidateKeyResponse(
            valid=False,
            provider="openrouter",
            message="Request timed out",
        )
    except Exception as e:
        return ValidateKeyResponse(
            valid=False,
            provider="openrouter",
            message=f"Connection error: {str(e)}",
        )


async def _validate_ollama(host: str | None = None) -> ValidateKeyResponse:
    """Check if Ollama is available and get models."""
    import httpx

    db = get_db()
    ollama_host = host or db.get_setting("ollama_host") or settings.ollama_host

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ollama_host}/api/tags")

            if response.status_code == 200:
                data = response.json()
                raw = [m for m in data.get("models", []) if isinstance(m, dict)]
                raw.sort(key=lambda m: str(m.get("modified_at") or ""), reverse=True)
                models = [m["name"] for m in raw if isinstance(m.get("name"), str)]
                return ValidateKeyResponse(
                    valid=True,
                    provider="ollama",
                    message=f"Connected to Ollama at {ollama_host}",
                    models=models,
                )
            else:
                return ValidateKeyResponse(
                    valid=False,
                    provider="ollama",
                    message=f"Ollama returned error: {response.status_code}",
                )
    except Exception:
        return ValidateKeyResponse(
            valid=False,
            provider="ollama",
            message=f"Cannot connect to Ollama at {ollama_host}",
        )


@router.get("/models/{provider}")
async def get_available_models(provider: str) -> dict:
    """Get available models for a provider."""
    from kgpt.config import LLMProvider
    from kgpt.llm import get_available_models

    try:
        provider_enum = LLMProvider(provider)
        db = get_db()

        # Get API key from DB or env
        api_key = None
        if provider == "openai":
            api_key = get_effective_key(db, "openai_api_key", settings.openai_api_key)
        elif provider == "openrouter":
            api_key = get_effective_key(db, "openrouter_api_key", settings.openrouter_api_key)
        elif provider == "anthropic":
            api_key = get_effective_key(db, "anthropic_api_key", settings.anthropic_api_key)

        # Check if we have a key for providers that need one
        if provider in ["openai", "anthropic", "openrouter"] and not api_key:
            return {
                "provider": provider,
                "models": [],
                "error": "No API key configured",
                "needs_key": True,
            }

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
