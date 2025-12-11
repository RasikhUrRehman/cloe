"""
Session Manager Module
Centralized manager for active agent sessions to avoid global state.
Includes session timeout mechanism for auto-concluding inactive sessions.
"""
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, TYPE_CHECKING

from chatbot.utils.utils import setup_logging

if TYPE_CHECKING:
    from chatbot.core.agent import CleoRAGAgent

logger = setup_logging()

# Default session timeout in minutes
DEFAULT_SESSION_TIMEOUT_MINUTES = 2


class SessionManager:
    """
    Centralized manager for active agent sessions.
    Uses singleton pattern to provide a single source of truth for session state.
    Includes automatic session timeout handling.
    """
    _instance: Optional["SessionManager"] = None
    
    def __init__(self):
        """Initialize the session manager with empty sessions dict."""
        self._sessions: Dict[str, "CleoRAGAgent"] = {}
        self._last_activity: Dict[str, datetime] = {}  # Track last activity per session
        self._timeout_minutes = DEFAULT_SESSION_TIMEOUT_MINUTES
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start background thread to check for timed out sessions."""
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._stop_cleanup.clear()
            self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self._cleanup_thread.start()
            logger.info("Session cleanup thread started")
    
    def _cleanup_loop(self):
        """Background loop to check and cleanup timed out sessions."""
        while not self._stop_cleanup.is_set():
            try:
                self._check_and_cleanup_sessions()
            except Exception as e:
                logger.error(f"Error in session cleanup loop: {e}")
            # Check every minute
            self._stop_cleanup.wait(60)
    
    def _check_and_cleanup_sessions(self):
        """Check for timed out sessions and conclude them."""
        now = datetime.utcnow()
        timeout_delta = timedelta(minutes=self._timeout_minutes)
        sessions_to_conclude = []
        
        for session_id, last_activity in list(self._last_activity.items()):
            if now - last_activity > timeout_delta:
                sessions_to_conclude.append(session_id)
        
        for session_id in sessions_to_conclude:
            self._conclude_timed_out_session(session_id)
    
    def _conclude_timed_out_session(self, session_id: str):
        """Conclude a session that has timed out."""
        try:
            agent = self._sessions.get(session_id)
            if agent:
                # Use the toolkit's conclude_session method
                if hasattr(agent, 'toolkit'):
                    result = agent.toolkit.conclude_session(
                        f"Session timed out after {self._timeout_minutes} minutes of inactivity"
                    )
                    logger.info(f"Auto-concluded timed out session {session_id}: {result}")
                
                # Remove from tracking
                self._last_activity.pop(session_id, None)
                # Note: We don't remove the session itself in case user comes back
                # The session data is preserved for reference
        except Exception as e:
            logger.error(f"Error concluding timed out session {session_id}: {e}")
    
    def update_activity(self, session_id: str):
        """Update the last activity timestamp for a session."""
        self._last_activity[session_id] = datetime.utcnow()
    
    def set_timeout_minutes(self, minutes: int):
        """Set the session timeout in minutes."""
        self._timeout_minutes = max(1, minutes)  # Minimum 1 minute
        logger.info(f"Session timeout set to {self._timeout_minutes} minutes")
    
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
        agent = self._sessions.get(session_id)
        if agent:
            # Update activity timestamp when session is accessed
            self.update_activity(session_id)
        return agent
    
    def set_session(self, session_id: str, agent: "CleoRAGAgent") -> None:
        """
        Store an agent for a session ID.
        
        Args:
            session_id: The session ID
            agent: The CleoRAGAgent instance
        """
        self._sessions[session_id] = agent
        self.update_activity(session_id)
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
            self._last_activity.pop(session_id, None)
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
        
        # Update activity timestamp
        self.update_activity(session_id)
        return self._sessions[session_id]
    
    def clear_all(self) -> None:
        """Clear all sessions."""
        self._sessions.clear()
        self._last_activity.clear()
        logger.info("All sessions cleared from SessionManager")


def get_session_manager() -> SessionManager:
    """
    Get the singleton SessionManager instance.
    
    Returns:
        SessionManager instance
    """
    return SessionManager.get_instance()
