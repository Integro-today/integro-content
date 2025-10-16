"""Intent detection service with ML and keyword fallback."""

import logging
from typing import Optional, List, Tuple
import os

from integro.activities import ACTIVITIES

logger = logging.getLogger(__name__)


class IntentDetectionService:
    """
    Detect user intent with ML model and keyword fallback.
    
    Implements a fallback chain:
    1. ML model (if available)
    2. Keyword detection
    3. None (no clear intent)
    """
    
    def __init__(self):
        """Initialize intent detection service."""
        self.model = None
        self.model_loaded = False
        self.fallback_mode = False
        
        # Import activities to use their keyword detection
        self.activities = {
            name: activity_class()
            for name, activity_class in ACTIVITIES.items()
        }
        
        # Intent keywords for general detection
        self.intent_keywords = {
            "ifs": [
                "ifs", "internal family", "parts", "exile", 
                "manager", "firefighter", "self energy", "internal system",
                "parts work", "inner parts", "protector"
            ],
            "daily_content": [
                "daily", "content", "wisdom", "reflection", 
                "today", "daily message", "inspiration", "quote",
                "practice", "guidance", "insight"
            ]
        }
    
    def _load_model(self):
        """Attempt to load sentence transformer model."""
        if self.model_loaded or self.fallback_mode:
            return
        
        try:
            # Only try to import if not in fallback mode
            from sentence_transformers import SentenceTransformer
            
            model_name = os.getenv('INTENT_MODEL', 'all-MiniLM-L6-v2')
            logger.info(f"Loading intent detection model: {model_name}")
            
            self.model = SentenceTransformer(model_name)
            self.model_loaded = True
            logger.info("Intent detection model loaded successfully")
            
        except ImportError as e:
            logger.warning(f"Sentence transformers not available: {e}. Using keyword fallback.")
            self.fallback_mode = True
            
        except Exception as e:
            logger.error(f"Failed to load intent model: {e}. Using keyword fallback.")
            self.fallback_mode = True
    
    def detect_intent(self, message: str, context: List[str] = None) -> Tuple[Optional[str], float]:
        """
        Detect user intent from message and context.
        
        Args:
            message: User's message
            context: Recent conversation context
        
        Returns:
            Tuple of (intent, confidence) or (None, 0.0) if no clear intent
        """
        try:
            # Try to load model if not loaded
            if not self.model_loaded and not self.fallback_mode:
                self._load_model()
            
            # Use ML-based detection if available
            if self.model_loaded and self.model:
                return self._detect_with_model(message, context)
            
            # Fallback to keyword-based detection
            return self._detect_with_keywords(message, context)
            
        except Exception as e:
            logger.error(f"Intent detection error: {e}")
            return None, 0.0
    
    def _detect_with_model(self, message: str, context: List[str]) -> Tuple[Optional[str], float]:
        """ML-based intent detection using sentence transformers."""
        try:
            # TODO: Implement proper ML-based detection
            # For now, fall back to keywords
            logger.debug("ML model loaded but using keyword fallback for now")
            return self._detect_with_keywords(message, context)
            
        except Exception as e:
            logger.error(f"ML detection failed: {e}")
            return self._detect_with_keywords(message, context)
    
    def _detect_with_keywords(self, message: str, context: List[str]) -> Tuple[Optional[str], float]:
        """Keyword-based intent detection with activity-specific logic."""
        try:
            # First check activity-specific keyword detection
            best_intent = None
            best_confidence = 0.0
            
            for activity_name, activity in self.activities.items():
                intent, confidence = activity.detect_keywords(message)
                if intent and confidence > best_confidence:
                    best_intent = intent
                    best_confidence = confidence
            
            # If high confidence from activity detection, use it
            if best_confidence >= 0.7:
                return best_intent, best_confidence
            
            # Otherwise do general keyword detection
            message_lower = message.lower()
            
            for intent, keywords in self.intent_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in message_lower)
                
                if matches > 0:
                    # Calculate confidence based on matches
                    # Special boost for exact matches of key phrases
                    if intent == "ifs" and ("ifs" in message_lower or "internal family" in message_lower):
                        confidence = 0.9
                    elif intent == "daily_content" and ("daily" in message_lower and "content" in message_lower):
                        confidence = 0.8
                    else:
                        # General confidence calculation
                        confidence = min(0.4 + (matches * 0.2), 1.0)
                    
                    if confidence > best_confidence:
                        best_intent = intent
                        best_confidence = confidence
            
            # Return best match or None
            if best_confidence > 0.3:  # Minimum confidence threshold
                return best_intent, best_confidence
            
            return None, 0.0
            
        except Exception as e:
            logger.error(f"Keyword detection failed: {e}")
            return None, 0.0
    
    def detect_completion_request(self, message: str) -> bool:
        """
        Detect if user wants to complete/exit current activity.
        
        Args:
            message: User's message
            
        Returns:
            True if completion request detected
        """
        completion_phrases = [
            "i'm done", "i am done", "finish", "complete", "end this",
            "stop", "that's enough", "thats enough", "exit", "quit",
            "back to menu", "main menu", "different activity", 
            "something else", "switch", "change activity", "done with this",
            "let's stop", "lets stop", "finished"
        ]
        
        message_lower = message.lower().strip()
        return any(phrase in message_lower for phrase in completion_phrases)
    
    def detect_help_request(self, message: str) -> bool:
        """
        Detect if user wants help or menu.
        
        Args:
            message: User's message
            
        Returns:
            True if help request detected
        """
        help_phrases = [
            "help", "menu", "what can you do", "what activities",
            "show activities", "list activities", "options", "what's available",
            "what are my options", "show menu", "guide me"
        ]
        
        message_lower = message.lower().strip()
        return any(phrase in message_lower for phrase in help_phrases)