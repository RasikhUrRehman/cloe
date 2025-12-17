"""
Jobs Routes
Handles job-related API endpoints
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from chatbot.utils.utils import setup_logging
from chatbot.utils.xano_client import get_xano_client

logger = setup_logging()
router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


# Response Models
class JobResponse(BaseModel):
    """Response model for job data"""
    id: int
    job_title: Optional[str] = None
    job_description: Optional[str] = None
    job_location: Optional[str] = None
    job_type: Optional[str] = None
    salary_range: Optional[str] = None
    company_name: Optional[str] = None
    company_id: Optional[int] = None
    requirements: Optional[Any] = None
    responsibilities: Optional[Any] = None
    benefits: Optional[Any] = None
    application_deadline: Optional[str] = None
    posted_date: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[int] = None
    
    class Config:
        extra = "allow"  # Allow additional fields from Xano


class JobListResponse(BaseModel):
    """Response model for job list"""
    jobs: List[JobResponse]
    total: int


@router.get("", response_model=JobListResponse)
async def get_all_jobs():
    """
    Get all available jobs from Xano database
    
    Returns:
        List of all jobs
    """
    try:
        xano_client = get_xano_client()
        jobs = xano_client.get_jobs()
        
        if jobs is None:
            logger.error("Failed to fetch jobs from Xano")
            raise HTTPException(status_code=500, detail="Failed to fetch jobs from database")
        
        return JobListResponse(jobs=jobs, total=len(jobs))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_all_jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_by_id(job_id: str):
    """
    Get detailed information for a specific job by ID
    
    Args:
        job_id: The unique identifier for the job
        
    Returns:
        Detailed job information
    """
    try:
        xano_client = get_xano_client()
        job = xano_client.get_job_by_id(job_id)
        
        if job is None:
            logger.warning(f"Job not found with ID: {job_id}")
            raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
        
        return JobResponse(**job)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_job_by_id: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
