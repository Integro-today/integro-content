"""Storage factory for automatic PostgreSQL/SQLite detection."""

import os
from typing import Optional, Any
from integro.utils.logging import get_logger

logger = get_logger(__name__)


def create_storage_adapter(
    name: str = "integro",
    enable_storage: bool = True,
    storage_db_file: str = "sessions.db",
    table_name: Optional[str] = None,
    auto_upgrade_schema: bool = True
) -> Optional[Any]:
    """
    Create appropriate storage adapter based on environment.
    
    Automatically detects PostgreSQL availability via DATABASE_URL.
    Falls back to SQLite if PostgreSQL is not available.
    
    Args:
        name: Agent name for table naming
        enable_storage: Whether to enable storage
        storage_db_file: SQLite database file path (fallback)
        table_name: Override table name (optional)
        auto_upgrade_schema: Auto-upgrade database schema
    
    Returns:
        Storage adapter instance or None
    """
    if not enable_storage:
        return None
    
    # Generate table name if not provided
    if not table_name:
        table_name = f"{name.lower().replace(' ', '_')}_sessions"
    
    # Check for PostgreSQL availability
    db_url = os.getenv("DATABASE_URL")
    railway_env = os.getenv("RAILWAY_ENVIRONMENT")
    
    if db_url:
        try:
            # Agno v2 Postgres database
            from agno.db.postgres import PostgresDb as Storage
            PostgresStorage = Storage

            logger.info(f"PostgreSQL detected (env: {railway_env}), initializing Postgres session storage")
            logger.info(f"Database URL: {db_url[:30]}...")

            # Try multiple constructor signatures to be compatible across versions
            attempts = [
                {"sessions_table": table_name, "db_url": db_url},
                {"sessions_table": table_name, "url": db_url},
                {"db_url": db_url},
                {"url": db_url},
            ]
            last_err = None
            for params in attempts:
                try:
                    storage = PostgresStorage(**params)
                    logger.info(f"PostgresStorage initialized (params: {list(params.keys())})")
                    return storage
                except Exception as e:  # noqa: BLE001
                    last_err = e
                    continue
            raise RuntimeError(f"All PostgresDb init attempts failed: {last_err}")

        except ImportError as e:
            logger.warning(f"PostgreSQL libraries not installed: {e}")
            logger.warning("Falling back to SQLite storage")
        except Exception as e:
            logger.error(f"Failed to initialize PostgresStorage: {e}")
            logger.warning("Falling back to SQLite storage")
    
    # Fallback to SQLite
    try:
        # Direct Agno v2 import - using db not storage
        from agno.db.sqlite import SqliteDb as Storage
        SqliteStorage = Storage
        
        # Determine SQLite path based on environment
        if railway_env:
            # Use Railway volume path
            volume_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "/app/data")
            db_path = os.path.join(volume_path, storage_db_file)
            logger.info(f"Railway environment detected, using volume path: {db_path}")
        else:
            # Use local path
            db_path = storage_db_file
            logger.info(f"Local environment, using SQLite at: {db_path}")
        
        # SqliteDb in v2 - check what parameters it actually accepts
        try:
            # Try with no table parameter (it may manage tables internally)
            storage = SqliteStorage(
                db_file=db_path
                # table parameters handled internally by SqliteDb
            )
        except Exception as e:
            logger.error(f"Failed to create SqliteDb with db_file only: {e}")
            # Fallback to old parameter if needed
            try:
                storage = SqliteStorage(
                    table_name=table_name,
                    db_file=db_path
                )
            except:
                # Last resort - just db_file
                storage = SqliteStorage(db_file=db_path)
        
        logger.info(f"SqliteStorage initialized with table '{table_name}'")
        return storage
        
    except Exception as e:
        logger.error(f"Failed to initialize SqliteStorage: {e}")
        return None


def get_storage_info() -> dict:
    """
    Get information about current storage configuration.
    
    Returns:
        Dictionary with storage information
    """
    db_url = os.getenv("DATABASE_URL")
    railway_env = os.getenv("RAILWAY_ENVIRONMENT")
    volume_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "/app/data")
    
    info = {
        "has_postgres": bool(db_url),
        "railway_environment": railway_env,
        "volume_path": volume_path if railway_env else None,
        "storage_type": "PostgreSQL" if db_url else "SQLite"
    }
    
    if db_url:
        # Parse database URL for info (without password)
        try:
            from urllib.parse import urlparse
            parsed = urlparse(db_url)
            info["postgres_host"] = parsed.hostname
            info["postgres_port"] = parsed.port
            info["postgres_database"] = parsed.path.lstrip('/')
            info["postgres_user"] = parsed.username
        except:
            pass
    
    return info


def test_storage_connection() -> bool:
    """
    Test if storage connection works.
    
    Returns:
        True if connection successful
    """
    try:
        storage = create_storage_adapter(
            name="test",
            enable_storage=True
        )
        
        if storage:
            # Try to access the storage (this will create tables if needed)
            if hasattr(storage, 'get_all_session_ids'):
                # This is a method available in both PostgresStorage and SqliteStorage
                storage.get_all_session_ids("test_user")
            return True
            
    except Exception as e:
        logger.error(f"Storage connection test failed: {e}")
    
    return False