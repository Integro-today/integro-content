"""Base activity class for all therapeutic activities."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from enum import Enum
import logging

# Direct Agno v2 imports
from agno.agent import Agent
from agno.models.groq import Groq
from agno.models.openai import OpenAIChat as OpenAI

logger = logging.getLogger(__name__)


class ActivityState(Enum):
    """States for activity lifecycle."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class BaseActivity(ABC):
    """
    Base class for all therapeutic activities.
    
    This abstract class defines the interface that all activities must implement
    for proper integration with the TherapeuticWorkflow.
    """
    
    def __init__(self, name: str, description: str, duration_estimate: str):
        """
        Initialize base activity.
        
        Args:
            name: Activity name (e.g., "Byron Katie's The Work")
            description: Brief description of the activity
            duration_estimate: Estimated time (e.g., "15-20 minutes")
        """
        self.name = name
        self.description = description
        self.duration_estimate = duration_estimate
        self.state = ActivityState.NOT_STARTED
        self.activity_data = {}
        
    @abstractmethod
    def create_agent(self) -> Agent:
        """
        Create and return the agent for this activity.
        
        Must be called at module level for Agno compliance.
        
        Returns:
            Agent configured for this activity
        """
        pass
    
    async def load_knowledge_base(self):
        """
        Load knowledge base for this activity if configured.
        
        Override in subclasses that need knowledge base integration.
        
        Returns:
            KnowledgeBase instance or None
        """
        return None
    
    @abstractmethod
    def get_welcome_message(self) -> str:
        """
        Get the welcome message when starting this activity.
        
        Returns:
            Welcome message string
        """
        pass
    
    @abstractmethod
    def get_completion_message(self) -> str:
        """
        Get the completion message when finishing this activity.
        
        Returns:
            Thoughtful completion message
        """
        pass
    
    @abstractmethod
    def track_progress(self, message: str, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track progress for this specific activity.
        
        Args:
            message: User's message
            activity_data: Current activity data
            
        Returns:
            Updated activity data
        """
        pass
    
    @abstractmethod
    def is_naturally_complete(self, activity_data: Dict[str, Any]) -> bool:
        """
        Check if the activity has reached its natural completion point.
        
        Args:
            activity_data: Current activity data
            
        Returns:
            True if naturally complete
        """
        pass
    
    def get_instructions(self) -> list:
        """
        Get agent instructions for this activity.
        
        Returns:
            List of instruction strings
        """
        return []
    
    def get_model(self) -> Any:
        """
        Get the LLM model for this activity.
        
        Returns:
            Model instance (Groq or OpenAI)
        """
        import os
        provider = os.getenv('DEFAULT_LLM_PROVIDER', 'groq')
        
        if provider == 'openai' and os.getenv('OPENAI_API_KEY'):
            return OpenAIChat(id="gpt-4o-mini")
        else:
            return Groq(id="moonshotai/kimi-k2-instruct-0905")
    
    def detect_keywords(self, message: str) -> Tuple[Optional[str], float]:
        """
        Detect activity-specific keywords in message.
        
        Args:
            message: User's message
            
        Returns:
            Tuple of (detected_intent, confidence)
        """
        return None, 0.0
    
    def get_state_for_persistence(self) -> Dict[str, Any]:
        """
        Get activity state for persistence.
        
        Returns:
            Dictionary of state to persist
        """
        return {
            "state": self.state.value,
            "activity_data": self.activity_data
        }
    
    def restore_from_state(self, state: Dict[str, Any]):
        """
        Restore activity from persisted state.
        
        Args:
            state: Persisted state dictionary
        """
        if "state" in state:
            self.state = ActivityState(state["state"])
        if "activity_data" in state:
            self.activity_data = state["activity_data"]