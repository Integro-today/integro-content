#!/usr/bin/env python3
"""
Comprehensive Persona Batch Simulation Test

Runs async simulations with ALL persona agents in the database against a single workflow agent.
Tests the full diversity of personas with 3 conversations each.

Configuration:
- Workflow Agent: Intentions Workflow 3
- Personas: All persona agents in database (16 total as of 2025-10-17)
- Simulations per persona: 3
- Max concurrent: 10
- Total simulations: 48 (16 personas × 3 each)

Performance:
- Expected time: ~6-8 minutes (with 10 concurrent at ~8-12s per simulation)
- Output: 48 JSON + 48 Markdown files

Usage:
    docker exec integro_simulation_backend python test_all_personas_batch.py
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import time

from test_two_agent_simulation import TwoAgentSimulation
from integro.config import ConfigStorage, AgentLoader
from integro.utils.logging import get_logger
from convert_simulation_to_markdown import convert_to_markdown, load_simulation

logger = get_logger(__name__)


class RateLimiter:
    """
    Manages API rate limits by tracking actual token usage from API responses.

    Uses Groq API usage statistics and rate limit headers to stay within limits.
    """

    def __init__(self, tokens_per_minute: int = 250_000, safety_margin: float = 0.85):
        """
        Initialize rate limiter.

        Args:
            tokens_per_minute: TPM limit (default from error messages: 250,000)
            safety_margin: Use this fraction of limit (0.85 = 85% to be safe)
        """
        self.tokens_per_minute = int(tokens_per_minute * safety_margin)
        self.tokens_used = 0
        self.window_start = time.time()
        self.lock = asyncio.Lock()
        self.total_tokens_tracked = 0

        print(f"[RATE LIMIT] Initialized with {self.tokens_per_minute:,} TPM limit (85% of {tokens_per_minute:,})")

    async def wait_if_needed(self, estimated_tokens: int = 8000):
        """
        Check if we need to wait before making next API call.
        Uses conservative estimate until actual usage is reported.

        Args:
            estimated_tokens: Conservative estimate for next call (default 8000)
        """
        async with self.lock:
            current_time = time.time()
            elapsed = current_time - self.window_start

            # Reset window if 60 seconds have passed
            if elapsed >= 60:
                if self.tokens_used > 0:
                    print(f"  [RATE LIMIT] Window reset. Used {self.tokens_used:,} tokens in last minute")
                self.tokens_used = 0
                self.window_start = current_time
                elapsed = 0

            # Check if we need to wait
            if self.tokens_used + estimated_tokens > self.tokens_per_minute:
                # Calculate wait time to next window
                wait_time = 60 - elapsed
                if wait_time > 0:
                    print(f"  [RATE LIMIT] Near limit: {self.tokens_used:,}/{self.tokens_per_minute:,} tokens used")
                    print(f"  [RATE LIMIT] Waiting {wait_time:.1f}s for window reset...")
                    await asyncio.sleep(wait_time + 0.5)  # Add 0.5s buffer
                    # Reset for new window
                    self.tokens_used = 0
                    self.window_start = time.time()

    def record_usage(self, actual_tokens: int):
        """
        Record actual token usage from API response.

        Args:
            actual_tokens: Actual tokens used from API response usage field
        """
        self.tokens_used += actual_tokens
        self.total_tokens_tracked += actual_tokens


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
    initial_prompt: str,
    rate_limiter: Optional[RateLimiter] = None
) -> Dict[str, Any]:
    """
    Run a single simulation asynchronously.

    Args:
        storage: ConfigStorage instance
        agent_loader: AgentLoader instance
        workflow_agent_id: Database ID of workflow agent (sends first)
        persona_agent_id: Database ID of persona agent (responds)
        persona_name: Name of persona (for labeling)
        simulation_number: Simulation number for this persona
        max_turns: Number of conversation rounds
        batch_timestamp: Batch timestamp for session ID
        output_folder: Output directory
        initial_prompt: Prompt for workflow agent to start
        rate_limiter: Optional RateLimiter to manage API rate limits

    Returns:
        Dictionary with simulation results
    """
    print(f"  [{simulation_number}] {persona_name} - Starting...")

    try:
        # Wait for rate limiter before starting (if provided)
        if rate_limiter:
            await rate_limiter.wait_if_needed(estimated_tokens=8000)

        # Create new simulation instance
        # NOTE: "system" agent sends first, "user" agent responds
        # So workflow agent is "system", persona is "user"
        sim = TwoAgentSimulation(
            storage=storage,
            agent_loader=agent_loader,
            system_agent_id=workflow_agent_id,  # Workflow sends first
            user_agent_id=persona_agent_id,      # Persona responds
            max_turns=max_turns,
            session_id=f"batch_{batch_timestamp}_{persona_name.lower().replace(' ', '_')}_sim{simulation_number:02d}"
        )

        # Load agents
        await sim.load_agents()

        # Run conversation (each turn will naturally pace itself via Groq API)
        await sim.run_conversation(initial_prompt=initial_prompt)

        # Save to file
        output_file = output_folder / f"{persona_name.lower().replace(' ', '_')}_simulation_{simulation_number:02d}.json"
        notes = f"Batch {batch_timestamp}, {persona_name} simulation {simulation_number}"
        await sim.save_to_file(output_file, notes=notes)

        # Auto-convert to Markdown for human readability
        try:
            simulation_data = load_simulation(output_file)
            markdown_content = convert_to_markdown(simulation_data)
            md_file = output_file.with_suffix('.md')
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
        except Exception as e:
            logger.warning(f"Failed to generate markdown for {output_file.name}: {e}")

        file_size = output_file.stat().st_size / 1024  # KB
        print(f"  [{simulation_number}] {persona_name} - ✓ Complete ({file_size:.1f} KB, {len(sim.messages)} messages)")

        return {
            'success': True,
            'persona': persona_name,
            'persona_id': persona_agent_id,
            'simulation_number': simulation_number,
            'output_file': output_file,
            'session_id': sim.session_id,
            'message_count': len(sim.messages)
        }

    except Exception as e:
        print(f"  [{simulation_number}] {persona_name} - ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'persona': persona_name,
            'persona_id': persona_agent_id,
            'simulation_number': simulation_number,
            'error': str(e)
        }


async def run_all_personas_batch(
    workflow_agent_id: str,
    simulations_per_persona: int = 3,
    max_turns: int = 20,
    output_base_dir: Optional[Path] = None,
    max_concurrent: int = 5
):
    """
    Run simulations with ALL persona agents in the database.

    Args:
        workflow_agent_id: Database ID of the workflow agent (e.g., "intentions_workflow_3")
        simulations_per_persona: Number of simulations per persona (default: 3)
        max_turns: Number of conversation rounds per simulation (default: 20)
        output_base_dir: Base directory for output
        max_concurrent: Maximum number of concurrent simulations (default: 10)
    """
    # Create timestamped batch folder
    batch_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if output_base_dir is None:
        output_base_dir = Path("Agents/batch_simulations")

    batch_folder = output_base_dir / f"all_personas_batch_{batch_timestamp}"
    batch_folder.mkdir(parents=True, exist_ok=True)

    # Initialize storage and loader
    storage = ConfigStorage()
    agent_loader = AgentLoader()

    # Load ALL persona agents from database
    print("\n" + "="*70)
    print("LOADING PERSONA AGENTS FROM DATABASE")
    print("="*70)

    all_agents = await storage.list_agents()

    # Filter for persona agents (exclude workflows)
    persona_agents = [
        agent for agent in all_agents
        if 'persona' in agent['name'].lower() and 'workflow' not in agent['name'].lower()
    ]

    print(f"\nFound {len(persona_agents)} persona agents:")
    for i, agent in enumerate(sorted(persona_agents, key=lambda x: x['name']), 1):
        print(f"  {i:2d}. {agent['name']:<45} (ID: {agent['id']})")

    total_sims = len(persona_agents) * simulations_per_persona

    print("\n" + "="*70)
    print(f"COMPREHENSIVE PERSONA BATCH SIMULATION")
    print("="*70)
    print(f"Workflow Agent: {workflow_agent_id} (sends first)")
    print(f"Persona Agents: {len(persona_agents)} personas")
    print(f"Simulations per persona: {simulations_per_persona}")
    print(f"Total simulations: {total_sims}")
    print(f"Turns per simulation: {max_turns} ({max_turns * 2} messages)")
    print(f"Max concurrent: {max_concurrent}")
    print(f"Output folder: {batch_folder}")
    print("="*70 + "\n")

    # Initialize rate limiter for Groq API
    rate_limiter = RateLimiter(tokens_per_minute=250_000, safety_margin=0.85)

    # Seed prompt for workflow agent to generate opening message
    initial_prompt = """You're starting intention-setting work with someone.

Intentions work like a compass - they point toward what matters without forcing the destination.

I'll help you build 3 intentions.

What brought you to this work?"""

    # Create tasks for all simulations
    tasks = []

    for persona in persona_agents:
        persona_id = persona['id']
        persona_name = persona['name']

        # Create N simulations for this persona
        for sim_num in range(1, simulations_per_persona + 1):
            task = run_single_simulation(
                storage=storage,
                agent_loader=agent_loader,
                workflow_agent_id=workflow_agent_id,
                persona_agent_id=persona_id,
                persona_name=persona_name,
                simulation_number=sim_num,
                max_turns=max_turns,
                batch_timestamp=batch_timestamp,
                output_folder=batch_folder,
                initial_prompt=initial_prompt,
                rate_limiter=rate_limiter
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

    # Analyze results
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    # Group by persona
    results_by_persona = {}
    for result in successful:
        persona_name = result['persona']
        if persona_name not in results_by_persona:
            results_by_persona[persona_name] = []
        results_by_persona[persona_name].append(result)

    # Summary
    print("\n" + "="*70)
    print(f"BATCH COMPLETE: {len(successful)}/{total_sims} successful")
    print("="*70)
    print(f"Duration: {duration:.1f} seconds ({duration/total_sims:.1f}s per simulation avg)")
    if rate_limiter and rate_limiter.total_tokens_tracked > 0:
        print(f"Tokens tracked: {rate_limiter.total_tokens_tracked:,} (estimate)")
    print()

    # Per-persona summary
    print("Results by Persona:")
    for persona_name in sorted(results_by_persona.keys()):
        persona_results = results_by_persona[persona_name]
        print(f"\n  {persona_name} ({len(persona_results)}/{simulations_per_persona} successful):")
        for r in sorted(persona_results, key=lambda x: x['simulation_number']):
            file_size = r['output_file'].stat().st_size / 1024
            print(f"    - Sim {r['simulation_number']}: {r['output_file'].name} ({file_size:.1f} KB, {r['message_count']} messages)")

    if failed:
        print(f"\n  Failed simulations ({len(failed)}):")
        for r in failed:
            print(f"    - {r['persona']} sim {r['simulation_number']}: {r.get('error', 'Unknown error')}")

    print("\n" + "="*70)
    print(f"Output folder: {batch_folder}")
    print(f"Formats: JSON (machine-readable) + Markdown (human-readable)")
    print("="*70 + "\n")

    return successful, batch_folder, duration


async def main():
    """Main entry point."""
    print("\n" + "="*70)
    print("COMPREHENSIVE PERSONA BATCH SIMULATION TEST")
    print("="*70)

    # Initialize storage
    storage = ConfigStorage()

    # Find Intentions Workflow 3
    agents = await storage.list_agents()

    workflow_agent_id = None
    for agent in agents:
        if 'intentions' in agent['name'].lower() and 'workflow' in agent['name'].lower() and '3' in agent['name']:
            workflow_agent_id = agent['id']
            print(f"✓ Found workflow agent: {agent['name']} (ID: {workflow_agent_id})")
            break

    if not workflow_agent_id:
        print("\nERROR: Could not find 'Intentions Workflow 3'")
        print("Available workflow agents:")
        for agent in agents:
            if 'workflow' in agent['name'].lower():
                print(f"  - {agent['id']}: {agent['name']}")
        return

    # Run comprehensive batch
    results, batch_folder, duration = await run_all_personas_batch(
        workflow_agent_id=workflow_agent_id,
        simulations_per_persona=3,  # 3 conversations per persona
        max_turns=20,               # 20 rounds (40 messages) per conversation
        max_concurrent=3            # 3 concurrent simulations (balance speed vs rate limits)
    )

    print("\n✓ Comprehensive persona batch simulation complete!")
    print(f"✓ All files saved to: {batch_folder}")
    print(f"✓ Total time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"✓ Average: {duration/len(results):.1f} seconds per simulation")
    print(f"✓ Total successful simulations: {len(results)}")


if __name__ == "__main__":
    asyncio.run(main())
