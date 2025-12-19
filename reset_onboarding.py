#!/usr/bin/env python3
"""
Reset kGPT to a new user state.

Options:
  --soft     Just clear API keys (triggers onboarding, keeps data)
  --full     Clear all settings + chat history (keeps documents)
  --nuke     Complete factory reset (deletes everything including documents)

Default is --soft for safety.
"""

import argparse
import sqlite3
import sys
from pathlib import Path

# Database path (same as in config.py)
DB_PATH = Path("data/kgpt.db")

# Settings that store API keys
API_KEY_SETTINGS = [
    "openai_api_key",
    "exa_api_key",
    "cohere_api_key",
    "huggingface_token",
]

# All user-configurable settings
ALL_SETTINGS = API_KEY_SETTINGS + [
    "llm_provider",
    "llm_model",
    "embedding_provider",
    "embedding_model",
    "web_search_enabled",
    "setup_complete",
]


def get_connection():
    """Get database connection."""
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        print("Make sure you're running this from the project root directory.")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def soft_reset():
    """Clear API keys to trigger onboarding. Keeps all data."""
    conn = get_connection()
    cursor = conn.cursor()

    deleted = 0
    for key in API_KEY_SETTINGS:
        cursor.execute("SELECT 1 FROM settings WHERE key = ?", (key,))
        if cursor.fetchone():
            cursor.execute("DELETE FROM settings WHERE key = ?", (key,))
            deleted += 1
            print(f"  Cleared: {key}")

    conn.commit()
    conn.close()

    if deleted == 0:
        print("  No API keys found in database")
    else:
        print(f"\nCleared {deleted} API key(s)")

    return deleted > 0


def full_reset():
    """Clear all settings and chat history. Keeps document sources."""
    conn = get_connection()
    cursor = conn.cursor()

    # Clear all settings
    cursor.execute("SELECT COUNT(*) FROM settings")
    settings_count = cursor.fetchone()[0]
    cursor.execute("DELETE FROM settings")
    print(f"  Cleared {settings_count} setting(s)")

    # Clear chat history
    cursor.execute("SELECT COUNT(*) FROM chat_history")
    messages_count = cursor.fetchone()[0]
    cursor.execute("DELETE FROM chat_history")

    cursor.execute("SELECT COUNT(*) FROM chat_sessions")
    sessions_count = cursor.fetchone()[0]
    cursor.execute("DELETE FROM chat_sessions")
    print(f"  Cleared {sessions_count} chat session(s) ({messages_count} messages)")

    conn.commit()
    conn.close()

    return True


def nuke_reset():
    """Factory reset - delete everything."""
    conn = get_connection()
    cursor = conn.cursor()

    # Clear all tables
    tables = ["settings", "chat_history", "chat_sessions", "document_sources", "kafka_clusters"]

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        if count > 0:
            cursor.execute(f"DELETE FROM {table}")
            print(f"  Cleared {table}: {count} row(s)")

    conn.commit()
    conn.close()

    # Delete the vector store data
    qdrant_path = Path("data/qdrant_storage")
    if qdrant_path.exists():
        import shutil

        shutil.rmtree(qdrant_path)
        print("  Cleared: qdrant_storage (vector embeddings)")

    print("\nNote: If using external Qdrant, manually delete collections or restart the container.")

    return True


def show_status():
    """Show current database status."""
    if not DB_PATH.exists():
        print("Database not found")
        return

    conn = get_connection()
    cursor = conn.cursor()

    print("\nCurrent state:")

    # API keys
    for key in API_KEY_SETTINGS:
        cursor.execute("SELECT 1 FROM settings WHERE key = ?", (key,))
        status = "configured" if cursor.fetchone() else "not set"
        print(f"  {key}: {status}")

    # Counts
    cursor.execute("SELECT COUNT(*) FROM chat_sessions")
    print(f"  Chat sessions: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM document_sources")
    print(f"  Document sources: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM kafka_clusters")
    print(f"  Kafka clusters: {cursor.fetchone()[0]}")

    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Reset kGPT to a new user state",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python reset_onboarding.py              # Soft reset (clear API keys only)
  python reset_onboarding.py --soft       # Same as above
  python reset_onboarding.py --full       # Clear settings + chat history
  python reset_onboarding.py --nuke       # Factory reset (everything)
  python reset_onboarding.py --status     # Show current state
        """,
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--soft", action="store_true", help="Clear API keys only (default)")
    group.add_argument("--full", action="store_true", help="Clear all settings + chat history")
    group.add_argument("--nuke", action="store_true", help="Factory reset (deletes everything)")
    group.add_argument("--status", action="store_true", help="Show current database state")

    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompts")

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    # Determine reset level
    if args.nuke:
        level = "nuke"
        description = "FACTORY RESET - This will delete ALL data including documents and vectors"
    elif args.full:
        level = "full"
        description = "Full reset - Clear all settings and chat history (keeps documents)"
    else:
        level = "soft"
        description = "Soft reset - Clear API keys to trigger onboarding (keeps all data)"

    print(f"\n{description}\n")

    if not args.yes and level in ("full", "nuke"):
        confirm = input("Are you sure? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Cancelled")
            return

    print("Resetting...")

    if level == "nuke":
        nuke_reset()
    elif level == "full":
        full_reset()
    else:
        soft_reset()

    print("\nNext steps:")
    print("  1. Restart the kGPT server (if running)")
    print("  2. Visit http://localhost:5173/settings")
    print("  3. Complete the onboarding flow")


if __name__ == "__main__":
    main()
