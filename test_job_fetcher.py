"""
Test Job Fetcher with Real API Data
Shows how the formatted job details will appear to the agent
"""
from chatbot.utils.job_fetcher import get_all_jobs, get_job_by_id, format_job_details, get_job_summary

def test_job_fetcher():
    """Test the job fetcher functions"""
    
    print("=" * 100)
    print("TESTING JOB FETCHER")
    print("=" * 100)
    
    # Test 1: Fetch all jobs
    print("\n📋 TEST 1: Fetching all jobs...")
    all_jobs = get_all_jobs()
    
    if not all_jobs:
        print("❌ No jobs found or error occurred")
        return
    
    print(f"✅ Found {len(all_jobs)} jobs")
    
    # Show brief list
    print("\nAvailable Jobs:")
    for i, job in enumerate(all_jobs, 1):
        print(f"{i}. {job.get('job_title', 'N/A')} - ${job.get('PayRate', 'N/A')}/hr - {job.get('job_type', 'N/A')}")
    
    # Test 2: Get specific job
    if all_jobs:
        print("\n" + "=" * 100)
        print("📋 TEST 2: Getting specific job details...")
        first_job_id = all_jobs[0].get('id')
        print(f"Fetching job ID: {first_job_id}")
        
        job = get_job_by_id(first_job_id)
        
        if job:
            print("✅ Job found!")
            
            # Test 3: Format job details (what the agent sees)
            print("\n" + "=" * 100)
            print("📋 TEST 3: Formatted Job Details (Agent's View)...")
            formatted = format_job_details(job)
            print(formatted)
            
            # Test 4: Job summary
            print("\n" + "=" * 100)
            print("📋 TEST 4: Job Summary (Concise View)...")
            summary = get_job_summary(job)
            print(summary)
            
        else:
            print("❌ Job not found")
    
    # Test 5: Show all job details in full
    print("\n" + "=" * 100)
    print("📋 TEST 5: Complete Details for First 2 Jobs...")
    
    for i, job in enumerate(all_jobs[:2], 1):
        print(f"\n{'=' * 100}")
        print(f"JOB #{i}")
        print(format_job_details(job))
    
    print("\n" + "=" * 100)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 100)


if __name__ == "__main__":
    test_job_fetcher()
