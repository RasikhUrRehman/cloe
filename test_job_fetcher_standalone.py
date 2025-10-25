"""
Standalone Test Job Fetcher
Tests job fetching without importing the full chatbot module
"""
import requests
import json
from typing import Dict, Any, List, Optional

# Xano API URL
API_URL = "https://xoho-w3ng-km3o.n7e.xano.io/api:L-QNLSmb/get_all_job_"


def get_all_jobs() -> List[Dict[str, Any]]:
    """Fetch all jobs from the Xano API"""
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        jobs = response.json()
        print(f"✅ Successfully fetched {len(jobs)} jobs from API")
        return jobs
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching jobs from API: {e}")
        return []


def format_job_details(job: Dict[str, Any]) -> str:
    """Format job details into a readable string"""
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


def main():
    """Main test function"""
    print("=" * 100)
    print("JOB FETCHER TEST - SHOWING ALL JOB DETAILS")
    print("=" * 100)
    
    # Fetch all jobs
    all_jobs = get_all_jobs()
    
    if not all_jobs:
        print("\n❌ No jobs available or error occurred")
        return
    
    # Show brief list
    print(f"\n📋 Total Jobs Found: {len(all_jobs)}\n")
    print("Quick List:")
    for i, job in enumerate(all_jobs, 1):
        print(f"{i}. {job.get('job_title', 'N/A')} - ${job.get('PayRate', 'N/A')}/hr - {job.get('job_type', 'N/A')} - {job.get('Shift', 'N/A')} shift")
    
    # Show complete details for all jobs
    print("\n" + "=" * 100)
    print("COMPLETE DETAILS FOR ALL JOBS")
    print("=" * 100)
    
    for i, job in enumerate(all_jobs, 1):
        print(f"\n🔹 JOB #{i}")
        print(format_job_details(job))
        print("=" * 100)
    
    print("\n✅ Test completed!")


if __name__ == "__main__":
    main()
