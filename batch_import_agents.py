#!/usr/bin/env python3
"""
Batch Agent Import Tool

Imports multiple persona or workflow agents from .md files in a directory.

Usage:
    # Import all personas in Agents/personas/
    python batch_import_agents.py Agents/personas/ --type persona

    # Import all workflows in Agents/
    python batch_import_agents.py Agents/ --type workflow --pattern "*workflow*.md"

    # Import with auto-versioning
    python batch_import_agents.py Agents/personas/ --type persona --auto-version

    # Export all to YAML
    python batch_import_agents.py Agents/personas/ --type persona --export

    # Docker usage:
    docker exec integro_simulation_backend python batch_import_agents.py Agents/personas/ --type persona
"""

import asyncio
import argparse
from pathlib import Path
from typing import List
from create_agent_from_md import create_agent_from_md
from integro.utils.logging import get_logger

logger = get_logger(__name__)


async def batch_import_agents(
    directory: Path,
    agent_type: str,
    pattern: str = "*.md",
    auto_version: bool = False,
    export_yaml: bool = False,
    exclude_patterns: List[str] = None
) -> List[str]:
    """
    Batch import agents from a directory.

    Args:
        directory: Directory containing .md files
        agent_type: Either "persona" or "workflow"
        pattern: Glob pattern to match files
        auto_version: Whether to auto-increment versions
        export_yaml: Whether to export configs to YAML
        exclude_patterns: Patterns to exclude (e.g., ["*template*", "*archive*"])

    Returns:
        List of created agent IDs
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    if not directory.is_dir():
        raise ValueError(f"Not a directory: {directory}")

    # Find all matching .md files
    md_files = list(directory.glob(pattern))

    # Apply exclusions
    if exclude_patterns:
        for exclude_pattern in exclude_patterns:
            exclude_files = set(directory.glob(exclude_pattern))
            md_files = [f for f in md_files if f not in exclude_files]

    if not md_files:
        logger.warning(f"No .md files found in {directory} matching pattern '{pattern}'")
        return []

    logger.info(f"Found {len(md_files)} .md files to import")
    print("\n" + "="*70)
    print(f"BATCH IMPORT: {len(md_files)} agents")
    print("="*70)

    created_ids = []
    failed = []

    for i, md_file in enumerate(md_files, 1):
        print(f"\n[{i}/{len(md_files)}] Processing: {md_file.name}")
        try:
            agent_id = await create_agent_from_md(
                file_path=md_file,
                agent_type=agent_type,
                version=None,
                export_yaml=export_yaml,
                auto_version=auto_version
            )
            created_ids.append(agent_id)
            print(f"  ✓ Created: {agent_id}")
        except Exception as e:
            logger.error(f"  ✗ Failed: {e}")
            failed.append((md_file.name, str(e)))

    # Summary
    print("\n" + "="*70)
    print(f"BATCH IMPORT COMPLETE")
    print("="*70)
    print(f"Successfully imported: {len(created_ids)}/{len(md_files)} agents")

    if created_ids:
        print(f"\nCreated agents:")
        for agent_id in created_ids:
            print(f"  - {agent_id}")

    if failed:
        print(f"\nFailed imports ({len(failed)}):")
        for filename, error in failed:
            print(f"  - {filename}: {error}")

    return created_ids


async def main():
    parser = argparse.ArgumentParser(
        description="Batch import agents from .md files in a directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "directory",
        type=str,
        help="Directory containing .md files"
    )

    parser.add_argument(
        "--type",
        choices=["persona", "workflow"],
        required=True,
        help="Agent type: 'persona' or 'workflow'"
    )

    parser.add_argument(
        "--pattern",
        type=str,
        default="*.md",
        help="Glob pattern to match files (default: *.md)"
    )

    parser.add_argument(
        "--auto-version",
        action="store_true",
        help="Auto-increment version numbers for all agents"
    )

    parser.add_argument(
        "--export",
        action="store_true",
        help="Export all configs to YAML files"
    )

    parser.add_argument(
        "--exclude",
        nargs="+",
        help="Patterns to exclude (e.g., --exclude '*template*' '*archive*')"
    )

    args = parser.parse_args()

    directory = Path(args.directory)

    try:
        created_ids = await batch_import_agents(
            directory=directory,
            agent_type=args.type,
            pattern=args.pattern,
            auto_version=args.auto_version,
            export_yaml=args.export,
            exclude_patterns=args.exclude
        )

        if created_ids:
            print(f"\n✓ Batch import successful! Created {len(created_ids)} agents.")
        else:
            print("\n⚠ No agents were created.")

    except Exception as e:
        logger.error(f"Batch import failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
