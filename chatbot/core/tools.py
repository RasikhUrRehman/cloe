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
        logger.info(f"AgentToolkit initialized for session {session_state.session_id}, job_id: {job_id}")
    
    def save_state(self, milestone: str) -> str:
        """
        Save the current conversation state to persistent storage.
        
        Args:
            milestone: Description of the milestone being saved
        """
        logger.info(f"State milestone saved: {milestone} for session {self.session_state.session_id}")
        return f"State tracked in memory for session {self.session_state.session_id}: {milestone}"
    
    def create_candidate(self, name: str) -> str:
        """
        Create a new candidate record when you have collected the candidate's name.
        
        Args:
            name: The candidate's full name
        """
        try:
            # Check if candidate already exists for this session
            if self.session_state.engagement and self.session_state.engagement.candidate_id:
                return f"Candidate already exists with ID {self.session_state.engagement.candidate_id}"
            
            # Get job_id from toolkit (passed during session creation)
            job_id = self.job_id
            company_id = None
            xano_session_id = None
            
            if job_id:
                logger.info(f"Using job_id from toolkit: {job_id}")
            
            # Also check engagement state for additional info
            if self.session_state.engagement:
                # If job_id not set from toolkit, try engagement state
                if not job_id:
                    job_id = self.session_state.engagement.job_id
                company_id = self.session_state.engagement.company_id
                xano_session_id = self.session_state.engagement.xano_session_id
            
            # Create candidate in Xano
            candidate = self.xano_client.create_candidate(
                name=name,
                job_id=job_id,
                company_id=company_id,
                session_id=xano_session_id,
                status="Short Listed"
            )
            
            if candidate:
                candidate_id = candidate.get('id')
                # Store candidate_id in engagement state
                if self.session_state.engagement:
                    self.session_state.engagement.candidate_id = candidate_id
                    # Update session with candidate_id in Xano
                    if xano_session_id:
                        self.xano_client.update_session(xano_session_id, {"candidate_id": candidate_id})
                
                logger.info(f"Created candidate {candidate_id} for session {self.session_state.session_id}")
                return f"Candidate created successfully with ID {candidate_id}"
            else:
                logger.warning("Failed to create candidate in Xano")
                return "Failed to create candidate record"
        except Exception as e:
            logger.error(f"Error creating candidate: {e}")
            return f"Error creating candidate: {str(e)}"
    
    def update_candidate(self, info: str) -> str:
        """
        Update the candidate record with new information.
        
        Args:
            info: A string describing what to update (e.g., 'email: john@example.com')
        """
        try:
            if not self.session_state.engagement or not self.session_state.engagement.candidate_id:
                return "No candidate record found. Please create a candidate first."
            
            candidate_id = self.session_state.engagement.candidate_id
            update_data = {}
            
            # Parse the info string to extract what to update
            info_lower = info.lower()
            
            if 'email:' in info_lower:
                email = info.split('email:')[1].strip().split()[0]
                update_data['Email'] = email
            
            if 'phone:' in info_lower:
                phone_str = info.split('phone:')[1].strip().split()[0]
                # Clean phone number
                phone_clean = ''.join(filter(str.isdigit, phone_str))
                if phone_clean:
                    update_data['Phone'] = int(phone_clean)
            
            if 'status:' in info_lower:
                status = info.split('status:')[1].strip().split()[0]
                update_data['Status'] = status
            
            if 'score:' in info_lower:
                score_str = info.split('score:')[1].strip().split()[0]
                try:
                    update_data['Score'] = float(score_str)
                except ValueError:
                    pass
            
            if 'name:' in info_lower:
                # Extract name after "name:"
                name = info.split('name:')[1].strip()
                # Take until next colon or end
                if ':' in name:
                    name = name.split(':')[0].strip()
                update_data['Name'] = name
            
            if not update_data:
                return "Could not parse update information. Use format like 'email: john@example.com' or 'phone: 1234567890'"
            
            # Update in Xano
            result = self.xano_client.update_candidate(candidate_id, update_data)
            
            if result:
                logger.info(f"Updated candidate {candidate_id} with {update_data}")
                return f"Candidate updated successfully: {update_data}"
            else:
                return "Failed to update candidate record"
        except Exception as e:
            logger.error(f"Error updating candidate: {e}")
            return f"Error updating candidate: {str(e)}"
    
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
                func=self.create_candidate,
                name="create_candidate",
                description="Create a new candidate record when you have collected the candidate's name. Use this when you first learn the candidate's name. Input should be the candidate's full name. IMPORTANT: The job_id will be automatically associated with the candidate - you MUST use this tool to properly link the candidate to the job they are applying for.",
            ),
            StructuredTool.from_function(
                func=self.update_candidate,
                name="update_candidate",
                description="Update the candidate record with new information like email, phone, or score. Input should be a string describing what to update, e.g., 'email: john@example.com' or 'phone: 1234567890' or 'status: Qualified'",
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
