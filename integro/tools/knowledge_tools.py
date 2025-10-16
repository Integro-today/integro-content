"""Knowledge base tools for Integro agents."""

from typing import List
from agno.tools import tool
from integro.memory.knowledge import KnowledgeBase
from integro.utils.logging import get_logger

logger = get_logger(__name__)


def create_knowledge_tools(knowledge_base: KnowledgeBase) -> List:
    """
    Create knowledge tools for a given knowledge base.
    
    Args:
        knowledge_base: KnowledgeBase instance to use
        
    Returns:
        List of tool functions
    """
    
    @tool
    def search_knowledge(query: str, max_results: int = 3) -> str:
        """
        Search the knowledge base for relevant information.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            Formatted search results
        """
        try:
            logger.info(f"Searching knowledge base for: {query}")
            results = knowledge_base.search(query, limit=max_results)
            
            if not results:
                logger.info(f"No results found for query: {query}")
                return f"No results found for query: {query}"
            
            # Ben, format results for readability with scores
            formatted = []
            for doc, score in results:
                content = doc.get("content", "")
                doc_id = doc.get("doc_id", doc.get("id", "unknown"))
                formatted.append(
                    f"[Score: {score:.2f}] Document {doc_id}:\n{content}"
                )
            
            result_text = "\n\n".join(formatted)
            logger.info(f"Found {len(results)} results, returning: {result_text[:200]}...")
            return result_text
            
        except Exception as e:
            logger.error(f"Error searching knowledge: {e}")
            return f"Error searching knowledge base: {str(e)}"
    
    @tool
    def get_document_by_id(doc_id: str) -> str:
        """
        Retrieve a specific document by its ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document content or error message
        """
        try:
            doc = knowledge_base.get_document(doc_id)
            
            if not doc:
                return f"Document not found: {doc_id}"
            
            content = doc.get("content", "")
            metadata = {k: v for k, v in doc.items() if k not in ["content", "id"]}
            
            result = f"Document {doc_id}:\n{content}"
            
            if metadata:
                result += f"\n\nMetadata: {metadata}"
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving document: {e}")
            return f"Error retrieving document: {str(e)}"
    
    return [search_knowledge, get_document_by_id]


class KnowledgeTools:
    """Tools for interacting with a knowledge base."""
    
    def __init__(self, knowledge_base: KnowledgeBase):
        """
        Initialize knowledge tools.
        
        Args:
            knowledge_base: KnowledgeBase instance to use
        """
        self.kb = knowledge_base
        self._tools = create_knowledge_tools(knowledge_base)
    
    def get_tools(self) -> List:
        """Get all knowledge tools."""
        return self._tools