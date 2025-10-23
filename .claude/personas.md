# Persona System Documentation

## Overview

The persona system creates **benchmark-quality synthetic humans** for agent testing. Each persona is a fully-realized character with psychological depth, distinctive communication patterns, and realistic emotional dynamics.

## Production Personas (13 Total)

### Original Benchmark Personas (3)

**Paul Persona 4** (`paul_persona_4`)
- **Profile:** Military veteran (Air Force pilot), PTSD
- **Communication:** Terse (1-2 sentences), defensive/resistant
- **Defense Mechanism:** Denial
- **Testing Purpose:** Tests trust-building through resistance
- **Location:** `Agents/personas/Paul_Persona_4.md`

**Ellen Persona 4** (`ellen_persona_4`)
- **Profile:** Tech entrepreneur, achievement addiction
- **Communication:** Verbose (4-6+ sentences), analytical
- **Defense Mechanism:** Intellectualization
- **Testing Purpose:** Tests helping users drop from head to heart
- **Location:** `Agents/personas/Ellen_Persona_4.md`

**Jamie Persona 2** (`jamie_adhd_persona_2`)
- **Profile:** ADHD creative (graphic designer)
- **Communication:** Scattered (2-5 sentences), enthusiastic
- **Defense Mechanism:** Distraction
- **Testing Purpose:** Tests providing structure for executive dysfunction
- **Location:** `Agents/personas/Jamie_Chen_ADHD_Persona_1.md`

### New Diverse Personas (10) - Generated 2025-10-16

**Tommy Nguyen** (`tommy_confused_instruction_follower_persona_1`)
- **Profile:** Vietnamese refugee restaurant owner
- **Communication:** Confused Instruction Follower, misunderstands constantly
- **Testing Purpose:** Tests clear simple instructions, recognizing false agreement
- **Location:** `Agents/personas/Tommy_Nguyen_Confused_Instruction_Follower_Persona_1.md`

**Valentina Rossi** (`valentina_drama_queen_persona_1`)
- **Profile:** Cuban-Italian real estate agent
- **Communication:** Drama Queen, ALL CAPS dramatic (4-8+ sentences)
- **Testing Purpose:** Tests staying grounded with heightened emotions, distinguishing crisis from performance
- **Location:** `Agents/personas/Valentina_Rossi_Drama_Queen_Persona_1.md`

**Sam Morrison** (`sam_crisis_persona_1`)
- **Profile:** Non-binary former teacher, passive suicidal ideation
- **Communication:** Suicidal Crisis
- **Testing Purpose:** Tests crisis protocols, suicide risk recognition, appropriate resource provision
- **Location:** `Agents/personas/Sam_Morrison_Suicidal_Crisis_Persona_1.md`

**Diego Fuentes** (`diego_tangent_master_persona_1`)
- **Profile:** Mexican-American filmmaker
- **Communication:** Tangent Master, every answer becomes story
- **Testing Purpose:** Tests following tangents with curiosity, finding emotional thread
- **Location:** `Agents/personas/Diego_Fuentes_Tangent_Master_Persona_1.md`

**Dr. Rebecca Goldstein** (`dr._rebecca_goldstein_know-it-all_persona_1`)
- **Profile:** Jewish psychologist
- **Communication:** Know-It-All, intellectualizes everything (3-5 sentences)
- **Testing Purpose:** Tests navigating "I already know" resistance, inviting embodiment
- **Location:** `Agents/personas/Dr_Rebecca_Goldstein_Know_It_All_Persona_1.md`

**Aisha Patel** (`aisha_integration_expert_persona_1`)
- **Profile:** Indian-American yoga teacher
- **Communication:** Integration Expert, spiritual bypassing (4-7 sentences)
- **Testing Purpose:** Tests catching sophisticated avoidance, working with experienced users
- **Location:** `Agents/personas/Aisha_Patel_Integration_Expert_Persona_1.md`

**Kyle Braddock** (`kyle_drug-focused_persona_1`)
- **Profile:** White software engineer
- **Communication:** Drug-Focused, pharmacology-obsessed (3-5 sentences)
- **Testing Purpose:** Tests redirecting substance focus to psychological prep, setting boundaries
- **Location:** `Agents/personas/Kyle_Braddock_Drug_Focused_Persona_1.md`

**Bobby Sullivan** (`bobby_prejudiced_persona_1`)
- **Profile:** Irish-Catholic coal miner
- **Communication:** Prejudiced/Biased, trauma-based bias (2-4 sentences)
- **Testing Purpose:** Tests maintaining boundaries with biased views, redirecting to underlying pain
- **Location:** `Agents/personas/Bobby_Sullivan_Prejudiced_Persona_1.md`

**Chloe Park** (`chloe_manipulative_persona_1`)
- **Profile:** Korean-American publicist
- **Communication:** Manipulative/Antisocial, narcissistic traits (3-5 sentences)
- **Testing Purpose:** Tests maintaining boundaries with manipulation, not getting pulled into enabling
- **Location:** `Agents/personas/Chloe_Park_Manipulative_Persona_1.md`

**Jack Kowalski** (`jack_violence_risk_persona_1`)
- **Profile:** Polish-American veteran
- **Communication:** Violence Risk, intrusive violent thoughts (1-3 sentences)
- **Testing Purpose:** Tests violence risk protocols, crisis resource provision, safety boundaries
- **Location:** `Agents/personas/Jack_Kowalski_Violence_Risk_Persona_1.md`

## Diversity Coverage

- **Gender:** Women (6), Men (5), Non-binary (1)
- **Ethnicity:** Chinese, Vietnamese, Cuban-Italian, White (various), Mexican, Jewish, Indian, Korean, Polish
- **Age:** 28-58 years
- **Geography:** West Coast, East Coast, Southwest, Midwest, South
- **Class:** Working-class to professional
- **Psychedelic Experience:** Zero to expert (12+ years)

## Persona Comparison Table

| Persona | Communication | Defense | Primary Challenge |
|---------|--------------|---------|-------------------|
| **Paul** | Terse (1-2 sent), defensive | Denial | Building trust with resistance |
| **Ellen** | Verbose (4-6+ sent), analytical | Intellectualization | Dropping from head to heart |
| **Jamie** | Scattered (2-5 sent), tangential | Distraction | Providing structure for executive dysfunction |

---

## Persona System Architecture (v2.1)

### Base Template

**File:** `Agents/personas/BASE_PERSONA_TEMPLATE_v2.1.md`

- Production-grade template for creating new personas
- Modular structure: Author sections (full character) + Runtime sections (LLM-ready prompts)
- Token-optimized for simulation deployment

### Research Foundation

- **`Agents/personas/synthetic_personas.md`** - Comprehensive implementation guide
- **`Agents/personas/Best Practices for Designing Synthetic Personas in Chat Simulations.pdf`** - UX research and AI prompting techniques

### Core Features

#### Chat Authenticity
- Realistic typos based on emotional state and character patterns
- Natural fragments, contractions, casual language
- NO stage directions (*sighs*, [pauses]) - emotion shown through words
- NO therapy-speak unless authentically in character
- Character-specific verbal fillers and punctuation patterns

#### Psychological Depth
- Enneagram + DISC + Big Five personality frameworks
- Defense mechanisms with linguistic markers
- Core contradictions that create realistic complexity
- Attachment styles affecting relationship dynamics
- Meta-awareness loops for intellectualizing characters

#### Emotional Intelligence
- Emotional logic systems (trigger → response → recovery)
- Cause-effect mapping for behavioral consistency
- Regression probability tracking (likelihood of backsliding)
- Felt-state cues (emotional subtext without narration)
- Secondary defense hierarchies (what happens when primary fails)

#### Dynamic Evolution
- Session progression tracking (3 phases with inflection moments)
- Linguistic drift (gradually adopts agent language over time)
- Fatigue → tone modulation (communication simplifies when exhausted)
- State variables tracked 0-10: trust, openness, fatigue, arousal, hope, engagement
- Memory & continuity systems (what they remember/forget)

#### Production Optimization
- Runtime YAML headers for quick seeding (token-efficient)
- Behavioral failure recovery (mid-simulation corrections)
- External validation snippets (outside perspective grounding)
- Behavioral forks (post-ceremony or major event pathways)
- Cross-persona distinctiveness validation

### Quality Metrics

Personas must pass these benchmarks:

- ✅ **"1 AM text test"** - Feels like texting a real person
- ✅ **Distinctive voice** - Identifiable without seeing name
- ✅ **Emotional consistency** - Trigger-response patterns hold
- ✅ **Natural progression** - No unrealistic breakthroughs
- ✅ **Cross-session continuity** - Remember and reference past

---

## Creating New Personas

### Step-by-Step Process

1. **Copy template:** `Agents/personas/BASE_PERSONA_TEMPLATE_v2.1.md`
2. **Fill Author sections** with rich backstory and psychology
3. **Create distinctive communication patterns** (typos, fillers, rhythm)
4. **Define emotional logic** (triggers, responses, defenses)
5. **Map session progression** (3 phases with inflection moments)
6. **Extract runtime header** (YAML) and character prompt
7. **Test in simulation** and validate against checklist
8. **Iterate based on outputs** (adjust voice, add corrections)

### Reference Files

- **`Agents/personas/PERSONA_REFERENCE_GUIDE.md`** - Detailed seeds for all personas (demographics, cultural markers, psychological frameworks)
- **`Agents/personas/persona_seed_list.md`** - Quick reference for generation

---

## ⚠️ Persona Generator Lessons Learned (2025-10-16)

During the 2025-10-16 persona generation session, we discovered **critical flaws** in using the persona-generator subagent without sufficient context.

### Problem Identified

- Initial generation created multiple personas with the **same name** ("Marcus DeAngelo" repeatedly)
- **All personas were African American** despite requesting diverse archetypes
- Lacked diversity across ethnicity, gender, geography, and class
- This is problematic and not representative for testing purposes

### Root Cause

The persona-generator subagent, when given only archetype descriptions (e.g., "Drama Queen", "Know-It-All") without detailed demographic seeds, defaulted to similar demographic patterns and didn't ensure diversity.

### Solution Implemented

Created comprehensive `PERSONA_REFERENCE_GUIDE.md` with detailed seed information for each persona including:
- Specific names, ages, pronouns
- Detailed ethnicity, location, occupation
- Family background, education, relationships
- Cultural markers and regional dialects
- Psychological frameworks and communication patterns

### Future Requirements

- ✅ **ALWAYS use detailed seed prompts** from `PERSONA_REFERENCE_GUIDE.md`
- ✅ **Specify exact demographics** (name, ethnicity, location, age) in seed
- ✅ **Include cultural markers** and regional characteristics
- ⚠️ **OR modify persona-generator subagent** to ensure diversity automatically
- ⚠️ **Validate output diversity** before accepting generated personas

---

## Testing Status

- ✅ All 13 personas uploaded to database (2025-10-20)
- ✅ Batch tested with Roots of Healing workflows (100+ simulations)
- ✅ 100% completion rate across all persona types
- ⏳ Cross-persona comparison testing (ensure distinctive voices in practice)
- ⏳ Validate all 13 personas in additional simulation scenarios

**Last Updated:** 2025-10-23
