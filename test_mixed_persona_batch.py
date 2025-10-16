#!/usr/bin/env python3
"""Mixed persona async batch simulation runner.

Runs simulations with multiple personas responding to the same workflow agent.
This version has the Intentions Workflow agent (Tegra) send the first message.
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
    workflow_agent_id: str,
    persona_agent_id: str,
    persona_name: str,
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
        workflow_agent_id: Database ID of workflow agent (sends first)
        persona_agent_id: Database ID of persona agent (responds)
        persona_name: Name of persona (for labeling)
        simulation_number: Simulation number in batch
        max_turns: Number of conversation rounds
        batch_timestamp: Batch timestamp for session ID
        output_folder: Output directory
        initial_prompt: Prompt for workflow agent to start

    Returns:
        Dictionary with simulation results
    """
    print(f"  [{simulation_number:02d}] {persona_name} - Starting...")

    try:
        # Create new simulation instance
        # NOTE: "system" agent sends first, "user" agent responds
        # So workflow agent is "system", persona is "user"
        sim = TwoAgentSimulation(
            storage=storage,
            agent_loader=agent_loader,
            system_agent_id=workflow_agent_id,  # Tegra sends first
            user_agent_id=persona_agent_id,      # Persona responds
            max_turns=max_turns,
            session_id=f"batch_{batch_timestamp}_{persona_name.lower()}_sim{simulation_number:02d}"
        )

        # Load agents
        await sim.load_agents()

        # Run conversation
        await sim.run_conversation(initial_prompt=initial_prompt)

        # Save to file
        output_file = output_folder / f"{persona_name.lower()}_simulation_{simulation_number:02d}.json"
        notes = f"Batch {batch_timestamp}, {persona_name} simulation {simulation_number}"
        await sim.save_to_file(output_file, notes=notes)

        file_size = output_file.stat().st_size / 1024  # KB
        print(f"  [{simulation_number:02d}] {persona_name} - ✓ Complete ({file_size:.1f} KB, {len(sim.messages)} messages)")

        return {
            'success': True,
            'persona': persona_name,
            'simulation_number': simulation_number,
            'output_file': output_file,
            'session_id': sim.session_id,
            'message_count': len(sim.messages)
        }

    except Exception as e:
        print(f"  [{simulation_number:02d}] {persona_name} - ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'persona': persona_name,
            'simulation_number': simulation_number,
            'error': str(e)
        }


async def run_mixed_persona_batch(
    workflow_agent_id: str,
    paul_agent_id: str,
    ellen_agent_id: str,
    simulations_per_persona: int = 5,
    max_turns: int = 20,
    output_base_dir: Optional[Path] = None,
    max_concurrent: int = 5
):
    """
    Run simulations with multiple personas responding to the same workflow agent.

    Args:
        workflow_agent_id: Database ID of the workflow agent (Tegra)
        paul_agent_id: Database ID of Paul Persona 3
        ellen_agent_id: Database ID of Ellen Persona 3
        simulations_per_persona: Number of simulations per persona
        max_turns: Number of conversation rounds per simulation
        output_base_dir: Base directory for output
        max_concurrent: Maximum number of concurrent simulations
    """
    # Create timestamped batch folder
    batch_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if output_base_dir is None:
        output_base_dir = Path("Agents/batch_simulations")

    batch_folder = output_base_dir / f"mixed_batch_{batch_timestamp}"
    batch_folder.mkdir(parents=True, exist_ok=True)

    total_sims = simulations_per_persona * 2

    print("\n" + "="*70)
    print(f"MIXED PERSONA BATCH: {total_sims} simulations ({simulations_per_persona} per persona)")
    print("="*70)
    print(f"Workflow Agent: {workflow_agent_id} (Tegra - sends first)")
    print(f"Paul Persona 3: {paul_agent_id} ({simulations_per_persona} simulations)")
    print(f"Ellen Persona 3: {ellen_agent_id} ({simulations_per_persona} simulations)")
    print(f"Turns per simulation: {max_turns} ({max_turns * 2} messages)")
    print(f"Max concurrent: {max_concurrent}")
    print(f"Output folder: {batch_folder}")
    print("="*70 + "\n")

    # Initialize storage and loader
    storage = ConfigStorage()
    agent_loader = AgentLoader()

    # Seed prompt for Tegra to generate opening message
    # This prompt is sent to the workflow agent to generate system0
    # Design considerations:
    # - No time estimates ("15-20 minutes")
    # - No assumptions about journey timing (past/present/future)
    # - Flexible language: "this work" instead of "your journey"
    # - Keeps core Tegra voice: brief, grounded, compass metaphor
    initial_prompt = """You're starting intention-setting work with someone.

Intentions work like a compass - they point toward what matters without forcing the destination.

I'll help you build 3 intentions.

What brought you to this work?"""

    # Create tasks for all simulations
    tasks = []

    # Paul simulations (1-5)
    for i in range(1, simulations_per_persona + 1):
        task = run_single_simulation(
            storage=storage,
            agent_loader=agent_loader,
            workflow_agent_id=workflow_agent_id,
            persona_agent_id=paul_agent_id,
            persona_name="paul",
            simulation_number=i,
            max_turns=max_turns,
            batch_timestamp=batch_timestamp,
            output_folder=batch_folder,
            initial_prompt=initial_prompt
        )
        tasks.append(task)

    # Ellen simulations (1-5)
    for i in range(1, simulations_per_persona + 1):
        task = run_single_simulation(
            storage=storage,
            agent_loader=agent_loader,
            workflow_agent_id=workflow_agent_id,
            persona_agent_id=ellen_agent_id,
            persona_name="ellen",
            simulation_number=i,
            max_turns=max_turns,
            batch_timestamp=batch_timestamp,
            output_folder=batch_folder,
            initial_prompt=initial_prompt
        )
        tasks.append(task)

    # Run simulations with concurrency limit
    print(f"Running {total_sims} simulations (batches of {max_concurrent})...\n")
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

    # Filter and group results
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    paul_results = [r for r in successful if r['persona'] == 'paul']
    ellen_results = [r for r in successful if r['persona'] == 'ellen']

    # Summary
    print("\n" + "="*70)
    print(f"BATCH COMPLETE: {len(successful)}/{total_sims} successful")
    print(f"  Paul: {len(paul_results)}/{simulations_per_persona}")
    print(f"  Ellen: {len(ellen_results)}/{simulations_per_persona}")
    print(f"Duration: {duration:.1f} seconds ({duration/total_sims:.1f}s per simulation avg)")
    print("="*70)
    print(f"Output folder: {batch_folder}")

    if paul_results:
        print(f"\nPaul simulations:")
        for r in sorted(paul_results, key=lambda x: x['simulation_number']):
            file_size = r['output_file'].stat().st_size / 1024
            print(f"  - {r['output_file'].name} ({file_size:.1f} KB, {r['message_count']} messages)")

    if ellen_results:
        print(f"\nEllen simulations:")
        for r in sorted(ellen_results, key=lambda x: x['simulation_number']):
            file_size = r['output_file'].stat().st_size / 1024
            print(f"  - {r['output_file'].name} ({file_size:.1f} KB, {r['message_count']} messages)")

    if failed:
        print(f"\nFailed simulations:")
        for r in failed:
            print(f"  - {r['persona']} {r['simulation_number']:02d}: {r['error']}")

    print()

    return successful, batch_folder, duration


async def main():
    """Main entry point."""
    print("\n" + "="*70)
    print("MIXED PERSONA ASYNC BATCH SIMULATION")
    print("="*70)

    # Initialize storage
    storage = ConfigStorage()

    # List available agents
    agents = await storage.list_agents()

    print("\n=== Available Agents ===")
    for agent in agents:
        print(f"  - {agent['id']}: {agent['name']}")
    print()

    # Find required agents
    workflow_agent_id = None
    paul_agent_id = None
    ellen_agent_id = None

    for agent in agents:
        agent_name_lower = agent['name'].lower()

        # Look for Intentions Workflow 7
        if 'intentions' in agent_name_lower and 'workflow' in agent_name_lower and '7' in agent_name_lower:
            workflow_agent_id = agent['id']
            print(f"✓ Found Intentions Workflow 7: {agent['id']}")

        # Look for Paul Persona 3
        if 'paul' in agent_name_lower and 'persona' in agent_name_lower and '3' in agent_name_lower:
            paul_agent_id = agent['id']
            print(f"✓ Found Paul Persona 3: {agent['id']}")

        # Look for Ellen Persona 3
        if 'ellen' in agent_name_lower and 'persona' in agent_name_lower and '3' in agent_name_lower:
            ellen_agent_id = agent['id']
            print(f"✓ Found Ellen Persona 3: {agent['id']}")

    # Check if all agents found
    if not workflow_agent_id:
        print("\nERROR: Could not find 'Intentions Workflow 7'")
        print("Available workflow agents:")
        for agent in agents:
            if 'workflow' in agent['name'].lower() or 'intentions' in agent['name'].lower():
                print(f"  - {agent['id']}: {agent['name']}")
        return

    if not paul_agent_id:
        print("\nERROR: Could not find 'Paul Persona 3'")
        return

    if not ellen_agent_id:
        print("\nERROR: Could not find 'Ellen Persona 3'")
        return

    # Run mixed persona batch
    results, batch_folder, duration = await run_mixed_persona_batch(
        workflow_agent_id=workflow_agent_id,
        paul_agent_id=paul_agent_id,
        ellen_agent_id=ellen_agent_id,
        simulations_per_persona=10,  # 10 Paul + 10 Ellen = 20 total
        max_turns=20,
        max_concurrent=20  # Run all 20 at once for maximum speed
    )

    print("✓ Mixed persona batch simulation complete!")
    print(f"✓ All files saved to: {batch_folder}")
    print(f"✓ Total time: {duration:.1f} seconds")
    print(f"✓ Average: {duration/len(results):.1f} seconds per simulation")


if __name__ == "__main__":
    asyncio.run(main())
