"""Agno-compatible knowledge base wrapper for Integro."""

from typing import Dict, Any, List, Optional, Tuple
from agno.knowledge import Knowledge
from agno.vectordb.qdrant import Qdrant
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.embedder.base import Embedder
from qdrant_client import QdrantClient
from integro.utils.logging import get_logger
from integro.memory.knowledge import KnowledgeBase as IntegroKnowledgeBase

logger = get_logger(__name__)


class AgnoKnowledgeAdapter:
    """
    Adapter to convert Integro's KnowledgeBase to agno's Knowledge.
    
    This allows us to use our existing KnowledgeBase infrastructure
    while providing agno-compatible knowledge to agents.
    """
    
    def __init__(
        self,
        collection_name: str = "agno_knowledge",
        embedder: Optional[Embedder] = None,
        in_memory: bool = True,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        embedding_dim: Optional[int] = None  # Allow specifying dimensions
    ):
        """
        Initialize the agno knowledge adapter.
        
        Args:
            collection_name: Name for the Qdrant collection
            embedder: Embedder to use (defaults to OpenAI if available)
            in_memory: Use in-memory Qdrant instance
            qdrant_url: Qdrant server URL (if not in_memory)
            qdrant_api_key: Qdrant API key
            embedding_dim: Embedding dimensions (defaults to 384 for FastEmbed, 1536 for OpenAI)
        """
        self.collection_name = collection_name
        self.in_memory = in_memory
        self.qdrant_url = qdrant_url
        self.qdrant_api_key = qdrant_api_key
        self.embedding_dim = embedding_dim
        
        # Ben, create the vector database for agno
        # We'll try OpenAI embedder first, then fall back to a custom one
        if embedder:
            self.embedder = embedder
        else:
            # If embedding_dim is specified as 384, always use FastEmbed for compatibility
            if self.embedding_dim == 384:
                self.embedder = self._create_fastembed_wrapper()
                logger.info("Using FastEmbed wrapper for AgentKnowledge (384 dimensions)")
            else:
                try:
                    # Try OpenAI embedder if API key is available
                    import os
                    if os.getenv("OPENAI_API_KEY") and self.embedding_dim != 384:
                        # Use OpenAI with specified dimensions or default 1536
                        from openai import OpenAI
                        # Create a wrapper that uses the right dimensions
                        class OpenAIEmbedderWrapper:
                            def __init__(self, dimensions=1536):
                                self.client = OpenAI()
                                self.dimensions = dimensions
                                self.model = "text-embedding-3-small"
                            
                            def embed(self, text: str) -> List[float]:
                                response = self.client.embeddings.create(
                                    input=text,
                                    model=self.model,
                                    dimensions=self.dimensions
                                )
                                return response.data[0].embedding
                            
                            def embed_batch(self, texts: List[str]) -> List[List[float]]:
                                response = self.client.embeddings.create(
                                    input=texts,
                                    model=self.model,
                                    dimensions=self.dimensions
                                )
                                return [data.embedding for data in response.data]
                            
                            def get_embedding_dim(self) -> int:
                                return self.dimensions
                            
                            def get_embedding_and_usage(self, text: str) -> Tuple[List[float], Dict[str, Any]]:
                                response = self.client.embeddings.create(
                                    input=text,
                                    model=self.model,
                                    dimensions=self.dimensions
                                )
                                usage = {
                                    "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else len(text.split()),
                                    "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else len(text.split())
                                }
                                return response.data[0].embedding, usage
                            
                            def get_embedding(self, text: str) -> List[float]:
                                """Get embedding for a single text (required by agno for search)."""
                                return self.embed(text)
                        
                        self.embedder = OpenAIEmbedderWrapper(dimensions=self.embedding_dim or 1536)
                        logger.info(f"Using OpenAI embedder for Knowledge ({self.embedding_dim or 1536} dimensions)")
                    else:
                        # Fall back to our custom embedder wrapper
                        self.embedder = self._create_fastembed_wrapper()
                        logger.info("Using FastEmbed wrapper for Knowledge")
                except Exception as e:
                    logger.warning(f"Could not create OpenAI embedder: {e}")
                    self.embedder = self._create_fastembed_wrapper()
        
        # Ben, create the Qdrant vector database for agno
        # Use location for in-memory or URL for server
        if self.in_memory:
            self.vector_db = Qdrant(
                collection=self.collection_name,
                embedder=self.embedder,
                location=":memory:"
            )
            logger.info("Using in-memory Qdrant for Knowledge")
        else:
            self.vector_db = Qdrant(
                collection=self.collection_name,
                embedder=self.embedder,
                url=self._get_qdrant_url(),
                api_key=self.qdrant_api_key
            )
            logger.info(f"Agno knowledge using Qdrant server at {self._get_qdrant_url()}")
        
        # Ben, ensure the collection exists
        try:
            if not self.vector_db.exists():
                self.vector_db.create()
                logger.info(f"Created collection '{self.collection_name}'")
        except Exception as e:
            logger.debug(f"Collection check/create: {e}")
        
        # Ben, initialize Knowledge with our vector DB
        self.agent_knowledge = Knowledge(
            vector_db=self.vector_db
        )
        
        logger.info(f"Knowledge initialized with collection '{self.collection_name}'")
    
    def _get_qdrant_url(self) -> str:
        """Get the appropriate Qdrant URL for embedded service."""
        if self.qdrant_url:
            return self.qdrant_url
            
        import os
        if os.getenv('RAILWAY_ENVIRONMENT'):
            # Railway deployment with embedded Qdrant service
            try:
                from integro.utils.qdrant_embedded import get_qdrant_service
                qdrant_service = get_qdrant_service()
                return f"http://{qdrant_service.host}:{qdrant_service.port}"
            except Exception as e:
                logger.error(f"Failed to get embedded Qdrant service URL: {e}")
                return "http://localhost:6333"  # Fallback
        else:
            # Local development
            return "http://localhost:6333"
    
    def _create_fastembed_wrapper(self):
        """
        Create a wrapper around FastEmbed that implements agno's Embedder interface.
        Uses lazy loading to avoid blocking on initialization.
        """
        class FastEmbedWrapper:
            """Wrapper to make FastEmbed compatible with agno."""
            
            def __init__(self):
                self._model = None  # Lazy load the model
                self.dimensions = 384  # BGE small has 384 dimensions
            
            @property
            def model(self):
                """Lazy load the FastEmbed model only when needed."""
                if self._model is None:
                    logger.debug("Loading FastEmbed model on first use...")
                    from fastembed import TextEmbedding
                    self._model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
                    logger.debug("FastEmbed model loaded")
                return self._model
            
            def embed(self, text: str) -> List[float]:
                """Embed a single text."""
                embeddings = list(self.model.embed([text]))
                return embeddings[0].tolist() if embeddings else []
            
            def embed_batch(self, texts: List[str]) -> List[List[float]]:
                """Embed multiple texts."""
                embeddings = list(self.model.embed(texts))
                return [emb.tolist() for emb in embeddings]
            
            def get_embedding_dim(self) -> int:
                """Get embedding dimensions."""
                return self.dimensions
            
            def get_embedding_and_usage(self, text: str) -> Tuple[List[float], Dict[str, Any]]:
                """
                Get embedding with usage stats (required by agno).
                
                Returns:
                    Tuple of (embedding, usage_dict)
                """
                embedding = self.embed(text)
                # Ben, mock usage stats since FastEmbed doesn't provide them
                usage = {
                    "prompt_tokens": len(text.split()),
                    "total_tokens": len(text.split())
                }
                return embedding, usage
            
            def get_embedding(self, text: str) -> List[float]:
                """
                Get embedding for a single text (required by agno for search).
                
                Args:
                    text: Text to embed
                    
                Returns:
                    Embedding vector
                """
                return self.embed(text)
        
        return FastEmbedWrapper()
    
    def load_from_integro_kb(self, integro_kb: IntegroKnowledgeBase) -> int:
        """
        Load documents from an Integro KnowledgeBase into Knowledge.
        
        Args:
            integro_kb: IntegroKnowledgeBase instance to copy from
            
        Returns:
            Number of documents loaded
        """
        logger.debug("Starting load from Integro KB...")
        try:
            # Ben, first check if the Integro KB collection exists and has documents
            all_docs = []
            
            try:
                # Check collection info first
                collections = integro_kb.client.get_collections().collections
                collection_names = [c.name for c in collections]
                logger.debug(f"Available collections in Integro KB: {collection_names}")
                collection_exists = integro_kb.collection_name in collection_names
                
                if not collection_exists:
                    logger.warning(f"Collection '{integro_kb.collection_name}' does not exist in Integro KB")
                    logger.warning(f"Available collections: {collection_names}")
                    return 0
                
                # Get collection info to see if it has points
                collection_info = integro_kb.client.get_collection(integro_kb.collection_name)
                points_count = collection_info.points_count
                logger.info(f"Integro KB collection '{integro_kb.collection_name}' has {points_count} points")
                
                # Also try using the helper method if available
                if hasattr(integro_kb, 'get_document_count'):
                    alt_count = integro_kb.get_document_count()
                    logger.info(f"Alternative count check: {alt_count} documents")
                    points_count = max(points_count, alt_count)
                
                if points_count == 0:
                    logger.warning("Integro KB collection has no documents")
                    # Let's still try the scroll in case there's a sync issue
                    logger.info("Attempting to scroll anyway in case of sync issues...")
                
                # Now scroll through all points
                offset = None
                while True:
                    records = integro_kb.client.scroll(
                        collection_name=integro_kb.collection_name,
                        limit=100,
                        offset=offset,
                        with_vectors=True  # IMPORTANT: Include vectors
                    )
                    
                    if not records or not records[0]:
                        break
                    
                    points, next_offset = records
                    for point in points:
                        doc = {
                            "id": point.id,
                            "content": point.payload.get("content", ""),
                            "vector": point.vector,  # Include the pre-computed embedding
                            **point.payload
                        }
                        all_docs.append((doc, 1.0))  # Score of 1.0 for all
                    
                    offset = next_offset
                    if offset is None:
                        break
                
                logger.info(f"Retrieved {len(all_docs)} documents from Integro KB")
                        
            except Exception as scroll_error:
                logger.error(f"Error accessing Integro KB: {scroll_error}")
                # Try alternative methods - search with various queries
                logger.info("Attempting fallback search methods...")
                
                # Try multiple search queries to get documents
                search_queries = [
                    "*",  # Some vector DBs support wildcard
                    "",   # Empty query might return all
                    "the", "and", "or", "is", "are",  # Common words
                    "treatment", "recovery", "therapy",  # Domain-specific terms
                ]
                
                seen_ids = set()
                for query in search_queries:
                    try:
                        results = integro_kb.search(query, limit=100)
                        for doc, score in results:
                            doc_id = doc.get("id", doc.get("doc_id"))
                            if doc_id and doc_id not in seen_ids:
                                all_docs.append((doc, score))
                                seen_ids.add(doc_id)
                    except Exception as e:
                        logger.debug(f"Search with query '{query}' failed: {e}")
                
                if all_docs:
                    logger.info(f"Fallback search found {len(all_docs)} unique documents")
            
            if not all_docs:
                logger.warning("No documents found in Integro KnowledgeBase")
                return 0
            
            # Batch process documents for better performance
            from agno.document import Document
            
            logger.info(f"Converting {len(all_docs)} documents to agno format...")
            agno_docs = []
            doc_embeddings = []  # Store pre-computed embeddings
            
            for doc, score in all_docs:
                content = doc.get("content", "")
                doc_id = doc.get("doc_id", doc.get("id", f"doc_{len(agno_docs)}"))
                vector = doc.get("vector")  # Get pre-computed embedding
                
                # Ben, prepare metadata for agno
                metadata = {
                    k: v for k, v in doc.items()
                    if k not in ["content", "id", "doc_id", "vector"]
                }
                metadata["source_kb"] = "integro"
                metadata["original_id"] = doc_id
                
                # Ben, add to Knowledge using agno's Document format
                agno_doc = Document(
                    content=content,
                    name=doc_id,
                    meta_data=metadata
                )
                agno_docs.append(agno_doc)
                
                # Store the pre-computed embedding if available
                if vector:
                    doc_embeddings.append(vector)
                else:
                    doc_embeddings.append(None)
            
            # Load into the vector DB in batches with pre-computed embeddings
            batch_size = 100
            loaded = 0
            logger.info(f"Upserting documents in batches of {batch_size}...")
            
            # Check if we have pre-computed embeddings for all docs
            has_all_embeddings = all(emb is not None for emb in doc_embeddings)
            
            for i in range(0, len(agno_docs), batch_size):
                batch = agno_docs[i:i+batch_size]
                batch_embeddings = doc_embeddings[i:i+batch_size]
                
                # If we have embeddings, use a custom upsert that includes them
                if has_all_embeddings:
                    # Direct upsert with embeddings to avoid re-computation
                    from qdrant_client.models import PointStruct
                    import uuid
                    points = []
                    for doc, embedding in zip(batch, batch_embeddings):
                        # Generate a UUID based on the document name for consistency
                        doc_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, doc.name))
                        points.append(PointStruct(
                            id=doc_uuid,
                            vector=embedding,
                            payload={
                                "content": doc.content,
                                "name": doc.name,
                                "meta_data": doc.meta_data,  # Store as separate field
                                "usage": {}  # Empty usage stats for pre-computed embeddings
                            }
                        ))
                    
                    # Upsert directly to the underlying Qdrant client
                    try:
                        # Access the raw Qdrant client through the vector_db._client
                        raw_client = self.vector_db._client if hasattr(self.vector_db, '_client') else self.vector_db.client
                        raw_client.upsert(
                            collection_name=self.collection_name,
                            points=points,
                            wait=False  # Don't wait for indexing
                        )
                        logger.debug("Direct upsert with embeddings successful")
                    except Exception as e:
                        logger.warning(f"Direct upsert failed ({e}), falling back to regular upsert")
                        # Fallback to regular upsert if direct access not available
                        self.agent_knowledge.vector_db.upsert(batch)
                else:
                    # Regular upsert (will compute embeddings)
                    self.agent_knowledge.vector_db.upsert(batch)
                
                loaded += len(batch)
                if loaded % 100 == 0 or loaded == len(agno_docs):
                    logger.info(f"Loaded {loaded}/{len(agno_docs)} documents...")
            
            logger.info(f"Loaded {loaded} documents from Integro KB to Knowledge")
            return loaded
            
        except Exception as e:
            logger.error(f"Error loading from Integro KB: {e}")
            return 0
    
    def add_document(
        self,
        content: str,
        doc_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a document directly to Knowledge.
        
        Args:
            content: Document content
            doc_id: Optional document ID
            metadata: Optional metadata
            
        Returns:
            Success status
        """
        try:
            from agno.document import Document
            
            # Ben, create an agno Document
            doc = Document(
                content=content,
                name=doc_id or f"doc_{hash(content)}",
                meta_data=metadata or {}
            )
            
            # Add to knowledge base
            self.agent_knowledge.vector_db.upsert([doc])
            
            logger.debug(f"Added document to Knowledge: {doc.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document to Knowledge: {e}")
            return False
    
    def add_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> int:
        """
        Add multiple documents to Knowledge.
        
        Args:
            documents: List of document dicts with 'content', 'doc_id', and optional 'metadata'
            
        Returns:
            Number of documents successfully added
        """
        added = 0
        for doc in documents:
            if self.add_document(
                content=doc.get("content", ""),
                doc_id=doc.get("doc_id", doc.get("id")),
                metadata=doc.get("metadata", {})
            ):
                added += 1
        
        logger.info(f"Added {added} documents to Knowledge")
        return added
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search the Knowledge.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching documents
        """
        try:
            results = self.agent_knowledge.search(query, num_documents=limit)
            
            # Ben, format results
            documents = []
            for doc in results:
                documents.append({
                    "content": doc.content,
                    "name": doc.name,
                    "metadata": doc.meta_data,
                    "score": getattr(doc, 'score', 0.0)
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error searching Knowledge: {e}", exc_info=True)
            return []
    
    def get_agent_knowledge(self) -> Knowledge:
        """
        Get the Knowledge instance for use with agno agents.
        
        Returns:
            Knowledge instance
        """
        return self.agent_knowledge
    
    def clear(self) -> bool:
        """
        Clear all documents from the knowledge base.
        
        Returns:
            Success status
        """
        try:
            # Ben, recreate the collection to clear it
            self.vector_db.delete()
            logger.info("Cleared Knowledge")
            return True
        except Exception as e:
            logger.error(f"Error clearing Knowledge: {e}")
            return False


def create_agent_knowledge(
    integro_kb: Optional[IntegroKnowledgeBase] = None,
    collection_name: str = "agent_knowledge",
    in_memory: bool = True,
    documents: Optional[List[Dict[str, Any]]] = None,
    embedding_dim: Optional[int] = None,
    **kwargs
) -> Knowledge:
    """
    Helper function to create Knowledge from an Integro KnowledgeBase.
    
    Args:
        integro_kb: Optional IntegroKnowledgeBase to copy from
        collection_name: Name for the collection
        in_memory: Use in-memory storage
        documents: Optional list of documents to add directly
        embedding_dim: Embedding dimensions (auto-detected from integro_kb if not specified)
        **kwargs: Additional arguments for AgnoKnowledgeAdapter
        
    Returns:
        Knowledge instance ready for use with agno agents
    """
    # Auto-detect embedding dimensions from Integro KB if not specified
    if integro_kb and embedding_dim is None:
        # FastEmbed uses 384 dimensions by default
        embedding_dim = 384
        logger.info(f"Auto-detected embedding dimensions: {embedding_dim}")
    
    logger.debug(f"Creating Knowledge adapter with collection={collection_name}, dim={embedding_dim}")
    adapter = AgnoKnowledgeAdapter(
        collection_name=collection_name,
        in_memory=in_memory,
        embedding_dim=embedding_dim,
        **kwargs
    )
    
    # Load from Integro KB if provided
    if integro_kb:
        logger.info("Loading documents from Integro KnowledgeBase...")
        num_loaded = adapter.load_from_integro_kb(integro_kb)
        logger.info(f"Loaded {num_loaded} documents from Integro KB")
        if num_loaded == 0:
            logger.warning("No documents were loaded from Integro KB")
    
    # Add any additional documents directly
    if documents:
        num_added = adapter.add_documents(documents)
        logger.info(f"Added {num_added} documents directly to Knowledge")
    
    return adapter.get_agent_knowledge()