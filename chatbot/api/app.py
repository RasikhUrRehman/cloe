"""
FastAPI Application for Cleo RAG Agent
Provides REST API endpoints for chat interactions
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime

from chatbot.core.agent import CleoRAGAgent
from chatbot.core.retrievers import RetrievalMethod
from chatbot.state.states import SessionState, StateManager
from chatbot.utils.config import settings, ensure_directories
from chatbot.utils.utils import setup_logging

# Initialize logging
logger = setup_logging()

# Ensure directories exist
ensure_directories()

# Initialize FastAPI app
app = FastAPI(
    title="Cleo RAG Agent API",
    description="AI-powered job application chatbot with RAG capabilities",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (in production, use Redis or database)
active_sessions: Dict[str, CleoRAGAgent] = {}


# Pydantic Models
class SessionCreateRequest(BaseModel):
    """Request model for creating a new session"""
    retrieval_method: Optional[str] = Field(
        default="hybrid",
        description="Retrieval method: semantic, similarity, or hybrid"
    )
    language: Optional[str] = Field(
        default="en",
        description="Language code (en, es, etc.)"
    )


class SessionCreateResponse(BaseModel):
    """Response model for session creation"""
    session_id: str
    message: str
    current_stage: str


class ChatRequest(BaseModel):
    """Request model for chat messages"""
    session_id: str
    message: str


class ChatResponse(BaseModel):
    """Response model for chat messages"""
    session_id: str
    response: str
    current_stage: str
    timestamp: str


class SessionStatusResponse(BaseModel):
    """Response model for session status"""
    session_id: str
    current_stage: str
    engagement_complete: bool
    qualification_complete: bool
    application_complete: bool
    verification_complete: bool


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    version: str
    timestamp: str


# Helper Functions
def get_or_create_agent(session_id: str, retrieval_method: str = "hybrid") -> CleoRAGAgent:
    """
    Get existing agent or create new one
    
    Args:
        session_id: Session ID
        retrieval_method: Retrieval method to use
    
    Returns:
        CleoRAGAgent instance
    """
    if session_id not in active_sessions:
        # Map string to enum
        method_map = {
            "semantic": RetrievalMethod.SEMANTIC,
            "similarity": RetrievalMethod.SIMILARITY,
            "hybrid": RetrievalMethod.HYBRID
        }
        method = method_map.get(retrieval_method.lower(), RetrievalMethod.HYBRID)
        
        # Try to load existing session from storage
        state_manager = StateManager()
        engagement = state_manager.load_engagement(session_id)
        
        if engagement:
            # Reconstruct session state
            session_state = SessionState(session_id=session_id)
            session_state.engagement = engagement
            session_state.qualification = state_manager.load_qualification(session_id)
            session_state.application = state_manager.load_application(session_id)
            session_state.verification = state_manager.load_verification(session_id)
            
            # Determine current stage
            if session_state.verification and session_state.verification.stage_completed:
                from chatbot.state.states import ConversationStage
                session_state.current_stage = ConversationStage.COMPLETED
            elif session_state.application and not session_state.application.stage_completed:
                from chatbot.state.states import ConversationStage
                session_state.current_stage = ConversationStage.APPLICATION
            elif session_state.qualification and not session_state.qualification.stage_completed:
                from chatbot.state.states import ConversationStage
                session_state.current_stage = ConversationStage.QUALIFICATION
            elif session_state.engagement and not session_state.engagement.stage_completed:
                from chatbot.state.states import ConversationStage
                session_state.current_stage = ConversationStage.ENGAGEMENT
            
            agent = CleoRAGAgent(session_state=session_state, retrieval_method=method)
        else:
            # Create new agent
            agent = CleoRAGAgent(retrieval_method=method)
        
        active_sessions[session_id] = agent
    
    return active_sessions[session_id]


# API Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )


@app.post("/api/v1/session/create", response_model=SessionCreateResponse)
async def create_session(request: SessionCreateRequest):
    """
    Create a new conversation session
    
    Args:
        request: Session creation request
    
    Returns:
        Session creation response with session_id
    """
    try:
        # Generate new session ID
        session_id = str(uuid.uuid4())
        
        # Create agent
        agent = get_or_create_agent(session_id, request.retrieval_method)
        
        # Set language if provided
        if request.language:
            if not agent.session_state.engagement:
                from chatbot.state.states import EngagementState
                agent.session_state.engagement = EngagementState(
                    session_id=session_id
                )
            agent.session_state.engagement.language = request.language
        
        logger.info(f"Created new session: {session_id}")
        
        return SessionCreateResponse(
            session_id=session_id,
            message="Session created successfully. You can now start chatting!",
            current_stage=agent.session_state.current_stage.value
        )
    
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message and get a response
    
    Args:
        request: Chat request with session_id and message
    
    Returns:
        Chat response with agent's reply
    """
    try:
        # Get or create agent
        agent = get_or_create_agent(request.session_id)
        
        # Process message
        response = agent.process_message(request.message)
        
        logger.info(f"Processed message for session {request.session_id}")
        
        return ChatResponse(
            session_id=request.session_id,
            response=response,
            current_stage=agent.session_state.current_stage.value,
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@app.get("/api/v1/session/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """
    Get the current status of a session
    
    Args:
        session_id: Session ID
    
    Returns:
        Session status information
    """
    try:
        # Get or create agent
        agent = get_or_create_agent(session_id)
        
        # Get conversation summary
        summary = agent.get_conversation_summary()
        
        return SessionStatusResponse(
            session_id=summary['session_id'],
            current_stage=summary['current_stage'],
            engagement_complete=summary['engagement_complete'],
            qualification_complete=summary['qualification_complete'],
            application_complete=summary['application_complete'],
            verification_complete=summary['verification_complete']
        )
    
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session status: {str(e)}")


@app.delete("/api/v1/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session and free up resources
    
    Args:
        session_id: Session ID
    
    Returns:
        Deletion confirmation
    """
    try:
        if session_id in active_sessions:
            # Save final state before deleting
            agent = active_sessions[session_id]
            agent.state_manager.save_session(agent.session_state)
            
            # Remove from active sessions
            del active_sessions[session_id]
            
            logger.info(f"Deleted session: {session_id}")
            return {"message": f"Session {session_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


@app.post("/api/v1/session/{session_id}/reset")
async def reset_session(session_id: str):
    """
    Reset a session's conversation memory
    
    Args:
        session_id: Session ID
    
    Returns:
        Reset confirmation
    """
    try:
        if session_id in active_sessions:
            agent = active_sessions[session_id]
            agent.reset_conversation()
            
            logger.info(f"Reset session: {session_id}")
            return {"message": f"Session {session_id} reset successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset session: {str(e)}")


# Startup and Shutdown Events
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("Cleo RAG Agent API starting up...")
    logger.info(f"Using OpenAI model: {settings.OPENAI_CHAT_MODEL}")
    logger.info(f"Milvus host: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Cleo RAG Agent API shutting down...")
    
    # Save all active sessions
    for session_id, agent in active_sessions.items():
        try:
            agent.state_manager.save_session(agent.session_state)
            logger.info(f"Saved session: {session_id}")
        except Exception as e:
            logger.error(f"Error saving session {session_id}: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
