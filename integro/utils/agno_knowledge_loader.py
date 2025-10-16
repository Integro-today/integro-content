"""Agno-compliant knowledge base loader for therapeutic agents."""

import os
import logging
from typing import Optional
from agno.knowledge import Knowledge
try:
    from agno.vectordb.qdrant import Qdrant
except ImportError:
    # Fallback if Qdrant vectordb not available
    Qdrant = None
from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)


class AgnoTherapeuticKnowledgeLoader:
    """Loader for Agno-compliant knowledge bases from Qdrant."""
    
    def __init__(self):
        """Initialize the knowledge loader with Qdrant configuration."""
        # Get Qdrant configuration from environment
        self.qdrant_host = os.getenv('QDRANT_HOST', 'https://qdrant-staging-staging.up.railway.app')
        self.qdrant_port = os.getenv('QDRANT_PORT')
        self.use_external = os.getenv('USE_EXTERNAL_QDRANT', 'true').lower() == 'true'
        
        # Knowledge base collection names (hardcoded for now)
        self.ifs_collection = os.getenv('IFS_KNOWLEDGE_BASE_ID', 'ifs_knowledge_base')
        self.byron_katie_collection = os.getenv('BYRON_KATIE_KNOWLEDGE_BASE_ID', 'byron_katie_knowledge_base')
        
        # Configure Qdrant URL
        if 'railway.app' in self.qdrant_host or self.qdrant_host.startswith('https://'):
            # Railway or external HTTPS endpoint
            self.qdrant_url = self.qdrant_host
        elif self.qdrant_port:
            # Local with port
            self.qdrant_url = f"http://{self.qdrant_host}:{self.qdrant_port}"
        else:
            # Local default
            self.qdrant_url = f"http://{self.qdrant_host}:6333"
            
        logger.info(f"Configured Qdrant URL: {self.qdrant_url}")
    
    def create_knowledge_base(self, collection_name: str, display_name: str = None) -> Optional[Knowledge]:
        """
        Create an Agno Knowledge instance for a Qdrant collection.
        
        Args:
            collection_name: Name of the Qdrant collection
            display_name: Human-readable name for logging
            
        Returns:
            Knowledge instance or None if creation fails
        """
        if not collection_name:
            logger.info(f"No collection name provided for {display_name or 'knowledge base'}")
            return None
            
        try:
            # First check if collection exists
            client = QdrantClient(url=self.qdrant_url)
            try:
                collection_info = client.get_collection(collection_name)
                doc_count = collection_info.points_count
                logger.info(f"✅ Found collection '{collection_name}' with {doc_count} documents")
            except Exception as e:
                logger.warning(f"⚠️ Collection '{collection_name}' not found on {self.qdrant_url}")
                logger.info("Will create collection when documents are added")
                # Continue anyway - Agno can create the collection
            
            # Create Agno-compliant vector database
            vector_db = Qdrant(
                collection=collection_name,
                url=self.qdrant_url,
                # Use default embedding dimension (384 for sentence-transformers)
                dimension=384
            )
            
            # Create Knowledge with the vector database
            knowledge = Knowledge(
                vector_db=vector_db,
                # Optional: Add embedder if needed
                # embedder=OpenAIEmbedder(id="text-embedding-3-small")
            )
            
            logger.info(f"✅ Created Knowledge for {display_name or collection_name}")
            return knowledge
            
        except Exception as e:
            logger.error(f"❌ Failed to create knowledge base for {collection_name}: {e}")
            return None
    
    def load_ifs_knowledge(self) -> Optional[Knowledge]:
        """Load IFS knowledge base."""
        logger.info("Loading IFS knowledge base...")
        return self.create_knowledge_base(
            self.ifs_collection,
            "IFS Knowledge Base"
        )
    
    def load_byron_katie_knowledge(self) -> Optional[Knowledge]:
        """Load Byron Katie knowledge base."""
        logger.info("Loading Byron Katie knowledge base...")
        return self.create_knowledge_base(
            self.byron_katie_collection,
            "Byron Katie Knowledge Base"
        )
    
    def create_and_populate_knowledge_base(self, collection_name: str, content: list[str]) -> Optional[Knowledge]:
        """
        Create a knowledge base and populate it with hardcoded content.
        
        Args:
            collection_name: Name for the Qdrant collection
            content: List of text content to add to the knowledge base
            
        Returns:
            Populated Knowledge instance
        """
        knowledge = self.create_knowledge_base(collection_name)
        if knowledge and content:
            try:
                # Add content to the knowledge base
                for text in content:
                    knowledge.add_content(text_content=text)
                logger.info(f"✅ Added {len(content)} documents to {collection_name}")
            except Exception as e:
                logger.error(f"Failed to populate knowledge base: {e}")
        return knowledge


# Global instance for easy access
agno_knowledge_loader = AgnoTherapeuticKnowledgeLoader()


# Hardcoded therapeutic content for fallback
IFS_CONTENT = [
    """
    Internal Family Systems (IFS) is a transformative, evidence-based model of psychotherapy that believes every person's psyche contains multiple "parts" or sub-personalities, as well as a core Self.
    
    Key IFS Concepts:
    - Parts: Distinct sub-personalities within our internal system, each with its own perspective, feelings, memories, goals, and motivations
    - Self: The core, compassionate, calm, curious essence that can heal and lead the internal system
    - Exiles: Young, wounded parts that carry pain, trauma, and difficult emotions from the past
    - Managers: Protective parts that try to control our lives to prevent exiles' pain from surfacing
    - Firefighters: Reactive protective parts that spring into action when exiled feelings break through
    
    The 8 C's of Self-Leadership:
    1. Calm - A physiological and mental serenity
    2. Curiosity - An open, accepting interest in parts
    3. Clarity - The ability to perceive situations without distortion
    4. Compassion - An open-hearted understanding of parts' pain
    5. Confidence - Trust in one's Self to handle what arises
    6. Courage - Strength to face difficult parts and situations
    7. Creativity - Spontaneous and flexible problem-solving
    8. Connectedness - Feeling of unity with all parts and life itself
    """,
    
    """
    Working with Parts in Psychedelic Integration:
    
    During psychedelic experiences, parts often emerge more clearly and communicate more directly. Integration involves:
    
    1. Welcoming all parts that showed up during the journey
    2. Getting curious about their roles and intentions
    3. Understanding what they're protecting
    4. Accessing Self-energy to witness and heal
    
    Common parts that emerge in psychedelic experiences:
    - The Inner Critic (Manager) - Often softens or reveals its protective intention
    - The Wounded Child (Exile) - May surface with long-held pain needing attention
    - The Spiritual Seeker (Part) - Yearns for transcendence and meaning
    - The Protector (Manager) - Guards against vulnerability
    - The Wild One (Firefighter) - Seeks intensity and altered states
    
    Integration Practice:
    - "How do you feel toward this part?" - Checking for Self-energy
    - "What does this part want you to know?" - Opening communication
    - "What is it afraid would happen if it didn't do its job?" - Understanding protection
    - "How old is this part?" - Recognizing when parts formed
    - "What does this part need from you?" - Facilitating healing
    """
]

BYRON_KATIE_CONTENT = [
    """
    Byron Katie's The Work: A Path to Freedom Through Inquiry
    
    The Work is a simple yet powerful process of inquiry that teaches you to identify and question the thoughts that cause suffering. It consists of four questions and turnarounds.
    
    The Four Questions:
    1. Is it true? (Yes or no. If no, move to question 3.)
    2. Can you absolutely know that it's true? (Yes or no.)
    3. How do you react, what happens, when you believe that thought?
    4. Who would you be without the thought?
    
    The Turnarounds:
    After answering the four questions, you turn the thought around to find opposite statements that might be as true or truer. Common turnarounds include:
    - To the opposite
    - To the self
    - To the other
    
    For each turnaround, find at least three specific, genuine examples of how this turnaround is true in your life.
    
    Key Principles:
    - Suffering is optional and comes from believing our stressful thoughts
    - Reality is always kinder than our stories about it
    - When we argue with reality, we lose—but only 100% of the time
    - The Work is meditation; it's about awareness, not about changing anything
    """,
    
    """
    Using The Work for Psychedelic Integration:
    
    Psychedelic experiences often reveal beliefs and thought patterns that have been running our lives unconsciously. The Work helps integrate these insights by:
    
    1. Examining thoughts that arose during the journey
    2. Questioning limiting beliefs that were highlighted
    3. Investigating fears or resistances that emerged
    4. Exploring new perspectives gained
    
    Common thoughts to investigate after psychedelic experiences:
    - "I am broken/damaged"
    - "I need to be healed"
    - "Others don't understand me"
    - "I'm not doing enough"
    - "The world is harsh/dangerous"
    - "I need psychedelics to be spiritual"
    - "My trauma defines me"
    
    Integration through Inquiry:
    - Notice stressful thoughts from your journey
    - Write them down simply and specifically
    - Apply the four questions with genuine curiosity
    - Find turnarounds and examples
    - Notice how your perspective shifts
    - Allow insights to integrate naturally
    
    Remember: The Work is not about forcing positivity or denying pain. It's about meeting your thoughts with understanding and discovering what's true for you.
    """
]