"""
FastAPI Application for Cleo RAG Agent
Provides REST API endpoints for chat interactions
"""
import os
from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from chatbot.core.agent import CleoRAGAgent
from chatbot.utils.config import ensure_directories, settings
from chatbot.utils.utils import setup_logging
from chatbot.utils.session_manager import get_session_manager

# Import modular routes
from chatbot.api.routes import (
    chat_router,
    sessions_router,
    candidates_router,
    jobs_router,
    companies_router,
    messages_router,
    applications_router,
    questions_router,
)

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

# Initialize the session manager (singleton pattern, no globals needed)
session_manager = get_session_manager()
logger.info("Session manager initialized")

# Include routers
app.include_router(chat_router)
app.include_router(sessions_router)
app.include_router(candidates_router)
app.include_router(jobs_router)
app.include_router(companies_router)
app.include_router(messages_router)
app.include_router(applications_router)
app.include_router(questions_router)


# Health check models
class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    version: str
    timestamp: str


@app.get("/", response_model=HealthResponse)
@app.head("/")
def read_root() -> HealthResponse:
    """Health endpoint that supports GET and HEAD on root path"""
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow().isoformat(),
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
    )


# Serve web UI
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "web")

@app.get("/ui")
async def serve_ui():
    """Serve the web UI"""
    return FileResponse(os.path.join(WEB_DIR, "index.html"))


# Mount static files for web UI (CSS, JS)
if os.path.exists(WEB_DIR):
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


# Startup and Shutdown Events
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("Cleo RAG Agent API starting up...")
    logger.info(f"Using OpenAI model: {settings.OPENAI_CHAT_MODEL}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Cleo RAG Agent API shutting down...")
    logger.info(f"Active sessions at shutdown: {len(session_manager.sessions)}")
