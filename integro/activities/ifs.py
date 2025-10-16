"""Internal Family Systems (IFS) activity for exploring internal parts."""

from typing import Dict, Any, Optional
import logging
import asyncio

from agno.agent import Agent
from integro.activities.base import BaseActivity

logger = logging.getLogger(__name__)


class IFSActivity(BaseActivity):
    """
    Internal Family Systems (IFS) activity.
    
    Helps users explore and work with internal parts
    that emerged during their psychedelic experience.
    Duration: 20-30 minutes
    """
    
    def __init__(self):
        super().__init__(
            name="Internal Family Systems",
            description="Explore parts that emerged",
            duration_estimate="20-30 minutes"
        )
        
    def create_agent(self) -> Agent:
        """Create IFS agent for parts work with optional knowledge base."""
        from agno.agent import Agent
        
        # Try to load knowledge base using simple embedded approach
        knowledge_base = None
        try:
            from integro.utils.simple_agno_kb import get_ifs_knowledge
            knowledge_base = get_ifs_knowledge()
            if knowledge_base:
                logger.info("✅ Loaded IFS knowledge base with embedded content")
        except Exception as e:
            logger.warning(f"Could not create IFS knowledge base: {e}")
            
        # Create Agno-compliant agent with optional knowledge base
        if knowledge_base:
            logger.info("✅ Creating IFS agent with knowledge base")
            return Agent(
                name="IFS Therapist",
                model=self.get_model(),
                instructions=self._get_enhanced_instructions(),
                knowledge=knowledge_base,
                search_knowledge=True,
                markdown=True
            )
        else:
            logger.info("Creating IFS agent without knowledge base")
            return Agent(
                name="IFS Therapist", 
                model=self.get_model(),
                instructions=self._get_basic_instructions(),
                markdown=True
            )
    
    def get_welcome_message(self) -> str:
        """Get welcome message for IFS."""
        return (
            "🌟 Let's explore your internal system with IFS.\n\n"
            "During psychedelic experiences, different parts of ourselves often emerge.\n"
            "What parts of yourself showed up during your journey?"
        )
    
    def get_completion_message(self) -> str:
        """Get completion message for IFS."""
        return (
            "🌟 **Thank you for exploring your internal system.**\n\n"
            "You've connected with your parts with curiosity and compassion. "
            "Each part you met today has wisdom to share about your journey. "
            "Continue to approach them with Self-energy when they arise.\n\n"
            "Remember: All parts have positive intentions for you."
        )
    
    def track_progress(self, message: str, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track IFS parts work progress."""
        if "ifs_progress" not in activity_data:
            activity_data["ifs_progress"] = {
                "identified_parts": [],
                "current_part": None,
                "self_energy_accessed": False,
                "parts_categories": {
                    "exiles": [],
                    "managers": [],
                    "firefighters": []
                },
                "integration_insights": []
            }
        
        progress = activity_data["ifs_progress"]
        message_lower = message.lower()
        
        # Check for part identification
        part_keywords = ["part", "exile", "manager", "firefighter", "protector", "inner"]
        if any(keyword in message_lower for keyword in part_keywords):
            # Track general part identification
            if "working_with_parts" not in progress:
                progress["working_with_parts"] = True
            
            # Categorize parts
            if "exile" in message_lower:
                progress["parts_categories"]["exiles"].append(message[:50])
            elif "manager" in message_lower:
                progress["parts_categories"]["managers"].append(message[:50])
            elif "firefighter" in message_lower:
                progress["parts_categories"]["firefighters"].append(message[:50])
            else:
                progress["identified_parts"].append(message[:50])
        
        # Check for Self-energy access
        self_keywords = ["self", "compassion", "calm", "curious", "witness", "centered"]
        if any(keyword in message_lower for keyword in self_keywords):
            if "self" in message_lower and any(word in message_lower for word in ["energy", "compassion", "calm"]):
                progress["self_energy_accessed"] = True
        
        # Check for integration insights
        insight_keywords = ["realize", "understand", "see", "integrate", "wisdom"]
        if any(keyword in message_lower for keyword in insight_keywords):
            progress["integration_insights"].append(message[:100])
            
        return activity_data
    
    def is_naturally_complete(self, activity_data: Dict[str, Any]) -> bool:
        """Check if parts work has reached a natural completion."""
        if "ifs_progress" not in activity_data:
            return False
            
        progress = activity_data["ifs_progress"]
        
        # Consider complete if:
        # - At least one part identified
        # - Self-energy accessed
        # - Some integration insights gained
        parts_identified = (
            len(progress.get("identified_parts", [])) > 0 or
            any(len(parts) > 0 for parts in progress.get("parts_categories", {}).values())
        )
        
        return (
            parts_identified and
            progress.get("self_energy_accessed", False) and
            len(progress.get("integration_insights", [])) > 0
        )
    
    def get_instructions(self) -> list:
        """Get specific instructions for IFS agent."""
        return [
            "You are a compassionate IFS facilitator.",
            "Help users explore parts that emerged during their psychedelic journey.",
            "Guide them to approach all parts with curiosity, not judgment.",
            "Support access to Self-energy - the calm, compassionate witness.",
            "Validate that all parts have positive intentions.",
            "Be patient as they explore their internal system."
        ]
    
    def detect_keywords(self, message: str) -> tuple:
        """Detect IFS keywords."""
        keywords = [
            "ifs", "internal family", "parts", "exile", 
            "manager", "firefighter", "self energy", "internal system",
            "parts work", "inner parts", "protector"
        ]
        
        message_lower = message.lower()
        matches = sum(1 for keyword in keywords if keyword in message_lower)
        
        if "ifs" in message_lower or "internal family" in message_lower:
            return ("ifs", 0.9)
        elif "parts" in message_lower and any(word in message_lower for word in ["work", "explore", "internal"]):
            return ("ifs", 0.8)
        elif matches >= 2:
            return ("ifs", 0.6)
        elif matches == 1:
            return ("ifs", 0.3)
        
        return (None, 0.0)
    
    def _get_basic_instructions(self) -> list:
        """Get basic IFS instructions without knowledge base context."""
        return [
            "Guide users through Internal Family Systems work for integration.",
            "Help them identify parts that emerged during their psychedelic experience:",
            "- Exiles: Wounded parts carrying pain or trauma that surfaced",
            "- Managers: Protective parts trying to maintain control", 
            "- Firefighters: Parts that react intensely to overwhelming feelings",
            "Support them in accessing Self-energy - the calm, compassionate witness.",
            "Encourage curiosity toward all parts without judgment.",
            "Remember: All parts have positive intentions, even difficult ones.",
            "",
            "Start by asking: What parts of yourself showed up during your journey?",
            "Help them identify and dialogue with these parts.",
            "Guide them to approach each part with curiosity and compassion."
        ]
    
    def _get_enhanced_instructions(self) -> list:
        """Get enhanced IFS instructions with knowledge base integration."""
        return [
            "You are an expert IFS (Internal Family Systems) therapist specializing in psychedelic integration.",
            "",
            "CORE PRINCIPLES:",
            "• All parts have positive intentions, even difficult ones",
            "• Self-energy is the natural healing resource within everyone", 
            "• Approach all parts with curiosity, not judgment",
            "• Parts need to be witnessed and understood, not eliminated",
            "",
            "INTEGRATION FOCUS:",
            "Help users work with parts that emerged during their psychedelic journey:",
            "- Exiles: Wounded parts carrying pain/trauma that surfaced",
            "- Managers: Protective parts trying to maintain control",
            "- Firefighters: Parts that react intensely to overwhelming feelings",
            "",
            "THERAPEUTIC APPROACH:",
            "1. Start by asking what parts showed up during their journey",
            "2. Help them identify and get to know each part",
            "3. Facilitate dialogue between Self and parts",
            "4. Support integration of insights from the experience",
            "",
            "Use your knowledge base to provide accurate IFS techniques and concepts.",
            "Reference established IFS methods when helpful.",
            "Always prioritize the user's direct experience and insights."
        ]
    
    async def load_knowledge_base(self):
        """Load IFS knowledge base asynchronously."""
        try:
            from integro.utils.knowledge_loader_direct import direct_knowledge_loader as knowledge_loader
            return await knowledge_loader.load_ifs_knowledge()
        except Exception as e:
            logger.error(f"Failed to load IFS knowledge base: {e}")
            return None