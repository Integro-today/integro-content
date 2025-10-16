#!/usr/bin/env python3
"""
Migrate existing SQLite data (configs.db) into PostgreSQL.

- Agents
- Knowledge bases
- KB documents (including embeddings)

Environment:
  DATABASE_URL=postgresql://user:pass@host:5432/db

This script is idempotent via upserts.
"""
import os
import sqlite3
import json
import asyncio
from pathlib import Path
from typing import Any

import asyncpg

from integro.utils.logging import get_logger

logger = get_logger(__name__)


from datetime import datetime, timezone


def _coerce_datetime(value: Any) -> datetime:
    """Convert SQLite stored timestamps (often ISO strings) to tz-aware datetimes.

    Falls back to current UTC time if parsing fails. Ensures timezone-aware value
    for TIMESTAMPTZ columns in Postgres.
    """
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        s = value.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(s)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return datetime.now(timezone.utc)


def find_sqlite_db() -> Path | None:
    candidates = [
        Path("/app/configs.db"),
        Path("/app/data/configs.db"),
        Path("configs.db"),
        Path("data/configs.db"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


async def ensure_schema(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agents (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                config JSONB NOT NULL,
                knowledge_base_id VARCHAR(255),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_bases (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                collection_name VARCHAR(255),
                config JSONB NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kb_documents (
                id SERIAL PRIMARY KEY,
                kb_id VARCHAR(255) NOT NULL,
                doc_id VARCHAR(512) NOT NULL,
                file_path TEXT,
                content TEXT,
                metadata JSONB,
                embedding BYTEA,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(kb_id, doc_id)
            )
            """
        )


async def migrate() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not set; skipping migration")
        return

    sqlite_path = find_sqlite_db()
    if not sqlite_path:
        logger.info("No configs.db found; nothing to migrate")
        return

    logger.info(f"Migrating SQLite from {sqlite_path} to PostgreSQL")

    pool = await asyncpg.create_pool(database_url, min_size=1, max_size=5)
    await ensure_schema(pool)

    with sqlite3.connect(str(sqlite_path)) as sconn:
        sconn.row_factory = sqlite3.Row
        scur = sconn.cursor()

        # Agents
        agents = scur.execute(
            "SELECT id, name, description, config, knowledge_base_id, created_at FROM agents"
        ).fetchall()
        migrated_agents = 0
        async with pool.acquire() as conn:
            for row in agents:
                created_at_dt = _coerce_datetime(row["created_at"]) if "created_at" in row.keys() else datetime.now(timezone.utc)
                await conn.execute(
                    """
                    INSERT INTO agents (id, name, description, config, knowledge_base_id, created_at, updated_at)
                    VALUES ($1, $2, $3, $4::jsonb, $5, $6, NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        config = EXCLUDED.config,
                        knowledge_base_id = EXCLUDED.knowledge_base_id,
                        updated_at = NOW()
                    """,
                    row["id"], row["name"], row["description"], row["config"], row["knowledge_base_id"], created_at_dt,
                )
                migrated_agents += 1
        logger.info(f"Migrated {migrated_agents} agents")

        # Knowledge bases
        kbs = scur.execute(
            "SELECT id, name, description, collection_name, config, created_at FROM knowledge_bases"
        ).fetchall()
        migrated_kbs = 0
        async with pool.acquire() as conn:
            for row in kbs:
                created_at_dt = _coerce_datetime(row["created_at"]) if "created_at" in row.keys() else datetime.now(timezone.utc)
                await conn.execute(
                    """
                    INSERT INTO knowledge_bases (id, name, description, collection_name, config, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5::jsonb, $6, NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        collection_name = EXCLUDED.collection_name,
                        config = EXCLUDED.config,
                        updated_at = NOW()
                    """,
                    row["id"], row["name"], row["description"], row["collection_name"], row["config"], created_at_dt,
                )
                migrated_kbs += 1
        logger.info(f"Migrated {migrated_kbs} knowledge bases")

        # KB Documents
        kb_docs = scur.execute(
            "SELECT kb_id, doc_id, file_path, content, metadata, embedding, created_at FROM kb_documents"
        ).fetchall()
        migrated_docs = 0
        async with pool.acquire() as conn:
            for row in kb_docs:
                metadata_json: Any = None
                try:
                    metadata_json = json.loads(row["metadata"]) if row["metadata"] else None
                except Exception:
                    metadata_json = None
                created_at_dt = _coerce_datetime(row["created_at"]) if "created_at" in row.keys() else datetime.now(timezone.utc)
                await conn.execute(
                    """
                    INSERT INTO kb_documents (kb_id, doc_id, file_path, content, metadata, embedding, created_at)
                    VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7)
                    ON CONFLICT (kb_id, doc_id) DO UPDATE SET
                        file_path = EXCLUDED.file_path,
                        content = EXCLUDED.content,
                        metadata = EXCLUDED.metadata,
                        embedding = EXCLUDED.embedding
                    """,
                    row["kb_id"], row["doc_id"], row["file_path"], row["content"], json.dumps(metadata_json) if metadata_json is not None else None, row["embedding"], created_at_dt,
                )
                migrated_docs += 1
        logger.info(f"Migrated {migrated_docs} KB documents")

    await pool.close()
    logger.info("SQLite to PostgreSQL migration complete")


if __name__ == "__main__":
    asyncio.run(migrate())
