#!/usr/bin/env python3
"""
Test Roots of Healing Workflow against all personas.

This script runs the new Roots of Healing Day 1 workflow against all 13 personas
to test how Tegra handles diverse user types in the integration curriculum.
"""

import asyncio
from datetime import datetime
from test_async_batch_simulations import run_batch_simulations

async def main():
    workflow_id = "roots_of_healing_-_day_1_workflow_1"

    # All 13 personas for comprehensive testing
    persona_ids = [
        "paul_persona_4",                                      # Military vet (terse/defensive)
        "ellen_persona_4",                                     # Tech entrepreneur (verbose/analytical)
        "jamie_adhd_persona_2",                               # ADHD creative (scattered)
        "tommy_confused_instruction_follower_persona_1",      # Confused instruction follower
        "valentina_drama_queen_persona_1",                    # Drama queen (ALL CAPS)
        "sam_crisis_persona_1",                               # Suicidal crisis
        "diego_tangent_master_persona_1",                     # Tangent master (storyteller)
        "dr._rebecca_goldstein_know-it-all_persona_1",        # Know-it-all psychologist
        "aisha_integration_expert_persona_1",                 # Integration expert (spiritual bypassing)
        "kyle_drug-focused_persona_1",                        # Drug-focused (pharmacology obsessed)
        "bobby_prejudiced_persona_1",                         # Prejudiced/biased
        "chloe_manipulative_persona_1",                       # Manipulative/antisocial
        "jack_violence_risk_persona_1",                       # Violence risk
    ]

    print("="*80)
    print("ROOTS OF HEALING - ALL PERSONAS BATCH TEST")
    print("="*80)
    print(f"Workflow: Roots of Healing Workflow 1")
    print(f"Personas: {len(persona_ids)}")
    print(f"Simulations per persona: 1")
    print(f"Max concurrent: 5")
    print(f"Max rounds: 20")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()

    await run_batch_simulations(
        workflow_id=workflow_id,
        persona_ids=persona_ids,
        simulations_per_persona=1,
        max_rounds=20,
        max_concurrent=5,
        output_dir="Agents/batch_simulations/roots_healing_all_personas"
    )

    print()
    print("="*80)
    print("BATCH TEST COMPLETE")
    print("="*80)
    print(f"Results: Agents/batch_simulations/roots_healing_all_personas/")
    print()
    print("Review outputs:")
    print("  - JSON files for machine analysis")
    print("  - Markdown files for human review")
    print()

if __name__ == "__main__":
    asyncio.run(main())
