"""Qdrant memory adapter for Integro."""

from typing import Dict, Any, List, Optional
from datetime import datetime
# import json
import hashlib
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    # SearchRequest,
    UpdateStatus
)
from fastembed import TextEmbedding
from integro.utils.logging import get_logger

logger = get_logger(__name__)


class QdrantMemory:
    """
    Qdrant-based memory adapter for user-scoped conversations and memories.
    
    Each user gets their own scoped collection for privacy and isolation.
    """
    
    def __init__(
        self,
        user_id: str,
        collection_prefix: str = "integro_memory",
        url: str = None,
        api_key: Optional[str] = None,
        vector_size: Optional[int] = None,
        distance: Distance = Distance.COSINE,
        embedding_model: Optional[Any] = None
    ):
        """
        Initialize Qdrant memory adapter.
        
        Args:
            user_id: Unique user identifier for scoping
            collection_prefix: Prefix for collection names
            url: Qdrant server URL
            api_key: Optional API key for Qdrant
            vector_size: Size of embedding vectors (auto-detected if None)
            distance: Distance metric for similarity
            embedding_model: Either a custom embedding model with embed() method,
                           or a string name for FastEmbed model (default: BAAI/bge-small-en-v1.5)
        """
        self.user_id = user_id
        self.collection_name = f"{collection_prefix}_{self._hash_user_id(user_id)}"
        self.distance = distance
        
        # Ben, we support both FastEmbed models (by name) and custom models here
        if embedding_model is None:
            # Ben, BAAI/bge-small-en-v1.5 is our default - it's fast and accurate enough for most cases
            self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            self._use_fastembed = True
            logger.info("Using default FastEmbed model: BAAI/bge-small-en-v1.5")
        elif isinstance(embedding_model, str):
            # They gave us a model name string, so we'll use FastEmbed with it
            self.embedding_model = TextEmbedding(model_name=embedding_model)
            self._use_fastembed = True
            logger.info(f"Using FastEmbed model: {embedding_model}")
        else:
            # Got a custom model object - needs to have an embed() method
            self.embedding_model = embedding_model
            self._use_fastembed = False
            logger.info("Using custom embedding model")
        
        # Ben, we figure out vector dimensions by running a test embedding
        if vector_size is None:
            # Quick test to see how many dimensions this model outputs
            sample_embedding = self._get_embedding("test")
            self.vector_size = len(sample_embedding)
        else:
            self.vector_size = vector_size
        
        logger.info(f"Vector size: {self.vector_size}")
        
        # Railway-aware Qdrant connection for embedded service
        if url is None:
            import os
            
            # First check for external Qdrant service
            if os.getenv('USE_EXTERNAL_QDRANT') or os.getenv('QDRANT_HOST'):
                host = os.getenv('QDRANT_HOST', 'qdrant.railway.internal')
                port = os.getenv('QDRANT_PORT', '6333')
                url = f"http://{host}:{port}"
                api_key = os.getenv('QDRANT_API_KEY', api_key)
                logger.info(f"Using external Qdrant service: {url}")
            # Check if Qdrant is explicitly disabled (fallback mode)
            elif os.getenv('DISABLE_QDRANT') or os.path.exists('/app/data/qdrant_disabled'):
                logger.warning("Qdrant is disabled - using in-memory storage")
                url = ":memory:"
            elif os.getenv('RAILWAY_ENVIRONMENT'):
                # Railway deployment with embedded Qdrant service
                from integro.utils.qdrant_embedded import get_qdrant_service
                
                try:
                    # Get the embedded service instance
                    qdrant_service = get_qdrant_service()
                    
                    # Use the embedded service connection details
                    url = f"http://{qdrant_service.host}:{qdrant_service.port}"
                    logger.info(f"Using embedded Qdrant service: {url}")
                    
                    # Check if service is running (it should be started by web server)
                    if not qdrant_service.is_running():
                        logger.warning("Embedded Qdrant service not running - it should be started by web server initialization")
                        # Don't start it here - let the web server handle lifecycle
                        
                except Exception as e:
                    logger.error(f"Failed to connect to embedded Qdrant service: {e}")
                    # Fallback to localhost connection
                    url = "http://localhost:6333"
                    logger.warning(f"Falling back to localhost connection: {url}")
            else:
                # Local development - use localhost or in-memory
                # Check for forced in-memory mode first
                if os.getenv('FORCE_IN_MEMORY_QDRANT'):
                    logger.info("Forced to use in-memory mode (FORCE_IN_MEMORY_QDRANT set)")
                    url = ":memory:"
                else:
                    # Check if local Qdrant is available, otherwise use in-memory
                    try:
                        test_client = QdrantClient(url="http://localhost:6333", timeout=2, prefer_grpc=False)
                        test_client.get_collections()
                        url = "http://localhost:6333"
                        logger.info("Local Qdrant server found at localhost:6333")
                    except Exception:
                        # No local Qdrant available, use in-memory
                        url = ":memory:"
                        logger.info("No local Qdrant server found - using in-memory instance")
        
        # Connect to Qdrant with retry logic
        self.client = self._create_client_with_retry(url, api_key)
        
        # Make sure this user has their collection ready
        self._ensure_collection()
    
    def _hash_user_id(self, user_id: str) -> str:
        """Hash user ID for collection naming."""
        return hashlib.md5(user_id.encode()).hexdigest()[:16]
    
    def _create_client_with_retry(self, url: str, api_key: Optional[str] = None, max_retries: int = 5) -> QdrantClient:
        """
        Create Qdrant client with connection retry logic.
        
        Args:
            url: Qdrant server URL
            api_key: Optional API key
            max_retries: Maximum number of connection attempts
            
        Returns:
            Connected QdrantClient instance
            
        Raises:
            ConnectionError: If unable to connect after all retries
        """
        import time
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Create client - handle in-memory differently
                if url == ":memory:":
                    # For in-memory, use location parameter instead of url
                    client = QdrantClient(location=":memory:")
                    logger.info(f"✅ Connected to in-memory Qdrant (attempt {attempt + 1}/{max_retries})")
                else:
                    # For servers, use URL with compatibility check disabled
                    client = QdrantClient(url=url, api_key=api_key, prefer_grpc=False)
                    logger.info(f"✅ Connected to Qdrant at {url} (attempt {attempt + 1}/{max_retries})")
                
                # Test connection by getting collections
                client.get_collections()
                return client
                
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4, 8, 16 seconds
                    logger.warning(f"Qdrant connection attempt {attempt + 1}/{max_retries} failed: {e}")
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Failed to connect to Qdrant after {max_retries} attempts")
        
        # If we get here, all retries failed
        raise ConnectionError(f"Unable to connect to Qdrant at {url} after {max_retries} attempts. Last error: {last_error}")
    
    def _ensure_collection(self):
        """Ensure the user's collection exists."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=self.distance,
                        on_disk=True  # CRITICAL: Store vectors on disk for Railway
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
            else:
                logger.debug(f"Collection already exists: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text using the configured embedding model.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        if self._use_fastembed:
            # Ben, FastEmbed gives us a generator - we need to unwrap it to get the actual vector
            embeddings = list(self.embedding_model.embed([text]))
            return embeddings[0].tolist() if len(embeddings) > 0 else []
        else:
            # Custom embedding model - Ben: should have embed() method returning List[float]
            # This might need refactor. I've focused on Fastembed for development expediency.
            return self.embedding_model.embed(text)
    
    async def add_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        memory_type: str = "conversation"
    ) -> str:
        """
        Add a memory to the user's collection.
        
        Args:
            content: Memory content
            metadata: Optional metadata
            memory_type: Type of memory (conversation, fact, etc.)
            
        Returns:
            Memory ID
        """
        try:
            # Ben, we make a unique ID from user + content + timestamp
            memory_id = hashlib.md5(
                f"{self.user_id}_{content}_{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()
            
            # Turn the content into a searchable vector
            embedding = self._get_embedding(content)
            
            # Pack all the metadata together
            payload = {
                "user_id": self.user_id,
                "content": content,
                "type": memory_type,
                "created_at": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            # Store it in the vector DB
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=memory_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            
            logger.debug(f"Added memory: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            raise
    
    async def search_memories(
        self,
        query: str,
        limit: int = 10,
        memory_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search memories using semantic similarity.
        
        Args:
            query: Search query
            limit: Maximum results to return
            memory_type: Optional filter by memory type
            filters: Additional filters
            
        Returns:
            List of matching memories
        """
        try:
            # Ben, convert the search query to a vector
            query_embedding = self._get_embedding(query)
            
            # Set up our search filters
            filter_conditions = []
            
            # Ben, CRITICAL - always scope to this user only for privacy
            filter_conditions.append(
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=self.user_id)
                )
            )
            
            # Filter by type if they want specific kinds of memories
            if memory_type:
                filter_conditions.append(
                    FieldCondition(
                        key="type",
                        match=MatchValue(value=memory_type)
                    )
                )
            
            # Apply any other filters they passed in
            if filters:
                for key, value in filters.items():
                    filter_conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
            
            # Do the actual vector similarity search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=Filter(must=filter_conditions) if filter_conditions else None,
                limit=limit
            )
            
            # Package up the results nicely
            memories = []
            for result in results:
                memory = {
                    "id": result.id,
                    "score": result.score,
                    **result.payload
                }
                memories.append(memory)
            
            logger.debug(f"Found {len(memories)} memories for query: {query}")
            return memories
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            raise
    
    async def get_conversation_history(
        self,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for the user.
        
        Args:
            session_id: Optional session ID to filter by
            limit: Maximum messages to return
            
        Returns:
            List of conversation messages
        """
        filters = {"type": "conversation"}
        if session_id:
            filters["session_id"] = session_id
        
        # Ben, Qdrant doesn't sort by time natively, so we grab extras
        # then sort them ourselves - bit hacky but works fine
        memories = await self.search_memories(
            query="",  # Empty query for all results
            limit=limit * 2,  # Get more to sort
            memory_type="conversation",
            filters=filters if session_id else None
        )
        
        # Sort by creation time if we have it
        if memories and "created_at" in memories[0]:
            memories.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return memories[:limit]
    
    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing memory.
        
        Args:
            memory_id: Memory ID to update
            content: New content (if updating)
            metadata: New or updated metadata
            
        Returns:
            Success status
        """
        try:
            # Fetch what's currently stored
            existing = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[memory_id]
            )
            
            if not existing:
                logger.warning(f"Memory not found: {memory_id}")
                return False
            
            # Merge in the new metadata
            payload = existing[0].payload
            if metadata:
                payload.update(metadata)
            
            # If they're changing the actual content, we need new embeddings
            if content:
                payload["content"] = content
                embedding = self._get_embedding(content)
                
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=[
                        PointStruct(
                            id=memory_id,
                            vector=embedding,
                            payload=payload
                        )
                    ]
                )
            else:
                # Just metadata changes, no need for new embeddings
                self.client.set_payload(
                    collection_name=self.collection_name,
                    payload=payload,
                    points=[memory_id]
                )
            
            logger.debug(f"Updated memory: {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating memory: {e}")
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: Memory ID to delete
            
        Returns:
            Success status
        """
        try:
            result = self.client.delete(
                collection_name=self.collection_name,
                points_selector=[memory_id]
            )
            
            success = result.status == UpdateStatus.COMPLETED
            if success:
                logger.debug(f"Deleted memory: {memory_id}")
            else:
                logger.warning(f"Failed to delete memory: {memory_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False
    
    async def clear_all_memories(self) -> bool:
        """
        Clear all memories for the user.
        
        Returns:
            Success status
        """
        try:
            # Ben, easiest way is to just drop and recreate the collection
            self.client.delete_collection(collection_name=self.collection_name)
            self._ensure_collection()
            
            logger.info(f"Cleared all memories for user: {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing memories: {e}")
            return False