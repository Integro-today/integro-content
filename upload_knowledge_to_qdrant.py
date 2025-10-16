#!/usr/bin/env python3
"""Upload therapeutic knowledge chunks to Railway Qdrant collections."""

import os
import sys
import logging
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import hashlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TherapeuticKnowledgeUploader:
    """Upload therapeutic knowledge to Qdrant collections."""
    
    def __init__(self, qdrant_url: str = None):
        """Initialize the uploader with Qdrant connection."""
        self.qdrant_url = qdrant_url or os.getenv('QDRANT_HOST', 'https://qdrant-staging-staging.up.railway.app')
        
        # Initialize Qdrant client
        logger.info(f"Connecting to Qdrant at: {self.qdrant_url}")
        self.client = QdrantClient(url=self.qdrant_url)
        
        # Initialize sentence transformer for embeddings
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions
        logger.info("Loaded sentence transformer model")
        
        # Collection names from environment or defaults
        self.ifs_collection = os.getenv('IFS_KNOWLEDGE_BASE_ID', 'ifs-knowledge-base')
        self.byron_katie_collection = os.getenv('BYRON_KATIE_KNOWLEDGE_BASE_ID', 'byron-katie-knowledge-base')
    
    def create_collection_if_not_exists(self, collection_name: str, dimension: int = 384):
        """Create a collection if it doesn't already exist."""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            if collection_name in [c.name for c in collections.collections]:
                logger.info(f"Collection '{collection_name}' already exists")
                return True
            
            # Create collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE)
            )
            logger.info(f"✅ Created collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            return False
    
    def generate_id(self, text: str) -> str:
        """Generate a unique ID for a text chunk."""
        return hashlib.md5(text.encode()).hexdigest()[:16]
    
    def upload_chunks(self, collection_name: str, chunks: List[Dict[str, Any]]):
        """
        Upload knowledge chunks to a collection.
        
        Args:
            collection_name: Name of the Qdrant collection
            chunks: List of dicts with 'text' and optional 'metadata' keys
        """
        if not self.create_collection_if_not_exists(collection_name):
            return False
        
        points = []
        for i, chunk in enumerate(chunks):
            text = chunk.get('text', '')
            metadata = chunk.get('metadata', {})
            
            # Generate embedding
            embedding = self.model.encode(text).tolist()
            
            # Create point
            point_id = self.generate_id(text)
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    'text': text,
                    'chunk_index': i,
                    **metadata
                }
            )
            points.append(point)
        
        # Upload points to collection
        try:
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            logger.info(f"✅ Uploaded {len(points)} chunks to '{collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload chunks: {e}")
            return False
    
    def upload_ifs_knowledge(self):
        """Upload IFS knowledge chunks."""
        logger.info("\n📚 Uploading IFS Knowledge Base...")
        
        ifs_chunks = [
            {
                'text': """Internal Family Systems (IFS) Core Model:
                IFS is an evidence-based psychotherapy that views the mind as containing multiple sub-personalities or 'parts',
                each with its own perspective, interests, memories, and viewpoint. A core tenet is that every part has a positive
                intent, even if its actions are counterproductive or harmful.""",
                'metadata': {'topic': 'core_model', 'category': 'theory'}
            },
            {
                'text': """The Self in IFS:
                The Self is the core, undamaged essence of a person. It is characterized by eight C's:
                Calm, Clarity, Curiosity, Compassion, Confidence, Courage, Creativity, and Connectedness.
                When leading from Self, a person can heal their parts and help them transform.""",
                'metadata': {'topic': 'self', 'category': 'theory'}
            },
            {
                'text': """IFS Parts Categories - Exiles:
                Exiles are young, vulnerable parts that have experienced trauma or have been wounded.
                They carry the pain, fear, and shame from past experiences. Other parts work hard to protect
                us from feeling the pain of exiles. Exiles often appear as young children in our internal system.""",
                'metadata': {'topic': 'exiles', 'category': 'parts'}
            },
            {
                'text': """IFS Parts Categories - Managers:
                Managers are protective parts that work to prevent the pain of exiles from being triggered.
                They try to control our lives, relationships, and environment. Common manager roles include:
                the Inner Critic, the Perfectionist, the Planner, the Caretaker, and the Achiever.""",
                'metadata': {'topic': 'managers', 'category': 'parts'}
            },
            {
                'text': """IFS Parts Categories - Firefighters:
                Firefighters are reactive protective parts that spring into action when exiled emotions break through.
                They use extreme measures to distract from or numb emotional pain. Common firefighter behaviors include:
                substance use, binge eating, self-harm, dissociation, and compulsive behaviors.""",
                'metadata': {'topic': 'firefighters', 'category': 'parts'}
            },
            {
                'text': """IFS and Psychedelic Integration:
                During psychedelic experiences, the usual barriers between parts often soften, allowing:
                1. Direct communication with exiled parts
                2. Managers to relax their protective roles
                3. Understanding of firefighters' protective intentions
                4. Enhanced access to Self-energy
                5. Spontaneous unburdening of old wounds""",
                'metadata': {'topic': 'psychedelic_integration', 'category': 'application'}
            },
            {
                'text': """IFS Integration Questions:
                Key questions for exploring parts after psychedelic experiences:
                - How do you feel toward this part? (checking for Self-energy)
                - What does this part want you to know?
                - What is this part afraid would happen if it stopped doing its job?
                - How old is this part? When did it take on this role?
                - What does this part need from you to feel safe?""",
                'metadata': {'topic': 'integration_questions', 'category': 'practice'}
            },
            {
                'text': """IFS Unburdening Process:
                Unburdening is the process of releasing the extreme beliefs, emotions, and sensations that parts carry.
                After witnessing a part's story with compassion from Self, the part can release its burden through:
                1. Acknowledging the burden
                2. Asking if the part is ready to let it go
                3. Releasing it to light, water, fire, earth, or wind
                4. Inviting in positive qualities to fill the space""",
                'metadata': {'topic': 'unburdening', 'category': 'practice'}
            },
            {
                'text': """Self-Leadership in Daily Life:
                Practicing Self-leadership involves:
                - Noticing when parts are activated
                - Breathing and centering to access Self
                - Speaking for parts rather than from them
                - Offering compassion to all parts
                - Making decisions from Self rather than from reactive parts""",
                'metadata': {'topic': 'self_leadership', 'category': 'practice'}
            },
            {
                'text': """Working with Protective Parts:
                When working with managers and firefighters:
                1. Thank them for their protection
                2. Get curious about their positive intention
                3. Ask what they're protecting
                4. Negotiate permission to work with exiles
                5. Assure them they won't lose their role, just transform it""",
                'metadata': {'topic': 'protective_parts', 'category': 'practice'}
            }
        ]
        
        return self.upload_chunks(self.ifs_collection, ifs_chunks)
    
    def upload_byron_katie_knowledge(self):
        """Upload Byron Katie's The Work knowledge chunks."""
        logger.info("\n📚 Uploading Byron Katie Knowledge Base...")
        
        byron_katie_chunks = [
            {
                'text': """Byron Katie's The Work Overview:
                The Work is a simple yet powerful process of inquiry consisting of four questions and turnarounds.
                It's a way to identify and question the thoughts that cause all the suffering in the world.
                The Work is meditation—it's about awareness, not about trying to change your thoughts.""",
                'metadata': {'topic': 'overview', 'category': 'foundation'}
            },
            {
                'text': """The Four Questions of The Work:
                1. Is it true? (Yes or no. If no, move to 3.)
                2. Can you absolutely know that it's true? (Yes or no.)
                3. How do you react, what happens, when you believe that thought?
                4. Who would you be without the thought?""",
                'metadata': {'topic': 'four_questions', 'category': 'core_process'}
            },
            {
                'text': """Question 1 - Is it true?:
                This question requires a simple yes or no answer. It invites you to revisit your statement
                with an open mind. If your answer is no, continue to question 3. This question begins the
                process of stepping back from automatic believing of our thoughts.""",
                'metadata': {'topic': 'question_1', 'category': 'questions'}
            },
            {
                'text': """Question 2 - Can you absolutely know that it's true?:
                This question goes deeper, inviting you to examine if you can really know with absolute
                certainty that your thought is true. It reveals the limits of what we can actually know
                and opens the mind to other possibilities.""",
                'metadata': {'topic': 'question_2', 'category': 'questions'}
            },
            {
                'text': """Question 3 - How do you react when you believe that thought?:
                This question helps you become aware of the cause-and-effect relationship between your
                thoughts and your emotions, physical sensations, and behaviors. Notice: What emotions arise?
                How do you treat yourself and others? What physical sensations occur?""",
                'metadata': {'topic': 'question_3', 'category': 'questions'}
            },
            {
                'text': """Question 4 - Who would you be without the thought?:
                This question invites you to imagine yourself in the same situation without believing the
                thought. It's not about dropping the thought, but exploring who you would be in that moment
                without the thought running your life.""",
                'metadata': {'topic': 'question_4', 'category': 'questions'}
            },
            {
                'text': """The Turnarounds:
                After the four questions, turn the thought around to find opposites that could be as true or truer:
                - To the self (I should understand myself)
                - To the other (He does understand me)
                - To the opposite (He shouldn't understand me)
                For each turnaround, find at least three genuine, specific examples.""",
                'metadata': {'topic': 'turnarounds', 'category': 'core_process'}
            },
            {
                'text': """The Work and Psychedelic Integration:
                Psychedelic experiences often reveal thought patterns that have been unconscious. The Work helps:
                1. Question insights that feel overwhelming
                2. Investigate fears that arose during the journey
                3. Examine beliefs about self, others, and reality
                4. Integrate new perspectives through inquiry
                5. Find peace with whatever was experienced""",
                'metadata': {'topic': 'psychedelic_integration', 'category': 'application'}
            },
            {
                'text': """Common Thoughts for Psychedelic Integration:
                Thoughts that often benefit from The Work after psychedelic experiences:
                - 'I am broken/damaged'
                - 'I need to be healed'
                - 'I saw the truth about reality'
                - 'Others don't understand my experience'
                - 'I need psychedelics to grow spiritually'
                - 'My trauma defines me'
                - 'I'm not doing enough with my insights'""",
                'metadata': {'topic': 'integration_thoughts', 'category': 'application'}
            },
            {
                'text': """Finding Genuine Examples for Turnarounds:
                When finding examples for turnarounds:
                1. Look for specific, real situations from your life
                2. Avoid spiritual bypassing or forced positivity
                3. Be honest about what you can genuinely see
                4. Small examples are as valid as big ones
                5. If you can't find three examples, that's okay—find what you can""",
                'metadata': {'topic': 'turnaround_examples', 'category': 'practice'}
            },
            {
                'text': """The Work as Living Meditation:
                The Work is meant to be lived, not just understood intellectually:
                - Notice stressful thoughts as they arise
                - Write them down for later inquiry
                - Do The Work regularly, not just in crisis
                - Allow insights to integrate naturally
                - Trust the process without forcing outcomes""",
                'metadata': {'topic': 'living_meditation', 'category': 'practice'}
            },
            {
                'text': """Judge Your Neighbor Worksheet:
                The foundation of The Work is the Judge Your Neighbor worksheet:
                1. Who angers, confuses, hurts, saddens, or disappoints you, and why?
                2. How do you want them to change?
                3. What should or shouldn't they do, be, think, or feel?
                4. What do you need from them?
                5. What do you think of them? Make a list.
                6. What don't you want to experience again?""",
                'metadata': {'topic': 'worksheet', 'category': 'tools'}
            }
        ]
        
        return self.upload_chunks(self.byron_katie_collection, byron_katie_chunks)
    
    def verify_upload(self, collection_name: str):
        """Verify that chunks were uploaded successfully."""
        try:
            collection_info = self.client.get_collection(collection_name)
            count = collection_info.points_count
            logger.info(f"✅ Collection '{collection_name}' has {count} documents")
            
            # Try a sample search
            sample_vector = self.model.encode("therapy healing integration").tolist()
            results = self.client.search(
                collection_name=collection_name,
                query_vector=sample_vector,
                limit=3
            )
            
            if results:
                logger.info(f"   Sample search returned {len(results)} results")
                for i, result in enumerate(results, 1):
                    text_preview = result.payload.get('text', '')[:100]
                    logger.info(f"   {i}. Score: {result.score:.3f} - {text_preview}...")
                    
        except Exception as e:
            logger.error(f"Failed to verify collection: {e}")


def main():
    """Main function to upload all knowledge bases."""
    print("=" * 70)
    print("🚀 Therapeutic Knowledge Base Uploader")
    print("=" * 70)
    
    # Get Qdrant URL
    qdrant_url = os.getenv('QDRANT_HOST', 'https://qdrant-staging-staging.up.railway.app')
    print(f"\n📍 Target Qdrant Server: {qdrant_url}")
    
    # Confirm before proceeding
    print("\nThis will create/update the following collections:")
    print(f"  - IFS: {os.getenv('IFS_KNOWLEDGE_BASE_ID', 'ifs-knowledge-base')}")
    print(f"  - Byron Katie: {os.getenv('BYRON_KATIE_KNOWLEDGE_BASE_ID', 'byron-katie-knowledge-base')}")
    
    response = input("\nProceed with upload? (y/n): ")
    if response.lower() != 'y':
        print("Upload cancelled.")
        return
    
    # Initialize uploader
    uploader = TherapeuticKnowledgeUploader(qdrant_url)
    
    # Upload knowledge bases
    success = True
    
    if uploader.upload_ifs_knowledge():
        uploader.verify_upload(uploader.ifs_collection)
    else:
        success = False
    
    if uploader.upload_byron_katie_knowledge():
        uploader.verify_upload(uploader.byron_katie_collection)
    else:
        success = False
    
    print("\n" + "=" * 70)
    if success:
        print("✅ Knowledge bases uploaded successfully!")
        print("\nYour agents can now use these collections by setting:")
        print(f"  IFS_KNOWLEDGE_BASE_ID={uploader.ifs_collection}")
        print(f"  BYRON_KATIE_KNOWLEDGE_BASE_ID={uploader.byron_katie_collection}")
    else:
        print("⚠️ Some uploads failed. Check the logs above.")
    print("=" * 70)


if __name__ == "__main__":
    main()