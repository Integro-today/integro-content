# Complete Local Setup Guide for Integro

This guide will walk you through setting up the entire Integro system locally, including all dependencies and databases.

## Prerequisites

- Python 3.8+ (3.11 recommended)
- Docker (for Qdrant) or ability to run containers
- Git
- A Groq API key (for LLM access)

## Step 1: Clone and Navigate to Project

```bash
git clone <repository-url>
cd integro-agents
```

## Step 2: Set Up Python Environment

### Option A: Using Make (Easiest)

```bash
# Full automated setup
make full-setup

# This will:
# 1. Install uv package manager
# 2. Create virtual environment
# 3. Install all dependencies including dev tools
```

### Option B: Using UV Script

```bash
# Make script executable
chmod +x uv_setup.sh

# Run automated setup
./uv_setup.sh
```

### Option C: Manual Setup

```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv --python 3.11

# Activate it
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e ".[dev]"
```

## Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Create .env file
cat > .env << 'EOF'
# LLM Provider Keys (at least one required)
GROQ_API_KEY=your_groq_api_key_here

# Optional: Other LLM providers
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_google_key_here

# Qdrant Configuration (optional - defaults shown)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # Leave empty for local Qdrant

# Optional: Custom paths
INTEGRO_CONFIG_DB=configs.db
INTEGRO_SESSIONS_DB=sessions.db
INTEGRO_MEMORY_DB=memory.db
EOF
```

Then edit the file to add your actual API keys:
```bash
nano .env  # or use your preferred editor
```

### Getting API Keys

- **Groq**: Sign up at https://console.groq.com/keys
- **Anthropic**: https://console.anthropic.com/
- **OpenAI**: https://platform.openai.com/api-keys
- **Google**: https://makersuite.google.com/app/apikey

## Step 4: Set Up Qdrant Vector Database

Qdrant is used for semantic memory and knowledge storage. Choose one option:

### Option A: Docker (Recommended for Production)

```bash
# Pull and run Qdrant
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant

# Verify it's running
curl http://localhost:6333/collections
# Should return: {"result":{"collections":[]},"status":"ok","time":0.0}
```

### Option B: Docker Compose (For persistence)

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__LOG_LEVEL=INFO
```

Then run:
```bash
docker-compose up -d
```

### Option C: In-Memory (For testing only)

No setup needed! The code can use in-memory Qdrant:
```python
# In your code
kb = KnowledgeBase(in_memory=True)
```

## Step 5: Initialize Databases

The SQLite databases will be created automatically on first run, but you can initialize them manually:

```bash
# Activate environment if not already
source .venv/bin/activate

# Initialize databases via Python
python -c "
from integro.config.storage import ConfigStorage
storage = ConfigStorage('configs.db')
print('✓ Databases initialized')
"
```

## Step 6: Verify Installation

### Run Tests
```bash
# Quick test with caching
make test

# Or manually
python -m pytest tests/test_simple.py -v

# Test offline mode (no API calls)
make test-offline
```

### Run Example Agent
```bash
# Quick example
make run-example

# Or manually
python -c "
from integro import IntegroAgent
import asyncio

async def main():
    agent = IntegroAgent(
        name='TestBot',
        models=[{'provider': 'groq', 'model_id': 'llama-3.1-8b-instant'}]
    )
    await agent.initialize()
    response = await agent.arun('Hello! How are you?')
    print(response)

asyncio.run(main())
"
```

## Step 7: Using the CLI Tools

Integro provides several CLI interfaces:

### Agent Manager TUI
```bash
python -m integro.cli agents
# Interactive terminal UI for managing agents
```

### Knowledge Base Manager TUI
```bash
python -m integro.cli knowledge
# Interactive terminal UI for managing knowledge bases
```

### Chat Interface TUI
```bash
python -m integro.cli chat
# Interactive chat with your agents
```

## Step 8: Create Your First Agent

```python
# example_agent.py
import asyncio
from integro import IntegroAgent
from integro.memory import QdrantMemory
from agno import tool

# Define a custom tool
@tool
def calculate(expression: str) -> str:
    """Calculate a mathematical expression."""
    try:
        result = eval(expression)
        return f"The result is: {result}"
    except:
        return "Invalid expression"

async def main():
    # Create agent with memory
    agent = IntegroAgent(
        name="MathAssistant",
        description="A helpful math assistant",
        models=[
            {"provider": "groq", "model_id": "llama-3.1-8b-instant"}
        ],
        memory=QdrantMemory(user_id="user123"),
        tools=[calculate],
        instructions=[
            "You are a helpful math assistant.",
            "Always explain your calculations."
        ]
    )
    
    # Initialize
    await agent.initialize()
    
    # Test conversation
    print("Agent: " + await agent.arun("Hello!"))
    print("Agent: " + await agent.arun("What's 25 * 4?"))
    print("Agent: " + await agent.arun("Remember that my favorite number is 42"))
    print("Agent: " + await agent.arun("What's my favorite number multiplied by 2?"))

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python example_agent.py
```

## Troubleshooting

### Issue: "GROQ_API_KEY not found"
**Solution**: Make sure your `.env` file exists and contains:
```
GROQ_API_KEY=your_actual_key_here
```

### Issue: "Connection refused" to Qdrant
**Solution**: Make sure Qdrant is running:
```bash
# Check if Docker container is running
docker ps | grep qdrant

# If not, start it
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
```

### Issue: "Rate limit exceeded" errors
**Solution**: Use the cached test mode:
```bash
make test  # Uses cached responses after first run
```

### Issue: Import errors
**Solution**: Make sure you're in the virtual environment:
```bash
source .venv/bin/activate
pip list | grep integro  # Should show integro installed
```

### Issue: SQLite database locked
**Solution**: Close other connections or delete and recreate:
```bash
rm *.db
python -c "from integro.config.storage import ConfigStorage; ConfigStorage()"
```

## Directory Structure After Setup

```
integro-agents/
├── .venv/              # Python virtual environment
├── .env                # Your API keys and config
├── configs.db          # SQLite: agent configurations
├── sessions.db         # SQLite: chat sessions
├── memory.db           # SQLite: memory metadata
├── qdrant_storage/     # Qdrant vector data (if using Docker)
├── tests/
│   └── cassettes/      # Cached API responses for tests
└── integro/            # Main package code
```

## Next Steps

1. **Explore the TUI**: Run `python -m integro.cli agents` to create agents interactively
2. **Read the docs**: Check `claude_learnings.md` and `memory_knowledge_explained.md`
3. **Build custom agents**: Extend `BaseAgent` class for custom behavior
4. **Add tools**: Create custom tools using the `@tool` decorator
5. **Manage knowledge**: Use `KnowledgeBase` class to add documents

## Quick Reference

```bash
# Activate environment
source .venv/bin/activate

# Run tests
make test

# Format code
make format

# Lint code
make lint

# Clean everything
make clean

# Start Qdrant
docker start qdrant

# Stop Qdrant
docker stop qdrant

# View Qdrant collections
curl http://localhost:6333/collections

# Open SQLite CLI
sqlite3 configs.db
```

## Support

- Check `tests/` directory for usage examples
- Read `TESTING.md` for test documentation
- Review agent examples in `tests/test_simple.py`

You're now ready to build AI agents with Integro!