#!/usr/bin/env python3
"""
Export all agents from the database to YAML files.
Run: docker exec integro_simulation_backend python export_agents.py
"""
import asyncio
import os
from pathlib import Path
from integro.config import ConfigStorage, AgentLoader

async def export_all_agents():
    """Export all agents from database to configs/agents/ directory"""

    storage = ConfigStorage('configs.db')
    loader = AgentLoader()

    # Create output directory
    output_dir = Path('/app/configs/agents')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all agents
    agents = await storage.list_agents()

    print(f"Found {len(agents)} agents to export")
    print("-" * 50)

    exported = []
    failed = []

    for agent_summary in agents:
        agent_id = agent_summary['id']
        agent_name = agent_summary['name']

        try:
            # Load full agent config
            config = await storage.load_agent(agent_id)

            if config:
                # Create safe filename
                safe_name = agent_id.replace(' ', '_').replace('/', '_').lower()
                output_file = output_dir / f"{safe_name}.yaml"

                # Save to YAML
                loader.save_to_file(config, output_file)

                exported.append(agent_name)
                print(f"✓ Exported: {agent_name}")
                print(f"  → {output_file}")
            else:
                failed.append(f"{agent_name} (not found)")
                print(f"✗ Failed: {agent_name} (not found)")

        except Exception as e:
            failed.append(f"{agent_name} ({str(e)})")
            print(f"✗ Failed: {agent_name}")
            print(f"  Error: {e}")

    print("-" * 50)
    print(f"Exported: {len(exported)} agents")
    if failed:
        print(f"Failed: {len(failed)} agents")
        for f in failed:
            print(f"  - {f}")

    print(f"\nAll agents exported to: {output_dir}")
    print("You can now commit this directory to git!")

if __name__ == "__main__":
    asyncio.run(export_all_agents())
