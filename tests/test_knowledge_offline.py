"""
Offline tests for knowledge base functionality.
These tests don't make API calls and test only the knowledge base and tools.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
import pytest
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from integro import KnowledgeBase, create_knowledge_tools
from integro.utils.logging import get_logger

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_knowledge_base():
    """Set up an in-memory knowledge base with test data."""
    kb = KnowledgeBase(
        collection_name="test_knowledge",
        in_memory=True
        # vector_size auto-detected from embedding model
    )
    
    # Add test documents with very specific information
    # These facts are obscure enough that the model won't know them without the KB
    
    kb.add_document(
        doc_id="planet_zephyr",
        content="Planet Zephyr is a fictional planet in the Integro test universe. It has purple oceans, three moons named Luna, Stella, and Nova, and its capital city is called Windholm. The planet's population is exactly 7,892,345 beings.",
        metadata={"category": "planets", "fictional": True}
    )
    
    kb.add_document(
        doc_id="integro_founder",
        content="The Integro Framework was founded by Dr. Alexandra Quantum in the year 2157. She invented it while working at the Institute of Advanced Cognition on Mars. Her favorite programming language was Cosmic++.",
        metadata={"category": "history", "fictional": True}
    )
    
    kb.add_document(
        doc_id="secret_recipe",
        content="The secret recipe for Integro Success Sauce contains: 42 lines of code, 3 cups of recursion, a pinch of async/await, and exactly 17 milliseconds of processing time. Mix thoroughly in a quantum compiler.",
        metadata={"category": "recipes", "fictional": True}
    )
    
    kb.add_document(
        doc_id="robot_laws",
        content="The Five Laws of Integro Robotics are: 1) Always use type hints, 2) Never divide by zero, 3) Cache everything twice, 4) Question all assumptions except this one, 5) The answer is always 42 unless it's 43.",
        metadata={"category": "laws", "fictional": True}
    )
    
    kb.add_document(
        doc_id="error_codes",
        content="Integro Error Code E-789: This error occurs when trying to search for meaning in random test data. Solution: Add more test data. Error Code E-790: Insufficient coffee in developer. Solution: Brew more coffee.",
        metadata={"category": "errors", "fictional": True}
    )
    
    return kb


def test_knowledge_base_creation():
    """Test that knowledge base can be created and populated."""
    kb = setup_knowledge_base()
    assert kb is not None
    assert kb.collection_name == "test_knowledge"
    logger.info("Knowledge base created successfully")


def test_knowledge_base_search():
    """Test direct knowledge base search functionality."""
    kb = setup_knowledge_base()
    
    # Test searching for Planet Zephyr
    results = kb.search("Planet Zephyr population", limit=1)
    assert len(results) > 0, "Should find Planet Zephyr"
    
    doc, score = results[0]
    assert "7,892,345" in doc["content"], "Should contain population number"
    assert doc["doc_id"] == "planet_zephyr", "Should have correct doc ID"
    logger.info(f"Found Planet Zephyr with score {score:.2f}")
    
    # Test searching for founder
    results = kb.search("who founded Integro Framework", limit=1)
    assert len(results) > 0, "Should find founder information"
    
    doc, score = results[0]
    assert "Alexandra Quantum" in doc["content"], "Should contain founder name"
    logger.info(f"Found founder info with score {score:.2f}")
    
    # Test searching for robotics laws
    results = kb.search("robotics laws type hints", limit=1)
    assert len(results) > 0, "Should find robotics laws"
    
    doc, score = results[0]
    assert "type hints" in doc["content"] or "42" in doc["content"], "Should contain law details"
    logger.info(f"Found robotics laws with score {score:.2f}")


def test_knowledge_base_retrieval():
    """Test document retrieval by ID."""
    kb = setup_knowledge_base()
    
    # Test retrieving by original ID
    doc = kb.get_document("secret_recipe")
    assert doc is not None, "Should retrieve document by ID"
    assert "42 lines of code" in doc["content"], "Should contain recipe details"
    assert doc["doc_id"] == "secret_recipe", "Should have correct doc_id"
    logger.info("Retrieved document by ID successfully")
    
    # Test retrieving non-existent document
    doc = kb.get_document("nonexistent")
    assert doc is None, "Should return None for non-existent document"
    logger.info("Correctly returned None for non-existent document")


def test_knowledge_tools():
    """Test knowledge tools functionality without API calls."""
    kb = setup_knowledge_base()
    tools = create_knowledge_tools(kb)
    
    assert len(tools) == 2, "Should have 2 tools"
    
    # Note: Agno Function objects are not directly callable in tests
    # They're meant to be used within an agent context
    # We'll test the underlying functionality through the knowledge base directly
    
    # Test that tools were created
    search_tool = tools[0]
    get_doc_tool = tools[1]
    
    # Verify tools are Function objects
    from agno.tools.function import Function
    assert isinstance(search_tool, Function), "Should be an agno Function"
    assert isinstance(get_doc_tool, Function), "Should be an agno Function"
    
    # Test the knowledge base search directly (what the tool would call)
    results = kb.search("Planet Zephyr", limit=1)
    assert len(results) > 0, "Should find results"
    doc, score = results[0]
    assert "Planet Zephyr" in doc["content"], "Should find Planet Zephyr"
    logger.info(f"Direct search found: {doc['doc_id']} (score: {score:.2f})")
    
    # Test document retrieval directly
    doc = kb.get_document("error_codes")
    assert doc is not None, "Should retrieve document"
    assert "E-789" in doc["content"], "Should contain error code"
    logger.info(f"Direct retrieval found: {doc['doc_id'][:100]}...")


def test_knowledge_search_relevance():
    """Test that search returns relevant documents based on query."""
    kb = setup_knowledge_base()
    
    # Search for specific error code
    results = kb.search("error E-789 solution", limit=2)
    assert len(results) > 0, "Should find error code"
    
    # The first result should be the error codes document
    doc, score = results[0]
    assert doc["doc_id"] == "error_codes", "Should find error codes document first"
    assert score > 0.5, "Should have reasonable relevance score"
    logger.info(f"Error code search relevance: {score:.2f}")
    
    # Search for something not in KB
    results = kb.search("weather forecast tomorrow rain", limit=1)
    if results:
        doc, score = results[0]
        # Score should be lower for irrelevant queries
        assert score < 0.7, "Irrelevant query should have lower score"
        logger.info(f"Irrelevant query score: {score:.2f}")


def test_knowledge_embedding_quality():
    """Test that embeddings provide good semantic similarity."""
    kb = setup_knowledge_base()
    
    # Similar queries should find the same document
    queries = [
        "how many people live on Planet Zephyr",
        "Planet Zephyr population count",
        "inhabitants of Zephyr planet"
    ]
    
    doc_ids = []
    for query in queries:
        results = kb.search(query, limit=1)
        if results:
            doc, score = results[0]
            doc_ids.append(doc["doc_id"])
            logger.info(f"Query '{query[:30]}...' found {doc['doc_id']} (score: {score:.2f})")
    
    # All queries should find the same document
    assert len(set(doc_ids)) == 1, "Similar queries should find the same document"
    assert doc_ids[0] == "planet_zephyr", "Should find Planet Zephyr for all population queries"


async def run_all_offline_tests():
    """Run all offline knowledge tests."""
    print("\n" + "="*60)
    print("INTEGRO KNOWLEDGE BASE OFFLINE TEST SUITE")
    print("="*60 + "\n")
    
    tests = [
        ("Knowledge Base Creation", test_knowledge_base_creation),
        ("Knowledge Base Search", test_knowledge_base_search),
        ("Document Retrieval", test_knowledge_base_retrieval),
        ("Knowledge Tools", test_knowledge_tools),
        ("Search Relevance", test_knowledge_search_relevance),
        ("Embedding Quality", test_knowledge_embedding_quality),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n▶ Running: {test_name}")
            test_func()
            print(f"  ✅ {test_name} PASSED")
            passed += 1
        except Exception as e:
            print(f"  ❌ {test_name} FAILED: {e}")
            failed += 1
    
    # Summary
    print("\n" + "="*60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Run with pytest if available, otherwise run directly
    try:
        import sys
        sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
    except ImportError:
        print("pytest not installed, running tests directly...")
        asyncio.run(run_all_offline_tests())