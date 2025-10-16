#!/usr/bin/env python3
"""Convert simulation JSON files to readable Markdown format.

Usage:
    python convert_simulation_to_markdown.py <simulation_file.json>
    python convert_simulation_to_markdown.py Agents/batch_simulations/mixed_batch_20251016_174617/paul_simulation_03.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any


def load_simulation(json_path: Path) -> Dict[str, Any]:
    """Load simulation JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def convert_to_markdown(simulation: Dict[str, Any]) -> str:
    """
    Convert simulation JSON to readable Markdown format.

    Args:
        simulation: Simulation dictionary loaded from JSON

    Returns:
        Formatted Markdown string
    """
    # Extract agent names
    system_agent = simulation.get('system_agent_id', 'system')
    user_agent = simulation.get('user_agent_id', 'user')
    session_id = simulation.get('session', 'unknown')
    datetime_str = simulation.get('datetime', 'unknown')
    notes = simulation.get('notes', '')
    seed_message = simulation.get('seed_message', '')
    max_turns = simulation.get('max_turns', 0)

    # Start building markdown
    md_lines = []

    # Header
    md_lines.append(f"# Simulation: {session_id}")
    md_lines.append("")
    md_lines.append(f"**Date**: {datetime_str}")
    md_lines.append(f"**System Agent**: {system_agent}")
    md_lines.append(f"**User Agent**: {user_agent}")
    md_lines.append(f"**Turns**: {max_turns} rounds ({max_turns * 2} messages)")

    if notes:
        md_lines.append(f"**Notes**: {notes}")

    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    # Seed message if present
    if seed_message:
        md_lines.append("## Seed Prompt")
        md_lines.append("")
        md_lines.append(f"*Initial prompt sent to {system_agent}:*")
        md_lines.append("")
        md_lines.append(seed_message)
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    # Conversation
    md_lines.append("## Conversation")
    md_lines.append("")

    # Collect all message keys and sort them
    message_keys = []
    for key in simulation.keys():
        if key.startswith('system') or key.startswith('user'):
            # Extract number from key (e.g., 'system0' -> 0, 'user15' -> 15)
            # Skip metadata keys like 'system_agent_id' and 'user_agent_id'
            try:
                if key.startswith('system'):
                    prefix = 'system'
                    num = int(key[6:])  # len('system') = 6
                else:
                    prefix = 'user'
                    num = int(key[4:])  # len('user') = 4
                message_keys.append((num, prefix, key))
            except ValueError:
                # Skip non-message keys like 'system_agent_id'
                continue

    # Sort by turn number and then by prefix (system comes before user)
    message_keys.sort(key=lambda x: (x[0], 0 if x[1] == 'system' else 1))

    # Process each message
    for turn_num, prefix, key in message_keys:
        message = simulation[key]

        # Determine agent name
        if prefix == 'system':
            agent_name = system_agent
        else:
            agent_name = user_agent

        # Add message to markdown
        md_lines.append(f"**{agent_name}**: {message}")
        md_lines.append("")
        md_lines.append("")

    return "\n".join(md_lines)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python convert_simulation_to_markdown.py <simulation_file.json>")
        print("\nExample:")
        print("  python convert_simulation_to_markdown.py Agents/batch_simulations/mixed_batch_20251016_174617/paul_simulation_03.json")
        sys.exit(1)

    # Get input file path
    json_path = Path(sys.argv[1])

    if not json_path.exists():
        print(f"Error: File not found: {json_path}")
        sys.exit(1)

    if not json_path.suffix == '.json':
        print(f"Error: File must be a .json file: {json_path}")
        sys.exit(1)

    # Load simulation
    print(f"Loading simulation: {json_path}")
    simulation = load_simulation(json_path)

    # Convert to markdown
    print("Converting to Markdown...")
    markdown = convert_to_markdown(simulation)

    # Save to .md file in same directory
    md_path = json_path.with_suffix('.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown)

    # Calculate file sizes
    json_size = json_path.stat().st_size / 1024  # KB
    md_size = md_path.stat().st_size / 1024  # KB

    print(f"✓ Converted successfully!")
    print(f"✓ Output: {md_path}")
    print(f"✓ JSON: {json_size:.1f} KB → Markdown: {md_size:.1f} KB")

    # Show preview
    lines = markdown.split('\n')
    print(f"\nPreview (first 30 lines):")
    print("─" * 70)
    for line in lines[:30]:
        print(line)
    if len(lines) > 30:
        print("...")
        print(f"({len(lines) - 30} more lines)")


if __name__ == "__main__":
    main()
