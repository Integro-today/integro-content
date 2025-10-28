# Integro Content - Agent Simulation & Testing Platform

## Mission

Convert structured DOCX/PDF curriculum content into machine-readable JSON and build a production-ready agent simulation system for testing therapeutic conversation agents against realistic user personas.

Part of the broader Integro ecosystem:
- **integro-api**: Backend services
- **integro-web**: Frontend application
- **integro-content**: Content management + agent simulation lab (this project)

---

## Content Assets

**54-Week Psychedelic Integration Curriculum**
- 3 Expeditions (Healing Self, Connection to Other, Connection to Awe)
- 18 weeks per expedition
- ~324-378 days of therapeutic content
- 1,000+ pages of educational material
- 100+ therapeutic tools and exercises
- Designed for transformative learning and psychedelic integration

**Structure**: Weekly DOCX/PDF files with 6-7 days each containing daily passages, activities, tools, and academic sources. Schema defined in `/schemas/weekly-content-schema.json`.

---

## Agent Simulation System (Production-Ready)

### Overview

A **high-performance testing framework** for evaluating therapeutic agents through realistic multi-turn conversations with synthetic user personas.

**Key Capabilities:**
- Pre-deployment validation and A/B testing
- Regression testing for prompt changes
- Performance benchmarking across LLM providers
- Persona coverage testing (different user types)
- Automated dual-format output (JSON + Markdown)

### Quick Start

```bash
# 1. Build and start services
make docker-build && make docker-up

# 2. Run single simulation test
docker exec integro_simulation_backend python test_two_agent_simulation.py \
    --workflow-id roots_of_healing_-_day_1_workflow_1 \
    --persona-id ellen_persona_4 \
    --max-rounds 20 \
    --output Agents/test_simulations/roots_ellen_test.json

# 3. Or run full batch test (all 13 personas)
docker exec integro_simulation_backend python test_roots_healing_batch.py

# 4. Start simulation viewer
docker exec -d integro_simulation_backend python simulation_viewer.py
# Then visit http://localhost:8890
```

**For complete command reference, use Read tool on:** `/home/ben/integro-content/.claude/quick-reference.md`

---

## Current Agents

### Workflow Agents (Latest: V9/V12)

- **Intentions Workflow 8** - Pre-journey intention-setting (Tegra voice)
- **Roots of Healing Workflow 1-11** - Day 1 curriculum iterations (Groq)
- **Roots of Healing Workflow 12 (V9)** - Latest: Improved grammar, workflow-first order, DeepInfra Kimi K2, verbatim curriculum content, knowledge base integration (5,390 chunks from Maté, Ross, Jung)

### Persona Agents (13 Total)

**Original Benchmark Personas (3):**
- **Paul** - Military veteran, terse/defensive → Tests trust-building through resistance
- **Ellen** - Tech entrepreneur, verbose/analytical → Tests dropping from head to heart
- **Jamie** - ADHD creative, scattered/enthusiastic → Tests providing structure

**New Diverse Personas (10):**
- Tommy (Confused Instruction Follower), Valentina (Drama Queen), Sam (Suicidal Crisis)
- Diego (Tangent Master), Dr. Rebecca (Know-It-All), Aisha (Integration Expert)
- Kyle (Drug-Focused), Bobby (Prejudiced), Chloe (Manipulative), Jack (Violence Risk)

**Diversity:** 13 personas covering diverse demographics, communication styles, and therapeutic challenges

**For complete persona documentation, use Read tool on:** `/home/ben/integro-content/.claude/personas.md`

---

## Documentation

### ⚠️ IMPORTANT: How to Use This Documentation

**This CLAUDE.md file is a high-level overview only.** Detailed information has been extracted into specialized documentation files.

**When you need detailed information, you MUST use the Read tool to look up the relevant documentation file.** Do NOT assume you know the contents - always read the file first.

### Core Documentation Files

**INSTRUCTIONS: Use Read tool with these exact paths when you need detailed information.**

#### 1. quick-reference.md
**Path:** `/home/ben/integro-content/.claude/quick-reference.md`

**Use when:** User asks for commands, workflows, or how to do something

**Contains:**
- Quick start guide (build, test, view simulations)
- Common Docker, database, and Qdrant commands
- Simulation workflows (single and batch)
- Agent creation commands
- Evaluation commands
- File locations and service ports
- Troubleshooting section
- Environment variables

**Example triggers:**
- "How do I run a simulation?"
- "What's the command to start the viewer?"
- "How do I create an agent?"

---

#### 2. personas.md
**Path:** `/home/ben/integro-content/.claude/personas.md`

**Use when:** User asks about personas, synthetic users, or testing scenarios

**Contains:**
- Complete list of all 13 production personas with profiles
- Persona system architecture (v2.1)
- Diversity coverage statistics
- Quality metrics and benchmarks
- Step-by-step persona creation guide
- Persona generator lessons learned (2025-10-16)
- Reference guide information

**Example triggers:**
- "Tell me about the personas"
- "What personas are available?"
- "How do I create a new persona?"
- "What's the diversity coverage?"

---

#### 3. simulation-tools.md
**Path:** `/home/ben/integro-content/.claude/simulation-tools.md`

**Use when:** User asks about running tests, simulations, or testing tools

**Contains:**
- test_two_agent_simulation.py documentation
- test_roots_healing_batch.py documentation
- test_mixed_persona_batch.py documentation
- test_async_batch_simulations.py documentation
- RateLimiter class details
- simulation_viewer.py usage
- create_agent_from_md.py documentation
- Performance metrics and benchmarks
- Output structure and formats

**Example triggers:**
- "How do I run a batch test?"
- "What testing tools are available?"
- "How fast are the simulations?"
- "How do I use the simulation viewer?"

---

#### 4. evaluation.md
**Path:** `/home/ben/integro-content/.claude/evaluation.md`

**Use when:** User asks about evaluating simulations, quality assessment, or Training-Free GRPO

**Contains:**
- simulation-evaluator subagent documentation
- evaluate_simulation.py complete usage guide
- Evaluation dimensions (5 scoring categories)
- Example output structures
- Recommendation thresholds
- Training-Free GRPO workflow integration
- Agent caching instructions
- When to use each evaluation tool

**Example triggers:**
- "How do I evaluate a simulation?"
- "Tell me about the evaluation tools"
- "What is Training-Free GRPO?"
- "How do I check simulation quality?"

---

#### 5. knowledge-base.md
**Path:** `/home/ben/integro-content/.claude/knowledge-base.md`

**Use when:** User asks about knowledge bases, RAG, embeddings, or Qdrant

**Contains:**
- Knowledge base creation process (7 steps)
- Agno RAG integration architecture
- Configuration requirements (QDRANT_URL, .env)
- Current knowledge bases (5,390 documents)
- Supported document formats (PDF, DOCX, EPUB, etc.)
- Testing knowledge search
- Qdrant UI access
- Database schema
- Troubleshooting guide
- Best practices

**Example triggers:**
- "How do I create a knowledge base?"
- "Tell me about RAG integration"
- "How do I add documents to an agent?"
- "What knowledge bases exist?"

---

### Additional Documentation

**Also in project root - use Read tool when referenced:**

- **SIMULATION_EVALUATION_TOOL.md** - Detailed evaluation tool documentation
- **Training_Free_GRPO_summarization.md** - Training-Free GRPO methodology
- **python-docx_mapping.md** - API reference for parsing DOCX

---

## Infrastructure

### Docker Stack

**Services:**
- `integro_simulation_backend` - FastAPI + agent system
- `integro_simulation_frontend` - Next.js UI
- `integro_simulation_db` - PostgreSQL (agent configs)
- `integro_simulation_qdrant` - Vector DB (embeddings)
- `integro_simulation_voice_agent` - LiveKit voice support

**Ports:**
- Backend: http://localhost:8888
- Frontend: http://localhost:8889
- Qdrant: http://localhost:6333
- Simulation Viewer: http://localhost:8890

### Database Schema

```sql
agents (id, name, description, config, knowledge_base_id, created_at, updated_at)
knowledge_bases (id, name, description, collection_name, config, created_at, updated_at)
kb_documents (id, kb_id, doc_id, file_path, content, metadata, embedding, created_at)
```

---

## File Structure

```
integro-content/
├── .claude/
│   ├── CLAUDE.md                       # This file (overview only - READ other docs for details)
│   ├── quick-reference.md              # Common commands (READ when user asks how to do things)
│   ├── personas.md                     # Persona system docs (READ for persona details)
│   ├── simulation-tools.md             # Testing tools docs (READ for test commands)
│   ├── evaluation.md                   # Evaluation tools docs (READ for evaluation info)
│   └── knowledge-base.md               # KB and RAG docs (READ for KB/RAG questions)
├── Agents/
│   ├── batch_simulations/              # Batch test outputs (JSON + MD)
│   ├── test_simulations/               # Single test outputs
│   ├── personas/                       # Persona definitions (13 total)
│   ├── knowledge/                      # Knowledge base documents
│   ├── roots_of_healing_workflow_*.md  # Workflow definitions (V1-V3)
│   ├── intentions_workflow_8.md        # Pre-journey workflow
│   └── tegra_voice.md                  # Tegra voice guidelines
├── integro/                            # Main Python package
│   ├── agent/                          # Agent core logic
│   ├── config/storage.py               # Database abstraction
│   ├── memory/agno_knowledge.py        # RAG integration
│   └── web_server.py                   # FastAPI application
├── frontend/                           # Next.js UI
├── test_two_agent_simulation.py        # Single simulation with CLI
├── test_roots_healing_batch.py         # Batch test all personas
├── evaluate_simulation.py              # Workflow evaluation tool
├── simulation_viewer.py                # Web-based viewer (port 8890)
├── create_agent_from_md.py             # Agent creation with KB support
├── docker-compose.yaml                 # Local dev stack
├── pyproject.toml                      # Python dependencies
└── Makefile                            # Dev commands
```

---

## Performance Metrics

**Simulation Speed:**
- Single simulation: ~60s
- Async batch (5 concurrent): ~11.4s per simulation (5.3x speedup)
- Mixed batch (20 concurrent): ~3.9s per simulation (15.4x speedup)

**Quality:**
- 100% completion rate across 100+ simulations
- All conversations reach 40 messages (20 rounds)
- Authentic persona behavior maintained throughout

**Knowledge Base:**
- 5,390 documents from 4 therapeutic books
- External Qdrant instance for persistent embeddings
- Agno RAG integration fully verified and working

---

## Next Steps

**Simulation System:**
- [ ] Database integration (store runs in simulation_runs table)
- [ ] Automated LLM-based quality scoring
- [ ] Comparison dashboard for side-by-side analysis
- [ ] CI/CD integration for automated testing

**Content Parsing:**
- [ ] Build PDF→JSON parser
- [ ] Process all 54 weeks
- [ ] Validate against schema
- [ ] Integrate with agent workflows

**Daily Curriculum:**
- [x] Week 1 Day 1 workflows (V1-V3)
- [x] Knowledge base integration (5,390 chunks)
- [x] Batch testing with all 13 personas
- [ ] Create workflows for remaining 377 days
- [ ] Build workflow templates for different activity types

**Persona Development:**
- [x] 13 production personas covering diverse demographics
- [x] v2.1 template with psychological depth
- [ ] Validate all personas in additional simulation scenarios
- [ ] Cross-persona comparison testing

---

## Status

**Repository**: https://github.com/Integro-today/integro-content

**Last Updated**: 2025-10-23

**Status**: Production simulation system with 500+ successful test runs. Latest: Workflow V9/V12 (DeepInfra Kimi K2) tested across all 13 personas with 100% success rate.

**Workflow System**: Roots of Healing V12 with improved grammar, workflow-first conversation order, verbatim curriculum content, and integrated knowledge base (5,390 chunks)

**Persona System**: 13 production personas covering diverse demographics and therapeutic challenges

**Knowledge Base Infrastructure**: ✅ Dual-storage architecture (PostgreSQL + Qdrant) with intelligent reuse - automatically detects and reuses existing KBs with matching documents

**Model Support**: Groq (Kimi K2 Instruct) and DeepInfra (moonshotai/Kimi-K2-Instruct-0905)

**Simulation Viewer**: Web-based viewer on port 8890, outputs in `Agents/simulations/batch_simulations/`

**Recent Improvements (2025-10-23)**:
- Knowledge base creation now properly populates both PostgreSQL (frontend display) and Qdrant (agent search)
- Knowledge base reuse prevents duplicate uploads when using same source documents
- DeepInfra provider support added to ModelConfig
- Workflow-first conversation order (workflow greets user, persona responds)
- Batch simulation system supports 4 concurrent executions
