"""
FastAPI Application for Cleo RAG Agent
Provides REST API endpoints for chat interactions
"""

import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from chatbot.core.agent import CleoRAGAgent
from chatbot.core.ingestion import DocumentIngestion
from chatbot.core.retrievers import RetrievalMethod
from chatbot.state.states import SessionState, StateManager
from chatbot.utils.config import ensure_directories, settings
from chatbot.utils.job_fetcher import get_job_by_id
from chatbot.utils.utils import get_current_timestamp, setup_logging

# Initialize logging
logger = setup_logging()

# Ensure directories exist
ensure_directories()

# Initialize FastAPI app
app = FastAPI(
    title="Cleo RAG Agent API",
    description="AI-powered job application chatbot with RAG capabilities",
    version="1.0.0",
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

    job_id: Optional[str] = Field(default=None, description="Job ID to apply for")
    retrieval_method: Optional[str] = Field(
        default="hybrid",
        description="Retrieval method: semantic, similarity, or hybrid",
    )
    language: Optional[str] = Field(
        default="en", description="Language code (en, es, etc.)"
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
    responses: List[str]  # Changed from single 'response' to multiple 'responses'
    current_stage: str
    timestamp: str


class SessionStatusResponse(BaseModel):
    """Response model for session status"""

    session_id: str
    current_stage: str
    engagement_complete: bool
    qualification_complete: bool
    application_complete: bool
    ready_for_verification: bool


class SessionDetailsResponse(BaseModel):
    """Response model for complete session details"""

    session_id: str
    current_stage: str
    created_at: str
    updated_at: str
    engagement: Optional[Dict[str, Any]] = None
    qualification: Optional[Dict[str, Any]] = None
    application: Optional[Dict[str, Any]] = None
    verification: Optional[Dict[str, Any]] = None
    chat_history: List[Dict[str, str]] = []
    job_details: Optional[Dict[str, Any]] = None
    status: Dict[str, bool]


class HealthResponse(BaseModel):
    """Response model for health check"""

    status: str
    version: str
    timestamp: str


class DocumentUploadResponse(BaseModel):
    """Response model for document upload"""

    message: str
    document_id: str
    filename: str
    document_type: str
    company_name: str
    job_type: str
    section: str
    total_chunks: int
    total_characters: int
    timestamp: str



@app.get("/", response_model=HealthResponse)
@app.head("/")
def read_root() -> HealthResponse:
    """Health endpoint that supports GET and HEAD on root path

    Returns basic status information used by load-balancers and health checks.
    """
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow().isoformat(),
    )


class DocumentListResponse(BaseModel):
    """Response model for listing documents"""

    documents: List[Dict[str, Any]]
    total_count: int


class DocumentDeleteResponse(BaseModel):
    """Response model for document deletion"""

    message: str
    document_id: str
    deleted: bool


class ApplicationResponse(BaseModel):
    """Response model for application data"""
    
    session_id: str
    timestamp: str
    job: Optional[Dict[str, Any]] = None
    applicant: Optional[Dict[str, Any]] = None
    qualification: Optional[Dict[str, Any]] = None
    application: Optional[Dict[str, Any]] = None
    verification: Optional[Dict[str, Any]] = None
    fit_score: Optional[Dict[str, Any]] = None
    status: str


class ApplicationSummary(BaseModel):
    """Summary model for application list"""
    
    session_id: Optional[str] = None
    timestamp: Optional[str] = None
    applicant_name: Optional[str] = None
    applicant_email: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    status: Optional[str] = None
    fit_score: Optional[float] = None
    rating: Optional[str] = None


class ApplicationListResponse(BaseModel):
    """Response model for listing applications"""
    
    applications: List[ApplicationSummary]
    total_count: int
    limit: int
    offset: int


# Helper Functions
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
            
        # Check for common problematic patterns
        problematic_patterns = [
            "I'm having trouble processing that",
            "Could you try rephrasing your response?",
            "I'm sorry, I didn't understand that.",
        ]
        
        response_lower = response.lower().strip()
        
        # Skip responses that are too short or contain problematic patterns
        if len(response_lower) < 5:
            continue
            
        is_problematic = any(
            pattern.lower() in response_lower 
            for pattern in problematic_patterns
        )
        
        if not is_problematic:
            validated.append(response)
    
    # If no valid responses, return fallback
    if not validated:
        return [
            "I'm experiencing technical difficulties at the moment. "
            "An agent will connect with you soon to assist you further. "
            "Thank you for your patience."
        ]
    
    return validated


def get_or_create_agent(
    session_id: str, retrieval_method: str = "hybrid"
) -> CleoRAGAgent:
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
            "hybrid": RetrievalMethod.HYBRID,
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
            if (
                session_state.verification
                and session_state.verification.stage_completed
            ):
                from chatbot.state.states import ConversationStage

                session_state.current_stage = ConversationStage.COMPLETED
            elif (
                session_state.application
                and not session_state.application.stage_completed
            ):
                from chatbot.state.states import ConversationStage

                session_state.current_stage = ConversationStage.APPLICATION
            elif (
                session_state.qualification
                and not session_state.qualification.stage_completed
            ):
                from chatbot.state.states import ConversationStage

                session_state.current_stage = ConversationStage.QUALIFICATION
            elif (
                session_state.engagement
                and not session_state.engagement.stage_completed
            ):
                from chatbot.state.states import ConversationStage

                session_state.current_stage = ConversationStage.ENGAGEMENT

            agent = CleoRAGAgent(session_state=session_state, retrieval_method=method)
        else:
            # Create new agent with specified session_id
            session_state = SessionState(session_id=session_id)
            agent = CleoRAGAgent(session_state=session_state, retrieval_method=method)

        active_sessions[session_id] = agent

    return active_sessions[session_id]


# API Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return HealthResponse(
        status="healthy", version="1.0.0", timestamp=datetime.utcnow().isoformat()
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy", version="1.0.0", timestamp=datetime.utcnow().isoformat()
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

        # Fetch job details if job_id is provided
        job_details = None
        if request.job_id:
            job_details = get_job_by_id(request.job_id)
            if not job_details:
                logger.warning(
                    f"Job ID {request.job_id} not found, proceeding without job details"
                )

        # Create agent
        agent = get_or_create_agent(session_id, request.retrieval_method)

        # Initialize engagement state with job details
        if not agent.session_state.engagement:
            from chatbot.state.states import EngagementState

            agent.session_state.engagement = EngagementState(session_id=session_id)

        # Set job_id and job_details
        if request.job_id:
            agent.session_state.engagement.job_id = request.job_id
            agent.session_state.engagement.job_details = job_details

        # Set language if provided
        if request.language:
            agent.session_state.engagement.language = request.language

        # Recreate agent with job context (this will include job details in the system prompt)
        agent._refresh_agent_with_job_context()

        # Generate initial greeting from Cleo
        initial_greeting_prompt = "Start the conversation by greeting the user warmly and introducing yourself."
        initial_messages = agent.process_message(initial_greeting_prompt)

        logger.info(
            f"Created new session: {session_id} for job: {request.job_id if request.job_id else 'N/A'}"
        )

        return SessionCreateResponse(
            session_id=session_id,
            message=(
                initial_messages[0]
                if initial_messages
                else "Hello! I'm Cleo, ready to help you!"
            ),  # Use first message for initial greeting
            current_stage=agent.session_state.current_stage.value,
        )

    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create session: {str(e)}"
        )


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message and get a response

    Args:
        request: Chat request with session_id and message

    Returns:
        Chat response with agent's reply (can be multiple messages)
    """
    try:
        # Get or create agent
        agent = get_or_create_agent(request.session_id)

        # Process message (returns list of messages)
        responses = agent.process_message(request.message)

        # Additional validation to ensure we don't return malformed responses
        validated_responses = _validate_api_responses(responses)

        logger.info(
            f"Processed message for session {request.session_id}, generated {len(validated_responses)} response(s)"
        )

        return ChatResponse(
            session_id=request.session_id,
            responses=validated_responses,  # Return list of messages
            current_stage=agent.session_state.current_stage.value,
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        # Return fallback message instead of HTTP error
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
            session_id=summary["session_id"],
            current_stage=summary["current_stage"],
            engagement_complete=summary["engagement_complete"],
            qualification_complete=summary["qualification_complete"],
            application_complete=summary["application_complete"],
            ready_for_verification=summary["ready_for_verification"],
        )

    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get session status: {str(e)}"
        )


@app.get("/api/v1/session/{session_id}", response_model=SessionDetailsResponse)
async def get_session_details(session_id: str):
    """
    Get complete session details including chat history, job details, and all state information

    Args:
        session_id: Session ID

    Returns:
        Complete session details
    """
    try:
        # Get or create agent
        agent = get_or_create_agent(session_id)

        # Get conversation summary
        summary = agent.get_conversation_summary()

        # Get chat history from memory
        chat_history = []
        if agent.memory and hasattr(agent.memory, 'chat_memory'):
            for message in agent.memory.chat_memory.messages:
                chat_history.append({
                    "role": "human" if message.type == "human" else "ai",
                    "content": message.content,
                    "timestamp": getattr(message, 'timestamp', datetime.utcnow().isoformat())
                })

        # Prepare state data
        engagement_data = None
        if agent.session_state.engagement:
            engagement_data = agent.session_state.engagement.model_dump()

        qualification_data = None
        if agent.session_state.qualification:
            qualification_data = agent.session_state.qualification.model_dump()

        application_data = None
        if agent.session_state.application:
            application_data = agent.session_state.application.model_dump()

        verification_data = None
        if agent.session_state.verification:
            verification_data = agent.session_state.verification.model_dump()

        # Get job details if available
        job_details = None
        if agent.session_state.engagement and agent.session_state.engagement.job_details:
            job_details = agent.session_state.engagement.job_details

        return SessionDetailsResponse(
            session_id=agent.session_state.session_id,
            current_stage=agent.session_state.current_stage.value,
            created_at=agent.session_state.created_at,
            updated_at=agent.session_state.updated_at,
            engagement=engagement_data,
            qualification=qualification_data,
            application=application_data,
            verification=verification_data,
            chat_history=chat_history,
            job_details=job_details,
            status={
                "engagement_complete": summary["engagement_complete"],
                "qualification_complete": summary["qualification_complete"],
                "application_complete": summary["application_complete"],
                "ready_for_verification": summary["ready_for_verification"],
            }
        )

    except Exception as e:
        logger.error(f"Error getting session details: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get session details: {str(e)}"
        )


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
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete session: {str(e)}"
        )


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
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting session: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to reset session: {str(e)}"
        )


@app.get("/api/v1/session/{session_id}/fit_score")
async def get_fit_score(session_id: str):
    """
    Get fit score for a completed application

    Args:
        session_id: Session ID

    Returns:
        Fit score information and reports if available
    """
    try:
        # Get or create agent
        agent = get_or_create_agent(session_id)

        # Check if application is complete
        if not (
            agent.session_state.application
            and agent.session_state.application.stage_completed
        ):
            raise HTTPException(status_code=400, detail="Application not yet complete")

        # Calculate current fit score
        from chatbot.utils.fit_score import FitScoreCalculator

        # Get chat history
        chat_history = []
        if agent.memory and hasattr(agent.memory, 'chat_memory'):
            for message in agent.memory.chat_memory.messages:
                chat_history.append({
                    "role": "human" if message.type == "human" else "ai",
                    "content": message.content,
                })

        calculator = FitScoreCalculator(llm=agent.llm)

        fit_score = calculator.calculate_fit_score(
            qualification=agent.session_state.qualification,
            application=agent.session_state.application,
            chat_history=chat_history,
            verification=agent.session_state.verification,
        )

        # Try to get generated reports
        import os

        from chatbot.utils.config import settings

        reports_path = {"json_report": None, "pdf_report": None}

        # Check if reports exist
        json_path = os.path.join(settings.REPORTS_DIR, f"{session_id}_report.json")
        pdf_path = os.path.join(settings.REPORTS_DIR, f"{session_id}_report.pdf")

        if os.path.exists(json_path):
            reports_path["json_report"] = json_path
        if os.path.exists(pdf_path):
            reports_path["pdf_report"] = pdf_path

        return {
            "session_id": session_id,
            "fit_score": {
                "total_score": fit_score.total_score,
                "rating": calculator.get_fit_rating(fit_score.total_score),
                "qualification_score": fit_score.qualification_score,
                "experience_score": fit_score.experience_score,
                "personality_score": fit_score.personality_score,
                "breakdown": fit_score.breakdown,
            },
            "reports": reports_path,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting fit score: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get fit score: {str(e)}"
        )


@app.post("/api/v1/session/{session_id}/calculate_fit_score")
async def calculate_fit_score(session_id: str):
    """
    Manually trigger fit score calculation and report generation

    Args:
        session_id: Session ID

    Returns:
        Fit score calculation result
    """
    try:
        # Get or create agent
        agent = get_or_create_agent(session_id)

        # Check if we have minimum required data
        if not agent.session_state.qualification:
            raise HTTPException(
                status_code=400, detail="No qualification data available"
            )

        if not agent.session_state.application:
            raise HTTPException(status_code=400, detail="No application data available")

        # Calculate fit score
        from chatbot.utils.fit_score import FitScoreCalculator
        from chatbot.utils.report_generator import ReportGenerator

        # Get chat history
        chat_history = []
        if agent.memory and hasattr(agent.memory, 'chat_memory'):
            for message in agent.memory.chat_memory.messages:
                chat_history.append({
                    "role": "human" if message.type == "human" else "ai",
                    "content": message.content,
                })

        calculator = FitScoreCalculator(llm=agent.llm)
        fit_score = calculator.calculate_fit_score(
            qualification=agent.session_state.qualification,
            application=agent.session_state.application,
            chat_history=chat_history,
            verification=agent.session_state.verification,
        )

        # Generate reports
        report_gen = ReportGenerator()
        reports = report_gen.generate_report(
            session_id=session_id, include_fit_score=True
        )

        # Update application status if not already complete
        if (
            agent.session_state.application
            and not agent.session_state.application.stage_completed
        ):
            agent.session_state.application.application_status = "submitted"
            agent.session_state.application.stage_completed = True

            # Move to verification stage
            from chatbot.state.states import ConversationStage, VerificationState

            agent.session_state.current_stage = ConversationStage.VERIFICATION

            if not agent.session_state.verification:
                agent.session_state.verification = VerificationState(
                    session_id=session_id
                )

            # Save updated state
            agent.state_manager.save_session(agent.session_state)

        logger.info(
            f"Fit score calculated and reports generated for session {session_id}"
        )

        return {
            "session_id": session_id,
            "fit_score": {
                "total_score": fit_score.total_score,
                "rating": calculator.get_fit_rating(fit_score.total_score),
                "qualification_score": fit_score.qualification_score,
                "experience_score": fit_score.experience_score,
                "personality_score": fit_score.personality_score,
                "breakdown": fit_score.breakdown,
            },
            "reports": reports,
            "stage_updated": True,
            "current_stage": agent.session_state.current_stage.value,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating fit score: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate fit score: {str(e)}"
        )


@app.get("/api/v1/session/{session_id}/application", response_model=ApplicationResponse)
async def get_application(session_id: str):
    """
    Get the completed application data for a session

    Args:
        session_id: Session ID (can be with or without 'application_' prefix)

    Returns:
        Complete application data including applicant info, qualifications, 
        fit score, and job details
    """
    try:
        import json
        import os

        # Normalize session ID - remove 'application_' prefix if present
        normalized_session_id = session_id.replace('application_', '')
        
        # Check if application JSON file exists
        application_file = os.path.join("./applications", f"application_{normalized_session_id}.json")
        
        if not os.path.exists(application_file):
            # Try to get from state manager as fallback
            state_manager = StateManager()
            
            # Load individual states
            engagement = state_manager.load_engagement(normalized_session_id)
            qualification = state_manager.load_qualification(normalized_session_id)
            application = state_manager.load_application(normalized_session_id)
            verification = state_manager.load_verification(normalized_session_id)
            
            # Check if application exists
            if not application:
                raise HTTPException(
                    status_code=404, 
                    detail=f"No application found for session {normalized_session_id}"
                )
            
            # Check if application is complete
            if not application.stage_completed:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Application for session {normalized_session_id} is not yet complete"
                )
            
            # Build application data from state
            application_data = {
                "session_id": normalized_session_id,
                "timestamp": get_current_timestamp(),
                "job": engagement.job_details if engagement else None,
                "applicant": {
                    "name": application.full_name,
                    "phone": application.phone_number,
                    "email": application.email,
                    "address": application.address,
                } if application else None,
                "qualification": qualification.model_dump() if qualification else None,
                "application": application.model_dump() if application else None,
                "verification": verification.model_dump() if verification else None,
                "fit_score": None,  # Fit score is only available in JSON file
                "status": "completed" if application.stage_completed else "in_progress",
            }
            
            return application_data
        
        # Load application from JSON file
        with open(application_file, 'r') as f:
            application_data = json.load(f)
        
        return application_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving application: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve application: {str(e)}"
        )


@app.get("/api/v1/applications", response_model=ApplicationListResponse)
async def list_applications(limit: int = 100, offset: int = 0):
    """
    List all applications
    
    Args:
        limit: Maximum number of applications to return (default: 100)
        offset: Number of applications to skip (default: 0)
    
    Returns:
        List of applications with basic info
    """
    try:
        import json
        import os
        from pathlib import Path
        
        applications_dir = Path("./applications")
        
        if not applications_dir.exists():
            return {
                "applications": [],
                "total_count": 0,
                "limit": limit,
                "offset": offset
            }
        
        # Get all application JSON files
        application_files = list(applications_dir.glob("application_*.json"))
        total_count = len(application_files)
        
        # Sort by modification time (most recent first)
        application_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Apply pagination
        paginated_files = application_files[offset:offset + limit]
        
        applications = []
        for app_file in paginated_files:
            try:
                with open(app_file, 'r') as f:
                    app_data = json.load(f)
                    
                # Extract summary info
                applications.append({
                    "session_id": app_data.get("session_id"),
                    "timestamp": app_data.get("timestamp"),
                    "applicant_name": app_data.get("applicant", {}).get("name"),
                    "applicant_email": app_data.get("applicant", {}).get("email"),
                    "job_title": app_data.get("job", {}).get("title") if app_data.get("job") else None,
                    "company": app_data.get("job", {}).get("company") if app_data.get("job") else None,
                    "status": app_data.get("status", "unknown"),
                    "fit_score": app_data.get("fit_score", {}).get("total_score") if app_data.get("fit_score") else None,
                    "rating": app_data.get("fit_score", {}).get("rating") if app_data.get("fit_score") else None,
                })
            except Exception as e:
                logger.error(f"Error reading application file {app_file}: {e}")
                continue
        
        return {
            "applications": applications,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing applications: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list applications: {str(e)}"
        )


# Document Management Endpoints
@app.post("/api/v1/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),  # "company" or "job"
    company_name: str = Form(default=""),  # Company name
    job_type: str = Form(default="general"),
    section: str = Form(default="general"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Upload a PDF document for the knowledge base

    Args:
        file: PDF file to upload
        document_type: Type of document ("company" or "job")
        company_name: Name of the company (optional)
        job_type: Job category (e.g., "warehouse", "healthcare", "retail")
        section: Document section (e.g., "company_info", "job_requirements", "benefits")

    Returns:
        Document upload response
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Validate document type
        if document_type not in ["company", "job"]:
            raise HTTPException(
                status_code=400, detail="document_type must be 'company' or 'job'"
            )

        # Generate unique document ID
        document_id = str(uuid.uuid4())

        # Create upload directory if it doesn't exist
        upload_dir = Path(settings.UPLOADS_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Save uploaded file
        file_extension = Path(file.filename).suffix
        company_part = f"_{company_name.replace(' ', '_')}" if company_name else ""
        saved_filename = f"{document_id}_{document_type}{company_part}_{job_type}_{section}{file_extension}"
        file_path = upload_dir / saved_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Saved uploaded file: {file_path}")

        # Add background task to process the document
        background_tasks.add_task(
            process_uploaded_document,
            str(file_path),
            document_id,
            file.filename,
            document_type,
            company_name,
            job_type,
            section,
        )

        return DocumentUploadResponse(
            message="Document uploaded successfully and is being processed",
            document_id=document_id,
            filename=file.filename,
            document_type=document_type,
            company_name=company_name,
            job_type=job_type,
            section=section,
            total_chunks=0,  # Will be updated after processing
            total_characters=0,  # Will be updated after processing
            timestamp=datetime.utcnow().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to upload document: {str(e)}"
        )


@app.get("/api/v1/documents", response_model=DocumentListResponse)
async def list_documents():
    """
    List all uploaded documents

    Returns:
        List of uploaded documents with their metadata
    """
    try:
        upload_dir = Path(settings.UPLOADS_DIR)
        documents = []

        if upload_dir.exists():
            for file_path in upload_dir.glob("*.pdf"):
                # Parse filename to extract metadata
                filename_parts = file_path.stem.split("_")
                if len(filename_parts) >= 4:
                    document_id = filename_parts[0]
                    document_type = filename_parts[1]
                    job_type = filename_parts[2]
                    section = "_".join(
                        filename_parts[3:]
                    )  # Handle sections with underscores

                    file_stats = file_path.stat()
                    documents.append(
                        {
                            "document_id": document_id,
                            "filename": file_path.name,
                            "original_filename": file_path.name.replace(
                                f"{document_id}_{document_type}_{job_type}_{section}_",
                                "",
                            ),
                            "document_type": document_type,
                            "job_type": job_type,
                            "section": section,
                            "file_size": file_stats.st_size,
                            "upload_date": datetime.fromtimestamp(
                                file_stats.st_ctime
                            ).isoformat(),
                        }
                    )

        return DocumentListResponse(documents=documents, total_count=len(documents))

    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list documents: {str(e)}"
        )


@app.delete("/api/v1/documents/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(document_id: str):
    """
    Delete an uploaded document

    Args:
        document_id: ID of the document to delete

    Returns:
        Document deletion response
    """
    try:
        upload_dir = Path(settings.UPLOADS_DIR)
        deleted = False

        # Find and delete the file
        for file_path in upload_dir.glob(f"{document_id}_*.pdf"):
            file_path.unlink()
            deleted = True
            logger.info(f"Deleted document: {file_path}")
            break

        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")

        return DocumentDeleteResponse(
            message="Document deleted successfully",
            document_id=document_id,
            deleted=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete document: {str(e)}"
        )


async def process_uploaded_document(
    file_path: str,
    document_id: str,
    original_filename: str,
    document_type: str,
    company_name: str,
    job_type: str,
    section: str,
):
    """
    Background task to process uploaded document
    """
    try:
        # Initialize document ingestion
        ingestion = DocumentIngestion()

        # Process the document
        result = ingestion.ingest_document(
            pdf_path=file_path,
            document_name=f"{document_id}_{original_filename}",
            job_type=job_type,
            section=section,
        )

        logger.info(f"Successfully processed document {document_id}: {result}")

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")


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

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, log_level="info")