# Integro Content Project

## Project Overview

This project is part of the broader Integro ecosystem, working alongside:
- **integro-api**: Backend API services
- **integro-web**: Web application frontend
- **Agno Agent Nursery**: Agentic workflow creation and management system

### Mission
Convert structured DOCX content files into machine-readable JSON format to enable the Agno agent nursery to create and execute intelligent agentic workflows for content delivery and interaction.

## Content Structure

### Current Content Organization

The curriculum consists of **3 major expeditions** with **54 weeks total** (18 weeks per expedition):

#### Expedition 1: Healing the Self (18 weeks)
```
Week 1-2:   Roots of Healing
Week 3-4:   Body As Healer
Week 5-6:   Resistance, Acceptance, and Surrender
Week 7-8:   Rhythms of Healing
Week 9-10:  Emotions and Resilience
Week 11:    Wholeness: Shadow Work
Week 12:    Wholeness: Parts Work
Week 13-14: Authenticity: Coming Home to Ourselves
Week 15-16: Stories
Week 17-18: Visioning the Future Self
```

#### Expedition 2: Connection to Other (The Web of Connection) (18 weeks)
```
Week 1-2:   Foundations of Connection
Week 3-4:   Communication as a Bridge
Week 5-6:   Wholeness in Relationship
Week 7-8:   Attunement and Safety
Week 9-10:  Intimacy and Vulnerability
Week 11-12: Attachment, Love, and Belonging
Week 13-14: Boundaries and Needs
Week 15-16: The Ongoing Dance: Growth and Maintenance
Week 17-18: Expanding Connection (Across Difference and with More-Than-Human World)
```

#### Expedition 3: Connection to Awe (18 weeks)
```
Week 1-2:   Sacred Presence
Week 3-4:   Ego and Surrender
Week 5-6:   Unitive Consciousness
Week 7-8:   Awe and Wonder
Week 9-10:  Love As a Divine Force
Week 11-12: Death and Rebirth
Week 13-14: Silence and the Void
Week 15-16: Sacred Embodiment: Living the Divine Through the Body
Week 17-18: Ordinary Life As Practice
```

#### Additional Content
- **Syllabus**: Program overview
- **Demo Content**: Sample days (IFS and The Work)
- **Content with no current home**: Standalone topics for future use
- **Daily Content Template**: Template for creating new content

### Document Structure Pattern

Each weekly file contains **6-7 days of content**. Each day follows this consistent structure:

**Day-Level Components:**
- **Week**: Week number
- **Day**: Day number (1-7)
- **Day Title**: Specific topic for the day
- **Lesson Name**: Weekly theme (consistent across all days in the week)
- **Meme**: Placeholder for engaging image
- **Summary**: 1-2 sentence overview
- **Daily Passage**: Main educational content (3-5 pages)
- **Alternative View**: Counterpoint or balanced perspective
- **Activity**: Reflective questions and exercises
- **Tool References**: Meditation tools, worksheets, exercises
- **Sources**: Academic/therapeutic references
- **Domain**: Content domain (e.g., "Psychotherapeutic and Cognitive")
- **Modality**: Therapeutic approach (e.g., "Psychological and Therapeutic")

**Example from Week 1, Day 1:**
- Day Title: "What Does Healing Mean?"
- Summary: Healing is about moving toward wholeness, not fixing what's broken
- Activity Questions: "When I think of healing, what images come to mind?"
- Sources: Gabor Maté, Carl Jung, Daniel Siegel, etc.

## Project Scale

**Content Volume:**
- 3 Expeditions
- 54 Weeks (18 per expedition)
- ~324-378 Days of content (6-7 days per week)
- Estimated 1,000+ pages of educational material
- 100+ therapeutic tools and exercises
- 200+ academic/clinical sources

This represents a comprehensive transformative learning curriculum designed for psychedelic integration and deep personal healing work.

## Target JSON Schema

The goal is to convert DOCX/PDF files into structured JSON. See `/schemas/weekly-content-schema.json` for the full JSON Schema definition.

**Example output structure:**

```json
{
  "expedition": {
    "number": 1,
    "title": "Healing the Self"
  },
  "week": 1,
  "theme": "Roots of Healing",
  "days": [
    {
      "day_number": 1,
      "day_title": "What Does Healing Mean?",
      "summary": "Healing is not about fixing what is broken. It's about moving toward wholeness...",
      "daily_passage": "When most people think about healing, they imagine a process...",
      "alternative_view": "Some argue that healing must be practical and outcome-driven...",
      "activity": {
        "questions": [
          "When I think of the word 'healing,' what images or assumptions come to mind?",
          "How has my life taught me to see healing as fixing?"
        ]
      },
      "tools": [
        {"name": "Personal Resource Map tool"}
      ],
      "sources": [
        {
          "author": "Maté, G.",
          "year": 2003,
          "title": "When the Body Says No: Exploring the Stress-Disease Connection",
          "publisher": "Wiley"
        }
      ],
      "domain": "Psychotherapeutic",
      "modality": "Psychological and Therapeutic"
    }
  ],
  "metadata": {
    "source_file": "Week 1_ Roots of Healing.pdf",
    "last_updated": "2025-10-13T11:20:00Z"
  }
}
```

## Agno Framework Integration

### What is Agno?
Agno is a Python framework for building multi-agent systems with:
- **Agents**: Individual AI entities with specific roles and capabilities
- **Teams**: Collections of agents working collaboratively
- **Workflows**: Multi-step processes orchestrating agents, teams, and custom functions
- **Tools**: Specialized capabilities agents can use (search, data retrieval, etc.)

### Agno Architecture Concepts

#### 1. Agents
Individual AI entities with:
- Model (OpenAI, Claude, etc.)
- Tools (DuckDuckGo, HackerNews, custom functions)
- Instructions/Role
- Memory/State

#### 2. Teams
Collections of agents that:
- Share context and communicate
- Delegate tasks among members
- Work on complex multi-faceted problems
- Can include nested sub-teams

#### 3. Workflows
Sequential or conditional execution of:
- Agents
- Teams
- Custom Python functions
- Parallel steps
- Conditional branches

Example workflow pattern from Agno docs:
```python
Workflow(
    name="Content Creation Workflow",
    steps=[
        research_team,      # Team of agents
        content_planner,    # Individual agent
        writer_agent,       # Individual agent
        editor_agent        # Individual agent
    ]
)
```

### Agent Nursery Application

The content from this project will be used to create Agno workflows such as:

1. **Daily Content Delivery Workflow**
   - Research agent: Gathers relevant supplementary materials
   - Content agent: Delivers daily content in appropriate format
   - Activity agent: Guides users through daily activities
   - Reflection agent: Helps users process and integrate

2. **Personalized Learning Path**
   - Assessment agent: Evaluates user progress
   - Recommendation agent: Suggests next steps
   - Content adapter: Adjusts content difficulty/style

3. **Community Facilitation Team**
   - Discussion facilitator: Guides group conversations
   - Question answerer: Responds to content questions
   - Connection maker: Links concepts across weeks/expeditions

## Development Phases

### Phase 1: Content Parsing (Current)
- [ ] Set up DOCX parsing infrastructure
- [ ] Identify consistent patterns across all files
- [ ] Handle edge cases and variations
- [ ] Extract structured data from headings/subheadings
- [ ] Preserve formatting and metadata

### Phase 2: JSON Schema Design
- [ ] Define comprehensive JSON schema
- [ ] Account for all content types (text, activities, media)
- [ ] Design for Agno workflow compatibility
- [ ] Create validation rules

### Phase 3: Conversion Pipeline
- [ ] Build automated DOCX → JSON converter
- [ ] Implement batch processing
- [ ] Add quality assurance checks
- [ ] Create manual review workflow

### Phase 4: Agno Integration
- [ ] Design agent roles for content delivery
- [ ] Create workflow templates
- [ ] Implement content-aware agents
- [ ] Build testing framework for agent workflows

### Phase 5: Agent Nursery Deployment
- [ ] Deploy to agent nursery environment
- [ ] Create agent configuration files
- [ ] Set up monitoring and observability
- [ ] Implement feedback loops

## Technical Considerations

### Content Processing
- **Primary Source**: PDF files (DOCX files exist but are binary/not directly parseable)
- **PDF Parsing**: Use `PyPDF2`, `pdfplumber`, or `pypdf` for text extraction
- **Structure preservation**: Maintain day/section hierarchy through text pattern matching
- **Metadata extraction**: Week number, expedition, theme, day titles
- **Error handling**: Graceful handling of formatting inconsistencies
- **Pattern Recognition**: Identify section headers (Summary, Daily Passage, Activity, etc.)

### File Organization
```
FINAL INTEGRO CONTENT/
├── Expedition 1_ Healing the Self/
│   ├── Week 1_ Roots of Healing/
│   │   ├── Week 1_ Roots of Healing.docx
│   │   ├── Week 1_ Roots of Healing.pdf  ← Primary source
│   │   └── Week 1_ Roots of Healing.docx:Zone.Identifier (ignore)
│   └── ...
├── Expedition 2_ Connection to Other/
├── Expedition 3_ Connection to Awe/
├── Content with no current home--to be used later/
├── Demo Content/
└── Syllabus/
```

### JSON Output
- **Validation**: JSON Schema validation for all outputs (see `/schemas/weekly-content-schema.json`)
- **Storage**: Organized by expedition/week structure in `/output` directory
- **Versioning**: Track content versions for updates
- **References**: Maintain cross-references between weeks and tools

### Agno Workflow Design
- **Modularity**: Design reusable agent components
- **State management**: Use workflow session state for user progress
- **Database**: Consider SQLite or PostgreSQL for workflow persistence
- **Tools**: Create custom tools for content retrieval and filtering

## Agent Lab Infrastructure

This project now includes a complete agent development and testing laboratory integrated from `integro-agents-wip`.

### Architecture Overview

**Backend (FastAPI)**:
- **Web Server**: `integro/web_server.py` - Full FastAPI application with WebSocket support
- **Agent System**: `integro/agent/` - Core agent logic and configuration
- **Storage Layer**: `integro/config/storage.py` - Unified PostgreSQL/SQLite abstraction
- **Workflows**: `integro/workflows/` - Agno workflow implementations
- **Memory**: `integro/memory/` - Knowledge base and conversation memory
- **Tools**: `integro/tools/` - Agent capabilities and functions

**Frontend (Next.js)**:
- Located in `frontend/` directory
- Real-time agent chat interface via WebSocket
- Agent configuration UI
- Knowledge base management
- Multi-agent comparison view

**Database Schema**:
```sql
-- Agent configurations
agents (id, name, description, config, knowledge_base_id, created_at, updated_at)

-- Knowledge bases
knowledge_bases (id, name, description, collection_name, config, created_at, updated_at)

-- KB documents with embeddings
kb_documents (id, kb_id, doc_id, file_path, content, metadata, embedding, created_at)
```

**Deployment**:
- Docker Compose with multi-stage builds for automatic dependency management
- PostgreSQL, Qdrant, Backend, Frontend, Voice Agent services
- Railway deployment configurations
- Development scripts in `scripts/` directory
- Container names: `integro_simulation_*` (qdrant, db, backend, frontend, voice_agent)

### Agent Execution Model

Agents are executed via:
```python
response = await agent.arun(
    message="User input",
    session_id="unique_session_id",
    stream=False
)
```

Agents can:
- Use knowledge bases (RAG with Qdrant)
- Execute tools and functions
- Maintain conversation history
- Stream responses via WebSocket

### Dependency Management

The project uses **uv** for modern Python dependency management:

**Files**:
- `pyproject.toml` - Source of truth for all dependencies
- `uv.lock` - Locked versions for reproducibility
- `requirements.txt` - Auto-generated during Docker build

**Docker Multi-Stage Builds**:
Both `Dockerfile` and `Dockerfile.voice` automatically generate `requirements.txt` from `pyproject.toml`:
```dockerfile
# Stage 1: Generate requirements
FROM python:3.11-slim AS requirements-builder
RUN pip install --no-cache-dir uv
COPY pyproject.toml .
RUN uv pip compile pyproject.toml --extra voice -o requirements.txt

# Stage 2: Build application
FROM python:3.11-slim
COPY --from=requirements-builder /build/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

**Optional Dependencies**:
- `[dev]` - Development tools (pytest, black, ruff, mypy)
- `[voice]` - LiveKit voice agent support (livekit, livekit-agents, plugins)

**Commands** (via Makefile):
```bash
make install        # Install with voice extras
make lock           # Update uv.lock
make requirements   # Generate requirements.txt
make docker-build   # Build with auto-generated requirements
```

## Agent Simulation & Evaluation System

### Purpose

A **production-ready testing and evaluation framework** for agent configurations by simulating realistic conversations between two agents. This system enables:

- **Pre-deployment validation**: Test agents before production
- **A/B testing**: Compare different prompt configurations and workflow agents
- **Regression testing**: Ensure changes don't break existing behavior
- **Safety verification**: Detect inappropriate responses
- **Performance metrics**: Quantify agent quality and conversation efficiency
- **Persona testing**: Validate agent behavior across different user personas

### System Architecture

The simulation system consists of four main components integrated with the agent lab infrastructure:

#### 1. Core Simulation Infrastructure

**TwoAgentSimulation Class** (`test_two_agent_simulation.py`):
- Loads agents from database using ConfigStorage (same as `/api/agents`)
- Manages conversation flow between two agents
- Supports configurable conversation lengths (default: 20 rounds = 40 messages)
- Saves conversations to JSON with agent references (not full configs)

**Conversation Flow**:
1. **System agent** receives initial prompt and generates opening message → `system0`
2. **User agent** (persona) responds → `user0`
3. System agent responds → `system1`
4. User agent responds → `user1`
5. Continues for max_turns rounds

**Integration with Agent Lab**:
```python
# Uses existing agent lab infrastructure
storage = ConfigStorage()  # Same as /api/agents
agent_loader = AgentLoader()

# Load agents by database ID
system_config = await storage.load_agent(system_agent_id)
user_config = await storage.load_agent(user_agent_id)

# Create agents using same method as web interface
system_agent = agent_loader.create_agent(system_config, knowledge_base=None)
user_agent = agent_loader.create_agent(user_config, knowledge_base=None)

# Run conversation using Agno's arun() API
response = await agent.arun(
    message,  # Positional argument per Agno docs
    session_id=session_id,
    stream=False
)
```

#### 2. Test Scripts and Capabilities

**test_two_agent_simulation.py** - Single Simulation:
- Basic two-agent conversation runner
- Sequential execution
- Used for debugging and single-run testing
- Output: `Agents/simulation_YYYYMMDD_HHMMSS.json`

**test_batch_simulations.py** - Sequential Batch:
- Runs multiple simulations sequentially (10+ simulations)
- Agent reuse for efficiency (load once, run multiple times)
- Timestamped batch folders
- Output: `Agents/batch_simulations/batch_YYYYMMDD_HHMMSS/`
- Performance: ~50-60 seconds per simulation

**test_async_batch_simulations.py** - Parallel Async Batch:
- Runs simulations concurrently with semaphore-controlled concurrency
- 5-10x faster than sequential execution
- Configurable max concurrent simulations (default: 5)
- Each simulation loads agents independently (thread-safe)
- Real-time progress updates
- Output: `Agents/batch_simulations/batch_YYYYMMDD_HHMMSS/`
- Performance: ~8-12 seconds per simulation

**test_mixed_persona_batch.py** - Mixed Persona Testing:
- Tests one workflow agent against multiple persona types
- Runs N simulations per persona in parallel
- Currently configured: 5 Paul + 5 Ellen simulations
- Named output files by persona: `paul_simulation_01.json`, `ellen_simulation_01.json`
- Workflow agent sends first message (role reversal)
- Output: `Agents/batch_simulations/mixed_batch_YYYYMMDD_HHMMSS/`

#### 3. Current Test Configuration

**Agents in Database**:
- **Workflow Agents**: Intentions Workflow 1-4 (Tegra voice variations)
- **Personas**: Paul Persona 3 (veteran with PTSD), Ellen Persona 3 (entrepreneur with achievement addiction)
- **Other**: Attachment Style, Guidelines Evaluator, Trauma Guide, etc.

**Test Scenarios**:

1. **Paul Persona 3** (Military Veteran):
   - Night terrors and PTSD symptoms
   - Relationship strain with partner Amanda
   - Direct, military communication style
   - Preparing for ayahuasca ceremony via Heroic Hearts
   - Opening: Brief, resistant, focused on practical outcomes

2. **Ellen Persona 3** (Tech Entrepreneur):
   - Achievement addiction and spiritual disconnection
   - Fear of emptiness without external validation
   - Reflective, analytical communication style
   - Preparing for ibogaine ceremony at Beond
   - Opening: Longer, introspective, questioning purpose

3. **Workflow Variations**:
   - **Workflow 2**: Empathetic, reflective, more therapeutic language
   - **Workflow 3**: Balanced approach with structured progression
   - **Workflow 4 (Tegra)**: Direct, grounded, minimal therapy-speak

#### 4. Output Format and Storage

**JSON Structure**:
```json
{
  "session": "batch_20251016_001540_paul_sim01",
  "datetime": "2025-10-16T00:16:49.630101",
  "notes": "Batch 20251016_001540, paul simulation 1",
  "seed_message": "You're starting intention-setting work with someone.\n\nIntentions work like a compass...",
  "system_agent_id": "intentions_workflow_6",
  "user_agent_id": "paul_persona_3",
  "max_turns": 20,
  "system0": "Let's set intentions for your work...",
  "user0": "I got into Heroic Hearts. Flying to Costa Rica...",
  "system1": "Three threads: 1. Sleep through the night...",
  "user1": "Yeah, that about sums it up...",
  ...
  "system19": "...",
  "user19": "..."
}
```

**File Organization**:
```
Agents/
├── batch_simulations/
│   ├── batch_20251015_222200/          # Sequential batch (Paul only)
│   │   ├── simulation_01.json (13 KB)
│   │   ├── simulation_02.json (17 KB)
│   │   └── ... (10 files total)
│   ├── batch_20251015_223412/          # Async batch (Ellen only)
│   │   ├── simulation_01.json (13 KB)
│   │   └── ... (10 files, 5.3x faster)
│   └── mixed_batch_20251015_225959/    # Mixed personas
│       ├── paul_simulation_01.json (6 KB)
│       ├── paul_simulation_02.json (6 KB)
│       ├── ellen_simulation_01.json (11 KB)
│       └── ... (5 Paul + 5 Ellen)
└── simulation_template.json
```

### Performance Metrics

**Achieved Performance** (as of 2025-10-16):

| Test Type | Simulations | Concurrent | Total Time | Per Simulation | Speedup |
|-----------|------------|-----------|------------|----------------|---------|
| Sequential Batch | 10 (Paul) | 1 | ~10 minutes | 60s | 1x baseline |
| Async Batch | 10 (Ellen) | 5 | 113.8s | 11.4s | 5.3x faster |
| Mixed Batch (WF4) | 10 (5P+5E) | 5 | 84.8s | 8.5s | 7x faster |
| Mixed Batch (WF6) | 20 (10P+10E) | 20 | 77.4s | 3.9s | 15x faster |
| Mixed Batch (WF7) | 20 (10P+10E) | 20 | 78.3s | 3.9s | 15x faster |

**File Size Patterns**:
- Paul conversations: 5-12 KB (more concise, military style)
- Ellen conversations: 8-18 KB (longer, reflective style)
- Workflow 4 (Tegra): 20-30% smaller files than Workflow 3 (more efficient)

**Conversation Quality**:
- 100% completion rate across all tests
- All 40-message conversations (20 rounds) complete successfully
- Authentic persona behavior maintained throughout
- Natural conversation flow with appropriate therapeutic responses
- Personas generate unique openings from same prompt

### Evaluation Capabilities

Simulations can be evaluated on:

1. **Response Quality**:
   - Coherence and relevance of responses
   - Therapeutic appropriateness
   - Alignment with agent instructions
   - Natural conversation flow

2. **Safety & Ethics**:
   - Boundary violations
   - Inappropriate content
   - Harmful advice detection

3. **Persona Consistency**:
   - Character traits maintained
   - Communication style authentic
   - Background details consistent

4. **Workflow Effectiveness**:
   - Goal completion (3 intentions created)
   - Efficiency (turns to completion)
   - User satisfaction indicators

5. **Agent Comparison**:
   - Side-by-side workflow agent testing
   - Persona-specific performance
   - Token efficiency metrics

### Use Cases

1. **Prompt Engineering & A/B Testing**:
   - Run 10 simulations with Workflow 3, 10 with Workflow 4
   - Compare conversation quality, efficiency, and outcomes
   - Select best-performing agent configuration

2. **Persona Coverage Testing**:
   - Verify workflow agent handles diverse user types
   - Test military veteran (Paul) vs entrepreneur (Ellen)
   - Identify persona-specific failure modes

3. **Regression Testing**:
   - Run baseline simulations before agent changes
   - Run new simulations after updates
   - Compare outputs to detect behavioral changes

4. **Performance Benchmarking**:
   - Test different LLM providers (OpenAI, Anthropic, Groq)
   - Compare response times and quality
   - Optimize token usage

5. **Workflow Validation**:
   - Verify multi-step therapeutic protocols
   - Ensure intention-setting process completes
   - Test edge cases and error handling

### Running Simulations

**Single Simulation**:
```bash
docker exec integro_simulation_backend python test_two_agent_simulation.py
# Output: Agents/simulation_20251015_210500.json
```

**Async Batch (10 Ellen simulations)**:
```bash
docker exec integro_simulation_backend python test_async_batch_simulations.py
# Output: Agents/batch_simulations/batch_20251015_223412/
# 10 files, ~114 seconds total
```

**Mixed Persona Batch (10 Paul + 10 Ellen with Workflow 7)**:
```bash
docker exec integro_simulation_backend python test_mixed_persona_batch.py
# Output: Agents/batch_simulations/mixed_batch_20251016_003125/
# 20 files, ~78 seconds total (20 running in parallel)
```

### Integration with Agent Lab

The simulation system is fully integrated with the agent lab infrastructure:

1. **Uses Same Database**: Agents loaded via ConfigStorage (same as `/api/agents`)
2. **Uses Same Agent Loader**: Identical initialization as web interface
3. **Uses Same Agno API**: Calls `agent.arun()` with proper Agno syntax
4. **Shares Session Management**: Uses Agno session IDs for conversation history
5. **Docker Environment**: Runs in `integro_simulation_backend` container

**Data Flow**:
```
PostgreSQL (agents table)
    ↓
ConfigStorage.load_agent()
    ↓
AgentLoader.create_agent()
    ↓
agent.arun(message, session_id=...)
    ↓
JSON output (agent references only)
```

### Future Enhancements

- [ ] Database integration: Store simulations in `simulation_runs` table
- [ ] Automated evaluation: LLM-based quality scoring
- [ ] Comparison dashboard: Side-by-side conversation analysis
- [ ] Goal detection: Early termination when intentions complete
- [ ] Metrics tracking: Response time, token usage, completion rates
- [ ] CI/CD integration: Automated testing on agent updates

## Related Projects

### integro-api
Backend services that:
- Serve JSON content to web and agents
- Manage user progress and state
- Handle authentication and authorization
- Provide APIs for agent nursery

### integro-web
Frontend application that:
- Displays content to users
- Tracks user journey through expeditions
- Interfaces with agent-powered features
- Provides community features

### Agno Agent Nursery
Platform for:
- Creating agent workflows
- Deploying agents to production
- Monitoring agent performance
- Managing agent lifecycle

## Key Files and Directories

```
integro-content/
├── .claude/
│   └── CLAUDE.md                    # This file - project overview
├── FINAL INTEGRO CONTENT/           # Source content (54 weeks across 3 expeditions)
│   ├── Expedition 1_ Healing the Self/
│   ├── Expedition 2_ Connection to Other/
│   └── Expedition 3_ Connection to Awe/
├── Agents/                          # Agent configurations and templates
│   ├── intentions_json.md           # Intentions schema
│   ├── simulation_template.json     # Old format (full agent configs)
│   └── simulation_output_template.json # New format (agent references)
├── schemas/                         # JSON schemas
│   └── weekly-content-schema.json   # Content structure definition
├── integro/                         # Main Python package
│   ├── agent/                       # Agent core logic
│   ├── config/                      # Configuration management (storage.py)
│   ├── workflows/                   # Agno workflow implementations
│   ├── memory/                      # Knowledge base & conversation memory
│   ├── tools/                       # Agent tools and capabilities
│   ├── simulations/                 # Simulation infrastructure (placeholder)
│   ├── web_server.py                # FastAPI application
│   └── ...
├── frontend/                        # Next.js web application
├── scripts/                         # Deployment & utility scripts
├── tests/                           # Test suite
├── data/                            # Runtime data (logs, qdrant storage)
├── output/                          # Generated JSON files
│   └── simulations/                 # Agent simulation outputs
├── docker-compose.yaml              # Local development stack
├── Dockerfile                       # Backend multi-stage build
├── Dockerfile.voice                 # Voice agent multi-stage build
├── .dockerignore                    # Docker build optimization
├── pyproject.toml                   # Python dependencies (source of truth)
├── uv.lock                          # Locked dependency versions
├── requirements.txt                 # Auto-generated for Docker
├── Makefile                         # Development commands
├── test_two_agent_simulation.py     # Single simulation test (sequential)
├── test_batch_simulations.py        # Sequential batch simulation runner
├── test_async_batch_simulations.py  # Parallel async batch runner (5-10x faster)
├── test_mixed_persona_batch.py      # Mixed persona testing (Paul + Ellen)
├── agno_mapping.md                  # Comprehensive Agno API reference
├── SIMULATION_README.md             # Simulation system documentation
├── REQUIREMENTS_GENERATION.md       # Dependency management guide
└── DOCKER_SETUP_COMPLETE.md         # Docker setup documentation
```

## Getting Started

### Quick Start (Agent Lab)

```bash
# 1. Install dependencies locally (optional)
make install

# 2. Build Docker containers (auto-generates requirements.txt)
make docker-build

# 3. Start all services
make docker-up

# 4. Access services:
# - Backend API: http://localhost:8888
# - Frontend: http://localhost:8889
# - Qdrant: http://localhost:6333
# - PostgreSQL: localhost:5432

# 5. View logs
make docker-logs

# 6. Stop services
make docker-down
```

### Test Two-Agent Simulation

```bash
# Run the simulation test script
make test-simulation

# Or directly
python test_two_agent_simulation.py

# Output: output/simulations/simulation_YYYYMMDD_HHMMSS.json
```

### Content Processing (Future)

1. ✅ **Explore content**: Reviewed PDF structure and patterns
2. ✅ **Define schema**: Created JSON schema at `/schemas/weekly-content-schema.json`
3. **Build parser**: Develop PDF parsing utilities
   - Extract text from PDFs
   - Identify section boundaries (Week, Day, Summary, etc.)
   - Parse structured content into JSON
4. **Convert sample**: Test with Week 1, Expedition 1
5. **Iterate**: Refine parser based on edge cases
6. **Scale**: Process all 54 weeks
7. **Integrate**: Connect with agent nursery and integro-api

## Success Metrics

- ✅ All 54 weeks of content identified and mapped
- All PDF/DOCX files successfully converted to JSON
- JSON validates against schema
- Agno agents can consume and deliver content
- Content relationships preserved (week-to-week, tool references)
- Zero data loss in conversion
- Agent workflows operate effectively
- Tools and activities properly linked
- Source citations maintained

## Important Notes

### Content Philosophy
- Content is designed for **transformative learning** and **psychedelic integration**
- Each expedition represents a **thematic journey** of healing and growth
- Weeks build **progressively** on previous content
- Activities are designed for **experiential learning** and deep reflection
- Agent delivery should **enhance, not replace**, human connection and community

### Technical Notes
- **Use PDF files** as primary source (Claude Code Read tool can parse PDFs)
- DOCX files are binary and not directly readable
- Zone.Identifier files are Windows metadata - can be ignored
- Content totals ~1,000+ pages across 54 weeks
- Consistent structure makes automated parsing feasible

### File Status
- **Only Week 1, Expedition 1 has a PDF** - others may need conversion
- May need to batch convert DOCX → PDF using external tools (e.g., LibreOffice headless, Pandoc, or Microsoft Word automation)
- Alternative: Use python-docx library to extract text from DOCX files directly

---

**Last Updated**: 2025-10-15
**Project Status**: Production Simulation System Active, Agent Lab Running, Docker Auto-Generation
**Current Focus**: Agent testing and evaluation, content parsing (parallel track)

## Recent Additions (2025-10-15)

### ✅ Docker Auto-Generation Setup
- Multi-stage Dockerfiles that auto-generate `requirements.txt` from `pyproject.toml`
- Voice dependencies added as optional extras (`[voice]`)
- Container names updated to `integro_simulation_*` prefix
- `.dockerignore` optimization for faster builds

### ✅ Data Migration from integro-agents-wip
- Copied PostgreSQL database volume (10 agents migrated)
- Copied Qdrant vector database volume
- All agent configurations preserved and accessible
- Environment variables configured for API keys

### ✅ Production Simulation System
**Four test scripts operational:**

1. **test_two_agent_simulation.py** - Single simulation runner
   - Sequential execution
   - Debug and single-run testing
   - 20 rounds (40 messages)
   - Workflow agent sends first message

2. **test_batch_simulations.py** - Sequential batch runner
   - 10+ simulations per run
   - Agent reuse for efficiency
   - ~60 seconds per simulation
   - Timestamped batch folders

3. **test_async_batch_simulations.py** - Parallel async batch runner
   - 5-10x faster than sequential
   - Semaphore-controlled concurrency (max 5 concurrent)
   - ~8-12 seconds per simulation
   - Real-time progress updates
   - Thread-safe agent loading

4. **test_mixed_persona_batch.py** - Mixed persona testing
   - Tests one workflow agent against multiple personas
   - 10 Paul + 10 Ellen simulations (20 total)
   - Named output files by persona
   - Workflow agent sends first message (role reversal)
   - Configurable concurrency (default: 20 parallel)
   - ~78 seconds for 20 simulations (3.9s avg at max concurrency)

**Performance achieved:**
- Sequential: ~60s per simulation (baseline)
- Async single persona (5 concurrent): 11.4s per simulation (5.3x faster)
- Async mixed personas (5 concurrent): 8.5s per simulation (7x faster)
- Async mixed personas (20 concurrent): 3.9s per simulation (15x faster)
- 100% completion rate across all tests
- 60+ successful simulation runs

**Agent configurations tested:**
- Paul Persona 3 (military veteran, PTSD, direct communication)
- Ellen Persona 3 (entrepreneur, achievement addiction, reflective)
- Intentions Workflow 2 (empathetic, therapeutic)
- Intentions Workflow 3 (balanced, structured)
- Intentions Workflow 4 (Tegra voice: direct, grounded, minimal therapy-speak)
- Intentions Workflow 6 (updated opening message, flexible timeline)
- Intentions Workflow 7 (refined Tegra voice)

**Output organization:**
- `Agents/batch_simulations/` - All batch runs
- Timestamped folders: `batch_YYYYMMDD_HHMMSS/` or `mixed_batch_YYYYMMDD_HHMMSS/`
- JSON files with agent references (not full configs)
- File sizes: 5-18 KB per conversation (Paul: 5-12 KB, Ellen: 8-18 KB)

### ✅ Comprehensive Documentation
- `agno_mapping.md` - Complete Agno framework API reference (40+ examples)
- `SIMULATION_README.md` - Simulation architecture and use cases
- `REQUIREMENTS_GENERATION.md` - Dependency management with uv
- `DOCKER_SETUP_COMPLETE.md` - Docker setup guide
- `CLAUDE.md` - Updated with complete simulation system documentation

### ✅ Enhanced Makefile
35+ commands for:
- Dependency management (`make install`, `make lock`, `make requirements`)
- Docker operations (`make docker-build`, `make docker-up`, `make docker-logs`)
- Testing (`make test`, `make test-simulation`)
- Code quality (`make lint`, `make format`)
- Information (`make help`, `make info`)

**Completed:**
1. ✅ Build simulation test script (`test_two_agent_simulation.py`)
2. ✅ Build production batch runners (sequential and async)
3. ✅ Build mixed persona testing framework
4. ✅ Achieve 15x performance improvement with full parallelism (20 concurrent)
5. ✅ Test 60+ simulations across 5 workflow agents and 2 personas
6. ✅ Add seed_message tracking to JSON output
7. ✅ Optimize concurrency for maximum throughput

**Next Steps**:
1. Database integration: Store simulations in `simulation_runs` table
2. Automated evaluation: LLM-based quality scoring
3. Comparison dashboard: Side-by-side conversation analysis
4. CI/CD integration: Automated testing on agent updates
5. Continue PDF/DOCX → JSON content parsing (parallel track)
