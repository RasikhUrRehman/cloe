"""
List Available Jobs
Helper script to see all available jobs and their IDs
"""
import requests
import json

API_URL = "https://xoho-w3ng-km3o.n7e.xano.io/api:L-QNLSmb/get_all_job_"

def list_all_jobs():
    """
    Fetch and display all available jobs
    """
    try:
        print("Fetching jobs from API...")
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        jobs = response.json()
        
        print(f"\n✅ Total Jobs Found: {len(jobs)}\n")
        print("=" * 100)
        
        for i, job in enumerate(jobs, start=1):
            job_id = job.get('id', 'N/A')
            job_title = job.get('job_title', 'N/A')
            company = job.get('company_name', 'N/A')
            location = job.get('location', 'N/A')
            job_type = job.get('job_type', 'N/A')
            
            print(f"\n🔹 JOB #{i}")
            print(f"   ID: {job_id}")
            print(f"   Title: {job_title}")
            print(f"   Company: {company}")
            print(f"   Location: {location}")
            print(f"   Type: {job_type}")
            print("-" * 100)
        
        return jobs
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching jobs: {e}")
        return []


def get_job_details(job_id: str):
    """
    Get detailed information about a specific job
    
    Args:
        job_id: The job ID to fetch
    """
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        jobs = response.json()
        
        for job in jobs:
            if str(job.get('id')) == str(job_id):
                print(f"\n📋 JOB DETAILS - {job.get('job_title', 'N/A')}")
                print("=" * 100)
                print(json.dumps(job, indent=2))
                print("=" * 100)
                return job
        
        print(f"⚠️ No job found with ID: {job_id}")
        return None
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching job details: {e}")
        return None


def main():
    """
    Main function
    """
    print("=" * 100)
    print("Available Jobs Listing")
    print("=" * 100)
    
    # List all jobs
    jobs = list_all_jobs()
    
    if not jobs:
        print("\nNo jobs available or error occurred.")
        return
    
    # Ask if user wants to see details of a specific job
    print("\n" + "=" * 100)
    job_id = input("\nEnter Job ID to see full details (or press Enter to skip): ").strip()
    
    if job_id:
        get_job_details(job_id)


if __name__ == "__main__":
    main()
