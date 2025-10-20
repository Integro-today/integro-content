# Agent Creation Guide

## Overview

This guide explains how to create and manage agents in the Integro agent lab system using the provided command-line tools.

## Tools

### 1. `create_agent_from_md.py` - Single Agent Creation

Creates a single persona or workflow agent from a .md file and saves it to the database.

**Features:**
- Parses .md files to extract agent prompts
- Generates systematic agent names with version control
- Saves agents directly to database (PostgreSQL or SQLite)
- Optional YAML export for version control
- Auto-version detection

**Usage:**

```bash
# Basic usage - create a persona
python create_agent_from_md.py Agents/personas/Paul_Persona_4.md --type persona

# Create with specific version
python create_agent_from_md.py Agents/personas/Ellen_Persona_4.md --type persona --version 4

# Create with auto-versioning (finds next available version)
python create_agent_from_md.py Agents/personas/Jamie_Persona_1.md --type persona --auto-version

# Create and export to YAML
python create_agent_from_md.py Agents/personas/Paul_Persona_4.md --type persona --export

# Create a workflow agent
python create_agent_from_md.py Agents/intentions_workflow_8.md --type workflow --version 8

# Docker usage
docker exec integro_simulation_backend python create_agent_from_md.py \
  Agents/personas/Sam_Morrison_Suicidal_Crisis_Persona_1.md \
  --type persona --version 1
```

**Arguments:**
- `file` - Path to .md file (required)
- `--type` - Agent type: 'persona' or 'workflow' (required)
- `--version` - Version number (optional, defaults to auto-detect)
- `--auto-version` - Auto-increment version from existing agents
- `--export` - Export config to YAML in configs/agents/

### 2. `batch_import_agents.py` - Bulk Agent Import

Imports multiple agents from a directory in one command.

**Features:**
- Process entire directories at once
- Pattern matching to filter files
- Exclude patterns for templates/archives
- Auto-versioning for all agents
- Bulk YAML export

**Usage:**

```bash
# Import all personas from a directory
python batch_import_agents.py Agents/personas/ --type persona

# Import with pattern matching
python batch_import_agents.py Agents/ --type workflow --pattern "*workflow*.md"

# Import with auto-versioning
python batch_import_agents.py Agents/personas/ --type persona --auto-version

# Import and export all to YAML
python batch_import_agents.py Agents/personas/ --type persona --export

# Exclude templates and archives
python batch_import_agents.py Agents/personas/ --type persona \
  --exclude '*template*' '*archive*' '*BASE*'

# Docker usage
docker exec integro_simulation_backend python batch_import_agents.py \
  Agents/personas/ --type persona
```

**Arguments:**
- `directory` - Directory containing .md files (required)
- `--type` - Agent type: 'persona' or 'workflow' (required)
- `--pattern` - Glob pattern to match files (default: *.md)
- `--auto-version` - Auto-increment versions for all agents
- `--export` - Export all configs to YAML
- `--exclude` - Patterns to exclude (can specify multiple)

## Agent Types

### Persona Agents

**Purpose:** Synthetic user personas for testing therapeutic agents in simulations

**Description Template:**
> "A persona agent used for testing therapeutic conversation agents in simulations. This persona represents a specific user archetype with distinct communication patterns, psychological defense mechanisms, and emotional dynamics."

**Naming Convention:** `{Name} Persona {Version}`
- Examples: `Paul Persona 4`, `Ellen Persona 3`, `Sam Crisis Persona 1`

**Use Cases:**
- Testing agent behavior against different user types
- Regression testing after prompt/workflow changes
- A/B testing across LLM providers
- Benchmarking conversation quality

### Workflow Agents

**Purpose:** Therapeutic agents that guide users through integration processes

**Description Template:**
> "An integration workflow agent that assists users in the Integro psychedelic integration platform. This agent guides users through structured therapeutic processes and integration work."

**Naming Convention:** `{Name} Workflow {Version}`
- Examples: `Intentions Workflow 8`, `Integration Workflow 2`

**Use Cases:**
- Intention-setting before ceremonies
- Integration work after experiences
- Guided therapeutic conversations
- Structured psychedelic preparation

## Naming System

### Systematic Naming Convention

The tools use a systematic naming convention for version control and tracking:

**Pattern:** `{Base Name} {Type} {Version}`

**Examples:**
- `Paul Persona 4` - Paul persona, version 4
- `Intentions Workflow 8` - Intentions workflow, version 8
- `Sam Crisis Persona 1` - Sam Crisis persona, version 1

### Base Name Extraction

The tool automatically extracts the base name from:
1. **First markdown header** (preferred)
   - Example: `# SAM CRISIS PERSONA 1 (v2.1)` → base name: `Sam Crisis`
2. **File name** (fallback)
   - Example: `Sam_Morrison_Suicidal_Crisis_Persona_1.md` → base name: `Sam Morrison Suicidal Crisis`

The tool automatically removes:
- Version markers: `(v2.1)`, `v2.0`, `- v1.5`
- Type suffixes: `Persona 4`, `Workflow 8`
- Standalone type keywords: `Persona`, `Workflow`

### Version Control

**Manual Version:**
```bash
python create_agent_from_md.py file.md --type persona --version 5
```

**Auto-Version (finds next available):**
```bash
python create_agent_from_md.py file.md --type persona --auto-version
```

**Version Detection:**
The tool checks the database for existing agents matching the base name pattern and auto-increments to the next available version.

## Agent Configuration

### Default Settings

All agents are created with these default settings:

```yaml
models:
  - provider: groq
    model_id: moonshotai/kimi-k2-instruct-0905
    params:
      temperature: 0.7

tools: []  # No tools by default

behavior:
  markdown: true
  tool_call_limit: 20
  stream: false
  stream_intermediate_steps: false

memory:
  enable_memory: true
  memory_type: sqlite
  memory_config: {}

storage:
  enable_storage: true
  storage_db_file: sessions.db
  add_history_to_messages: true
  num_history_runs: 5

knowledge:
  knowledge_base_id: null
  search_knowledge: true
  add_references: false

context:
  session_state: {}
  add_state_in_messages: true
  context: {}
  add_context: true

reasoning:
  reasoning: false
  reasoning_model: null

output:
  response_model: null
  use_json_mode: false

metadata:
  version: "1.0"
```

### Customizing Agents

To customize an agent after creation:

1. **Via Web Interface:** Navigate to `http://localhost:8889/agents/{agent_id}`
2. **Via YAML:** Export with `--export` flag, edit YAML, re-import
3. **Via Code:** Modify `AgentConfig` in Python

## File Structure

### Input Files

**.md files** should contain the full agent prompt/instructions:

```markdown
# AGENT NAME PERSONA 1 (v2.1)

Full persona definition...
Instructions...
Voice samples...
etc.
```

### Output Files

**Database Storage:**
- Agents saved to `agents` table in database
- Agent ID: `{base_name}_{type}_{version}` (snake_case)
- Example: `paul_persona_4`, `intentions_workflow_8`

**Optional YAML Export:**
```
configs/agents/
├── paul_persona_4.yaml
├── ellen_persona_3.yaml
├── intentions_workflow_8.yaml
└── ...
```

## Integration with Simulation System

Once created, agents can be used in simulations:

```python
# In test scripts
from integro.config import ConfigStorage, AgentLoader

storage = ConfigStorage()
agent_loader = AgentLoader()

# Load agents
workflow_agent = await storage.load_agent("intentions_workflow_8")
persona_agent = await storage.load_agent("paul_persona_4")

# Use in simulations
from test_two_agent_simulation import TwoAgentSimulation

sim = TwoAgentSimulation(
    storage=storage,
    agent_loader=agent_loader,
    system_agent_id="intentions_workflow_8",
    user_agent_id="paul_persona_4",
    max_turns=20
)

await sim.load_agents()
await sim.run_conversation(initial_prompt="Begin intention-setting.")
```

## Examples

### Example 1: Import All New Personas

```bash
# Import all 12 personas from the personas directory
docker exec integro_simulation_backend python batch_import_agents.py \
  Agents/personas/ \
  --type persona \
  --exclude '*template*' '*BASE*' '*Archive*' \
  --auto-version
```

### Example 2: Create Single Workflow with Export

```bash
# Create workflow agent and export to YAML for version control
docker exec integro_simulation_backend python create_agent_from_md.py \
  Agents/intentions_workflow_8.md \
  --type workflow \
  --version 8 \
  --export
```

### Example 3: Update Existing Persona

```bash
# Create new version of existing persona
docker exec integro_simulation_backend python create_agent_from_md.py \
  Agents/personas/Paul_Persona_5.md \
  --type persona \
  --version 5
```

## Troubleshooting

### Issue: "Module not found: agno"

**Solution:** Run commands inside Docker where dependencies are installed:
```bash
docker exec integro_simulation_backend python create_agent_from_md.py ...
```

### Issue: Duplicate agent names

**Solution:** Use `--auto-version` to automatically find the next available version:
```bash
python create_agent_from_md.py file.md --type persona --auto-version
```

### Issue: Wrong base name extracted

**Solution:** Add a clear first-level header to your .md file:
```markdown
# DESIRED BASE NAME PERSONA 1

Rest of content...
```

### Issue: Agent not appearing in web interface

**Solution:**
1. Check that agent was saved successfully (look for success message)
2. Refresh the web interface at `http://localhost:8889/agents`
3. Check database: `docker exec integro_simulation_backend python -c "from integro.config import ConfigStorage; import asyncio; asyncio.run(ConfigStorage().list_agents())"`

## Database Schema

Agents are stored in the `agents` table:

```sql
CREATE TABLE agents (
    id VARCHAR(255) PRIMARY KEY,           -- Snake-case agent ID
    name VARCHAR(255) NOT NULL,            -- Display name
    description TEXT,                       -- Agent description
    config JSONB NOT NULL,                 -- Full AgentConfig as JSON
    knowledge_base_id VARCHAR(255),        -- Optional KB reference
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
)
```

## Best Practices

1. **Use systematic naming:** Always follow the `{Name} {Type} {Version}` pattern
2. **Version control:** Increment versions when making significant changes
3. **Export important agents:** Use `--export` to save YAML copies for git versioning
4. **Test before production:** Test new agents in simulations before using in production
5. **Document changes:** Update your .md files with version notes and changes
6. **Batch operations:** Use `batch_import_agents.py` for bulk operations
7. **Auto-version for safety:** Use `--auto-version` to avoid overwriting existing agents

## Advanced Usage

### Programmatic Agent Creation

```python
import asyncio
from create_agent_from_md import create_agent_from_md
from pathlib import Path

async def main():
    agent_id = await create_agent_from_md(
        file_path=Path("Agents/personas/CustomPersona.md"),
        agent_type="persona",
        version=1,
        export_yaml=True,
        auto_version=False
    )
    print(f"Created agent: {agent_id}")

asyncio.run(main())
```

### Custom Agent Config

```python
from integro.config import ConfigStorage, AgentConfig

async def create_custom_agent():
    storage = ConfigStorage()

    config = AgentConfig(
        name="Custom Agent 1",
        description="A custom agent",
        instructions=["Instruction 1", "Instruction 2"],
        models=[{
            "provider": "groq",
            "model_id": "moonshotai/kimi-k2-instruct-0905",
            "params": {"temperature": 0.7}
        }],
        # ... other settings
    )

    agent_id = await storage.save_agent(config)
    return agent_id
```

## Related Documentation

- [Agno Framework Documentation](agno_mapping.md)
- [Persona System Documentation](Agents/personas/PERSONA_REFERENCE_GUIDE.md)
- [Simulation Testing Guide](test_mixed_persona_batch.py)
- [Project Overview](.claude/CLAUDE.md)

## Support

For issues or questions:
- Check the troubleshooting section above
- Review the project documentation in `.claude/CLAUDE.md`
- Examine the example usage in this guide
- Look at existing agents in `configs/agents/` for reference
