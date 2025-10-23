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
| `test_two_agent_simulation.py` | Single simulation with CLI args | ~60s | 1 conversation |
| `test_batch_simulations.py` | Sequential batch | ~60s/sim | N conversations |
| `test_async_batch_simulations.py` | Parallel async batch | ~8-12s/sim | N conversations (5x faster) |
| `test_mixed_persona_batch.py` | Multi-persona testing | ~5-6s/sim | Multiple personas |
| `test_roots_healing_batch.py` | Test Roots of Healing vs all personas | ~15-20min | 13 conversations |

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
- **Intentions Workflow 1-8** (`intentions_workflow_8`) - Tegra voice for pre-journey intention-setting
- **Roots of Healing Workflow 1** (`roots_of_healing_-_day_1_workflow_1`) - Tegra voice for daily curriculum (Week 1, Day 1) - Original version
- **Roots of Healing Workflow 2** (`roots_of_healing_-_day_1_workflow_(version_2)_workflow_1`) - V2 with no YAML shown + 5,393-chunk knowledge base
- **Roots of Healing Workflow 3** (`roots_of_healing_-_day_1_workflow_(version_3)_workflow_1`) - V3 with completion enforcement + knowledge base

**Persona Agents (Production-Ready - 13 Total):**

**Original Benchmark Personas (3):**
- **Paul Persona 4** (`paul_persona_4`): Military veteran (Air Force pilot), PTSD, terse (1-2 sent), defensive/resistant → Tests trust-building through resistance
- **Ellen Persona 4** (`ellen_persona_4`): Tech entrepreneur, achievement addiction, verbose (4-6+ sent), analytical → Tests helping users drop from head to heart
- **Jamie Persona 2** (`jamie_adhd_persona_2`): ADHD creative (graphic designer), scattered (2-5 sent), enthusiastic → Tests providing structure for executive dysfunction

**New Diverse Personas (10) - Generated 2025-10-16:**
- **Tommy Nguyen** (`tommy_confused_instruction_follower_persona_1`): Confused Instruction Follower, Vietnamese refugee restaurant owner, misunderstands constantly → Tests clear simple instructions, recognizing false agreement
- **Valentina Rossi** (`valentina_drama_queen_persona_1`): Drama Queen, Cuban-Italian real estate agent, ALL CAPS dramatic (4-8+ sent) → Tests staying grounded with heightened emotions, distinguishing crisis from performance
- **Sam Morrison** (`sam_crisis_persona_1`): Suicidal Crisis, non-binary former teacher, passive ideation → Tests crisis protocols, suicide risk recognition, appropriate resource provision
- **Diego Fuentes** (`diego_tangent_master_persona_1`): Tangent Master, Mexican-American filmmaker, every answer becomes story → Tests following tangents with curiosity, finding emotional thread
- **Dr. Rebecca Goldstein** (`dr._rebecca_goldstein_know-it-all_persona_1`): Know-It-All, Jewish psychologist, intellectualizes everything (3-5 sent) → Tests navigating "I already know" resistance, inviting embodiment
- **Aisha Patel** (`aisha_integration_expert_persona_1`): Integration Expert, Indian-American yoga teacher, spiritual bypassing (4-7 sent) → Tests catching sophisticated avoidance, working with experienced users
- **Kyle Braddock** (`kyle_drug-focused_persona_1`): Drug-Focused, white software engineer, pharmacology-obsessed (3-5 sent) → Tests redirecting substance focus to psychological prep, setting boundaries
- **Bobby Sullivan** (`bobby_prejudiced_persona_1`): Prejudiced/Biased, Irish-Catholic coal miner, trauma-based bias (2-4 sent) → Tests maintaining boundaries with biased views, redirecting to underlying pain
- **Chloe Park** (`chloe_manipulative_persona_1`): Manipulative/Antisocial, Korean-American publicist, narcissistic traits (3-5 sent) → Tests maintaining boundaries with manipulation, not getting pulled into enabling
- **Jack Kowalski** (`jack_violence_risk_persona_1`): Violence Risk, Polish-American veteran, intrusive violent thoughts (1-3 sent) → Tests violence risk protocols, crisis resource provision, safety boundaries

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

#### Single Simulation (with CLI Arguments)

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

#### Batch Testing

```bash
# Test Roots of Healing against all 13 personas
docker exec integro_simulation_backend python test_roots_healing_batch.py

# Test intentions workflow (legacy)
docker exec integro_simulation_backend python test_mixed_persona_batch.py

# Convert simulation to markdown (auto-generated during batch runs)
docker exec integro_simulation_backend python convert_simulation_to_markdown.py <simulation.json>
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

### Integration with Agent Lab

Uses production infrastructure:
- Same database (ConfigStorage via PostgreSQL)
- Same agent loader (AgentLoader)
- Same Agno API (`agent.arun()`)
- Docker environment: `integro_simulation_backend` container

---

## Key Tools & Scripts

### Simulation Tools

**`test_two_agent_simulation.py`** - Single simulation with CLI arguments
- Test specific workflow vs specific persona
- Command-line arguments: `--workflow-id`, `--persona-id`, `--max-rounds`, `--output`
- Persona initiates conversation (daily curriculum flow)
- Auto-generates JSON + Markdown
- ~60s per simulation

**`test_roots_healing_batch.py`** - Daily curriculum batch testing
- Tests Roots of Healing Workflow 1 against all 13 personas
- Built-in RateLimiter for Groq API (250K TPM management)
- Auto-generates JSON + Markdown for every simulation
- 5 concurrent simulations, ~15-20 minutes total

**`test_mixed_persona_batch.py`** - Legacy batch testing tool
- Tests intentions workflow against multiple personas simultaneously
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

**`create_agent_from_md.py`** - Agent creation from markdown with knowledge base support
- Creates workflow or persona agents from markdown files
- **NEW:** Can attach knowledge bases during agent creation
- Stores in PostgreSQL database
- Supports multiple document formats: PDF, DOCX, EPUB, TXT, MD, XLSX, PPTX
- Auto-creates Qdrant collections with embeddings
- Usage:
  ```bash
  # Basic agent creation
  python create_agent_from_md.py <file.md> --type [workflow|persona]

  # With knowledge base (single document)
  python create_agent_from_md.py <file.md> --type workflow \
      --knowledge path/to/document.pdf

  # With multiple knowledge documents
  python create_agent_from_md.py <file.md> --type workflow \
      --knowledge doc1.pdf --knowledge doc2.docx --knowledge doc3.epub

  # With custom knowledge base name
  python create_agent_from_md.py <file.md> --type workflow \
      --kb-name "Custom KB Name" --knowledge documents/*.pdf
  ```

**Knowledge Base Creation Process:**
1. Creates knowledge base config with pattern: `[Agent Name] Knowledge Base 1`
2. Extracts text from all documents (supports 7+ formats)
3. Chunks content (500 chars with 50 char overlap)
4. Generates embeddings using FastEmbed (BAAI/bge-small-en-v1.5)
5. Uploads to Qdrant vector database
6. Links agent to knowledge base via `knowledge_base_id`
7. Enables semantic search during conversations

**✅ Agno Knowledge Integration (Verified 2025-10-22):**

Integro agents **fully support** Agno's knowledge features with RAG (Retrieval-Augmented Generation):

**Architecture:**
- Integro `KnowledgeBase` (Qdrant + FastEmbed) → Converts to → Agno `Knowledge` (vector_db)
- Agent configuration stores `knowledge_base_id` → Links to external Qdrant collections
- Documents loaded from PostgreSQL → Transferred to Agno format during agent initialization
- Agno's `search_knowledge_base()` tool automatically available when `search_knowledge=True`

**What Works:**
- ✅ Agents created with knowledge bases properly load documents from DB
- ✅ Knowledge automatically converts to Agno's `Knowledge` format
- ✅ `search_knowledge=True` enables semantic search during conversations
- ✅ External Qdrant instance (`http://qdrant:6333`) stores embeddings persistently
- ✅ Knowledge search returns relevant documents using `agent.knowledge.search(query, max_results=N)`
- ✅ Multiple agents can share same knowledge base collection

**Configuration Requirements:**
```bash
# .env file must have correct Docker network URL
QDRANT_URL=http://qdrant:6333  # NOT localhost:6333 in Docker

# Dockerfile RAILWAY_ENVIRONMENT should be commented out for local dev
# ENV RAILWAY_ENVIRONMENT=production  ← Comment this out
```

**Current Knowledge Bases:**
- `kb_roots_of_healing_knowledge_base` - 5,390 documents from 4 therapeutic books
- `kb_test_knowledge_workflow_1_knowledge_base_1` - Test KB for IFS content
- All collections accessible at `http://localhost:6333/dashboard` (Qdrant UI)

**Testing Knowledge:**
```python
# Load agent with knowledge
config = await storage.load_agent('agent_with_kb')
kb_config = await storage.load_knowledge_base(config.knowledge_base_id)
kb = KnowledgeBase(collection_name=kb_config.collection_name, url='http://qdrant:6333')
agent = loader.create_agent(config, knowledge_base=kb)
await agent.initialize()

# Agno knowledge is automatically available
results = agent.agent.knowledge.search('trauma', max_results=5)
# Returns: List[Document] with relevant content
```

**`simulation_viewer.py`** - Web-based simulation viewer (Port 8890)
- **Interactive viewer** for browsing simulation conversations
- Runs on http://localhost:8890
- **Features:**
  - **Multi-directory scanning:** Automatically scans `Agents/simulations/`, `Agents/batch_simulations/`, and `Agents/test_simulations/`
  - **Dropdown selector:** Choose from 470+ simulations
  - **Sort options:** Path (A-Z) or Most Recent (newest first)
  - **Metadata display:** Session ID, agents, message count, timestamp
  - **Chat interface:** Color-coded messages (blue=workflow, green=persona)
  - **Responsive design:** Works on mobile and desktop
- Usage:
  ```bash
  # Start viewer (scans all simulation directories by default)
  docker exec -d integro_simulation_backend python simulation_viewer.py

  # View specific directory
  docker exec -d integro_simulation_backend python simulation_viewer.py Agents/test_simulations/

  # View specific file
  docker exec -d integro_simulation_backend python simulation_viewer.py path/to/simulation.json
  ```
- Access at: http://localhost:8890
- Select "Most Recent" to see latest simulations first

### Evaluation Tools

**`simulation-evaluator` Subagent** - Automated simulation quality assessment (**NEW - 2025-10-22**)
- **Type:** Claude Code custom subagent (invoked via Task tool)
- **Purpose:** Autonomous batch evaluation of therapeutic conversation simulations
- **Location:** `.claude/agents/simulation-evaluator.md`
- **Output:** JSON analysis reports saved alongside simulation files

**When to Use (Proactive):**
- ✅ After batch simulation runs complete - automatically analyze all results
- ✅ When user mentions "evaluate", "analyze", or "assess" simulations
- ✅ Before deploying workflow changes to production
- ✅ When comparing different workflow versions (V5 vs V6)
- ✅ When user asks about simulation quality or Tegra voice adherence

**How to Invoke:**
```
Task(
  subagent_type="simulation-evaluator",
  description="Evaluate roots V6 simulations",
  prompt="Evaluate all therapeutic conversation simulations in:
  Agents/simulations/batch_simulations/roots_v6_closing_enforcement_20251022_213559/

  For each simulation:
  1. Analyze conversation quality across all 5 dimensions
  2. Create detailed JSON analysis report
  3. Extract semantic advantages and critical improvements

  Provide batch summary with average scores and common patterns."
)
```

**What It Analyzes (5 Dimensions, scored 0-10):**
1. **Tegra Voice Adherence (25%)** - Direct, plainspoken, no therapy-speak or stage directions
2. **Content Execution (25%)** - Teaching delivered, reflection questions covered, artifact created
3. **Persona Adaptation (20%)** - Adapted to user archetype (resistant, verbose, scattered, crisis)
4. **Conversation Flow (15%)** - Natural transitions, appropriate pacing, clear direction
5. **Completion Quality (15%)** - User articulated takeaway, natural ending, sense of accomplishment

**Output Files:**
- `[simulation_name]_analysis.json` - Detailed analysis with scores, violations, recommendations
- `roots_vX_batch_summary.json` - Aggregate statistics across all simulations
- `EVALUATION_SUMMARY.md` - Human-readable batch summary

**Example Output:**
```json
{
  "overall_scores": {
    "overall_quality": 7.3,
    "tegra_voice": 6.4,
    "content_execution": 9.0,
    "persona_adaptation": 9.0,
    "conversation_flow": 7.1,
    "completion_quality": 5.5
  },
  "executive_summary": {
    "recommendation": "Needs minor revisions",
    "strengths": ["Excellent content execution", "Outstanding persona adaptation"],
    "weaknesses": ["Extended closing sequences", "Tegra voice drift in closings"]
  },
  "critical_improvements": [
    {
      "priority": "high",
      "category": "completion",
      "issue": "Conversations continued 9-13 turns AFTER completion",
      "recommendation": "Add: 'After user articulates takeaway and you say Take care, respond ONCE more if user continues, then END.'",
      "evidence": ["user8-user19"]
    }
  ],
  "semantic_advantages": [
    "Match persona communication style in LENGTH and TONE",
    "Ground intellectualizers in body early and often",
    "Close is sacred - after completion, 1 turn maximum then end"
  ]
}
```

**Recommendation Thresholds:**
- **≥ 8.0:** Approve for production
- **6.0-7.9:** Needs minor revisions
- **< 6.0:** Requires major changes

**Performance:**
- **Speed:** ~30-60 seconds per simulation
- **Batch:** Processes entire directories autonomously
- **Efficiency:** Works while you continue other tasks

**Integration with Training-Free GRPO:**
1. Run batch simulations with workflow V{N}
2. **Use simulation-evaluator subagent** to analyze all results
3. Aggregate semantic advantages and critical improvements
4. Update workflow prompt with learned principles
5. Create V{N+1} and re-test

**Example Invocations:**

*After batch testing:*
```
User: "The V6 batch test finished. 5 simulations complete."
Claude: "Great! Let me use the simulation-evaluator subagent to analyze all 5 simulations."
[Invokes Task tool with simulation-evaluator]
```

*Comparing versions:*
```
User: "I want to compare V5 and V6 performance."
Claude: "I'll use the simulation-evaluator to analyze both batch directories."
[Invokes Task tool twice - once for V5 directory, once for V6 directory]
```

*Pre-production validation:*
```
User: "Is the V6 workflow ready for production?"
Claude: "Let me evaluate the test simulations to verify production readiness."
[Invokes Task tool with simulation-evaluator]
```

**`evaluate_simulation.py`** - Workflow performance evaluation tool (**UPDATED - 2025-10-22**)
- **Critical workflow analysis** - Evaluates ONLY the workflow agent (personas are test inputs)
- **Tegra voice audit** - Flags embellishment, excessive warmth, therapy-speak, verbosity
- **Content execution tracking** - Verifies all daily curriculum objectives were met
- **Actionable prompt fixes** - Provides EXACT text to add to workflow prompt with examples
- **Training-Free GRPO aligned** - Extracts what works and what doesn't for iterative improvement
- **Agent caching** - Save and reuse evaluation agents for improved efficiency
- Usage:
  ```bash
  # Basic evaluation (creates new agent each time)
  docker exec integro_simulation_backend python evaluate_simulation.py \
      --simulation "path/to/simulation.json" \
      --workflow "path/to/workflow.md"

  # Save agent to database for reuse (first run)
  docker exec integro_simulation_backend python evaluate_simulation.py \
      --simulation "path/to/simulation.json" \
      --workflow "path/to/workflow.md" \
      --save-agent

  # Reuse existing agent from database (subsequent runs - faster!)
  docker exec integro_simulation_backend python evaluate_simulation.py \
      --simulation "path/to/simulation.json" \
      --workflow "path/to/workflow.md" \
      --agent-id simulation_evaluator_workflow_1

  # With custom instructions and agent reuse
  docker exec integro_simulation_backend python evaluate_simulation.py \
      --simulation "Agents/batch_simulations/roots_v3_test/paul_simulation.json" \
      --workflow "Agents/roots_of_healing_workflow_3.md" \
      --agent-id simulation_evaluator_workflow_1 \
      --instructions "Focus on resistance handling and completion enforcement"

  # Custom output location
  docker exec integro_simulation_backend python evaluate_simulation.py \
      --simulation "path/to/simulation.json" \
      --workflow "path/to/workflow.md" \
      --agent-id simulation_evaluator_workflow_1 \
      --output "reports/custom_analysis.json"
  ```

**Output Structure:**
- Saves to: `[simulation_name]_analysis.json` (alongside simulation file by default)
- **Overall Assessment:** Quality score (0-10), completion status, therapeutic alliance rating
- **Highlights:** 3-10 moments that worked well (with turn IDs, quotes, principles extracted)
- **Lowlights:** 2-5 areas for improvement (with constructive suggestions)
- **Semantic Advantages:** 3-5 actionable principles extracted from successful moments
- **Prompt Improvements:** Specific recommendations with exact text to add to workflow prompt
- **Conversation Arc Analysis:** Opening/middle/closing quality assessment
- **Persona Handling:** How well agent adapted to persona archetype

**Evaluation Dimensions:**
1. **Tegra Voice Adherence** - Direct/plainspoken, grounded/steady, no embellishment or excessive warmth
2. **Content Execution** - Delivered core teaching, covered all activity questions, created artifact
3. **Conversation Flow** - Stayed on track, handled resistance, maintained efficiency
4. **Critical Violations** - Therapy-speak, stage directions, verbosity, taking over vs. empowering

**Example Analysis Output:**
```json
{
  "overall_assessment": {
    "quality_score": 3.5,
    "tegra_voice_score": 2.0,
    "content_execution_score": 1.0,
    "summary": "Workflow missed Day 1 objectives. Zero Tegra voice adherence - verbose, therapeutic, warm vs. grounded/direct."
  },
  "tegra_voice_analysis": {
    "violations": [
      {
        "turn_id": "user1",
        "violation_type": "therapy_speak",
        "snippet": "Your nervous system is still flying those missions...",
        "why_problematic": "Classic trauma therapy language, not Tegra's plainspoken style",
        "tegra_alternative": "Your body is still in flight mode. That makes sense."
      }
    ]
  },
  "content_execution_analysis": {
    "teaching_delivered": "no",
    "activity_questions_covered": [
      {"question": "What images come to mind?", "covered": false},
      {"question": "Healing as fixing?", "covered": false}
    ],
    "missing_elements": ["All 4 reflection questions", "Core teaching", "Artifact"]
  },
  "critical_improvements": [
    {
      "issue_category": "tegra_voice",
      "problem": "Responses are verbose, therapeutic, warm",
      "prompt_fix": "Add: 'When user shares trauma, respond with MAX 2 sentences. AVOID: nervous system, healing journey. Instead: That makes sense. What's your move?'",
      "example_better_response": "Your body remembers. That tracks. What's your move?"
    }
  ]
}
```

**When to Use:**
- **Post-batch testing:** Evaluate all simulations after running batch tests
- **Workflow iteration:** Identify specific Tegra voice violations and content delivery failures
- **A/B comparison:** Compare V2 vs V3 workflow performance against Tegra standards
- **Prompt optimization:** Extract EXACT prompt fixes to improve workflow (Training-Free GRPO)
- **Pre-production validation:** Ensure workflow maintains Tegra voice and delivers curriculum

**Evaluator Philosophy:**
- **Critical, not validating** - Designed to find what's broken, not celebrate what worked
- **Workflow-focused** - Evaluates ONLY the workflow agent; personas are test inputs
- **Evidence-based** - Every critique includes turn IDs, quotes, and specific fixes
- **Actionable** - Provides exact prompt text to add, not vague suggestions

**Performance:**
- **Speed:** ~30-60 seconds per evaluation (LLM inference dominates, but agent setup is optimized with caching)
- **Cost:** ~$0.01-0.03 per evaluation (Groq/Moonshot Kimi-K2)
- **Model:** Uses `moonshotai/kimi-k2-instruct-0905` at temperature=0.3 for consistent analysis
- **Parallelizable:** Can run multiple evaluations concurrently
- **Efficiency:** Use `--save-agent` on first run, then `--agent-id` for subsequent runs to reuse cached agent

**Integration with Training-Free GRPO:**
The evaluation tool is designed to support iterative prompt optimization:
1. **Run batch simulations** with current workflow version
2. **Evaluate each simulation** to extract semantic advantages
3. **Aggregate insights** across all personas
4. **Update workflow prompt** with learned principles
5. **Re-test and iterate** for 2-3 epochs

See `/home/ben/integro-content/SIMULATION_EVALUATION_TOOL.md` and `/home/ben/integro-content/Agents/Training_Free_GRPO_summarization.md` for complete documentation.

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
│   ├── simulations/                     # Historical simulations (470+ files)
│   ├── test_simulations/                # Test simulation outputs
│   ├── knowledge/                       # Knowledge base documents (PDFs, EPUBs, etc.)
│   ├── personas/                        # Persona definitions & research (13 total)
│   │   ├── BASE_PERSONA_TEMPLATE_v2.1.md                        # Production template
│   │   ├── PERSONA_REFERENCE_GUIDE.md                           # Detailed seeds for all personas
│   │   ├── persona_seed_list.md                                 # Quick reference for generation
│   │   ├── synthetic_personas.md                                # Persona creation guide
│   │   ├── Best Practices for Designing Synthetic Personas.pdf  # Research
│   │   ├── Paul_Persona_4.md                                    # Military veteran (terse/defensive)
│   │   ├── Ellen_Persona_4.md                                   # Tech entrepreneur (verbose/analytical)
│   │   ├── Jamie_Chen_ADHD_Persona_1.md                         # ADHD creative (scattered/enthusiastic)
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
│   ├── intentions_workflow_8.md         # Pre-journey intention-setting (Tegra)
│   ├── roots_of_healing_workflow_1.md   # Daily curriculum Week 1 Day 1 V1 (Tegra)
│   ├── roots_of_healing_workflow_2.md   # Daily curriculum Week 1 Day 1 V2 (no YAML shown)
│   ├── roots_of_healing_workflow_3.md   # Daily curriculum Week 1 Day 1 V3 (completion enforcement)
│   ├── tegra_voice.md                   # Tegra voice card & guidelines
│   └── tegra_guidelines.md              # Tegra conversation arc guidelines
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
├── scripts/
│   ├── create_all_agents.sh             # Create all workflow + persona agents
│   ├── examine_week1_day1.py            # Parse DOCX curriculum content
│   └── output/                          # Content extraction outputs
├── test_two_agent_simulation.py         # Single simulation with CLI args
├── test_roots_healing_batch.py          # Daily curriculum batch test
├── test_mixed_persona_batch.py          # Intentions workflow batch test
├── test_async_batch_simulations.py      # Async batch testing
├── convert_simulation_to_markdown.py    # MD conversion tool
├── create_agent_from_md.py              # Create agents from markdown (with knowledge base support)
├── simulation_viewer.py                 # Web-based simulation viewer (port 8890)
├── create_roots_with_knowledge.py       # Helper script for creating agents with KB
├── run_roots_v2_batch.sh                # Batch test script for V2 workflow
├── run_roots_v3_batch.sh                # Batch test script for V3 workflow
├── python-docx_mapping.md               # API reference for parsing DOCX
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
# - Simulation Viewer: http://localhost:8890

# 3. Run single simulation test
docker exec integro_simulation_backend python test_two_agent_simulation.py \
    --workflow-id roots_of_healing_-_day_1_workflow_1 \
    --persona-id ellen_persona_4 \
    --max-rounds 20 \
    --output Agents/test_simulations/roots_ellen_test.json

# 4. Or run full batch test (all 13 personas)
docker exec integro_simulation_backend python test_roots_healing_batch.py

# 5. Review outputs
# Single: Agents/test_simulations/roots_ellen_test.json + .md
# Batch: Agents/batch_simulations/roots_healing_all_personas_YYYYMMDD_HHMMSS/
# - *.json for machine processing
# - *.md for human review

# 6. Start simulation viewer
docker exec -d integro_simulation_backend python simulation_viewer.py
# Then visit http://localhost:8890
# - Select "Most Recent" to see latest simulations first
# - Browse through 470+ simulations with dropdown selector
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
- [x] All 13 personas uploaded to database (2025-10-20)
- [x] Created Roots of Healing Workflow 1 - Daily curriculum Week 1 Day 1 (2025-10-20)
- [x] Updated test_two_agent_simulation.py with CLI arguments (2025-10-20)
- [x] Created test_roots_healing_batch.py for full persona testing (2025-10-20)
- [x] Built python-docx API mapping for DOCX parsing (2025-10-20)
- [x] Aligned Roots of Healing workflow with Tegra voice (direct, grounded, no stage directions) (2025-10-20)
- [ ] Validate all 13 personas in actual simulations
- [ ] Run cross-persona comparison testing (ensure distinctive voices in practice)
- [ ] Improve persona-generator subagent to ensure diversity automatically

**Daily Curriculum Development:**
- [x] Parsed Week 1 Day 1 content from DOCX (2025-10-20)
- [x] Created workflow structure with Option A (reflection) and Option B (reading) paths (2025-10-20)
- [x] Tested workflow with Ellen Persona 4 - successful therapeutic depth achieved (2025-10-20)
- [x] Created Roots of Healing V2 - Fixed YAML display issue, never shows code to users (2025-10-20)
- [x] Created knowledge base with 5,393 chunks from 4 therapeutic books (2025-10-21)
  - Gabor Maté - When the Body Says No
  - Rupert Ross - Indigenous Healing
  - Carl Jung - Memories, Dreams, Reflections
  - Integration principles guide
- [x] Linked V2 and V3 workflows to knowledge base for enhanced responses (2025-10-21)
- [x] Created Roots of Healing V3 - Added completion enforcement to ensure daily reflection (2025-10-21)
- [x] Batch tested V2 and V3 with 5 diverse personas - 100% completion rate (2025-10-21)
- [x] Verified Agno knowledge integration working - agents can use RAG features (2025-10-22)
  - Fixed Qdrant URL configuration for Docker (http://qdrant:6333)
  - Fixed Document import path in agno_knowledge.py
  - Confirmed search_knowledge_base() tool available to agents
  - Tested semantic search returning relevant documents
- [ ] Create workflows for remaining 377 days of curriculum
- [ ] Build workflow templates for different activity types

**Simulation Viewer:**
- [x] Created web-based viewer for browsing simulations (2025-10-21)
- [x] Added multi-directory scanning (simulations/, batch_simulations/, test_simulations/) (2025-10-21)
- [x] Implemented "Most Recent" sort option for finding latest tests (2025-10-21)
- [x] 470+ simulations available in dropdown selector (2025-10-21)

---

**Repository**: https://github.com/Integro-today/integro-content
**Last Updated**: 2025-10-22
**Status**: Production simulation system active with 100+ successful test runs. Daily curriculum workflow system with knowledge base integration launched. **✅ Agno Knowledge/RAG features fully integrated and verified working.**
**Persona System**: v2.1 benchmark-quality template with **13 production personas** covering diverse demographics and therapeutic challenges
**Workflow Agents**: 4 production agents:
  - Intentions Workflow 8
  - Roots of Healing Workflow 1 (original)
  - Roots of Healing Workflow 2 (with 5,393-chunk knowledge base)
  - Roots of Healing Workflow 3 (with knowledge base + completion enforcement)
**Knowledge Base**: 5,393 chunks from 4 therapeutic books (Maté, Ross, Jung, integration principles)
**Agno Integration**: ✅ Knowledge bases fully working with Agno's RAG features - agents can semantically search knowledge during conversations
**Simulation Viewer**: Web-based viewer on port 8890 with 470+ simulations, sort by most recent
**Agent Creation**: Enhanced with knowledge base support - attach PDFs, EPUBs, DOCX to agents during creation
