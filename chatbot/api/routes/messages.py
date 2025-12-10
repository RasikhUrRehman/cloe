"""
Messages Routes
Handles all AI chat message-related API endpoints
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from chatbot.utils.utils import setup_logging
from chatbot.utils.xano_client import get_xano_client

logger = setup_logging()
router = APIRouter(prefix="/api/v1/messages", tags=["Messages"])


# Request/Response Models
class MessageCreateRequest(BaseModel):
    """Request model for creating a message"""
    session_id: int = Field(..., description="Session ID")
    MsgContent: str = Field(..., description="Message content")
    MsgCreator: str = Field(..., description="Message creator (AI or User)")


class MessageUpdateRequest(BaseModel):
    """Request model for updating a message"""
    MsgContent: Optional[str] = Field(default=None, description="Message content")
    MsgCreator: Optional[str] = Field(default=None, description="Message creator")


class MessageResponse(BaseModel):
    """Response model for message data"""
    id: Optional[int] = None
    session_id: Optional[int] = None
    MsgContent: Optional[str] = None
    MsgCreator: Optional[str] = None
    created_at: Optional[Any] = None  # Can be int (timestamp) or str


@router.get("", response_model=List[MessageResponse])
async def list_messages():
    """
    List all AI chat messages from Xano
    """
    try:
        xano_client = get_xano_client()
        messages = xano_client.get_messages()
        if messages is None:
            return []
        return messages
    except Exception as e:
        logger.error(f"Error listing messages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list messages: {str(e)}")


@router.post("", response_model=MessageResponse)
async def create_message(request: MessageCreateRequest):
    """
    Create a new AI chat message in Xano
    """
    try:
        if request.MsgCreator not in ["AI", "User"]:
            raise HTTPException(
                status_code=400, 
                detail="MsgCreator must be either 'AI' or 'User'"
            )
        
        xano_client = get_xano_client()
        
        message = xano_client.post_message(
            session_id=request.session_id,
            msg_content=request.MsgContent,
            msg_creator=request.MsgCreator,
        )
        
        if message:
            logger.info(f"Created message: {message.get('id')}")
            return message
        
        raise HTTPException(status_code=500, detail="Failed to create message in Xano")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create message: {str(e)}")


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(message_id: int):
    """
    Get a specific message by ID
    """
    try:
        xano_client = get_xano_client()
        message = xano_client.get_message_by_id(message_id)
        
        if message:
            return message
        
        raise HTTPException(status_code=404, detail=f"Message {message_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get message: {str(e)}")


@router.patch("/{message_id}", response_model=MessageResponse)
async def update_message(message_id: int, request: MessageUpdateRequest):
    """
    Update a message in Xano
    """
    try:
        xano_client = get_xano_client()
        
        update_data = {}
        if request.MsgContent is not None:
            update_data["MsgContent"] = request.MsgContent
        if request.MsgCreator is not None:
            if request.MsgCreator not in ["AI", "User"]:
                raise HTTPException(
                    status_code=400, 
                    detail="MsgCreator must be either 'AI' or 'User'"
                )
            update_data["MsgCreator"] = request.MsgCreator
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        message = xano_client.update_message(message_id, update_data)
        
        if message:
            logger.info(f"Updated message: {message_id}")
            return message
        
        raise HTTPException(status_code=500, detail="Failed to update message in Xano")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update message: {str(e)}")


@router.delete("/{message_id}")
async def delete_message(message_id: int):
    """
    Delete a message from Xano
    """
    try:
        xano_client = get_xano_client()
        
        if xano_client.delete_message(message_id):
            logger.info(f"Deleted message: {message_id}")
            return {"message": f"Message {message_id} deleted successfully"}
        
        raise HTTPException(status_code=500, detail="Failed to delete message from Xano")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete message: {str(e)}")


@router.get("/session/{session_id}", response_model=List[MessageResponse])
async def get_messages_by_session(session_id: int):
    """
    Get all messages for a specific session
    """
    try:
        xano_client = get_xano_client()
        messages = xano_client.get_messages_by_session_id(session_id)
        
        if messages is None:
            return []
        
        return messages
    except Exception as e:
        logger.error(f"Error getting messages for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")
