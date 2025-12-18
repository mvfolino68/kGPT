"""Kafka admin operation executor with code preview and structured results."""

from loguru import logger

from kgpt.agents.kafka_agent import KafkaClusterContext, get_cluster_context

from .operations import OperationType, get_operation


class ExecutionResult:
    """Result of executing a Kafka admin operation."""

    def __init__(
        self,
        success: bool,
        operation_id: str,
        operation_name: str,
        data: dict | None = None,
        error: str | None = None,
        code_executed: str | None = None,
        message: str | None = None,
    ):
        self.success = success
        self.operation_id = operation_id
        self.operation_name = operation_name
        self.data = data or {}
        self.error = error
        self.code_executed = code_executed
        self.message = message

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "success": self.success,
            "operation": self.operation_id,
            "operation_name": self.operation_name,
        }
        if self.data:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error
        if self.code_executed:
            result["code_executed"] = self.code_executed
        if self.message:
            result["message"] = self.message
        return result


class KafkaAdminExecutor:
    """Executes Kafka admin operations against a cluster."""

    def __init__(self, context: KafkaClusterContext):
        self.context = context
        self._operation_handlers: dict[str, callable] = {
            # Topic operations
            "list_topics": self._list_topics,
            "describe_topic": self._describe_topic,
            "create_topic": self._create_topic,
            "delete_topic": self._delete_topic,
            "add_partitions": self._add_partitions,
            "alter_topic_config": self._alter_topic_config,
            # Consumer group operations
            "list_consumer_groups": self._list_consumer_groups,
            "describe_consumer_group": self._describe_consumer_group,
            "delete_consumer_group": self._delete_consumer_group,
            "get_consumer_group_offsets": self._get_consumer_group_offsets,
            # Cluster operations
            "describe_cluster": self._describe_cluster,
            "describe_broker_config": self._describe_broker_config,
            # ACL operations
            "list_acls": self._list_acls,
        }

    def execute(self, operation_id: str, params: dict) -> ExecutionResult:
        """Execute an operation with the given parameters."""
        operation = get_operation(operation_id)
        if not operation:
            return ExecutionResult(
                success=False,
                operation_id=operation_id,
                operation_name="Unknown",
                error=f"Unknown operation: {operation_id}",
            )

        handler = self._operation_handlers.get(operation_id)
        if not handler:
            return ExecutionResult(
                success=False,
                operation_id=operation_id,
                operation_name=operation.name,
                error=f"No handler implemented for operation: {operation_id}",
            )

        # Get code preview
        code_preview = operation.get_code_preview(params)

        try:
            logger.info(f"Executing operation: {operation_id} with params: {params}")
            result = handler(params)
            result.code_executed = code_preview
            return result
        except Exception as e:
            logger.error(f"Operation {operation_id} failed: {e}")
            return ExecutionResult(
                success=False,
                operation_id=operation_id,
                operation_name=operation.name,
                error=str(e),
                code_executed=code_preview,
            )

    def can_execute_directly(self, operation_id: str) -> bool:
        """Check if an operation can be executed without confirmation."""
        operation = get_operation(operation_id)
        return operation is not None and operation.operation_type == OperationType.READ

    # ========================================================================
    # Topic Operations
    # ========================================================================

    def _list_topics(self, params: dict) -> ExecutionResult:
        """List all topics."""
        metadata = self.context.get_cluster_metadata()
        topics = metadata.get("topics", [])

        # Get partition counts for each topic
        topic_details = []
        for topic in topics:
            try:
                details = self.context.get_topic_details(topic)
                topic_details.append(
                    {
                        "name": topic,
                        "partitions": details.get("partition_count", 0),
                    }
                )
            except Exception:
                topic_details.append({"name": topic, "partitions": "?"})

        return ExecutionResult(
            success=True,
            operation_id="list_topics",
            operation_name="List Topics",
            data={
                "topics": topic_details,
                "total_count": len(topics),
            },
            message=f"Found {len(topics)} topic(s) in the cluster.",
        )

    def _describe_topic(self, params: dict) -> ExecutionResult:
        """Describe a topic in detail."""
        topic_name = params.get("topic_name")
        if not topic_name:
            return ExecutionResult(
                success=False,
                operation_id="describe_topic",
                operation_name="Describe Topic",
                error="Topic name is required",
            )

        result = self.context.describe_topic(topic_name)

        if not result.get("success", False):
            return ExecutionResult(
                success=False,
                operation_id="describe_topic",
                operation_name="Describe Topic",
                error=result.get("error", "Failed to describe topic"),
            )

        return ExecutionResult(
            success=True,
            operation_id="describe_topic",
            operation_name="Describe Topic",
            data={
                "topic": topic_name,
                "partition_count": result.get("partition_count", 0),
                "partitions": result.get("partitions", []),
                "configuration": result.get("configuration", {}),
                "replication_factor": self._get_replication_factor(result.get("partitions", [])),
            },
            message=f"Topic '{topic_name}' has {result.get('partition_count', 0)} partition(s).",
        )

    def _get_replication_factor(self, partitions: list) -> int:
        """Extract replication factor from partition info."""
        if not partitions:
            return 0
        first_partition = partitions[0] if partitions else {}
        replicas = first_partition.get("replicas", [])
        return len(replicas)

    def _create_topic(self, params: dict) -> ExecutionResult:
        """Create a new topic."""
        result = self.context.create_topic(
            topic_name=params.get("topic_name"),
            num_partitions=int(params.get("num_partitions", 3)),
            replication_factor=int(params.get("replication_factor", 1)),
            config=params.get("config"),
        )

        return ExecutionResult(
            success=result.get("success", False),
            operation_id="create_topic",
            operation_name="Create Topic",
            data={
                "topic": params.get("topic_name"),
                "partitions": params.get("num_partitions", 3),
                "replication_factor": params.get("replication_factor", 1),
            },
            error=result.get("error"),
            message=result.get("message"),
        )

    def _delete_topic(self, params: dict) -> ExecutionResult:
        """Delete a topic."""
        result = self.context.delete_topic(params.get("topic_name"))

        return ExecutionResult(
            success=result.get("success", False),
            operation_id="delete_topic",
            operation_name="Delete Topic",
            data={"topic": params.get("topic_name")},
            error=result.get("error"),
            message=result.get("message"),
        )

    def _add_partitions(self, params: dict) -> ExecutionResult:
        """Add partitions to a topic."""
        result = self.context.add_partitions(
            topic_name=params.get("topic_name"),
            new_total_partitions=int(params.get("new_total_partitions")),
        )

        return ExecutionResult(
            success=result.get("success", False),
            operation_id="add_partitions",
            operation_name="Add Partitions",
            data={
                "topic": params.get("topic_name"),
                "new_total_partitions": params.get("new_total_partitions"),
            },
            error=result.get("error"),
            message=result.get("message"),
        )

    def _alter_topic_config(self, params: dict) -> ExecutionResult:
        """Alter topic configuration."""
        config_updates = {params.get("config_key"): params.get("config_value")}
        result = self.context.alter_topic_config(
            topic_name=params.get("topic_name"),
            config_updates=config_updates,
        )

        return ExecutionResult(
            success=result.get("success", False),
            operation_id="alter_topic_config",
            operation_name="Alter Topic Config",
            data={
                "topic": params.get("topic_name"),
                "config_updates": config_updates,
            },
            error=result.get("error"),
            message=result.get("message"),
        )

    # ========================================================================
    # Consumer Group Operations
    # ========================================================================

    def _list_consumer_groups(self, params: dict) -> ExecutionResult:
        """List all consumer groups."""
        groups = self.context.get_consumer_groups()

        return ExecutionResult(
            success=True,
            operation_id="list_consumer_groups",
            operation_name="List Consumer Groups",
            data={
                "groups": groups,
                "total_count": len(groups),
            },
            message=f"Found {len(groups)} consumer group(s).",
        )

    def _describe_consumer_group(self, params: dict) -> ExecutionResult:
        """Describe a consumer group."""
        group_id = params.get("group_id")
        if not group_id:
            return ExecutionResult(
                success=False,
                operation_id="describe_consumer_group",
                operation_name="Describe Consumer Group",
                error="Group ID is required",
            )

        result = self.context.describe_consumer_group(group_id)

        if "error" in result:
            return ExecutionResult(
                success=False,
                operation_id="describe_consumer_group",
                operation_name="Describe Consumer Group",
                error=result["error"],
            )

        return ExecutionResult(
            success=True,
            operation_id="describe_consumer_group",
            operation_name="Describe Consumer Group",
            data=result,
            message=f"Consumer group '{group_id}' has {len(result.get('members', []))} member(s).",
        )

    def _delete_consumer_group(self, params: dict) -> ExecutionResult:
        """Delete a consumer group."""
        result = self.context.delete_consumer_group(params.get("group_id"))

        return ExecutionResult(
            success=result.get("success", False),
            operation_id="delete_consumer_group",
            operation_name="Delete Consumer Group",
            data={"group_id": params.get("group_id")},
            error=result.get("error"),
            message=result.get("message"),
        )

    def _get_consumer_group_offsets(self, params: dict) -> ExecutionResult:
        """Get consumer group offsets."""
        group_id = params.get("group_id")
        if not group_id:
            return ExecutionResult(
                success=False,
                operation_id="get_consumer_group_offsets",
                operation_name="Get Consumer Offsets",
                error="Group ID is required",
            )

        try:
            from confluent_kafka.admin import ConsumerGroupTopicPartitions

            cgtps = ConsumerGroupTopicPartitions(group_id)
            futures = self.context.admin.list_consumer_group_offsets([cgtps])

            result = futures[group_id].result()

            offsets = []
            for tp in result.topic_partitions:
                offsets.append(
                    {
                        "topic": tp.topic,
                        "partition": tp.partition,
                        "offset": tp.offset,
                        "metadata": tp.metadata,
                    }
                )

            return ExecutionResult(
                success=True,
                operation_id="get_consumer_group_offsets",
                operation_name="Get Consumer Offsets",
                data={
                    "group_id": group_id,
                    "offsets": offsets,
                },
                message=f"Retrieved offsets for {len(offsets)} partition(s).",
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                operation_id="get_consumer_group_offsets",
                operation_name="Get Consumer Offsets",
                error=str(e),
            )

    # ========================================================================
    # Cluster Operations
    # ========================================================================

    def _describe_cluster(self, params: dict) -> ExecutionResult:
        """Describe the cluster."""
        metadata = self.context.get_cluster_metadata()

        brokers = []
        for broker_id, broker_info in metadata.get("brokers", {}).items():
            brokers.append(
                {
                    "id": broker_id,
                    "host": broker_info.get("host"),
                    "port": broker_info.get("port"),
                }
            )

        return ExecutionResult(
            success=True,
            operation_id="describe_cluster",
            operation_name="Describe Cluster",
            data={
                "cluster_id": metadata.get("cluster_id"),
                "controller_id": metadata.get("controller_id"),
                "brokers": brokers,
                "broker_count": metadata.get("broker_count", 0),
                "topic_count": metadata.get("topic_count", 0),
            },
            message=f"Cluster has {metadata.get('broker_count', 0)} broker(s) and {metadata.get('topic_count', 0)} topic(s).",
        )

    def _describe_broker_config(self, params: dict) -> ExecutionResult:
        """Get broker configuration."""
        broker_id = params.get("broker_id")
        if broker_id is None:
            return ExecutionResult(
                success=False,
                operation_id="describe_broker_config",
                operation_name="Describe Broker Config",
                error="Broker ID is required",
            )

        try:
            from confluent_kafka.admin import ConfigResource, ResourceType

            resource = ConfigResource(ResourceType.BROKER, str(broker_id))
            futures = self.context.admin.describe_configs([resource])

            config_result = futures[resource].result()

            configs = {}
            for entry in config_result.values():
                configs[entry.name] = {
                    "value": entry.value,
                    "is_default": entry.is_default,
                    "is_read_only": entry.is_read_only,
                }

            return ExecutionResult(
                success=True,
                operation_id="describe_broker_config",
                operation_name="Describe Broker Config",
                data={
                    "broker_id": broker_id,
                    "configs": configs,
                },
                message=f"Retrieved {len(configs)} configuration entries for broker {broker_id}.",
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                operation_id="describe_broker_config",
                operation_name="Describe Broker Config",
                error=str(e),
            )

    # ========================================================================
    # ACL Operations
    # ========================================================================

    def _list_acls(self, params: dict) -> ExecutionResult:
        """List ACLs."""
        try:
            from confluent_kafka.admin import (
                AclBindingFilter,
                AclOperation,
                AclPermissionType,
                ResourcePatternType,
                ResourceType,
            )

            acl_filter = AclBindingFilter(
                restype=ResourceType.ANY,
                name=None,
                resource_pattern_type=ResourcePatternType.ANY,
                principal=None,
                host=None,
                operation=AclOperation.ANY,
                permission_type=AclPermissionType.ANY,
            )

            future = self.context.admin.describe_acls(acl_filter)
            acl_bindings = future.result()

            acls = []
            for acl in acl_bindings:
                acls.append(
                    {
                        "resource_type": str(acl.restype),
                        "resource_name": acl.name,
                        "pattern_type": str(acl.resource_pattern_type),
                        "principal": acl.principal,
                        "host": acl.host,
                        "operation": str(acl.operation),
                        "permission_type": str(acl.permission_type),
                    }
                )

            return ExecutionResult(
                success=True,
                operation_id="list_acls",
                operation_name="List ACLs",
                data={
                    "acls": acls,
                    "total_count": len(acls),
                },
                message=f"Found {len(acls)} ACL(s) in the cluster.",
            )
        except Exception as e:
            error_msg = str(e)
            # ACLs might not be supported if cluster doesn't have security enabled
            if "SECURITY_DISABLED" in error_msg or "not supported" in error_msg.lower():
                return ExecutionResult(
                    success=True,
                    operation_id="list_acls",
                    operation_name="List ACLs",
                    data={"acls": [], "total_count": 0},
                    message="ACLs are not enabled on this cluster (security is disabled).",
                )
            return ExecutionResult(
                success=False,
                operation_id="list_acls",
                operation_name="List ACLs",
                error=error_msg,
            )


def get_executor() -> KafkaAdminExecutor | None:
    """Get an executor for the current cluster context."""
    context = get_cluster_context()
    if context is None:
        return None
    return KafkaAdminExecutor(context)
