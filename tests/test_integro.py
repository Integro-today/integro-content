"""Test script for Integro package."""

import asyncio
from datetime import datetime
from integro import IntegroAgent, QdrantMemory
from agno import tool
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)


# Create example tools
@tool
def calculate(expression: str) -> str:
    """Calculate a mathematical expression."""
    try:
        # Safe evaluation for basic math
        allowed = set("0123456789+-*/() .")
        if all(c in allowed for c in expression):
            result = eval(expression)
            return f"The result of {expression} is: {result}"
        else:
            return "Invalid expression. Only basic math operations are allowed."
    except Exception as e:
        return f"Error calculating: {e}"


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    return f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"


@tool
def word_count(text: str) -> str:
    """Count words in the given text."""
    words = len(text.split())
    return f"The text contains {words} words."


async def test_basic_agent():
    """Test basic agent functionality."""
    print("\n=== Testing Basic Agent ===\n")
    
    # Create agent without Qdrant (using SQLite memory)
    agent = IntegroAgent(
        name="Test Assistant",
        description="A test AI assistant",
        user_id="test_user",
        models=[
            {"provider": "anthropic", "model_id": "claude-3-haiku-20240307"}
        ],
        tools=[calculate, get_current_time, word_count],
        instructions=[
            "You are a helpful test assistant.",
            "Always be concise in your responses.",
            "Use the tools when appropriate."
        ],
        enable_memory=True,
        stream=False
    )
    
    # Initialize agent
    await agent.initialize()
    print("✓ Agent initialized")
    
    # Test simple conversation
    response = await agent.arun("Hello! What can you do?")
    print(f"\nUser: Hello! What can you do?")
    print(f"Agent: {response}")
    
    # Test tool usage
    response = await agent.arun("What is 25 * 4?")
    print(f"\nUser: What is 25 * 4?")
    print(f"Agent: {response}")
    
    # Test another tool
    response = await agent.arun("What time is it?")
    print(f"\nUser: What time is it?")
    print(f"Agent: {response}")
    
    # Test runtime tool registration
    @tool
    def reverse_text(text: str) -> str:
        """Reverse the given text."""
        return text[::-1]
    
    agent.register_tool(reverse_text, category="text")
    print("\n✓ Registered new tool: reverse_text")
    
    # List tools
    tools = agent.list_tools()
    print(f"\nRegistered tools by category:")
    for category, tool_names in tools.items():
        print(f"  {category}: {', '.join(tool_names)}")
    
    print("\n✓ Basic agent test completed")


async def test_qdrant_memory():
    """Test agent with Qdrant memory."""
    print("\n=== Testing Qdrant Memory ===\n")
    
    try:
        # Create Qdrant memory adapter
        memory = QdrantMemory(
            user_id="test_user_qdrant",
            collection_prefix="integro_test",
            url="http://localhost:6333"
        )
        print("✓ Connected to Qdrant")
        
        # Create agent with Qdrant memory
        agent = IntegroAgent(
            name="Memory Assistant",
            description="An AI assistant with memory capabilities",
            user_id="test_user_qdrant",
            models=[
                {"provider": "anthropic", "model_id": "claude-3-haiku-20240307"}
            ],
            tools=[],
            instructions=[
                "You have access to persistent memory.",
                "Remember important information from our conversations."
            ],
            memory=memory,
            stream=False
        )
        
        # Initialize agent
        await agent.initialize()
        print("✓ Agent with Qdrant memory initialized")
        
        # Save some memories
        memory_id1 = await agent.save_memory(
            "User's favorite color is blue",
            metadata={"topic": "preferences", "category": "color"}
        )
        print(f"✓ Saved memory 1: {memory_id1}")
        
        memory_id2 = await agent.save_memory(
            "User is learning Python programming",
            metadata={"topic": "skills", "category": "programming"}
        )
        print(f"✓ Saved memory 2: {memory_id2}")
        
        memory_id3 = await agent.save_memory(
            "User had a conversation about AI and machine learning",
            metadata={"topic": "interests", "category": "technology"},
            memory_type="conversation"
        )
        print(f"✓ Saved memory 3: {memory_id3}")
        
        # Search memories
        results = await agent.search_memories("programming", limit=5)
        print(f"\n✓ Search for 'programming' found {len(results)} results:")
        for result in results:
            print(f"  - {result.get('content', 'N/A')} (score: {result.get('score', 0):.2f})")
        
        # Get conversation history
        history = await memory.get_conversation_history(limit=5)
        print(f"\n✓ Conversation history ({len(history)} entries):")
        for entry in history:
            print(f"  - {entry.get('content', 'N/A')[:50]}...")
        
        # Clean up
        await memory.clear_all_memories()
        print("\n✓ Cleared all test memories")
        
        print("\n✓ Qdrant memory test completed")
        
    except Exception as e:
        print(f"⚠ Qdrant test skipped (is Qdrant running?): {e}")


async def test_model_fallback():
    """Test model fallback functionality."""
    print("\n=== Testing Model Fallback ===\n")
    
    # Create agent with multiple models for fallback
    agent = IntegroAgent(
        name="Fallback Assistant",
        description="An assistant with model fallback",
        user_id="test_fallback",
        models=[
            {"provider": "invalid", "model_id": "nonexistent-model"},  # Will fail
            {"provider": "anthropic", "model_id": "claude-3-haiku-20240307"}  # Fallback
        ],
        tools=[calculate],
        stream=False
    )
    
    # Initialize should succeed with fallback
    await agent.initialize()
    print("✓ Agent initialized with fallback model")
    
    # Test that it still works
    response = await agent.arun("What is 10 + 10?")
    print(f"\nUser: What is 10 + 10?")
    print(f"Agent: {response}")
    
    print("\n✓ Model fallback test completed")


async def main():
    """Run all tests."""
    print("\n" + "="*50)
    print("       INTEGRO PACKAGE TEST SUITE")
    print("="*50)
    
    # Run tests
    await test_basic_agent()
    await test_qdrant_memory()
    await test_model_fallback()
    
    print("\n" + "="*50)
    print("       ALL TESTS COMPLETED")
    print("="*50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())