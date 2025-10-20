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

**Persona Agents (Production-Ready - 12 Total):**

**Original Benchmark Personas (3):**
- **Paul Persona 4**: Military veteran (Air Force pilot), PTSD, terse (1-2 sent), defensive/resistant → Tests trust-building through resistance
- **Ellen Persona 4**: Tech entrepreneur, achievement addiction, verbose (4-6+ sent), analytical → Tests helping users drop from head to heart
- **Jamie Persona 1**: ADHD creative (graphic designer), scattered (2-5 sent), enthusiastic → Tests providing structure for executive dysfunction

**New Diverse Personas (10) - Generated 2025-10-16:**
- **Vanessa Chen**: Hyper-Detailed Rambler, Chinese-American UX researcher, extremely verbose (8-12+ sent) → Tests patience with extensive detail, gentle redirection
- **Tommy Nguyen**: Confused Instruction Follower, Vietnamese refugee restaurant owner, misunderstands constantly → Tests clear simple instructions, recognizing false agreement
- **Valentina Rossi**: Drama Queen, Cuban-Italian real estate agent, ALL CAPS dramatic (4-8+ sent) → Tests staying grounded with heightened emotions, distinguishing crisis from performance
- **Sam Morrison**: Suicidal Crisis, non-binary former teacher, passive ideation → Tests crisis protocols, suicide risk recognition, appropriate resource provision
- **Diego Fuentes**: Tangent Master, Mexican-American filmmaker, every answer becomes story → Tests following tangents with curiosity, finding emotional thread
- **Dr. Rebecca Goldstein**: Know-It-All, Jewish psychologist, intellectualizes everything (3-5 sent) → Tests navigating "I already know" resistance, inviting embodiment
- **Maria Rodriguez**: Absolute Novice, Mexican-American teaching assistant, overwhelmed beginner → Tests explaining at beginner level without condescension
- **Aisha Patel**: Integration Expert, Indian-American yoga teacher, spiritual bypassing (4-7 sent) → Tests catching sophisticated avoidance, working with experienced users
- **Kyle Braddock**: Drug-Focused, white software engineer, pharmacology-obsessed (3-5 sent) → Tests redirecting substance focus to psychological prep, setting boundaries
- **Bobby Sullivan**: Prejudiced/Biased, Irish-Catholic coal miner, trauma-based bias (2-4 sent) → Tests maintaining boundaries with biased views, redirecting to underlying pain
- **Chloe Park**: Manipulative/Antisocial, Korean-American publicist, narcissistic traits (3-5 sent) → Tests maintaining boundaries with manipulation, not getting pulled into enabling
- **Jack Kowalski**: Violence Risk, Polish-American veteran, intrusive violent thoughts (1-3 sent) → Tests violence risk protocols, crisis resource provision, safety boundaries

**Diversity Coverage:**
- Gender: Women (6), Men (5), Non-binary (1)
- Ethnicity: Chinese, Vietnamese, Cuban-Italian, White (various), Mexican, Jewish, Indian, Korean, Polish
- Age: 28-58 years
- Geography: West Coast, East Coast, Southwest, Midwest, South
- Class: Working-class to professional
- Psychedelic Experience: Zero to expert (12+ years)

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

**⚠️ Persona Generator Lessons Learned (2025-10-16):**

During the 2025-10-16 persona generation session, we discovered **critical flaws** in using the persona-generator subagent without sufficient context:

**Problem Identified:**
- Initial generation created multiple personas with the **same name** ("Marcus DeAngelo" repeatedly)
- **All personas were African American** despite requesting diverse archetypes
- Lacked diversity across ethnicity, gender, geography, and class
- This is problematic and not representative for testing purposes

**Root Cause:**
The persona-generator subagent, when given only archetype descriptions (e.g., "Drama Queen", "Know-It-All") without detailed demographic seeds, defaulted to similar demographic patterns and didn't ensure diversity.

**Solution Implemented:**
Created comprehensive `PERSONA_REFERENCE_GUIDE.md` with detailed seed information for each persona including:
- Specific names, ages, pronouns
- Detailed ethnicity, location, occupation
- Family background, education, relationships
- Cultural markers and regional dialects
- Psychological frameworks and communication patterns

**Future Requirements:**
- ✅ **ALWAYS use detailed seed prompts** from `PERSONA_REFERENCE_GUIDE.md`
- ✅ **Specify exact demographics** (name, ethnicity, location, age) in seed
- ✅ **Include cultural markers** and regional characteristics
- ⚠️ **OR modify persona-generator subagent** to ensure diversity automatically
- ⚠️ **Validate output diversity** before accepting generated personas

**Reference Files:**
- `Agents/personas/PERSONA_REFERENCE_GUIDE.md` - Detailed seeds for all 12 personas
- `Agents/personas/persona_seed_list.md` - Quick reference for future generation

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
│   ├── personas/                        # Persona definitions & research (12 total)
│   │   ├── BASE_PERSONA_TEMPLATE_v2.1.md                        # Production template
│   │   ├── PERSONA_REFERENCE_GUIDE.md                           # Detailed seeds for all personas
│   │   ├── persona_seed_list.md                                 # Quick reference for generation
│   │   ├── synthetic_personas.md                                # Persona creation guide
│   │   ├── Best Practices for Designing Synthetic Personas.pdf  # Research
│   │   ├── Paul_Persona_4.md                                    # Military veteran (terse/defensive)
│   │   ├── Ellen_Persona_4.md                                   # Tech entrepreneur (verbose/analytical)
│   │   ├── Jamie_Persona_1.md                                   # ADHD creative (scattered/enthusiastic)
│   │   ├── Hyper_Detailed_Rambler_Persona_1.md                  # Vanessa Chen (extremely verbose)
│   │   ├── Tommy_Nguyen_Confused_Instruction_Follower_Persona_1.md  # Vietnamese refugee
│   │   ├── Valentina_Rossi_Drama_Queen_Persona_1.md             # Cuban-Italian dramatic
│   │   ├── Sam_Morrison_Suicidal_Crisis_Persona_1.md            # Non-binary crisis
│   │   ├── Diego_Fuentes_Tangent_Master_Persona_1.md            # Mexican-American tangential
│   │   ├── Dr_Rebecca_Goldstein_Know_It_All_Persona_1.md        # Jewish psychologist
│   │   ├── Aisha_Patel_Integration_Expert_Persona_1.md          # Indian-American spiritual bypassing
│   │   ├── Kyle_Braddock_Drug_Focused_Persona_1.md              # White software engineer
│   │   ├── Bobby_Sullivan_Prejudiced_Persona_1.md               # Irish-Catholic coal miner
│   │   ├── Chloe_Park_Manipulative_Persona_1.md                 # Korean-American narcissistic
│   │   └── Jack_Kowalski_Violence_Risk_Persona_1.md             # Polish-American veteran
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
- [x] Created 10 additional diverse personas (2025-10-16):
  - [x] Hyper-Detailed Rambler (Vanessa Chen - Chinese-American UX researcher)
  - [x] Confused Instruction Follower (Tommy Nguyen - Vietnamese refugee)
  - [x] Drama Queen (Valentina Rossi - Cuban-Italian real estate agent)
  - [x] Suicidal Crisis (Sam Morrison - non-binary former teacher)
  - [x] Tangent Master (Diego Fuentes - Mexican-American filmmaker)
  - [x] Know-It-All (Dr. Rebecca Goldstein - Jewish psychologist)
  - [x] Absolute Novice (Maria Rodriguez - Mexican-American teaching assistant)
  - [x] Integration Expert (Aisha Patel - Indian-American yoga teacher)
  - [x] Drug-Focused (Kyle Braddock - white software engineer)
  - [x] Prejudiced/Biased (Bobby Sullivan - Irish-Catholic coal miner)
  - [x] Manipulative/Antisocial (Chloe Park - Korean-American publicist)
  - [x] Violence Risk (Jack Kowalski - Polish-American veteran)
- [x] Built persona library documentation (PERSONA_REFERENCE_GUIDE.md)
- [ ] Validate all 12 personas in actual simulations
- [ ] Run cross-persona comparison testing (ensure distinctive voices in practice)
- [ ] Create YAML configs for new personas to import into database
- [ ] Improve persona-generator subagent to ensure diversity automatically

---

**Repository**: https://github.com/Integro-today/integro-content
**Last Updated**: 2025-10-16
**Status**: Production simulation system active with 100+ successful test runs
**Persona System**: v2.1 benchmark-quality template with **12 production personas** covering diverse demographics and therapeutic challenges (Paul, Ellen, Jamie + 9 new personas generated 2025-10-16)
