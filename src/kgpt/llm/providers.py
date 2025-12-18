"""LLM and embedding provider configuration with LiteLLM and dynamic model discovery."""

import os

import httpx
import litellm
from langchain_community.chat_models import ChatLiteLLM
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from loguru import logger

from kgpt.config import EmbeddingProvider, LLMProvider, settings

# Configure LiteLLM
litellm.drop_params = True
litellm.telemetry = False


class FastEmbedEmbeddingsParallel(Embeddings):
    """Optimized FastEmbed wrapper with parallel processing for faster embeddings."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        batch_size: int = 256,
        parallel: int = 0,  # 0 = use all CPU cores
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        self.parallel = parallel
        self._model = None

    @property
    def model(self):
        """Lazy load the model."""
        if self._model is None:
            from fastembed import TextEmbedding

            logger.info(f"Loading FastEmbed model: {self.model_name} (parallel={self.parallel})")
            self._model = TextEmbedding(model_name=self.model_name)
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed documents using parallel processing."""
        if not texts:
            return []

        logger.info(
            f"Embedding {len(texts)} texts with batch_size={self.batch_size}, parallel={self.parallel}"
        )

        # FastEmbed's embed() returns a generator, we need to consume it
        embeddings = list(
            self.model.embed(
                texts,
                batch_size=self.batch_size,
                parallel=self.parallel,
            )
        )

        return [emb.tolist() for emb in embeddings]

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query."""
        embeddings = list(self.model.embed([text], batch_size=1))
        return embeddings[0].tolist()


def _get_db_setting(key: str, default: str | None = None) -> str | None:
    """Get a setting from the database, with fallback."""
    try:
        from kgpt.db import get_db

        db = get_db()
        value = db.get_setting(key)
        return value if value is not None else default
    except Exception:
        return default


# Default/fallback models per provider
DEFAULT_MODELS = {
    LLMProvider.OPENAI: ["gpt-4o", "gpt-4o-mini", "o3-mini", "o1-preview"],
    LLMProvider.ANTHROPIC: [
        "claude-3-7-sonnet-20250219",
        "claude-3-5-sonnet-latest",
        "claude-3-5-haiku-latest",
    ],
    LLMProvider.OLLAMA: ["llama3.3", "llama3.2", "mistral-small", "deepseek-r1:14b"],
    LLMProvider.OPENROUTER: [
        "anthropic/claude-3.7-sonnet",
        "google/gemini-2.0-flash-001",
        "deepseek/deepseek-chat",
        "openai/gpt-4o-mini",
    ],
}

# For backwards compatibility
AVAILABLE_MODELS = DEFAULT_MODELS

# Embedding model dimensions
EMBEDDING_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
    "BAAI/bge-small-en-v1.5": 384,
    "BAAI/bge-base-en-v1.5": 768,
    "snowflake/arctic-embed-m": 768,
    "nomic-embed-text": 768,
}


def get_structured_llm(
    provider: LLMProvider | None = None,
    model: str | None = None,
    temperature: float = 0,
) -> BaseChatModel:
    """
    Get a native LangChain LLM that supports structured output.

    Unlike ChatLiteLLM, native models like ChatOpenAI and ChatAnthropic
    support with_structured_output() for Pydantic models.
    """
    # Get provider from DB or env
    if provider is None:
        db_provider = _get_db_setting("llm_provider")
        if db_provider:
            provider = LLMProvider(db_provider)
        else:
            provider = settings.llm_provider

    # Get model from DB or env
    if model is None:
        model_name = _get_db_setting("llm_model", settings.llm_model) or "gpt-4o-mini"
    else:
        model_name = model

    # Get API keys from DB or env
    openai_key = _get_db_setting("openai_api_key", settings.openai_api_key)
    anthropic_key = _get_db_setting("anthropic_api_key", settings.anthropic_api_key)
    openrouter_key = _get_db_setting("openrouter_api_key", settings.openrouter_api_key)

    logger.info(f"Creating structured LLM: provider={provider}, model={model_name}")

    if provider == LLMProvider.OPENAI:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=openai_key or None,
        )
    elif provider == LLMProvider.ANTHROPIC:
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model_name=model_name,  # ChatAnthropic uses model_name, not model
            temperature=temperature,
            api_key=anthropic_key or "",
        )
    elif provider == LLMProvider.OPENROUTER:
        # OpenRouter is OpenAI-compatible
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=openrouter_key or None,
            base_url="https://openrouter.ai/api/v1",
        )
    else:
        # Fallback to ChatLiteLLM (won't support structured output)
        logger.warning(f"Provider {provider} may not support structured output")
        return get_llm(
            provider=provider, model=model_name, temperature=temperature, streaming=False
        )


def get_llm(
    provider: LLMProvider | None = None,
    model: str | None = None,
    temperature: float | None = None,
    streaming: bool = True,
    **kwargs,
) -> BaseChatModel:
    """
    Get an LLM instance using LiteLLM.

    Settings are read from DB first, then fall back to env vars.
    """
    # Get provider from DB or env
    if provider is None:
        db_provider = _get_db_setting("llm_provider")
        if db_provider:
            provider = LLMProvider(db_provider)
        else:
            provider = settings.llm_provider

    # Get model from DB or env
    if model is None:
        model_name = _get_db_setting("llm_model", settings.llm_model)
    else:
        model_name = model

    temp = temperature if temperature is not None else settings.llm_temperature

    # Ensure provider prefix for LiteLLM if not present
    full_model_name = model_name
    if "/" not in model_name:
        if provider == LLMProvider.OPENAI:
            full_model_name = f"openai/{model_name}"
        elif provider == LLMProvider.ANTHROPIC:
            full_model_name = f"anthropic/{model_name}"
        elif provider == LLMProvider.OLLAMA:
            full_model_name = f"ollama/{model_name}"
        # OpenRouter models already have provider prefix (e.g., "anthropic/claude-3.7-sonnet")
    elif provider == LLMProvider.OPENROUTER and not model_name.startswith("openrouter/"):
        # OpenRouter models need the openrouter/ prefix for LiteLLM
        full_model_name = f"openrouter/{model_name}"

    logger.info(f"Creating LLM: {full_model_name}")

    # Set API keys in environment for LiteLLM (DB first, then env)
    openai_key = _get_db_setting("openai_api_key", settings.openai_api_key)
    anthropic_key = _get_db_setting("anthropic_api_key", settings.anthropic_api_key)
    openrouter_key = _get_db_setting("openrouter_api_key", settings.openrouter_api_key)
    cohere_key = _get_db_setting("cohere_api_key", settings.cohere_api_key)

    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
    if anthropic_key:
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key
    if openrouter_key:
        os.environ["OPENROUTER_API_KEY"] = openrouter_key
    if cohere_key:
        os.environ["COHERE_API_KEY"] = cohere_key

    # Get Ollama host from DB or env
    ollama_host = _get_db_setting("ollama_host", settings.ollama_host)

    return ChatLiteLLM(
        model=full_model_name,
        temperature=temp,
        streaming=streaming,
        api_base=ollama_host if provider == LLMProvider.OLLAMA else None,
        **kwargs,
    )


def fetch_openai_models(api_key: str | None = None) -> list[str]:
    key = api_key or settings.openai_api_key
    if not key:
        return DEFAULT_MODELS[LLMProvider.OPENAI]
    try:
        response = httpx.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return sorted(
            [
                m["id"]
                for m in data["data"]
                if "gpt" in m["id"] or "o1" in m["id"] or "o3" in m["id"]
            ]
        )
    except Exception as e:
        logger.warning(f"Failed to fetch OpenAI models: {e}")
        return DEFAULT_MODELS[LLMProvider.OPENAI]


def fetch_openrouter_models() -> list[str]:
    try:
        response = httpx.get("https://openrouter.ai/api/v1/models", timeout=10)
        response.raise_for_status()
        data = response.json()
        return [m["id"] for m in data["data"]]
    except Exception as e:
        logger.warning(f"Failed to fetch OpenRouter models: {e}")
        return DEFAULT_MODELS[LLMProvider.OPENROUTER]


def fetch_ollama_models(host: str | None = None) -> list[str]:
    ollama_host = host or settings.ollama_host
    try:
        response = httpx.get(f"{ollama_host}/api/tags", timeout=5)
        response.raise_for_status()
        return [m["name"] for m in response.json().get("models", [])]
    except Exception as e:
        logger.warning(f"Failed to fetch Ollama models: {e}")
        return DEFAULT_MODELS[LLMProvider.OLLAMA]


def get_available_models(
    provider: LLMProvider,
    api_key: str | None = None,
    use_cache: bool = True,
) -> list[str]:
    cache_key = f"models_{provider.value}"
    if use_cache and hasattr(get_available_models, "_cache"):
        cached = get_available_models._cache.get(cache_key)
        if cached:
            return cached

    if provider == LLMProvider.OPENAI:
        models = fetch_openai_models(api_key)
    elif provider == LLMProvider.OPENROUTER:
        models = fetch_openrouter_models()
    elif provider == LLMProvider.OLLAMA:
        models = fetch_ollama_models()
    else:
        models = DEFAULT_MODELS.get(provider, [])

    if not hasattr(get_available_models, "_cache"):
        get_available_models._cache = {}
    get_available_models._cache[cache_key] = models
    return models


def clear_models_cache():
    if hasattr(get_available_models, "_cache"):
        get_available_models._cache.clear()


def get_embeddings(
    provider: EmbeddingProvider | None = None,
    model: str | None = None,
) -> Embeddings:
    """Get embeddings instance. Settings are read from DB first, then env vars."""
    # Get provider from DB or env
    if provider is None:
        db_provider = _get_db_setting("embedding_provider")
        logger.info(f"DB embedding_provider: {db_provider}")
        if db_provider:
            provider = EmbeddingProvider(db_provider)
        else:
            provider = settings.embedding_provider

    # Get model from DB or env
    model_name = model or _get_db_setting("embedding_model", settings.embedding_model)

    logger.info(f"Creating embeddings with provider={provider}, model={model_name}")

    # Get API keys from DB or env
    openai_key = _get_db_setting("openai_api_key", settings.openai_api_key)
    cohere_key = _get_db_setting("cohere_api_key", settings.cohere_api_key)
    ollama_host = _get_db_setting("ollama_host", settings.ollama_host)
    hf_token = _get_db_setting("huggingface_token")

    # Set HuggingFace token in environment if available (needed for FastEmbed model downloads)
    if hf_token:
        os.environ["HF_TOKEN"] = hf_token
        logger.info("Using Hugging Face token from settings")

    if provider == EmbeddingProvider.OPENAI:
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(model=model_name, api_key=openai_key)
    elif provider == EmbeddingProvider.FASTEMBED:
        # Use our optimized FastEmbed wrapper with parallel processing
        return FastEmbedEmbeddingsParallel(model_name=model_name)
    elif provider == EmbeddingProvider.COHERE:
        from langchain_cohere import CohereEmbeddings

        return CohereEmbeddings(model=model_name, cohere_api_key=cohere_key)
    else:
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(model=model_name, base_url=ollama_host)


def test_llm_connection(
    provider: LLMProvider,
    model: str,
    api_key: str | None = None,
) -> tuple[bool, str]:
    try:
        llm = get_llm(provider=provider, model=model, temperature=0, streaming=False)
        llm.invoke("ping")
        return True, "Connection successful"
    except Exception as e:
        return False, str(e)


def get_embedding_dimensions(model: str) -> int:
    return EMBEDDING_DIMENSIONS.get(model, 1536)  # Default to 1536 for OpenAI standards
