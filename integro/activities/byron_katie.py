"""Byron Katie's The Work activity for questioning thoughts."""

from typing import Dict, Any, List, Optional
import logging
import asyncio

from agno.agent import Agent
from integro.activities.base import BaseActivity

logger = logging.getLogger(__name__)


class ByronKatieActivity(BaseActivity):
    """
    Byron Katie's The Work activity.
    
    Guides users through the four questions and turnarounds
    to question thoughts that arose during their experience.
    Duration: 15-20 minutes per thought
    """
    
    # The Four Questions of The Work
    FOUR_QUESTIONS = [
        "Is it true?",
        "Can you absolutely know that it's true?",
        "How do you react, what happens, when you believe that thought?",
        "Who would you be without the thought?"
    ]
    
    # Turnaround types
    TURNAROUNDS = [
        "to the opposite",
        "to the self",
        "to the other"
    ]
    
    def __init__(self):
        super().__init__(
            name="Byron Katie's The Work",
            description="Question thoughts from your journey",
            duration_estimate="15-20 minutes per thought"
        )
        
    def create_agent(self) -> Agent:
        """Create Byron Katie agent for The Work with optional knowledge base."""
        from agno.agent import Agent
        
        # Try to load knowledge base using simple embedded approach
        knowledge_base = None
        try:
            from integro.utils.simple_agno_kb import get_byron_katie_knowledge
            knowledge_base = get_byron_katie_knowledge()
            if knowledge_base:
                logger.info("✅ Loaded Byron Katie knowledge base with embedded content")
        except Exception as e:
            logger.warning(f"Could not create Byron Katie knowledge base: {e}")
            
        # Create Agno-compliant agent with optional knowledge base
        if knowledge_base:
            logger.info("✅ Creating Byron Katie agent with knowledge base")
            return Agent(
                name="Byron Katie Guide",
                model=self.get_model(),
                instructions=self._get_enhanced_instructions() if hasattr(self, '_get_enhanced_instructions') else self._get_detailed_instructions(),
                knowledge=knowledge_base,
                search_knowledge=True,
                markdown=True
            )
        else:
            logger.info("Creating Byron Katie agent without knowledge base")
            return Agent(
                name="Byron Katie Guide",
                model=self.get_model(),
                instructions=self._get_detailed_instructions(),
                markdown=True
            )
    
    def _get_detailed_instructions(self) -> List[str]:
        """Get comprehensive instructions for Byron Katie agent."""
        return [
            # Core identity and approach
            "You are continuing to guide the user through their psychedelic integration, now using Byron Katie's The Work.",
            "Maintain the same warm, supportive presence they've already experienced with you.",
            "Communicate with clarity, simplicity, and kindness - The Work is gentle but profound.",
            "You're the same guide, just shifting into a specific technique for examining thoughts.",
            "",
            # Transition and context
            "Acknowledge the transition naturally: 'Let's work with this using Byron Katie's method...' "
            "or 'The Work can really help us explore this thought more deeply...'",
            "",
            # Process structure
            "Guide users through The Work systematically:",
            "1. First, help them identify a specific thought or belief to question",
            "2. Ask each of the four questions in order, allowing deep reflection",
            "3. After the four questions, guide them through turnarounds",
            "4. Help them find genuine examples for each turnaround",
            "",
            # The Four Questions with detailed guidance
            "THE FOUR QUESTIONS (ask in order):",
            "",
            "Question 1: 'Is it true?'",
            "- Allow them to sit with this question",
            "- Accept only yes or no answers",
            "- If they say 'I don't know', gently ask 'If you had to choose yes or no, which would it be?'",
            "",
            "Question 2: 'Can you absolutely know that it's true?'",
            "- This deepens the inquiry from Question 1",
            "- Again, only yes or no",
            "- Help them explore the limits of what they can truly know",
            "",
            "Question 3: 'How do you react, what happens, when you believe that thought?'",
            "- Explore physical sensations, emotions, and behaviors",
            "- Ask: 'What do you feel in your body?'",
            "- Ask: 'How do you treat yourself and others?'",
            "- Ask: 'What images or memories arise?'",
            "- Let them fully experience the impact of the thought",
            "",
            "Question 4: 'Who would you be without the thought?'",
            "- Help them imagine the same situation without the thought",
            "- Ask: 'Close your eyes. See yourself in that situation without the thought. What do you see?'",
            "- Explore the freedom and peace that might be available",
            "",
            # Turnarounds
            "TURNAROUNDS (after all four questions):",
            "- Guide them to find turnarounds (opposites) of the original thought",
            "- Common turnarounds: to the opposite, to the self, to the other",
            "- For each turnaround, ask them to find 3 genuine examples of how it could be true",
            "- Turnarounds are not about being right/wrong, but seeing different perspectives",
            "",
            # Support and encouragement
            "WHEN USERS ARE STUCK:",
            "- Offer gentle encouragement: 'Take your time. There's no rush.'",
            "- Validate their process: 'It's okay to find this challenging. You're doing important work.'",
            "- Provide examples if needed, but let insights come from them",
            "- Remind them: 'The Work is about discovering what's true for you, not what I think.'",
            "",
            # Integration focus
            "PSYCHEDELIC INTEGRATION CONTEXT:",
            "- Acknowledge that thoughts from psychedelic experiences can feel especially profound",
            "- Help distinguish genuine insights from mental constructs",
            "- Be aware that some thoughts may relate to ego dissolution, unity experiences, or profound realizations",
            "- Validate the importance of questioning even 'positive' thoughts if they create stress",
            "",
            # Completion
            "ENDING THE SESSION:",
            "- After completing The Work on one thought, ask if they'd like to work on another",
            "- If finishing, ask: 'Would you like a summary of our work together?'",
            "- Remind them they can return to The Work anytime a stressful thought arises",
            "- Encourage journaling about turnarounds that resonated",
            "",
            # Important reminders
            "REMEMBER:",
            "- Never push or rush - let insights emerge naturally",
            "- The Work is meditation, not therapy",
            "- You're facilitating their self-inquiry, not providing answers",
            "- Stay focused on The Work - don't steer to other activities",
            "- Each person's truth is their own to discover"
        ]
    
    def get_welcome_message(self) -> str:
        """Get welcome message for Byron Katie."""
        return (
            "Let's explore Byron Katie's The Work together. This is a beautiful process for "
            "questioning thoughts that might be causing stress or confusion after your journey.\n\n"
            "We'll take a specific thought or belief and gently examine it through four simple questions, "
            "then explore some turnarounds to see it from different angles.\n\n"
            "Take a moment to connect with yourself... What thought or belief from your experience "
            "feels important to examine right now? It could be something troubling you, or even a "
            "'positive' realization that feels heavy to carry."
        )
    
    def get_completion_message(self) -> str:
        """Get completion message for Byron Katie."""
        return (
            "Beautiful work exploring that thought. You've shown real courage in questioning "
            "beliefs that felt so solid.\n\n"
            "The insights from The Work often continue to unfold over the coming days. You might "
            "want to write down any turnarounds that particularly resonated - they can be powerful "
            "anchors as you continue integrating.\n\n"
            "Would you like to explore another thought, or shall we transition to something else? "
            "I'm here to support whatever feels right for you."
        )
    
    def track_progress(self, message: str, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track Byron Katie progress through the four questions and turnarounds."""
        if "byron_katie_progress" not in activity_data:
            activity_data["byron_katie_progress"] = {
                "stage": "identifying_thought",  # identifying_thought -> questions -> turnarounds -> complete
                "current_thought": None,
                "current_question": 0,  # 0-4 for the four questions
                "questions_answered": {},  # Store answers to each question
                "turnarounds_started": False,
                "turnarounds_completed": [],  # List of completed turnarounds
                "insights": [],
                "thoughts_worked": 0  # Track how many thoughts they've worked through
            }
        
        progress = activity_data["byron_katie_progress"]
        message_lower = message.lower()
        
        # Stage: Identifying the thought to work with
        if progress["stage"] == "identifying_thought":
            # Look for a substantial message that could be a thought/belief
            if len(message) > 15 and not any(skip in message_lower for skip in ["don't know", "not sure", "help me"]):
                progress["current_thought"] = message
                progress["stage"] = "questions"
                progress["current_question"] = 1
                logger.info(f"Byron Katie: Identified thought to work with: {message[:50]}...")
        
        # Stage: Working through the four questions
        elif progress["stage"] == "questions":
            current_q = progress["current_question"]
            
            # Check for valid answers to yes/no questions (Q1 and Q2)
            if current_q in [1, 2]:
                if any(word in message_lower for word in ["yes", "no", "true", "false", "absolutely", "definitely"]):
                    progress["questions_answered"][f"Q{current_q}"] = message
                    progress["current_question"] = current_q + 1
                    if current_q == 4:
                        progress["stage"] = "turnarounds"
                        progress["turnarounds_started"] = True
            
            # Questions 3 and 4 accept longer responses
            elif current_q in [3, 4]:
                if len(message) > 10:  # Any substantial response
                    progress["questions_answered"][f"Q{current_q}"] = message
                    if current_q < 4:
                        progress["current_question"] = current_q + 1
                    else:
                        progress["stage"] = "turnarounds"
                        progress["turnarounds_started"] = True
        
        # Stage: Working with turnarounds
        elif progress["stage"] == "turnarounds":
            # Check if they're providing turnaround examples
            if any(word in message_lower for word in ["opposite", "instead", "actually", "really", "true that"]):
                progress["turnarounds_completed"].append(message[:100])
                
                # After a few turnarounds, mark as complete
                if len(progress["turnarounds_completed"]) >= 2:
                    progress["stage"] = "complete"
                    progress["thoughts_worked"] += 1
            
            # Or if they indicate they're done with turnarounds
            elif any(phrase in message_lower for phrase in ["done", "finished", "complete", "that's all"]):
                progress["stage"] = "complete"
                progress["thoughts_worked"] += 1
        
        # Capture insights at any stage
        if any(word in message_lower for word in ["realize", "see now", "understand", "insight", "awareness", "clarity"]):
            progress["insights"].append(message[:150])
            logger.info(f"Byron Katie: Captured insight: {message[:50]}...")
            
        return activity_data
    
    def is_naturally_complete(self, activity_data: Dict[str, Any]) -> bool:
        """Check if The Work process is complete for at least one thought."""
        if "byron_katie_progress" not in activity_data:
            return False
            
        progress = activity_data["byron_katie_progress"]
        
        # Complete when they've worked through at least one thought fully
        # or explicitly marked as complete in the turnaround stage
        return (
            progress.get("stage") == "complete" or 
            progress.get("thoughts_worked", 0) >= 1
        )
    
    def get_instructions(self) -> list:
        """Get specific instructions for Byron Katie agent."""
        return [
            "You are a patient guide for Byron Katie's The Work.",
            "Help users question thoughts from their psychedelic experiences.",
            "Be gentle but thorough with each question.",
            "Don't rush - let insights emerge naturally.",
            "Validate their courage in questioning beliefs.",
            "Suggest they sit with each question before answering."
        ]
    
    def detect_keywords(self, message: str) -> tuple:
        """Detect Byron Katie keywords."""
        keywords = [
            "byron katie", "the work", "four questions", 
            "is it true", "question my thoughts", "question thoughts",
            "turn around", "turnaround", "belief", "thought work"
        ]
        
        message_lower = message.lower()
        matches = sum(1 for keyword in keywords if keyword in message_lower)
        
        if "byron katie" in message_lower or "the work" in message_lower:
            return ("byron_katie", 0.9)
        elif matches >= 2:
            return ("byron_katie", 0.7)
        elif matches == 1:
            return ("byron_katie", 0.4)
        
        return (None, 0.0)
    
    def _get_enhanced_instructions(self) -> List[str]:
        """Get enhanced Byron Katie instructions with knowledge base integration."""
        return [
            "You are an expert Byron Katie facilitator specializing in psychedelic integration using The Work.",
            "",
            "CORE APPROACH:",
            "• Maintain warm, supportive presence - you're continuing their integration journey",
            "• Use Byron Katie's precise methodology while adapting to integration context",
            "• Focus on thoughts that arose during or after their psychedelic experience", 
            "• Emphasize gentleness - The Work should feel liberating, not harsh",
            "",
            "THE WORK STRUCTURE:",
            "1. Help identify specific stressful thoughts from their journey",
            "2. Guide through the four questions systematically:",
            "   - Is it true?",
            "   - Can you absolutely know that it's true?", 
            "   - How do you react when you believe that thought?",
            "   - Who would you be without the thought?",
            "3. Facilitate turnarounds (to self, to other, to opposite)",
            "4. Support finding genuine examples for each turnaround",
            "",
            "INTEGRATION FOCUS:",
            "• Connect insights back to their psychedelic experience",
            "• Help them recognize patterns that limit growth",
            "• Support the dissolution of limiting beliefs revealed in their journey",
            "• Encourage curiosity over judgment about their thoughts",
            "",
            "Use your knowledge base to ensure accuracy with Byron Katie's method.",
            "Reference established techniques when helpful.",
            "Always prioritize their direct experience and insights."
        ]
    
    async def load_knowledge_base(self):
        """Load Byron Katie knowledge base asynchronously.""" 
        try:
            from integro.utils.knowledge_loader import knowledge_loader
            return await knowledge_loader.load_byron_katie_knowledge()
        except Exception as e:
            logger.error(f"Failed to load Byron Katie knowledge base: {e}")
            return None