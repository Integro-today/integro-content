"""TUI chat application for testing agents."""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from textual import on, work
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Header, Footer, Static, Button, Input, 
    Select, Label, LoadingIndicator, RichLog
)
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.binding import Binding
from textual.message import Message
from textual.worker import get_current_worker
from rich.text import Text
from rich.markdown import Markdown

from integro.config import AgentLoader, ConfigStorage, KnowledgeBaseLoader
from integro.agent import IntegroAgent
from integro.utils.logging import get_logger

logger = get_logger(__name__)


class ChatApp(App[None]):
    """TUI chat application for testing agents."""
    
    CSS = """
    #main {
        layout: horizontal;
    }
    
    #sidebar {
        width: 30;
        background: $panel;
        padding: 1;
    }
    
    #chat-area {
        width: 1fr;
    }
    
    #messages {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }
    
    #input-area {
        dock: bottom;
        height: 3;
        padding: 0 1;
    }
    
    #message-input {
        width: 1fr;
    }
    
    Select {
        margin: 1 0;
    }
    
    Button {
        margin: 1 0;
    }
    
    .status {
        height: 3;
        border: solid $secondary;
        padding: 1;
        margin: 1 0;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+l", "clear", "Clear"),
        Binding("ctrl+n", "new_session", "New Session"),
    ]
    
    def __init__(self, storage_path: str = "configs.db"):
        """Initialize chat app."""
        super().__init__()
        self.storage_path = storage_path
        self.storage: Optional[ConfigStorage] = None
        self.agent_loader = AgentLoader()
        self.kb_loader = KnowledgeBaseLoader()
        
        self.agents: Dict[str, Any] = {}
        self.kbs: Dict[str, Any] = {}
        self.current_agent: Optional[IntegroAgent] = None
        self.current_kb = None
        self.session_id = datetime.now().isoformat()
        self.is_processing = False
    
    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header()
        
        with Container(id="main"):
            # Ben, sidebar
            with Vertical(id="sidebar"):
                yield Label("Agent Selection")
                yield Select(
                    [],
                    id="agent-select",
                    prompt="Select an agent"
                )
                
                yield Label("Knowledge Base")
                yield Select(
                    [],
                    id="kb-select",
                    prompt="Select KB (optional)"
                )
                
                yield Button("Load Agent", id="load", variant="primary")
                yield Button("New Session", id="new-session")
                yield Button("Clear Chat", id="clear-chat")
                
                yield Static("No agent loaded", id="status", classes="status")
            
            # Ben, chat area
            with Vertical(id="chat-area"):
                yield RichLog(id="messages", wrap=True, highlight=True, markup=True)
                
                with Horizontal(id="input-area"):
                    yield Input(
                        placeholder="Type your message...",
                        id="message-input"
                    )
                    yield Button("Send", id="send", variant="primary")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize on mount."""
        # Ben, initialize storage
        self.storage = ConfigStorage(self.storage_path)
        
        # Ben, load options
        self.load_agents()
        self.load_kbs()
        
        # Ben, focus input
        self.query_one("#message-input", Input).focus()
    
    @work(exclusive=True)
    async def load_agents(self) -> None:
        """Load available agents."""
        try:
            if not self.storage:
                return
                
            agents_list = await self.storage.list_agents()
            
            # Ben, async workers can update UI directly
            self.update_agent_select(agents_list)
            
        except Exception as e:
            logger.error(f"Error loading agents: {e}")
    
    def update_agent_select(self, agents_list: List[Dict]) -> None:
        """Update agent select widget."""
        agent_select = self.query_one("#agent-select", Select)
        
        options = []
        self.agents = {}
        
        for agent_data in agents_list:
            agent_id = agent_data['id']
            agent_name = agent_data['name']
            options.append((agent_name, agent_id))
            self.agents[agent_id] = agent_data
        
        agent_select.set_options(options)
    
    @work(exclusive=True)
    async def load_kbs(self) -> None:
        """Load available knowledge bases."""
        try:
            if not self.storage:
                return
                
            kb_list = await self.storage.list_knowledge_bases()
            
            # Ben, async workers can update UI directly
            self.update_kb_select(kb_list)
            
        except Exception as e:
            logger.error(f"Error loading KBs: {e}")
    
    def update_kb_select(self, kb_list: List[Dict]) -> None:
        """Update KB select widget."""
        kb_select = self.query_one("#kb-select", Select)
        
        options = [("None", "none")]
        self.kbs = {}
        
        for kb_data in kb_list:
            kb_id = kb_data['id']
            kb_name = kb_data['name']
            options.append((kb_name, kb_id))
            self.kbs[kb_id] = kb_data
        
        kb_select.set_options(options)
    
    @on(Button.Pressed, "#load")
    def on_load_pressed(self) -> None:
        """Handle load button."""
        agent_select = self.query_one("#agent-select", Select)
        kb_select = self.query_one("#kb-select", Select)
        
        if not agent_select.value:
            self.notify("Please select an agent", severity="warning")
            return
        
        agent_id = agent_select.value
        kb_id = kb_select.value if kb_select.value != "none" else None
        
        self.load_agent(agent_id, kb_id)
    
    @work(exclusive=True)
    async def load_agent(self, agent_id: str, kb_id: Optional[str] = None) -> None:
        """Load an agent with optional knowledge base."""
        try:
            if not self.storage:
                return
                
            # Ben, async workers can update UI directly
            self.update_status("Loading agent...")
            
            # Ben, load configurations
            agent_config = await self.storage.load_agent(agent_id)
            if not agent_config:
                self.notify(f"Agent {agent_id} not found", severity="error")
                return
            
            # Ben, load knowledge base if specified
            kb = None
            if kb_id:
                kb_config = await self.storage.load_knowledge_base(kb_id)
                if kb_config:
                    kb = self.kb_loader.create_knowledge_base(kb_config)
                    self.current_kb = kb
            
            # Ben, create agent
            agent = self.agent_loader.create_agent(
                agent_config,
                knowledge_base=kb
            )
            
            # Ben, initialize agent
            await agent.initialize()
            
            # Ben, async workers can update UI directly
            self.set_current_agent(agent, agent_config.name, kb_id)
            
        except Exception as e:
            logger.error(f"Error loading agent: {e}")
            self.update_status(f"Error: {e}")
    
    def set_current_agent(self, agent: IntegroAgent, name: str, kb_id: Optional[str]) -> None:
        """Set current agent in main thread."""
        self.current_agent = agent
        self.update_status(f"Agent: {name}\nKB: {kb_id or 'None'}")
        self.add_system_message(f"Agent '{name}' loaded and ready.")
    
    def update_status(self, text: str) -> None:
        """Update status display."""
        status = self.query_one("#status", Static)
        status.update(text)
    
    def add_system_message(self, text: str) -> None:
        """Add system message to chat."""
        messages = self.query_one("#messages", RichLog)
        messages.write(Text(f"[System] {text}", style="yellow"))
    
    def add_user_message(self, text: str) -> None:
        """Add user message to chat."""
        messages = self.query_one("#messages", RichLog)
        messages.write(Text(f"You: {text}", style="cyan"))
    
    def add_assistant_message(self, text: str) -> None:
        """Add assistant message to chat."""
        messages = self.query_one("#messages", RichLog)
        # Ben, render as markdown
        messages.write(Markdown(text))
    
    @on(Input.Submitted, "#message-input")
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        await self.send_message()
    
    @on(Button.Pressed, "#send")
    async def on_send_pressed(self) -> None:
        """Handle send button."""
        await self.send_message()
    
    @work(exclusive=True)
    async def send_message(self) -> None:
        """Send a message to the agent."""
        if self.is_processing:
            return
        
        if not self.current_agent:
            self.notify("No agent loaded", severity="warning")
            return
        
        # Ben, get message
        input_widget = self.query_one("#message-input", Input)
        message_text = input_widget.value.strip()
        
        if not message_text:
            return
        
        # Ben, clear input and show message - direct calls in async workers
        input_widget.clear()
        self.add_user_message(message_text)
        
        self.is_processing = True
        
        try:
            # Ben, run agent
            response = await self.current_agent.arun(
                message=message_text,
                stream=False,  # Ben, simplify for now
                session_id=self.session_id
            )
            
            # Ben, show response
            content = response.content if hasattr(response, 'content') else str(response)
            self.add_assistant_message(content)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.add_system_message(f"Error: {e}")
        finally:
            self.is_processing = False
    
    @on(Button.Pressed, "#clear-chat")
    def action_clear(self) -> None:
        """Clear the chat."""
        messages = self.query_one("#messages", RichLog)
        messages.clear()
        self.add_system_message("Chat cleared")
    
    @on(Button.Pressed, "#new-session")
    def action_new_session(self) -> None:
        """Start new session."""
        self.session_id = datetime.now().isoformat()
        self.action_clear()
        self.add_system_message("New session started")
    
    def action_quit(self) -> None:
        """Quit the app."""
        self.exit()


if __name__ == "__main__":
    app = ChatApp()
    app.run()