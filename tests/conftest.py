"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_question():
    """Sample question for testing."""
    return "How do I configure a Kafka producer?"


@pytest.fixture
def sample_documents():
    """Sample documents for testing retrieval."""
    from langchain_core.documents import Document

    return [
        Document(
            page_content="To configure a Kafka producer, set bootstrap.servers and key/value serializers.",
            metadata={"source": "https://docs.confluent.io/producer"},
        ),
        Document(
            page_content="Producer configuration includes acks, retries, and batch.size settings.",
            metadata={"source": "https://kafka.apache.org/documentation"},
        ),
    ]
