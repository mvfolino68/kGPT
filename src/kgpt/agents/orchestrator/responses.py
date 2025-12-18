"""Canned responses for common queries (help, greetings, etc.)."""


HELP_RESPONSE = """## What I Can Do

I'm your Kafka assistant! Here's what I can help you with:

### Query and Explore
- **Check cluster status** - View brokers, topics, and consumer groups
- **List topics** - See all topics with their partition counts
- **Describe topics** - Get detailed topic configuration
- **Consumer lag** - Check consumer group lag and offsets

### Admin Operations
I can execute these operations directly on your connected cluster:

| Operation | Example Command |
|-----------|-----------------|
| **Create topic** | "Create a topic called orders with 3 partitions" |
| **Delete topic** | "Delete the topic named test-topic" |
| **Alter config** | "Set retention.ms to 604800000 for topic orders" |
| **Add partitions** | "Increase partitions to 6 for topic events" |
| **Delete consumer group** | "Delete consumer group my-consumer-group" |

### Documentation
- Ask about Kafka concepts, best practices, and configurations
- Get help with producers, consumers, and Streams
- Learn about security, monitoring, and troubleshooting

### Tips
- Connect to a cluster first in the **Cluster** page
- Use natural language - I understand requests like "delete my orders topic"
- Ask follow-up questions for more details

**Try asking:** "List all topics in my cluster" or "Create a topic called events with 5 partitions"
"""


def get_help_response() -> str:
    """Return the help response."""
    return HELP_RESPONSE
