"""
API Routes Package
Contains modular route definitions for the Cleo RAG Agent API
"""

from chatbot.api.routes.chat import router as chat_router
from chatbot.api.routes.sessions import router as sessions_router
from chatbot.api.routes.candidates import router as candidates_router
from chatbot.api.routes.jobs import router as jobs_router
from chatbot.api.routes.companies import router as companies_router
from chatbot.api.routes.messages import router as messages_router
from chatbot.api.routes.applications import router as applications_router

__all__ = [
    "chat_router",
    "sessions_router",
    "candidates_router",
    "jobs_router",
    "companies_router",
    "messages_router",
    "applications_router",
]
