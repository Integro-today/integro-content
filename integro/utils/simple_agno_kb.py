"""Simplified Agno knowledge base for therapeutic agents using embedded content."""

import os
import logging
from typing import Optional
from agno.knowledge import Knowledge
import asyncio

logger = logging.getLogger(__name__)


class SimpleTherapeuticKnowledge:
    """Simple knowledge provider using Agno's Knowledge with embedded content."""
    
    @staticmethod
    def create_ifs_knowledge() -> Optional[Knowledge]:
        """Create IFS knowledge base with embedded content."""
        try:
            # Create simple Knowledge without external vector DB
            # This will use in-memory storage
            knowledge = Knowledge()
            
            # Add IFS therapeutic content
            ifs_content = [
                """Internal Family Systems (IFS) Core Concepts:
                - Parts: Sub-personalities with distinct perspectives and roles
                - Self: The core essence with 8 C's (Calm, Curiosity, Clarity, Compassion, Confidence, Courage, Creativity, Connectedness)
                - Exiles: Wounded parts carrying pain from the past
                - Managers: Protective parts preventing pain from surfacing
                - Firefighters: Reactive parts that distract from breakthrough pain""",
                
                """IFS in Psychedelic Integration:
                During psychedelic experiences, parts emerge more clearly. Integration involves:
                1. Welcoming all parts that appeared
                2. Getting curious about their roles
                3. Understanding their protective intentions
                4. Accessing Self-energy for healing
                5. Building relationships with parts from Self""",
                
                """Common IFS Questions for Integration:
                - 'How do you feel toward this part?' - Checking for Self-energy
                - 'What does this part want you to know?' - Opening dialogue
                - 'What is it afraid would happen if it stopped?' - Understanding protection
                - 'How old is this part?' - Recognizing origins
                - 'What does this part need?' - Facilitating healing"""
            ]
            
            # Load content into knowledge base (compat with async/sync APIs)
            for content in ifs_content:
                try:
                    add_fn = getattr(knowledge, 'add_content', None)
                    result = None
                    if callable(add_fn):
                        result = add_fn(text_content=content)
                    else:
                        add_async = getattr(knowledge, 'add_content_async', None)
                        if callable(add_async):
                            result = add_async(text_content=content)

                    # If the call returned a coroutine, schedule it appropriately
                    if asyncio.iscoroutine(result):
                        try:
                            loop = asyncio.get_running_loop()
                            loop.create_task(result)
                        except RuntimeError:
                            asyncio.run(result)
                except Exception as load_err:
                    logger.warning(f"Skipping IFS content chunk due to error: {load_err}")
            
            logger.info("✅ Created IFS knowledge base with embedded content")
            return knowledge
            
        except Exception as e:
            logger.error(f"Failed to create IFS knowledge base: {e}")
            return None
    
    @staticmethod
    def create_byron_katie_knowledge() -> Optional[Knowledge]:
        """Create Byron Katie knowledge base with embedded content."""
        try:
            # Create simple Knowledge without external vector DB
            knowledge = Knowledge()
            
            # Add Byron Katie content
            byron_content = [
                """Byron Katie's The Work - Four Questions:
                1. Is it true? (Yes or no only)
                2. Can you absolutely know that it's true? (Yes or no)
                3. How do you react when you believe that thought? (Explore sensations, emotions, behaviors)
                4. Who would you be without the thought? (Imagine the freedom)
                
                After the questions, find turnarounds - opposites that might be equally or more true.""",
                
                """The Work for Psychedelic Integration:
                Psychedelic experiences reveal unconscious beliefs. Use The Work to:
                - Question thoughts that arose during the journey
                - Investigate limiting beliefs highlighted
                - Explore fears or resistances
                - Integrate new perspectives
                
                Common thoughts to investigate:
                'I am broken', 'I need healing', 'Others don't understand', 'I'm not enough'""",
                
                """Turnarounds in The Work:
                After the four questions, create turnarounds:
                - To the opposite: 'I am broken' becomes 'I am whole'
                - To the self: 'He should understand me' becomes 'I should understand me'
                - To the other: 'She is wrong' becomes 'I am wrong'
                
                Find three genuine, specific examples for each turnaround."""
            ]
            
            # Load content into knowledge base (compat with async/sync APIs)
            for content in byron_content:
                try:
                    add_fn = getattr(knowledge, 'add_content', None)
                    result = None
                    if callable(add_fn):
                        result = add_fn(text_content=content)
                    else:
                        add_async = getattr(knowledge, 'add_content_async', None)
                        if callable(add_async):
                            result = add_async(text_content=content)

                    if asyncio.iscoroutine(result):
                        try:
                            loop = asyncio.get_running_loop()
                            loop.create_task(result)
                        except RuntimeError:
                            asyncio.run(result)
                except Exception as load_err:
                    logger.warning(f"Skipping Byron Katie content chunk due to error: {load_err}")
            
            logger.info("✅ Created Byron Katie knowledge base with embedded content")
            return knowledge
            
        except Exception as e:
            logger.error(f"Failed to create Byron Katie knowledge base: {e}")
            return None


# Convenience functions for easy access
def get_ifs_knowledge() -> Optional[Knowledge]:
    """Get IFS knowledge base."""
    return SimpleTherapeuticKnowledge.create_ifs_knowledge()

def get_byron_katie_knowledge() -> Optional[Knowledge]:
    """Get Byron Katie knowledge base."""
    return SimpleTherapeuticKnowledge.create_byron_katie_knowledge()