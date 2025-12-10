"""
Companies Routes
Handles all company-related API endpoints
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from chatbot.utils.utils import setup_logging
from chatbot.utils.xano_client import get_xano_client

logger = setup_logging()
router = APIRouter(prefix="/api/v1/companies", tags=["Companies"])


# Request/Response Models
class CompanyCreateRequest(BaseModel):
    """Request model for creating a company"""
    company_name: str = Field(..., description="Company name (required)")
    description: Optional[str] = Field(default=None, description="Company description")
    website: Optional[str] = Field(default=None, description="Company website URL")
    industry: Optional[str] = Field(default=None, description="Industry type")
    logo: Optional[str] = Field(default=None, description="Logo URL")
    related_user: Optional[int] = Field(default=None, description="Related user ID")
    Verified: bool = Field(default=False, description="Whether company is verified")
    Company_Docs: Optional[List[str]] = Field(default=None, description="List of document URLs")


class CompanyUpdateRequest(BaseModel):
    """Request model for updating a company"""
    company_name: Optional[str] = Field(default=None, description="Company name")
    description: Optional[str] = Field(default=None, description="Company description")
    website: Optional[str] = Field(default=None, description="Company website URL")
    industry: Optional[str] = Field(default=None, description="Industry type")
    logo: Optional[str] = Field(default=None, description="Logo URL")
    related_user: Optional[int] = Field(default=None, description="Related user ID")
    Verified: Optional[bool] = Field(default=None, description="Whether company is verified")
    Company_Docs: Optional[List[str]] = Field(default=None, description="List of document URLs")


class CompanyResponse(BaseModel):
    """Response model for company data"""
    id: Optional[str] = None
    company_name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    logo: Optional[str] = None
    related_user: Optional[int] = None
    Verified: Optional[bool] = None
    Company_Docs: Optional[List[str]] = None
    created_at: Optional[Any] = None  # Can be int (timestamp) or str


@router.get("", response_model=List[CompanyResponse])
async def list_companies():
    """
    List all companies from Xano
    """
    try:
        xano_client = get_xano_client()
        companies = xano_client.get_companies()
        if companies is None:
            return []
        return companies
    except Exception as e:
        logger.error(f"Error listing companies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list companies: {str(e)}")


@router.post("", response_model=CompanyResponse)
async def create_company(request: CompanyCreateRequest):
    """
    Create a new company in Xano
    """
    try:
        xano_client = get_xano_client()
        
        company = xano_client.create_company(
            company_name=request.company_name,
            description=request.description,
            website=request.website,
            industry=request.industry,
            logo=request.logo,
            related_user=request.related_user,
            verified=request.Verified,
            company_docs=request.Company_Docs,
        )
        
        if company:
            logger.info(f"Created company: {company.get('id')}")
            return company
        
        raise HTTPException(status_code=500, detail="Failed to create company in Xano")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating company: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create company: {str(e)}")


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: str):
    """
    Get a specific company by ID
    """
    try:
        xano_client = get_xano_client()
        company = xano_client.get_company_by_id(company_id)
        
        if company:
            return company
        
        raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get company: {str(e)}")


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(company_id: str, request: CompanyUpdateRequest):
    """
    Update a company in Xano
    """
    try:
        xano_client = get_xano_client()
        
        update_data = request.model_dump(exclude_none=True)
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        company = xano_client.update_company(company_id, update_data)
        
        if company:
            logger.info(f"Updated company: {company_id}")
            return company
        
        raise HTTPException(status_code=500, detail="Failed to update company in Xano")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating company: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update company: {str(e)}")


@router.delete("/{company_id}")
async def delete_company(company_id: str):
    """
    Delete a company from Xano
    """
    try:
        xano_client = get_xano_client()
        
        if xano_client.delete_company(company_id):
            logger.info(f"Deleted company: {company_id}")
            return {"message": f"Company {company_id} deleted successfully"}
        
        raise HTTPException(status_code=500, detail="Failed to delete company from Xano")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting company: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete company: {str(e)}")
