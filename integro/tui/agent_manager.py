"""TUI for managing agents."""

import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from textual import on, work
from textual.app import App, ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Header, Footer, Static, Button, Input, TextArea,
    DataTable, Label, Select, Switch, ListView, ListItem,
    LoadingIndicator, Placeholder
)
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer, Grid
from textual.binding import Binding
from textual.worker import get_current_worker
from rich.text import Text

from integro.config import AgentLoader, AgentConfig, ConfigStorage
from integro.utils.logging import get_logger

logger = get_logger(__name__)


class AgentEditScreen(ModalScreen[Optional[AgentConfig]]):
    """Modal screen for editing agent configuration."""
    
    CSS = """
    AgentEditScreen {
        align: center middle;
    }
    
    #dialog {
        width: 80;
        height: 40;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    
    #form-container {
        height: 1fr;
        overflow-y: auto;
    }
    
    .form-field {
        height: auto;
        margin: 1 0;
    }
    
    Input, TextArea {
        width: 100%;
    }
    
    #instructions {
        height: 8;
    }
    
    #models {
        height: 6;
    }
    
    #buttons {
        dock: bottom;
        height: 3;
        align: center middle;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    def __init__(self, agent_config: Optional[AgentConfig] = None):
        """Initialize edit screen."""
        super().__init__()
        self.agent_config = agent_config or AgentLoader.create_default_config("New Agent")
    
    def compose(self) -> ComposeResult:
        """Compose the modal UI."""
        with Vertical(id="dialog"):
            yield Label("Edit Agent Configuration")
            
            with ScrollableContainer(id="form-container"):
                with Vertical(classes="form-field"):
                    yield Label("Name:")
                    yield Input(
                        value=self.agent_config.name,
                        placeholder="Agent name",
                        id="name"
                    )
                
                with Vertical(classes="form-field"):
                    yield Label("Description:")
                    yield Input(
                        value=self.agent_config.description,
                        placeholder="Agent description",
                        id="description"
                    )
                
                with Vertical(classes="form-field"):
                    yield Label("User ID:")
                    yield Input(
                        value=self.agent_config.user_id,
                        placeholder="User ID",
                        id="user_id"
                    )
                
                with Vertical(classes="form-field"):
                    yield Label("Instructions (one per line):")
                    yield TextArea(
                        "\n".join(self.agent_config.instructions),
                        id="instructions"
                    )
                
                with Vertical(classes="form-field"):
                    yield Label("Models (JSON format):")
                    models_text = ""
                    for model in self.agent_config.models:
                        models_text += f"{model}\n"
                    yield TextArea(models_text, id="models")
                
                with Grid(classes="form-field"):
                    yield Label("Stream:")
                    yield Switch(value=self.agent_config.stream, id="stream")
                    yield Label("Markdown:")
                    yield Switch(value=self.agent_config.markdown, id="markdown")
                    yield Label("Memory:")
                    yield Switch(value=self.agent_config.enable_memory, id="memory")
                    yield Label("Storage:")
                    yield Switch(value=self.agent_config.enable_storage, id="storage")
            
            with Horizontal(id="buttons"):
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", variant="default", id="cancel")
    
    @on(Button.Pressed, "#save")
    def save_agent(self) -> None:
        """Save agent configuration."""
        # Ben, gather form data
        self.agent_config.name = self.query_one("#name", Input).value
        self.agent_config.description = self.query_one("#description", Input).value
        self.agent_config.user_id = self.query_one("#user_id", Input).value
        
        # Ben, parse instructions
        instructions_text = self.query_one("#instructions", TextArea).text
        self.agent_config.instructions = [
            line.strip() for line in instructions_text.split("\n") if line.strip()
        ]
        
        # Ben, get switches
        self.agent_config.stream = self.query_one("#stream", Switch).value
        self.agent_config.markdown = self.query_one("#markdown", Switch).value
        self.agent_config.enable_memory = self.query_one("#memory", Switch).value
        self.agent_config.enable_storage = self.query_one("#storage", Switch).value
        
        self.dismiss(self.agent_config)
    
    @on(Button.Pressed, "#cancel")
    def cancel_edit(self) -> None:
        """Cancel editing."""
        self.dismiss(None)


class AgentManagerApp(App[None]):
    """TUI application for managing agents."""
    
    CSS = """
    #main-container {
        layout: horizontal;
    }
    
    #list-panel {
        width: 60%;
        border-right: solid $primary;
    }
    
    #agents-table {
        height: 1fr;
    }
    
    #details-panel {
        width: 40%;
        padding: 1;
    }
    
    #button-bar {
        dock: bottom;
        height: 3;
        background: $panel;
        align: center middle;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("n", "new_agent", "New"),
        Binding("e", "edit_agent", "Edit"),
        Binding("d", "delete_agent", "Delete"),
        Binding("r", "refresh", "Refresh"),
    ]
    
    def __init__(self, storage_path: str = "configs.db"):
        """Initialize agent manager."""
        super().__init__()
        self.storage_path = storage_path
        self.storage: Optional[ConfigStorage] = None
        self.loader = AgentLoader()
        self.agents: List[AgentConfig] = []
        self.selected_agent: Optional[AgentConfig] = None
    
    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header()
        
        with Container(id="main-container"):
            with Vertical(id="list-panel"):
                yield DataTable(id="agents-table")
                
                with Horizontal(id="button-bar"):
                    yield Button("New", id="new", variant="primary")
                    yield Button("Edit", id="edit")
                    yield Button("Delete", id="delete", variant="error")
                    yield Button("Refresh", id="refresh")
            
            with ScrollableContainer(id="details-panel"):
                yield Static("Select an agent to view details", id="details")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize on mount."""
        # Ben, initialize storage
        self.storage = ConfigStorage(self.storage_path)
        
        # Ben, set up data table
        table = self.query_one("#agents-table", DataTable)
        table.add_columns("Name", "Description", "User", "KB")
        table.cursor_type = "row"
        
        # Ben, load agents
        self.load_agents()
    
    @work(exclusive=True)
    async def load_agents(self) -> None:
        """Load agents from storage."""
        try:
            if not self.storage:
                return
                
            agents_list = await self.storage.list_agents()
            
            # Ben, in async workers we call directly, no call_from_thread needed
            self.update_agents_table(agents_list)
            
        except Exception as e:
            logger.error(f"Error loading agents: {e}")
            self.notify(f"Error loading agents: {e}", severity="error")
    
    def update_agents_table(self, agents_list: List[Dict]) -> None:
        """Update agents table in main thread."""
        table = self.query_one("#agents-table", DataTable)
        table.clear()
        
        self.agents = []
        for agent_data in agents_list:
            # Ben, we'll load full configs on demand
            self.agents.append(agent_data)
            
            table.add_row(
                agent_data['name'],
                agent_data.get('description', '')[:30],
                agent_data.get('user_id', 'default'),
                "✓" if agent_data.get('knowledge_base_id') else "✗"
            )
    
    @on(DataTable.RowSelected, "#agents-table")
    async def on_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection."""
        if 0 <= event.cursor_row < len(self.agents):
            agent_data = self.agents[event.cursor_row]
            # Ben, load full config
            if self.storage:
                self.selected_agent = await self.storage.load_agent(agent_data['id'])
                self.update_details()
    
    def update_details(self) -> None:
        """Update the details panel."""
        if not self.selected_agent:
            return
        
        details = self.query_one("#details", Static)
        
        text = Text()
        text.append(f"{self.selected_agent.name}\n", style="bold cyan")
        text.append(f"\n{self.selected_agent.description}\n\n")
        text.append(f"User: {self.selected_agent.user_id}\n\n")
        
        text.append("Instructions:\n", style="bold")
        for inst in self.selected_agent.instructions[:5]:
            text.append(f"  • {inst}\n")
        
        text.append("\nSettings:\n", style="bold")
        text.append(f"  Stream: {self.selected_agent.stream}\n")
        text.append(f"  Memory: {self.selected_agent.enable_memory}\n")
        text.append(f"  Storage: {self.selected_agent.enable_storage}\n")
        
        details.update(text)
    
    @on(Button.Pressed, "#new")
    async def action_new_agent(self) -> None:
        """Create new agent."""
        # Call the worker method (no await needed - it runs in background)
        self.create_new_agent()
    
    @on(Button.Pressed, "#edit")
    async def action_edit_agent(self) -> None:
        """Edit selected agent."""
        if not self.selected_agent:
            self.notify("No agent selected", severity="warning")
            return
        # Call the worker method (no await needed - it runs in background)
        self.edit_selected_agent()
    
    @on(Button.Pressed, "#delete")
    async def action_delete_agent(self) -> None:
        """Delete selected agent."""
        if not self.selected_agent or not self.storage:
            self.notify("No agent selected", severity="warning")
            return
        # Call the worker method (no await needed - it runs in background)
        self.delete_selected_agent()
    
    @on(Button.Pressed, "#refresh")
    def action_refresh(self) -> None:
        """Refresh agents list."""
        self.load_agents()
        self.notify("Refreshed")
    
    @work(exclusive=True)
    async def create_new_agent(self) -> None:
        """Create new agent with modal."""
        config = await self.push_screen_wait(AgentEditScreen())
        if config and self.storage:
            await self.storage.save_agent(config)
            self.load_agents()
            # Ben, async workers can call notify directly
            self.notify(f"Created: {config.name}")
    
    @work(exclusive=True)
    async def edit_selected_agent(self) -> None:
        """Edit selected agent with modal."""
        config = await self.push_screen_wait(AgentEditScreen(self.selected_agent))
        if config and self.storage:
            await self.storage.save_agent(config)
            self.load_agents()
            # Ben, async workers can call notify directly
            self.notify(f"Updated: {config.name}")
    
    @work(exclusive=True)
    async def delete_selected_agent(self) -> None:
        """Delete selected agent."""
        agent_id = self.selected_agent.name.lower().replace(" ", "_")
        if await self.storage.delete_agent(agent_id):
            self.load_agents()
            # Ben, async workers can call notify directly
            self.notify(f"Deleted: {self.selected_agent.name}")
            self.selected_agent = None
            self.update_details()


if __name__ == "__main__":
    app = AgentManagerApp()
    app.run()