#!/usr/bin/env python3
"""Test script for two-agent conversation simulation.

This script demonstrates the agent-to-agent simulation infrastructure by:
1. Loading two agents from the database (using ConfigStorage CRUD operations)
2. Having them converse for 30 messages total (15 rounds)
3. Saving the conversation to a JSON file in the simulation format

The output JSON references agents by their database IDs rather than storing
full configurations, making it lightweight and maintainable.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from integro.config import ConfigStorage, AgentLoader
from integro.agent import IntegroAgent
from integro.utils.logging import get_logger

logger = get_logger(__name__)


class TwoAgentSimulation:
    """Manages a conversation between two agents."""

    def __init__(
        self,
        storage: ConfigStorage,
        agent_loader: AgentLoader,
        system_agent_id: str,
        user_agent_id: str,
        max_turns: int = 15,  # 15 rounds = 30 messages
        session_id: Optional[str] = None,
    ):
        """
        Initialize two-agent simulation.

        Args:
            storage: ConfigStorage instance for database operations
            agent_loader: AgentLoader for creating agent instances
            system_agent_id: Database ID of the "system" agent (responds first)
            user_agent_id: Database ID of the "user" agent (responds second)
            max_turns: Number of conversation rounds (each round = 2 messages)
            session_id: Optional session ID for conversation tracking
        """
        self.storage = storage
        self.agent_loader = agent_loader
        self.system_agent_id = system_agent_id
        self.user_agent_id = user_agent_id
        self.max_turns = max_turns
        self.session_id = session_id or f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Agent instances
        self.system_agent: Optional[IntegroAgent] = None
        self.user_agent: Optional[IntegroAgent] = None

        # Conversation history
        self.messages: Dict[str, str] = {}

        # Seed message (initial prompt sent to system agent)
        self.seed_message: str = ""

    async def load_agents(self):
        """Load both agents from database and initialize them."""
        logger.info(f"Loading system agent: {self.system_agent_id}")
        system_config = await self.storage.load_agent(self.system_agent_id)
        if not system_config:
            raise ValueError(f"System agent '{self.system_agent_id}' not found in database")

        logger.info(f"Loading user agent: {self.user_agent_id}")
        user_config = await self.storage.load_agent(self.user_agent_id)
        if not user_config:
            raise ValueError(f"User agent '{self.user_agent_id}' not found in database")

        # Create agent instances (without knowledge bases for simplicity in this test)
        logger.info("Creating system agent instance...")
        self.system_agent = self.agent_loader.create_agent(system_config, knowledge_base=None)
        await self.system_agent.initialize()

        logger.info("Creating user agent instance...")
        self.user_agent = self.agent_loader.create_agent(user_config, knowledge_base=None)
        await self.user_agent.initialize()

        logger.info("Both agents loaded and initialized successfully")

    async def run_conversation(self, initial_prompt: str = "Begin the conversation."):
        """
        Run the conversation between the two agents.

        Args:
            initial_prompt: The prompt to send to the system agent to generate their opening
        """
        logger.info(f"Starting conversation with {self.max_turns} rounds (40 messages)")

        # Store the seed message
        self.seed_message = initial_prompt

        # System agent receives the prompt and generates their opening message
        logger.info("Turn 0: System agent generating opening message")
        system_session_id = f"{self.session_id}_system"

        # System agent responds to the initial prompt
        system_response = await self.system_agent.arun(
            initial_prompt,
            session_id=system_session_id,
            stream=False
        )

        system_content = system_response.content if hasattr(system_response, 'content') else str(system_response)
        self.messages['system0'] = system_content
        logger.info(f"  System opening: {system_content[:100]}...")

        # Now start the conversation loop
        for turn in range(self.max_turns):
            # User agent responds to system agent's last message
            logger.info(f"Turn {turn}: User agent responding...")
            user_session_id = f"{self.session_id}_user"

            # Get the last system message
            last_system_msg = self.messages.get(f'system{turn}', '')

            if not last_system_msg:
                logger.warning(f"No system message found for turn {turn}, breaking")
                break

            # User agent responds (using proper Agno API)
            user_response = await self.user_agent.arun(
                last_system_msg,  # Message as positional argument per Agno docs
                session_id=user_session_id,
                stream=False
            )

            # Extract content from RunOutput
            user_content = user_response.content if hasattr(user_response, 'content') else str(user_response)
            self.messages[f'user{turn}'] = user_content
            logger.info(f"  User: {user_content[:100]}...")

            # Check if we've reached the max turns
            if turn >= self.max_turns - 1:
                logger.info("Reached maximum turns, ending conversation")
                break

            # System agent responds to user agent (using proper Agno API)
            logger.info(f"Turn {turn}: System agent responding...")
            system_response = await self.system_agent.arun(
                user_content,  # Message as positional argument per Agno docs
                session_id=system_session_id,
                stream=False
            )

            # Extract content from RunOutput
            system_content = system_response.content if hasattr(system_response, 'content') else str(system_response)
            self.messages[f'system{turn + 1}'] = system_content
            logger.info(f"  System: {system_content[:100]}...")

        logger.info(f"Conversation complete with {len(self.messages)} messages")

    def to_json(self, notes: str = "") -> Dict[str, Any]:
        """
        Convert conversation to JSON format matching simulation_template.json.

        Args:
            notes: Optional notes about the simulation

        Returns:
            Dictionary in simulation format
        """
        # Build the output with agent references instead of full configs
        output = {
            "session": self.session_id,
            "datetime": datetime.now().isoformat(),
            "notes": notes,
            "seed_message": self.seed_message,  # The initial prompt sent to system agent
            "system_agent_id": self.system_agent_id,
            "user_agent_id": self.user_agent_id,
            "max_turns": self.max_turns,
        }

        # Add all messages (system0-14, user0-14 for 15 rounds)
        for i in range(self.max_turns):
            system_key = f'system{i}'
            user_key = f'user{i}'
            output[system_key] = self.messages.get(system_key, "")
            output[user_key] = self.messages.get(user_key, "")

        return output

    async def save_to_file(self, output_path: Path, notes: str = ""):
        """
        Save conversation to JSON file.

        Args:
            output_path: Path to save JSON file
            notes: Optional notes about the simulation
        """
        output_data = self.to_json(notes=notes)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Saved conversation to {output_path}")


async def list_available_agents(storage: ConfigStorage):
    """List all agents in the database."""
    agents = await storage.list_agents()

    print("\n=== Available Agents ===")
    for agent in agents:
        print(f"  ID: {agent['id']}")
        print(f"  Name: {agent['name']}")
        print(f"  Description: {agent.get('description', 'N/A')}")
        print(f"  KB: {agent.get('knowledge_base_id', 'None')}")
        print()

    return agents


async def main():
    """Main test function."""
    print("\n" + "="*60)
    print("TWO-AGENT SIMULATION TEST")
    print("="*60)

    # Initialize storage and loader
    storage = ConfigStorage()
    agent_loader = AgentLoader()

    # List available agents
    agents = await list_available_agents(storage)

    if len(agents) < 2:
        print("ERROR: Need at least 2 agents in the database to run simulation")
        print("Please create agents using the web interface or API first")
        return

    # Look for specific agents mentioned by user
    # "Paul Persona 3" and "Intentions Workflow 2"
    system_agent_id = None
    user_agent_id = None

    # Try to find agents by name
    for agent in agents:
        agent_name_lower = agent['name'].lower()
        if 'paul' in agent_name_lower and 'persona' in agent_name_lower:
            if '3' in agent_name_lower or 'pwersona' in agent_name_lower:
                system_agent_id = agent['id']
                print(f"✓ Found Paul Persona 3: {agent['id']}")

        if 'intentions' in agent_name_lower and 'workflow' in agent_name_lower:
            if '2' in agent_name_lower or '1.2' in agent_name_lower:
                user_agent_id = agent['id']
                print(f"✓ Found Intentions Workflow 2: {agent['id']}")

    # Fallback: use first two agents if specific ones not found
    if not system_agent_id or not user_agent_id:
        print("\nNote: Could not find 'Paul Persona 3' or 'Intentions Workflow 2'")
        print("Using first two agents in database for testing...")
        system_agent_id = agents[0]['id']
        user_agent_id = agents[1]['id'] if len(agents) > 1 else agents[0]['id']

    print(f"\nSimulation Configuration:")
    print(f"  System Agent: {system_agent_id}")
    print(f"  User Agent: {user_agent_id}")
    print(f"  Max Turns: 20 (40 messages total)")
    print()

    # Create simulation
    sim = TwoAgentSimulation(
        storage=storage,
        agent_loader=agent_loader,
        system_agent_id=system_agent_id,
        user_agent_id=user_agent_id,
        max_turns=20,  # 20 rounds = 40 messages
    )

    # Load agents
    print("Loading agents from database...")
    try:
        await sim.load_agents()
    except Exception as e:
        print(f"ERROR loading agents: {e}")
        import traceback
        traceback.print_exc()
        return

    # Run conversation
    print("\nStarting conversation...")
    initial_prompt = "As [PERSONA NAME], write your opening message to begin the intention-setting process for your psychedelic journey. Keep it brief (1-3 sentences) and authentic to your character."

    try:
        await sim.run_conversation(initial_prompt=initial_prompt)
    except Exception as e:
        print(f"ERROR during conversation: {e}")
        import traceback
        traceback.print_exc()
        return

    # Save results to Agents folder (relative path for Docker compatibility)
    output_dir = Path("Agents")
    output_file = output_dir / f"simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    notes = f"Test simulation between {system_agent_id} (system) and {user_agent_id} (user)"

    print(f"\nSaving conversation to {output_file}...")
    try:
        await sim.save_to_file(output_file, notes=notes)
        print(f"✓ Successfully saved to {output_file}")
    except Exception as e:
        print(f"ERROR saving file: {e}")
        import traceback
        traceback.print_exc()
        return

    # Print summary
    print("\n" + "="*60)
    print("SIMULATION COMPLETE")
    print("="*60)
    print(f"Session ID: {sim.session_id}")
    print(f"Total Messages: {len(sim.messages)}")
    print(f"Output File: {output_file}")
    print()

    # Show first few exchanges
    print("First exchanges:")
    for i in range(min(3, sim.max_turns)):
        system_msg = sim.messages.get(f'system{i}', '')
        user_msg = sim.messages.get(f'user{i}', '')

        if system_msg:
            print(f"\n[System {i}]: {system_msg[:150]}...")
        if user_msg:
            print(f"[User {i}]: {user_msg[:150]}...")

    print("\n✓ Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
