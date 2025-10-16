"""Knowledge base implementation for Integro using Qdrant."""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
# import hashlib
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    # Filter,
    # FieldCondition,
    # MatchValue,
)
from fastembed import TextEmbedding
from integro.utils.logging import get_logger

logger = get_logger(__name__)


class KnowledgeBase:
    """
    Knowledge base implementation using Qdrant for document storage and retrieval.
    """
    
    def __init__(
        self,
        collection_name: str = "knowledge",
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        vector_size: Optional[int] = None,
        distance: Distance = Distance.COSINE,
        in_memory: bool = False,
        embedding_model: Optional[Any] = None
    ):
        """
        Initialize knowledge base.
        
        Args:
            collection_name: Name of the Qdrant collection
            url: Qdrant server URL (ignored if in_memory=True)
            api_key: Optional API key for Qdrant
            vector_size: Size of embedding vectors (auto-detected if None)
            distance: Distance metric for similarity
            in_memory: Use in-memory Qdrant instance
            embedding_model: Either a custom embedding model with embed() method,
                           or a string name for FastEmbed model (default: BAAI/bge-small-en-v1.5)
        """
        self.collection_name = collection_name
        self.distance = distance
        
        # Ben, same embedding model setup as QdrantMemory - we share the approach
        if embedding_model is None:
            # Ben, using the same default model as memory - keeps things consistent
            logger.info("Loading default FastEmbed model: BAAI/bge-small-en-v1.5")
            import time
            embed_start = time.time()
            self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            self._use_fastembed = True
            logger.info(f"FastEmbed model loaded in {time.time() - embed_start:.3f}s")
        elif isinstance(embedding_model, str):
            # Got a model name, let FastEmbed handle it
            logger.info(f"Loading FastEmbed model: {embedding_model}")
            import time
            embed_start = time.time()
            self.embedding_model = TextEmbedding(model_name=embedding_model)
            self._use_fastembed = True
            logger.info(f"FastEmbed model loaded in {time.time() - embed_start:.3f}s")
        else:
            # Custom model object passed in
            self.embedding_model = embedding_model
            self._use_fastembed = False
            logger.debug("Using custom embedding model (no loading needed)")
        
        # Ben, figure out vector size by running a test
        if vector_size is None:
            # Quick embedding to count dimensions
            logger.info("Running test embedding to determine vector size...")
            import time
            test_start = time.time()
            sample_embedding = self._get_embedding("test")
            self.vector_size = len(sample_embedding)
            logger.info(f"Test embedding completed in {time.time() - test_start:.3f}s, vector size: {self.vector_size}")
        else:
            self.vector_size = vector_size
            logger.debug(f"Using provided vector size: {vector_size}")
        
        logger.info(f"Vector size: {self.vector_size}")
        
        # Ben, set up Qdrant - can be in-memory for testing or connect to embedded service
        if in_memory:
            self.client = QdrantClient(":memory:")
        else:
            # External Qdrant connection controlled via environment variables
            if url is None:
                import os
                # Prefer explicit QDRANT_URL if provided
                url = os.getenv('QDRANT_URL')
                if not url:
                    host = os.getenv('QDRANT_HOST', 'qdrant')
                    port = os.getenv('QDRANT_PORT', '6333')
                    url = f"http://{host}:{port}"
                logger.info(f"Knowledge base connecting to Qdrant at: {url}")
            
            # Create client connection (skip if already set to in-memory above)
            if not hasattr(self, 'client') or self.client is None:
                self.client = QdrantClient(
                    url=url,
                    api_key=api_key
                )
        
        # Make sure our knowledge collection is ready
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Ensure the collection exists."""
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
                logger.info(f"Created knowledge collection: {self.collection_name}")
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
            # Ben, unwrap the generator from FastEmbed
            embeddings = list(self.embedding_model.embed([text]))
            return embeddings[0].tolist() if len(embeddings) > 0 else []
        else:
            # Custom model needs an embed() method that returns floats
            return self.embedding_model.embed(text)
    
    def add_documents_bulk(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Add multiple documents in bulk (more efficient).
        
        Args:
            documents: List of dicts with 'doc_id', 'content', and optional 'metadata'
            
        Returns:
            List of document IDs (UUID format)
        """
        import uuid
        
        try:
            points = []
            doc_ids = []
            
            for doc in documents:
                doc_id = doc.get('doc_id', str(uuid.uuid4()))
                content = doc.get('content', '')
                metadata = doc.get('metadata', {})
                
                # Ben, convert to UUID
                doc_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, doc_id))
                
                # Get embedding
                embedding = self._get_embedding(content)
                
                # Prepare payload
                payload = {
                    "content": content,
                    "doc_id": doc_id,
                    "created_at": datetime.utcnow().isoformat(),
                    **metadata
                }
                
                points.append(
                    PointStruct(
                        id=doc_uuid,
                        vector=embedding,
                        payload=payload
                    )
                )
                doc_ids.append(doc_uuid)
            
            # Bulk upsert with wait
            if points:
                self.client.upsert(
                    collection_name=self.collection_name,
                    wait=True,
                    points=points
                )
                logger.info(f"Bulk added {len(points)} documents to collection")
            
            return doc_ids
            
        except Exception as e:
            logger.error(f"Error bulk adding documents: {e}")
            raise
    
    def add_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> str:
        """
        Add a document to the knowledge base.
        
        Args:
            doc_id: Unique document ID
            content: Document content
            metadata: Optional metadata
            embedding: Optional pre-computed embedding vector
            
        Returns:
            Document ID (UUID format)
        """
        import uuid
        
        try:
            # Ben, Qdrant needs UUIDs, so we deterministically convert doc_id to UUID
            # Using namespace DNS ensures we don't collide with other UUID spaces
            doc_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, doc_id))
            
            # Use provided embedding or generate one
            if embedding is None:
                embedding = self._get_embedding(content)
            else:
                # Ensure it's a list of floats
                embedding = [float(x) for x in embedding]
            
            # Ben, keep the original doc_id in payload so we can reference it later
            payload = {
                "content": content,
                "doc_id": doc_id,  # Original ID for reference
                "created_at": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            # Store in Qdrant using the UUID
            self.client.upsert(
                collection_name=self.collection_name,
                wait=True,  # Ben, wait for the operation to complete
                points=[
                    PointStruct(
                        id=doc_uuid,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            
            logger.debug(f"Added document: {doc_id} (UUID: {doc_uuid})")
            return doc_uuid
            
        except Exception as e:
            logger.error(f"Error adding document {doc_id}: {e}")
            logger.error(f"Document content length: {len(content)}")
            logger.error(f"Embedding length: {len(embedding) if embedding else 'None'}")
            raise
    
    def search(
        self,
        query: str,
        limit: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            limit: Maximum results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of (document, score) tuples
        """
        try:
            # Ben, vectorize the search query
            query_embedding = self._get_embedding(query)
            
            # Run similarity search in Qdrant
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Package results with scores
            documents = []
            for result in results:
                doc = {
                    "id": result.id,
                    **result.payload
                }
                documents.append((doc, result.score))
            
            logger.debug(f"Found {len(documents)} documents for query: {query}")
            return documents
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            raise
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by ID.
        
        Args:
            doc_id: Document ID (original or UUID)
            
        Returns:
            Document data or None if not found
        """
        import uuid
        
        try:
            # Ben, doc_id might already be a UUID or might need conversion
            try:
                # See if this is already a UUID
                uuid.UUID(doc_id)
                search_id = doc_id
            except ValueError:
                # Not a UUID, so convert it the same way we did in add_document
                search_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, doc_id))
            
            results = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[search_id]
            )
            
            if results:
                return {
                    "id": results[0].id,
                    **results[0].payload
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving document: {e}")
            return None
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document.
        
        Args:
            doc_id: Document ID to delete (original or UUID)
            
        Returns:
            Success status
        """
        import uuid
        
        try:
            # Ben, doc_id might already be a UUID or might need conversion
            try:
                # See if this is already a UUID
                uuid.UUID(doc_id)
                search_id = doc_id
            except ValueError:
                # Not a UUID, so convert it the same way we did in add_document
                search_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, doc_id))
            
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[search_id]
            )
            logger.debug(f"Deleted document: {doc_id} (UUID: {search_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    def get_document_count(self) -> int:
        """
        Get the number of documents in the knowledge base.
        
        Returns:
            Number of documents
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return collection_info.points_count
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0
    
    def clear(self) -> bool:
        """
        Clear all documents from the knowledge base.
        
        Returns:
            Success status
        """
        try:
            # Ben, nuclear option - drop and rebuild the collection
            self.client.delete_collection(collection_name=self.collection_name)
            self._ensure_collection()
            
            logger.info(f"Cleared knowledge base: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing knowledge base: {e}")
            return False
    
    def validate_filters(self, filters: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], List[str]]:
        """
        Validate filters for knowledge base search.
        
        This method is required by agno's Agent when using search_knowledge=True.
        
        Args:
            filters: Optional filters to validate
            
        Returns:
            Tuple of (valid_filters, invalid_keys)
        """
        if not filters:
            return {}, []
        
        # Ben, for now we accept all filters as valid since Qdrant handles them
        # In a real implementation, you'd check against known metadata fields
        valid_filters = filters.copy()
        invalid_keys = []
        
        logger.debug(f"Validated filters: {valid_filters}, invalid: {invalid_keys}")
        return valid_filters, invalid_keys
    
    async def aget_relevant_docs(
        self,
        query: str,
        num_documents: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get relevant documents asynchronously (agno compatibility).
        
        This method is required by agno's Agent for knowledge base integration.
        
        Args:
            query: Search query
            num_documents: Number of documents to retrieve
            filters: Optional filters
            
        Returns:
            List of relevant documents
        """
        try:
            # Ben, our search method is sync so we wrap it
            # In a real async implementation you'd use an async Qdrant client
            import asyncio
            loop = asyncio.get_event_loop()
            
            # Run sync search in executor to avoid blocking
            results = await loop.run_in_executor(
                None,
                self.search,
                query,
                num_documents,
                None  # score_threshold
            )
            
            # Ben, format results for agno - it expects a list of dicts
            documents = []
            for doc, score in results:
                doc_dict = {
                    "content": doc.get("content", ""),
                    "metadata": {
                        k: v for k, v in doc.items() 
                        if k not in ["content", "id"]
                    },
                    "score": score,
                    "id": doc.get("id", doc.get("doc_id", "unknown"))
                }
                documents.append(doc_dict)
            
            logger.debug(f"Retrieved {len(documents)} relevant documents for query: {query}")
            return documents
            
        except Exception as e:
            logger.error(f"Error getting relevant documents: {e}")
            return []
    
    def get_relevant_docs(
        self,
        query: str,
        num_documents: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get relevant documents synchronously (agno compatibility).
        
        Args:
            query: Search query
            num_documents: Number of documents to retrieve
            filters: Optional filters
            
        Returns:
            List of relevant documents
        """
        try:
            results = self.search(query, num_documents)
            
            # Ben, format results for agno
            documents = []
            for doc, score in results:
                doc_dict = {
                    "content": doc.get("content", ""),
                    "metadata": {
                        k: v for k, v in doc.items() 
                        if k not in ["content", "id"]
                    },
                    "score": score,
                    "id": doc.get("id", doc.get("doc_id", "unknown"))
                }
                documents.append(doc_dict)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error getting relevant documents: {e}")
            return []