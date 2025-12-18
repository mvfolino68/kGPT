"""Query enhancement for domain-aware web searches.

This module rewrites user queries to include Kafka/Confluent domain context,
ensuring web searches return relevant results instead of unrelated matches
(e.g., "kraft" -> "KRaft Apache Kafka" instead of kraft paper).

Approach:
1. Disambiguation: Map ambiguous terms to their Kafka-specific meanings
2. Context injection: Add domain context when queries are too generic
3. LLM enhancement: For complex queries, use the LLM to rewrite intelligently
"""

import re

from loguru import logger

# Mapping of ambiguous terms to their Kafka-specific expansions
# Format: {lowercase_term: (kafka_term, description)}
KAFKA_TERM_DISAMBIGUATION = {
    # KRaft - most commonly confused
    "kraft": ("KRaft", "Kafka Raft consensus protocol"),
    "raft": ("KRaft", "Kafka Raft consensus protocol"),
    # Kafka ecosystem components
    "connect": ("Kafka Connect", "Kafka Connect data integration"),
    "streams": ("Kafka Streams", "Kafka Streams processing library"),
    "ksql": ("ksqlDB", "ksqlDB streaming SQL"),
    "ksqldb": ("ksqlDB", "ksqlDB streaming SQL"),
    "schema registry": ("Confluent Schema Registry", "Confluent Schema Registry"),
    "sr": ("Confluent Schema Registry", "Confluent Schema Registry"),
    # Producer/consumer patterns
    "producer": ("Kafka producer", "Kafka producer"),
    "consumer": ("Kafka consumer", "Kafka consumer"),
    "consumer group": ("Kafka consumer group", "Kafka consumer group"),
    # Core concepts that might be too generic
    "partition": ("Kafka partition", "Kafka topic partition"),
    "partitions": ("Kafka partitions", "Kafka topic partitions"),
    "offset": ("Kafka offset", "Kafka consumer offset"),
    "offsets": ("Kafka offsets", "Kafka consumer offsets"),
    "broker": ("Kafka broker", "Kafka broker"),
    "brokers": ("Kafka brokers", "Kafka brokers"),
    "topic": ("Kafka topic", "Kafka topic"),
    "topics": ("Kafka topics", "Kafka topics"),
    "replication": ("Kafka replication", "Kafka topic replication"),
    "leader": ("Kafka partition leader", "Kafka partition leader"),
    "follower": ("Kafka partition follower", "Kafka partition follower"),
    "isr": ("Kafka ISR", "Kafka In-Sync Replicas"),
    # Zookeeper transition
    "zookeeper": ("ZooKeeper", "Apache ZooKeeper with Kafka"),
    "zk": ("ZooKeeper", "Apache ZooKeeper with Kafka"),
    # Message formats
    "avro": ("Avro", "Apache Avro with Kafka"),
    "protobuf": ("Protobuf", "Protocol Buffers with Kafka"),
    # Confluent Platform
    "control center": ("Confluent Control Center", "Confluent Control Center"),
    "c3": ("Confluent Control Center", "Confluent Control Center"),
    "cloud": ("Confluent Cloud", "Confluent Cloud"),
    "ccloud": ("Confluent Cloud", "Confluent Cloud"),
    # Common operations
    "compaction": ("Kafka log compaction", "Kafka log compaction"),
    "retention": ("Kafka retention", "Kafka message retention"),
    "tiered storage": ("Kafka tiered storage", "Kafka tiered storage"),
    # MirrorMaker
    "mm2": ("MirrorMaker 2", "Kafka MirrorMaker 2"),
    "mirrormaker": ("MirrorMaker", "Kafka MirrorMaker"),
    # Transactions
    "exactly once": ("Kafka exactly-once semantics", "Kafka exactly-once semantics"),
    "eos": ("Kafka exactly-once semantics", "Kafka exactly-once semantics"),
    "idempotent": ("Kafka idempotent producer", "Kafka idempotent producer"),
    "transactional": ("Kafka transactions", "Kafka transactions"),
}

# Patterns that indicate the query already has sufficient Kafka context
KAFKA_CONTEXT_PATTERNS = [
    r"\bkafka\b",
    r"\bconfluent\b",
    r"\bapache kafka\b",
    r"\bkraft\b",  # Already correctly spelled
]


def _has_kafka_context(query: str) -> bool:
    """Check if query already contains Kafka-specific context."""
    query_lower = query.lower()
    return any(re.search(pattern, query_lower) for pattern in KAFKA_CONTEXT_PATTERNS)


def _find_ambiguous_terms(query: str) -> list[tuple[str, str, str]]:
    """
    Find ambiguous terms in the query that should be disambiguated.

    Returns list of (original_match, kafka_term, description) tuples.
    """
    query_lower = query.lower()
    found_terms = []

    # Sort by length (longest first) to handle multi-word terms first
    sorted_terms = sorted(KAFKA_TERM_DISAMBIGUATION.keys(), key=len, reverse=True)

    for term in sorted_terms:
        # Use word boundaries for matching
        pattern = r"\b" + re.escape(term) + r"\b"
        if re.search(pattern, query_lower):
            kafka_term, description = KAFKA_TERM_DISAMBIGUATION[term]
            # Find the actual match in the original query (preserve case)
            match = re.search(pattern, query_lower)
            if match:
                original = query[match.start() : match.end()]
                found_terms.append((original, kafka_term, description))

    return found_terms


def enhance_query_for_web_search(
    query: str,
    sub_goals: list[str] | None = None,
    add_domain_suffix: bool = True,
) -> str:
    """
    Enhance a query for domain-aware web search.

    This applies several strategies:
    1. Disambiguate known ambiguous terms (kraft -> KRaft)
    2. Add Kafka/Confluent context if missing
    3. Optionally append domain suffix for better results

    Args:
        query: The original user query
        sub_goals: Optional sub-goals from the router (for context)
        add_domain_suffix: Whether to add "Apache Kafka" suffix if no context

    Returns:
        Enhanced query string optimized for Kafka-related web search
    """
    original_query = query
    enhanced_query = query

    # Step 1: Check if query already has Kafka context
    has_context = _has_kafka_context(query)

    # Step 2: Find and replace ambiguous terms
    ambiguous_terms = _find_ambiguous_terms(query)

    if ambiguous_terms:
        for original, kafka_term, description in ambiguous_terms:
            # Only replace if the kafka_term is different (case-insensitive)
            if original.lower() != kafka_term.lower():
                # Replace with the Kafka-specific term
                enhanced_query = re.sub(
                    r"\b" + re.escape(original) + r"\b",
                    kafka_term,
                    enhanced_query,
                    flags=re.IGNORECASE,
                )
                has_context = True  # Now we have context
                logger.debug(f"Disambiguated '{original}' -> '{kafka_term}'")

    # Step 3: Add domain context if query is too generic
    if add_domain_suffix and not has_context:
        # Query has no Kafka context, add it
        enhanced_query = f"{enhanced_query} Apache Kafka"
        logger.debug("Added 'Apache Kafka' suffix for domain context")

    # Log the enhancement
    if enhanced_query != original_query:
        logger.info(f"Enhanced query: '{original_query}' -> '{enhanced_query}'")

    return enhanced_query


def enhance_queries_for_web_search(
    queries: list[str],
    add_domain_suffix: bool = True,
) -> list[str]:
    """
    Enhance multiple queries for web search.

    Args:
        queries: List of queries to enhance
        add_domain_suffix: Whether to add domain context if missing

    Returns:
        List of enhanced queries
    """
    return [enhance_query_for_web_search(q, add_domain_suffix=add_domain_suffix) for q in queries]


def get_web_search_query(
    question: str,
    sub_goals: list[str] | None = None,
) -> str:
    """
    Generate the optimal web search query from user question and sub-goals.

    This is the main entry point for the streaming module.

    Strategy:
    1. If sub_goals exist and are specific, use the most relevant one
    2. Otherwise, enhance the main question
    3. Always apply disambiguation

    Args:
        question: The user's original question
        sub_goals: Optional sub-goals from the router

    Returns:
        Optimized search query for Exa
    """
    # If we have specific sub-goals, the first one is usually the most relevant
    if sub_goals and len(sub_goals) > 0:
        # Use the first sub-goal as it's typically the core question
        primary_query = sub_goals[0]
        # But also check if main question has important terms not in sub-goal
        enhanced = enhance_query_for_web_search(primary_query, sub_goals)
        logger.debug(f"Using sub-goal for web search: {enhanced}")
        return enhanced

    # Otherwise enhance the main question
    return enhance_query_for_web_search(question)
