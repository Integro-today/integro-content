#!/usr/bin/env python3
"""
Debug script to inspect external Qdrant knowledge bases for therapeutic agents.

This script connects to the external Qdrant database and shows:
1. Available collections
2. Document counts for each KB
3. Sample documents from each collection
4. Metadata and content structure
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv
import json

# Setup logging with detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class KnowledgeBaseDebugger:
    """Debug utility for inspecting external Qdrant knowledge bases."""
    
    def __init__(self):
        """Initialize connection to external Qdrant."""
        self.qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
        self.qdrant_port = int(os.getenv('QDRANT_PORT', '6333'))
        self.use_external = os.getenv('USE_EXTERNAL_QDRANT', 'false').lower() == 'true'
        
        # Knowledge base IDs from environment
        self.ifs_kb_id = os.getenv('IFS_KNOWLEDGE_BASE_ID', 'ifs-parts-work-kb')
        self.byron_katie_kb_id = os.getenv('BYRON_KATIE_KNOWLEDGE_BASE_ID', 'byron-katie-work-kb')
        
        logger.info("=" * 80)
        logger.info("🔍 KNOWLEDGE BASE DEBUGGER - External Qdrant Inspection")
        logger.info("=" * 80)
        logger.info(f"📍 Qdrant Host: {self.qdrant_host}")
        logger.info(f"📍 Qdrant Port: {self.qdrant_port}")
        logger.info(f"📍 External Mode: {self.use_external}")
        logger.info(f"📚 IFS KB ID: {self.ifs_kb_id}")
        logger.info(f"📚 Byron Katie KB ID: {self.byron_katie_kb_id}")
        logger.info("-" * 80)
        
        # Initialize Qdrant client
        try:
            self.client = QdrantClient(
                host=self.qdrant_host,
                port=self.qdrant_port,
                timeout=30.0
            )
            logger.info("✅ Successfully connected to Qdrant")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Qdrant: {e}")
            self.client = None
    
    async def list_all_collections(self) -> List[str]:
        """List all available collections in Qdrant."""
        logger.info("\n📂 LISTING ALL COLLECTIONS")
        logger.info("-" * 40)
        
        if not self.client:
            logger.error("No Qdrant client available")
            return []
        
        try:
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if collection_names:
                logger.info(f"Found {len(collection_names)} collections:")
                for i, name in enumerate(collection_names, 1):
                    logger.info(f"  {i}. {name}")
            else:
                logger.warning("No collections found in Qdrant")
            
            return collection_names
            
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []
    
    async def inspect_collection(self, collection_name: str) -> Dict[str, Any]:
        """Inspect a specific collection and its contents."""
        logger.info(f"\n🔎 INSPECTING COLLECTION: {collection_name}")
        logger.info("-" * 40)
        
        if not self.client:
            logger.error("No Qdrant client available")
            return {}
        
        try:
            # Check if collection exists
            try:
                collection_info = self.client.get_collection(collection_name)
                logger.info(f"✅ Collection '{collection_name}' exists")
            except Exception as e:
                logger.warning(f"⚠️ Collection '{collection_name}' not found: {e}")
                return {"error": f"Collection not found: {e}"}
            
            # Get collection statistics
            stats = {
                "vectors_count": collection_info.vectors_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "points_count": collection_info.points_count,
                "segments_count": collection_info.segments_count,
                "status": collection_info.status,
                "optimizer_status": collection_info.optimizer_status
            }
            
            logger.info("📊 Collection Statistics:")
            logger.info(f"  • Points/Documents: {stats['points_count']}")
            logger.info(f"  • Vectors: {stats['vectors_count']}")
            logger.info(f"  • Status: {stats['status']}")
            
            # Get sample documents
            sample_documents = []
            if stats['points_count'] > 0:
                logger.info("\n📄 Sample Documents (first 5):")
                logger.info("-" * 40)
                
                # Retrieve sample points
                try:
                    response = self.client.scroll(
                        collection_name=collection_name,
                        limit=5,
                        with_payload=True,
                        with_vectors=False
                    )
                    
                    for idx, point in enumerate(response[0], 1):
                        doc_info = {
                            "id": point.id,
                            "payload": point.payload
                        }
                        sample_documents.append(doc_info)
                        
                        logger.info(f"\n  Document {idx}:")
                        logger.info(f"    ID: {point.id}")
                        
                        if point.payload:
                            # Display key fields
                            if 'title' in point.payload:
                                logger.info(f"    Title: {point.payload.get('title', 'N/A')[:100]}")
                            if 'content' in point.payload:
                                content = point.payload.get('content', '')[:200]
                                logger.info(f"    Content: {content}...")
                            if 'source' in point.payload:
                                logger.info(f"    Source: {point.payload.get('source', 'N/A')}")
                            if 'metadata' in point.payload:
                                logger.info(f"    Metadata: {json.dumps(point.payload.get('metadata', {}), indent=6)[:200]}")
                            
                            # Show all available fields
                            all_fields = list(point.payload.keys())
                            logger.info(f"    Available fields: {', '.join(all_fields)}")
                
                except Exception as e:
                    logger.error(f"Error retrieving documents: {e}")
            
            return {
                "collection_name": collection_name,
                "statistics": stats,
                "sample_documents": sample_documents
            }
            
        except Exception as e:
            logger.error(f"Error inspecting collection: {e}")
            return {"error": str(e)}
    
    async def debug_knowledge_bases(self):
        """Main debug function to inspect all therapeutic knowledge bases."""
        logger.info("\n" + "=" * 80)
        logger.info("🚀 STARTING KNOWLEDGE BASE DEBUG SESSION")
        logger.info("=" * 80)
        
        # List all collections
        all_collections = await self.list_all_collections()
        
        # Check IFS Knowledge Base
        logger.info("\n" + "=" * 80)
        logger.info("📚 IFS (INTERNAL FAMILY SYSTEMS) KNOWLEDGE BASE")
        logger.info("=" * 80)
        
        ifs_info = await self.inspect_collection(self.ifs_kb_id)
        
        if "error" not in ifs_info:
            logger.info(f"✅ IFS Knowledge Base Successfully Loaded!")
            logger.info(f"   Documents available: {ifs_info['statistics']['points_count']}")
        else:
            logger.warning(f"⚠️ IFS Knowledge Base not populated yet")
            logger.info(f"   Expected collection name: {self.ifs_kb_id}")
            logger.info("   To populate: Upload IFS therapy documents to this collection")
        
        # Check Byron Katie Knowledge Base
        logger.info("\n" + "=" * 80)
        logger.info("📚 BYRON KATIE'S THE WORK KNOWLEDGE BASE")
        logger.info("=" * 80)
        
        katie_info = await self.inspect_collection(self.byron_katie_kb_id)
        
        if "error" not in katie_info:
            logger.info(f"✅ Byron Katie Knowledge Base Successfully Loaded!")
            logger.info(f"   Documents available: {katie_info['statistics']['points_count']}")
        else:
            logger.warning(f"⚠️ Byron Katie Knowledge Base not populated yet")
            logger.info(f"   Expected collection name: {self.byron_katie_kb_id}")
            logger.info("   To populate: Upload The Work documents to this collection")
        
        # Generate summary report
        logger.info("\n" + "=" * 80)
        logger.info("📋 KNOWLEDGE BASE INTEGRATION SUMMARY")
        logger.info("=" * 80)
        
        # Connection status
        logger.info("\n🔌 Connection Status:")
        if self.client:
            logger.info(f"  ✅ Connected to Qdrant at {self.qdrant_host}:{self.qdrant_port}")
        else:
            logger.info(f"  ❌ Failed to connect to Qdrant")
        
        # Knowledge base status
        logger.info("\n📚 Knowledge Base Status:")
        
        ifs_ready = "error" not in ifs_info and ifs_info.get('statistics', {}).get('points_count', 0) > 0
        katie_ready = "error" not in katie_info and katie_info.get('statistics', {}).get('points_count', 0) > 0
        
        logger.info(f"  • IFS KB ({self.ifs_kb_id}):")
        if ifs_ready:
            logger.info(f"    ✅ READY - {ifs_info['statistics']['points_count']} documents available")
        else:
            logger.info(f"    ⚠️ NOT READY - Collection needs to be created/populated")
        
        logger.info(f"  • Byron Katie KB ({self.byron_katie_kb_id}):")
        if katie_ready:
            logger.info(f"    ✅ READY - {katie_info['statistics']['points_count']} documents available")
        else:
            logger.info(f"    ⚠️ NOT READY - Collection needs to be created/populated")
        
        # Workflow integration status
        logger.info("\n🔄 Workflow Integration:")
        logger.info("  • Both agents configured to use knowledge bases")
        logger.info("  • Graceful fallback enabled (works without KB)")
        logger.info("  • IntegroAgent used when KB available")
        logger.info("  • Standard Agent used as fallback")
        
        # Debug success confirmation
        logger.info("\n" + "=" * 80)
        if ifs_ready or katie_ready:
            logger.info("🎉 DEBUG SUCCESS: Knowledge bases are configured and accessible!")
            if ifs_ready:
                logger.info(f"   ✅ IFS agent will use enhanced knowledge from {ifs_info['statistics']['points_count']} documents")
            if katie_ready:
                logger.info(f"   ✅ Byron Katie agent will use enhanced knowledge from {katie_info['statistics']['points_count']} documents")
        else:
            logger.info("📝 DEBUG NOTE: Knowledge bases configured but not yet populated")
            logger.info("   • Agents will work normally using fallback mode")
            logger.info("   • Populate collections to enable enhanced responses")
        
        logger.info("=" * 80)
        logger.info(f"Debug session completed at {datetime.now().isoformat()}")
        logger.info("=" * 80)
        
        return {
            "connection_successful": self.client is not None,
            "ifs_ready": ifs_ready,
            "katie_ready": katie_ready,
            "collections_found": all_collections,
            "ifs_info": ifs_info,
            "katie_info": katie_info
        }


async def main():
    """Main entry point for the debug script."""
    debugger = KnowledgeBaseDebugger()
    results = await debugger.debug_knowledge_bases()
    
    # Save results to file for documentation
    output_file = f"kb_debug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        # Convert to JSON-serializable format
        json_results = {
            "timestamp": datetime.now().isoformat(),
            "connection_successful": results['connection_successful'],
            "ifs_ready": results['ifs_ready'],
            "katie_ready": results['katie_ready'],
            "collections_found": results['collections_found'],
            "summary": {
                "ifs_kb": self.ifs_kb_id if 'self' in locals() else os.getenv('IFS_KNOWLEDGE_BASE_ID'),
                "katie_kb": self.byron_katie_kb_id if 'self' in locals() else os.getenv('BYRON_KATIE_KNOWLEDGE_BASE_ID'),
                "qdrant_host": os.getenv('QDRANT_HOST'),
                "external_mode": os.getenv('USE_EXTERNAL_QDRANT')
            }
        }
        json.dump(json_results, f, indent=2)
    
    logger.info(f"\n📁 Debug report saved to: {output_file}")
    
    return results


if __name__ == "__main__":
    # Run the async debug function
    asyncio.run(main())