"""
Test script for running 5 simulations with Intentions Workflow 8 and Paul Persona 4.
"""

import asyncio
import sys
import time
from pathlib import Path
from datetime import datetime

from test_two_agent_simulation import TwoAgentSimulation
from integro.config import ConfigStorage, AgentLoader
from integro.utils.logging import get_logger
from convert_simulation_to_markdown import load_simulation, convert_to_markdown

logger = get_logger(__name__)


class RateLimiter:
    """
    Manages API rate limits by tracking actual token usage from API responses.
    Uses Groq API usage statistics and rate limit headers to stay within limits.
    """

    def __init__(self, tokens_per_minute: int = 250_000, safety_margin: float = 0.85):
        """
        Args:
            tokens_per_minute: TPM limit from Groq (250K for developer plan)
            safety_margin: Use only this fraction of limit (0.85 = 85%)
        """
        self.tokens_per_minute = int(tokens_per_minute * safety_margin)
        self.tokens_used = 0
        self.window_start = time.time()
        self.lock = asyncio.Lock()
        self.total_tokens_tracked = 0
        print(f"[RATE LIMIT] Initialized with {self.tokens_per_minute:,} TPM limit (85% of {tokens_per_minute:,})")

    async def wait_if_needed(self, estimated_tokens: int = 8000):
        """Wait if we're approaching the rate limit."""
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
                wait_time = 60 - elapsed
                if wait_time > 0:
                    print(f"  [RATE LIMIT] Near limit: {self.tokens_used:,}/{self.tokens_per_minute:,} tokens used")
                    print(f"  [RATE LIMIT] Waiting {wait_time:.1f}s for window reset...")
                    await asyncio.sleep(wait_time + 0.5)
                    self.tokens_used = 0
                    self.window_start = time.time()

    async def record_usage(self, tokens: int):
        """Record actual token usage from API response."""
        async with self.lock:
            self.tokens_used += tokens
            self.total_tokens_tracked += tokens


async def run_single_simulation(
    storage: ConfigStorage,
    agent_loader: AgentLoader,
    workflow_agent_id: str,
    paul_agent_id: str,
    simulation_number: int,
    max_turns: int,
    batch_timestamp: str,
    output_folder: Path,
    initial_prompt: str,
    rate_limiter: RateLimiter
) -> dict:
    """Run a single simulation between workflow and Paul persona."""
    print(f"  [{simulation_number:02d}] Paul - Starting...")

    try:
        # Wait if needed before starting simulation
        await rate_limiter.wait_if_needed()

        # Create new simulation instance
        sim = TwoAgentSimulation(
            storage=storage,
            agent_loader=agent_loader,
            system_agent_id=workflow_agent_id,
            user_agent_id=paul_agent_id,
            max_turns=max_turns,
            session_id=f"batch_{batch_timestamp}_paul_sim{simulation_number:02d}"
        )

        # Load agents
        await sim.load_agents()

        # Run conversation
        await sim.run_conversation(initial_prompt=initial_prompt)

        # Save to file
        output_file = output_folder / f"paul_simulation_{simulation_number:02d}.json"
        notes = f"Batch {batch_timestamp}, Paul Persona 4 simulation {simulation_number}"
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
        print(f"  [{simulation_number:02d}] Paul - ✓ Complete ({file_size:.1f} KB, {len(sim.messages)} messages)")

        return {
            'success': True,
            'simulation_number': simulation_number,
            'output_file': output_file,
            'session_id': sim.session_id,
            'message_count': len(sim.messages)
        }

    except Exception as e:
        print(f"  [{simulation_number:02d}] Paul - ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'simulation_number': simulation_number,
            'error': str(e)
        }


async def main():
    """Run 5 simulations with Paul Persona 4 and Intentions Workflow 8."""
    print("\n" + "="*60)
    print("PAUL PERSONA 4 TEST - 5 SIMULATIONS")
    print("="*60 + "\n")

    # Initialize storage and loader
    storage = ConfigStorage()
    agent_loader = AgentLoader()

    # Load all agents
    print("Loading agents...")
    agents = await storage.list_agents()
    print(f"Found {len(agents)} agents\n")

    # Find Intentions Workflow 8
    workflow_agent_id = None
    for agent in agents:
        agent_name_lower = agent['name'].lower()
        if 'intentions' in agent_name_lower and 'workflow' in agent_name_lower and '8' in agent_name_lower:
            workflow_agent_id = agent['id']
            print(f"✓ Found Intentions Workflow 8: {agent['id']}")
            break

    if not workflow_agent_id:
        print("✗ Intentions Workflow 8 not found!")
        return

    # Find Paul Persona 4
    paul_agent_id = None
    for agent in agents:
        agent_name_lower = agent['name'].lower()
        if 'paul' in agent_name_lower and 'persona' in agent_name_lower and '4' in agent_name_lower:
            paul_agent_id = agent['id']
            print(f"✓ Found Paul Persona 4: {agent['id']}")
            break

    if not paul_agent_id:
        print("✗ Paul Persona 4 not found!")
        return

    # Create output folder
    batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = Path("Agents/batch_simulations") / f"paul_batch_{batch_timestamp}"
    output_folder.mkdir(parents=True, exist_ok=True)
    print(f"✓ Output folder: {output_folder}\n")

    # Initialize rate limiter
    rate_limiter = RateLimiter(tokens_per_minute=250_000, safety_margin=0.85)

    # Initial prompt for Tegra
    initial_prompt = """You're starting intention-setting work with someone.

Intentions work like a compass - they point toward what matters without forcing the destination.

I'll help you build 3 intentions.

What brought you to this work?"""

    # Run 5 simulations sequentially
    print(f"Running 5 simulations...\n")
    start_time = time.time()

    results = []
    for i in range(1, 6):
        result = await run_single_simulation(
            storage=storage,
            agent_loader=agent_loader,
            workflow_agent_id=workflow_agent_id,
            paul_agent_id=paul_agent_id,
            simulation_number=i,
            max_turns=20,
            batch_timestamp=batch_timestamp,
            output_folder=output_folder,
            initial_prompt=initial_prompt,
            rate_limiter=rate_limiter
        )
        results.append(result)

    # Summary
    elapsed_time = time.time() - start_time
    successful = [r for r in results if r['success']]

    print("\n" + "="*60)
    print("BATCH COMPLETE")
    print("="*60)
    print(f"Successful: {len(successful)}/5")
    print(f"Failed: {5-len(successful)}/5")
    print(f"Total time: {elapsed_time:.1f}s")
    print(f"Avg time per simulation: {elapsed_time/5:.1f}s")
    print(f"Total tokens tracked: {rate_limiter.total_tokens_tracked:,}")
    print(f"Output folder: {output_folder}")
    print("="*60 + "\n")

    if successful:
        print(f"Paul simulations:")
        for r in sorted(successful, key=lambda x: x['simulation_number']):
            file_size = r['output_file'].stat().st_size / 1024
            print(f"  - {r['output_file'].name} ({file_size:.1f} KB, {r['message_count']} messages)")
        print()


if __name__ == "__main__":
    asyncio.run(main())
