"""State manager service for session persistence."""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class StateManager:
    """
    Manages session state persistence.
    
    Currently uses in-memory storage as a placeholder.
    TODO: Implement Redis backend for production.
    """
    
    # In-memory storage for development
    _storage = {}
    
    def __init__(self, session_id: str, ttl_hours: int = 24):
        """
        Initialize state manager for a session.
        
        Args:
            session_id: Unique session identifier
            ttl_hours: Time to live in hours (default 24)
        """
        self.session_id = session_id
        self.ttl = timedelta(hours=ttl_hours)
        self._ensure_session_exists()
        
    def _ensure_session_exists(self):
        """Ensure session exists in storage."""
        if self.session_id not in self._storage:
            self._storage[self.session_id] = {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "data": {}
            }
    
    def update_state(self, state: Dict[str, Any]) -> bool:
        """
        Update session state.
        
        Args:
            state: State dictionary to persist
            
        Returns:
            True if successful
        """
        try:
            self._ensure_session_exists()
            
            # Update the state
            if isinstance(state, dict):
                self._storage[self.session_id]["data"].update(state)
            else:
                self._storage[self.session_id]["data"] = state
                
            self._storage[self.session_id]["updated_at"] = datetime.now().isoformat()
            
            logger.debug(f"Updated state for session {self.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update state: {e}")
            return False
    
    def get_state(self) -> Optional[Dict[str, Any]]:
        """
        Get current session state.
        
        Returns:
            State dictionary or None if not found
        """
        try:
            if self.session_id in self._storage:
                return self._storage[self.session_id]["data"]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get state: {e}")
            return None
    
    def set_state(self, state: Dict[str, Any]) -> bool:
        """
        Replace entire session state.
        
        Args:
            state: New state dictionary
            
        Returns:
            True if successful
        """
        try:
            self._ensure_session_exists()
            self._storage[self.session_id]["data"] = state
            self._storage[self.session_id]["updated_at"] = datetime.now().isoformat()
            
            logger.debug(f"Set state for session {self.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set state: {e}")
            return False
    
    def delete_session(self) -> bool:
        """
        Delete session from storage.
        
        Returns:
            True if successful
        """
        try:
            if self.session_id in self._storage:
                del self._storage[self.session_id]
                logger.debug(f"Deleted session {self.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions based on TTL."""
        try:
            now = datetime.now()
            expired_sessions = []
            
            for session_id, session_data in self._storage.items():
                updated_at = datetime.fromisoformat(session_data["updated_at"])
                if now - updated_at > self.ttl:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self._storage[session_id]
                logger.debug(f"Cleaned up expired session {session_id}")
                
        except Exception as e:
            logger.error(f"Failed to cleanup sessions: {e}")
    
    @classmethod
    def get_all_sessions(cls) -> Dict[str, Any]:
        """
        Get all active sessions (for debugging).
        
        Returns:
            Dictionary of all sessions
        """
        return cls._storage.copy()
    
    def __repr__(self) -> str:
        """String representation."""
        return f"StateManager(session_id='{self.session_id}')"


# TODO: Add Redis implementation
class RedisStateManager(StateManager):
    """
    Redis-backed state manager for production use.
    
    This is a placeholder for the Redis implementation.
    """
    
    def __init__(self, session_id: str, redis_client=None, ttl_hours: int = 24):
        """
        Initialize Redis state manager.
        
        Args:
            session_id: Unique session identifier
            redis_client: Redis client instance
            ttl_hours: Time to live in hours
        """
        super().__init__(session_id, ttl_hours)
        self.redis_client = redis_client
        
        if redis_client is None:
            logger.warning("No Redis client provided, falling back to in-memory storage")
    
    # TODO: Implement Redis methods
    # - update_state() with Redis SET
    # - get_state() with Redis GET
    # - delete_session() with Redis DEL
    # - Use Redis TTL for automatic expiration