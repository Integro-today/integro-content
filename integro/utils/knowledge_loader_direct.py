"""Direct knowledge base loader for therapeutic agents - bypasses ConfigStorage."""

import os
import logging
from typing import Optional
from integro.memory.knowledge import KnowledgeBase

logger = logging.getLogger(__name__)


class DirectTherapeuticKnowledgeLoader:
    """Direct loader for knowledge bases from Qdrant without ConfigStorage."""
    
    async def load_knowledge_base_direct(self, collection_name: str, name: str = None) -> Optional[KnowledgeBase]:
        """
        Load a knowledge base directly from Qdrant by collection name.
        
        Args:
            collection_name: Qdrant collection name (e.g., kb_c38f320c)
            name: Display name for logging (optional)
            
        Returns:
            KnowledgeBase instance or None if loading fails
        """
        if not collection_name:
            logger.info("No collection name provided")
            return None
            
        try:
            # Get Qdrant connection details
            qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
            qdrant_port = int(os.getenv('QDRANT_PORT', '6333'))
            use_external = os.getenv('USE_EXTERNAL_QDRANT', 'false').lower() == 'true'
            
            if not use_external:
                logger.info("External Qdrant disabled, using in-memory storage")
                return None
            
            logger.info(f"Attempting direct connection to Qdrant collection: {collection_name}")
            logger.info(f"Qdrant endpoint: {qdrant_host}:{qdrant_port}")
            
            # Use default embedding model for compatibility
            embedding_model = "BAAI/bge-small-en-v1.5"
            
            # Create knowledge base with direct Qdrant connection
            # KnowledgeBase expects a URL, not separate host/port
            qdrant_url = f"http://{qdrant_host}:{qdrant_port}"
            
            kb = KnowledgeBase(
                collection_name=collection_name,
                url=qdrant_url,
                embedding_model=embedding_model,
                in_memory=False  # Use external Qdrant
            )
            
            # Verify the collection exists and get info
            try:
                from qdrant_client import QdrantClient
                debug_client = QdrantClient(host=qdrant_host, port=qdrant_port)
                collection_info = debug_client.get_collection(collection_name)
                doc_count = collection_info.points_count
                
                display_name = name or collection_name
                logger.info(f"✅ Successfully connected to knowledge base: {display_name}")
                logger.info(f"   📚 Collection: {collection_name}")
                logger.info(f"   📄 Documents available: {doc_count}")
                logger.info(f"   🔗 Qdrant connection: {qdrant_host}:{qdrant_port}")
                logger.info(f"   🤖 Embedding model: {embedding_model}")
                
                return kb
                
            except Exception as verify_error:
                logger.warning(f"⚠️ Collection {collection_name} verification failed: {verify_error}")
                logger.info("Collection may not exist or may be empty")
                return None
            
        except Exception as e:
            logger.error(f"❌ Failed to load knowledge base {collection_name}: {e}")
            return None
    
    async def load_ifs_knowledge(self) -> Optional[KnowledgeBase]:
        """Load IFS knowledge base directly from Qdrant."""
        collection_name = os.getenv('IFS_KNOWLEDGE_BASE_ID')
        if not collection_name:
            logger.info("IFS_KNOWLEDGE_BASE_ID not set - IFS agent will run without knowledge base")
            return None
            
        logger.info(f"Loading IFS knowledge base directly: {collection_name}")
        return await self.load_knowledge_base_direct(collection_name, "IFS Knowledge Base")
    
    async def load_byron_katie_knowledge(self) -> Optional[KnowledgeBase]:
        """Load Byron Katie's knowledge base directly from Qdrant."""
        collection_name = os.getenv('BYRON_KATIE_KNOWLEDGE_BASE_ID')
        if not collection_name:
            logger.info("BYRON_KATIE_KNOWLEDGE_BASE_ID not set - Byron Katie agent will run without knowledge base")
            return None
            
        logger.info(f"Loading Byron Katie knowledge base directly: {collection_name}")
        return await self.load_knowledge_base_direct(collection_name, "Byron Katie Knowledge Base")


# Global instance for easy access
direct_knowledge_loader = DirectTherapeuticKnowledgeLoader()