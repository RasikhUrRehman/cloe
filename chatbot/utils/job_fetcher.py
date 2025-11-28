"""
Job Fetcher Utility
Fetches job details from Xano API
"""

from typing import Any, Dict, List, Optional

import requests

from chatbot.utils.utils import setup_logging
from chatbot.utils.xano_client import get_xano_client

logger = setup_logging()

# Xano API URL
API_URL = "https://xoho-w3ng-km3o.n7e.xano.io/api:L-QNLSmb/get_all_job_"


def get_all_jobs() -> List[Dict[str, Any]]:
    """
    Fetch all jobs from the Xano API

    Returns:
        List of job dictionaries
    """
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        jobs = response.json()
        logger.info(f"Successfully fetched {len(jobs)} jobs from API")
        return jobs
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching jobs from API: {e}")
        return []


def get_job_by_id(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a specific job by its ID using the dedicated endpoint

    Args:
        job_id: The unique identifier for the job

    Returns:
        Job dictionary if found, None otherwise
    """
    try:
        # Use the new Xano client to fetch job by ID directly
        xano_client = get_xano_client()
        job = xano_client.get_job_by_id(job_id)
        
        if job:
            return job
        
        # Fallback: Try fetching from all jobs if direct endpoint fails
        logger.info(f"Falling back to get_all_jobs for job_id: {job_id}")
        all_jobs = get_all_jobs()

        # Find the specific job
        for job in all_jobs:
            if str(job.get("id")) == str(job_id):
                logger.info(
                    f"Found job: {job.get('job_title', 'Unknown')} (ID: {job_id})"
                )
                return job

        logger.warning(f"No job found with ID: {job_id}")
        return None

    except Exception as e:
        logger.error(f"Error fetching job by ID {job_id}: {e}")
        return None


def format_job_details(job: Dict[str, Any]) -> str:
    """
    Format job details into a readable string for the agent

    Args:
        job: Job dictionary from API

    Returns:
        Formatted string with job details
    """
    if not job:
        return "No job information available."

    # Extract all available job details
    job_id = job.get("id", "N/A")
    job_title = job.get("job_title", "N/A")
    related_company = job.get("related_company", "N/A")
    description = job.get("description", "N/A")
    job_type = job.get("job_type", "N/A")
    required_experience = job.get("required_experience", "N/A")
    pay_rate = job.get("PayRate", "N/A")
    starting_date = job.get("Starting_Date", "N/A")
    shift = job.get("Shift", "N/A")
    age_16_above = job.get("Age_16_above", False)
    age_18_above = job.get("Age_18_Above", False)
    background_check_req = job.get("Background_check_Req", False)
    id_verification_req = job.get("ID_Verification_req", False)
    uniform_provided = job.get("Uniform_Provided", False)
    perks_benefits = job.get("Perks_Benefits", [])
    expiry_date = job.get("Expiry_Date", "N/A")
    eligibility_criteria = job.get("Eligibility_Criteria", "N/A")
    screening_questions = job.get("Screening_Questions", "N/A")
    related_branch_id = job.get("related_branch_id", "N/A")

    # Format perks/benefits
    if isinstance(perks_benefits, list):
        benefits_str = ", ".join(perks_benefits) if perks_benefits else "None specified"
    else:
        benefits_str = str(perks_benefits)

    # Determine age requirement
    if age_18_above:
        age_req = "18 years or older"
    elif age_16_above:
        age_req = "16 years or older"
    else:
        age_req = "Not specified"

    # Format the job details
    formatted = f"""
=== COMPLETE JOB DETAILS ===

JOB ID: {job_id}
Job Title: {job_title}
Company ID: {related_company}
Branch ID: {related_branch_id}

BASIC INFORMATION:
- Job Type: {job_type}
- Pay Rate: ${pay_rate}/hour
- Starting Date: {starting_date}
- Shift: {shift}
- Application Expiry: {expiry_date}

DESCRIPTION:
{description}

EXPERIENCE & REQUIREMENTS:
- Required Experience: {required_experience} years
- Age Requirement: {age_req}
- Background Check Required: {"Yes" if background_check_req else "No"}
- ID Verification Required: {"Yes" if id_verification_req else "No"}
- Uniform Provided: {"Yes" if uniform_provided else "No"}

PERKS & BENEFITS:
{benefits_str}

ELIGIBILITY CRITERIA:
{eligibility_criteria}

SCREENING QUESTIONS:
{screening_questions}

===========================
"""

    return formatted


def get_job_summary(job: Dict[str, Any]) -> str:
    """
    Get a concise summary of the job for system prompt

    Args:
        job: Job dictionary from API

    Returns:
        Brief job summary
    """
    if not job:
        return "No job information available."

    # Determine age requirement
    age_18_above = job.get("Age_18_Above", False)
    age_16_above = job.get("Age_16_above", False)

    if age_18_above:
        age_req = "18+"
    elif age_16_above:
        age_req = "16+"
    else:
        age_req = "Not specified"

    # Format perks/benefits
    perks_benefits = job.get("Perks_Benefits", [])
    if isinstance(perks_benefits, list):
        benefits_str = ", ".join(perks_benefits) if perks_benefits else "None"
    else:
        benefits_str = str(perks_benefits)

    summary = f"""
JOB OVERVIEW:
- Title: {job.get('job_title', 'N/A')}
- Type: {job.get('job_type', 'N/A')}
- Pay Rate: ${job.get('PayRate', 'N/A')}/hour
- Shift: {job.get('Shift', 'N/A')}
- Starting Date: {job.get('Starting_Date', 'N/A')}
- Required Experience: {job.get('required_experience', 'N/A')} years
- Age Requirement: {age_req}
- Background Check: {"Required" if job.get('Background_check_Req', False) else "Not required"}
- ID Verification: {"Required" if job.get('ID_Verification_req', False) else "Not required"}
- Perks/Benefits: {benefits_str}
- Description: {job.get('description', 'N/A')[:200]}...
"""

    return summary
