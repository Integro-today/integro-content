"""Database path configuration for Railway deployment."""

import os
from pathlib import Path


def get_database_path():
    """Get database path with Railway volume support."""
    
    # Use Railway's automatic volume detection if available
    railway_volume_path = os.getenv('RAILWAY_VOLUME_MOUNT_PATH')
    if railway_volume_path:
        data_dir = Path(railway_volume_path)
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    
    # Fallback: Use /app/data for Railway deployment (persistent volume)
    if os.getenv('RAILWAY_ENVIRONMENT'):
        data_dir = Path('/app/data')
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    else:
        # Local development uses current directory
        return Path('.')


def get_config_db_path():
    """Get path to configs.db."""
    return get_database_path() / 'configs.db'


def get_sessions_db_path():
    """Get path to sessions.db."""
    return get_database_path() / 'sessions.db'


def get_memory_db_path():
    """Get path to memory.db."""
    return get_database_path() / 'memory.db'


def get_qdrant_data_path():
    """Get path for Qdrant storage directory."""
    qdrant_dir = get_database_path() / 'qdrant' / 'storage'
    qdrant_dir.mkdir(parents=True, exist_ok=True)
    return qdrant_dir


def get_qdrant_snapshots_path():
    """Get path for Qdrant snapshots directory."""
    snapshots_dir = get_database_path() / 'qdrant' / 'snapshots'
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    return snapshots_dir


def get_backup_path():
    """Get path for backup storage."""
    backup_dir = get_database_path() / 'backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def get_logs_path():
    """Get path for log storage."""
    logs_dir = get_database_path() / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir