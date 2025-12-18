"""Kafka admin operations module."""

from .discovery import (
    format_operations_for_help,
    get_all_operations_dict,
    get_available_operations_for_context,
    get_operation_examples,
    get_operations_by_category_dict,
    get_operations_summary,
    get_suggested_operations,
    operation_to_dict,
)
from .executor import ExecutionResult, KafkaAdminExecutor, get_executor
from .operations import (
    KAFKA_OPERATIONS,
    KafkaOperation,
    OperationParam,
    OperationType,
    get_all_operations,
    get_operation,
    get_operations_by_category,
    get_read_operations,
    get_write_operations,
)

__all__ = [
    # Executor
    "KafkaAdminExecutor",
    "ExecutionResult",
    "get_executor",
    # Operations registry
    "KAFKA_OPERATIONS",
    "KafkaOperation",
    "OperationParam",
    "OperationType",
    "get_operation",
    "get_all_operations",
    "get_operations_by_category",
    "get_read_operations",
    "get_write_operations",
    # Discovery
    "get_operations_summary",
    "operation_to_dict",
    "get_all_operations_dict",
    "get_operations_by_category_dict",
    "get_available_operations_for_context",
    "format_operations_for_help",
    "get_suggested_operations",
    "get_operation_examples",
]
