# Simulation Tools Documentation

## Overview

Production-ready testing framework for evaluating therapeutic agents through realistic multi-turn conversations with synthetic user personas.

**Key Capabilities:**
- Pre-deployment validation and A/B testing
- Regression testing for prompt changes
- Performance benchmarking across LLM providers
- Persona coverage testing (different user types)
- Automated dual-format output (JSON + Markdown)

---

## Test Scripts

### test_two_agent_simulation.py

**Purpose:** Single simulation with CLI arguments

**Features:**
- Test specific workflow vs specific persona
- Command-line arguments: `--workflow-id`, `--persona-id`, `--max-rounds`, `--output`
- Persona initiates conversation (daily curriculum flow)
- Auto-generates JSON + Markdown
- ~60s per simulation

**Usage:**

```bash
# Test specific workflow vs specific persona
docker exec integro_simulation_backend python test_two_agent_simulation.py \
    --workflow-id roots_of_healing_-_day_1_workflow_1 \
    --persona-id ellen_persona_4 \
    --max-rounds 20 \
    --output Agents/test_simulations/roots_ellen_test.json

# Quick test with different persona
docker exec integro_simulation_backend python test_two_agent_simulation.py \
    --workflow-id intentions_workflow_8 \
    --persona-id paul_persona_4 \
    --max-rounds 20 \
    --output Agents/test_simulations/intentions_paul_test.json
```

**Conversation Flow (Daily Curriculum):**
1. Persona initiates conversation (requests daily content)
2. Workflow responds with grounding/consent
3. Interactive path (reflection questions) OR reading path (full passage)
4. Artifact creation (YAML to dashboard)
5. Closing

---

### test_roots_healing_batch.py

**Purpose:** Daily curriculum batch testing

**Features:**
- Tests Roots of Healing Workflow against all 13 personas
- Built-in RateLimiter for Groq API (250K TPM management)
- Auto-generates JSON + Markdown for every simulation
- 5 concurrent simulations, ~15-20 minutes total

**Usage:**

```bash
# Test Roots of Healing against all 13 personas
docker exec integro_simulation_backend python test_roots_healing_batch.py
```

**Output Structure:**
```
Agents/batch_simulations/roots_healing_all_personas_YYYYMMDD_HHMMSS/
├── paul_persona_4_simulation_01.json + .md
├── ellen_persona_4_simulation_01.json + .md
├── jamie_adhd_persona_2_simulation_01.json + .md
├── tommy_confused_instruction_follower_persona_1_simulation_01.json + .md
├── valentina_drama_queen_persona_1_simulation_01.json + .md
├── sam_crisis_persona_1_simulation_01.json + .md
├── diego_tangent_master_persona_1_simulation_01.json + .md
├── dr._rebecca_goldstein_know-it-all_persona_1_simulation_01.json + .md
├── aisha_integration_expert_persona_1_simulation_01.json + .md
├── kyle_drug-focused_persona_1_simulation_01.json + .md
├── bobby_prejudiced_persona_1_simulation_01.json + .md
├── chloe_manipulative_persona_1_simulation_01.json + .md
└── jack_violence_risk_persona_1_simulation_01.json + .md
```

---

### test_mixed_persona_batch.py

**Purpose:** Legacy batch testing tool

**Features:**
- Tests intentions workflow against multiple personas simultaneously
- Built-in RateLimiter for Groq API (250K TPM management)
- Auto-generates JSON + Markdown for every simulation
- Configurable concurrency and batch size

**Usage:**

```bash
# Test intentions workflow (legacy)
docker exec integro_simulation_backend python test_mixed_persona_batch.py
```

---

### test_async_batch_simulations.py

**Purpose:** Parallel async batch testing

**Features:**
- Parallel execution for maximum performance
- ~8-12s per simulation (5x faster than sequential)
- Supports 5-20 concurrent simulations
- Same output format as other batch scripts

---

## Support Tools

### convert_simulation_to_markdown.py

**Purpose:** Human-readable conversion

**Features:**
- Converts JSON simulations to clean Markdown
- Replaces `system`/`user` with actual agent names
- Preserves all punctuation, line breaks, and message flow
- Auto-invoked during batch runs (no manual conversion needed)

**Usage:**

```bash
# Manual conversion (usually not needed)
docker exec integro_simulation_backend python convert_simulation_to_markdown.py <simulation.json>
```

---

### RateLimiter Class

**Purpose:** API rate management

**Features:**
- Tracks token usage across concurrent simulations
- Automatic wait when approaching TPM limits
- 85% safety margin on published limits
- Prevents all rate limit errors

**Configuration:**
- Model: `moonshotai/kimi-k2-instruct-0905`
- TPM Limit: 250,000 (uses 85% = 212,500 for safety)
- Automatic pause/resume when approaching limits
- Zero rate limit errors in production

---

### simulation_viewer.py

**Purpose:** Web-based simulation viewer (Port 8890)

**Features:**
- **Interactive viewer** for browsing simulation conversations
- Runs on http://localhost:8890
- **Multi-directory scanning:** Automatically scans `Agents/simulations/`, `Agents/batch_simulations/`, and `Agents/test_simulations/`
- **Dropdown selector:** Choose from 470+ simulations
- **Sort options:** Path (A-Z) or Most Recent (newest first)
- **Metadata display:** Session ID, agents, message count, timestamp
- **Chat interface:** Color-coded messages (blue=workflow, green=persona)
- **Responsive design:** Works on mobile and desktop

**Usage:**

```bash
# Start viewer (scans all simulation directories by default)
docker exec -d integro_simulation_backend python simulation_viewer.py

# View specific directory
docker exec -d integro_simulation_backend python simulation_viewer.py Agents/test_simulations/

# View specific file
docker exec -d integro_simulation_backend python simulation_viewer.py path/to/simulation.json
```

**Access:** http://localhost:8890

**Tips:**
- Select "Most Recent" to see latest simulations first
- Use dropdown to browse through 470+ available simulations

---

### create_agent_from_md.py

**Purpose:** Agent creation from markdown with knowledge base support

**Features:**
- Creates workflow or persona agents from markdown files
- **NEW:** Can attach knowledge bases during agent creation
- Stores in PostgreSQL database
- Supports multiple document formats: PDF, DOCX, EPUB, TXT, MD, XLSX, PPTX
- Auto-creates Qdrant collections with embeddings

**Usage:**

```bash
# Basic agent creation
docker exec integro_simulation_backend python create_agent_from_md.py <file.md> --type [workflow|persona]

# With knowledge base (single document)
docker exec integro_simulation_backend python create_agent_from_md.py <file.md> --type workflow \
    --knowledge path/to/document.pdf

# With multiple knowledge documents
docker exec integro_simulation_backend python create_agent_from_md.py <file.md> --type workflow \
    --knowledge doc1.pdf --knowledge doc2.docx --knowledge doc3.epub

# With custom knowledge base name
docker exec integro_simulation_backend python create_agent_from_md.py <file.md> --type workflow \
    --kb-name "Custom KB Name" --knowledge documents/*.pdf
```

**See Also:** [knowledge-base.md](./knowledge-base.md) for knowledge base creation details

---

## Performance Metrics

### Latest Results (2025-10-16)

| Configuration | Simulations | Time | Avg/Sim | Speedup |
|--------------|-------------|------|---------|---------|
| Sequential | 10 | ~10 min | 60s | 1x baseline |
| Async (5 concurrent) | 10 | 114s | 11.4s | 5.3x |
| Mixed (10 concurrent) | 20 | 116s | 5.8s | 10.3x |
| Mixed (20 concurrent) | 20 | 78s | 3.9s | 15.4x |

### Quality Metrics

- ✅ 100% completion rate across 100+ simulations
- ✅ All conversations reach 40 messages (20 rounds)
- ✅ Authentic persona behavior maintained throughout
- ✅ Natural therapeutic conversation flow

### File Size Patterns

- **Paul (terse):** 4-15 KB per conversation
- **Ellen (verbose):** 7-20 KB per conversation

---

## Auto-Format Generation

Every simulation automatically creates dual formats:

- **JSON** - Machine-readable (APIs, analysis, storage)
- **Markdown** - Human-readable (review, evaluation, sharing)

No manual conversion needed - both formats generated during batch runs.

---

## Integration with Agent Lab

Uses production infrastructure:
- Same database (ConfigStorage via PostgreSQL)
- Same agent loader (AgentLoader)
- Same Agno API (`agent.arun()`)
- Docker environment: `integro_simulation_backend` container

---

## Architecture

### Core Components

- **`TwoAgentSimulation` class** - Manages agent-to-agent conversations
- **`RateLimiter` class** - Groq API rate management (250K TPM limit)
- **Auto-conversion** - Markdown generation for human readability
- **PostgreSQL** - Agent storage
- **Qdrant** - Vector DB for embeddings
- **FastAPI backend** + **Next.js frontend**

### Docker Services

- `integro_simulation_backend` - FastAPI + agent system
- `integro_simulation_frontend` - Next.js UI
- `integro_simulation_db` - PostgreSQL (agent configs)
- `integro_simulation_qdrant` - Vector DB (embeddings)
- `integro_simulation_voice_agent` - LiveKit voice support

---

## Development Commands

**Makefile:**

```bash
make install          # Install dependencies with uv
make docker-build     # Build containers (auto-generates requirements.txt)
make docker-up        # Start all services
make docker-logs      # View container logs
make test-simulation  # Run single simulation test
```

---

**Last Updated:** 2025-10-23
