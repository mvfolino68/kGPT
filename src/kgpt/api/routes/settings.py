"""Settings API routes - simplified to OpenAI-only with Exa and Cohere support."""

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
    db_value: str | None = db.get_setting(key)
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
    llm_model = get_setting_with_fallback(db, "llm_model", settings.openai_model)
    embedding_provider = get_setting_with_fallback(
        db, "embedding_provider", settings.embedding_provider.value
    )
    embedding_model = get_setting_with_fallback(db, "embedding_model", settings.embedding_model)

    # Get web search enabled setting
    web_search_setting = db.get_setting("web_search_enabled")
    if web_search_setting is None:
        web_search_enabled = settings.web_search_enabled
    elif isinstance(web_search_setting, bool):
        web_search_enabled = web_search_setting
    elif isinstance(web_search_setting, str):
        web_search_enabled = web_search_setting.lower() == "true"
    else:
        web_search_enabled = True

    # Get key status with source information
    openai_key = get_key_status(db, "openai_api_key", settings.openai_api_key)
    exa_key = get_key_status(db, "exa_api_key", settings.exa_api_key)
    cohere_key = get_key_status(db, "cohere_api_key", settings.cohere_api_key)
    huggingface_token = get_key_status(db, "huggingface_token", None)  # HF only from DB

    return SettingsResponse(
        llm_provider="openai",
        llm_model=llm_model or "gpt-4o",
        embedding_provider=embedding_provider or "fastembed",
        embedding_model=embedding_model or "BAAI/bge-small-en-v1.5",
        qdrant_url=settings.qdrant_url,
        qdrant_collection=settings.qdrant_collection,
        web_search_enabled=web_search_enabled,
        # Key status
        openai_key=openai_key,
        exa_key=exa_key,
        cohere_key=cohere_key,
        huggingface_token=huggingface_token,
        # Legacy fields
        has_openai_key=openai_key.configured,
        has_exa_key=exa_key.configured,
        has_cohere_key=cohere_key.configured,
        has_huggingface_token=huggingface_token.configured,
    )


@router.put("", response_model=SettingsResponse)
async def update_settings(request: SettingsUpdateRequest) -> SettingsResponse:
    """Update application settings."""
    db = get_db()

    # Update LLM model
    if request.llm_model is not None:
        db.set_setting("llm_model", request.llm_model)
        logger.info(f"Updated LLM model to: {request.llm_model}")

    # Update embedding settings
    if request.embedding_provider is not None:
        db.set_setting("embedding_provider", request.embedding_provider)

    if request.embedding_model is not None:
        db.set_setting("embedding_model", request.embedding_model)

    # Update web search setting
    if request.web_search_enabled is not None:
        db.set_setting("web_search_enabled", str(request.web_search_enabled).lower())
        logger.info(f"Updated web search enabled to: {request.web_search_enabled}")

    # Store API keys securely
    if request.openai_api_key is not None:
        db.set_setting("openai_api_key", request.openai_api_key)
        logger.info("Updated OpenAI API key")

    if request.exa_api_key is not None:
        db.set_setting("exa_api_key", request.exa_api_key)
        logger.info("Updated Exa API key")

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
            request.huggingface_token is not None,
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
    effective_key: str | None = api_key
    if api_key == "__USE_STORED__":
        if provider == "openai":
            effective_key = get_effective_key(db, "openai_api_key", settings.openai_api_key)

        if not effective_key:
            return ValidateKeyResponse(
                valid=False,
                provider=provider,
                message="No API key configured",
            )

    try:
        if provider == "openai" and effective_key:
            return await _validate_openai_key(effective_key)
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
                        or m["id"].startswith("o4")
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


@router.get("/models/{provider}")
async def get_available_models(provider: str) -> dict:
    """Get available models for a provider."""
    from kgpt.llm import get_available_models

    db = get_db()

    if provider != "openai":
        return {"provider": provider, "models": [], "error": f"Unknown provider: {provider}"}

    # Get API key from DB or env
    api_key = get_effective_key(db, "openai_api_key", settings.openai_api_key)

    if not api_key:
        return {
            "provider": provider,
            "models": [],
            "error": "No API key configured",
            "needs_key": True,
        }

    models = get_available_models()
    return {"provider": provider, "models": models}


@router.post("/models/refresh")
async def refresh_models() -> dict:
    """Refresh the cached model lists."""
    # No caching in simplified version
    return {"status": "ok"}
