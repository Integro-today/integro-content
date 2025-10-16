"""
Test knowledge base retrieval with in-memory Qdrant.
The agent can only answer questions by querying the knowledge base.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
import pytest
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from integro import IntegroAgent, KnowledgeBase, KnowledgeTools
from integro.utils.logging import get_logger

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test models
TEST_MODELS = [
    {"provider": "groq", "model_id": "moonshotai/kimi-k2-instruct-0905", "params": {"temperature": 0.1}},
]


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


@pytest.fixture
def knowledge_base():
    """Provide a knowledge base with test data."""
    return setup_knowledge_base()


@pytest.fixture
def knowledge_tools(knowledge_base):
    """Provide knowledge tools."""
    return KnowledgeTools(knowledge_base)


@pytest.mark.vcr(
    filter_headers=["authorization", "x-api-key"],
    record_mode="new_episodes"
)
@pytest.mark.asyncio
async def test_knowledge_retrieval_only(knowledge_tools):
    """Test that agent can only answer from knowledge base."""
    
    # Create agent with ONLY knowledge tools
    agent = IntegroAgent(
        name="Knowledge Agent",
        description="An agent that can only answer from its knowledge base",
        user_id="test_user",
        models=TEST_MODELS,
        tools=knowledge_tools.get_tools(),
        instructions=[
            "You are a knowledge retrieval agent with STRICT limitations.",
            "CRITICAL: You MUST call the search_knowledge tool for EVERY question.",
            "You have NO other knowledge except what you find with search_knowledge.",
            "NEVER provide information without searching first.",
            "If search_knowledge returns no results, respond ONLY with: 'No information found in knowledge base'.",
            "When you find information, quote it EXACTLY as returned by the tool.",
            "Do NOT add explanations or context beyond what the tool returns.",
        ],
        enable_memory=False,
        enable_storage=False,
        stream=False,
        tool_call_limit=5  # Increased limit
    )
    
    await agent.initialize()
    
    # Test 1: Ask about Planet Zephyr (should find in KB)
    response = await agent.arun("What is the population of Planet Zephyr?")
    response_text = response.content if hasattr(response, 'content') else str(response)
    
    logger.info(f"Test 1 - Planet Zephyr population: {response_text}")
    assert "7,892,345" in response_text or "7892345" in response_text, \
        f"Agent should find population in KB. Got: {response_text}"
    
    # Test 2: Ask about the founder (should find in KB)
    response = await agent.arun("Who founded the Integro Framework and when?")
    response_text = response.content if hasattr(response, 'content') else str(response)
    
    logger.info(f"Test 2 - Integro founder: {response_text}")
    assert "Alexandra Quantum" in response_text or "2157" in response_text, \
        f"Agent should find founder info in KB. Got: {response_text}"
    
    # Test 3: Ask about something NOT in KB (should not make up info)
    response = await agent.arun("What is the weather like on Earth today?")
    response_text = response.content if hasattr(response, 'content') else str(response)
    
    logger.info(f"Test 3 - Weather (not in KB): {response_text}")
    assert ("don't have" in response_text.lower() or 
            "no information" in response_text.lower() or
            "not found" in response_text.lower() or
            "no results" in response_text.lower()), \
        f"Agent should indicate info not in KB. Got: {response_text}"


@pytest.mark.vcr(
    filter_headers=["authorization", "x-api-key"],
    record_mode="new_episodes"
)
@pytest.mark.asyncio
async def test_knowledge_search_relevance(knowledge_tools):
    """Test that agent retrieves relevant documents based on query."""
    
    agent = IntegroAgent(
        name="Search Agent",
        description="An agent that searches the knowledge base",
        user_id="test_user",
        models=TEST_MODELS,
        tools=knowledge_tools.get_tools(),
        instructions=[
            "You are a knowledge search agent.",
            "ALWAYS use search_knowledge tool first before answering.",
            "Report EXACTLY what you find in the search results.",
            "Include the relevance scores if shown.",
            "Do NOT provide any information not found in search results.",
        ],
        enable_memory=False,
        enable_storage=False,
        stream=False,
        tool_call_limit=5
    )
    
    await agent.initialize()
    
    # Test searching for robotics laws
    response = await agent.arun("Search for information about robotics laws")
    response_text = response.content if hasattr(response, 'content') else str(response)
    
    logger.info(f"Robotics laws search: {response_text}")
    assert ("type hints" in response_text.lower() or 
            "divide by zero" in response_text.lower() or
            "42" in response_text), \
        f"Should find robotics laws. Got: {response_text}"


@pytest.mark.vcr(
    filter_headers=["authorization", "x-api-key"],
    record_mode="new_episodes"
)
@pytest.mark.asyncio
async def test_knowledge_complex_query(knowledge_tools):
    """Test complex queries requiring specific KB lookups."""
    
    agent = IntegroAgent(
        name="Research Agent",
        description="An agent that researches using the knowledge base",
        user_id="test_user",
        models=TEST_MODELS,
        tools=knowledge_tools.get_tools(),
        instructions=[
            "You are a research agent with access to ONLY a knowledge base.",
            "For EVERY question, you MUST search the knowledge base first.",
            "You may search multiple times with different queries if needed.",
            "ONLY provide information that appears in search results.",
            "Quote the search results directly when answering.",
            "If no results found, say 'No information in knowledge base'.",
        ],
        enable_memory=False,
        enable_storage=False,
        stream=False,
        tool_call_limit=8
    )
    
    await agent.initialize()
    
    # Complex query requiring specific information
    response = await agent.arun(
        "I need to know about error codes. What is error E-789 and how do I fix it?"
    )
    response_text = response.content if hasattr(response, 'content') else str(response)
    
    logger.info(f"Error code query: {response_text}")
    assert ("random test data" in response_text.lower() or 
            "add more test data" in response_text.lower() or
            "E-789" in response_text), \
        f"Should find error code info. Got: {response_text}"


@pytest.mark.asyncio
async def test_knowledge_without_vcr():
    """Test knowledge base without API calls (no VCR needed)."""
    
    # This test doesn't make API calls, just tests the knowledge base directly
    kb = setup_knowledge_base()
    
    # Test direct search
    results = kb.search("Planet Zephyr", limit=1)
    assert len(results) > 0, "Should find Planet Zephyr"
    
    doc, score = results[0]
    assert "purple oceans" in doc["content"], "Should contain planet details"
    assert doc["doc_id"] == "planet_zephyr", "Should have correct doc ID"
    
    # Test searching for founder
    results = kb.search("founder Integro", limit=1)
    assert len(results) > 0, "Should find founder information"
    
    # Test document retrieval by ID
    doc = kb.get_document("secret_recipe")
    assert doc is not None, "Should retrieve document by ID"
    assert "42 lines of code" in doc["content"], "Should contain recipe details"
    
    logger.info("Direct knowledge base tests passed!")


async def run_all_tests():
    """Run all knowledge tests."""
    print("\n" + "="*60)
    print("INTEGRO KNOWLEDGE BASE TEST SUITE")
    print("="*60 + "\n")
    
    # Check for API key
    if not os.getenv("GROQ_API_KEY"):
        print("❌ GROQ_API_KEY not found in environment")
        print("   Running only non-API tests...")
        await test_knowledge_without_vcr()
        return
    
    print("✓ GROQ_API_KEY found\n")
    
    # Set up knowledge base and tools
    kb = setup_knowledge_base()
    tools = KnowledgeTools(kb)
    
    tests = [
        ("Knowledge Retrieval Only", test_knowledge_retrieval_only, tools),
        ("Search Relevance", test_knowledge_search_relevance, tools),
        ("Complex Queries", test_knowledge_complex_query, tools),
        ("Direct KB Access", test_knowledge_without_vcr, None),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func, test_tools in tests:
        try:
            print(f"\n▶ Running: {test_name}")
            
            if test_tools:
                await test_func(test_tools)
            else:
                await test_func()
            
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
        asyncio.run(run_all_tests())