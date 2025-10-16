"""Bridge between FastAPI WebSocket and Agno Therapeutic Workflow."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, AsyncIterator
from datetime import datetime
from enum import Enum

from agno.agent import RunResponse
from integro.workflows.therapeutic import TherapeuticWorkflow
from integro.utils.logging import get_logger

logger = get_logger(__name__)


class WorkflowMessageType(Enum):
    """WebSocket message types for workflow communication."""
    # Incoming messages (from client)
    START_WORKFLOW = "start_workflow"
    SEND_MESSAGE = "workflow_message"
    COMPLETE_ACTIVITY = "complete_activity"
    REQUEST_MENU = "request_menu"
    SWITCH_ACTIVITY = "switch_activity"
    END_SESSION = "end_session"
    
    # Outgoing messages (to client)
    WORKFLOW_READY = "workflow_ready"
    ACTIVITY_CHANGED = "activity_changed"
    RESPONSE_CHUNK = "workflow_chunk"
    RESPONSE_COMPLETE = "workflow_complete"
    ACTIVITY_COMPLETED = "activity_completed"
    SESSION_STATE = "session_state"
    ERROR = "workflow_error"
    TYPING = "workflow_typing"
    MENU = "activity_menu"


class WorkflowIntegration:
    """
    Integrates Agno Therapeutic Workflow with WebSocket communication.
    
    This class handles:
    - Workflow lifecycle management per client
    - Message translation between WebSocket and workflow
    - Streaming response handling
    - Session state synchronization
    """
    
    def __init__(self):
        """Initialize the workflow integration."""
        self.active_workflows: Dict[str, TherapeuticWorkflow] = {}
        self.client_sessions: Dict[str, str] = {}
        logger.info("WorkflowIntegration initialized")
    
    async def create_workflow(self, client_id: str, user_id: Optional[str] = None) -> TherapeuticWorkflow:
        """
        Create a new workflow instance for a client.
        
        Args:
            client_id: Unique client identifier
            user_id: Optional user ID for personalization
            
        Returns:
            TherapeuticWorkflow instance
        """
        try:
            # Generate session ID for this workflow
            session_id = f"therapeutic_{client_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create workflow instance
            workflow = TherapeuticWorkflow(
                session_id=session_id,
                user_id=user_id or client_id
            )
            
            # Store workflow
            self.active_workflows[client_id] = workflow
            self.client_sessions[client_id] = session_id
            
            logger.info(f"Created workflow for client {client_id}, session {session_id}")
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to create workflow for client {client_id}: {e}")
            raise
    
    def get_workflow(self, client_id: str) -> Optional[TherapeuticWorkflow]:
        """Get workflow instance for a client."""
        return self.active_workflows.get(client_id)
    
    def remove_workflow(self, client_id: str):
        """Remove and cleanup workflow for a client."""
        if client_id in self.active_workflows:
            workflow = self.active_workflows[client_id]
            # Save final state before removal
            if hasattr(workflow, 'state_manager'):
                workflow.state_manager.update_state(workflow.session_state)
            
            del self.active_workflows[client_id]
            logger.info(f"Removed workflow for client {client_id}")
        
        if client_id in self.client_sessions:
            del self.client_sessions[client_id]
    
    async def handle_message(self, client_id: str, message: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """
        Handle incoming WebSocket message and yield responses.
        
        Args:
            client_id: Client identifier
            message: Incoming message dict
            
        Yields:
            Response messages for WebSocket
        """
        message_type = message.get("type")
        
        try:
            # Start new workflow
            if message_type == WorkflowMessageType.START_WORKFLOW.value:
                user_id = message.get("user_id")
                workflow = await self.create_workflow(client_id, user_id)
                
                yield {
                    "type": WorkflowMessageType.WORKFLOW_READY.value,
                    "session_id": workflow.session_id,
                    "message": "Welcome to your psychedelic integration session. I'm here to support your journey.",
                    "current_activity": workflow.session_state.get("current_activity"),
                    "timestamp": datetime.now().isoformat()
                }
            
            # Process workflow message
            elif message_type == WorkflowMessageType.SEND_MESSAGE.value:
                workflow = self.get_workflow(client_id)
                if not workflow:
                    yield {
                        "type": WorkflowMessageType.ERROR.value,
                        "message": "No active workflow. Please start a session first.",
                        "timestamp": datetime.now().isoformat()
                    }
                    return
                
                # Get message content
                content = message.get("content", "")
                
                # Send typing indicator
                yield {
                    "type": WorkflowMessageType.TYPING.value,
                    "status": True,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Process through workflow and stream responses
                try:
                    async for response_chunk in self._stream_workflow_response(workflow, content):
                        yield response_chunk
                        
                finally:
                    # Stop typing indicator
                    yield {
                        "type": WorkflowMessageType.TYPING.value,
                        "status": False,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Send current session state
                    yield {
                        "type": WorkflowMessageType.SESSION_STATE.value,
                        "current_activity": workflow.session_state.get("current_activity"),
                        "completed_activities": list(workflow.session_state.get("completed_activities", {}).keys()),
                        "timestamp": datetime.now().isoformat()
                    }
            
            # Request activity menu
            elif message_type == WorkflowMessageType.REQUEST_MENU.value:
                workflow = self.get_workflow(client_id)
                if workflow:
                    menu = self._generate_activity_menu(workflow)
                    yield {
                        "type": WorkflowMessageType.MENU.value,
                        "menu": menu,
                        "timestamp": datetime.now().isoformat()
                    }
            
            # Complete current activity
            elif message_type == WorkflowMessageType.COMPLETE_ACTIVITY.value:
                workflow = self.get_workflow(client_id)
                if workflow:
                    # Send completion request through workflow
                    async for response_chunk in self._stream_workflow_response(workflow, "I'm done with this activity"):
                        yield response_chunk
                    
                    yield {
                        "type": WorkflowMessageType.ACTIVITY_COMPLETED.value,
                        "activity": workflow.session_state.get("current_activity"),
                        "timestamp": datetime.now().isoformat()
                    }
            
            # Switch activity
            elif message_type == WorkflowMessageType.SWITCH_ACTIVITY.value:
                workflow = self.get_workflow(client_id)
                if workflow:
                    activity = message.get("activity")
                    prompt = self._get_activity_prompt(activity)
                    
                    async for response_chunk in self._stream_workflow_response(workflow, prompt):
                        yield response_chunk
                    
                    yield {
                        "type": WorkflowMessageType.ACTIVITY_CHANGED.value,
                        "new_activity": workflow.session_state.get("current_activity"),
                        "timestamp": datetime.now().isoformat()
                    }
            
            # End session
            elif message_type == WorkflowMessageType.END_SESSION.value:
                workflow = self.get_workflow(client_id)
                if workflow:
                    # Save final state
                    final_summary = self._generate_session_summary(workflow)
                    self.remove_workflow(client_id)
                    
                    yield {
                        "type": WorkflowMessageType.RESPONSE_COMPLETE.value,
                        "content": final_summary,
                        "session_ended": True,
                        "timestamp": datetime.now().isoformat()
                    }
            
            else:
                yield {
                    "type": WorkflowMessageType.ERROR.value,
                    "message": f"Unknown message type: {message_type}",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error handling message for client {client_id}: {e}", exc_info=True)
            yield {
                "type": WorkflowMessageType.ERROR.value,
                "message": f"An error occurred: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _stream_workflow_response(self, workflow: TherapeuticWorkflow, message: str) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream workflow responses as WebSocket messages.
        
        Args:
            workflow: The workflow instance
            message: User message to process
            
        Yields:
            WebSocket response chunks
        """
        try:
            # Run workflow and stream responses
            response_buffer = []
            
            for response in workflow.run(message):
                if isinstance(response, RunResponse):
                    content = response.content if hasattr(response, 'content') else str(response)
                    
                    # Buffer responses
                    response_buffer.append(content)
                    
                    # Yield chunk for streaming
                    yield {
                        "type": WorkflowMessageType.RESPONSE_CHUNK.value,
                        "content": content,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Small delay for streaming effect
                    await asyncio.sleep(0.01)
            
            # Send complete message
            full_response = "".join(response_buffer)
            yield {
                "type": WorkflowMessageType.RESPONSE_COMPLETE.value,
                "content": full_response,
                "current_activity": workflow.session_state.get("current_activity"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error streaming workflow response: {e}")
            yield {
                "type": WorkflowMessageType.ERROR.value,
                "message": f"Error processing message: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_activity_menu(self, workflow: TherapeuticWorkflow) -> Dict[str, Any]:
        """Generate activity menu based on current workflow state."""
        completed = workflow.session_state.get("completed_activities", {}).keys()
        current = workflow.session_state.get("current_activity")
        
        activities = [
            {
                "id": "daily_content",
                "name": "Daily Wisdom Content",
                "description": "Brief wisdom and reflection practice",
                "duration": "5-10 minutes",
                "status": "completed" if "daily_content" in completed else "available",
                "is_current": current == "daily_content"
            },
            {
                "id": "byron_katie",
                "name": "Byron Katie's The Work",
                "description": "Question thoughts from your journey",
                "duration": "15-20 minutes",
                "status": "completed" if "byron_katie" in completed else "available",
                "is_current": current == "byron_katie"
            },
            {
                "id": "ifs",
                "name": "Internal Family Systems",
                "description": "Explore parts that emerged",
                "duration": "20-30 minutes",
                "status": "completed" if "ifs" in completed else "available",
                "is_current": current == "ifs"
            }
        ]
        
        return {
            "activities": activities,
            "current_activity": current,
            "completed_count": len(completed),
            "total_count": 3
        }
    
    def _get_activity_prompt(self, activity: str) -> str:
        """Get the prompt to trigger a specific activity."""
        prompts = {
            "daily_content": "I'd like to see today's daily wisdom content",
            "byron_katie": "I want to do Byron Katie's The Work",
            "ifs": "Let's explore with Internal Family Systems"
        }
        return prompts.get(activity, "help")
    
    def _generate_session_summary(self, workflow: TherapeuticWorkflow) -> str:
        """Generate a summary of the session."""
        completed = list(workflow.session_state.get("completed_activities", {}).keys())
        duration = workflow.session_state.get("session_start", "")
        
        summary = "🙏 **Session Complete**\n\n"
        
        if completed:
            summary += f"You explored {len(completed)} activities today:\n"
            for activity in completed:
                activity_name = activity.replace("_", " ").title()
                summary += f"• {activity_name}\n"
            summary += "\n"
        
        summary += "Thank you for taking time for integration today. "
        summary += "Remember, integration is an ongoing process. "
        summary += "Be gentle with yourself as these insights unfold.\n\n"
        summary += "Until next time, stay present. 🌟"
        
        return summary


# Global workflow integration instance
workflow_integration = WorkflowIntegration()