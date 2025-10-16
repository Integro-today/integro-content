"""
Test that verifies we can run tests offline using recorded cassettes.
This test will fail if it tries to make any real API calls.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
import pytest
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from integro import IntegroAgent
from agno.tools import tool

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test models
TEST_MODELS = [
    {"provider": "groq", "model_id": "llama-3.1-8b-instant", "params": {"temperature": 0.1}},
]


@pytest.mark.vcr(
    filter_headers=["authorization", "x-api-key"],
    record_mode="none"  # This will fail if it tries to make a real API call
)
@pytest.mark.asyncio
async def test_offline_basic_response():
    """Test that we can run without hitting the API."""
    
    agent = IntegroAgent(
        name="Simple Agent",
        description="A simple test agent",
        user_id="test_user",
        models=TEST_MODELS,
        tools=[],
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
    
    # This should use the cassette and not make a real API call
    response = await agent.arun("Say hello")
    response_text = response.content if hasattr(response, 'content') else str(response)
    
    assert "hello" in response_text.lower() or "world" in response_text.lower()
    logger.info(f"Offline test successful! Response: {response_text}")


if __name__ == "__main__":
    # Run with pytest
    sys.exit(pytest.main([__file__, "-v"]))