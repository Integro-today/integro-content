# Training-Free Group Relative Policy Optimization (Training-Free GRPO)

**Research Paper**: [Training-Free Group Relative Policy Optimization](https://arxiv.org/html/2510.08191v1)
**Authors**: Tencent Youtu Lab (Yuzheng Cai, Siqi Cai, et al.)
**Published**: October 2025
**Relevance**: High - Directly applicable to improving Integro's agent simulation and optimization pipeline

---

## Executive Summary

**Training-Free GRPO** is a breakthrough method that improves LLM agent performance **without fine-tuning or parameter updates**. Instead of expensive gradient-based training, it learns from experience through **iterative self-reflection** and maintains a **knowledge base of best practices** that guides the agent during inference.

**Perfect for small companies because:**
- ✅ No GPU training infrastructure needed
- ✅ Works with just 50-200 training examples (vs. thousands for traditional RL)
- ✅ ~$18 to train vs. $10,000+ for fine-tuning
- ✅ Uses frozen API-based models (DeepSeek, OpenAI, Anthropic)
- ✅ Preserves generalization across domains
- ✅ No model deployment complexity

---

## The Problem with Traditional RL Fine-Tuning

Traditional approaches like GRPO, PPO, and other reinforcement learning methods require:

| Issue | Traditional RL | Training-Free GRPO |
|-------|---------------|-------------------|
| **Computational Cost** | 20,000+ GPU hours ($10,000+) | 2-3 hours API usage (~$18) |
| **Training Data** | Thousands of examples | 50-200 examples |
| **Infrastructure** | Dedicated GPU cluster | API calls only |
| **Deployment** | Custom model hosting | Use existing APIs |
| **Generalization** | Domain-specific (overfits) | Cross-domain (preserves generalization) |
| **Iteration Speed** | Days to retrain | Minutes to hours |
| **Parameter Updates** | Yes (risky, irreversible) | No (safe, reversible) |

**Key Insight**: The paper argues that LLMs already have the capability to perform well—they just need **experiential knowledge** to guide them, not parameter changes.

---

## Core Methodology: How It Works

### Traditional GRPO vs. Training-Free GRPO

**Traditional GRPO (Parameter Space Optimization):**
1. Generate multiple outputs (rollouts) for a query
2. Score each with a reward model
3. Calculate numerical advantages (which outputs are better)
4. Update model parameters via gradient descent
5. Repeat for many epochs

**Training-Free GRPO (Context Space Optimization):**
1. Generate multiple outputs (rollouts) for a query
2. Score each with a reward model (or ground truth)
3. **Ask the LLM to explain WHY some outputs are better (semantic advantage)**
4. **Distill insights into natural language "experiences"**
5. **Update an external knowledge base (not parameters)**
6. Inject knowledge base into future prompts
7. Repeat for 2-3 epochs

### The Key Innovation: Semantic Advantage

Instead of calculating `advantage[i] = reward[i] - mean(rewards)`, the system:

1. **Generates summaries** of each output's approach
2. **Compares rollouts** to identify what made successful ones work
3. **Extracts lessons** in natural language (e.g., "When solving geometry problems, always verify that computed coordinates satisfy all original constraints")
4. **Stores experiences** in a knowledge base
5. **Iteratively refines** the knowledge base (add/delete/modify/keep operations)

---

## Practical Implementation for Small Companies

Based on the paper's methodology and the practical steps diagram you shared:

### Step 1: Identify Target Tasks

**What to focus on:**
- Specific workflows where your agents struggle (e.g., "Intentions Workflow often misses emotional subtext")
- Domain-specific reasoning patterns (e.g., "therapeutic boundary-setting with manipulative personas")
- Tool integration challenges (e.g., "when to use memory retrieval vs. direct response")

**For Integro:**
- Therapeutic conversation quality with resistant personas (Paul)
- Handling verbose/analytical users who intellectualize (Ellen)
- Crisis detection and appropriate escalation (Sam Morrison persona)
- Managing prejudiced language while maintaining therapeutic alliance (Bobby Sullivan)

### Step 2: Collect a Small Ground-Truth Set

**Size**: 50-200 representative examples
**What you need**: Input query + desired output (or just a reward signal like correct/incorrect)

**For Integro:**
- Sample 100 conversations from your existing batch simulations
- Manually label 50-100 agent responses as "good" (therapeutic, appropriate) or "bad" (missed cues, broke boundaries, too directive)
- OR use specific success criteria:
  - Did the agent maintain boundaries? (yes/no)
  - Did it reflect emotion correctly? (yes/no)
  - Did it avoid giving advice? (yes/no)
  - Did it recognize crisis indicators? (yes/no)

**Example structure:**
```json
{
  "query": "Paul's terse message: 'Yeah whatever. Tried the breathing thing. Didn't work.'",
  "good_response": "Sounds like you gave it a shot but it didn't land for you. What happened when you tried it?",
  "bad_response": "The breathing exercise is scientifically proven to reduce anxiety. Try doing it for 10 minutes instead of 5.",
  "success_criteria": {
    "validates_experience": true,
    "avoids_prescriptive_advice": true,
    "invites_exploration": true
  }
}
```

### Step 3: Run a Training-Free GRPO Loop

**The paper's 4-step process** (can be scripted):

#### A. Generate Group of Rollouts

For each training input, generate **5-10 completions** (group size = 5-10):

```python
# For each training example
for query in training_set:
    rollouts = []
    for i in range(5):  # Group size = 5
        response = agent.run(
            message=query,
            knowledge_base=current_experiences  # Inject current experience library
        )
        rollouts.append(response)
```

#### B. Score Rollouts

Use either:
- **Ground truth comparison** (correctness check)
- **Simple reward model** (score 0-10 on therapeutic quality)
- **Rule-based scoring** (did it meet success criteria?)

```python
# Simple scoring example
def score_therapeutic_response(response, ground_truth_criteria):
    score = 0
    if validates_feeling(response): score += 1
    if avoids_advice(response): score += 1
    if maintains_boundaries(response): score += 1
    if reflects_emotion(response): score += 1
    return score

rewards = [score_therapeutic_response(r, criteria) for r in rollouts]
```

#### C. Summarize Semantic Advantage

**Prompt the same LLM** to introspect on what made successful rollouts better:

```python
# Only for groups with clear winners and losers (not all identical scores)
if len(set(rewards)) > 1:
    # Step 1: Generate individual summaries
    summaries = []
    for rollout in rollouts:
        summary_prompt = f"""
        Query: {query}
        Response: {rollout}

        Summarize the therapeutic approach taken in this response.
        Focus on: tone, technique, boundaries, emotional attunement.
        """
        summary = llm.generate(summary_prompt)
        summaries.append(summary)

    # Step 2: Extract semantic advantage
    experience_prompt = f"""
    Query: {query}

    Here are {len(rollouts)} different therapeutic responses with their scores:
    {format_rollouts_with_scores(rollouts, rewards, summaries)}

    Current experience library:
    {current_experiences}

    Analyze what made the high-scoring responses better.
    Extract 1-3 concise, actionable principles that explain their success.
    Format as bullet points.
    """

    semantic_advantage = llm.generate(experience_prompt)
```

#### D. Update Knowledge Base

**Ask the LLM to manage the experience library**:

```python
update_prompt = f"""
Current experience library:
{current_experiences}

New insights from this batch:
{all_semantic_advantages_from_batch}

Decide how to update the experience library. For each new insight, choose ONE:
1. ADD - This is a new, valuable principle to add
2. DELETE - This contradicts or obsoletes an existing experience (specify which)
3. MODIFY - This refines an existing experience (specify which and how)
4. KEEP - This is redundant with existing experiences

Output your decisions as structured operations.
"""

operations = llm.generate(update_prompt)
current_experiences = apply_operations(current_experiences, operations)
```

#### E. Repeat for 2-3 Epochs

The paper found **3 epochs** (3 passes through the training set) was optimal:
- **Epoch 1**: Discovers major patterns
- **Epoch 2**: Refines and consolidates
- **Epoch 3**: Fine-tunes edge cases

### Step 4: Inject Knowledge Base into Inference

**During production inference**, prepend the learned experiences:

```python
def agent_with_experiences(user_message, experience_library):
    enhanced_system_prompt = f"""
    You are a therapeutic integration guide for psychedelic experiences.

    **Learned Best Practices:**
    {experience_library}

    Apply these principles thoughtfully in your responses.

    {original_system_prompt}
    """

    return agent.run(
        message=user_message,
        system_prompt=enhanced_system_prompt
    )
```

### Step 5: Monitor & Iterate

**Track performance on a hold-out test set:**
- Evaluate on personas NOT in training set
- Compare metrics: therapeutic quality scores, boundary violations, crisis recognition rate
- When performance degrades, add new experiences from failure cases

---

## Key Findings from the Paper

### Performance Results

**Mathematical Reasoning (AIME 2024/2025 benchmarks):**
- Baseline (DeepSeek-V3.1 + ReAct): 80.0% / 67.9%
- **+ Training-Free GRPO**: 82.7% / 73.3% (+2.7% / +5.4%)
- Training data: Only 100 examples
- Training cost: ~$18
- Outperformed fine-tuned 32B models that cost $10,000+ to train

**Web Searching (WebWalkerQA):**
- Baseline: 63.2%
- **+ Training-Free GRPO**: 67.8% (+4.6%)

### Learning Dynamics Insights

From the paper's analysis (Figure 4):

1. **Steady improvement across epochs**: Each epoch consistently improves both training and test performance
2. **Efficiency gains**: Average tool calls decreased during training (agent learned shortcuts)
3. **Generalization**: Performance improved on out-of-domain test sets, not just training data
4. **Knowledge quality over quantity**: 100 examples with 3 epochs beat thousands of examples with traditional methods

### Ablation Study Results

The paper tested removing key components:

| Configuration | AIME24 | AIME25 | Insight |
|--------------|--------|--------|---------|
| Baseline (no experiences) | 80.0% | 67.9% | - |
| **Directly generated experiences** | 79.8% | 67.3% | ❌ Random experiences hurt performance |
| **No ground truth** (self-evaluation only) | 80.7% | 68.9% | ✅ Works but weaker |
| **No group comparison** (single rollout) | 80.4% | 69.3% | ❌ Group comparison is critical |
| **Full Training-Free GRPO** | 82.7% | 73.3% | ✅ All components matter |

**Critical lessons:**
- ⚠️ You can't just generate random "best practices" and inject them
- ✅ Ground truth labels significantly improve learning (but not strictly required)
- ✅ **Group comparison is essential** - comparing multiple rollouts reveals what works
- ✅ Iterative refinement (add/delete/modify) prevents knowledge base bloat

### Cross-Domain Generalization

**The killer advantage for small companies:**

Traditional fine-tuned models are domain-specific:
- ReTool (math-trained): 67.0% on math → **18.3% on web tasks** (catastrophic forgetting)
- MiroThinker (web-trained): 53.6% on web → **43.5% on math** (poor transfer)

**Training-Free GRPO preserves generalization:**
- Same frozen base model works across all domains
- Just swap the experience library based on task
- **No deployment complexity** - single API model handles everything

---

## Application to Integro Simulation System

### Current State Analysis

Your system already has **most infrastructure needed**:

✅ **Agent simulation framework** (`TwoAgentSimulation`)
✅ **Batch testing** (can run 100+ conversations easily)
✅ **Multiple personas** (12 diverse personas for testing)
✅ **JSON output** (structured conversation logs)
✅ **Markdown conversion** (human review of quality)

### What You're Missing (Easy Additions)

1. **Reward/scoring function** for therapeutic quality
2. **Experience library storage** (simple text file or DB field)
3. **Semantic advantage extraction** (prompt templates)
4. **Multi-rollout generation** (already possible, just need to run N times per query)

### Proposed Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Training Phase (One-Time Setup)                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Sample 100 conversations from existing sims         │
│  2. Label therapeutic quality (manual or rule-based)    │
│  3. For each training example:                          │
│     ├─ Generate 5 rollouts with current agent          │
│     ├─ Score each rollout (therapeutic quality)        │
│     ├─ Extract semantic advantage (LLM introspection)  │
│     └─ Update experience library                       │
│  4. Repeat for 3 epochs                                │
│                                                         │
│  Output: experience_library.md or DB field             │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│         Inference Phase (Production)                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Agent System Prompt = Base Prompt + Experience Library│
│                                                         │
│  User Message → Agent (with experiences) → Response    │
│                                                         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│         Monitoring Phase (Continuous)                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Run batch simulations against all personas         │
│  2. Track quality metrics (boundaries, empathy, etc.)  │
│  3. Identify failure cases                             │
│  4. Add failures to training set                       │
│  5. Re-run Training-Free GRPO (incremental update)     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Implementation Roadmap

**Phase 1: Proof of Concept (1-2 days)**
- [ ] Create `training_free_grpo.py` script
- [ ] Manually label 20 conversations as "good" or "bad"
- [ ] Implement group rollout generation (N=5)
- [ ] Implement simple scoring function
- [ ] Implement semantic advantage extraction (single prompt)
- [ ] Run 1 epoch, validate experience library makes sense

**Phase 2: Full Pipeline (3-5 days)**
- [ ] Expand to 100 labeled examples
- [ ] Implement experience library operations (add/delete/modify/keep)
- [ ] Run 3 epochs
- [ ] Test on hold-out personas (e.g., if trained on Paul/Ellen, test on Jamie)
- [ ] Measure improvement in therapeutic quality metrics

**Phase 3: Integration (2-3 days)**
- [ ] Store experience libraries in database (per workflow agent)
- [ ] Modify agent loader to inject experiences at runtime
- [ ] Create UI for reviewing/editing experience libraries
- [ ] Set up monitoring dashboard

**Phase 4: Continuous Improvement (Ongoing)**
- [ ] Weekly batch simulation runs
- [ ] Automatic flagging of low-quality conversations
- [ ] Monthly experience library updates
- [ ] A/B testing: agent with experiences vs. without

---

## Practical Tips for Small Companies

### 1. Start Small and Iterate

**Don't optimize prematurely:**
- Start with 20-50 examples, not 200
- Use simple scoring (binary good/bad), not complex reward models
- Run 1-2 epochs first, not 10
- Test on a single agent/workflow, not all 8

### 2. Use Cheap Models for Learning

**Training-Free GRPO doesn't require the best model for learning:**
- Use GPT-4o-mini or Claude 3.5 Haiku for semantic advantage extraction
- Reserve expensive models (o1, Claude 3.7 Sonnet) for production inference
- The experience library is what matters, not which model created it

### 3. Leverage Your Existing Simulations

**You have a goldmine of data:**
- Your `Agents/batch_simulations/` folder has 100+ conversations
- Use markdown files for human review and labeling
- Filter by persona to create specialized experience libraries
  - `experiences_resistant_users.md` (trained on Paul, Bobby)
  - `experiences_verbose_users.md` (trained on Ellen, Dr. Rebecca)
  - `experiences_crisis_situations.md` (trained on Sam, Jack)

### 4. Make Labeling Easy

**Don't overthink the reward model:**

```python
# Simple rule-based scoring
def score_response(response, persona_type):
    score = 0

    # Universal criteria
    if no_advice_giving(response): score += 1
    if validates_emotion(response): score += 1
    if open_ended_question(response): score += 1

    # Persona-specific criteria
    if persona_type == "resistant":
        if avoids_pushing(response): score += 1
        if meets_user_where_they_are(response): score += 1
    elif persona_type == "verbose":
        if gentle_redirection(response): score += 1
        if focuses_key_emotion(response): score += 1

    return score / max_possible_score
```

### 5. Version Control Your Experiences

**Treat experience libraries like code:**
```bash
experiences/
├── v1.0_baseline.md
├── v1.1_resistant_users.md
├── v1.2_crisis_handling.md
└── v2.0_integrated.md
```

**Track what works:**
- Git commit each version
- A/B test new versions against old
- Roll back if performance degrades

### 6. Validate Continuously

**The paper emphasizes hold-out testing:**
- Reserve 20% of personas for testing (never train on them)
- Run weekly batch simulations
- Track metrics over time:
  - Therapeutic alliance maintenance
  - Boundary violation rate
  - Crisis recognition accuracy
  - User satisfaction (if real users)

---

## Code Example: Minimal Implementation

Here's a simplified Python script based on the paper's methodology:

```python
# training_free_grpo.py
import json
from typing import List, Dict
from integro.agent import AgentLoader
from integro.config.storage import ConfigStorage

class TrainingFreeGRPO:
    def __init__(self, agent_id: str, base_model: str = "deepseek"):
        self.agent_id = agent_id
        self.base_model = base_model
        self.experience_library = []

    def generate_rollouts(self, query: str, n: int = 5) -> List[str]:
        """Generate N rollouts for a single query."""
        rollouts = []
        for i in range(n):
            response = self.agent.run(
                message=query,
                knowledge_base=self.format_experiences()
            )
            rollouts.append(response)
        return rollouts

    def score_rollout(self, rollout: str, ground_truth: Dict) -> float:
        """Simple rule-based scoring (replace with your criteria)."""
        score = 0
        if self.validates_emotion(rollout): score += 1
        if self.avoids_advice(rollout): score += 1
        if self.maintains_boundaries(rollout): score += 1
        if self.open_ended_question(rollout): score += 1
        return score / 4.0

    def extract_semantic_advantage(
        self,
        query: str,
        rollouts: List[str],
        scores: List[float]
    ) -> str:
        """Ask LLM to explain what made good rollouts better."""
        # Only process groups with variation in scores
        if len(set(scores)) == 1:
            return None

        prompt = f"""
        Query: {query}

        I generated {len(rollouts)} responses with these quality scores:
        """
        for i, (rollout, score) in enumerate(zip(rollouts, scores)):
            prompt += f"\n\nResponse {i+1} (score: {score}):\n{rollout}"

        prompt += f"""

        Current therapeutic principles I'm following:
        {self.format_experiences()}

        Analyze what made the high-scoring responses more therapeutically effective.
        Extract 1-3 concise, actionable principles.
        Format as bullet points.
        """

        semantic_advantage = self.llm_call(prompt)
        return semantic_advantage

    def update_experience_library(self, semantic_advantages: List[str]):
        """Ask LLM to update experience library."""
        prompt = f"""
        Current experience library:
        {self.format_experiences()}

        New insights from this training batch:
        {self.format_advantages(semantic_advantages)}

        For each new insight, decide:
        - ADD: New valuable principle
        - DELETE <index>: Contradicts existing principle #<index>
        - MODIFY <index>: Refines existing principle #<index>
        - KEEP: Already covered

        Output your decisions as JSON:
        [
          {{"action": "ADD", "principle": "..."}},
          {{"action": "MODIFY", "index": 2, "principle": "..."}},
          ...
        ]
        """

        operations = self.llm_call(prompt, response_format="json")
        self.apply_operations(operations)

    def train(self, training_data: List[Dict], epochs: int = 3):
        """Main training loop."""
        for epoch in range(epochs):
            print(f"\n=== Epoch {epoch + 1}/{epochs} ===")
            batch_advantages = []

            for example in training_data:
                query = example["query"]
                ground_truth = example["ground_truth"]

                # Generate group of rollouts
                rollouts = self.generate_rollouts(query, n=5)

                # Score each rollout
                scores = [self.score_rollout(r, ground_truth) for r in rollouts]

                # Extract semantic advantage
                advantage = self.extract_semantic_advantage(query, rollouts, scores)
                if advantage:
                    batch_advantages.append(advantage)

            # Update experience library after full batch
            self.update_experience_library(batch_advantages)

            print(f"Experience library now has {len(self.experience_library)} principles")

    def format_experiences(self) -> str:
        """Format experience library for injection into prompts."""
        if not self.experience_library:
            return "No learned experiences yet."

        formatted = "# Learned Therapeutic Principles\n\n"
        for i, exp in enumerate(self.experience_library, 1):
            formatted += f"{i}. {exp}\n"
        return formatted

# Usage example
if __name__ == "__main__":
    # Load training data
    training_data = [
        {
            "query": "Yeah whatever. Tried the breathing thing. Didn't work.",
            "ground_truth": {
                "validates_emotion": True,
                "avoids_prescriptive": True,
                "invites_exploration": True
            }
        },
        # ... 99 more examples
    ]

    # Initialize Training-Free GRPO
    grpo = TrainingFreeGRPO(agent_id="intentions_workflow_8")

    # Train for 3 epochs
    grpo.train(training_data, epochs=3)

    # Save experience library
    with open("experiences_intentions_workflow_8.md", "w") as f:
        f.write(grpo.format_experiences())
```

---

## Cost Analysis for Integro

Based on the paper's reported costs:

### Training Phase

**Assumptions:**
- 100 training examples
- 5 rollouts per example per epoch
- 3 epochs
- Average 500 tokens input, 200 tokens output per rollout

**Total tokens:**
- Rollout generation: 100 examples × 5 rollouts × 3 epochs × 700 tokens = 1,050,000 tokens
- Semantic advantage extraction: 100 examples × 3 epochs × 2,000 tokens = 600,000 tokens
- Experience library updates: 3 epochs × 10,000 tokens = 30,000 tokens
- **Total: ~1.7M tokens**

**Cost (using DeepSeek API):**
- Input: 1.2M tokens × $0.14/M = $0.17
- Output: 0.5M tokens × $0.28/M = $0.14
- **Total: ~$0.30**

**Even with GPT-4o:**
- Input: 1.2M tokens × $2.50/M = $3.00
- Output: 0.5M tokens × $10.00/M = $5.00
- **Total: ~$8.00**

### Inference Phase (Per Conversation)

**Additional cost per conversation:**
- Experience library: ~1,000 tokens (cached after first use)
- Marginal cost: $0.00014 per conversation with caching

**Effectively free in production.**

---

## Next Steps for Integro

### Immediate Actions (This Week)

1. **Create training dataset**:
   - Review 100 existing simulations from `Agents/batch_simulations/`
   - Label therapeutic quality (use rubric: validates emotion, avoids advice, maintains boundaries, etc.)
   - Store as JSON: `training_data/therapeutic_quality_100.json`

2. **Implement proof of concept**:
   - Copy the code example above
   - Run 1 epoch with 20 examples
   - Manually review generated experience library
   - Validate it makes therapeutic sense

3. **Test on hold-out persona**:
   - Run batch simulation with baseline agent (no experiences)
   - Run batch simulation with enhanced agent (with experiences)
   - Compare therapeutic quality scores

### Short-Term (Next 2 Weeks)

4. **Scale to full training set** (100 examples, 3 epochs)
5. **Create persona-specific experience libraries**:
   - `experiences_resistant_users.md` (Paul, Bobby, Jack)
   - `experiences_verbose_analytical.md` (Ellen, Dr. Rebecca, Aisha)
   - `experiences_crisis_risk.md` (Sam, Jack)
6. **Integrate into agent loader**:
   - Modify `AgentLoader` to inject experience library based on detected user type
   - Store experience libraries in database

### Long-Term (Next Month)

7. **Build monitoring dashboard**:
   - Automated batch testing (weekly)
   - Quality metric tracking over time
   - Experience library versioning
8. **Continuous improvement loop**:
   - Flag low-quality conversations automatically
   - Add to training set
   - Incremental experience library updates (monthly)

---

## Key Takeaways

1. **Training-Free GRPO is perfect for small companies** - no infrastructure, minimal cost, fast iteration

2. **You already have the data** - your existing simulations are a goldmine for training

3. **The magic is in semantic advantage** - asking the LLM "why was this better?" is more powerful than numerical scores

4. **Group comparison is critical** - comparing multiple rollouts reveals patterns that single-shot evaluation misses

5. **Iterative refinement matters** - 3 epochs with add/delete/modify operations produces better knowledge than single-pass extraction

6. **Generalization is preserved** - frozen model + swappable experience libraries beats specialized fine-tuned models

7. **Start simple, iterate fast** - 20 examples, 1 epoch, simple scoring gets you 80% of the value

---

## References

- **Paper**: [Training-Free Group Relative Policy Optimization](https://arxiv.org/html/2510.08191v1)
- **Code**: https://github.com/TencentCloudADP/youtu-agent/tree/training_free_GRPO
- **Related Work**:
  - ReAct: Synergizing reasoning and acting in LLMs
  - In-Context Reinforcement Learning (ICRL)
  - Agent KB: Cross-domain experience reuse

---

**Document Created**: 2025-10-17
**Author**: Claude (for Integro Content Team)
**Status**: Ready for implementation
