"""
Jobs Routes
Handles all job-related API endpoints
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from chatbot.utils.utils import setup_logging
from chatbot.utils.xano_client import get_xano_client

logger = setup_logging()
router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


# Request/Response Models
class JobCreateRequest(BaseModel):
    """Request model for creating a job"""
    job_title: str = Field(..., description="Job title")
    company: Optional[str] = Field(default=None, description="Company name")
    location: Optional[str] = Field(default=None, description="Job location")
    description: Optional[str] = Field(default=None, description="Job description")
    requirements: Optional[List[str]] = Field(default=None, description="Job requirements")
    salary_range: Optional[str] = Field(default=None, description="Salary range")
    job_type: Optional[str] = Field(default=None, description="Job type (full-time, part-time, etc.)")
    company_id: Optional[str] = Field(default=None, description="Company ID")


class JobUpdateRequest(BaseModel):
    """Request model for updating a job"""
    job_title: Optional[str] = Field(default=None, description="Job title")
    company: Optional[str] = Field(default=None, description="Company name")
    location: Optional[str] = Field(default=None, description="Job location")
    description: Optional[str] = Field(default=None, description="Job description")
    requirements: Optional[List[str]] = Field(default=None, description="Job requirements")
    salary_range: Optional[str] = Field(default=None, description="Salary range")
    job_type: Optional[str] = Field(default=None, description="Job type")
    company_id: Optional[str] = Field(default=None, description="Company ID")


class JobResponse(BaseModel):
    """Response model for job data"""
    id: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    salary_range: Optional[str] = None
    job_type: Optional[str] = None
    company_id: Optional[str] = None
    created_at: Optional[Any] = None  # Can be int (timestamp) or str


@router.get("", response_model=List[JobResponse])
async def list_jobs():
    """
    List all jobs from Xano
    """
    try:
        xano_client = get_xano_client()
        jobs = xano_client.get_jobs()
        if jobs is None:
            return []
        return jobs
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.post("", response_model=JobResponse)
async def create_job(request: JobCreateRequest):
    """
    Create a new job in Xano
    """
    try:
        xano_client = get_xano_client()
        
        job_data = request.model_dump(exclude_none=True)
        job = xano_client.create_job(job_data)
        
        if job:
            logger.info(f"Created job: {job.get('id')}")
            return job
        
        raise HTTPException(status_code=500, detail="Failed to create job in Xano")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """
    Get a specific job by ID
    """
    try:
        xano_client = get_xano_client()
        job = xano_client.get_job_by_id(job_id)
        
        if job:
            return job
        
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job: {str(e)}")


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(job_id: str, request: JobUpdateRequest):
    """
    Update a job in Xano
    """
    try:
        xano_client = get_xano_client()
        
        update_data = request.model_dump(exclude_none=True)
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        job = xano_client.update_job(job_id, update_data)
        
        if job:
            logger.info(f"Updated job: {job_id}")
            return job
        
        raise HTTPException(status_code=500, detail="Failed to update job in Xano")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update job: {str(e)}")


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a job from Xano
    """
    try:
        xano_client = get_xano_client()
        
        if xano_client.delete_job(job_id):
            logger.info(f"Deleted job: {job_id}")
            return {"message": f"Job {job_id} deleted successfully"}
        
        raise HTTPException(status_code=500, detail="Failed to delete job from Xano")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")
