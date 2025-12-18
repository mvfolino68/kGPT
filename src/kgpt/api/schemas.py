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


class CitationMetadata(BaseModel):
    """Additional metadata for educational source display."""

    collection: str | None = None
    similarity_score: float | None = None
    rerank_score: float | None = None
    published_date: str | None = None
    search_query: str | None = None


class CitationObject(BaseModel):
    """A structured citation with metadata for educational display."""

    title: str
    url: str
    type: str = "doc"  # "doc" or "web" or "cluster"
    content_preview: str | None = None
    relevance_score: float | None = None
    metadata: CitationMetadata | None = None


class ChatResponse(BaseModel):
    """Response from a chat request."""

    answer: str = Field(..., description="Assistant's response")
    citations: list[str | CitationObject] = Field(default=[], description="Source citations")
    error: str | None = Field(default=None, description="Error message if any")


class ChatSession(BaseModel):
    """A chat session containing messages."""

    id: str
    title: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AgentTraceData(BaseModel):
    """Agent pipeline trace data for educational visibility."""

    routing_decision: dict | None = None
    retrieval_results: dict | None = None
    validation_results: dict | None = None
    web_search_results: dict | None = None
    agent_timeline: list[dict] = Field(default_factory=list)


class ChatSessionMessage(BaseModel):
    """A message within a chat session."""

    id: int
    session_id: str
    role: str
    content: str
    citations: list[str | CitationObject] = []
    agent_trace: AgentTraceData | None = None
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
    """Document source types for internal/custom documentation."""

    URL = "url"  # Single page or internal wiki page
    GITHUB = "github"  # GitHub repo (public or private with token)
    FILE = "file"  # Uploaded file (PDF, markdown, text)
    SITEMAP = "sitemap"  # Legacy - kept for backwards compatibility
    # Future integrations (stubs):
    # CONFLUENCE = "confluence"
    # NOTION = "notion"
    # GOOGLE_DRIVE = "gdrive"


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

    name: str | None = Field(
        default=None, description="Name for this source (auto-generated if empty)"
    )
    source_type: SourceType = Field(..., description="Type of source")
    url: str | None = Field(default=None, description="URL for the document source")
    collection_name: str = Field(default="kgpt_docs", description="Qdrant collection name")
    auto_name: bool = Field(default=True, description="Use AI to generate a smart name")


class NameSuggestionRequest(BaseModel):
    """Request for smart name suggestions."""

    url: str = Field(..., description="URL to generate name for")
    source_type: SourceType = Field(default=SourceType.URL, description="Type of source")


class NameSuggestionResponse(BaseModel):
    """Response with name suggestions."""

    suggestions: list[str] = Field(default_factory=list, description="List of name suggestions")
    smart_name: str | None = Field(default=None, description="AI-generated smart name")


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


class EmbeddingProviderEnum(str, Enum):
    """Embedding provider options."""

    OPENAI = "openai"
    FASTEMBED = "fastembed"


class KeyStatus(BaseModel):
    """Status of an API key."""

    configured: bool = False  # Whether key exists (env or db)
    source: str | None = None  # "env", "db", or None
    valid: bool | None = None  # True/False if validated, None if not checked


class SettingsResponse(BaseModel):
    """Current application settings."""

    # LLM settings (OpenAI only)
    llm_provider: str = "openai"
    llm_model: str

    # Embedding settings
    embedding_provider: str
    embedding_model: str

    # Vector store settings
    qdrant_url: str
    qdrant_collection: str

    # Web search settings
    web_search_enabled: bool = True

    # Key status with source information
    openai_key: KeyStatus = Field(default_factory=KeyStatus)
    exa_key: KeyStatus = Field(default_factory=KeyStatus)
    cohere_key: KeyStatus = Field(default_factory=KeyStatus)
    huggingface_token: KeyStatus = Field(default_factory=KeyStatus)

    # Legacy fields for backwards compatibility
    has_openai_key: bool = False
    has_exa_key: bool = False
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
    exa_api_key: str | None = None
    cohere_api_key: str | None = None
    huggingface_token: str | None = None
    web_search_enabled: bool | None = None


# ============================================================================
# Admin Operation Schemas
# ============================================================================


class PartitionDetail(BaseModel):
    """Detailed information about a topic partition."""

    partition: int
    leader: int | None = None
    replicas: list[int] = Field(default_factory=list)
    isrs: list[int] = Field(default_factory=list)


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
    # Support both int (for create_topic) and list (for describe_topic)
    partitions: int | list[PartitionDetail] | None = None
    partition_count: int | None = None
    replication_factor: int | None = None
    # Topic configuration from describe_topic
    configuration: dict | None = None
    all_configs: dict | None = None


# ============================================================================
# Agent Activity Schemas (for educational pipeline visibility)
# ============================================================================


class AgentEvent(BaseModel):
    """Event emitted when an agent starts or completes."""

    agent: str = Field(
        ..., description="Agent name: router, retrieval, kafka, admin, web_search, synthesis"
    )
    status: str = Field(..., description="Status: started, completed, error")
    description: str | None = None
    duration_ms: int | None = None
    result: dict | None = None


class RoutingDecision(BaseModel):
    """Routing decision from the router agent."""

    route: str = Field(..., description="Route: retrieval, kafka, admin, both, direct, help")
    reasoning: str
    sub_goals: list[str] = Field(default_factory=list)
    needs_cluster: bool = False
    needs_retrieval: bool = False
    needs_web_search: bool = False
    needs_admin: bool = False


class RetrievalResultItem(BaseModel):
    """A single retrieved document with scores."""

    source: str
    source_name: str
    content_preview: str
    similarity_score: float
    rerank_score: float | None = None
    collection: str
    search_query: str | None = None


class RetrievalResults(BaseModel):
    """Results from the retrieval agent."""

    docs: list[RetrievalResultItem] = Field(default_factory=list)
    total: int = 0
    queries_used: int = 1
    reranked: bool = False
    reranking_model: str | None = None


# ============================================================================
# Health Schemas
# ============================================================================


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    qdrant_connected: bool
    kafka_connected: bool
