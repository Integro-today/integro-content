# Integro

A generic, configurable AI agent framework with runtime tool configuration and Qdrant memory support.

## Features

- **Runtime Configurable**: Configure tools, models, and instructions at runtime
- **Model Fallback**: Automatic fallback between multiple LLM providers
- **Memory Management**: User-scoped memory with Qdrant vector database
- **Tool Registry**: Dynamic tool loading and configuration
- **Clean Architecture**: No business-specific logic, fully extensible
- **Async Support**: Full async/await support with uvloop compatibility

## Installation

```bash
pip install integro
```

## Quick Start

```python
from integro import IntegroAgent
from integro.memory import QdrantMemory

# Create an agent with memory
agent = IntegroAgent(
    name="Assistant",
    description="A helpful AI assistant",
    user_id="user123",
    models=[
        {"provider": "anthropic", "model_id": "claude-3-sonnet-20240229"},
        {"provider": "google", "model_id": "gemini-pro"}
    ],
    memory=QdrantMemory(user_id="user123"),
    tools=[],  # Add your tools here
    instructions=[
        "You are a helpful assistant.",
        "Always be concise and clear."
    ]
)

# Run the agent
response = await agent.arun("Hello, how can you help me?")
print(response)
```

## Configuration

### Models

Integro supports multiple model providers with automatic fallback:

```python
models = [
    {
        "provider": "anthropic",
        "model_id": "claude-3-sonnet-20240229",
        "params": {"temperature": 0.7}
    },
    {
        "provider": "openai",
        "model_id": "gpt-4-turbo-preview",
        "params": {"max_tokens": 2000}
    }
]
```

### Memory

Use Qdrant for user-scoped memory:

```python
from integro.memory import QdrantMemory

memory = QdrantMemory(
    user_id="user123",
    collection_name="conversations",
    url="http://localhost:6333"
)
```

### Tools

Register tools at runtime:

```python
from agno import tool

@tool
def calculate(expression: str) -> str:
    """Calculate a mathematical expression."""
    return str(eval(expression))

agent = IntegroAgent(
    tools=[calculate],
    # ... other config
)
```

## Architecture

Integro follows a clean, modular architecture:

- `integro.agent.base`: Base agent class with core functionality
- `integro.agent.config`: Configuration classes for models and agents
- `integro.agent.integro`: Main IntegroAgent implementation
- `integro.memory`: Memory adapters (Qdrant)
- `integro.tools`: Tool registry and management
- `integro.utils`: Utility functions
