"""
Chat Routes
Handles all chat-related API endpoints
"""
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from chatbot.utils.utils import setup_logging
from chatbot.utils.xano_client import get_xano_client

logger = setup_logging()
router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    """Request model for chat messages"""
    session_id: str
    message: str


class ChatResponse(BaseModel):
    """Response model for chat messages"""
    session_id: str
    responses: List[str]
    current_stage: str
    timestamp: str


def _validate_api_responses(responses: List[str]) -> List[str]:
    """
    Validate API responses to ensure they are not malformed
    
    Args:
        responses: List of response messages
        
    Returns:
        List of validated response messages
    """
    if not responses or not isinstance(responses, list):
        return [
            "I'm experiencing technical difficulties at the moment. "
            "An agent will connect with you soon to assist you further."
        ]

    validated = []
    for response in responses:
        if not response or not isinstance(response, str):
            continue

        problematic_patterns = [
            "I'm having trouble processing that",
            "Could you try rephrasing your response?",
            "I'm sorry, I didn't understand that.",
        ]

        response_lower = response.lower().strip()
        if len(response_lower) < 5:
            continue

        is_problematic = any(
            pattern.lower() in response_lower
            for pattern in problematic_patterns
        )

        if not is_problematic:
            validated.append(response)

    if not validated:
        return [
            "I'm experiencing technical difficulties at the moment. "
            "An agent will connect with you soon to assist you further. "
            "Thank you for your patience."
        ]

    return validated


# Store for active sessions - will be shared from main app
active_sessions: Dict[str, Any] = {}


def set_active_sessions(sessions: Dict[str, Any]):
    """Set the reference to active sessions from main app"""
    global active_sessions
    active_sessions = sessions


def get_or_create_agent(session_id: str, job_id: str = None):
    """Get existing agent or create new one"""
    from chatbot.core.agent import CleoRAGAgent
    from chatbot.state.states import SessionState
    
    if session_id not in active_sessions:
        session_state = SessionState(session_id=session_id)
        agent = CleoRAGAgent(session_state=session_state, job_id=job_id)
        active_sessions[session_id] = agent
    return active_sessions[session_id]


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message and get a response
    
    Args:
        request: Chat request with session_id and message
        
    Returns:
        Chat response with agent's reply (can be multiple messages)
    """
    try:
        agent = get_or_create_agent(request.session_id)
        
        # Post user message to Xano
        xano_client = get_xano_client()
        if agent.session_state.engagement and agent.session_state.engagement.xano_session_id:
            xano_client.post_message(
                agent.session_state.engagement.xano_session_id,
                request.message,
                "User"
            )
        
        # Process message
        responses = agent.process_message(request.message)
        validated_responses = _validate_api_responses(responses)
        
        # Post AI responses to Xano
        if agent.session_state.engagement and agent.session_state.engagement.xano_session_id:
            for response in validated_responses:
                xano_client.post_message(
                    agent.session_state.engagement.xano_session_id,
                    response,
                    "AI"
                )

        logger.info(
            f"Processed message for session {request.session_id}, generated {len(validated_responses)} response(s)"
        )

        return ChatResponse(
            session_id=request.session_id,
            responses=validated_responses,
            current_stage=agent.session_state.current_stage.value,
            timestamp=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        return ChatResponse(
            session_id=request.session_id,
            responses=[
                "I'm experiencing technical difficulties at the moment. "
                "An agent will connect with you soon to assist you further. "
                "Thank you for your patience."
            ],
            current_stage="error",
            timestamp=datetime.utcnow().isoformat(),
        )
