"""
Session Manager Module
Centralized manager for active agent sessions to avoid global state.
"""
from typing import Any, Dict, Optional, TYPE_CHECKING

from chatbot.utils.utils import setup_logging

if TYPE_CHECKING:
    from chatbot.core.agent import CleoRAGAgent

logger = setup_logging()


class SessionManager:
    """
    Centralized manager for active agent sessions.
    Uses singleton pattern to provide a single source of truth for session state.
    """
    _instance: Optional["SessionManager"] = None
    
    def __init__(self):
        """Initialize the session manager with empty sessions dict."""
        self._sessions: Dict[str, "CleoRAGAgent"] = {}
    
    @classmethod
    def get_instance(cls) -> "SessionManager":
        """Get or create the singleton SessionManager instance."""
        if cls._instance is None:
            cls._instance = SessionManager()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None
    
    @property
    def sessions(self) -> Dict[str, "CleoRAGAgent"]:
        """Get the sessions dictionary."""
        return self._sessions
    
    def get_session(self, session_id: str) -> Optional["CleoRAGAgent"]:
        """
        Get an agent by session ID.
        
        Args:
            session_id: The session ID to look up
            
        Returns:
            The CleoRAGAgent if found, None otherwise
        """
        return self._sessions.get(session_id)
    
    def set_session(self, session_id: str, agent: "CleoRAGAgent") -> None:
        """
        Store an agent for a session ID.
        
        Args:
            session_id: The session ID
            agent: The CleoRAGAgent instance
        """
        self._sessions[session_id] = agent
        logger.info(f"Session {session_id} stored in SessionManager")
    
    def remove_session(self, session_id: str) -> bool:
        """
        Remove a session by ID.
        
        Args:
            session_id: The session ID to remove
            
        Returns:
            True if session was removed, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Session {session_id} removed from SessionManager")
            return True
        return False
    
    def has_session(self, session_id: str) -> bool:
        """
        Check if a session exists.
        
        Args:
            session_id: The session ID to check
            
        Returns:
            True if session exists, False otherwise
        """
        return session_id in self._sessions
    
    def get_or_create_agent(self, session_id: str, job_id: Optional[str] = None) -> "CleoRAGAgent":
        """
        Get existing agent or create a new one for the session.
        
        Args:
            session_id: The session ID
            job_id: Optional job ID for new agents
            
        Returns:
            The CleoRAGAgent for the session
        """
        from chatbot.core.agent import CleoRAGAgent
        from chatbot.state.states import SessionState
        
        if session_id not in self._sessions:
            session_state = SessionState(session_id=session_id)
            agent = CleoRAGAgent(session_state=session_state, job_id=job_id)
            self._sessions[session_id] = agent
            logger.info(f"Created new agent for session {session_id}")
        return self._sessions[session_id]
    
    def clear_all(self) -> None:
        """Clear all sessions."""
        self._sessions.clear()
        logger.info("All sessions cleared from SessionManager")


def get_session_manager() -> SessionManager:
    """
    Get the singleton SessionManager instance.
    
    Returns:
        SessionManager instance
    """
    return SessionManager.get_instance()
