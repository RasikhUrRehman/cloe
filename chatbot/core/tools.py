"""
Agent Tools Module
Contains tool factory for creating tools bound to an agent instance.
Uses LangChain's StructuredTool with closure to avoid global state.
"""
from typing import TYPE_CHECKING, List, Optional
from langchain.tools import StructuredTool

from chatbot.utils.utils import setup_logging
from chatbot.utils.xano_client import get_xano_client

if TYPE_CHECKING:
    from chatbot.state.states import SessionState

logger = setup_logging()


class AgentToolkit:
    """
    Toolkit that creates tools bound to a specific agent's session state.
    This avoids using global variables by encapsulating state within the toolkit instance.
    """
    
    def __init__(self, session_state: "SessionState", job_id: Optional[str] = None):
        """
        Initialize the toolkit with agent's session state and job_id.
        
        Args:
            session_state: The agent's SessionState object
            job_id: The job ID for the position being applied to
        """
        self.session_state = session_state
        self.job_id = job_id
        self.xano_client = get_xano_client()
        self._session_concluded = False  # Track if session has been concluded
        logger.info(f"AgentToolkit initialized for session {session_state.session_id}, job_id: {job_id}")
    
    def save_state(self, milestone: str) -> str:
        """
        Save the current conversation state to persistent storage.
        
        Args:
            milestone: Description of the milestone being saved
        """
        logger.info(f"State milestone saved: {milestone} for session {self.session_state.session_id}")
        return f"State tracked in memory for session {self.session_state.session_id}: {milestone}"
    
    def conclude_session(self, reason: str) -> str:
        """
        Conclude the current session when the user indicates they want to end the conversation.
        This properly closes the session, updates the status in Xano, and saves any collected data.
        
        Args:
            reason: The reason for concluding the session (e.g., "User said goodbye", "User needs time to decide")
        """
        try:
            if self._session_concluded:
                return "Session has already been concluded."
            
            self._session_concluded = True
            xano_session_id = None
            
            if self.session_state.engagement:
                xano_session_id = self.session_state.engagement.xano_session_id
            
            # Determine final status based on what was collected
            final_status = "Ended"
            if self.session_state.application and self.session_state.application.stage_completed:
                final_status = "Completed"
            elif self.session_state.qualification and self.session_state.qualification.stage_completed:
                final_status = "Qualified - Pending"
            elif self.session_state.engagement and self.session_state.engagement.consent_given:
                final_status = "In Progress - Paused"
            else:
                final_status = "Ended - Early Exit"
            
            # Update session in Xano with final status and any collected info
            if xano_session_id:
                update_data = {
                    "Status": final_status,
                    "conversation_stage": "concluded",
                    "conclusion_reason": reason,
                }
                
                # Add any collected candidate info to session
                if self.session_state.application:
                    if self.session_state.application.full_name:
                        update_data["candidate_name"] = self.session_state.application.full_name
                    if self.session_state.application.email:
                        update_data["candidate_email"] = self.session_state.application.email
                    if self.session_state.application.phone_number:
                        update_data["candidate_phone"] = self.session_state.application.phone_number
                
                self.xano_client.update_session(xano_session_id, update_data)
                logger.info(f"Session {xano_session_id} concluded with status: {final_status}, reason: {reason}")
            
            return f"Session concluded successfully. Status: {final_status}. Reason: {reason}"
            
        except Exception as e:
            logger.error(f"Error concluding session: {e}")
            return f"Session ended with note: {reason}"
    
    def store_candidate_info(self, info: str) -> str:
        """
        Store candidate information in the session state.
        This information is kept in memory and stored in session for generating results.
        
        Args:
            info: A string describing what to store (e.g., 'email: john@example.com')
        """
        try:
            xano_session_id = None
            if self.session_state.engagement:
                xano_session_id = self.session_state.engagement.xano_session_id
            
            update_data = {}
            
            # Parse the info string to extract what to store
            info_lower = info.lower()
            
            if 'email:' in info_lower:
                email = info.split('email:')[1].strip().split()[0]
                update_data['candidate_email'] = email
                if self.session_state.application:
                    self.session_state.application.email = email
            
            if 'phone:' in info_lower:
                phone_str = info.split('phone:')[1].strip().split()[0]
                # Clean phone number
                phone_clean = ''.join(filter(str.isdigit, phone_str))
                if phone_clean:
                    update_data['candidate_phone'] = phone_clean
                    if self.session_state.application:
                        self.session_state.application.phone_number = phone_clean
            
            if 'name:' in info_lower:
                # Extract name after "name:"
                name = info.split('name:')[1].strip()
                # Take until next colon or end
                if ':' in name:
                    name = name.split(':')[0].strip()
                update_data['candidate_name'] = name
                if self.session_state.application:
                    self.session_state.application.full_name = name
            
            if not update_data:
                return "Could not parse information. Use format like 'email: john@example.com' or 'phone: 1234567890' or 'name: John Doe'"
            
            # Update session in Xano with candidate info (stored in session, not candidate table)
            if xano_session_id:
                self.xano_client.update_session(xano_session_id, update_data)
                logger.info(f"Updated session {xano_session_id} with candidate info: {update_data}")
            
            return f"Information saved: {update_data}"
        except Exception as e:
            logger.error(f"Error storing candidate info: {e}")
            return f"Error storing information: {str(e)}"
    
    def get_tools(self) -> List[StructuredTool]:
        """
        Get all tools bound to this toolkit's session state.
        
        Returns:
            List of StructuredTool instances bound to this toolkit
        """
        tools = [
            StructuredTool.from_function(
                func=self.save_state,
                name="save_state",
                description="Save the current conversation state to persistent storage. Use this to save key conversation milestones like when user starts application, shares resume, or agrees to proceed.",
            ),
            StructuredTool.from_function(
                func=self.store_candidate_info,
                name="store_candidate_info",
                description="Store candidate information like name, email, or phone in the session. Use this when you collect personal information from the candidate. Input should be a string like 'name: John Doe' or 'email: john@example.com' or 'phone: 1234567890'. This saves the information for generating results.",
            ),
            StructuredTool.from_function(
                func=self.conclude_session,
                name="conclude_session",
                description="Use this tool when the user indicates they want to end the conversation (e.g., says goodbye, thanks and leaves, needs to go, will think about it). This properly saves any collected data and marks the session as ended. Input should be the reason for ending (e.g., 'User said goodbye', 'User needs time to decide', 'User completed application'). IMPORTANT: Always call this when the user is leaving!",
            ),
        ]
        return tools


def create_agent_tools(session_state: "SessionState", job_id: Optional[str] = None) -> List[StructuredTool]:
    """
    Factory function to create tools bound to a specific session state.
    
    Args:
        session_state: The agent's SessionState object
        job_id: The job ID for the position being applied to
        
    Returns:
        List of tools bound to the provided session state
    """
    toolkit = AgentToolkit(session_state, job_id)
    return toolkit.get_tools()
