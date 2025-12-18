"""Kafka cluster API routes."""

from fastapi import APIRouter, HTTPException
from loguru import logger

from kgpt.api.schemas import (
    ClusterConnectRequest,
    ClusterInfo,
    ClusterResponse,
    KafkaCluster,
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
