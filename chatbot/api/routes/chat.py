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
from chatbot.utils.session_manager import get_session_manager

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
    logger.debug(f"Validating {len(responses) if responses else 0} responses")
    
    if not responses or not isinstance(responses, list):
        logger.warning(f"Invalid responses format: {type(responses)}")
        return [
            "I'm experiencing technical difficulties at the moment. "
            "An agent will connect with you soon to assist you further."
        ]

    validated = []
    for idx, response in enumerate(responses):
        if not response or not isinstance(response, str):
            logger.warning(f"Response {idx} is invalid type or empty: {type(response)}")
            continue

        response_stripped = response.strip()
        if len(response_stripped) < 5:
            logger.debug(f"Response {idx} too short (< 5 chars), skipping")
            continue

        problematic_patterns = [
            "I'm having trouble processing that",
            "Could you try rephrasing your response?",
            "I'm sorry, I didn't understand that.",
        ]

        response_lower = response_stripped.lower()
        is_problematic = any(
            pattern.lower() in response_lower
            for pattern in problematic_patterns
        )

        if not is_problematic:
            logger.debug(f"Response {idx} validated successfully")
            validated.append(response_stripped)
        else:
            logger.debug(f"Response {idx} contains problematic pattern")

    if not validated:
        logger.warning("All responses filtered out, returning fallback")
        return [
            "I'm experiencing technical difficulties at the moment. "
            "An agent will connect with you soon to assist you further. "
            "Thank you for your patience."
        ]

    logger.info(f"Validated {len(validated)} responses from {len(responses)} total")
    return validated


def get_or_create_agent(session_id: str, job_id: str = None):
    """Get existing agent or create new one"""
    session_manager = get_session_manager()
    return session_manager.get_or_create_agent(session_id, job_id)


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message and get a response.
    Requires an existing session - returns 404 if session not found.
    
    Args:
        request: Chat request with session_id and message
        
    Returns:
        Chat response with agent's reply (can be multiple messages)
    """
    try:
        session_manager = get_session_manager()
        
        if not session_manager.has_session(request.session_id):
            raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found. Please create a session first.")
        
        agent = session_manager.get_session(request.session_id)
        
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
        logger.debug(f"Raw responses from agent: {responses}")
        
        validated_responses = _validate_api_responses(responses)
        logger.debug(f"Validated responses: {validated_responses}")
        
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
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
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
