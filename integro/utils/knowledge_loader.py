"""Knowledge base loader utility for therapeutic agents."""

import os
import logging
from typing import Optional
from integro.memory.knowledge import KnowledgeBase
from integro.config.storage import ConfigStorage

logger = logging.getLogger(__name__)


class TherapeuticKnowledgeLoader:
    """Utility for loading knowledge bases for therapeutic agents."""
    
    def __init__(self):
        self.storage = ConfigStorage()
        
    async def load_knowledge_base(self, kb_id: str) -> Optional[KnowledgeBase]:
        """
        Load a knowledge base by ID from external Qdrant.
        
        Args:
            kb_id: Knowledge base identifier from environment variables
            
        Returns:
            KnowledgeBase instance or None if loading fails
        """
        if not kb_id:
            logger.info("No knowledge base ID provided")
            return None
            
        try:
            # Load knowledge base configuration
            kb_config = await self.storage.load_knowledge_base(kb_id)
            if not kb_config:
                logger.warning(f"Knowledge base {kb_id} not found in storage")
                return None
                
            logger.info(f"Loading knowledge base: {kb_config.name} ({kb_id})")
            
            # Create knowledge base with external Qdrant connection
            qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
            qdrant_port = int(os.getenv('QDRANT_PORT', '6333'))
            use_external = os.getenv('USE_EXTERNAL_QDRANT', 'false').lower() == 'true'
            
            if not use_external:
                logger.info("External Qdrant disabled, using in-memory storage")
                return None
                
            # Use FastEmbed default if model not specified properly
            embedding_model = kb_config.embedding_model
            if embedding_model == "fastembed":
                embedding_model = "BAAI/bge-small-en-v1.5"
                
            kb = KnowledgeBase(
                collection_name=kb_config.collection_name or kb_id,
                host=qdrant_host,
                port=qdrant_port,
                embedding_model=embedding_model,
                in_memory=False  # Use external Qdrant
            )
            
            # Add debug information about the loaded KB
            try:
                # Try to get collection info for debugging
                from qdrant_client import QdrantClient
                debug_client = QdrantClient(host=qdrant_host, port=qdrant_port)
                collection_info = debug_client.get_collection(kb_config.collection_name or kb_id)
                doc_count = collection_info.points_count
                logger.info(f"✅ Successfully loaded knowledge base: {kb_config.name}")
                logger.info(f"   📚 Collection: {kb_config.collection_name or kb_id}")
                logger.info(f"   📄 Documents available: {doc_count}")
                logger.info(f"   🔗 Qdrant connection: {qdrant_host}:{qdrant_port}")
                logger.info(f"   🤖 Embedding model: {embedding_model}")
            except Exception as debug_error:
                logger.info(f"✅ Knowledge base configured: {kb_config.name}")
                logger.info(f"   (Debug info unavailable: {debug_error})")
            
            return kb
            
        except Exception as e:
            logger.error(f"❌ Failed to load knowledge base {kb_id}: {e}")
            return None
    
    async def load_ifs_knowledge(self) -> Optional[KnowledgeBase]:
        """Load IFS (Internal Family Systems) knowledge base."""
        kb_id = os.getenv('IFS_KNOWLEDGE_BASE_ID')
        if not kb_id:
            logger.info("IFS_KNOWLEDGE_BASE_ID not set - IFS agent will run without knowledge base")
            return None
            
        logger.info(f"Loading IFS knowledge base: {kb_id}")
        return await self.load_knowledge_base(kb_id)
    
    async def load_byron_katie_knowledge(self) -> Optional[KnowledgeBase]:
        """Load Byron Katie's The Work knowledge base.""" 
        kb_id = os.getenv('BYRON_KATIE_KNOWLEDGE_BASE_ID')
        if not kb_id:
            logger.info("BYRON_KATIE_KNOWLEDGE_BASE_ID not set - Byron Katie agent will run without knowledge base")
            return None
            
        logger.info(f"Loading Byron Katie knowledge base: {kb_id}")
        return await self.load_knowledge_base(kb_id)


# Global instance for easy access
knowledge_loader = TherapeuticKnowledgeLoader()