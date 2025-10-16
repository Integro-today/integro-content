"""TUI applications for Integro."""

from integro.tui.agent_manager import AgentManagerApp
from integro.tui.kb_manager import KnowledgeBaseManagerApp
from integro.tui.chat import ChatApp

__all__ = [
    "AgentManagerApp",
    "KnowledgeBaseManagerApp",
    "ChatApp"
]