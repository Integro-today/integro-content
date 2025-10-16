#!/usr/bin/env python3
"""Verify Railway deployment configuration and volume mounts."""

import os
import sys
from pathlib import Path
import logging

# Add parent directory to path so we can import integro
sys.path.insert(0, str(Path(__file__).parent.parent))

from integro.config.database import get_database_path, get_config_db_path
from integro.memory.qdrant import QdrantMemory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_environment():
    """Verify Railway environment variables."""
    logger.info("=== Environment Verification ===")
    
    # Check Railway detection
    railway_env = os.getenv('RAILWAY_ENVIRONMENT')
    logger.info(f"RAILWAY_ENVIRONMENT: {railway_env}")
    
    # Check Qdrant configuration
    qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
    qdrant_port = os.getenv('QDRANT_PORT', '6333')
    logger.info(f"QDRANT_HOST: {qdrant_host}")
    logger.info(f"QDRANT_PORT: {qdrant_port}")
    
    # Check API keys
    groq_key = os.getenv('GROQ_API_KEY', 'NOT_SET')
    logger.info(f"GROQ_API_KEY: {'SET' if groq_key != 'NOT_SET' and len(groq_key) > 10 else 'NOT_SET'}")

def verify_volume_paths():
    """Verify volume mount paths."""
    logger.info("=== Volume Path Verification ===")
    
    # Get database paths
    db_path = get_database_path()
    config_path = get_config_db_path()
    
    logger.info(f"Database directory: {db_path}")
    logger.info(f"Config database path: {config_path}")
    logger.info(f"Database directory exists: {db_path.exists()}")
    logger.info(f"Database directory is writable: {os.access(db_path, os.W_OK) if db_path.exists() else 'Unknown'}")
    
    # Test creating a file in the volume
    try:
        test_file = db_path / "test_write.txt"
        test_file.write_text("Railway volume test")
        test_file.unlink()
        logger.info("✅ Volume write test: SUCCESS")
    except Exception as e:
        logger.error(f"❌ Volume write test: FAILED - {e}")

def verify_qdrant_connection():
    """Verify Qdrant connection."""
    logger.info("=== Qdrant Connection Verification ===")
    
    try:
        # Test QdrantMemory initialization (uses Railway environment variables)
        memory = QdrantMemory(user_id="test_user")
        
        # Try to get collections (this will test the connection)
        collections = memory.client.get_collections()
        logger.info(f"✅ Qdrant connection: SUCCESS")
        logger.info(f"Collections found: {len(collections.collections)}")
        
        # Test collection creation
        memory._ensure_collection()
        logger.info(f"✅ Collection creation: SUCCESS")
        
    except Exception as e:
        logger.error(f"❌ Qdrant connection: FAILED - {e}")

def main():
    """Run all verification checks."""
    logger.info("Starting Railway deployment verification...")
    
    verify_environment()
    verify_volume_paths()
    verify_qdrant_connection()
    
    logger.info("Verification complete!")

if __name__ == "__main__":
    main()