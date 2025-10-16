# Agent-to-Agent Simulation System

## Overview

This simulation system enables **systematic testing and evaluation** of agent configurations by having two agents converse with each other. This is valuable for:

- **Pre-deployment validation**: Test agents before production
- **A/B testing**: Compare different prompt configurations
- **Regression testing**: Ensure changes don't break existing behavior
- **Safety verification**: Detect inappropriate responses
- **Performance metrics**: Quantify agent quality

## Architecture

### Key Components

1. **ConfigStorage** (`integro/config/storage.py`)
   - Unified database abstraction (SQLite/PostgreSQL)
   - CRUD operations for agents and knowledge bases
   - Methods: `load_agent()`, `save_agent()`, `list_agents()`

2. **AgentLoader** (`integro/config/agent_loader.py`)
   - Creates agent instances from configurations
   - Method: `create_agent(config, knowledge_base=None)`

3. **IntegroAgent** (`integro/agent/`)
   - Core agent implementation
   - Method: `arun(message, session_id, stream=False)` - async agent execution

4. **TwoAgentSimulation** (`test_two_agent_simulation.py`)
   - Orchestrates conversation between two agents
   - Manages turn-taking and message recording
   - Saves conversations in standardized JSON format

### How It Works

```
┌─────────────────────────────────────────────────────────┐
│                    Simulation Flow                       │
└─────────────────────────────────────────────────────────┘

1. Load Agents from Database
   ├─ ConfigStorage.load_agent(system_agent_id)
   └─ ConfigStorage.load_agent(user_agent_id)

2. Create Agent Instances
   ├─ AgentLoader.create_agent(config)
   └─ agent.initialize()

3. Run Conversation Loop (15 rounds = 30 messages)
   ├─ System Agent: response = await system_agent.arun(message)
   ├─ Store: messages['system0'] = response.content
   ├─ User Agent: response = await user_agent.arun(last_system_msg)
   ├─ Store: messages['user0'] = response.content
   └─ Repeat for turns 1-14...

4. Save to JSON
   └─ Save with agent references (not full configs)
```

## Database Schema

The simulation system leverages existing database tables:

```sql
-- Agents table (from ConfigStorage)
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    config TEXT NOT NULL,  -- JSON serialized AgentConfig
    knowledge_base_id TEXT,
    created_at TEXT,
    updated_at TEXT
);

-- Knowledge bases table (optional)
CREATE TABLE knowledge_bases (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    collection_name TEXT,
    config TEXT NOT NULL,
    created_at TEXT,
    updated_at TEXT
);
```

## How Agent Lab Uses Agno

Based on analysis of `integro/web_server.py`:

### 1. Agent Loading (`load_agent_for_client`)

```python
# Load from database
agent_config = await storage.load_agent(agent_id)
kb_config = await storage.load_knowledge_base(kb_id)

# Create agent instance
agent = agent_loader.create_agent(agent_config, knowledge_base=kb)
await agent.initialize()

# Store for client
manager.set_agent(client_id, agent)
```

### 2. Message Handling (WebSocket `/ws/{client_id}`)

```python
# Receive message
data = await websocket.receive_json()
message = data.get("message")

# Run agent
session_id = manager.get_session(client_id)
response = await agent.arun(
    message=message,
    session_id=session_id,
    stream=False
)

# Send response
content = response.content if hasattr(response, 'content') else str(response)
await manager.send_message(client_id, {
    "type": "chat_response",
    "content": content
})
```

### 3. Session Management

```python
# Each client gets a unique session
session_id = manager.get_session(client_id)  # Returns ISO timestamp

# Agent uses session for conversation history
# (if agent configured with add_history_to_context=True)
response = await agent.arun(
    message=message,
    session_id=session_id,  # Tracks conversation across turns
    stream=False
)
```

### 4. Knowledge Base Integration

```python
# Load KB documents from database
documents = await storage.load_kb_documents(kb_id)

# Create in-memory Qdrant instance
kb = KnowledgeBase(
    collection_name=kb_config.collection_name,
    in_memory=True,
    embedding_model=kb_config.embedding_model
)

# Reconstruct embeddings and upsert to Qdrant
for doc in documents:
    embedding = reconstruct_from_bytes(doc['embedding'])
    kb.client.upsert(
        collection_name=kb.collection_name,
        points=[PointStruct(id=doc_id, vector=embedding, payload=content)]
    )

# Agent uses KB for RAG
agent = agent_loader.create_agent(agent_config, knowledge_base=kb)
```

## Output Format

Simulations produce JSON files matching this structure:

```json
{
  "session": "sim_20251015_120000",
  "datetime": "2025-10-15T12:00:00.000000",
  "notes": "Test simulation between two agents",
  "system_agent_id": "paul_persona_3",
  "user_agent_id": "intentions_workflow_2",
  "max_turns": 15,
  "system0": "Hello! I'd like to explore...",
  "user0": "That's a great question...",
  "system1": "I appreciate your perspective...",
  "user1": "Building on what you said...",
  ...
  "system14": "",
  "user14": ""
}
```

**Key Design Decision**: We store **agent IDs** (`system_agent_id`, `user_agent_id`) rather than full agent configurations. This:
- Keeps files lightweight
- Maintains single source of truth (database)
- Allows agents to be updated without invalidating simulations
- Makes it easy to re-run simulations with updated agent configs

## Usage

### Running a Simulation

```bash
# Run the test script
python test_two_agent_simulation.py
```

The script will:
1. List all available agents in the database
2. Try to find "Paul Persona 3" and "Intentions Workflow 2"
3. Fallback to first two agents if not found
4. Run 15-round conversation (30 messages)
5. Save to `output/simulations/simulation_YYYYMMDD_HHMMSS.json`

### Output Location

```
output/simulations/
└── simulation_20251015_143022.json
```

## Integration with Agno Framework

The simulation system uses Agno concepts as documented in `agno_mapping.md`:

### Agent Execution
```python
# Agno pattern (from agno_mapping.md)
response: RunOutput = agent.run("message", session_id="session_123")

# Integro implementation (async variant)
response = await agent.arun(
    message="message",
    session_id="session_123",
    stream=False
)
```

### Session Management
```python
# Agno concept: Sessions track multi-turn conversations
# Each simulation creates unique session IDs for both agents:
system_session_id = f"{session_id}_system"
user_session_id = f"{session_id}_user"

# Agents maintain separate conversation histories
```

### Storage
```python
# Agno concept: Storage persists sessions and state
# Integro uses ConfigStorage for agent configs:
agent_config = await storage.load_agent(agent_id)

# And IntegroAgent handles session storage internally
# (if configured with enable_storage=True)
```

## Next Steps

To build on this foundation:

1. **Create SimulationRunner class** (`integro/simulations/runner.py`)
   - Generalize the conversation logic
   - Add configurable termination conditions
   - Support goal detection callbacks

2. **Create SimulationStorage** (`integro/simulations/storage.py`)
   - Add `simulation_runs` table to database
   - Track metrics and metadata
   - Enable querying past simulations

3. **Add Evaluation Metrics**
   - Response quality scoring
   - Safety checks
   - Goal completion detection
   - Efficiency metrics (turns to resolution)

4. **Build Evaluation Framework**
   - LLM-as-judge for quality assessment
   - Automated safety screening
   - Statistical analysis across runs

5. **UI Integration**
   - Add simulation UI to agent lab
   - Real-time monitoring
   - Comparison views
   - Export capabilities

## Example Use Cases

### 1. Prompt Engineering
```python
# Create 10 variants of an agent with different prompts
for i in range(10):
    variant_agent = create_agent_variant(base_config, variant=i)
    await storage.save_agent(variant_agent)

    # Run simulation
    sim = TwoAgentSimulation(
        system_agent_id=variant_agent.id,
        user_agent_id="standard_test_agent"
    )
    await sim.run_conversation()

    # Evaluate
    score = evaluate_conversation(sim.messages)
    results[i] = score

# Keep the best performing variant
best = max(results, key=results.get)
```

### 2. Safety Testing
```python
# Test agent with adversarial inputs
sim = TwoAgentSimulation(
    system_agent_id="agent_under_test",
    user_agent_id="adversarial_agent"  # Tries to elicit bad behavior
)

await sim.run_conversation()

# Check for inappropriate responses
for msg in sim.messages.values():
    if contains_unsafe_content(msg):
        flag_for_review(sim.session_id, msg)
```

### 3. A/B Testing
```python
# Compare two versions of an agent
results_a = []
results_b = []

for i in range(100):
    # Test version A
    sim_a = TwoAgentSimulation("agent_v1", "test_user")
    await sim_a.run_conversation()
    results_a.append(evaluate(sim_a.messages))

    # Test version B
    sim_b = TwoAgentSimulation("agent_v2", "test_user")
    await sim_b.run_conversation()
    results_b.append(evaluate(sim_b.messages))

# Statistical comparison
p_value = ttest(results_a, results_b)
```

## Technical Details

### Message Flow

```
Turn 0:
  System Agent → "Hello, let's talk about X"
  └─ Stored as: messages['system0']

  User Agent receives system0
  User Agent → "That's interesting because..."
  └─ Stored as: messages['user0']

Turn 1:
  System Agent receives user0
  System Agent → "Building on that idea..."
  └─ Stored as: messages['system1']

  User Agent receives system1
  User Agent → "Yes, and furthermore..."
  └─ Stored as: messages['user1']

... continues for 15 rounds
```

### Session Isolation

Each agent maintains its own session:
- System agent: `{session_id}_system`
- User agent: `{session_id}_user`

This prevents conversation history bleeding between agents while allowing each to maintain context from their own perspective.

### Error Handling

The test script includes error handling for:
- Missing agents in database
- Agent initialization failures
- Conversation errors
- File I/O errors

## Files

- `test_two_agent_simulation.py` - Main test script
- `Agents/simulation_template.json` - Old format template (full configs)
- `Agents/simulation_output_template.json` - New format template (agent references)
- `SIMULATION_README.md` - This file
- `agno_mapping.md` - Comprehensive Agno framework documentation

## References

- **Agno Documentation**: https://docs.agno.com
- **Agent Lab Source**: `integro/web_server.py`
- **Storage Layer**: `integro/config/storage.py`
- **Agent Implementation**: `integro/agent/`
- **Agno Mapping**: `agno_mapping.md`
