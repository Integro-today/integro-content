"""Therapeutic workflow with Agno v2 compliant implementation."""

import os
import hashlib
import logging
from typing import AsyncIterator, Optional, Dict, Any, Tuple
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

# Direct Agno v2 imports
from agno.workflow import Workflow
from agno.agent import Agent, RunOutput  # v2 uses RunOutput not RunResponse
from agno.models.openai import OpenAIChat as OpenAI
from agno.models.groq import Groq

from integro.activities import (
    get_activity,
    DailyContentActivity,
    IFSActivity,
    ActivityState
)
from integro.services.state_manager import StateManager
from integro.services.intent_detection import IntentDetectionService

logger = logging.getLogger(__name__)


class ActivityType(Enum):
    """Available therapeutic activities."""
    CONVERSATION = "conversation"
    IFS = "ifs"
    DAILY_CONTENT = "daily_content"


class WorkflowInput(BaseModel):
    """Input schema for therapeutic workflow."""
    message: str = Field(description="User message")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    user_id: Optional[str] = Field(default="anonymous", description="User identifier")


# ============================================================================
# CRITICAL: Agent creation at MODULE LEVEL for Agno v2 stateless design
# ============================================================================

# Initialize services at module level
intent_detector = IntentDetectionService()

# Initialize activities at module level
daily_content_activity = DailyContentActivity()
ifs_activity = IFSActivity()


def _create_conversation_agent() -> Agent:
    """Create conversation agent with proper model."""
    provider = os.getenv('DEFAULT_LLM_PROVIDER', 'groq')
    
    if provider == 'openai' and os.getenv('OPENAI_API_KEY'):
        model = OpenAI(id="gpt-4o-mini")
    else:
        model = Groq(id="moonshotai/kimi-k2-instruct-0905")
    
    return Agent(
        id="conversation_assistant",
        name="Conversation Assistant",
        model=model,
        instructions=[
            "You are a compassionate integration guide for psychedelic experiences.",
            "Help users choose between therapeutic activities:",
            "- Daily Content: Brief wisdom and reflection practices (5-10 min)",
            "- Byron Katie's The Work: Question thoughts that arose during your journey (20 min)",
            "- IFS: Explore the parts of yourself revealed in your experience (30 min)",
            "Always be gentle, non-judgmental, and supportive.",
            "If someone seems distressed, offer grounding exercises.",
            "Acknowledge the courage it takes to integrate these experiences."
        ],
        markdown=True
    )


def _create_ifs_agent() -> Agent:
    """Create IFS agent for parts work."""
    return ifs_activity.create_agent()


def _create_daily_content_agent() -> Agent:
    """Create daily content agent with wisdom delivery."""
    return daily_content_activity.create_agent()


# Create agents at module level (stateless in v2)
conversation_agent = _create_conversation_agent()
ifs_agent = _create_ifs_agent()
daily_content_agent = _create_daily_content_agent()


class TherapeuticWorkflow(Workflow):
    """
    Agno v2 compliant therapeutic workflow for psychedelic integration.
    
    CRITICAL: Agents are stateless and created at module level.
    """
    
    id = "therapeutic_workflow"
    name = "Psychedelic Integration Workflow"
    description = "Therapeutic workflow with multiple integration paths"
    input_schema = WorkflowInput
    
    def __init__(self, **kwargs):
        """Initialize workflow with session management."""
        super().__init__(**kwargs)
        
        # Session management will be handled externally for stateless design
        self.state_manager = None
        self.session_state = {}
    
    def _initialize_session(self, session_id: str, user_id: str):
        """Initialize session state management."""
        self.state_manager = StateManager(session_id)
        
        # Initialize session state with activity tracking
        self.session_state = self.state_manager.get_state() or {
            "user_id": user_id,
            "session_id": session_id,
            "current_activity": None,
            "activity_states": {},  # Track state of each activity
            "completed_activities": {},  # Activities marked complete
            "activity_data": {},  # Activity-specific progress data
            "activity_history": [],  # Timeline of activities
            "conversation_history": [],
            "session_start": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        
        # Initialize activity states if not present
        for activity in ActivityType:
            if activity.value not in self.session_state.get("activity_states", {}):
                self.session_state.setdefault("activity_states", {})[activity.value] = ActivityState.NOT_STARTED.value
        
        self.state_manager.update_state(self.session_state)
        logger.info(f"Initialized workflow: session={session_id}, user={user_id}")
    
    async def run(self, input_data: WorkflowInput, **kwargs) -> AsyncIterator[RunOutput]:
        """
        Main workflow execution with Agno v2 async streaming.
        
        Args:
            input_data: Validated input with message, session_id, user_id
            **kwargs: Additional parameters like stream, debug_mode
            
        Yields:
            RunOutput objects for streaming
        """
        # Initialize session if needed
        if not self.state_manager:
            self._initialize_session(
                input_data.session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                input_data.user_id
            )
        
        message = input_data.message
        stream = kwargs.get('stream', True)
        
        try:
            # Check if this is the first interaction
            is_first_interaction = len(self.session_state.get("conversation_history", [])) == 0
            
            # Update conversation history
            self.session_state["conversation_history"].append({
                "role": "user",
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Handle initial session startup with daily content and menu
            if is_first_interaction:
                async for output in self._handle_session_startup():
                    yield output
                return
            
            # Check for completion request
            if intent_detector.detect_completion_request(message):
                async for output in self._handle_activity_completion():
                    yield output
                return
            
            # Check for help/menu request
            if intent_detector.detect_help_request(message):
                async for output in self._show_activity_menu():
                    yield output
                return
            
            # Check if returning from completed activity
            current_activity = self.session_state.get("current_activity")
            if current_activity and self._is_activity_complete(current_activity):
                async for output in self._handle_completed_activity_return():
                    yield output
                return
            
            # Detect intent for activity switching
            intent, confidence = self._detect_intent_safely(message)
            
            # Switch to new activity if high confidence
            if intent and intent != current_activity:
                # Check if trying to enter completed activity
                if self._is_activity_complete(intent):
                    async for output in self._handle_completed_activity_request(intent):
                        yield output
                    return
                
                # Switch to new activity
                if confidence > 0.7 or current_activity is None:
                    async for output in self._switch_activity(intent):
                        yield output
                    current_activity = intent
            
            # Route to appropriate activity handler
            if current_activity == ActivityType.IFS.value:
                async for output in self._run_ifs(message, stream=stream):
                    yield output
                    
            elif current_activity == ActivityType.DAILY_CONTENT.value:
                async for output in self._run_daily_content(message, stream=stream):
                    yield output
                    
            else:
                # Default to conversation mode
                async for output in self._run_conversation(message, stream=stream):
                    yield output
            
            # Update last activity time
            self.session_state["last_activity"] = datetime.now().isoformat()
            self.state_manager.update_state({"last_activity": self.session_state["last_activity"]})
            
        except Exception as e:
            logger.error(f"Workflow error: {e}", exc_info=True)
            yield RunOutput(
                content="I encountered an issue. Let's continue our conversation. "
                        "You can say 'help' to see available activities.",
                metadata={"error": str(e)}
            )
    
    # ========================================================================
    # Activity Routing Methods (Updated for Agno v2)
    # ========================================================================
    
    async def _run_conversation(self, message: str, stream: bool = True) -> AsyncIterator[RunOutput]:
        """Run standard conversation mode."""
        if stream:
            async for output in conversation_agent.run_stream(message):
                yield RunOutput(content=output.content if hasattr(output, 'content') else str(output))
        else:
            result = await conversation_agent.run(message)
            yield RunOutput(content=result.content if hasattr(result, 'content') else str(result))
    
    async def _run_ifs(self, message: str, stream: bool = True) -> AsyncIterator[RunOutput]:
        """Run IFS activity with tracking."""
        # Update activity data
        self.session_state["activity_data"] = ifs_activity.track_progress(
            message, 
            self.session_state.get("activity_data", {})
        )
        self.state_manager.update_state({"activity_data": self.session_state["activity_data"]})
        
        # Run the agent
        if stream:
            async for output in ifs_agent.run_stream(message):
                yield RunOutput(content=output.content if hasattr(output, 'content') else str(output))
        else:
            result = await ifs_agent.run(message)
            yield RunOutput(content=result.content if hasattr(result, 'content') else str(result))
    
    async def _run_daily_content(self, message: str, stream: bool = True) -> AsyncIterator[RunOutput]:
        """Run daily content activity with tracking."""
        # Update activity data
        self.session_state["activity_data"] = daily_content_activity.track_progress(
            message, 
            self.session_state.get("activity_data", {})
        )
        self.state_manager.update_state({"activity_data": self.session_state["activity_data"]})
        
        # Check for natural completion
        if daily_content_activity.is_naturally_complete(self.session_state.get("activity_data", {})):
            self.session_state["activity_data"]["daily_content_progress"]["fully_engaged"] = True
        
        # Run the agent
        if stream:
            async for output in daily_content_agent.run_stream(message):
                yield RunOutput(content=output.content if hasattr(output, 'content') else str(output))
        else:
            result = await daily_content_agent.run(message)
            yield RunOutput(content=result.content if hasattr(result, 'content') else str(result))
    
    # ========================================================================
    # Activity Management Methods (Updated for Agno v2)
    # ========================================================================
    
    def _detect_intent_safely(self, message: str) -> Tuple[Optional[str], float]:
        """Detect intent with error handling."""
        try:
            context = [
                h['message'] for h in self.session_state.get('conversation_history', [])[-3:]
            ]
            
            intent, confidence = intent_detector.detect_intent(message, context)
            
            # Map intent to ActivityType values if detected
            if intent:
                intent_mapping = {
                    "ifs": ActivityType.IFS.value,
                    "daily_content": ActivityType.DAILY_CONTENT.value
                }
                intent = intent_mapping.get(intent, intent)
            
            return intent, confidence
            
        except Exception as e:
            logger.warning(f"Intent detection failed: {e}. Defaulting to conversation.")
            return None, 0.0
    
    async def _switch_activity(self, new_activity: str) -> AsyncIterator[RunOutput]:
        """Switch to a new activity with state management."""
        old_activity = self.session_state.get("current_activity")
        
        # Mark old activity state if exists
        if old_activity and old_activity != new_activity:
            if old_activity in self.session_state["activity_states"]:
                # Don't mark as completed, just as in_progress
                self.session_state["activity_states"][old_activity] = ActivityState.IN_PROGRESS.value
        
        # Update current activity
        self.session_state["current_activity"] = new_activity
        self.session_state["activity_data"] = {}  # Clear activity data
        
        # Mark new activity as in progress
        if new_activity in self.session_state["activity_states"]:
            self.session_state["activity_states"][new_activity] = ActivityState.IN_PROGRESS.value
        
        # Add to history
        self.session_state["activity_history"].append({
            "activity": new_activity,
            "started": datetime.now().isoformat(),
            "from_activity": old_activity
        })
        
        # Persist state
        self.state_manager.update_state(self.session_state)
        
        # Get welcome message from activity
        activity_map = {
            ActivityType.IFS.value: ifs_activity,
            ActivityType.DAILY_CONTENT.value: daily_content_activity
        }
        
        if new_activity in activity_map:
            welcome = activity_map[new_activity].get_welcome_message()
        else:
            activity_name = self._get_activity_name(new_activity)
            welcome = f"✨ Switching to {activity_name}..."
        
        yield RunOutput(content=welcome)
        
        logger.info(f"Activity switch: {old_activity} -> {new_activity}")
    
    async def _handle_activity_completion(self) -> AsyncIterator[RunOutput]:
        """Handle graceful activity completion."""
        current = self.session_state.get("current_activity")
        logger.info(f"🔄 Activity completion requested. Current activity: {current}")
        
        if not current:
            yield RunOutput(
                content="You're already in conversation mode. What would you like to explore?"
            )
            return
        
        # Mark activity as complete
        self._mark_activity_complete(current)
        logger.info(f"✅ Marked {current} as complete")
        
        # Get completion message from activity
        activity_map = {
            ActivityType.IFS.value: ifs_activity,
            ActivityType.DAILY_CONTENT.value: daily_content_activity
        }
        
        if current in activity_map:
            completion_msg = activity_map[current].get_completion_message()
        else:
            completion_msg = "Activity completed. Thank you for your participation."
        
        yield RunOutput(content=completion_msg)
        
        # Clear current activity
        self.session_state["current_activity"] = None
        
        # Suggest remaining activities
        remaining_msg = self._suggest_remaining_activities()
        yield RunOutput(content=remaining_msg)
        
        # Update state persistence
        self.state_manager.update_state(self.session_state)
    
    async def _handle_session_startup(self) -> AsyncIterator[RunOutput]:
        """Handle the initial session startup with daily content and menu."""
        # First, show the IFS parts image with welcome message
        yield RunOutput(
            content="![IFS Parts - Your parts are like kids, if you listen with compassion, they calm down](/static/IFSImage.jpg)\n\n"
        )
        
        # Then show the daily IFS wisdom summary
        yield RunOutput(
            content="\nEver feel \"torn\" inside? **Internal Family Systems (IFS)** may explain why: we all have inner parts that sometimes clash. Protectors shield us, exiles carry pain. But beneath it all, the Self - calm and compassionate - remains whole. Healing begins when parts trust the Self to lead.\n"
        )
        
        # Show separator
        yield RunOutput(content="\n---\n")
        
        # Show the activities menu
        async for output in self._show_activity_menu():
            yield output
        
        # Update state to indicate session has started
        self.state_manager.update_state({
            "session_started": True,
            "startup_complete": datetime.now().isoformat()
        })
    
    async def _show_activity_menu(self) -> AsyncIterator[RunOutput]:
        """Show available activities menu."""
        completed = set(self.session_state.get("completed_activities", {}).keys())
        
        menu = "**🌟 Available Integration Activities:**\n\n"
        
        activities_info = [
            (ActivityType.DAILY_CONTENT.value, "📖 **Daily Content**: Explore today's wisdom more deeply", "5-10 minutes"),
            (ActivityType.IFS.value, "👥 **Internal Family Systems**: Work with the parts that emerged", "20-30 minutes")
        ]
        
        for activity, description, duration in activities_info:
            status = "✅ Completed" if activity in completed else "🔵 Available"
            menu += f"{description}\n   *{duration}* | {status}\n\n"
        
        menu += "💬 **Or we can simply have a conversation** about your experience and integration.\n\n"
        menu += "*What feels right for you in this moment?*"
        
        yield RunOutput(content=menu)
    
    async def _handle_completed_activity_request(self, activity: str) -> AsyncIterator[RunOutput]:
        """Handle request to enter already-completed activity."""
        activity_name = self._get_activity_name(activity)
        
        yield RunOutput(
            content=(
                f"You've already completed {activity_name} in this session. "
                f"Each activity is designed as a complete experience.\n\n"
                f"Would you like to:\n"
                f"• Try a different activity\n"
                f"• Continue our conversation\n"
                f"• Reflect on your experience with {activity_name}"
            )
        )
        
        # Show remaining activities
        remaining_msg = self._suggest_remaining_activities()
        if remaining_msg:
            yield RunOutput(content=remaining_msg)
    
    async def _handle_completed_activity_return(self) -> AsyncIterator[RunOutput]:
        """Handle when user is in a completed activity state."""
        # Clear the current activity
        self.session_state["current_activity"] = None
        
        yield RunOutput(
            content=(
                "Let's return to our conversation. "
                "You can explore another activity or we can simply talk."
            )
        )
        
        # Run conversation agent with a prompt
        async for output in conversation_agent.run_stream("What's on your mind?"):
            yield RunOutput(content=output.content if hasattr(output, 'content') else str(output))
    
    # ========================================================================
    # Helper Methods (Unchanged)
    # ========================================================================
    
    def _mark_activity_complete(self, activity: str):
        """Mark an activity as complete with metadata."""
        self.session_state["completed_activities"][activity] = {
            "completed_at": datetime.now().isoformat(),
            "duration": self._calculate_activity_duration(activity),
            "session_data": dict(self.session_state.get("activity_data", {}))
        }
        
        # Update activity state
        if activity in self.session_state["activity_states"]:
            self.session_state["activity_states"][activity] = ActivityState.COMPLETED.value
        
        # Clear activity data
        self.session_state["activity_data"] = {}
        
        # Persist state
        self.state_manager.update_state(self.session_state)
        logger.info(f"Activity completed: {activity}")
    
    def _is_activity_complete(self, activity: str) -> bool:
        """Check if an activity has been marked complete."""
        return activity in self.session_state.get("completed_activities", {})
    
    def _suggest_remaining_activities(self) -> str:
        """Suggest activities that haven't been completed."""
        all_activities = [
            ActivityType.IFS.value,
            ActivityType.DAILY_CONTENT.value
        ]
        completed = set(self.session_state.get("completed_activities", {}).keys())
        remaining = [a for a in all_activities if a not in completed]
        
        if not remaining:
            return (
                "🎉 You've explored all available activities in this session! "
                "Feel free to rest with your insights or share any reflections."
            )
        
        activity_descriptions = {
            ActivityType.IFS.value: "**IFS (Internal Family Systems)** - Explore your internal parts",
            ActivityType.DAILY_CONTENT.value: "**Daily Wisdom** - Brief reflection and guidance",
        }
        
        menu = "\n\n🌿 **What would you like to explore next?**\n\n"
        for activity in remaining:
            if activity in activity_descriptions:
                menu += f"• {activity_descriptions[activity]}\n"
        
        menu += "\nSimply tell me which activity you'd like to explore, or we can continue our conversation."
        return menu
    
    def _get_activity_name(self, activity: str) -> str:
        """Get human-readable activity name."""
        names = {
            ActivityType.IFS.value: "Internal Family Systems",
            ActivityType.DAILY_CONTENT.value: "Daily Wisdom Content",
            ActivityType.CONVERSATION.value: "Integration Conversation"
        }
        return names.get(activity, "activity")
    
    def _calculate_activity_duration(self, activity: str) -> str:
        """Calculate how long was spent in an activity."""
        # Find when activity started from history
        for event in reversed(self.session_state.get("activity_history", [])):
            if event.get("activity") == activity:
                start_time = datetime.fromisoformat(event["started"])
                duration = datetime.now() - start_time
                minutes = int(duration.total_seconds() / 60)
                return f"{minutes} minutes"
        return "unknown duration"