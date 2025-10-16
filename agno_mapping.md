# Agno Framework API Mapping

**Version**: 2.0+
**Purpose**: Comprehensive API reference for building multi-agent systems with Agno
**Documentation**: https://docs.agno.com
**Repository**: https://github.com/agno-agi/agno

---

## Table of Contents

1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [Agents](#agents)
4. [Teams](#teams)
5. [Workflows](#workflows)
6. [Tools](#tools)
7. [Knowledge (RAG)](#knowledge-rag)
8. [Memory](#memory)
9. [Storage & Sessions](#storage--sessions)
10. [AgentOS](#agentos)
11. [Models](#models)
12. [Complete Examples](#complete-examples)

---

## Overview

Agno is a **multi-agent framework, runtime, and UI built for speed**. It enables building production-ready agentic systems with:

- **Agents**: Individual AI entities with tools, knowledge, and memory
- **Teams**: Collections of agents working collaboratively
- **Workflows**: Deterministic step-based orchestration
- **AgentOS**: Production runtime with FastAPI backend and web UI
- **Complete Privacy**: Runs entirely in your infrastructure

### Key Design Principles

1. **Start Simple**: Begin with model + tools + instructions, add complexity as needed
2. **Privacy First**: All data stays in your infrastructure
3. **Production Ready**: Built-in database persistence, session management, metrics
4. **Flexible Orchestration**: Choose between autonomous teams or controlled workflows

---

## Core Concepts

### Architecture Hierarchy

```
AgentOS (Runtime + UI)
├── Workflows (Deterministic orchestration)
│   ├── Agents
│   ├── Teams
│   └── Functions
├── Teams (Collaborative agents)
│   └── Members (Agents)
└── Agents (Individual AI entities)
    ├── Model
    ├── Tools
    ├── Knowledge
    ├── Memory
    └── Storage
```

### Key Terminology

- **Agent**: Individual AI entity with model, tools, instructions
- **Team**: Group of agents collaborating on complex tasks
- **Workflow**: Sequential/conditional execution of agents, teams, and functions
- **Session**: Multi-turn conversation identified by `session_id`
- **Run**: Single interaction/turn within a session (identified by `run_id`)
- **Messages**: Communication protocol between agent and model
- **Knowledge**: Domain-specific content for RAG (Retrieval Augmented Generation)
- **Memory**: Persistent user information across sessions
- **Storage**: Database layer for sessions, state, and history

---

## Agents

### Basic Agent Creation

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

agent = Agent(
    name="My Agent",
    model=OpenAIChat(id="gpt-4o"),
    instructions="You are a helpful assistant.",
    markdown=True
)
```

### Agent with Tools

```python
from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools

agent = Agent(
    name="Web Search Agent",
    tools=[DuckDuckGoTools()],
    instructions="Search the web and provide accurate information.",
    markdown=True
)
```

### Agent with Database & Sessions

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude

agent = Agent(
    name="Persistent Agent",
    model=Claude(id="claude-sonnet-4-5"),
    db=SqliteDb(db_file="agent.db"),
    add_history_to_context=True,  # Include conversation history
    num_history_runs=3,  # How many previous runs to include
    markdown=True
)
```

### Agent with Knowledge (RAG)

```python
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector
from agno.knowledge.embedder.openai import OpenAIEmbedder

knowledge = Knowledge(
    name="Product Knowledge",
    vector_db=PgVector(
        table_name="vectors",
        db_url="postgresql://user:pass@localhost/db",
        embedder=OpenAIEmbedder()
    )
)

agent = Agent(
    name="Knowledge Agent",
    knowledge=knowledge,
    search_knowledge=True,  # Adds search_knowledge_base() tool
    instructions="Use the knowledge base to answer questions."
)
```

### Agent with Memory

```python
from agno.agent import Agent
from agno.db.postgres import PostgresDb

agent = Agent(
    name="Memory Agent",
    db=PostgresDb(db_url="postgresql://...", memory_table="user_memories"),
    enable_agentic_memory=True,  # Agent can manage memories with tool
    # OR
    enable_user_memories=True,  # Auto-run MemoryManager after each response
    markdown=True
)
```

### Complete Agent Configuration

```python
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.db.sqlite import SqliteDb
from agno.tools.duckduckgo import DuckDuckGoTools

agent = Agent(
    # Identity
    name="Research Agent",
    description="Expert research assistant",

    # Model
    model=Claude(id="claude-sonnet-4-5"),

    # Instructions
    instructions="You are a research expert. Be thorough and cite sources.",

    # Tools
    tools=[DuckDuckGoTools()],

    # Database & Persistence
    db=SqliteDb(db_file="research.db"),

    # Session History
    add_history_to_context=True,
    num_history_runs=5,

    # Knowledge
    knowledge=None,  # Add Knowledge object here
    search_knowledge=False,

    # Memory
    enable_user_memories=False,

    # Output
    markdown=True,

    # Session State
    session_state={"key": "value"},  # Custom state

    # Tool Behavior
    tool_call_limit=20,  # Max tool calls per run

    # Guardrails
    guardrails=[],  # Add guardrail instances
)
```

### Running Agents

#### Synchronous Execution

```python
from agno.agent import Agent, RunOutput

agent = Agent(...)

# Non-streaming
response: RunOutput = agent.run("What is the weather?")
print(response.content)
print(response.run_id)
print(response.session_id)

# Streaming
stream = agent.run("Tell me a story", stream=True)
for chunk in stream:
    if chunk.event == "run_content":
        print(chunk.content, end="")
```

#### Asynchronous Execution

```python
import asyncio
from agno.agent import Agent, RunOutput

agent = Agent(...)

async def main():
    # Non-streaming
    response: RunOutput = await agent.arun("Hello!")
    print(response.content)

    # Streaming
    stream = await agent.arun("Tell me a story", stream=True)
    async for chunk in stream:
        if chunk.event == "run_content":
            print(chunk.content, end="")

asyncio.run(main())
```

#### With User and Session IDs

```python
response = agent.run(
    "What did I ask before?",
    user_id="user_123",
    session_id="session_456"
)
```

#### Pretty Print Helper

```python
from agno.utils.pprint import pprint_run_response

response = agent.run("Hello")
pprint_run_response(response, markdown=True)

# Or with streaming
stream = agent.run("Hello", stream=True)
pprint_run_response(stream, markdown=True)
```

### Agent RunOutput Schema

```python
response: RunOutput = agent.run("Hello")

# Key attributes:
response.run_id          # Unique run identifier
response.session_id      # Session identifier
response.agent_id        # Agent identifier
response.agent_name      # Agent name
response.user_id         # User identifier
response.content         # Response content (str)
response.content_type    # Content type
response.messages        # List of messages sent to model
response.metrics         # Run metrics (latency, tokens, etc.)
response.model           # Model used for run
```

### Agent Methods

```python
agent = Agent(...)

# Run methods
agent.run(input, user_id=None, session_id=None, stream=False)
await agent.arun(input, user_id=None, session_id=None, stream=False)

# Print helpers (dev only)
agent.print_response(input, stream=False)
await agent.aprint_response(input, stream=False)

# Session management
agent.get_messages_for_session(session_id=None)
agent.get_user_memories(user_id)

# Knowledge
agent.search_knowledge_base(query, num_documents=5)

# Cancel run
agent.cancel_run(run_id)
```

---

## Teams

### Basic Team Creation

```python
from agno.team import Team
from agno.agent import Agent
from agno.models.openai import OpenAIChat

# Create specialized agents
news_agent = Agent(
    name="News Agent",
    role="Get the latest news and provide summaries"
)

weather_agent = Agent(
    name="Weather Agent",
    role="Get weather information and forecasts"
)

# Create team
team = Team(
    name="News and Weather Team",
    members=[news_agent, weather_agent],
    model=OpenAIChat(id="gpt-4o"),
    instructions="Coordinate with team members to provide comprehensive information."
)
```

### Running Teams

```python
from agno.team import Team

team = Team(...)

# Non-streaming
response = team.run("What's the news in Tokyo?")
print(response.content)

# Streaming
stream = team.run("What's the weather?", stream=True)
for chunk in stream:
    if chunk.event == "TeamRunContent":
        print(chunk.content, end="")

# Pretty print
from agno.utils.pprint import pprint_run_response
stream = team.run("Hello", stream=True)
pprint_run_response(stream, markdown=True)
```

### Team Configuration

```python
team = Team(
    name="Research Team",
    members=[agent1, agent2, agent3],
    model=OpenAIChat(id="gpt-4o"),
    instructions="Coordinate research tasks among team members.",

    # Database & Sessions
    db=SqliteDb(db_file="team.db"),
    add_history_to_context=True,
    num_history_runs=3,

    # Knowledge & Memory
    knowledge=None,
    search_knowledge=False,
    enable_user_memories=False,

    # State
    session_state={},

    # Output
    markdown=True
)
```

---

## Workflows

### Overview

Workflows provide **deterministic, controlled orchestration** of agents, teams, and functions through sequential or conditional steps.

**Use Workflows when:**
- You need predictable, repeatable processes
- You require clear audit trails
- You need complex multi-step orchestration
- You want parallel processing or conditional branching

**Use Teams when:**
- You need flexible, collaborative problem-solving
- Agents should autonomously delegate tasks

### Basic Workflow

```python
from agno.workflow import Workflow, RunEvent
from agno.agent import Agent

research_agent = Agent(name="Researcher", ...)
writer_agent = Agent(name="Writer", ...)

workflow = Workflow(
    name="Content Creation Workflow",
    steps=[
        research_agent,  # Step 1: Research
        writer_agent     # Step 2: Write
    ]
)

# Run workflow
result = workflow.run("Write about AI")
print(result.content)
```

### Workflow with Functions

```python
from agno.workflow import Workflow

def process_data(input_data: str) -> str:
    """Custom processing function."""
    return f"Processed: {input_data}"

workflow = Workflow(
    name="Hybrid Workflow",
    steps=[
        research_agent,
        process_data,  # Custom function
        writer_agent
    ]
)
```

### Running Workflows

```python
# Synchronous
result = workflow.run("Input message", stream=False)

# Asynchronous
result = await workflow.arun("Input message")

# With session
result = workflow.run(
    "Message",
    user_id="user_123",
    session_id="session_456"
)
```

### Workflow Features

- **Session State**: Shared state across all steps
- **Workflow History**: Access previous step outputs
- **Early Stopping**: Terminate based on conditions
- **Parallel Execution**: Run steps concurrently
- **Conditional Branching**: Dynamic step selection
- **Background Execution**: Non-blocking workflow runs

---

## Tools

### Using Pre-built Toolkits

```python
from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools

agent = Agent(
    tools=[
        DuckDuckGoTools(),
        HackerNewsTools()
    ]
)
```

### Common Toolkits

```python
# Web Search
from agno.tools.duckduckgo import DuckDuckGoTools

# Hacker News
from agno.tools.hackernews import HackerNewsTools

# MCP Tools (Model Context Protocol)
from agno.tools.mcp import MCPTools

# File operations
from agno.tools.file import FileTools

# Shell commands
from agno.tools.shell import ShellTools
```

### Writing Custom Tools

```python
import httpx
from agno.agent import Agent

def get_weather(city: str) -> str:
    """Get current weather for a city.

    Args:
        city (str): Name of the city

    Returns:
        str: Weather information
    """
    # API call logic here
    response = httpx.get(f"https://api.weather.com/{city}")
    return response.json()

agent = Agent(tools=[get_weather])
```

### Tools with Built-in Parameters

Tools can access agent context via built-in parameters:

```python
from agno.agent import Agent

def access_state(session_state: dict, agent: Agent) -> str:
    """Access agent session state and agent instance.

    Args:
        session_state: Automatically injected
        agent: Automatically injected
    """
    return f"Shopping list: {session_state['shopping_list']}"

agent = Agent(
    tools=[access_state],
    session_state={"shopping_list": ["milk", "bread"]}
)
```

**Available built-in parameters:**
- `session_state: dict` - Session state
- `agent: Agent` - Agent instance
- `team: Team` - Team instance
- `dependencies: dict` - Agent dependencies

### MCP Tools

```python
from agno.agent import Agent
from agno.tools.mcp import MCPTools
import asyncio

async def run_mcp_agent():
    # Initialize MCP tools
    mcp_tools = MCPTools(
        command="uvx mcp-server-git",
        # OR
        transport="streamable-http",
        url="https://docs.agno.com/mcp"
    )

    # Connect to MCP server
    await mcp_tools.connect()

    agent = Agent(tools=[mcp_tools], markdown=True)
    await agent.aprint_response("What is the license?", stream=True)

asyncio.run(run_mcp_agent())
```

---

## Knowledge (RAG)

### Knowledge Architecture

Knowledge enables **Retrieval Augmented Generation (RAG)** by storing domain-specific content in a vector database and retrieving relevant information at runtime.

**Key Components:**
1. **Contents DB**: Stores metadata, names, descriptions
2. **Vector DB**: Stores embeddings for semantic search
3. **Embedder**: Converts content to vectors
4. **Chunking**: Breaks documents into searchable pieces

### Basic Knowledge Setup

```python
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.db.postgres import PostgresDb

# Create knowledge base
knowledge = Knowledge(
    name="Product Documentation",
    description="Technical product documentation",

    # Contents database (metadata)
    contents_db=PostgresDb(
        db_url="postgresql://localhost/db",
        knowledge_table="knowledge_contents"
    ),

    # Vector database (embeddings)
    vector_db=PgVector(
        table_name="vectors",
        db_url="postgresql://localhost/db",
        embedder=OpenAIEmbedder()
    )
)
```

### Adding Content to Knowledge

```python
import asyncio

# From URL
asyncio.run(
    knowledge.add_content_async(
        name="Product Manual",
        url="https://example.com/manual.pdf",
        metadata={"category": "documentation"}
    )
)

# From file
asyncio.run(
    knowledge.add_content_async(
        name="Internal Docs",
        file_path="/path/to/docs.pdf",
        metadata={"internal": True}
    )
)

# From text
asyncio.run(
    knowledge.add_content_async(
        name="FAQ",
        content="Q: What is Agno? A: Agno is...",
        metadata={"type": "faq"}
    )
)
```

### Using Knowledge with Agents

```python
from agno.agent import Agent

# Agentic RAG (default) - Agent searches when needed
agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,  # Adds search_knowledge_base() tool
    instructions="Use the knowledge base to answer questions."
)

# Traditional RAG - Auto-add to context
agent = Agent(
    knowledge=knowledge,
    add_knowledge_to_context=True,  # Auto-retrieve based on query
    search_knowledge=False,  # Don't give tool
)
```

### Custom Knowledge Retriever

```python
from agno.agent import Agent
from typing import Optional

def custom_retriever(
    agent: Agent,
    query: str,
    num_documents: Optional[int],
    **kwargs
) -> Optional[list[dict]]:
    """Custom knowledge retrieval logic."""
    # Your custom search logic here
    results = agent.knowledge.search(query, limit=num_documents)
    return results

agent = Agent(
    knowledge=knowledge,
    knowledge_retriever=custom_retriever,
    search_knowledge=True
)
```

### Vector Databases

```python
# PostgreSQL with pgvector
from agno.vectordb.pgvector import PgVector

# Qdrant
from agno.vectordb.qdrant import Qdrant

# ChromaDB
from agno.vectordb.chroma import ChromaDB

# LanceDB
from agno.vectordb.lancedb import LanceDB

# Pinecone
from agno.vectordb.pinecone import Pinecone
```

### Embedders

```python
# OpenAI
from agno.knowledge.embedder.openai import OpenAIEmbedder

# Cohere
from agno.knowledge.embedder.cohere import CohereEmbedder

# HuggingFace
from agno.knowledge.embedder.huggingface import HuggingFaceEmbedder

# Sentence Transformers
from agno.knowledge.embedder.sentencetransformers import SentenceTransformersEmbedder

# Ollama (local)
from agno.knowledge.embedder.ollama import OllamaEmbedder
```

---

## Memory

### Overview

Memory gives agents the ability to **recall information about users** across sessions, providing personalized experiences.

### User Memories

```python
from agno.agent import Agent
from agno.db.postgres import PostgresDb

user_id = "user_123"

agent = Agent(
    db=PostgresDb(
        db_url="postgresql://localhost/db",
        memory_table="user_memories"
    ),

    # Option 1: Agent manages memories with tool
    enable_agentic_memory=True,

    # Option 2: Auto-run MemoryManager after each response
    # enable_user_memories=True,
)

# First interaction - agent learns
agent.print_response(
    "My name is Alice and I love hiking.",
    user_id=user_id
)

# Retrieve memories
memories = agent.get_user_memories(user_id=user_id)
print(memories)

# Later interaction - agent recalls
agent.print_response(
    "What outdoor activities should I try?",
    user_id=user_id
)
```

### Memory Table Schema

The `memory_table` stores:

| Field | Type | Description |
|-------|------|-------------|
| id | str | Memory identifier |
| user_id | str | User identifier |
| memory | str | Memory content |
| metadata | dict | Additional metadata |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

---

## Storage & Sessions

### Database Options

```python
# SQLite (local development)
from agno.db.sqlite import SqliteDb
db = SqliteDb(db_file="agent.db")

# PostgreSQL (production)
from agno.db.postgres import PostgresDb
db = PostgresDb(db_url="postgresql://user:pass@localhost/db")

# Async PostgreSQL
from agno.db.async_postgres import AsyncPostgresDb
db = AsyncPostgresDb(db_url="postgresql+asyncpg://...")

# MySQL
from agno.db.mysql import MySQLDb
db = MySQLDb(db_url="mysql://...")

# MongoDB
from agno.db.mongodb import MongoDb
db = MongoDb(connection_string="mongodb://...")

# Redis
from agno.db.redis import RedisDb
db = RedisDb(url="redis://localhost:6379")

# In-Memory (testing only)
from agno.db.in_memory import InMemoryDb
db = InMemoryDb()
```

### Session Management

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb

agent = Agent(
    db=SqliteDb(db_file="sessions.db"),
    add_history_to_context=True,
    num_history_runs=5  # Include last 5 runs in context
)

# Multi-user, multi-session example
user_1_id = "user_101"
user_2_id = "user_102"
session_1 = "session_101"
session_2 = "session_102"

# User 1, Session 1
agent.run("Hello", user_id=user_1_id, session_id=session_1)
agent.run("What did I say?", user_id=user_1_id, session_id=session_1)

# User 2, Session 2
agent.run("Hi there", user_id=user_2_id, session_id=session_2)
```

### Session Table Schema

| Field | Type | Description |
|-------|------|-------------|
| session_id | str | Unique session identifier |
| session_type | str | Type of session |
| agent_id | str | Agent identifier |
| team_id | str | Team identifier (if applicable) |
| workflow_id | str | Workflow identifier (if applicable) |
| user_id | str | User identifier |
| session_data | dict | Session data |
| agent_data | dict | Agent-specific data |
| metadata | dict | Additional metadata |
| runs | list | List of runs in session |
| summary | dict | Session summary |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

### Session Methods

```python
# Get session messages
messages = agent.get_messages_for_session(session_id="session_123")

# Search session history (requires db)
results = agent.search_session_history(query="topic", limit=10)
```

---

## AgentOS

### Overview

**AgentOS** is a production-ready runtime that provides:
- **FastAPI backend**: Pre-built API for agents, teams, workflows
- **WebSocket support**: Real-time streaming communication
- **Web UI**: Control plane for testing and monitoring
- **Complete privacy**: Runs entirely in your infrastructure

### Basic AgentOS Setup

```python
from agno.agent import Agent
from agno.os import AgentOS
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude
from agno.tools.mcp import MCPTools

# Create agent
agent = Agent(
    name="My Agent",
    model=Claude(id="claude-sonnet-4-5"),
    db=SqliteDb(db_file="agno.db"),
    tools=[MCPTools(transport="streamable-http", url="https://docs.agno.com/mcp")],
    add_history_to_context=True,
    markdown=True
)

# Create AgentOS
agent_os = AgentOS(agents=[agent])

# Get FastAPI app
app = agent_os.get_app()

# Run server
if __name__ == "__main__":
    agent_os.serve(app="app_module:app", reload=True)
```

### AgentOS with Multiple Agents

```python
from agno.os import AgentOS

agent_1 = Agent(name="Research Agent", ...)
agent_2 = Agent(name="Writing Agent", ...)
team = Team(name="Content Team", members=[agent_1, agent_2])
workflow = Workflow(name="Content Pipeline", steps=[...])

agent_os = AgentOS(
    agents=[agent_1, agent_2],
    teams=[team],
    workflows=[workflow]
)

app = agent_os.get_app()
```

### AgentOS Configuration

```python
from agno.os import AgentOS, AgentOSConfig

config = AgentOSConfig(
    host="0.0.0.0",
    port=7777,
    reload=True,
    enable_cors=True,
    cors_origins=["http://localhost:3000"],
    api_key="your-secret-key"  # For security
)

agent_os = AgentOS(
    agents=[agent],
    config=config
)
```

### AgentOS API Endpoints

When running AgentOS, you get automatic endpoints:

```
# Agent endpoints
POST   /v1/agents/{agent_name}/run
GET    /v1/agents/{agent_name}/sessions
GET    /v1/agents/{agent_name}/sessions/{session_id}
WS     /ws/{client_id}  # WebSocket for chat

# Team endpoints
POST   /v1/teams/{team_name}/run
GET    /v1/teams/{team_name}/sessions

# Workflow endpoints
POST   /v1/workflows/{workflow_name}/run
GET    /v1/workflows/{workflow_name}/sessions

# Knowledge endpoints
POST   /v1/knowledge/{kb_name}/add
POST   /v1/knowledge/{kb_name}/search
```

### Connecting to AgentOS UI

1. Run your AgentOS locally
2. Visit https://os.agno.com
3. Connect to your local instance (e.g., `http://localhost:7777`)
4. Interact with agents in real-time

---

## Models

### Supported Model Providers

```python
# OpenAI
from agno.models.openai import OpenAIChat
model = OpenAIChat(id="gpt-4o")
model = OpenAIChat(id="gpt-4o-mini")
model = OpenAIChat(id="o1")

# Anthropic Claude
from agno.models.anthropic import Claude
model = Claude(id="claude-sonnet-4-5")
model = Claude(id="claude-opus-4")

# Google Gemini
from agno.models.google import Gemini
model = Gemini(id="gemini-2.0-flash-exp")

# Groq
from agno.models.groq import Groq
model = Groq(id="llama-3.3-70b-versatile")

# Ollama (local)
from agno.models.ollama import Ollama
model = Ollama(id="llama3.2")

# AWS Bedrock
from agno.models.aws import AWSBedrock
model = AWSBedrock(id="anthropic.claude-v2")

# Azure OpenAI
from agno.models.azure import AzureOpenAI
model = AzureOpenAI(deployment_name="gpt-4")
```

### Model Configuration

```python
model = OpenAIChat(
    id="gpt-4o",
    temperature=0.7,
    max_tokens=2000,
    top_p=0.9,
    frequency_penalty=0.0,
    presence_penalty=0.0
)
```

---

## Complete Examples

### 1. Simple Web Search Agent

```python
from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools

agent = Agent(
    tools=[DuckDuckGoTools()],
    instructions="Search the web and provide concise answers.",
    markdown=True
)

agent.print_response("What's happening in AI today?", stream=True)
```

### 2. Knowledge-Powered RAG Agent

```python
import asyncio
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.db.postgres import PostgresDb

# Setup knowledge base
knowledge = Knowledge(
    name="Product Docs",
    contents_db=PostgresDb(
        db_url="postgresql://localhost/db",
        knowledge_table="knowledge_contents"
    ),
    vector_db=PgVector(
        table_name="vectors",
        db_url="postgresql://localhost/db",
        embedder=OpenAIEmbedder()
    )
)

# Add content
asyncio.run(
    knowledge.add_content_async(
        name="User Manual",
        url="https://example.com/manual.pdf"
    )
)

# Create agent
agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,
    instructions="Answer questions using the knowledge base."
)

agent.print_response("How do I configure the product?", stream=True)
```

### 3. Multi-Agent Team

```python
from agno.team import Team
from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.models.openai import OpenAIChat

researcher = Agent(
    name="Researcher",
    role="Research topics using web search",
    tools=[DuckDuckGoTools()]
)

analyst = Agent(
    name="Analyst",
    role="Analyze research data and provide insights"
)

writer = Agent(
    name="Writer",
    role="Write clear, engaging reports"
)

team = Team(
    name="Research Team",
    members=[researcher, analyst, writer],
    model=OpenAIChat(id="gpt-4o"),
    instructions="Collaborate to create comprehensive research reports."
)

team.print_response("Research the impact of AI on healthcare", stream=True)
```

### 4. Agent with Persistent Sessions

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude

agent = Agent(
    model=Claude(id="claude-sonnet-4-5"),
    db=SqliteDb(db_file="conversations.db"),
    add_history_to_context=True,
    num_history_runs=10,
    markdown=True
)

session_id = "user_session_001"

# First conversation
agent.print_response(
    "My name is Alex and I'm learning Python.",
    session_id=session_id
)

# Continue conversation (same session)
agent.print_response(
    "Can you recommend some Python resources?",
    session_id=session_id
)

# Agent remembers context
agent.print_response(
    "What was my name again?",
    session_id=session_id
)
```

### 5. Production AgentOS with WebSocket

```python
from agno.agent import Agent
from agno.os import AgentOS
from agno.db.postgres import PostgresDb
from agno.models.anthropic import Claude
from agno.tools.duckduckgo import DuckDuckGoTools

# Create production agent
agent = Agent(
    name="Production Agent",
    model=Claude(id="claude-sonnet-4-5"),
    db=PostgresDb(db_url="postgresql://localhost/prod_db"),
    tools=[DuckDuckGoTools()],
    add_history_to_context=True,
    enable_user_memories=True,
    markdown=True
)

# Create AgentOS
agent_os = AgentOS(
    agents=[agent],
    api_key="your-production-api-key"
)

# Get FastAPI app
app = agent_os.get_app()

# Run with production settings
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=7777,
        reload=False,  # Disable in production
        workers=4
    )
```

### 6. Workflow Orchestration

```python
from agno.workflow import Workflow
from agno.agent import Agent
from agno.team import Team

# Define agents
research_agent = Agent(
    name="Researcher",
    instructions="Research the topic thoroughly."
)

analysis_team = Team(
    name="Analysis Team",
    members=[
        Agent(name="Data Analyst", role="Analyze data"),
        Agent(name="Market Analyst", role="Analyze market trends")
    ],
    instructions="Provide comprehensive analysis."
)

writer_agent = Agent(
    name="Writer",
    instructions="Write clear, actionable reports."
)

def review_report(report: str) -> str:
    """Custom review function."""
    return f"Reviewed and approved: {report}"

# Create workflow
workflow = Workflow(
    name="Research to Report Workflow",
    steps=[
        research_agent,
        analysis_team,
        writer_agent,
        review_report
    ]
)

# Run workflow
result = workflow.run("Analyze the renewable energy market")
print(result.content)
```

### 7. Agent with Custom Tools

```python
import httpx
from agno.agent import Agent

def get_stock_price(symbol: str) -> str:
    """Get current stock price.

    Args:
        symbol (str): Stock ticker symbol

    Returns:
        str: Current price information
    """
    response = httpx.get(f"https://api.example.com/stocks/{symbol}")
    data = response.json()
    return f"{symbol}: ${data['price']}"

def calculate_portfolio_value(holdings: dict, session_state: dict) -> str:
    """Calculate total portfolio value.

    Args:
        holdings (dict): Stock holdings
        session_state (dict): Access to session state

    Returns:
        str: Portfolio valuation
    """
    total = sum(holdings.values())
    session_state['portfolio_value'] = total
    return f"Portfolio value: ${total:,.2f}"

agent = Agent(
    tools=[get_stock_price, calculate_portfolio_value],
    session_state={'portfolio_value': 0},
    instructions="Help users track their stock portfolio."
)

agent.print_response("What's the price of AAPL?")
```

---

## Best Practices

### 1. Start Simple

Begin with minimal configuration and add complexity only when needed:

```python
# Start here
agent = Agent(
    model=Claude(id="claude-sonnet-4-5"),
    tools=[DuckDuckGoTools()],
    instructions="Be helpful and concise."
)

# Add features incrementally:
# - Database for sessions
# - Knowledge for RAG
# - Memory for personalization
# - Guardrails for safety
```

### 2. Use Appropriate Storage

```python
# Development: SQLite
db = SqliteDb(db_file="dev.db")

# Production: PostgreSQL
db = PostgresDb(db_url=os.environ["DATABASE_URL"])
```

### 3. Session Management

Always use `session_id` for multi-turn conversations:

```python
agent.run(
    "Continue our discussion",
    user_id=user_id,
    session_id=session_id
)
```

### 4. Error Handling

```python
try:
    response = agent.run("Hello")
    print(response.content)
except Exception as e:
    print(f"Agent error: {e}")
```

### 5. Streaming for Better UX

```python
# Stream for real-time feedback
stream = agent.run("Tell me a story", stream=True)
for chunk in stream:
    if chunk.event == "run_content":
        print(chunk.content, end="", flush=True)
```

### 6. Tool Call Limits

Prevent infinite tool calling loops:

```python
agent = Agent(
    tools=[...],
    tool_call_limit=20  # Max 20 tool calls per run
)
```

### 7. Context Management

Control how much history is included:

```python
agent = Agent(
    db=db,
    add_history_to_context=True,
    num_history_runs=3  # Only last 3 runs
)
```

---

## Quick Reference

### Import Paths

```python
# Core
from agno.agent import Agent
from agno.team import Team
from agno.workflow import Workflow

# Models
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude
from agno.models.google import Gemini
from agno.models.groq import Groq

# Tools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from agno.tools.mcp import MCPTools

# Database
from agno.db.sqlite import SqliteDb
from agno.db.postgres import PostgresDb
from agno.db.in_memory import InMemoryDb

# Knowledge
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector
from agno.vectordb.qdrant import Qdrant
from agno.knowledge.embedder.openai import OpenAIEmbedder

# AgentOS
from agno.os import AgentOS, AgentOSConfig

# Utilities
from agno.utils.pprint import pprint_run_response
```

### Environment Variables

```bash
# Model API Keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."
export GROQ_API_KEY="..."

# Database
export DATABASE_URL="postgresql://user:pass@localhost/db"

# AgentOS
export AGNO_API_KEY="your-secret-key"
```

---

## Resources

- **Documentation**: https://docs.agno.com
- **GitHub**: https://github.com/agno-agi/agno
- **Community**: https://community.agno.com
- **Discord**: https://discord.gg/4MtYHHrgA8
- **Examples**: https://docs.agno.com/examples/introduction
- **Cookbook**: https://github.com/agno-agi/agno/tree/main/cookbook
- **LLM-friendly docs**: https://docs.agno.com/llms.txt

---

**Last Updated**: 2025-10-15
**Agno Version**: 2.0+
