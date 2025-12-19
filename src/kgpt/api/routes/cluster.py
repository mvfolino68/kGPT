"""Kafka cluster API routes."""

from fastapi import APIRouter, HTTPException
from loguru import logger

from kgpt.agents.admin import (
    get_available_operations_for_context,
    get_operation_examples,
    get_operations_by_category_dict,
    get_suggested_operations,
)
from kgpt.api.schemas import (
    BrokerInfo,
    ClusterConnectRequest,
    ClusterDetailsResponse,
    ClusterInfo,
    ClusterResponse,
    ConsumerGroupInfo,
    KafkaCluster,
    TopicInfo,
)
from kgpt.db import get_db

router = APIRouter(prefix="/cluster", tags=["cluster"])


def get_cluster_info_from_connection(bootstrap_servers: str, config: dict) -> ClusterInfo | None:
    """Get cluster information by connecting to Kafka."""
    try:
        from confluent_kafka.admin import AdminClient

        admin_config = {"bootstrap.servers": bootstrap_servers}

        # Add security config if needed
        if config.get("security_protocol") and config["security_protocol"] != "PLAINTEXT":
            admin_config["security.protocol"] = config["security_protocol"]
            if config.get("sasl_mechanism"):
                admin_config["sasl.mechanism"] = config["sasl_mechanism"]
            if config.get("sasl_username"):
                admin_config["sasl.username"] = config["sasl_username"]
            if config.get("sasl_password"):
                admin_config["sasl.password"] = config["sasl_password"]

        admin = AdminClient(admin_config)

        # Get cluster metadata
        metadata = admin.list_topics(timeout=10)

        topics = [t for t in metadata.topics if not t.startswith("_")]
        brokers = len(metadata.brokers)
        cluster_id = metadata.cluster_id

        return ClusterInfo(
            name=config.get("name", "Kafka Cluster"),
            bootstrap_servers=bootstrap_servers,
            connected=True,
            brokers=brokers,
            topics=topics,
            cluster_id=cluster_id,
        )

    except Exception as e:
        logger.error(f"Failed to connect to Kafka: {e}")
        return None


@router.get("", response_model=ClusterResponse)
async def get_clusters() -> ClusterResponse:
    """Get current Kafka cluster connection status."""
    db = get_db()

    # Get all configured clusters
    clusters = db.get_kafka_clusters()
    available = [KafkaCluster(**c) for c in clusters]

    # Get active cluster
    active = db.get_active_kafka_cluster()
    cluster_info = None

    if active:
        cluster_info = get_cluster_info_from_connection(
            active["bootstrap_servers"],
            active,
        )
        if cluster_info:
            cluster_info.name = active["name"]

    return ClusterResponse(cluster=cluster_info, available_clusters=available)


@router.get("/info", response_model=ClusterInfo | dict)
async def get_cluster_info_endpoint():
    """Get info about the currently connected cluster."""
    db = get_db()
    active = db.get_active_kafka_cluster()

    if not active:
        return {"connected": False}

    cluster_info = get_cluster_info_from_connection(
        active["bootstrap_servers"],
        active,
    )

    if cluster_info:
        cluster_info.name = active["name"]
        return cluster_info

    return {"connected": False}


@router.get("/details", response_model=ClusterDetailsResponse)
async def get_cluster_details():
    """
    Get comprehensive cluster details for dashboard display.

    Returns enriched information about brokers, topics, and consumer groups.
    """
    db = get_db()
    active = db.get_active_kafka_cluster()

    if not active:
        return ClusterDetailsResponse(connected=False)

    try:
        from confluent_kafka.admin import AdminClient

        admin_config = {"bootstrap.servers": active["bootstrap_servers"]}

        if active.get("security_protocol") and active["security_protocol"] != "PLAINTEXT":
            admin_config["security.protocol"] = active["security_protocol"]
            if active.get("sasl_mechanism"):
                admin_config["sasl.mechanism"] = active["sasl_mechanism"]
            if active.get("sasl_username"):
                admin_config["sasl.username"] = active["sasl_username"]
            if active.get("sasl_password"):
                admin_config["sasl.password"] = active["sasl_password"]

        admin = AdminClient(admin_config)
        metadata = admin.list_topics(timeout=10)

        # Process brokers
        brokers: list[BrokerInfo] = []
        broker_partition_counts: dict[int, int] = {}
        broker_leader_counts: dict[int, int] = {}

        for broker_id, broker in metadata.brokers.items():
            broker_partition_counts[broker_id] = 0
            broker_leader_counts[broker_id] = 0
            brokers.append(
                BrokerInfo(
                    id=broker_id,
                    host=broker.host,
                    port=broker.port,
                    is_controller=(broker_id == metadata.controller_id),
                )
            )

        # Process topics
        topics: list[TopicInfo] = []
        total_partitions = 0
        under_replicated_count = 0

        for topic_name, topic_meta in metadata.topics.items():
            is_internal = topic_name.startswith("_")
            partition_count = len(topic_meta.partitions)
            total_partitions += partition_count

            # Calculate replication factor and leader distribution
            replication_factor = 0
            leader_distribution: dict[int, int] = {}
            under_replicated = False

            for partition_id, partition in topic_meta.partitions.items():
                if replication_factor == 0:
                    replication_factor = len(partition.replicas)

                # Track leader distribution
                if partition.leader is not None and partition.leader >= 0:
                    leader_distribution[partition.leader] = (
                        leader_distribution.get(partition.leader, 0) + 1
                    )
                    broker_leader_counts[partition.leader] = (
                        broker_leader_counts.get(partition.leader, 0) + 1
                    )

                # Track partition counts per broker
                for replica in partition.replicas:
                    broker_partition_counts[replica] = broker_partition_counts.get(replica, 0) + 1

                # Check for under-replication
                if len(partition.isrs) < len(partition.replicas):
                    under_replicated = True

            if under_replicated:
                under_replicated_count += 1

            topics.append(
                TopicInfo(
                    name=topic_name,
                    partition_count=partition_count,
                    replication_factor=replication_factor,
                    leader_distribution=leader_distribution,
                    is_internal=is_internal,
                    under_replicated=under_replicated,
                )
            )

        # Update broker partition/leader counts
        for broker in brokers:
            broker.partition_count = broker_partition_counts.get(broker.id, 0)
            broker.leader_count = broker_leader_counts.get(broker.id, 0)

        # Sort topics: user topics first, then internal
        topics.sort(key=lambda t: (t.is_internal, t.name))

        # Get consumer groups
        consumer_groups: list[ConsumerGroupInfo] = []
        try:
            groups_future = admin.list_consumer_groups()
            groups_result = groups_future.result(timeout=10)

            for group in groups_result.valid:
                group_info = ConsumerGroupInfo(
                    group_id=group.group_id,
                    state=str(group.state) if hasattr(group, "state") else "Unknown",
                    protocol_type=None,
                    member_count=0,
                )

                # Try to get more details
                try:
                    describe_future = admin.describe_consumer_groups([group.group_id])
                    for gid, future in describe_future.items():
                        result = future.result(timeout=5)
                        group_info.state = str(result.state)
                        group_info.protocol_type = result.protocol_type
                        group_info.member_count = len(result.members)
                        if result.coordinator:
                            group_info.coordinator_id = result.coordinator.id

                        # Get subscribed topics
                        subscribed_topics = set()
                        for member in result.members:
                            if hasattr(member, "assignment") and member.assignment:
                                for tp in member.assignment.topic_partitions:
                                    subscribed_topics.add(tp.topic)
                        group_info.topics = sorted(subscribed_topics)
                except Exception as e:
                    logger.debug(f"Could not get details for group {group.group_id}: {e}")

                consumer_groups.append(group_info)

        except Exception as e:
            logger.warning(f"Could not fetch consumer groups: {e}")

        return ClusterDetailsResponse(
            connected=True,
            name=active.get("name"),
            cluster_id=metadata.cluster_id,
            controller_id=metadata.controller_id,
            brokers=brokers,
            broker_count=len(brokers),
            topics=topics,
            topic_count=len([t for t in topics if not t.is_internal]),
            total_partitions=total_partitions,
            under_replicated_count=under_replicated_count,
            consumer_groups=consumer_groups,
            consumer_group_count=len(consumer_groups),
        )

    except Exception as e:
        logger.error(f"Failed to get cluster details: {e}")
        return ClusterDetailsResponse(connected=False, error=str(e))


@router.post("/connect", response_model=ClusterInfo)
async def connect_cluster(request: ClusterConnectRequest) -> ClusterInfo:
    """Connect to a Kafka cluster."""
    db = get_db()

    # Test connection first
    cluster_info = get_cluster_info_from_connection(
        request.bootstrap_servers,
        request.model_dump(),
    )

    if not cluster_info:
        raise HTTPException(
            status_code=400,
            detail="Failed to connect to Kafka cluster. Check your connection settings.",
        )

    # Save to database
    cluster_id = db.add_kafka_cluster(
        name=request.name,
        bootstrap_servers=request.bootstrap_servers,
        security_protocol=request.security_protocol,
        sasl_mechanism=request.sasl_mechanism,
        sasl_username=request.sasl_username,
        sasl_password=request.sasl_password,
    )

    # Set as active
    db.set_active_kafka_cluster(cluster_id)

    # Update the agent's cluster context
    from kgpt.agents import KafkaClusterContext, set_cluster_context

    context = KafkaClusterContext(
        bootstrap_servers=request.bootstrap_servers,
        security_protocol=request.security_protocol,
        sasl_mechanism=request.sasl_mechanism,
        sasl_username=request.sasl_username,
        sasl_password=request.sasl_password,
    )
    set_cluster_context(context)

    cluster_info.name = request.name
    return cluster_info


@router.post("/disconnect")
async def disconnect_cluster() -> dict:
    """Disconnect from the current Kafka cluster."""
    from kgpt.agents import set_cluster_context

    set_cluster_context(None)

    db = get_db()
    active = db.get_active_kafka_cluster()
    if active:
        # Deactivate but keep the config
        db.set_active_kafka_cluster(-1)  # This will set all to inactive

    return {"status": "disconnected"}


@router.delete("/{cluster_id}")
async def delete_cluster(cluster_id: int) -> dict:
    """Delete a saved Kafka cluster configuration."""
    db = get_db()
    db.delete_kafka_cluster(cluster_id)
    return {"status": "deleted", "cluster_id": cluster_id}


@router.post("/connect/demo")
async def connect_demo_cluster() -> ClusterInfo:
    """Connect to the demo Kafka cluster (if running)."""
    # Try common demo cluster addresses
    demo_servers = ["kafka:9092", "localhost:9094", "localhost:9092"]

    for servers in demo_servers:
        cluster_info = get_cluster_info_from_connection(
            servers,
            {"name": "Demo Kafka Cluster"},
        )
        if cluster_info:
            # Save and activate
            db = get_db()
            cluster_id = db.add_kafka_cluster(
                name="Demo Kafka Cluster",
                bootstrap_servers=servers,
            )
            db.set_active_kafka_cluster(cluster_id)

            # Set agent context
            from kgpt.agents import KafkaClusterContext, set_cluster_context

            context = KafkaClusterContext(bootstrap_servers=servers)
            set_cluster_context(context)

            return cluster_info

    raise HTTPException(
        status_code=404,
        detail="Demo Kafka cluster not found. Make sure to run with --profile demo",
    )


# ============================================================================
# Operations Discovery Endpoints
# ============================================================================


@router.get("/operations")
async def get_operations() -> dict:
    """
    Get all available Kafka admin operations.

    Returns operations grouped by category with availability status
    based on whether a cluster is connected.
    """
    return get_available_operations_for_context()


@router.get("/operations/by-category")
async def get_operations_grouped() -> dict:
    """Get operations grouped by category."""
    return {
        "categories": get_operations_by_category_dict(),
    }


@router.get("/operations/examples")
async def get_examples() -> dict:
    """Get example prompts for each operation category."""
    return {
        "examples": get_operation_examples(),
    }


@router.get("/operations/suggestions")
async def get_suggestions(
    last_operation: str | None = None,
    last_success: bool = True,
) -> dict:
    """
    Get suggested next operations based on context.

    Args:
        last_operation: ID of the last executed operation
        last_success: Whether the last operation succeeded
    """
    # Get cluster info if connected
    from kgpt.agents.kafka_agent import get_cluster_context

    cluster_info = None
    context = get_cluster_context()
    if context:
        try:
            cluster_info = context.get_cluster_metadata()
        except Exception:
            pass

    suggestions = get_suggested_operations(
        last_operation=last_operation,
        last_success=last_success,
        cluster_info=cluster_info,
    )

    return {
        "suggestions": suggestions,
        "cluster_connected": context is not None,
    }
