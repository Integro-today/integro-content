"""Unified storage for agent and knowledge base configurations.

This module supports both SQLite (default) and PostgreSQL (when DATABASE_URL
environment variable is set). The public API remains the same to avoid changes
across the codebase. When PostgreSQL is enabled, JSON fields are stored as
JSONB and embeddings as BYTEA.
"""

import json
import os
import sqlite3
import aiosqlite
import asyncpg
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from contextlib import asynccontextmanager
from integro.config.agent_loader import AgentConfig
from integro.config.kb_loader import KnowledgeBaseConfig
from integro.config.database import get_config_db_path
from integro.utils.logging import get_logger

logger = get_logger(__name__)


class ConfigStorage:
    """Configuration storage with SQLite and PostgreSQL backends."""
    
    def __init__(self, db_path: Union[str, Path] = None):
        """
        Initialize configuration storage.
        
        Args:
            db_path: Path to SQLite database (defaults to Railway-aware path).
                    Ignored when DATABASE_URL is set.
        """
        self.database_url = os.getenv("DATABASE_URL")
        self.pg_pool: Optional[asyncpg.Pool] = None
        # print("=======================================")
        # print(self.database_url)
        # print("=======================================")
        if self.database_url:
            # Defer postgres pool creation to first async operation
            self.db_path = None  # Not used in PG mode
        else:
            if db_path is None:
                self.db_path = get_config_db_path()
            else:
                self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._init_db()

    async def _ensure_pg(self) -> None:
        """Ensure PostgreSQL pool is ready and schema initialized."""
        if not self.database_url:
            return
        if self.pg_pool is not None:
            return
        # Create connection pool
        self.pg_pool = await asyncpg.create_pool(self.database_url, min_size=1, max_size=10)
        # Initialize schema if not exists
        async with self.pg_pool.acquire() as conn:
            # Create tables
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
            # Indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_kb_name ON knowledge_bases(name)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_kb_docs ON kb_documents(kb_id)")
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Ben, create agents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    config TEXT NOT NULL,
                    knowledge_base_id TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id)
                )
            """)
            
            # Ben, create knowledge bases table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_bases (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    collection_name TEXT,
                    config TEXT NOT NULL,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            
            # Ben, create documents table for tracking KB documents
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kb_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kb_id TEXT NOT NULL,
                    doc_id TEXT NOT NULL,
                    file_path TEXT,
                    content TEXT,
                    metadata TEXT,
                    embedding BLOB,
                    created_at TEXT,
                    FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id),
                    UNIQUE(kb_id, doc_id)
                )
            """)
            
            # Ben, create indices for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kb_name ON knowledge_bases(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kb_docs ON kb_documents(kb_id)")
            
            conn.commit()
        
        logger.info(f"Initialized config storage at {self.db_path}")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get async SQLite connection.

        Only available in SQLite mode. In PostgreSQL mode, prefer using the
        high-level methods in this class. This method is retained for backward
        compatibility with older code paths that perform raw SQL on SQLite.
        """
        if self.database_url:
            raise RuntimeError("get_connection() is not available in PostgreSQL mode")
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            yield conn
    
    # Agent methods
    
    async def save_agent(self, agent_config: AgentConfig) -> str:
        """
        Save agent configuration to database.
        
        Args:
            agent_config: AgentConfig object
            
        Returns:
            Agent ID
        """
        # Ben, generate ID if not present
        agent_id = agent_config.name.lower().replace(" ", "_")
        now = datetime.utcnow().isoformat()
        
        if self.database_url:
            await self._ensure_pg()
            async with self.pg_pool.acquire() as conn:
                # Ensure created_at is a proper datetime for PostgreSQL
                created_at_dt = None
                if agent_config.created_at:
                    try:
                        created_at_dt = agent_config.created_at if hasattr(agent_config.created_at, 'isoformat') else datetime.fromisoformat(str(agent_config.created_at))
                    except Exception:
                        created_at_dt = None
                await conn.execute(
                    """
                    INSERT INTO agents (id, name, description, config, knowledge_base_id, created_at, updated_at)
                    VALUES ($1, $2, $3, $4::jsonb, $5, COALESCE($6, NOW()), NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        config = EXCLUDED.config,
                        knowledge_base_id = EXCLUDED.knowledge_base_id,
                        updated_at = NOW()
                    """,
                    agent_id,
                    agent_config.name,
                    agent_config.description,
                    json.dumps(agent_config.to_dict()),
                    agent_config.knowledge_base_id,
                    created_at_dt,
                )
        else:
            async with self.get_connection() as conn:
                await conn.execute("""
                    INSERT OR REPLACE INTO agents 
                    (id, name, description, config, knowledge_base_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    agent_id,
                    agent_config.name,
                    agent_config.description,
                    json.dumps(agent_config.to_dict()),
                    agent_config.knowledge_base_id,
                    agent_config.created_at or now,
                    now
                ))
                await conn.commit()
        
        logger.info(f"Saved agent '{agent_config.name}' to storage")
        return agent_id
    
    async def load_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """
        Load agent configuration from database.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            AgentConfig or None if not found
        """
        if self.database_url:
            await self._ensure_pg()
            async with self.pg_pool.acquire() as conn:
                row = await conn.fetchrow("SELECT config FROM agents WHERE id = $1", agent_id)
                if row:
                    config_data = row["config"] if isinstance(row["config"], dict) else json.loads(row["config"])  # type: ignore
                    return AgentConfig.from_dict(config_data)
        else:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT config FROM agents WHERE id = ?",
                    (agent_id,)
                )
                row = await cursor.fetchone()
                
                if row:
                    config_data = json.loads(row['config'])
                    return AgentConfig.from_dict(config_data)
        
        return None
    
    async def list_agents(self) -> List[Dict[str, Any]]:
        """
        List all agents in storage.
        
        Returns:
            List of agent summaries
        """
        if self.database_url:
            await self._ensure_pg()
            async with self.pg_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, name, description, knowledge_base_id, created_at, updated_at
                    FROM agents
                    ORDER BY name
                    """
                )
                return [dict(r) for r in rows]
        else:
            async with self.get_connection() as conn:
                cursor = await conn.execute("""
                    SELECT id, name, description, knowledge_base_id, created_at, updated_at
                    FROM agents
                    ORDER BY name
                """)
                rows = await cursor.fetchall()
                
                return [dict(row) for row in rows]
    
    async def delete_agent(self, agent_id: str) -> bool:
        """
        Delete agent from storage.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if deleted
        """
        if self.database_url:
            await self._ensure_pg()
            async with self.pg_pool.acquire() as conn:
                result = await conn.execute("DELETE FROM agents WHERE id = $1", agent_id)
                # result is a string like 'DELETE <n>'
                try:
                    return int(result.split()[-1]) > 0
                except Exception:
                    return False
        else:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    "DELETE FROM agents WHERE id = ?",
                    (agent_id,)
                )
                await conn.commit()
                
                return cursor.rowcount > 0
    
    # Knowledge base methods
    
    async def save_knowledge_base(self, kb_config: KnowledgeBaseConfig) -> str:
        """
        Save knowledge base configuration to database.
        
        Args:
            kb_config: KnowledgeBaseConfig object
            
        Returns:
            Knowledge base ID
        """
        now = datetime.utcnow().isoformat()
        
        if self.database_url:
            await self._ensure_pg()
            async with self.pg_pool.acquire() as conn:
                created_at_dt = None
                if kb_config.created_at:
                    try:
                        created_at_dt = kb_config.created_at if hasattr(kb_config.created_at, 'isoformat') else datetime.fromisoformat(str(kb_config.created_at))
                    except Exception:
                        created_at_dt = None
                await conn.execute(
                    """
                    INSERT INTO knowledge_bases (id, name, description, collection_name, config, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5::jsonb, COALESCE($6, NOW()), NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        collection_name = EXCLUDED.collection_name,
                        config = EXCLUDED.config,
                        updated_at = NOW()
                    """,
                    kb_config.id,
                    kb_config.name,
                    kb_config.description,
                    kb_config.collection_name,
                    json.dumps(kb_config.to_dict()),
                    created_at_dt,
                )
        else:
            async with self.get_connection() as conn:
                await conn.execute("""
                    INSERT OR REPLACE INTO knowledge_bases
                    (id, name, description, collection_name, config, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    kb_config.id,
                    kb_config.name,
                    kb_config.description,
                    kb_config.collection_name,
                    json.dumps(kb_config.to_dict()),
                    kb_config.created_at or now,
                    now
                ))
                await conn.commit()
        
        logger.info(f"Saved knowledge base '{kb_config.name}' to storage")
        return kb_config.id
    
    async def load_knowledge_base(self, kb_id: str) -> Optional[KnowledgeBaseConfig]:
        """
        Load knowledge base configuration from database.
        
        Args:
            kb_id: Knowledge base ID
            
        Returns:
            KnowledgeBaseConfig or None if not found
        """
        if self.database_url:
            await self._ensure_pg()
            async with self.pg_pool.acquire() as conn:
                row = await conn.fetchrow("SELECT config FROM knowledge_bases WHERE id = $1", kb_id)
                if row:
                    config_data = row["config"] if isinstance(row["config"], dict) else json.loads(row["config"])  # type: ignore
                    return KnowledgeBaseConfig.from_dict(config_data)
        else:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT config FROM knowledge_bases WHERE id = ?",
                    (kb_id,)
                )
                row = await cursor.fetchone()
                
                if row:
                    config_data = json.loads(row['config'])
                    return KnowledgeBaseConfig.from_dict(config_data)
        
        return None
    
    async def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """
        List all knowledge bases in storage.
        
        Returns:
            List of knowledge base summaries
        """
        if self.database_url:
            await self._ensure_pg()
            async with self.pg_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, name, description, collection_name, created_at, updated_at
                    FROM knowledge_bases
                    ORDER BY name
                    """
                )
                return [dict(r) for r in rows]
        else:
            async with self.get_connection() as conn:
                cursor = await conn.execute("""
                    SELECT id, name, description, collection_name, created_at, updated_at
                    FROM knowledge_bases
                    ORDER BY name
                """)
                rows = await cursor.fetchall()
                
                return [dict(row) for row in rows]
    
    async def delete_knowledge_base(self, kb_id: str) -> bool:
        """
        Delete knowledge base from storage.
        
        Args:
            kb_id: Knowledge base ID
            
        Returns:
            True if deleted
        """
        if self.database_url:
            await self._ensure_pg()
            async with self.pg_pool.acquire() as conn:
                # Delete docs first
                await conn.execute("DELETE FROM kb_documents WHERE kb_id = $1", kb_id)
                result = await conn.execute("DELETE FROM knowledge_bases WHERE id = $1", kb_id)
                try:
                    return int(result.split()[-1]) > 0
                except Exception:
                    return False
        else:
            async with self.get_connection() as conn:
                # Ben, also delete associated documents
                await conn.execute(
                    "DELETE FROM kb_documents WHERE kb_id = ?",
                    (kb_id,)
                )
                
                cursor = await conn.execute(
                    "DELETE FROM knowledge_bases WHERE id = ?",
                    (kb_id,)
                )
                await conn.commit()
                
                return cursor.rowcount > 0
    
    # Document methods for knowledge bases
    
    async def save_kb_document(
        self,
        kb_id: str,
        doc_id: str,
        content: str,
        file_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> int:
        """
        Save a document associated with a knowledge base.
        
        Args:
            kb_id: Knowledge base ID
            doc_id: Document ID
            content: Document content
            file_path: Optional source file path
            metadata: Optional metadata
            embedding: Optional embedding vector
            
        Returns:
            Document database ID
        """
        now = datetime.utcnow().isoformat()
        
        if self.database_url:
            await self._ensure_pg()
            # Convert embedding to bytes
            embedding_bytes = None
            if embedding:
                import struct
                embedding_bytes = struct.pack(f'{len(embedding)}f', *embedding)
            async with self.pg_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO kb_documents (kb_id, doc_id, file_path, content, metadata, embedding, created_at)
                    VALUES ($1, $2, $3, $4, $5::jsonb, $6, NOW())
                    ON CONFLICT (kb_id, doc_id) DO UPDATE SET
                        file_path = EXCLUDED.file_path,
                        content = EXCLUDED.content,
                        metadata = EXCLUDED.metadata,
                        embedding = EXCLUDED.embedding
                    """,
                    kb_id,
                    doc_id,
                    file_path,
                    content,
                    json.dumps(metadata) if metadata else None,
                    embedding_bytes,
                )
                # Return a synthetic id (not used by callers)
                return 0
        else:
            async with self.get_connection() as conn:
                # Ben, convert embedding to bytes if provided
                embedding_bytes = None
                if embedding:
                    import struct
                    embedding_bytes = struct.pack(f'{len(embedding)}f', *embedding)
                
                cursor = await conn.execute("""
                    INSERT OR REPLACE INTO kb_documents
                    (kb_id, doc_id, file_path, content, metadata, embedding, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    kb_id,
                    doc_id,
                    file_path,
                    content,
                    json.dumps(metadata) if metadata else None,
                    embedding_bytes,
                    now
                ))
                await conn.commit()
                
                return cursor.lastrowid
    
    async def load_kb_documents(self, kb_id: str) -> List[Dict[str, Any]]:
        """
        Load all documents for a knowledge base.
        
        Args:
            kb_id: Knowledge base ID
            
        Returns:
            List of documents
        """
        if self.database_url:
            await self._ensure_pg()
            async with self.pg_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT doc_id, file_path, content, metadata, embedding, created_at
                    FROM kb_documents
                    WHERE kb_id = $1
                    ORDER BY created_at
                    """,
                    kb_id,
                )
                documents = []
                for row in rows:
                    documents.append({
                        'doc_id': row['doc_id'],
                        'file_path': row['file_path'],
                        'content': row['content'],
                        'metadata': row['metadata'] if isinstance(row['metadata'], dict) else (json.loads(row['metadata']) if row['metadata'] else {}),
                        'embedding': row['embedding'],
                        'created_at': row['created_at'].isoformat() if hasattr(row['created_at'], 'isoformat') else row['created_at']
                    })
                return documents
        else:
            async with self.get_connection() as conn:
                cursor = await conn.execute("""
                    SELECT doc_id, file_path, content, metadata, embedding, created_at
                    FROM kb_documents
                    WHERE kb_id = ?
                    ORDER BY created_at
                """, (kb_id,))
                rows = await cursor.fetchall()
                
                documents = []
                for row in rows:
                    doc = {
                        'doc_id': row['doc_id'],
                        'file_path': row['file_path'],
                        'content': row['content'],
                        'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                        'embedding': row['embedding'],  # Will be bytes or None
                        'created_at': row['created_at']
                    }
                    documents.append(doc)
                
                return documents
    
    async def update_kb_document_embedding(
        self,
        kb_id: str,
        doc_id: str,
        embedding: List[float]
    ) -> bool:
        """
        Update the embedding for a specific document.
        
        Args:
            kb_id: Knowledge base ID
            doc_id: Document ID
            embedding: New embedding vector
            
        Returns:
            Success status
        """
        try:
            import struct
            embedding_bytes = struct.pack(f'{len(embedding)}f', *embedding)
            if self.database_url:
                await self._ensure_pg()
                async with self.pg_pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE kb_documents
                        SET embedding = $1
                        WHERE kb_id = $2 AND doc_id = $3
                        """,
                        embedding_bytes, kb_id, doc_id
                    )
                    return True
            else:
                async with self.get_connection() as conn:
                    await conn.execute(
                        """
                        UPDATE kb_documents
                        SET embedding = ?
                        WHERE kb_id = ? AND doc_id = ?
                        """,
                        (embedding_bytes, kb_id, doc_id)
                    )
                    await conn.commit()
                    
                    return True
        except Exception as e:
            logger.error(f"Error updating document embedding: {e}")
            return False
    
    async def get_agent_with_kb(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent with its associated knowledge base.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent data with knowledge base or None
        """
        if self.database_url:
            await self._ensure_pg()
            async with self.pg_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT a.config AS agent_config, k.config AS kb_config
                    FROM agents a
                    LEFT JOIN knowledge_bases k ON a.knowledge_base_id = k.id
                    WHERE a.id = $1
                    """,
                    agent_id,
                )
                if row:
                    result = {
                        'agent': AgentConfig.from_dict(row['agent_config'] if isinstance(row['agent_config'], dict) else json.loads(row['agent_config']))
                    }
                    if row['kb_config']:
                        result['knowledge_base'] = KnowledgeBaseConfig.from_dict(
                            row['kb_config'] if isinstance(row['kb_config'], dict) else json.loads(row['kb_config'])
                        )
                    return result
        else:
            async with self.get_connection() as conn:
                cursor = await conn.execute("""
                    SELECT 
                        a.config as agent_config,
                        k.config as kb_config
                    FROM agents a
                    LEFT JOIN knowledge_bases k ON a.knowledge_base_id = k.id
                    WHERE a.id = ?
                """, (agent_id,))
                row = await cursor.fetchone()
                
                if row:
                    result = {
                        'agent': AgentConfig.from_dict(json.loads(row['agent_config']))
                    }
                    if row['kb_config']:
                        result['knowledge_base'] = KnowledgeBaseConfig.from_dict(
                            json.loads(row['kb_config'])
                        )
                    return result
        
        return None
    
    async def link_agent_to_kb(self, agent_id: str, kb_id: str) -> bool:
        """
        Link an agent to a knowledge base.
        
        Args:
            agent_id: Agent ID
            kb_id: Knowledge base ID
            
        Returns:
            True if successful
        """
        if self.database_url:
            await self._ensure_pg()
            async with self.pg_pool.acquire() as conn:
                result = await conn.execute(
                    """
                    UPDATE agents
                    SET knowledge_base_id = $1, updated_at = NOW()
                    WHERE id = $2
                    """,
                    kb_id, agent_id
                )
                try:
                    return int(result.split()[-1]) > 0
                except Exception:
                    return False
        else:
            async with self.get_connection() as conn:
                cursor = await conn.execute("""
                    UPDATE agents
                    SET knowledge_base_id = ?, updated_at = ?
                    WHERE id = ?
                """, (kb_id, datetime.utcnow().isoformat(), agent_id))
                await conn.commit()
                
                return cursor.rowcount > 0

    async def clear_kb_documents(self, kb_id: str) -> None:
        """Delete all documents for a knowledge base."""
        if self.database_url:
            await self._ensure_pg()
            async with self.pg_pool.acquire() as conn:
                await conn.execute("DELETE FROM kb_documents WHERE kb_id = $1", kb_id)
        else:
            async with self.get_connection() as conn:
                await conn.execute(
                    "DELETE FROM kb_documents WHERE kb_id = ?",
                    (kb_id,)
                )
                await conn.commit()