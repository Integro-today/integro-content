#!/usr/bin/env python3
"""
Test Roots of Healing Workflow V8 against selected personas.

This script tests the V8 workflow (with [WORKFLOW COMPLETE] exit phrase) against
5 diverse personas to verify the hard stop closure mechanism works correctly.

Personas tested:
- Ellen (verbose/analytical)
- Paul (terse/defensive)
- Jamie (ADHD/scattered)
- Chloe (manipulative)
- Dr. Rebecca (know-it-all)
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from test_two_agent_simulation import TwoAgentSimulation
from integro.config import ConfigStorage, AgentLoader
from integro.utils.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Simple rate limiter for Groq API."""
    def __init__(self, max_tpm: int = 212500):
        self.max_tpm = max_tpm
        self.tokens_used = 0
        self.window_start = datetime.now()

    def reset_if_needed(self):
        """Reset counter if we're in a new minute."""
        now = datetime.now()
        elapsed = (now - self.window_start).total_seconds()
        if elapsed >= 60:
            self.tokens_used = 0
            self.window_start = now

    async def wait_if_needed(self, estimated_tokens: int = 5000):
        """Wait if we're approaching rate limits."""
        self.reset_if_needed()

        if self.tokens_used + estimated_tokens > self.max_tpm:
            wait_time = 60 - (datetime.now() - self.window_start).total_seconds()
            if wait_time > 0:
                logger.info(f"Rate limit approaching, waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                self.reset_if_needed()

        self.tokens_used += estimated_tokens


async def run_single_simulation(
    storage: ConfigStorage,
    agent_loader: AgentLoader,
    workflow_id: str,
    persona_id: str,
    simulation_number: int,
    max_rounds: int,
    output_folder: Path,
    rate_limiter: RateLimiter
) -> Dict[str, Any]:
    """Run a single simulation."""
    persona_name = persona_id.split('_')[0]
    print(f"  [{persona_name}] Starting simulation {simulation_number}...")

    try:
        # Wait for rate limit
        await rate_limiter.wait_if_needed()

        # Create simulation
        sim = TwoAgentSimulation(
            storage=storage,
            agent_loader=agent_loader,
            system_agent_id=persona_id,  # Persona speaks first
            user_agent_id=workflow_id,   # Workflow responds
            max_turns=max_rounds,
            session_id=f"{persona_name}_v8_sim{simulation_number:02d}"
        )

        # Load agents
        await sim.load_agents()

        # Run conversation
        initial_prompt = (
            "You are accessing your daily integration curriculum content. "
            "Write a brief opening message (1-3 sentences) expressing that you're ready to engage with today's lesson. "
            "Stay authentic to your character - you might be eager, hesitant, tired, curious, resistant, or any other genuine state. "
            "Examples: 'Alright, what's today's lesson about?' or 'I'm here for Day 1. Let's see what this is.' or 'Ready when you are.'"
        )

        await sim.run_conversation(initial_prompt=initial_prompt)

        # Save to file
        output_file = output_folder / f"{persona_name}_simulation_{simulation_number:02d}.json"
        notes = f"Roots V8 test with {persona_name}, simulation {simulation_number}"
        await sim.save_to_file(output_file, notes=notes)

        file_size = output_file.stat().st_size / 1024  # KB
        print(f"  [{persona_name}] ✓ Complete ({file_size:.1f} KB, {len(sim.messages)} messages)")

        return {
            'success': True,
            'persona': persona_name,
            'simulation_number': simulation_number,
            'output_file': output_file,
            'message_count': len(sim.messages)
        }

    except Exception as e:
        print(f"  [{persona_name}] ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'persona': persona_name,
            'simulation_number': simulation_number,
            'error': str(e)
        }


async def main():
    workflow_id = "roots_of_healing_-_day_1_workflow_(version_8)_workflow_1"

    # 5 selected personas for testing
    persona_ids = [
        "ellen_persona_4",                               # Verbose/analytical
        "paul_persona_4",                                # Terse/defensive
        "jamie_adhd_persona_2",                          # ADHD/scattered
        "chloe_manipulative_persona_1",                  # Manipulative
        "dr._rebecca_goldstein_know-it-all_persona_1",   # Know-it-all
    ]

    # Create output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path(f"Agents/simulations/batch_simulations/roots_v8_hard_stop_closure_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*80)
    print("ROOTS OF HEALING V8 - HARD STOP CLOSURE TEST")
    print("="*80)
    print(f"Workflow: Roots of Healing V8 (with [WORKFLOW COMPLETE] marker)")
    print(f"Personas: {len(persona_ids)}")
    print(f"Simulations per persona: 1")
    print(f"Max rounds: 20")
    print(f"Output: {output_dir}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()

    # Initialize storage and loader
    storage = ConfigStorage()
    agent_loader = AgentLoader()
    rate_limiter = RateLimiter()

    # Run simulations sequentially to avoid rate limits
    results = []
    start_time = datetime.now()

    for i, persona_id in enumerate(persona_ids, 1):
        result = await run_single_simulation(
            storage=storage,
            agent_loader=agent_loader,
            workflow_id=workflow_id,
            persona_id=persona_id,
            simulation_number=1,
            max_rounds=20,
            output_folder=output_dir,
            rate_limiter=rate_limiter
        )
        results.append(result)

        # Brief pause between simulations
        if i < len(persona_ids):
            await asyncio.sleep(2)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Summary
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print("\n" + "="*80)
    print(f"BATCH TEST COMPLETE: {len(successful)}/{len(persona_ids)} successful")
    print(f"Duration: {duration:.1f} seconds ({duration/len(persona_ids):.1f}s per simulation avg)")
    print("="*80)
    print(f"Output folder: {output_dir}")

    if successful:
        print(f"\n✓ Successful simulations:")
        for r in successful:
            file_size = r['output_file'].stat().st_size / 1024
            print(f"  - {r['persona']}: {file_size:.1f} KB, {r['message_count']} messages")

    if failed:
        print(f"\n✗ Failed simulations:")
        for r in failed:
            print(f"  - {r['persona']}: {r['error']}")

    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("1. Review conversations for [WORKFLOW COMPLETE] marker effectiveness")
    print("2. Check that conversations end cleanly after completion")
    print("3. Verify no robotic closing loops occurred")
    print(f"4. View results at: http://localhost:8890")
    print()


if __name__ == "__main__":
    asyncio.run(main())
