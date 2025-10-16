"""Daily content activity for wisdom and reflection."""

from typing import Dict, Any
import logging

from agno.agent import Agent
from integro.activities.base import BaseActivity

logger = logging.getLogger(__name__)


class DailyContentActivity(BaseActivity):
    """
    Daily wisdom content activity.
    
    Provides brief daily wisdom and reflection practices.
    Duration: 5-10 minutes
    """
    
    def __init__(self):
        super().__init__(
            name="Daily Wisdom Content",
            description="Today's wisdom and reflection practice",
            duration_estimate="5-10 minutes"
        )
        
    def create_agent(self) -> Agent:
        """Create daily content agent with wisdom delivery."""
        from agno.agent import Agent
        
        return Agent(
            name="Daily Content Guide",
            model=self.get_model(),
            instructions=[
                "Share today's daily wisdom content.",
                "First provide the summary for quick reflection.",
                "If the user wants more, share the expanded version.",
                "Help them integrate the wisdom into their day.",
                "Connect the daily theme to their integration journey.",
                
                # Today's IFS wisdom content
                "Share this wisdom about Internal Family Systems:",
                "",
                "The Internal Family Systems (IFS) model views the mind as a community of different 'parts' or subpersonalities. These parts aren't flaws but natural aspects of being human, often shaped by past experiences. While protectors (like managers and firefighters) work to keep us safe and exiles carry old wounds, the true leader is the Self, our calm, compassionate core. Problems arise when parts lose trust in the Self and take over ('blending'). Healing comes from helping parts relax, unblending from them, and allowing the Self to guide. Everyone has this undamaged Self, which brings clarity, confidence, and ease when it leads.",
                "",
                "If they ask for more details or practices, expand on working with parts."
            ],
            markdown=True  # show_tool_calls removed in v2
        )
    
    def get_welcome_message(self) -> str:
        """Get welcome message for daily content."""
        return (
            "🌟 **Today's Integration Wisdom: Understanding Your Inner System**\n\n"
            "The Internal Family Systems (IFS) model views the mind as a community of different 'parts' or subpersonalities. These parts aren't flaws but natural aspects of being human, often shaped by past experiences. While protectors (like managers and firefighters) work to keep us safe and exiles carry old wounds, the true leader is the Self, our calm, compassionate core.\n\n"
            "Problems arise when parts lose trust in the Self and take over ('blending'). Healing comes from helping parts relax, unblending from them, and allowing the Self to guide. Everyone has this undamaged Self, which brings clarity, confidence, and ease when it leads.\n\n"
            "*What parts of yourself did your journey reveal? Which ones need your compassionate attention?*"
        )
    
    def get_completion_message(self) -> str:
        """Get completion message for daily content."""
        return (
            "🙏 **Thank you for engaging with today's wisdom.**\n\n"
            "May these reflections support your integration journey. "
            "Consider carrying one insight with you as you move through your day. "
            "The practices offered are always available when you need grounding."
        )
    
    def track_progress(self, message: str, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track daily content engagement."""
        if "daily_content_progress" not in activity_data:
            activity_data["daily_content_progress"] = {
                "summary_viewed": False,
                "expansion_viewed": False,
                "practice_engaged": False
            }
        
        progress = activity_data["daily_content_progress"]
        
        # Track what content has been viewed
        if not progress["summary_viewed"]:
            progress["summary_viewed"] = True
        elif any(word in message.lower() for word in ["more", "expand", "deeper", "continue"]):
            progress["expansion_viewed"] = True
        elif any(word in message.lower() for word in ["practice", "try", "do", "apply"]):
            progress["practice_engaged"] = True
            
        return activity_data
    
    def is_naturally_complete(self, activity_data: Dict[str, Any]) -> bool:
        """Check if daily content is fully engaged."""
        if "daily_content_progress" not in activity_data:
            return False
            
        progress = activity_data["daily_content_progress"]
        return (
            progress.get("summary_viewed", False) and 
            progress.get("expansion_viewed", False)
        )
    
    def get_instructions(self) -> list:
        """Get specific instructions for daily content agent."""
        return [
            "You are a gentle guide for daily integration wisdom.",
            "Share wisdom that supports psychedelic integration.",
            "Be present, compassionate, and non-judgmental.",
            "Offer practical practices that can be done immediately.",
            "Connect the theme to common integration challenges."
        ]
    
    def detect_keywords(self, message: str) -> tuple:
        """Detect daily content keywords."""
        keywords = [
            "daily", "content", "wisdom", "reflection", 
            "today", "daily message", "inspiration", "quote",
            "practice", "guidance", "insight"
        ]
        
        message_lower = message.lower()
        matches = sum(1 for keyword in keywords if keyword in message_lower)
        
        if matches >= 2:
            return ("daily_content", 0.8)
        elif matches == 1:
            return ("daily_content", 0.4)
        
        return (None, 0.0)