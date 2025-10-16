"""
Simple test to verify Integro works without excessive API calls.
"""

import asyncio
import os
import time
from dotenv import load_dotenv
import pytest
import logging

from integro import IntegroAgent, ModelConfig
from agno.tools import tool

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API rate limit delay (seconds)
API_DELAY = 2

# Test models
TEST_MODELS = [
    {"provider": "groq", "model_id": "llama-3.1-8b-instant", "params": {"temperature": 0.1}},
]


@pytest.fixture
def simple_tools():
    """Provide simple test tools."""
    
    @tool
    def echo(text: str) -> str:
        """Echo the input text."""
        return text
    
    return [echo]


@pytest.mark.vcr(
    filter_headers=["authorization", "x-api-key"],
    record_mode="new_episodes"
)
@pytest.mark.asyncio
async def test_basic_response():
    """Test basic agent response without tools."""
    
    agent = IntegroAgent(
        name="Simple Agent",
        description="A simple test agent",
        user_id="test_user",
        models=TEST_MODELS,
        tools=[],  # No tools to avoid loops
        instructions=[
            "You are a simple test agent.",
            "Always respond with exactly 'Hello World' when asked to say hello.",
            "Be extremely concise."
        ],
        enable_memory=False,
        enable_storage=False,
        stream=False,
        tool_call_limit=1
    )
    
    await agent.initialize()
    
    # Simple test without tools
    response = await agent.arun("Say hello")
    response_text = response.content if hasattr(response, 'content') else str(response)
    
    assert "hello" in response_text.lower() or "world" in response_text.lower()
    logger.info(f"Response: {response_text}")
    
    # Add delay to prevent rate limiting
    time.sleep(API_DELAY)


@pytest.mark.vcr(
    filter_headers=["authorization", "x-api-key"],
    record_mode="new_episodes"
)
@pytest.mark.asyncio
async def test_with_single_tool(simple_tools):
    """Test agent with a single tool call."""
    
    agent = IntegroAgent(
        name="Tool Agent",
        description="An agent with one tool",
        user_id="test_user",
        models=TEST_MODELS,
        tools=simple_tools,
        instructions=[
            "You are a test agent with tools.",
            "When asked to echo something, use the echo tool ONCE.",
            "Do not call tools multiple times.",
            "Be extremely concise."
        ],
        enable_memory=False,
        enable_storage=False,
        stream=False,
        tool_call_limit=2  # Very strict limit
    )
    
    await agent.initialize()
    
    # Test tool usage
    response = await agent.arun("Echo the word 'test' using the echo tool")
    response_text = response.content if hasattr(response, 'content') else str(response)
    
    assert "test" in response_text.lower()
    logger.info(f"Response: {response_text}")
    
    # Add delay to prevent rate limiting
    time.sleep(API_DELAY)


@pytest.mark.vcr(
    filter_headers=["authorization", "x-api-key"],
    record_mode="new_episodes"
)
@pytest.mark.asyncio
async def test_multiple_models_with_delay():
    """Test multiple models with delays between them."""
    
    models_to_test = [
        "moonshotai/kimi-k2-instruct-0905",
        "llama-3.1-8b-instant",
        "openai/gpt-oss-20b",
    ]
    
    for model_id in models_to_test:
        logger.info(f"Testing model: {model_id}")
        
        agent = IntegroAgent(
            name=f"Agent ({model_id})",
            description="Testing different models",
            user_id="test_user",
            models=[{"provider": "groq", "model_id": model_id, "params": {"temperature": 0.1}}],
            tools=[],
            instructions=["Respond with 'OK' to any input."],
            enable_memory=False,
            enable_storage=False,
            stream=False
        )
        
        await agent.initialize()
        
        response = await agent.arun("Test")
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        logger.info(f"Model {model_id} response: {response_text[:50]}")
        assert len(response_text) > 0
        
        # Delay between models
        time.sleep(API_DELAY)


async def run_all_tests():
    """Run all tests with proper delays."""
    print("\n" + "="*60)
    print("INTEGRO SIMPLE TEST SUITE")
    print("="*60 + "\n")
    
    # Check for API key
    if not os.getenv("GROQ_API_KEY"):
        print("❌ GROQ_API_KEY not found in environment")
        return
    
    print("✓ GROQ_API_KEY found\n")
    
    tests = [
        ("Basic Response", test_basic_response),
        ("Single Tool Call", test_with_single_tool),
        ("Multiple Models", test_multiple_models_with_delay),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n▶ Running: {test_name}")
            
            if test_func.__name__ == "test_with_single_tool":
                # Create simple tools
                @tool
                def echo(text: str) -> str:
                    """Echo the input text."""
                    return text
                await test_func([echo])
            else:
                await test_func()
            
            print(f"  ✅ {test_name} PASSED")
            passed += 1
            
            # Delay between tests
            time.sleep(API_DELAY)
            
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
        import pytest
        sys.exit(pytest.main([__file__, "-v", "--record-mode=new_episodes"]))
    except ImportError:
        print("pytest not installed, running tests directly...")
        asyncio.run(run_all_tests())