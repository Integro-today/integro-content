# Evaluation Tools Documentation

## Overview

Tools for automated quality assessment of therapeutic conversation simulations. Evaluates workflow performance, Tegra voice adherence, content execution, and conversation quality.

---

## simulation-evaluator Subagent

**Type:** Claude Code custom subagent (invoked via Task tool)

**Purpose:** Autonomous batch evaluation of therapeutic conversation simulations

**Location:** `.claude/agents/simulation-evaluator.md`

**Output:** JSON analysis reports saved alongside simulation files

### When to Use (Proactive)

- ✅ After batch simulation runs complete - automatically analyze all results
- ✅ When user mentions "evaluate", "analyze", or "assess" simulations
- ✅ Before deploying workflow changes to production
- ✅ When comparing different workflow versions (V5 vs V6)
- ✅ When user asks about simulation quality or Tegra voice adherence

### How to Invoke

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

### Evaluation Dimensions (scored 0-10)

1. **Tegra Voice Adherence (25%)** - Direct, plainspoken, no therapy-speak or stage directions
2. **Content Execution (25%)** - Teaching delivered, reflection questions covered, artifact created
3. **Persona Adaptation (20%)** - Adapted to user archetype (resistant, verbose, scattered, crisis)
4. **Conversation Flow (15%)** - Natural transitions, appropriate pacing, clear direction
5. **Completion Quality (15%)** - User articulated takeaway, natural ending, sense of accomplishment

### Output Files

- `[simulation_name]_analysis.json` - Detailed analysis with scores, violations, recommendations
- `roots_vX_batch_summary.json` - Aggregate statistics across all simulations
- `EVALUATION_SUMMARY.md` - Human-readable batch summary

### Example Output

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

### Recommendation Thresholds

- **≥ 8.0:** Approve for production
- **6.0-7.9:** Needs minor revisions
- **< 6.0:** Requires major changes

### Performance

- **Speed:** ~30-60 seconds per simulation
- **Batch:** Processes entire directories autonomously
- **Efficiency:** Works while you continue other tasks

### Example Invocations

**After batch testing:**
```
User: "The V6 batch test finished. 5 simulations complete."
Claude: "Great! Let me use the simulation-evaluator subagent to analyze all 5 simulations."
[Invokes Task tool with simulation-evaluator]
```

**Comparing versions:**
```
User: "I want to compare V5 and V6 performance."
Claude: "I'll use the simulation-evaluator to analyze both batch directories."
[Invokes Task tool twice - once for V5 directory, once for V6 directory]
```

**Pre-production validation:**
```
User: "Is the V6 workflow ready for production?"
Claude: "Let me evaluate the test simulations to verify production readiness."
[Invokes Task tool with simulation-evaluator]
```

---

## evaluate_simulation.py

**Purpose:** Workflow performance evaluation tool

**Updated:** 2025-10-22

### Features

- **Critical workflow analysis** - Evaluates ONLY the workflow agent (personas are test inputs)
- **Tegra voice audit** - Flags embellishment, excessive warmth, therapy-speak, verbosity
- **Content execution tracking** - Verifies all daily curriculum objectives were met
- **Actionable prompt fixes** - Provides EXACT text to add to workflow prompt with examples
- **Training-Free GRPO aligned** - Extracts what works and what doesn't for iterative improvement
- **Agent caching** - Save and reuse evaluation agents for improved efficiency

### Usage

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

### Output Structure

**Saves to:** `[simulation_name]_analysis.json` (alongside simulation file by default)

**Sections:**
- **Overall Assessment:** Quality score (0-10), completion status, therapeutic alliance rating
- **Highlights:** 3-10 moments that worked well (with turn IDs, quotes, principles extracted)
- **Lowlights:** 2-5 areas for improvement (with constructive suggestions)
- **Semantic Advantages:** 3-5 actionable principles extracted from successful moments
- **Prompt Improvements:** Specific recommendations with exact text to add to workflow prompt
- **Conversation Arc Analysis:** Opening/middle/closing quality assessment
- **Persona Handling:** How well agent adapted to persona archetype

### Evaluation Dimensions

1. **Tegra Voice Adherence** - Direct/plainspoken, grounded/steady, no embellishment or excessive warmth
2. **Content Execution** - Delivered core teaching, covered all activity questions, created artifact
3. **Conversation Flow** - Stayed on track, handled resistance, maintained efficiency
4. **Critical Violations** - Therapy-speak, stage directions, verbosity, taking over vs. empowering

### Example Analysis Output

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

### When to Use

- **Post-batch testing:** Evaluate all simulations after running batch tests
- **Workflow iteration:** Identify specific Tegra voice violations and content delivery failures
- **A/B comparison:** Compare V2 vs V3 workflow performance against Tegra standards
- **Prompt optimization:** Extract EXACT prompt fixes to improve workflow (Training-Free GRPO)
- **Pre-production validation:** Ensure workflow maintains Tegra voice and delivers curriculum

### Evaluator Philosophy

- **Critical, not validating** - Designed to find what's broken, not celebrate what worked
- **Workflow-focused** - Evaluates ONLY the workflow agent; personas are test inputs
- **Evidence-based** - Every critique includes turn IDs, quotes, and specific fixes
- **Actionable** - Provides exact prompt text to add, not vague suggestions

### Performance

- **Speed:** ~30-60 seconds per evaluation (LLM inference dominates, but agent setup is optimized with caching)
- **Cost:** ~$0.01-0.03 per evaluation (Groq/Moonshot Kimi-K2)
- **Model:** Uses `moonshotai/kimi-k2-instruct-0905` at temperature=0.3 for consistent analysis
- **Parallelizable:** Can run multiple evaluations concurrently
- **Efficiency:** Use `--save-agent` on first run, then `--agent-id` for subsequent runs to reuse cached agent

---

## Integration with Training-Free GRPO

Both evaluation tools support iterative prompt optimization:

### Workflow

1. **Run batch simulations** with current workflow version
2. **Evaluate each simulation** to extract semantic advantages
   - Use simulation-evaluator subagent for batch analysis
   - OR use evaluate_simulation.py for individual analysis
3. **Aggregate insights** across all personas
4. **Update workflow prompt** with learned principles
5. **Create V{N+1}** and re-test

### Training-Free GRPO Cycle

```
V{N} workflow → Batch test → Evaluate → Extract semantic advantages
    ↑                                                  ↓
    └──────────── Update prompt ← Aggregate insights ←┘
```

### Semantic Advantages

These are actionable principles extracted from successful moments:
- "Match persona communication style in LENGTH and TONE"
- "Ground intellectualizers in body early and often"
- "Close is sacred - after completion, 1 turn maximum then end"

**See also:**
- `/home/ben/integro-content/SIMULATION_EVALUATION_TOOL.md` - Full evaluation tool documentation
- `/home/ben/integro-content/Agents/Training_Free_GRPO_summarization.md` - Training-Free GRPO methodology

---

**Last Updated:** 2025-10-23
