"""Pydantic schemas for API request/response models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

# ============================================================================
# Chat Schemas
# ============================================================================


class ChatMessage(BaseModel):
    """A single chat message."""

    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request to send a chat message."""

    message: str = Field(..., description="User's message")
    history: list[ChatMessage] = Field(default=[], description="Previous chat messages")


class ChatResponse(BaseModel):
    """Response from a chat request."""

    answer: str = Field(..., description="Assistant's response")
    citations: list[str] = Field(default=[], description="Source citations")
    error: str | None = Field(default=None, description="Error message if any")


class ChatSession(BaseModel):
    """A chat session containing messages."""

    id: str
    title: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ChatSessionMessage(BaseModel):
    """A message within a chat session."""

    id: int
    session_id: str
    role: str
    content: str
    citations: list[str] = []
    created_at: datetime | None = None


class ChatSessionWithMessages(BaseModel):
    """A chat session with all its messages."""

    session: ChatSession
    messages: list[ChatSessionMessage]


class ChatSessionsListResponse(BaseModel):
    """Response listing all chat sessions."""

    sessions: list[ChatSession]
    total: int


class CreateSessionRequest(BaseModel):
    """Request to create a new chat session."""

    title: str = Field(default="New Chat", description="Session title")


class UpdateSessionRequest(BaseModel):
    """Request to update a chat session."""

    title: str = Field(..., description="New session title")


# ============================================================================
# Documents Schemas
# ============================================================================


class SourceType(str, Enum):
    """Document source types."""

    SITEMAP = "sitemap"
    GITHUB = "github"
    URL = "url"
    FILE = "file"


class DocumentSource(BaseModel):
    """A document source configuration."""

    id: int | None = None
    name: str
    source_type: SourceType
    url: str | None = None
    collection_name: str
    document_count: int = 0
    status: str = "pending"
    created_at: datetime | None = None
    indexed_at: datetime | None = None


class IngestRequest(BaseModel):
    """Request to ingest documents."""

    name: str = Field(..., description="Name for this document source")
    source_type: SourceType = Field(..., description="Type of source")
    url: str | None = Field(default=None, description="URL for sitemap/github/url sources")
    collection_name: str = Field(default="kgpt_docs", description="Qdrant collection name")


class IngestResponse(BaseModel):
    """Response from ingestion request."""

    source_id: int
    status: str
    message: str
    document_count: int = 0


class DocumentsListResponse(BaseModel):
    """Response listing all document sources."""

    sources: list[DocumentSource]
    total: int


# ============================================================================
# Cluster Schemas
# ============================================================================


class KafkaCluster(BaseModel):
    """Kafka cluster configuration."""

    id: int | None = None
    name: str
    bootstrap_servers: str
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: str | None = None
    sasl_username: str | None = None
    sasl_password: str | None = None
    is_active: bool = False


class ClusterConnectRequest(BaseModel):
    """Request to connect to a Kafka cluster."""

    name: str = Field(..., description="Display name for the cluster")
    bootstrap_servers: str = Field(..., description="Bootstrap servers (comma-separated)")
    security_protocol: str = Field(default="PLAINTEXT", description="Security protocol")
    sasl_mechanism: str | None = Field(default=None, description="SASL mechanism")
    sasl_username: str | None = Field(default=None, description="SASL username")
    sasl_password: str | None = Field(default=None, description="SASL password")


class ClusterInfo(BaseModel):
    """Information about a connected Kafka cluster."""

    name: str
    bootstrap_servers: str
    connected: bool
    brokers: int | None = None
    topics: list[str] = []
    cluster_id: str | None = None


class ClusterResponse(BaseModel):
    """Response with cluster information."""

    cluster: ClusterInfo | None = None
    available_clusters: list[KafkaCluster] = []


# ============================================================================
# Settings Schemas
# ============================================================================


class LLMProviderEnum(str, Enum):
    """LLM provider options."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"


class EmbeddingProviderEnum(str, Enum):
    """Embedding provider options."""

    OPENAI = "openai"
    FASTEMBED = "fastembed"
    OLLAMA = "ollama"
    COHERE = "cohere"


class KeyStatus(BaseModel):
    """Status of an API key."""

    configured: bool = False  # Whether key exists (env or db)
    source: str | None = None  # "env", "db", or None
    valid: bool | None = None  # True/False if validated, None if not checked


class SettingsResponse(BaseModel):
    """Current application settings."""

    llm_provider: str
    llm_model: str
    embedding_provider: str
    embedding_model: str
    qdrant_url: str
    qdrant_collection: str
    ollama_host: str

    # Key status with source information
    openai_key: KeyStatus = Field(default_factory=KeyStatus)
    anthropic_key: KeyStatus = Field(default_factory=KeyStatus)
    openrouter_key: KeyStatus = Field(default_factory=KeyStatus)
    cohere_key: KeyStatus = Field(default_factory=KeyStatus)
    huggingface_token: KeyStatus = Field(default_factory=KeyStatus)

    # Legacy fields for backwards compatibility
    has_openai_key: bool = False
    has_anthropic_key: bool = False
    has_openrouter_key: bool = False
    has_cohere_key: bool = False
    has_huggingface_token: bool = False


class ValidateKeyRequest(BaseModel):
    """Request to validate an API key."""

    provider: str
    api_key: str


class ValidateKeyResponse(BaseModel):
    """Response from key validation."""

    valid: bool
    provider: str
    message: str | None = None
    models: list[str] = Field(default_factory=list)  # Available models if valid


class SettingsUpdateRequest(BaseModel):
    """Request to update settings."""

    llm_provider: str | None = None
    llm_model: str | None = None
    embedding_provider: str | None = None
    embedding_model: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    openrouter_api_key: str | None = None
    cohere_api_key: str | None = None
    huggingface_token: str | None = None
    ollama_host: str | None = None


# ============================================================================
# Admin Operation Schemas
# ============================================================================


class AdminOperationRequest(BaseModel):
    """Request to execute a confirmed admin operation."""

    operation: str = Field(..., description="Operation type (create_topic, delete_topic, etc.)")
    params: dict = Field(..., description="Operation parameters")


class AdminOperationResponse(BaseModel):
    """Response from an admin operation execution."""

    success: bool
    operation: str
    message: str | None = None
    error: str | None = None
    topic: str | None = None
    group_id: str | None = None
    partitions: int | None = None
    replication_factor: int | None = None


# ============================================================================
# Health Schemas
# ============================================================================


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    qdrant_connected: bool
    kafka_connected: bool
