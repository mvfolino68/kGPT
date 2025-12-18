"""Comprehensive Kafka admin operations registry with code preview."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class OperationType(str, Enum):
    """Categories of admin operations."""

    # Read-only operations - execute immediately
    READ = "read"
    # Write operations - require confirmation
    WRITE = "write"
    # Dangerous operations - require explicit confirmation with warning
    DESTRUCTIVE = "destructive"


@dataclass
class OperationParam:
    """Definition of an operation parameter."""

    name: str
    label: str
    param_type: str = "text"  # text, number, select, boolean
    required: bool = True
    default: Any = None
    placeholder: str = ""
    hint: str = ""
    options: list[str] = field(default_factory=list)


@dataclass
class KafkaOperation:
    """Definition of a Kafka admin operation."""

    id: str
    name: str
    description: str
    operation_type: OperationType
    params: list[OperationParam]
    code_template: str  # Python code template showing what will run
    category: str = "general"
    icon: str = "cog"

    def get_code_preview(self, params: dict) -> str:
        """Generate code preview with actual parameter values."""
        code = self.code_template
        for key, value in params.items():
            placeholder = "{" + key + "}"
            if placeholder in code:
                # Format value appropriately for Python code
                if isinstance(value, str):
                    code = code.replace(placeholder, f'"{value}"')
                else:
                    code = code.replace(placeholder, str(value))
        return code


# ============================================================================
# Operation Registry
# ============================================================================

KAFKA_OPERATIONS: dict[str, KafkaOperation] = {}


def register_operation(op: KafkaOperation):
    """Register an operation in the global registry."""
    KAFKA_OPERATIONS[op.id] = op
    return op


# ----------------------------------------------------------------------------
# Topic Operations
# ----------------------------------------------------------------------------

register_operation(
    KafkaOperation(
        id="list_topics",
        name="List Topics",
        description="List all topics in the cluster with partition counts",
        operation_type=OperationType.READ,
        category="topics",
        icon="list",
        params=[],
        code_template="""from confluent_kafka.admin import AdminClient

admin = AdminClient(config)
metadata = admin.list_topics()
topics = list(metadata.topics.keys())
print(f"Found {len(topics)} topics")""",
    )
)

register_operation(
    KafkaOperation(
        id="describe_topic",
        name="Describe Topic",
        description="Get detailed information about a topic including partitions, replicas, and configuration",
        operation_type=OperationType.READ,
        category="topics",
        icon="info",
        params=[
            OperationParam(
                name="topic_name",
                label="Topic Name",
                required=True,
                placeholder="my-topic",
                hint="Name of the topic to describe",
            ),
        ],
        code_template="""from confluent_kafka.admin import AdminClient, ConfigResource, ResourceType

admin = AdminClient(config)

# Get partition info
metadata = admin.list_topics(topic={topic_name})
topic_meta = metadata.topics[{topic_name}]

# Get configuration
resource = ConfigResource(ResourceType.TOPIC, {topic_name})
configs = admin.describe_configs([resource])""",
    )
)

register_operation(
    KafkaOperation(
        id="create_topic",
        name="Create Topic",
        description="Create a new topic with specified partitions and replication factor",
        operation_type=OperationType.WRITE,
        category="topics",
        icon="plus",
        params=[
            OperationParam(
                name="topic_name",
                label="Topic Name",
                required=True,
                placeholder="my-new-topic",
                hint="Unique name for the new topic",
            ),
            OperationParam(
                name="num_partitions",
                label="Partitions",
                param_type="number",
                required=False,
                default=3,
                hint="Number of partitions (default: 3)",
            ),
            OperationParam(
                name="replication_factor",
                label="Replication Factor",
                param_type="number",
                required=False,
                default=1,
                hint="Number of replicas per partition (default: 1)",
            ),
        ],
        code_template="""from confluent_kafka.admin import AdminClient, NewTopic

admin = AdminClient(config)

topic = NewTopic(
    {topic_name},
    num_partitions={num_partitions},
    replication_factor={replication_factor}
)

futures = admin.create_topics([topic])
futures[{topic_name}].result()  # Wait for completion""",
    )
)

register_operation(
    KafkaOperation(
        id="delete_topic",
        name="Delete Topic",
        description="Permanently delete a topic and all its data",
        operation_type=OperationType.DESTRUCTIVE,
        category="topics",
        icon="trash",
        params=[
            OperationParam(
                name="topic_name",
                label="Topic Name",
                required=True,
                placeholder="topic-to-delete",
                hint="Name of the topic to delete (this cannot be undone!)",
            ),
        ],
        code_template="""from confluent_kafka.admin import AdminClient

admin = AdminClient(config)

futures = admin.delete_topics([{topic_name}])
futures[{topic_name}].result()  # Wait for completion""",
    )
)

register_operation(
    KafkaOperation(
        id="add_partitions",
        name="Add Partitions",
        description="Increase the number of partitions for a topic (cannot decrease)",
        operation_type=OperationType.WRITE,
        category="topics",
        icon="expand",
        params=[
            OperationParam(
                name="topic_name",
                label="Topic Name",
                required=True,
                hint="Topic to add partitions to",
            ),
            OperationParam(
                name="new_total_partitions",
                label="New Total Partitions",
                param_type="number",
                required=True,
                hint="New total number of partitions (must be greater than current)",
            ),
        ],
        code_template="""from confluent_kafka.admin import AdminClient, NewPartitions

admin = AdminClient(config)

new_parts = NewPartitions({topic_name}, {new_total_partitions})
futures = admin.create_partitions([new_parts])
futures[{topic_name}].result()""",
    )
)

register_operation(
    KafkaOperation(
        id="alter_topic_config",
        name="Alter Topic Config",
        description="Modify topic configuration settings",
        operation_type=OperationType.WRITE,
        category="topics",
        icon="settings",
        params=[
            OperationParam(
                name="topic_name",
                label="Topic Name",
                required=True,
                hint="Topic to configure",
            ),
            OperationParam(
                name="config_key",
                label="Config Key",
                required=True,
                placeholder="retention.ms",
                hint="Configuration key to modify",
            ),
            OperationParam(
                name="config_value",
                label="Config Value",
                required=True,
                placeholder="86400000",
                hint="New value for the configuration",
            ),
        ],
        code_template="""from confluent_kafka.admin import AdminClient, ConfigResource, ResourceType

admin = AdminClient(config)

resource = ConfigResource(ResourceType.TOPIC, {topic_name})
resource.set_config({config_key}, {config_value})

futures = admin.alter_configs([resource])
futures[resource].result()""",
    )
)

# ----------------------------------------------------------------------------
# Consumer Group Operations
# ----------------------------------------------------------------------------

register_operation(
    KafkaOperation(
        id="list_consumer_groups",
        name="List Consumer Groups",
        description="List all consumer groups in the cluster",
        operation_type=OperationType.READ,
        category="consumers",
        icon="users",
        params=[],
        code_template="""from confluent_kafka.admin import AdminClient

admin = AdminClient(config)

groups_future = admin.list_consumer_groups()
groups = groups_future.result().valid
print(f"Found {len(groups)} consumer groups")""",
    )
)

register_operation(
    KafkaOperation(
        id="describe_consumer_group",
        name="Describe Consumer Group",
        description="Get detailed information about a consumer group including members and assignments",
        operation_type=OperationType.READ,
        category="consumers",
        icon="info",
        params=[
            OperationParam(
                name="group_id",
                label="Group ID",
                required=True,
                hint="Consumer group ID to describe",
            ),
        ],
        code_template="""from confluent_kafka.admin import AdminClient

admin = AdminClient(config)

futures = admin.describe_consumer_groups([{group_id}])
group_info = futures[{group_id}].result()

print(f"Group: {group_info.group_id}")
print(f"State: {group_info.state}")
print(f"Members: {len(group_info.members)}")""",
    )
)

register_operation(
    KafkaOperation(
        id="delete_consumer_group",
        name="Delete Consumer Group",
        description="Delete a consumer group (must be empty/inactive)",
        operation_type=OperationType.DESTRUCTIVE,
        category="consumers",
        icon="trash",
        params=[
            OperationParam(
                name="group_id",
                label="Group ID",
                required=True,
                hint="Consumer group to delete",
            ),
        ],
        code_template="""from confluent_kafka.admin import AdminClient

admin = AdminClient(config)

futures = admin.delete_consumer_groups([{group_id}])
futures[{group_id}].result()""",
    )
)

register_operation(
    KafkaOperation(
        id="get_consumer_group_offsets",
        name="Get Consumer Offsets",
        description="Get committed offsets for a consumer group",
        operation_type=OperationType.READ,
        category="consumers",
        icon="bookmark",
        params=[
            OperationParam(
                name="group_id",
                label="Group ID",
                required=True,
                hint="Consumer group ID",
            ),
        ],
        code_template="""from confluent_kafka.admin import AdminClient

admin = AdminClient(config)

# List committed offsets for all topic-partitions
futures = admin.list_consumer_group_offsets([ConsumerGroupTopicPartitions({group_id})])
offsets = futures[{group_id}].result()""",
    )
)

# ----------------------------------------------------------------------------
# Cluster Operations
# ----------------------------------------------------------------------------

register_operation(
    KafkaOperation(
        id="describe_cluster",
        name="Describe Cluster",
        description="Get cluster metadata including brokers, controller, and cluster ID",
        operation_type=OperationType.READ,
        category="cluster",
        icon="server",
        params=[],
        code_template="""from confluent_kafka.admin import AdminClient

admin = AdminClient(config)

metadata = admin.list_topics()
print(f"Cluster ID: {metadata.cluster_id}")
print(f"Controller: Broker {metadata.controller_id}")
print(f"Brokers: {len(metadata.brokers)}")""",
    )
)

register_operation(
    KafkaOperation(
        id="describe_broker_config",
        name="Describe Broker Config",
        description="Get configuration for a specific broker",
        operation_type=OperationType.READ,
        category="cluster",
        icon="settings",
        params=[
            OperationParam(
                name="broker_id",
                label="Broker ID",
                param_type="number",
                required=True,
                hint="Broker ID to describe (e.g., 0, 1, 2)",
            ),
        ],
        code_template="""from confluent_kafka.admin import AdminClient, ConfigResource, ResourceType

admin = AdminClient(config)

resource = ConfigResource(ResourceType.BROKER, str({broker_id}))
futures = admin.describe_configs([resource])
broker_config = futures[resource].result()""",
    )
)

# ----------------------------------------------------------------------------
# ACL Operations
# ----------------------------------------------------------------------------

register_operation(
    KafkaOperation(
        id="list_acls",
        name="List ACLs",
        description="List all Access Control Lists in the cluster",
        operation_type=OperationType.READ,
        category="security",
        icon="shield",
        params=[],
        code_template="""from confluent_kafka.admin import AdminClient, AclBindingFilter, ResourceType, ResourcePatternType

admin = AdminClient(config)

# List all ACLs
acl_filter = AclBindingFilter(
    restype=ResourceType.ANY,
    name=None,
    resource_pattern_type=ResourcePatternType.ANY,
    principal=None,
    host=None,
    operation=None,
    permission_type=None
)

futures = admin.describe_acls(acl_filter)
acls = futures.result()""",
    )
)


# ============================================================================
# Operation Executor
# ============================================================================


def get_operation(operation_id: str) -> KafkaOperation | None:
    """Get an operation by ID."""
    return KAFKA_OPERATIONS.get(operation_id)


def get_operations_by_category() -> dict[str, list[KafkaOperation]]:
    """Get all operations grouped by category."""
    categories: dict[str, list[KafkaOperation]] = {}
    for op in KAFKA_OPERATIONS.values():
        if op.category not in categories:
            categories[op.category] = []
        categories[op.category].append(op)
    return categories


def get_all_operations() -> list[KafkaOperation]:
    """Get all registered operations."""
    return list(KAFKA_OPERATIONS.values())


def get_read_operations() -> list[KafkaOperation]:
    """Get all read-only operations."""
    return [op for op in KAFKA_OPERATIONS.values() if op.operation_type == OperationType.READ]


def get_write_operations() -> list[KafkaOperation]:
    """Get all write operations."""
    return [
        op
        for op in KAFKA_OPERATIONS.values()
        if op.operation_type in (OperationType.WRITE, OperationType.DESTRUCTIVE)
    ]
