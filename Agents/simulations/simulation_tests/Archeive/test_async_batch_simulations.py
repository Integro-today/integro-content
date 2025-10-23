#!/usr/bin/env python3
"""Async parallel batch simulation runner - runs multiple agent simulations concurrently.

This script runs multiple simulations in parallel to generate diverse conversation
samples much faster than sequential execution.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from test_two_agent_simulation import TwoAgentSimulation
from integro.config import ConfigStorage, AgentLoader
from integro.utils.logging import get_logger

logger = get_logger(__name__)


async def run_single_simulation(
    storage: ConfigStorage,
    agent_loader: AgentLoader,
    system_agent_id: str,
    user_agent_id: str,
    simulation_number: int,
    max_turns: int,
    batch_timestamp: str,
    output_folder: Path,
    initial_prompt: str
) -> Dict[str, Any]:
    """
    Run a single simulation asynchronously.

    Args:
        storage: ConfigStorage instance
        agent_loader: AgentLoader instance
        system_agent_id: Database ID of system agent
        user_agent_id: Database ID of user agent
        simulation_number: Simulation number in batch
        max_turns: Number of conversation rounds
        batch_timestamp: Batch timestamp for session ID
        output_folder: Output directory
        initial_prompt: Prompt for persona to generate opening

    Returns:
        Dictionary with simulation results
    """
    print(f"  [{simulation_number:02d}] Starting...")

    try:
        # Create new simulation instance
        sim = TwoAgentSimulation(
            storage=storage,
            agent_loader=agent_loader,
            system_agent_id=system_agent_id,
            user_agent_id=user_agent_id,
            max_turns=max_turns,
            session_id=f"batch_{batch_timestamp}_sim{simulation_number:02d}"
        )

        # Load agents (each simulation loads independently for thread safety)
        await sim.load_agents()

        # Run conversation
        await sim.run_conversation(initial_prompt=initial_prompt)

        # Save to file
        output_file = output_folder / f"simulation_{simulation_number:02d}.json"
        notes = f"Batch {batch_timestamp}, simulation {simulation_number}"
        await sim.save_to_file(output_file, notes=notes)

        file_size = output_file.stat().st_size / 1024  # KB
        print(f"  [{simulation_number:02d}] ✓ Complete ({file_size:.1f} KB, {len(sim.messages)} messages)")

        return {
            'success': True,
            'simulation_number': simulation_number,
            'output_file': output_file,
            'session_id': sim.session_id,
            'message_count': len(sim.messages)
        }

    except Exception as e:
        print(f"  [{simulation_number:02d}] ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'simulation_number': simulation_number,
            'error': str(e)
        }


async def run_async_batch_simulations(
    system_agent_id: str,
    user_agent_id: str,
    num_simulations: int = 10,
    max_turns: int = 20,
    output_base_dir: Optional[Path] = None,
    max_concurrent: int = 5  # Limit concurrent simulations to avoid overload
):
    """
    Run multiple simulations concurrently.

    Args:
        system_agent_id: Database ID of the system agent (sends first)
        user_agent_id: Database ID of the user agent (responds)
        num_simulations: Number of simulations to run
        max_turns: Number of conversation rounds per simulation
        output_base_dir: Base directory for output (creates timestamped subfolder)
        max_concurrent: Maximum number of concurrent simulations
    """
    # Create timestamped batch folder
    batch_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if output_base_dir is None:
        output_base_dir = Path("Agents/batch_simulations")

    batch_folder = output_base_dir / f"batch_{batch_timestamp}"
    batch_folder.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*70)
    print(f"ASYNC BATCH SIMULATION RUN: {num_simulations} simulations (max {max_concurrent} concurrent)")
    print("="*70)
    print(f"System Agent: {system_agent_id}")
    print(f"User Agent: {user_agent_id}")
    print(f"Turns per simulation: {max_turns} ({max_turns * 2} messages)")
    print(f"Output folder: {batch_folder}")
    print("="*70 + "\n")

    # Initialize storage and loader (shared across simulations)
    storage = ConfigStorage()
    agent_loader = AgentLoader()

    # Initial prompt for persona to generate opening
    initial_prompt = "As [PERSONA NAME], write your opening message to begin the intention-setting process for your psychedelic journey. Keep it brief (1-3 sentences) and authentic to your character."

    # Create tasks for all simulations
    tasks = []
    for i in range(1, num_simulations + 1):
        task = run_single_simulation(
            storage=storage,
            agent_loader=agent_loader,
            system_agent_id=system_agent_id,
            user_agent_id=user_agent_id,
            simulation_number=i,
            max_turns=max_turns,
            batch_timestamp=batch_timestamp,
            output_folder=batch_folder,
            initial_prompt=initial_prompt
        )
        tasks.append(task)

    # Run simulations with concurrency limit
    print(f"Running {num_simulations} simulations (batches of {max_concurrent})...\n")
    start_time = datetime.now()

    # Use semaphore to limit concurrent executions
    semaphore = asyncio.Semaphore(max_concurrent)

    async def run_with_semaphore(task):
        async with semaphore:
            return await task

    # Run all tasks with concurrency control
    results = await asyncio.gather(*[run_with_semaphore(task) for task in tasks])

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Filter successful results
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    # Summary
    print("\n" + "="*70)
    print(f"BATCH COMPLETE: {len(successful)}/{num_simulations} successful")
    print(f"Duration: {duration:.1f} seconds ({duration/num_simulations:.1f}s per simulation avg)")
    print("="*70)
    print(f"Output folder: {batch_folder}")

    if successful:
        print(f"\nSuccessful simulations:")
        for r in successful:
            file_size = r['output_file'].stat().st_size / 1024
            print(f"  - {r['output_file'].name} ({file_size:.1f} KB, {r['message_count']} messages)")

    if failed:
        print(f"\nFailed simulations:")
        for r in failed:
            print(f"  - Simulation {r['simulation_number']:02d}: {r['error']}")

    print()

    return successful, batch_folder, duration


async def main():
    """Main entry point for async batch simulation runner."""
    print("\n" + "="*70)
    print("ASYNC PARALLEL BATCH SIMULATION RUNNER")
    print("="*70)

    # Initialize storage
    storage = ConfigStorage()

    # List available agents
    agents = await storage.list_agents()

    print("\n=== Available Agents ===")
    for agent in agents:
        print(f"  - {agent['id']}: {agent['name']}")
    print()

    # Find Ellen Persona 3 and Intentions Workflow 2
    system_agent_id = None
    user_agent_id = None

    for agent in agents:
        agent_name_lower = agent['name'].lower()

        # Look for Ellen Persona 3
        if 'ellen' in agent_name_lower and 'persona' in agent_name_lower and '3' in agent_name_lower:
            system_agent_id = agent['id']
            print(f"✓ Found Ellen Persona 3: {agent['id']}")

        if 'intentions' in agent_name_lower and 'workflow' in agent_name_lower and '2' in agent_name_lower:
            user_agent_id = agent['id']
            print(f"✓ Found Intentions Workflow 2: {agent['id']}")

    if not system_agent_id:
        print("\nERROR: Could not find 'Ellen Persona 3'")
        print("Looking for any Ellen agent...")
        for agent in agents:
            if 'ellen' in agent['name'].lower():
                print(f"  Found: {agent['id']} - {agent['name']}")
        return

    if not user_agent_id:
        print("\nERROR: Could not find 'Intentions Workflow 2'")
        return

    # Run async batch simulations
    results, batch_folder, duration = await run_async_batch_simulations(
        system_agent_id=system_agent_id,
        user_agent_id=user_agent_id,
        num_simulations=10,
        max_turns=20,
        max_concurrent=5  # Run 5 at a time to avoid overwhelming the system
    )

    print("✓ Async batch simulation complete!")
    print(f"✓ All files saved to: {batch_folder}")
    print(f"✓ Total time: {duration:.1f} seconds")
    print(f"✓ Average: {duration/10:.1f} seconds per simulation")
    print(f"✓ Speedup: ~{10*60/duration:.1f}x faster than sequential (estimated)")


if __name__ == "__main__":
    asyncio.run(main())
