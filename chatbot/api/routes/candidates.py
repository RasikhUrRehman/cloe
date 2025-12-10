"""
Candidates Routes
Handles all candidate-related API endpoints
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from chatbot.utils.utils import setup_logging
from chatbot.utils.xano_client import get_xano_client

logger = setup_logging()
router = APIRouter(prefix="/api/v1/candidates", tags=["Candidates"])


# Request/Response Models
class ApplicationFileModel(BaseModel):
    """Application file attachment model"""
    access: str = "public"
    path: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    size: Optional[int] = None
    mime: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class CandidateCreateRequest(BaseModel):
    """Request model for creating a candidate"""
    Name: str = Field(..., description="Candidate name (required)")
    Email: Optional[str] = Field(default=None, description="Candidate email")
    Phone: Optional[int] = Field(default=None, description="Phone number")
    Score: Optional[float] = Field(default=None, description="Fit score")
    Report_pdf: Optional[str] = Field(default=None, description="PDF report URL")
    job_id: Optional[str] = Field(default=None, description="Associated job ID")
    company_id: Optional[str] = Field(default=None, description="Associated company ID")
    Status: str = Field(default="Short Listed", description="Application status")
    user_id: Optional[int] = Field(default=None, description="User ID")
    session_id: Optional[int] = Field(default=None, description="Session ID")
    Application: Optional[ApplicationFileModel] = Field(default=None, description="Application file")


class CandidateUpdateRequest(BaseModel):
    """Request model for updating a candidate"""
    Name: Optional[str] = Field(default=None, description="Candidate name")
    Email: Optional[str] = Field(default=None, description="Candidate email")
    Phone: Optional[int] = Field(default=None, description="Phone number")
    Score: Optional[float] = Field(default=None, description="Fit score")
    Report_pdf: Optional[str] = Field(default=None, description="PDF report URL")
    job_id: Optional[str] = Field(default=None, description="Associated job ID")
    company_id: Optional[str] = Field(default=None, description="Associated company ID")
    Status: Optional[str] = Field(default=None, description="Application status")
    user_id: Optional[int] = Field(default=None, description="User ID")
    session_id: Optional[int] = Field(default=None, description="Session ID")
    Application: Optional[ApplicationFileModel] = Field(default=None, description="Application file")


class CandidateResponse(BaseModel):
    """Response model for candidate data"""
    id: int
    Name: str
    Email: Optional[str] = None
    Phone: Optional[int] = None
    Score: Optional[float] = None
    Report_pdf: Optional[str] = None
    job_id: Optional[str] = None
    company_id: Optional[str] = None
    Status: Optional[str] = None
    user_id: Optional[int] = None
    session_id: Optional[int] = None
    Application: Optional[Dict[str, Any]] = None
    created_at: Optional[Any] = None  # Can be int (timestamp) or str


@router.get("", response_model=List[CandidateResponse])
async def list_candidates():
    """
    List all candidates from Xano
    """
    try:
        xano_client = get_xano_client()
        candidates = xano_client.get_candidates()
        if candidates is None:
            return []
        return candidates
    except Exception as e:
        logger.error(f"Error listing candidates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list candidates: {str(e)}")


@router.post("", response_model=CandidateResponse)
async def create_candidate(request: CandidateCreateRequest):
    """
    Create a new candidate in Xano
    """
    try:
        xano_client = get_xano_client()
        
        # Prepare application data if provided
        application_data = None
        if request.Application:
            application_data = request.Application.model_dump()
        
        candidate = xano_client.create_candidate(
            name=request.Name,
            email=request.Email,
            phone=request.Phone,
            score=request.Score,
            report_pdf=request.Report_pdf,
            job_id=request.job_id,
            company_id=request.company_id,
            status=request.Status,
            user_id=request.user_id,
            session_id=request.session_id,
            application=application_data,
        )
        
        if candidate:
            logger.info(f"Created candidate: {candidate.get('id')}")
            return candidate
        
        raise HTTPException(status_code=500, detail="Failed to create candidate in Xano")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating candidate: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create candidate: {str(e)}")


@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(candidate_id: int):
    """
    Get a specific candidate by ID
    """
    try:
        xano_client = get_xano_client()
        candidate = xano_client.get_candidate_by_id(candidate_id)
        
        if candidate:
            return candidate
        
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting candidate: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get candidate: {str(e)}")


@router.patch("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(candidate_id: int, request: CandidateUpdateRequest):
    """
    Update a candidate in Xano
    """
    try:
        xano_client = get_xano_client()
        
        # Build update data from non-None fields
        update_data = {}
        if request.Name is not None:
            update_data["Name"] = request.Name
        if request.Email is not None:
            update_data["Email"] = request.Email
        if request.Phone is not None:
            update_data["Phone"] = request.Phone
        if request.Score is not None:
            update_data["Score"] = request.Score
        if request.Report_pdf is not None:
            update_data["Report_pdf"] = request.Report_pdf
        if request.job_id is not None:
            update_data["job_id"] = request.job_id
        if request.company_id is not None:
            update_data["company_id"] = request.company_id
        if request.Status is not None:
            update_data["Status"] = request.Status
        if request.user_id is not None:
            update_data["user_id"] = request.user_id
        if request.session_id is not None:
            update_data["session_id"] = request.session_id
        if request.Application is not None:
            update_data["Application"] = request.Application.model_dump()
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        candidate = xano_client.update_candidate(candidate_id, update_data)
        
        if candidate:
            logger.info(f"Updated candidate: {candidate_id}")
            return candidate
        
        raise HTTPException(status_code=500, detail="Failed to update candidate in Xano")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating candidate: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update candidate: {str(e)}")


@router.delete("/{candidate_id}")
async def delete_candidate(candidate_id: int):
    """
    Delete a candidate from Xano
    """
    try:
        xano_client = get_xano_client()
        
        if xano_client.delete_candidate(candidate_id):
            logger.info(f"Deleted candidate: {candidate_id}")
            return {"message": f"Candidate {candidate_id} deleted successfully"}
        
        raise HTTPException(status_code=500, detail="Failed to delete candidate from Xano")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting candidate: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete candidate: {str(e)}")
