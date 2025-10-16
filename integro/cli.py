"""CLI interface for Integro."""

import click
import asyncio
from pathlib import Path
from integro.tui import AgentManagerApp, KnowledgeBaseManagerApp, ChatApp
from integro.config import AgentLoader, KnowledgeBaseLoader, ConfigStorage
from integro.utils.logging import setup_logging, get_logger

logger = get_logger(__name__)


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--storage', default='configs.db', help='Path to storage database')
@click.pass_context
def cli(ctx, debug, storage):
    """Integro - AI Agent Management System."""
    # Ben, set up logging
    setup_logging(level="DEBUG" if debug else "INFO", suppress_warnings=not debug)
    
    # Ben, store context
    ctx.ensure_object(dict)
    ctx.obj['storage'] = storage
    ctx.obj['debug'] = debug


@cli.command()
@click.pass_context
def agents(ctx):
    """Manage agents in TUI."""
    storage_path = ctx.obj['storage']
    app = AgentManagerApp(storage_path)
    app.run()


@cli.command()
@click.pass_context
def knowledge(ctx):
    """Manage knowledge bases in TUI."""
    storage_path = ctx.obj['storage']
    app = KnowledgeBaseManagerApp(storage_path)
    app.run()


@cli.command()
@click.pass_context
def chat(ctx):
    """Chat with agents in TUI."""
    storage_path = ctx.obj['storage']
    app = ChatApp(storage_path)
    app.run()


@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, type=int, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
@click.pass_context
def web(ctx, host, port, reload):
    """Run the web interface server."""
    from integro.web_server import run_server
    
    # Determine log level
    log_level = "debug" if ctx.obj.get('debug') else "info"
    
    click.echo(f"Starting Integro web server on http://{host}:{port}")
    click.echo("Open your browser to access the chat interface")
    if ctx.obj.get('debug'):
        click.echo("Debug logging enabled")
    
    run_server(host=host, port=port, reload=reload, log_level=log_level)


@cli.group()
@click.pass_context
def create(ctx):
    """Create new configurations."""
    pass


@create.command()
@click.argument('name')
@click.option('--description', default='', help='Agent description')
@click.option('--output', '-o', help='Output file path')
@click.option('--format', type=click.Choice(['yaml', 'json']), default='yaml', help='Output format')
@click.pass_context
def agent(ctx, name, description, output, format):
    """Create a new agent configuration."""
    loader = AgentLoader()
    config = loader.create_default_config(name)
    config.description = description or f"AI assistant {name}"
    
    if output:
        file_path = Path(output)
    else:
        file_path = Path(f"{name.lower().replace(' ', '_')}.{format}")
    
    loader.save_to_file(config, file_path)
    click.echo(f"Created agent configuration: {file_path}")


@create.command()
@click.argument('name')
@click.option('--description', default='', help='Knowledge base description')
@click.option('--output', '-o', help='Output file path')
@click.option('--format', type=click.Choice(['yaml', 'json']), default='yaml', help='Output format')
@click.pass_context
def kb(ctx, name, description, output, format):
    """Create a new knowledge base configuration."""
    loader = KnowledgeBaseLoader()
    config = loader.create_default_config(name)
    config.description = description or f"Knowledge base: {name}"
    
    if output:
        file_path = Path(output)
    else:
        file_path = Path(f"{name.lower().replace(' ', '_')}_kb.{format}")
    
    loader.save_to_file(config, file_path)
    click.echo(f"Created knowledge base configuration: {file_path}")


@cli.group()
@click.pass_context
def import_cmd(ctx):
    """Import configurations."""
    pass


@import_cmd.command(name='agent')
@click.argument('file_path', type=click.Path(exists=True))
@click.pass_context
def import_agent(ctx, file_path):
    """Import agent configuration from file."""
    storage = ConfigStorage(ctx.obj['storage'])
    loader = AgentLoader()
    
    try:
        config = loader.load_from_file(file_path)
        
        # Ben, save to storage synchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        agent_id = loop.run_until_complete(storage.save_agent(config))
        loop.close()
        
        click.echo(f"Imported agent '{config.name}' (ID: {agent_id})")
    except Exception as e:
        click.echo(f"Error importing agent: {e}", err=True)


@import_cmd.command(name='kb')
@click.argument('file_path', type=click.Path(exists=True))
@click.pass_context
def import_kb(ctx, file_path):
    """Import knowledge base configuration from file."""
    storage = ConfigStorage(ctx.obj['storage'])
    loader = KnowledgeBaseLoader()
    
    try:
        config = loader.load_from_file(file_path)
        
        # Ben, save to storage synchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        kb_id = loop.run_until_complete(storage.save_knowledge_base(config))
        loop.close()
        
        click.echo(f"Imported knowledge base '{config.name}' (ID: {kb_id})")
    except Exception as e:
        click.echo(f"Error importing KB: {e}", err=True)


@cli.group()
@click.pass_context
def export(ctx):
    """Export configurations."""
    pass


@export.command(name='agent')
@click.argument('agent_id')
@click.option('--output', '-o', help='Output file path')
@click.option('--format', type=click.Choice(['yaml', 'json']), default='yaml', help='Output format')
@click.pass_context
def export_agent(ctx, agent_id, output, format):
    """Export agent configuration to file."""
    storage = ConfigStorage(ctx.obj['storage'])
    loader = AgentLoader()
    
    try:
        # Ben, load from storage
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        config = loop.run_until_complete(storage.load_agent(agent_id))
        loop.close()
        
        if not config:
            click.echo(f"Agent '{agent_id}' not found", err=True)
            return
        
        if output:
            file_path = Path(output)
        else:
            file_path = Path(f"{agent_id}.{format}")
        
        loader.save_to_file(config, file_path)
        click.echo(f"Exported agent to: {file_path}")
    except Exception as e:
        click.echo(f"Error exporting agent: {e}", err=True)


@export.command(name='kb')
@click.argument('kb_id')
@click.option('--output', '-o', help='Output file path')
@click.option('--format', type=click.Choice(['yaml', 'json']), default='yaml', help='Output format')
@click.pass_context
def export_kb(ctx, kb_id, output, format):
    """Export knowledge base configuration to file."""
    storage = ConfigStorage(ctx.obj['storage'])
    loader = KnowledgeBaseLoader()
    
    try:
        # Ben, load from storage
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        config = loop.run_until_complete(storage.load_knowledge_base(kb_id))
        loop.close()
        
        if not config:
            click.echo(f"Knowledge base '{kb_id}' not found", err=True)
            return
        
        if output:
            file_path = Path(output)
        else:
            file_path = Path(f"{kb_id}_kb.{format}")
        
        loader.save_to_file(config, file_path)
        click.echo(f"Exported KB to: {file_path}")
    except Exception as e:
        click.echo(f"Error exporting KB: {e}", err=True)


@cli.command()
@click.pass_context
def list(ctx):
    """List all agents and knowledge bases."""
    storage = ConfigStorage(ctx.obj['storage'])
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Ben, list agents
        agents = loop.run_until_complete(storage.list_agents())
        click.echo("\nAgents:")
        click.echo("-" * 50)
        if agents:
            for agent in agents:
                kb_status = "✓" if agent.get('knowledge_base_id') else "✗"
                click.echo(f"  {agent['id']}: {agent['name']} [KB: {kb_status}]")
        else:
            click.echo("  No agents found")
        
        # Ben, list knowledge bases
        kbs = loop.run_until_complete(storage.list_knowledge_bases())
        click.echo("\nKnowledge Bases:")
        click.echo("-" * 50)
        if kbs:
            for kb in kbs:
                click.echo(f"  {kb['id']}: {kb['name']} ({kb.get('collection_name', 'N/A')})")
        else:
            click.echo("  No knowledge bases found")
        
        loop.close()
        
    except Exception as e:
        click.echo(f"Error listing: {e}", err=True)


@cli.command()
@click.argument('agent_id')
@click.argument('kb_id')
@click.pass_context
def link(ctx, agent_id, kb_id):
    """Link an agent to a knowledge base."""
    storage = ConfigStorage(ctx.obj['storage'])
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success = loop.run_until_complete(storage.link_agent_to_kb(agent_id, kb_id))
        loop.close()
        
        if success:
            click.echo(f"Linked agent '{agent_id}' to KB '{kb_id}'")
        else:
            click.echo(f"Failed to link agent and KB", err=True)
            
    except Exception as e:
        click.echo(f"Error linking: {e}", err=True)


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()