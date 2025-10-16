#!/usr/bin/env python3
"""
Lightweight KB debug script that runs on Railway startup.
Logs knowledge base contents to console for debugging.
"""

import os
import sys
import logging
from qdrant_client import QdrantClient
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - KB-DEBUG - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def debug_knowledge_bases():
    """Quick debug of KB contents on startup."""
    
    # Get configuration
    qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
    qdrant_port = int(os.getenv('QDRANT_PORT', '6333'))
    ifs_kb_id = os.getenv('IFS_KNOWLEDGE_BASE_ID', 'ifs-parts-work-kb')
    byron_katie_kb_id = os.getenv('BYRON_KATIE_KNOWLEDGE_BASE_ID', 'byron-katie-work-kb')
    
    logger.info("=" * 60)
    logger.info("🔍 KNOWLEDGE BASE DEBUG - Railway Startup Check")
    logger.info("=" * 60)
    logger.info(f"Qdrant: {qdrant_host}:{qdrant_port}")
    logger.info(f"IFS KB ID (from env): {ifs_kb_id}")
    logger.info(f"Byron Katie KB ID (from env): {byron_katie_kb_id}")
    logger.info("-" * 60)
    
    try:
        # Connect to Qdrant with very short timeout
        # Check if we need an API key
        api_key = os.getenv('QDRANT_API_KEY')
        if api_key:
            logger.info(f"🔑 Using Qdrant API key (length: {len(api_key)})")
            client = QdrantClient(host=qdrant_host, port=qdrant_port, api_key=api_key, timeout=1.0)
        else:
            logger.info("🔓 No Qdrant API key configured")
            client = QdrantClient(host=qdrant_host, port=qdrant_port, timeout=1.0)
        
        # First, list ALL available collections
        logger.info("📚 Listing ALL available collections in Qdrant:")
        try:
            collections = client.get_collections()
            if collections.collections:
                logger.info(f"Found {len(collections.collections)} collections:")
                for collection in collections.collections:
                    logger.info(f"  - Collection: {collection.name}")
                    # Try to get more info if possible
                    try:
                        info = client.get_collection(collection.name)
                        logger.info(f"    Points: {info.points_count}, Status: {info.status}")
                    except Exception as e:
                        logger.info(f"    (Could not get details: {e})")
            else:
                logger.warning("⚠️ No collections found in Qdrant!")
        except Exception as e:
            logger.error(f"❌ Could not list collections: {e}")
        
        logger.info("-" * 60)
        
        # Check IFS KB
        try:
            ifs_info = client.get_collection(ifs_kb_id)
            logger.info(f"✅ IFS KB LOADED: {ifs_info.points_count} documents")
            
            # Get sample document
            if ifs_info.points_count > 0:
                sample = client.scroll(collection_name=ifs_kb_id, limit=1, with_payload=True)[0]
                if sample:
                    logger.info(f"   Sample: {str(sample[0].payload)[:200]}...")
        except Exception as e:
            logger.warning(f"⚠️ IFS KB not found: {e}")
        
        # Check Byron Katie KB
        try:
            katie_info = client.get_collection(byron_katie_kb_id)
            logger.info(f"✅ BYRON KATIE KB LOADED: {katie_info.points_count} documents")
            
            # Get sample document
            if katie_info.points_count > 0:
                sample = client.scroll(collection_name=byron_katie_kb_id, limit=1, with_payload=True)[0]
                if sample:
                    logger.info(f"   Sample: {str(sample[0].payload)[:200]}...")
        except Exception as e:
            logger.warning(f"⚠️ Byron Katie KB not found: {e}")
        
        logger.info("=" * 60)
        logger.info("KB Debug Complete - Service Starting")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Could not connect to Qdrant: {e}")
        logger.info("Continuing with workflow startup (fallback mode)")

if __name__ == "__main__":
    debug_knowledge_bases()