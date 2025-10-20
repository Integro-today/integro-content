#!/usr/bin/env python3
"""
Agent Creation Tool

Creates persona or workflow agents from .md files and saves them to the database.

Usage:
    # Create a persona agent
    python create_agent_from_md.py Agents/personas/Paul_Persona_4.md --type persona

    # Create a workflow agent
    python create_agent_from_md.py Agents/intentions_workflow_8.md --type workflow

    # Create with custom version
    python create_agent_from_md.py Agents/personas/Paul_Persona_4.md --type persona --version 5

    # Export to YAML (for version control)
    python create_agent_from_md.py Agents/personas/Paul_Persona_4.md --type persona --export

    # Docker usage:
    docker exec integro_simulation_backend python create_agent_from_md.py Agents/personas/Paul_Persona_4.md --type persona
"""

import asyncio
import argparse
import re
from pathlib import Path
from typing import Optional, Tuple
from integro.config import ConfigStorage, AgentLoader, AgentConfig
from integro.utils.logging import get_logger

logger = get_logger(__name__)

# Systematic naming patterns
PERSONA_NAME_PATTERN = "{name} Persona {version}"
WORKFLOW_NAME_PATTERN = "{name} Workflow {version}"

PERSONA_DESCRIPTION = (
    "A persona agent used for testing therapeutic conversation agents in simulations. "
    "This persona represents a specific user archetype with distinct communication patterns, "
    "psychological defense mechanisms, and emotional dynamics."
)

WORKFLOW_DESCRIPTION = (
    "An integration workflow agent that assists users in the Integro psychedelic integration platform. "
    "This agent guides users through structured therapeutic processes and integration work."
)


def parse_md_file(file_path: Path) -> Tuple[str, list[str]]:
    """
    Parse a .md file to extract name and instructions.

    Args:
        file_path: Path to the .md file

    Returns:
        Tuple of (extracted_name, instructions_list)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split into lines for instructions
    lines = content.split('\n')
    instructions = [line for line in lines if line.strip()]

    # Try to extract name from file path or content
    file_name = file_path.stem

    # Try to find name in first header
    name_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if name_match:
        extracted_name = name_match.group(1).strip()
    else:
        # Fall back to file name
        extracted_name = file_name.replace('_', ' ').title()

    # Clean up version markers and type suffixes from extracted name
    # Remove patterns like "(v2.0)", "v2.0", "- v2.0"
    extracted_name = re.sub(r'\s*[\(\-]?\s*v[\d.]+\s*[\)]?', '', extracted_name, flags=re.IGNORECASE)

    # Remove "Persona X" or "Workflow X" suffixes (where X is a number)
    extracted_name = re.sub(r'\s+Persona\s+\d+\s*$', '', extracted_name, flags=re.IGNORECASE)
    extracted_name = re.sub(r'\s+Workflow\s+\d+\s*$', '', extracted_name, flags=re.IGNORECASE)

    # Remove standalone "Persona" or "Workflow" at the end
    extracted_name = re.sub(r'\s+Persona\s*$', '', extracted_name, flags=re.IGNORECASE)
    extracted_name = re.sub(r'\s+Workflow\s*$', '', extracted_name, flags=re.IGNORECASE)

    # Remove "- Workflow" or "- Persona" style suffixes
    extracted_name = re.sub(r'\s*-\s*Workflow.*$', '', extracted_name, flags=re.IGNORECASE)
    extracted_name = re.sub(r'\s*-\s*Persona.*$', '', extracted_name, flags=re.IGNORECASE)

    return extracted_name.strip(), instructions


def extract_version_from_name(name: str) -> Optional[int]:
    """Extract version number from agent name if present."""
    match = re.search(r'(?:Persona|Workflow)\s+(\d+)$', name)
    if match:
        return int(match.group(1))
    return None


def generate_systematic_name(base_name: str, agent_type: str, version: Optional[int] = None) -> str:
    """
    Generate a systematic agent name following version control conventions.

    Args:
        base_name: Base name extracted from file (e.g., "Paul", "Intentions")
        agent_type: Either "persona" or "workflow"
        version: Optional version number (defaults to 1)

    Returns:
        Formatted agent name (e.g., "Paul Persona 4", "Intentions Workflow 8")
    """
    if version is None:
        version = 1

    # Clean up base name
    base_name = base_name.strip()

    if agent_type == "persona":
        return PERSONA_NAME_PATTERN.format(name=base_name, version=version)
    elif agent_type == "workflow":
        return WORKFLOW_NAME_PATTERN.format(name=base_name, version=version)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")


async def find_next_version(storage: ConfigStorage, base_name: str, agent_type: str) -> int:
    """
    Find the next available version number for an agent.

    Args:
        storage: ConfigStorage instance
        base_name: Base name (e.g., "Paul", "Intentions")
        agent_type: Either "persona" or "workflow"

    Returns:
        Next available version number
    """
    agents = await storage.list_agents()

    # Pattern to match existing agents
    if agent_type == "persona":
        pattern = re.compile(rf"^{re.escape(base_name)}\s+Persona\s+(\d+)$", re.IGNORECASE)
    else:
        pattern = re.compile(rf"^{re.escape(base_name)}\s+Workflow\s+(\d+)$", re.IGNORECASE)

    max_version = 0
    for agent in agents:
        match = pattern.match(agent['name'])
        if match:
            version = int(match.group(1))
            max_version = max(max_version, version)

    return max_version + 1


async def create_agent_from_md(
    file_path: Path,
    agent_type: str,
    version: Optional[int] = None,
    export_yaml: bool = False,
    auto_version: bool = False
) -> str:
    """
    Create an agent from a .md file and save to database.

    Args:
        file_path: Path to .md file
        agent_type: Either "persona" or "workflow"
        version: Optional version number
        export_yaml: Whether to export config to YAML
        auto_version: Whether to auto-increment version

    Returns:
        Agent ID
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if agent_type not in ["persona", "workflow"]:
        raise ValueError(f"agent_type must be 'persona' or 'workflow', got: {agent_type}")

    # Parse the markdown file
    logger.info(f"Parsing {file_path}...")
    base_name, instructions = parse_md_file(file_path)
    logger.info(f"Extracted base name: {base_name}")

    # Initialize storage
    storage = ConfigStorage()

    # Determine version
    if auto_version:
        version = await find_next_version(storage, base_name, agent_type)
        logger.info(f"Auto-detected next version: {version}")
    elif version is None:
        # Try to extract from existing name in file
        existing_version = extract_version_from_name(base_name)
        if existing_version:
            version = existing_version
        else:
            version = await find_next_version(storage, base_name, agent_type)
            logger.info(f"No version specified, using next available: {version}")

    # Generate systematic name
    agent_name = generate_systematic_name(base_name, agent_type, version)
    logger.info(f"Generated agent name: {agent_name}")

    # Set appropriate description
    description = PERSONA_DESCRIPTION if agent_type == "persona" else WORKFLOW_DESCRIPTION

    # Create agent config
    agent_config = AgentConfig(
        name=agent_name,
        description=description,
        user_id="default",
        models=[
            {
                "provider": "groq",
                "model_id": "moonshotai/kimi-k2-instruct-0905",
                "params": {"temperature": 0.7}
            }
        ],
        tools=[],
        instructions=instructions,
        knowledge_base_id=None,
        stream=False,
        stream_intermediate_steps=False,
        markdown=True,
        tool_call_limit=20,
        enable_memory=True,
        memory_type="sqlite",
        memory_config={},
        enable_storage=True,
        storage_db_file="sessions.db",
        add_history_to_messages=True,
        num_history_runs=5,
        search_knowledge=True,
        add_references=False,
        session_state={},
        add_state_in_messages=True,
        context={},
        add_context=True,
        reasoning=False,
        reasoning_model=None,
        response_model=None,
        use_json_mode=False,
        version="1.0"
    )

    # Save to database
    logger.info(f"Saving agent '{agent_name}' to database...")
    agent_id = await storage.save_agent(agent_config)
    logger.info(f"✓ Agent saved with ID: {agent_id}")

    # Optional: Export to YAML for version control
    if export_yaml:
        loader = AgentLoader()
        yaml_path = Path("configs/agents") / f"{agent_id}.yaml"
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        loader.save_to_file(agent_config, yaml_path)
        logger.info(f"✓ Exported to: {yaml_path}")

    return agent_id


async def main():
    parser = argparse.ArgumentParser(
        description="Create agent from .md file and save to database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "file",
        type=str,
        help="Path to .md file (e.g., Agents/personas/Paul_Persona_4.md)"
    )

    parser.add_argument(
        "--type",
        choices=["persona", "workflow"],
        required=True,
        help="Agent type: 'persona' for testing agents, 'workflow' for therapeutic agents"
    )

    parser.add_argument(
        "--version",
        type=int,
        help="Version number (default: auto-detect or increment from existing)"
    )

    parser.add_argument(
        "--auto-version",
        action="store_true",
        help="Auto-increment version number based on existing agents"
    )

    parser.add_argument(
        "--export",
        action="store_true",
        help="Export config to YAML file in configs/agents/ for version control"
    )

    args = parser.parse_args()

    file_path = Path(args.file)

    try:
        agent_id = await create_agent_from_md(
            file_path=file_path,
            agent_type=args.type,
            version=args.version,
            export_yaml=args.export,
            auto_version=args.auto_version
        )

        print("\n" + "="*70)
        print(f"✓ SUCCESS: Agent created with ID: {agent_id}")
        print("="*70)
        print(f"\nYou can now use this agent in simulations or through the web interface.")
        print(f"View at: http://localhost:8889/agents/{agent_id}")

    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
