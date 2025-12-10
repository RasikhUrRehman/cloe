"""
Agent Tools Module
Contains all tools available to the Cleo RAG Agent using LangChain's @tool decorator
"""
from typing import Optional
from langchain.tools import tool

from chatbot.utils.utils import setup_logging
from chatbot.utils.xano_client import get_xano_client

logger = setup_logging()

# Global references to be set by the agent
_session_state = None
_job_id = None


def set_tool_context(session_state, job_id: Optional[str] = None):
    """
    Set the context for tools to access session state and job_id.
    Must be called by the agent before tools can be used.
    
    Args:
        session_state: The current SessionState object
        job_id: The job ID for the position being applied to
    """
    global _session_state, _job_id
    _session_state = session_state
    _job_id = job_id
    logger.info(f"Tool context set for session {session_state.session_id}, job_id: {job_id}")


def get_session_state():
    """Get the current session state"""
    global _session_state
    if _session_state is None:
        raise RuntimeError("Tool context not set. Call set_tool_context first.")
    return _session_state


def get_job_id() -> Optional[str]:
    """Get the current job_id"""
    global _job_id
    return _job_id


@tool
def save_state(milestone: str) -> str:
    """
    Save the current conversation state to persistent storage.
    Use this to save key conversation milestones like when user starts application,
    shares resume, or agrees to proceed.
    
    Args:
        milestone: Description of the milestone being saved
    """
    session_state = get_session_state()
    logger.info(f"State milestone saved: {milestone} for session {session_state.session_id}")
    return f"State tracked in memory for session {session_state.session_id}: {milestone}"


@tool
def create_candidate(name: str) -> str:
    """
    Create a new candidate record when you have collected the candidate's name.
    Use this when you first learn the candidate's name.
    
    IMPORTANT: The job_id from memory will be automatically associated with the candidate.
    You MUST use this tool to properly link the candidate to the job they are applying for.
    
    Args:
        name: The candidate's full name
    """
    session_state = get_session_state()
    xano_client = get_xano_client()
    
    try:
        # Check if candidate already exists for this session
        if session_state.engagement and session_state.engagement.candidate_id:
            return f"Candidate already exists with ID {session_state.engagement.candidate_id}"
        
        # Get job_id from tool context (passed during session creation)
        job_id = get_job_id()
        company_id = None
        xano_session_id = None
        
        if job_id:
            logger.info(f"Using job_id from tool context: {job_id}")
        
        # Also check engagement state for additional info
        if session_state.engagement:
            # If job_id not set from context, try engagement state
            if not job_id:
                job_id = session_state.engagement.job_id
            company_id = session_state.engagement.company_id
            xano_session_id = session_state.engagement.xano_session_id
        
        # Create candidate in Xano using the xano_client
        candidate = xano_client.create_candidate(
            name=name,
            job_id=job_id,
            company_id=company_id,
            session_id=xano_session_id,
            status="Short Listed"
        )
        
        if candidate:
            candidate_id = candidate.get('id')
            # Store candidate_id in engagement state
            if session_state.engagement:
                session_state.engagement.candidate_id = candidate_id
                # Update session with candidate_id in Xano
                if xano_session_id:
                    xano_client.update_session(xano_session_id, {"candidate_id": candidate_id})
            
            logger.info(f"Created candidate {candidate_id} for session {session_state.session_id}")
            return f"Candidate created successfully with ID {candidate_id}"
        else:
            logger.warning("Failed to create candidate in Xano")
            return "Failed to create candidate record"
    except Exception as e:
        logger.error(f"Error creating candidate: {e}")
        return f"Error creating candidate: {str(e)}"


@tool
def update_candidate(info: str) -> str:
    """
    Update the candidate record with new information.
    
    Args:
        info: A string describing what to update. Format examples:
              - 'email: john@example.com'
              - 'phone: 1234567890'
              - 'status: Qualified'
              - 'score: 85.5'
              - 'name: John Doe'
    """
    session_state = get_session_state()
    xano_client = get_xano_client()
    
    try:
        if not session_state.engagement or not session_state.engagement.candidate_id:
            return "No candidate record found. Please create a candidate first."
        
        candidate_id = session_state.engagement.candidate_id
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
        
        # Update in Xano using the xano_client
        result = xano_client.update_candidate(candidate_id, update_data)
        
        if result:
            logger.info(f"Updated candidate {candidate_id} with {update_data}")
            return f"Candidate updated successfully: {update_data}"
        else:
            return "Failed to update candidate record"
    except Exception as e:
        logger.error(f"Error updating candidate: {e}")
        return f"Error updating candidate: {str(e)}"


def get_all_tools():
    """
    Get all available tools for the agent.
    
    Returns:
        List of tool functions decorated with @tool
    """
    return [
        save_state,
        create_candidate,
        update_candidate,
    ]
