#!/usr/bin/env python3
"""Test storage auto-detection for PostgreSQL and SQLite."""

import os
import asyncio
from dotenv import load_dotenv
from integro.storage.factory import create_storage_adapter, get_storage_info, test_storage_connection
from integro.agent import IntegroAgent
from rich.console import Console
from rich.table import Table
from rich import print

console = Console()

def test_storage_factory():
    """Test the storage factory auto-detection."""
    
    console.print("\n[bold blue]Testing Storage Auto-Detection[/bold blue]\n")
    
    # Get current storage configuration
    info = get_storage_info()
    
    # Create a table for display
    table = Table(title="Storage Configuration", show_header=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Storage Type", info["storage_type"])
    table.add_row("PostgreSQL Available", "✓" if info["has_postgres"] else "✗")
    table.add_row("Railway Environment", info.get("railway_environment", "Not set"))
    
    if info["has_postgres"]:
        table.add_row("PostgreSQL Host", info.get("postgres_host", "Unknown"))
        table.add_row("PostgreSQL Port", str(info.get("postgres_port", "Unknown")))
        table.add_row("PostgreSQL Database", info.get("postgres_database", "Unknown"))
        table.add_row("PostgreSQL User", info.get("postgres_user", "Unknown"))
    
    if info.get("volume_path"):
        table.add_row("Railway Volume Path", info["volume_path"])
    
    console.print(table)
    
    # Test storage creation
    console.print("\n[bold]Testing Storage Creation...[/bold]")
    
    storage = create_storage_adapter(
        name="test_agent",
        enable_storage=True
    )
    
    if storage:
        storage_type = type(storage).__name__
        console.print(f"✓ Successfully created storage: [green]{storage_type}[/green]")
        
        # Check if it's PostgreSQL or SQLite
        if hasattr(storage, 'db_url'):
            console.print(f"  Using PostgreSQL with schema: {getattr(storage, 'schema', 'default')}")
        elif hasattr(storage, 'db_file'):
            console.print(f"  Using SQLite at: {getattr(storage, 'db_file', 'unknown')}")
    else:
        console.print("[red]✗ Failed to create storage adapter[/red]")
        return False
    
    # Test connection
    console.print("\n[bold]Testing Storage Connection...[/bold]")
    
    if test_storage_connection():
        console.print("✓ Storage connection successful")
    else:
        console.print("[red]✗ Storage connection failed[/red]")
        return False
    
    return True

def test_agent_with_storage():
    """Test creating an agent with auto-detected storage."""
    
    console.print("\n[bold blue]Testing Agent with Auto-Detected Storage[/bold blue]\n")
    
    try:
        # Create agent - storage will be auto-detected
        agent = IntegroAgent(
            name="TestAgent",
            description="Agent for testing storage",
            models=[{"provider": "groq", "model_id": "moonshotai/kimi-k2-instruct-0905"}],
            enable_storage=True,  # This will trigger auto-detection
            enable_memory=False,   # Disable memory for this test
            user_id="test_user"
        )
        
        console.print("✓ Agent created successfully with auto-detected storage")
        
        # Check what type of storage was created
        if hasattr(agent, 'agent') and hasattr(agent.agent, 'storage'):
            storage = agent.agent.storage
            storage_type = type(storage).__name__
            console.print(f"  Storage type: [green]{storage_type}[/green]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Failed to create agent: {e}[/red]")
        return False

async def test_async_operations():
    """Test async operations with the storage."""
    
    console.print("\n[bold blue]Testing Async Storage Operations[/bold blue]\n")
    
    try:
        # Create storage adapter
        storage = create_storage_adapter(
            name="async_test",
            enable_storage=True
        )
        
        if not storage:
            console.print("[red]✗ Failed to create storage for async test[/red]")
            return False
        
        # Test getting session IDs (this should work for both PostgreSQL and SQLite)
        if hasattr(storage, 'get_all_session_ids'):
            session_ids = storage.get_all_session_ids("test_user")
            console.print(f"✓ Retrieved session IDs: {len(session_ids) if session_ids else 0} sessions")
        
        console.print("✓ Async operations completed successfully")
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Async operations failed: {e}[/red]")
        return False

def main():
    """Run all storage tests."""
    
    # Load environment variables
    load_dotenv()
    
    console.print("[bold magenta]═" * 60 + "[/bold magenta]")
    console.print("[bold magenta]Storage Auto-Detection Test Suite[/bold magenta]")
    console.print("[bold magenta]═" * 60 + "[/bold magenta]")
    
    # Show current environment
    console.print("\n[bold]Environment Variables:[/bold]")
    console.print(f"  DATABASE_URL: {'[green]Set[/green]' if os.getenv('DATABASE_URL') else '[yellow]Not set[/yellow]'}")
    console.print(f"  RAILWAY_ENVIRONMENT: {os.getenv('RAILWAY_ENVIRONMENT', '[yellow]Not set[/yellow]')}")
    console.print(f"  RAILWAY_VOLUME_MOUNT_PATH: {os.getenv('RAILWAY_VOLUME_MOUNT_PATH', '[yellow]Not set[/yellow]')}")
    
    # Run tests
    tests_passed = []
    
    # Test 1: Storage Factory
    tests_passed.append(test_storage_factory())
    
    # Test 2: Agent with Storage
    tests_passed.append(test_agent_with_storage())
    
    # Test 3: Async Operations
    asyncio.run(test_async_operations())
    
    # Summary
    console.print("\n[bold magenta]═" * 60 + "[/bold magenta]")
    console.print("[bold]Test Summary:[/bold]")
    
    passed = sum(tests_passed)
    total = len(tests_passed)
    
    if passed == total:
        console.print(f"[bold green]✓ All {total} tests passed![/bold green]")
    else:
        console.print(f"[bold yellow]⚠ {passed}/{total} tests passed[/bold yellow]")
    
    console.print("[bold magenta]═" * 60 + "[/bold magenta]\n")

if __name__ == "__main__":
    main()