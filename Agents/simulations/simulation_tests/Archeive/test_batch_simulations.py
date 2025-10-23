#!/usr/bin/env python3
"""Batch simulation runner - runs multiple agent simulations and saves to dedicated folder.

This script runs multiple simulations between the same two agents to generate
diverse conversation samples for analysis and evaluation.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from test_two_agent_simulation import TwoAgentSimulation
from integro.config import ConfigStorage, AgentLoader
from integro.utils.logging import get_logger

logger = get_logger(__name__)


async def run_batch_simulations(
    system_agent_id: str,
    user_agent_id: str,
    num_simulations: int = 10,
    max_turns: int = 20,
    output_base_dir: Optional[Path] = None
):
    """
    Run multiple simulations between two agents.

    Args:
        system_agent_id: Database ID of the system agent (sends first)
        user_agent_id: Database ID of the user agent (responds)
        num_simulations: Number of simulations to run
        max_turns: Number of conversation rounds per simulation
        output_base_dir: Base directory for output (creates timestamped subfolder)
    """
    # Create timestamped batch folder
    batch_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if output_base_dir is None:
        output_base_dir = Path("Agents/batch_simulations")

    batch_folder = output_base_dir / f"batch_{batch_timestamp}"
    batch_folder.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*70)
    print(f"BATCH SIMULATION RUN: {num_simulations} simulations")
    print("="*70)
    print(f"System Agent: {system_agent_id}")
    print(f"User Agent: {user_agent_id}")
    print(f"Turns per simulation: {max_turns} ({max_turns * 2} messages)")
    print(f"Output folder: {batch_folder}")
    print("="*70 + "\n")

    # Initialize storage and loader once
    storage = ConfigStorage()
    agent_loader = AgentLoader()

    # Initial prompt for persona to generate opening
    initial_prompt = "As [PERSONA NAME], write your opening message to begin the intention-setting process for your psychedelic journey. Keep it brief (1-3 sentences) and authentic to your character."

    results = []

    for i in range(num_simulations):
        print(f"\n[{i+1}/{num_simulations}] Starting simulation {i+1}...")

        try:
            # Create new simulation instance for each run
            sim = TwoAgentSimulation(
                storage=storage,
                agent_loader=agent_loader,
                system_agent_id=system_agent_id,
                user_agent_id=user_agent_id,
                max_turns=max_turns,
                session_id=f"batch_{batch_timestamp}_sim{i+1:02d}"
            )

            # Load agents (only needed on first iteration)
            if i == 0:
                print("  Loading agents from database...")
                await sim.load_agents()
            else:
                # Reuse loaded agents for efficiency
                print("  Reusing loaded agents...")
                sim.system_agent = results[0]['simulation'].system_agent
                sim.user_agent = results[0]['simulation'].user_agent

            # Run conversation
            print(f"  Running conversation ({max_turns} rounds)...")
            await sim.run_conversation(initial_prompt=initial_prompt)

            # Save to file
            output_file = batch_folder / f"simulation_{i+1:02d}.json"
            notes = f"Batch {batch_timestamp}, simulation {i+1}/{num_simulations}"
            await sim.save_to_file(output_file, notes=notes)

            print(f"  ✓ Saved to {output_file.name}")
            print(f"  Messages: {len(sim.messages)}")

            results.append({
                'simulation': sim,
                'output_file': output_file,
                'session_id': sim.session_id
            })

        except Exception as e:
            print(f"  ✗ ERROR in simulation {i+1}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Summary
    print("\n" + "="*70)
    print(f"BATCH COMPLETE: {len(results)}/{num_simulations} successful")
    print("="*70)
    print(f"Output folder: {batch_folder}")
    print(f"Files generated:")
    for r in results:
        file_size = r['output_file'].stat().st_size / 1024  # KB
        print(f"  - {r['output_file'].name} ({file_size:.1f} KB)")
    print()

    return results, batch_folder


async def main():
    """Main entry point for batch simulation runner."""
    print("\n" + "="*70)
    print("BATCH SIMULATION RUNNER")
    print("="*70)

    # Initialize storage
    storage = ConfigStorage()

    # List available agents
    agents = await storage.list_agents()

    print("\n=== Available Agents ===")
    for agent in agents:
        print(f"  - {agent['id']}: {agent['name']}")
    print()

    # Find Paul Persona 3 and Intentions Workflow 2
    system_agent_id = None
    user_agent_id = None

    for agent in agents:
        agent_name_lower = agent['name'].lower()
        if 'paul' in agent_name_lower and 'persona' in agent_name_lower and '3' in agent_name_lower:
            system_agent_id = agent['id']
            print(f"✓ Found Paul Persona 3: {agent['id']}")

        if 'intentions' in agent_name_lower and 'workflow' in agent_name_lower and '2' in agent_name_lower:
            user_agent_id = agent['id']
            print(f"✓ Found Intentions Workflow 2: {agent['id']}")

    if not system_agent_id or not user_agent_id:
        print("\nERROR: Could not find required agents")
        print("Need: 'Paul Persona 3' and 'Intentions Workflow 2'")
        return

    # Run batch simulations
    results, batch_folder = await run_batch_simulations(
        system_agent_id=system_agent_id,
        user_agent_id=user_agent_id,
        num_simulations=10,
        max_turns=20
    )

    print("✓ Batch simulation complete!")
    print(f"✓ All files saved to: {batch_folder}")


if __name__ == "__main__":
    asyncio.run(main())
