"""
Sessions Routes
Handles all session-related API endpoints
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from chatbot.state.states import SessionState, EngagementState
from chatbot.utils.job_fetcher import get_job_by_id
from chatbot.utils.utils import setup_logging
from chatbot.utils.xano_client import get_xano_client
from chatbot.utils.session_manager import get_session_manager
from chatbot.utils.question_generator import generate_questions_from_job_details

logger = setup_logging()
router = APIRouter(prefix="/api/v1/sessions", tags=["Sessions"])


def get_or_create_agent(session_id: str, job_id: str = None):
    """Get existing agent or create new one"""
    session_manager = get_session_manager()
    return session_manager.get_or_create_agent(session_id, job_id)


# Request/Response Models
class SessionCreateRequest(BaseModel):
    """Request model for creating a new session"""
    job_id: Optional[str] = Field(default=None, description="Job ID to apply for")
    language: Optional[str] = Field(default="en", description="Language code")


class SessionCreateResponse(BaseModel):
    """Response model for session creation"""
    session_id: str
    xano_session_id: Optional[int] = None
    message: str  # For backward compatibility - first message
    messages: Optional[List[str]] = None  # All split messages (new)
    current_stage: str


class SessionStatusResponse(BaseModel):
    """Response model for session status"""
    session_id: str
    current_stage: str
    engagement_complete: bool
    qualification_complete: bool
    application_complete: bool
    verification_complete: bool = False
    ready_for_verification: bool


class SessionDetailsResponse(BaseModel):
    """Response model for complete session details"""
    session_id: str
    xano_session_id: Optional[int] = None
    current_stage: str
    created_at: Any  # Can be int (timestamp) or str
    updated_at: Any  # Can be int (timestamp) or str
    engagement: Optional[Dict[str, Any]] = None
    qualification: Optional[Dict[str, Any]] = None
    application: Optional[Dict[str, Any]] = None
    verification: Optional[Dict[str, Any]] = None
    chat_history: List[Dict[str, str]] = []
    job_details: Optional[Dict[str, Any]] = None
    status: Dict[str, bool]


class SessionUpdateRequest(BaseModel):
    """Request model for updating session"""
    status: Optional[str] = Field(default=None, description="Session status")
    candidate_name: Optional[str] = Field(default=None, description="Candidate name")
    candidate_email: Optional[str] = Field(default=None, description="Candidate email")
    candidate_phone: Optional[str] = Field(default=None, description="Candidate phone")


class XanoSessionResponse(BaseModel):
    """Response model for Xano session data"""
    id: int
    status: Optional[str] = None
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    candidate_phone: Optional[str] = None
    created_at: Optional[Any] = None  # Can be int (timestamp) or str


@router.post("/create", response_model=SessionCreateResponse)
async def create_session(request: SessionCreateRequest):
    """
    Create a new conversation session
    """
    try:
        session_id = str(uuid.uuid4())
        
        # Fetch job details if job_id is provided
        job_details = None
        generated_questions = None
        if request.job_id:
            job_details = get_job_by_id(request.job_id)
            print(job_details)
            print("-----"*4)
            if not job_details:
                logger.warning(f"Job ID {request.job_id} not found")
            else:

                
                #Generate questions from job details
                try:
                    generated_questions = await generate_questions_from_job_details(job_details, num_questions=15)
                    logger.info(f"Generated {len(generated_questions)} questions for job {request.job_id}")
                except Exception as e:
                    logger.warning(f"Failed to generate questions for job {request.job_id}: {e}")

        
        # Create agent with job_id in memory
        agent = get_or_create_agent(session_id, job_id=request.job_id)

        # Initialize engagement state with job details
        if not agent.session_state.engagement:
            agent.session_state.engagement = EngagementState(session_id=session_id)

        if request.job_id:
            agent.session_state.engagement.job_id = request.job_id
            agent.session_state.engagement.job_details = job_details
            agent.session_state.engagement.generated_questions = generated_questions

        if request.language:
            agent.session_state.engagement.language = request.language

        # Recreate agent with job context
        agent._refresh_agent_with_job_context()

        # Generate initial greeting
        initial_greeting_prompt = "Start the conversation by greeting the user warmly and introducing yourself."
        initial_messages = agent.process_message(initial_greeting_prompt)
        
        # Post initial greeting to Xano
        xano_client = get_xano_client()
        if agent.session_state.engagement and agent.session_state.engagement.xano_session_id:
            for msg in initial_messages:
                xano_client.post_message(
                    agent.session_state.engagement.xano_session_id,
                    msg,
                    "AI"
                )

        logger.info(f"Created new session: {session_id} for job: {request.job_id or 'N/A'}")

        # Ensure initial_messages is always a list
        if not initial_messages:
            initial_messages = ["Hello! I'm Cleo, ready to help you!"]
        elif not isinstance(initial_messages, list):
            initial_messages = [initial_messages]
        
        return SessionCreateResponse(
            session_id=session_id,
            xano_session_id=agent.session_state.engagement.xano_session_id if agent.session_state.engagement else None,
            message=initial_messages[0],  # First message for backward compatibility
            messages=initial_messages,  # All split messages
            current_stage=agent.session_state.current_stage.value,
        )
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


# @router.get("", response_model=List[XanoSessionResponse])
# async def list_sessions():
#     """
#     List all sessions from Xano
#     """
#     try:
#         xano_client = get_xano_client()
#         sessions = xano_client.get_sessions()
#         if sessions is None:
#             return []
#         return sessions
#     except Exception as e:
#         logger.error(f"Error listing sessions: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


# @router.get("/{session_id}/status", response_model=SessionStatusResponse)
# async def get_session_status(session_id: str):
#     """
#     Get the current status of a session.
#     Returns 404 if the session does not exist.
#     Note: This endpoint no longer syncs to Xano on every call to reduce log noise.
#     Xano sync happens only on state changes (via process_message).
#     """
#     try:
#         session_manager = get_session_manager()
        
#         if not session_manager.has_session(session_id):
#             raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
#         agent = session_manager.get_session(session_id)
#         summary = agent.get_conversation_summary()
        
#         # Note: Removed sync_session_state_to_xano() call here
#         # Xano sync now happens only on actual state changes in process_message
        
#         # Get verification_complete from agent state
#         verification_complete = False
#         if agent.session_state.verification:
#             verification_complete = agent.session_state.verification.stage_completed

#         return SessionStatusResponse(
#             session_id=summary["session_id"],
#             current_stage=summary["current_stage"],
#             engagement_complete=summary["engagement_complete"],
#             qualification_complete=summary["qualification_complete"],
#             application_complete=summary["application_complete"],
#             verification_complete=verification_complete,
#             ready_for_verification=summary["ready_for_verification"],
#         )
#     except Exception as e:
#         logger.error(f"Error getting session status: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to get session status: {str(e)}")


# @router.get("/{session_id}/xano-status")
# async def get_session_xano_status(session_id: str):
#     """
#     Get the real-time synchronized session status from Xano.
#     This endpoint first syncs the local session state to Xano,
#     then returns the status as stored in Xano.
#     """
#     try:
#         session_manager = get_session_manager()
        
#         if not session_manager.has_session(session_id):
#             raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
#         agent = session_manager.get_session(session_id)
        
#         # First sync the current state to Xano
#         agent.sync_session_state_to_xano()
        
#         # Then get the status from Xano
#         xano_status = agent.get_xano_session_status()
        
#         return {
#             "session_id": session_id,
#             **xano_status,
#             "local_current_stage": agent.session_state.current_stage.value,
#         }
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error getting Xano session status: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to get Xano status: {str(e)}")


# @router.get("/{session_id}", response_model=SessionDetailsResponse)
# async def get_session_details(session_id: str):
#     """
#     Get complete session details including chat history from Xano.
#     Returns 404 if the session does not exist.
#     """
#     try:
#         session_manager = get_session_manager()
        
#         if not session_manager.has_session(session_id):
#             raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
#         agent = session_manager.get_session(session_id)
#         summary = agent.get_conversation_summary()
        
#         # Get chat history from Xano
#         chat_history = []
#         xano_client = get_xano_client()
#         if agent.session_state.engagement and agent.session_state.engagement.xano_session_id:
#             messages = xano_client.get_messages_by_session_id(
#                 agent.session_state.engagement.xano_session_id
#             )
#             if messages:
#                 for msg in messages:
#                     chat_history.append({
#                         "role": "human" if msg.get("MsgCreator") == "User" else "ai",
#                         "content": msg.get("MsgContent", ""),
#                         "timestamp": msg.get("created_at", datetime.utcnow().isoformat())
#                     })

#         # Prepare state data
#         engagement_data = None
#         if agent.session_state.engagement:
#             engagement_data = agent.session_state.engagement.model_dump()

#         qualification_data = None
#         if agent.session_state.qualification:
#             qualification_data = agent.session_state.qualification.model_dump()

#         application_data = None
#         if agent.session_state.application:
#             application_data = agent.session_state.application.model_dump()

#         verification_data = None
#         if agent.session_state.verification:
#             verification_data = agent.session_state.verification.model_dump()

#         job_details = None
#         if agent.session_state.engagement and agent.session_state.engagement.job_details:
#             job_details = agent.session_state.engagement.job_details

#         return SessionDetailsResponse(
#             session_id=agent.session_state.session_id,
#             xano_session_id=agent.session_state.engagement.xano_session_id if agent.session_state.engagement else None,
#             current_stage=agent.session_state.current_stage.value,
#             created_at=agent.session_state.created_at,
#             updated_at=agent.session_state.updated_at,
#             engagement=engagement_data,
#             qualification=qualification_data,
#             application=application_data,
#             verification=verification_data,
#             chat_history=chat_history,
#             job_details=job_details,
#             status={
#                 "engagement_complete": summary["engagement_complete"],
#                 "qualification_complete": summary["qualification_complete"],
#                 "application_complete": summary["application_complete"],
#                 "ready_for_verification": summary["ready_for_verification"],
#             }
#         )
#     except Exception as e:
#         logger.error(f"Error getting session details: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to get session details: {str(e)}")


# @router.patch("/{session_id}")
# async def update_session(session_id: str, request: SessionUpdateRequest):
#     """
#     Update session status or candidate_id in Xano.
#     Returns 404 if the session does not exist.
#     """
#     try:
#         session_manager = get_session_manager()
        
#         if not session_manager.has_session(session_id):
#             raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
#         agent = session_manager.get_session(session_id)
        
#         if not agent.session_state.engagement or not agent.session_state.engagement.xano_session_id:
#             raise HTTPException(status_code=404, detail="Session not found in Xano")
        
#         xano_client = get_xano_client()
#         update_data = {}
        
#         if request.status:
#             update_data["Status"] = request.status
#         if request.candidate_id:
#             update_data["candidate_id"] = request.candidate_id
        
#         if update_data:
#             result = xano_client.update_session(
#                 agent.session_state.engagement.xano_session_id,
#                 update_data
#             )
#             if result:
#                 return {"message": "Session updated successfully", "session": result}
#             else:
#                 raise HTTPException(status_code=500, detail="Failed to update session in Xano")
        
#         return {"message": "No updates provided"}
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error updating session: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")


# @router.delete("/{session_id}")
# async def delete_session(session_id: str):
#     """
#     Delete a session from both memory and Xano
#     """
#     try:
#         xano_client = get_xano_client()
#         session_manager = get_session_manager()
        
#         if session_manager.has_session(session_id):
#             agent = session_manager.get_session(session_id)
            
#             # Delete from Xano if exists
#             if agent.session_state.engagement and agent.session_state.engagement.xano_session_id:
#                 xano_client.delete_session(agent.session_state.engagement.xano_session_id)
            
#             session_manager.remove_session(session_id)
#             logger.info(f"Deleted session: {session_id}")
#             return {"message": f"Session {session_id} deleted successfully"}
#         else:
#             raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error deleting session: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


# @router.post("/{session_id}/reset")
# async def reset_session(session_id: str):
#     """
#     Reset a session's conversation memory
#     """
#     try:
#         session_manager = get_session_manager()
        
#         if session_manager.has_session(session_id):
#             agent = session_manager.get_session(session_id)
#             agent.reset_conversation()
#             logger.info(f"Reset session: {session_id}")
#             return {"message": f"Session {session_id} reset successfully"}
#         else:
#             raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error resetting session: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to reset session: {str(e)}")


# # Xano direct session APIs
# @router.get("/xano/{xano_session_id}")
# async def get_xano_session(xano_session_id: int):
#     """
#     Get session directly from Xano by Xano session ID.
#     If there's an active agent with this Xano session, it will sync the state first.
#     """
#     try:
#         xano_client = get_xano_client()
#         session_manager = get_session_manager()
        
#         # Try to find the active agent with this xano_session_id and sync its state
#         for local_session_id, agent in session_manager.sessions.items():
#             if (agent.session_state.engagement and 
#                 agent.session_state.engagement.xano_session_id == xano_session_id):
#                 # Found the active agent, sync its state to Xano first
#                 agent.sync_session_state_to_xano()
#                 logger.info(f"Synced active agent state for xano_session {xano_session_id}")
#                 break
        
#         session = xano_client.get_session_by_id(xano_session_id)
#         if session:
#             return session
#         raise HTTPException(status_code=404, detail=f"Session {xano_session_id} not found")
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error getting Xano session: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


# @router.delete("/xano/{xano_session_id}")
# async def delete_xano_session(xano_session_id: int):
#     """
#     Delete session directly from Xano
#     """
#     try:
#         xano_client = get_xano_client()
#         if xano_client.delete_session(xano_session_id):
#             return {"message": f"Xano session {xano_session_id} deleted successfully"}
#         raise HTTPException(status_code=500, detail="Failed to delete session from Xano")
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error deleting Xano session: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")
