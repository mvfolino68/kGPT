"""Kafka cluster API routes."""

from fastapi import APIRouter, HTTPException
from loguru import logger
from starlette.concurrency import run_in_threadpool

from kgpt.api.schemas import (
    ClusterConnectRequest,
    ClusterDetailsResponse,
    ClusterInfo,
    ClusterResponse,
    KafkaCluster,
)
from kgpt.db import get_db
from kgpt.services import KafkaService, get_kafka_service

router = APIRouter(prefix="/cluster", tags=["cluster"])


def _map_db_to_config(active: dict) -> dict:
    """Helper to map DB cluster record to KafkaService config."""
    config = {
        "name": active.get("name"),
        "bootstrap_servers": active.get("bootstrap_servers"),
    }
    if active.get("security_protocol"):
        config["security_protocol"] = active["security_protocol"]
    if active.get("sasl_mechanism"):
        config["sasl_mechanism"] = active["sasl_mechanism"]
    if active.get("sasl_username"):
        config["sasl_username"] = active["sasl_username"]
    if active.get("sasl_password"):
        config["sasl_password"] = active["sasl_password"]
    return config


@router.get("", response_model=ClusterResponse)
async def get_clusters() -> ClusterResponse:
    """Get current Kafka cluster connection status."""
    db = get_db()
    clusters = db.get_kafka_clusters()
    available = [KafkaCluster(**c) for c in clusters]

    active = db.get_active_kafka_cluster()
    cluster_info = None

    if active:
        # Use service to check status if we think we are connected
        service = get_kafka_service()
        # Ensure service is configured if it wasn't
        if not service.config:
            service.set_config(_map_db_to_config(active))

        try:
            # Lightweight check
            cluster_info = service.test_connection()
        except Exception:
            # Fallback if connection fails but DB thinks it's active
            cluster_info = ClusterInfo(
                name=active["name"],
                bootstrap_servers=active["bootstrap_servers"],
                connected=False,
            )

    return ClusterResponse(cluster=cluster_info, available_clusters=available)


@router.get("/info", response_model=ClusterInfo)
async def get_cluster_info():
    """Get basic cluster info."""
    service = get_kafka_service()
    if not service.config:
        return ClusterInfo(connected=False)

    try:
        await run_in_threadpool(service.get_cluster_details)
        return ClusterInfo(
            connected=True,
            name=service.config.get("name"),
            version="Unknown",  # Requires specific protocol usage to determine
        )
    except Exception:
        return ClusterInfo(connected=False)


@router.get("/details", response_model=ClusterDetailsResponse)
async def get_cluster_details():
    """Get current cluster details."""
    service = get_kafka_service()
    if not service.config:
        # Check if we have an active cluster in DB but not connected in service
        with get_db() as conn:
            active = conn.execute("SELECT * FROM clusters WHERE is_active = 1").fetchone()
            if active:
                # auto-connect
                try:
                    config = _map_db_to_config(active)
                    # Run connection in thread pool to avoid blocking
                    await run_in_threadpool(service.connect, config)
                except Exception as e:
                    logger.error(f"Failed to auto-connect: {e}")
                    return ClusterDetailsResponse(
                        connected=False,
                        error=f"Failed to connect to {active['name']}: {str(e)}",
                    )

    if not service.config:
        return ClusterDetailsResponse(connected=False)

    try:
        # Run potentially blocking operations in thread pool
        details = await run_in_threadpool(service.get_cluster_details)

        # Helper to convert potential dict_values/views to list
        def to_list(val):
            if val is None:
                return []
            if isinstance(val, (list, tuple)):
                return list(val)
            return list(val)

        return ClusterDetailsResponse(
            connected=True,
            cluster_id=details.get("cluster_id"),
            controller_id=details.get("controller_id"),
            brokers=to_list(details.get("brokers", [])),
            broker_count=details.get("broker_count", 0),
            topics=to_list(details.get("topics", [])),
            topic_count=details.get("topic_count", 0),
            consumer_groups=to_list(details.get("consumer_groups", [])),
            consumer_group_count=details.get("consumer_group_count", 0),
            total_partitions=details.get("total_partitions", 0),
            under_replicated_count=details.get("under_replicated_count", 0),
            name=service.config.get("name"),
        )
    except Exception as e:
        logger.error(f"Error fetching cluster details: {e}")
        return ClusterDetailsResponse(
            connected=False,
            error=str(e),
            name=service.config.get("name"),
        )


@router.post("/connect", response_model=ClusterResponse)
async def connect_to_cluster(request: ClusterConnectRequest):
    """Connect to a Kafka cluster."""
    service = get_kafka_service()
    try:
        config = request.model_dump()
        # Save to DB
        # Access the connection context manager explicitly, as Database is not a context manager itself
        with get_db()._get_connection() as conn:
            # Set all others inactive
            conn.execute("UPDATE clusters SET is_active = 0")

            # Check if exists
            existing = conn.execute(
                "SELECT id FROM clusters WHERE name = ?", (config["name"],)
            ).fetchone()

            if existing:
                conn.execute(
                    """
                    UPDATE clusters
                    SET bootstrap_servers = ?, security_protocol = ?,
                        sasl_mechanism = ?, sasl_username = ?, sasl_password = ?,
                        is_active = 1
                    WHERE name = ?
                    """,
                    (
                        config["bootstrap_servers"],
                        config.get("security_protocol", "PLAINTEXT"),
                        config.get("sasl_mechanism"),
                        config.get("sasl_username"),
                        config.get("sasl_password"),
                        config["name"],
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO clusters (
                        name, bootstrap_servers, security_protocol,
                        sasl_mechanism, sasl_username, sasl_password, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        config["name"],
                        config["bootstrap_servers"],
                        config.get("security_protocol", "PLAINTEXT"),
                        config.get("sasl_mechanism"),
                        config.get("sasl_username"),
                        config.get("sasl_password"),
                    ),
                )
            conn.commit()

        # Connect
        service_config = config.copy()
        await run_in_threadpool(service.connect, service_config)

        return ClusterResponse(
            success=True,
            message=f"Connected to {config['name']}",
            cluster_id=service.client.list_topics(timeout=5).cluster_id if service.client else None,
        )
    except Exception as e:
        logger.error(f"Connection error: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/disconnect")
async def disconnect_cluster() -> dict:
    """Disconnect from the current Kafka cluster."""
    # Update global service
    get_kafka_service().set_config(None)

    db = get_db()
    active = db.get_active_kafka_cluster()
    if active:
        db.set_active_kafka_cluster(-1)  # Set all inactive

    return {"status": "disconnected"}


@router.delete("/{cluster_id}")
async def delete_cluster(cluster_id: int) -> dict:
    """Delete a saved Kafka cluster configuration."""
    db = get_db()

    # If deleting active cluster, disconnect first
    active = db.get_active_kafka_cluster()
    if active and active.get("id") == cluster_id:
        get_kafka_service().set_config(None)

    db.delete_kafka_cluster(cluster_id)
    return {"status": "deleted", "cluster_id": cluster_id}


@router.post("/connect/demo")
async def connect_demo_cluster() -> ClusterInfo:
    """Connect to the demo Kafka cluster."""
    demo_servers = ["kafka:9092", "localhost:9094", "localhost:9092"]

    for servers in demo_servers:
        config = {"name": "Demo Kafka Cluster", "bootstrap_servers": servers}
        temp_service = KafkaService(config)

        try:
            cluster_info = temp_service.test_connection()

            # If successful, save and activate
            db = get_db()
            cluster_id = db.add_kafka_cluster(
                name="Demo Kafka Cluster",
                bootstrap_servers=servers,
            )
            db.set_active_kafka_cluster(cluster_id)
            get_kafka_service().set_config(config)

            return cluster_info
        except Exception:
            continue


@router.post("/topics")
async def create_kafka_topic(request: dict):
    """Create a Kafka topic."""
    service = get_kafka_service()
    topic_name = request.get("name")
    if not topic_name:
        raise HTTPException(status_code=400, detail="Topic name required")

    try:
        return await run_in_threadpool(
            service.create_topic,
            topic_name,
            num_partitions=request.get("partitions", 1),
            replication_factor=request.get("replication_factor", 1),
            config=request.get("config"),
        )
    except Exception as e:
        logger.error(f"Error creating topic {topic_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create topic: {str(e)}") from e


@router.delete("/topics/{topic_name}")
async def delete_kafka_topic(topic_name: str):
    """Delete a Kafka topic."""
    service = get_kafka_service()
    try:
        result = await run_in_threadpool(service.delete_topic, topic_name)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error deleting topic {topic_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete topic: {str(e)}") from e


@router.get("/brokers/{broker_id}/config")
async def get_broker_config(broker_id: int):
    """Get configuration for a specific broker."""
    service = get_kafka_service()
    try:
        return await run_in_threadpool(service.describe_broker_config, broker_id)
    except Exception as e:
        logger.error(f"Error fetching config for broker {broker_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get broker config: {str(e)}") from e


@router.delete("/groups/{group_id}")
async def delete_consumer_group(group_id: str):
    """Delete a consumer group."""
    service = get_kafka_service()
    try:
        result = await run_in_threadpool(service.delete_consumer_group, group_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error deleting consumer group {group_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete consumer group: {str(e)}"
        ) from e
