#!/usr/bin/env python3
"""
Import all agents from configs/agents/ directory to the database.
Run: docker exec integro_simulation_backend python import_agents.py
"""
import asyncio
from pathlib import Path
from integro.config import ConfigStorage, AgentLoader

async def import_all_agents():
    """Import all agents from configs/agents/ directory to database"""

    storage = ConfigStorage('configs.db')
    loader = AgentLoader()

    # Find all YAML files in configs/agents/
    agents_dir = Path('/app/configs/agents')

    if not agents_dir.exists():
        print(f"Error: {agents_dir} does not exist")
        print("Run export_agents.py first to create the directory")
        return

    yaml_files = list(agents_dir.glob('*.yaml')) + list(agents_dir.glob('*.yml'))

    if not yaml_files:
        print(f"No agent config files found in {agents_dir}")
        return

    print(f"Found {len(yaml_files)} agent config files to import")
    print("-" * 50)

    imported = []
    failed = []
    skipped = []

    for yaml_file in sorted(yaml_files):
        try:
            # Load config from file
            config = loader.load_from_file(yaml_file)

            # Check if agent already exists
            existing = await storage.load_agent(config.name)

            if existing:
                skipped.append(config.name)
                print(f"⊘ Skipped: {config.name} (already exists)")
                continue

            # Save to database
            agent_id = await storage.save_agent(config)

            imported.append(config.name)
            print(f"✓ Imported: {config.name}")
            print(f"  ID: {agent_id}")

        except Exception as e:
            failed.append(f"{yaml_file.name} ({str(e)})")
            print(f"✗ Failed: {yaml_file.name}")
            print(f"  Error: {e}")

    print("-" * 50)
    print(f"Imported: {len(imported)} agents")
    if skipped:
        print(f"Skipped: {len(skipped)} agents (already exist)")
    if failed:
        print(f"Failed: {len(failed)} agents")
        for f in failed:
            print(f"  - {f}")

if __name__ == "__main__":
    asyncio.run(import_all_agents())
