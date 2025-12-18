"""SQLite database for persisting settings, document sources, and cluster configs."""

import json
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from kgpt.config import settings


class Database:
    """SQLite database manager for kGPT."""

    def __init__(self, db_path: Path | None = None):
        """Initialize database connection."""
        self.db_path = db_path or settings.get_database_path()
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Settings table - key-value store for app settings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Document sources table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    url TEXT,
                    collection_name TEXT NOT NULL,
                    document_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    indexed_at TIMESTAMP,
                    metadata TEXT
                )
            """)

            # Kafka cluster configurations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kafka_clusters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    bootstrap_servers TEXT NOT NULL,
                    security_protocol TEXT DEFAULT 'PLAINTEXT',
                    sasl_mechanism TEXT,
                    sasl_username TEXT,
                    sasl_password TEXT,
                    is_active BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_connected_at TIMESTAMP
                )
            """)

            # Chat sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL DEFAULT 'New Chat',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Chat history (messages within sessions)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    citations TEXT,
                    agent_trace TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
                )
            """)

            # Migration: Add agent_trace column if it doesn't exist
            cursor.execute("PRAGMA table_info(chat_history)")
            columns = [row[1] for row in cursor.fetchall()]
            if "agent_trace" not in columns:
                cursor.execute("ALTER TABLE chat_history ADD COLUMN agent_trace TEXT")

            # Index for faster session lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_history_session
                ON chat_history(session_id)
            """)

            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # Settings methods
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row["value"])
                except json.JSONDecodeError:
                    return row["value"]
            return default

    def set_setting(self, key: str, value: Any):
        """Set a setting value."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            json_value = json.dumps(value) if not isinstance(value, str) else value
            cursor.execute(
                """
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, ?)
            """,
                (key, json_value, datetime.now()),
            )
            conn.commit()

    def get_all_settings(self) -> dict[str, Any]:
        """Get all settings as a dictionary."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            result = {}
            for row in cursor.fetchall():
                try:
                    result[row["key"]] = json.loads(row["value"])
                except json.JSONDecodeError:
                    result[row["key"]] = row["value"]
            return result

    # Document source methods
    def add_document_source(
        self,
        name: str,
        source_type: str,
        collection_name: str,
        url: str | None = None,
        metadata: dict | None = None,
    ) -> int:
        """Add a new document source."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO document_sources (name, source_type, url, collection_name, metadata)
                VALUES (?, ?, ?, ?, ?)
            """,
                (name, source_type, url, collection_name, json.dumps(metadata or {})),
            )
            conn.commit()
            return cursor.lastrowid

    def update_document_source(
        self,
        source_id: int,
        status: str | None = None,
        document_count: int | None = None,
        indexed_at: datetime | None = None,
    ):
        """Update a document source."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []

            if status is not None:
                updates.append("status = ?")
                params.append(status)
            if document_count is not None:
                updates.append("document_count = ?")
                params.append(document_count)
            if indexed_at is not None:
                updates.append("indexed_at = ?")
                params.append(indexed_at)

            if updates:
                params.append(source_id)
                cursor.execute(
                    f"UPDATE document_sources SET {', '.join(updates)} WHERE id = ?",
                    params,
                )
                conn.commit()

    def get_document_sources(self) -> list[dict]:
        """Get all document sources."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM document_sources ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def delete_document_source(self, source_id: int):
        """Delete a document source."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM document_sources WHERE id = ?", (source_id,))
            conn.commit()

    # Kafka cluster methods
    def add_kafka_cluster(
        self,
        name: str,
        bootstrap_servers: str,
        security_protocol: str = "PLAINTEXT",
        sasl_mechanism: str | None = None,
        sasl_username: str | None = None,
        sasl_password: str | None = None,
    ) -> int:
        """Add a new Kafka cluster configuration."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO kafka_clusters
                (name, bootstrap_servers, security_protocol, sasl_mechanism, sasl_username, sasl_password)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    name,
                    bootstrap_servers,
                    security_protocol,
                    sasl_mechanism,
                    sasl_username,
                    sasl_password,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get_kafka_clusters(self) -> list[dict]:
        """Get all Kafka cluster configurations."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM kafka_clusters ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]

    def get_active_kafka_cluster(self) -> dict | None:
        """Get the currently active Kafka cluster."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM kafka_clusters WHERE is_active = 1 LIMIT 1")
            row = cursor.fetchone()
            return dict(row) if row else None

    def set_active_kafka_cluster(self, cluster_id: int):
        """Set a Kafka cluster as active."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE kafka_clusters SET is_active = 0")
            cursor.execute("UPDATE kafka_clusters SET is_active = 1 WHERE id = ?", (cluster_id,))
            conn.commit()

    def delete_kafka_cluster(self, cluster_id: int):
        """Delete a Kafka cluster configuration."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM kafka_clusters WHERE id = ?", (cluster_id,))
            conn.commit()

    # Chat history methods
    def create_chat_session(self, title: str = "New Chat") -> str:
        """Create a new chat session and return its ID."""
        import uuid

        session_id = uuid.uuid4().hex
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO chat_sessions (id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """,
                (session_id, title, datetime.now(), datetime.now()),
            )
            conn.commit()
        return session_id

    def get_chat_sessions(self, limit: int = 50) -> list[dict]:
        """Get all chat sessions, ordered by most recent first."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, title, created_at, updated_at
                FROM chat_sessions
                ORDER BY updated_at DESC
                LIMIT ?
            """,
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_chat_session(self, session_id: str) -> dict | None:
        """Get a single chat session by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, created_at, updated_at FROM chat_sessions WHERE id = ?",
                (session_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_chat_session(self, session_id: str, title: str | None = None):
        """Update a chat session's title and updated_at timestamp."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if title is not None:
                cursor.execute(
                    "UPDATE chat_sessions SET title = ?, updated_at = ? WHERE id = ?",
                    (title, datetime.now(), session_id),
                )
            else:
                cursor.execute(
                    "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
                    (datetime.now(), session_id),
                )
            conn.commit()

    def delete_chat_session(self, session_id: str):
        """Delete a chat session and all its messages."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
            conn.commit()

    def add_chat_message(
        self,
        session_id: str,
        role: str,
        content: str,
        citations: list | None = None,
        agent_trace: dict | None = None,
    ) -> int:
        """Add a message to a chat session.

        Args:
            session_id: The session ID
            role: 'user' or 'assistant'
            content: Message content
            citations: List of citation objects with title, url, type, and optional content_preview
            agent_trace: Agent pipeline trace data (routing decision, retrieval results, etc.)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO chat_history (session_id, role, content, citations, agent_trace, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    role,
                    content,
                    json.dumps(citations or []),
                    json.dumps(agent_trace) if agent_trace else None,
                    datetime.now(),
                ),
            )
            # Update the session's updated_at timestamp
            cursor.execute(
                "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
                (datetime.now(), session_id),
            )
            conn.commit()
            return cursor.lastrowid

    def get_chat_messages(self, session_id: str) -> list[dict]:
        """Get all messages for a chat session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, session_id, role, content, citations, agent_trace, created_at
                FROM chat_history
                WHERE session_id = ?
                ORDER BY created_at ASC
            """,
                (session_id,),
            )
            messages = []
            for row in cursor.fetchall():
                msg = dict(row)
                try:
                    msg["citations"] = json.loads(msg["citations"]) if msg["citations"] else []
                except (json.JSONDecodeError, TypeError):
                    msg["citations"] = []
                try:
                    msg["agent_trace"] = (
                        json.loads(msg["agent_trace"]) if msg.get("agent_trace") else None
                    )
                except (json.JSONDecodeError, TypeError):
                    msg["agent_trace"] = None
                messages.append(msg)
            return messages

    def clear_all_chat_history(self):
        """Delete all chat sessions and messages."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_history")
            cursor.execute("DELETE FROM chat_sessions")
            conn.commit()

    # Setup wizard methods
    def is_setup_complete(self) -> bool:
        """Check if initial setup has been completed."""
        return self.get_setting("setup_complete", False)

    def mark_setup_complete(self):
        """Mark the initial setup as complete."""
        self.set_setting("setup_complete", True)


# Singleton database instance
_db_instance: Database | None = None


def get_db() -> Database:
    """Get the singleton database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
