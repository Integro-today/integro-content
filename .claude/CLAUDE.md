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

### Architecture

**Core Components:**
- `TwoAgentSimulation` class - Manages agent-to-agent conversations
- `RateLimiter` class - Groq API rate management (250K TPM limit)
- Auto-conversion to Markdown for human readability
- PostgreSQL agent storage + Qdrant vector DB
- FastAPI backend + Next.js frontend

**Test Scripts:**

| Script | Purpose | Performance | Output |
|--------|---------|-------------|--------|
| `test_two_agent_simulation.py` | Single simulation (debug) | ~60s | 1 conversation |
| `test_batch_simulations.py` | Sequential batch | ~60s/sim | N conversations |
| `test_async_batch_simulations.py` | Parallel async batch | ~8-12s/sim | N conversations (5x faster) |
| `test_mixed_persona_batch.py` | Multi-persona testing | ~5-6s/sim | 10 Paul + 10 Ellen |

**Rate Limiting (Groq API):**
- Model: `moonshotai/kimi-k2-instruct-0905`
- TPM Limit: 250,000 (uses 85% = 212,500 for safety)
- Automatic pause/resume when approaching limits
- Zero rate limit errors in production

**Auto-Format Generation:**
Every simulation automatically creates:
- **JSON** - Machine-readable (APIs, analysis, storage)
- **Markdown** - Human-readable (review, evaluation, sharing)

### Current Agents

**Workflow Agents:**
- Intentions Workflow 1-8 (Tegra voice variations for intention-setting)

**Persona Agents (Production-Ready):**
- **Paul Persona 4 (v2.1)**: Military veteran (Air Force pilot), PTSD symptoms, terse communication (1-2 sentences), defensive/resistant, preparing for ayahuasca at Heroic Hearts
- **Ellen Persona 4 (v2.1)**: Tech entrepreneur, achievement addiction, verbose/analytical communication (4-6+ sentences), spiritually seeking, preparing for ibogaine at Beond
- **Jamie Persona 1 (v2.1)**: ADHD creative (graphic designer), scattered/enthusiastic communication (2-5 sentences jumping topics), recently diagnosed, preparing for psilocybin in Oregon

**Persona System Architecture (v2.1):**

The persona system creates **benchmark-quality synthetic humans** for agent testing. Each persona is a fully-realized character with psychological depth, distinctive communication patterns, and realistic emotional dynamics.

**Base Template:** `Agents/personas/BASE_PERSONA_TEMPLATE_v2.1.md`
- Production-grade template for creating new personas
- Modular structure: Author sections (full character) + Runtime sections (LLM-ready prompts)
- Token-optimized for simulation deployment

**Research Foundation:**
- `Agents/personas/synthetic_personas.md` - Comprehensive implementation guide
- `Agents/personas/Best Practices for Designing Synthetic Personas in Chat Simulations.pdf` - UX research and AI prompting techniques

**Core Features:**

*Chat Authenticity:*
- Realistic typos based on emotional state and character patterns
- Natural fragments, contractions, casual language
- NO stage directions (*sighs*, [pauses]) - emotion shown through words
- NO therapy-speak unless authentically in character
- Character-specific verbal fillers and punctuation patterns

*Psychological Depth:*
- Enneagram + DISC + Big Five personality frameworks
- Defense mechanisms with linguistic markers
- Core contradictions that create realistic complexity
- Attachment styles affecting relationship dynamics
- Meta-awareness loops for intellectualizing characters

*Emotional Intelligence:*
- Emotional logic systems (trigger → response → recovery)
- Cause-effect mapping for behavioral consistency
- Regression probability tracking (likelihood of backsliding)
- Felt-state cues (emotional subtext without narration)
- Secondary defense hierarchies (what happens when primary fails)

*Dynamic Evolution:*
- Session progression tracking (3 phases with inflection moments)
- Linguistic drift (gradually adopts agent language over time)
- Fatigue → tone modulation (communication simplifies when exhausted)
- State variables tracked 0-10: trust, openness, fatigue, arousal, hope, engagement
- Memory & continuity systems (what they remember/forget)

*Production Optimization:*
- Runtime YAML headers for quick seeding (token-efficient)
- Behavioral failure recovery (mid-simulation corrections)
- External validation snippets (outside perspective grounding)
- Behavioral forks (post-ceremony or major event pathways)
- Cross-persona distinctiveness validation

**Persona Comparison:**

| Persona | Communication | Defense | Primary Challenge |
|---------|--------------|---------|-------------------|
| **Paul** | Terse (1-2 sent), defensive | Denial | Building trust with resistance |
| **Ellen** | Verbose (4-6+ sent), analytical | Intellectualization | Dropping from head to heart |
| **Jamie** | Scattered (2-5 sent), tangential | Distraction | Providing structure for executive dysfunction |

**Quality Metrics:**
- Pass "1 AM text test" (feels like texting a real person)
- Distinctive voice (identifiable without seeing name)
- Emotional consistency (trigger-response patterns hold)
- Natural progression (no unrealistic breakthroughs)
- Cross-session continuity (remember and reference past)

**Creating New Personas:**
1. Copy `BASE_PERSONA_TEMPLATE_v2.1.md`
2. Fill Author sections with rich backstory and psychology
3. Create distinctive communication patterns (typos, fillers, rhythm)
4. Define emotional logic (triggers, responses, defenses)
5. Map session progression (3 phases with inflection moments)
6. Extract runtime header (YAML) and character prompt
7. Test in simulation and validate against checklist
8. Iterate based on outputs (adjust voice, add corrections)

### Performance Metrics

**Latest Results (2025-10-16):**

| Configuration | Simulations | Time | Avg/Sim | Speedup |
|--------------|-------------|------|---------|---------|
| Sequential | 10 | ~10 min | 60s | 1x baseline |
| Async (5 concurrent) | 10 | 114s | 11.4s | 5.3x |
| Mixed (10 concurrent) | 20 | 116s | 5.8s | 10.3x |
| Mixed (20 concurrent) | 20 | 78s | 3.9s | 15.4x |

**Quality Metrics:**
- 100% completion rate across 100+ simulations
- All conversations reach 40 messages (20 rounds)
- Authentic persona behavior maintained throughout
- Natural therapeutic conversation flow

**File Size Patterns:**
- Paul (terse): 4-15 KB per conversation
- Ellen (verbose): 7-20 KB per conversation

### Running Simulations

```bash
# Quick test (4 simulations)
docker exec integro_simulation_backend python test_mixed_persona_batch.py

# Full batch (20 simulations: 10 Paul + 10 Ellen with Workflow 8)
# Configured in main() function: simulations_per_persona=10, max_concurrent=10
docker exec integro_simulation_backend python test_mixed_persona_batch.py

# Convert simulation to markdown
docker exec integro_simulation_backend python convert_simulation_to_markdown.py <simulation.json>
```

**Output Structure:**
```
Agents/batch_simulations/mixed_batch_YYYYMMDD_HHMMSS/
├── paul_simulation_01.json + paul_simulation_01.md
├── paul_simulation_02.json + paul_simulation_02.md
├── ... (10 Paul conversations)
├── ellen_simulation_01.json + ellen_simulation_01.md
├── ellen_simulation_02.json + ellen_simulation_02.md
└── ... (10 Ellen conversations)
```

### Integration with Agent Lab

Uses production infrastructure:
- Same database (ConfigStorage via PostgreSQL)
- Same agent loader (AgentLoader)
- Same Agno API (`agent.arun()`)
- Docker environment: `integro_simulation_backend` container

---

## Key Tools & Scripts

### Simulation Tools

**`test_mixed_persona_batch.py`** - Primary batch testing tool
- Tests workflow agents against multiple personas simultaneously
- Built-in RateLimiter for Groq API (250K TPM management)
- Auto-generates JSON + Markdown for every simulation
- Configurable concurrency and batch size

**`convert_simulation_to_markdown.py`** - Human-readable conversion
- Converts JSON simulations to clean Markdown
- Replaces `system`/`user` with actual agent names
- Preserves all punctuation, line breaks, and message flow
- Auto-invoked during batch runs (no manual conversion needed)

**`RateLimiter` class** - API rate management
- Tracks token usage across concurrent simulations
- Automatic wait when approaching TPM limits
- 85% safety margin on published limits
- Prevents all rate limit errors

### Development Tools

**Makefile commands:**
```bash
make install          # Install dependencies with uv
make docker-build     # Build containers (auto-generates requirements.txt)
make docker-up        # Start all services
make docker-logs      # View container logs
make test-simulation  # Run single simulation test
```

---

## Infrastructure

### Docker Stack

**Services:**
- `integro_simulation_backend` - FastAPI + agent system
- `integro_simulation_frontend` - Next.js UI
- `integro_simulation_db` - PostgreSQL (agent configs)
- `integro_simulation_qdrant` - Vector DB (embeddings)
- `integro_simulation_voice_agent` - LiveKit voice support

**Deployment:**
- Multi-stage Dockerfiles auto-generate `requirements.txt` from `pyproject.toml`
- uv for modern Python dependency management
- Railway deployment configurations
- Development scripts in `scripts/`

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
├── .claude/CLAUDE.md                    # This file
├── Agents/
│   ├── batch_simulations/               # Simulation outputs (JSON + MD)
│   ├── personas/                        # Persona definitions & research
│   │   ├── BASE_PERSONA_TEMPLATE_v2.1.md        # Production template
│   │   ├── synthetic_personas.md                # Persona creation guide
│   │   ├── Best Practices for Designing Synthetic Personas in Chat Simulations.pdf  # Research
│   │   ├── Paul Persona 4.md                    # Military veteran (v2.1)
│   │   ├── Ellen Persona 4.md                   # Tech entrepreneur (v2.1)
│   │   └── Jamie Persona 1.md                   # ADHD creative (v2.1)
│   └── intentions_workflow_8.md         # Latest workflow agent
├── FINAL INTEGRO CONTENT/               # 54 weeks of curriculum
│   ├── Expedition 1_ Healing the Self/
│   ├── Expedition 2_ Connection to Other/
│   └── Expedition 3_ Connection to Awe/
├── integro/                             # Main Python package
│   ├── agent/                           # Agent core logic
│   ├── config/storage.py                # Database abstraction
│   ├── workflows/                       # Agno workflows
│   ├── memory/                          # RAG + conversation memory
│   └── web_server.py                    # FastAPI application
├── frontend/                            # Next.js UI
├── schemas/weekly-content-schema.json   # Content structure
├── test_mixed_persona_batch.py          # Primary simulation tool
├── convert_simulation_to_markdown.py    # MD conversion tool
├── docker-compose.yaml                  # Local dev stack
├── pyproject.toml                       # Python dependencies
└── Makefile                             # Dev commands
```

---

## Quick Start

```bash
# 1. Build and start services
make docker-build && make docker-up

# 2. Access services
# - Backend: http://localhost:8888
# - Frontend: http://localhost:8889
# - Qdrant: http://localhost:6333

# 3. Run simulation test
docker exec integro_simulation_backend python test_mixed_persona_batch.py

# 4. Review outputs
# Check Agents/batch_simulations/mixed_batch_YYYYMMDD_HHMMSS/
# - *.json for machine processing
# - *.md for human review
```

---

## Next Steps

**Simulation System:**
- [ ] Database integration (store runs in simulation_runs table)
- [ ] Automated LLM-based quality scoring
- [ ] Comparison dashboard for side-by-side analysis
- [ ] CI/CD integration for automated testing

**Content Parsing (Parallel Track):**
- [ ] Build PDF→JSON parser
- [ ] Process all 54 weeks
- [ ] Validate against schema
- [ ] Integrate with agent workflows

**Persona Development (v2.1 System Active):**
- [x] Base template v2.1 with runtime headers, drift, fatigue modulation
- [x] Three benchmark personas: Paul (resistant/terse), Ellen (intellectual/verbose), Jamie (ADHD/scattered)
- [ ] Create 5-10 additional diverse personas using v2.1 template:
  - Drama Queen/King (theatrical, everything is intensified)
  - Belligerent/Hostile (openly resistant, challenges everything)
  - Quiet/Reserved (minimal responses, needs drawing out)
  - Hyper-Detailed Rambler (verbose to extreme, loses thread)
  - Bad at Following Instructions (earnest but confused)
  - Crisis/Suicidal (safety protocol testing)
  - Know-It-All (jumps to answers, resists process)
  - Integration Expert (sophisticated but may bypass)
  - Tangent Master (never answers directly)
  - Novice (overwhelmed, needs hand-holding)
- [ ] Validate all personas against v2.1 checklist
- [ ] Run cross-persona comparison testing (ensure distinctive voices)
- [ ] Build persona library documentation

---

**Repository**: https://github.com/Integro-today/integro-content
**Last Updated**: 2025-10-16
**Status**: Production simulation system active with 100+ successful test runs
**Persona System**: v2.1 benchmark-quality template with 3 production personas (Paul, Ellen, Jamie)
