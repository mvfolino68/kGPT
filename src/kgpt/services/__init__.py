"""Service layer for business logic."""

from .kafka import KafkaService, get_kafka_service
from .sse_stream import ChatStreamRequest, generate_sse_stream
from .suggested_actions import generate_suggested_actions

__all__ = [
    "generate_suggested_actions",
    "generate_sse_stream",
    "ChatStreamRequest",
    "KafkaService",
    "get_kafka_service",
]
