"""LLM and embedding provider configuration - OpenAI only."""

import os

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from loguru import logger

from kgpt.config import EmbeddingProvider, settings

# Embedding model dimensions
EMBEDDING_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
    "BAAI/bge-small-en-v1.5": 384,
    "BAAI/bge-base-en-v1.5": 768,
}


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

        logger.debug(
            f"Embedding {len(texts)} texts with batch_size={self.batch_size}, parallel={self.parallel}"
        )

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


def get_openai_api_key() -> str | None:
    """Get OpenAI API key from DB or environment."""
    return _get_db_setting("openai_api_key", settings.openai_api_key)


def get_llm(
    model: str | None = None,
    temperature: float | None = None,
    streaming: bool = True,
) -> BaseChatModel:
    """
    Get an OpenAI LLM instance.

    Settings are read from DB first, then fall back to env vars.
    """
    # Get model from DB or env
    model_name = model or _get_db_setting("openai_model", settings.openai_model) or "gpt-4o"
    temp = temperature if temperature is not None else settings.llm_temperature

    # Get API key
    api_key = get_openai_api_key()

    logger.debug(f"Creating OpenAI LLM: model={model_name}, streaming={streaming}")

    return ChatOpenAI(
        model=model_name,
        temperature=temp,
        streaming=streaming,
        api_key=api_key or None,
    )


def get_structured_llm(
    model: str | None = None,
    temperature: float = 0,
) -> BaseChatModel:
    """
    Get an OpenAI LLM that supports structured output.

    This is the same as get_llm but with streaming disabled for structured output.
    """
    return get_llm(model=model, temperature=temperature, streaming=False)


def get_embeddings(
    provider: EmbeddingProvider | None = None,
    model: str | None = None,
) -> Embeddings:
    """Get embeddings instance. Settings are read from DB first, then env vars."""
    # Get provider from DB or env
    if provider is None:
        db_provider = _get_db_setting("embedding_provider")
        if db_provider:
            provider = EmbeddingProvider(db_provider)
        else:
            provider = settings.embedding_provider

    # Get model from DB or env
    model_name = model or _get_db_setting("embedding_model", settings.embedding_model)

    logger.debug(f"Creating embeddings with provider={provider}, model={model_name}")

    # Get API key
    openai_key = get_openai_api_key()

    # Set HuggingFace token in environment if available (needed for FastEmbed model downloads)
    hf_token = _get_db_setting("huggingface_token")
    if hf_token:
        os.environ["HF_TOKEN"] = hf_token

    if provider == EmbeddingProvider.OPENAI:
        return OpenAIEmbeddings(model=model_name, api_key=openai_key)
    else:
        # FastEmbed - local embeddings
        return FastEmbedEmbeddingsParallel(model_name=model_name)


def get_available_models() -> list[str]:
    """Get list of available OpenAI models."""
    # Return commonly used models - can be expanded with API call if needed
    return [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
    ]


def test_llm_connection(model: str | None = None) -> tuple[bool, str]:
    """Test connection to OpenAI API."""
    try:
        llm = get_llm(model=model, temperature=0, streaming=False)
        llm.invoke("ping")
        return True, "Connection successful"
    except Exception as e:
        return False, str(e)


def get_embedding_dimensions(model: str) -> int:
    """Get the embedding dimensions for a model."""
    return EMBEDDING_DIMENSIONS.get(model, 1536)
