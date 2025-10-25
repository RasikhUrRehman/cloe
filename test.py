# import requests
# import json

# API_URL = "https://xoho-w3ng-km3o.n7e.xano.io/api:L-QNLSmb/get_all_job_"

# def get_all_jobs():
#     """
#     Fetch all jobs from the Xano API and return them as a list.
#     """
#     try:
#         response = requests.get(API_URL)
#         response.raise_for_status()
#         return response.json()
#     except requests.exceptions.RequestException as e:
#         print("❌ Error fetching jobs:", e)
#         return []

# def get_job_by_id(jobs, job_id):
#     """
#     Fetch a single job by its unique ID from the given job list.
#     """
#     for job in jobs:
#         if job["id"] == job_id:
#             return job
#     return None

# if __name__ == "__main__":
#     # Fetch all jobs
#     all_jobs = get_all_jobs()

#     # Display summary
#     print(f"✅ Total Jobs Found: {len(all_jobs)}\n")

#     # Print all job IDs
#     print("📋 Job IDs:")
#     for job in all_jobs:
#         print(f"- {job['id']} : {job['job_title']}")

#     # Example: fetch a single job using its unique ID
#     job_id_to_search = "93626fb0-a859-4d0e-afa7-9f4854380e77"
#     selected_job = get_job_by_id(all_jobs, job_id_to_search)

#     if selected_job:
#         print("\n🎯 Job Found:\n")
#         print(json.dumps(selected_job, indent=4))
#     else:
#         print(f"\n⚠️ No job found with ID: {job_id_to_search}")


import requests
import json

API_URL = "https://xoho-w3ng-km3o.n7e.xano.io/api:L-QNLSmb/get_all_job_"

def get_all_jobs():
    """
    Fetch all jobs from the Xano API and return them as a list.
    """
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("❌ Error fetching jobs:", e)
        return []

if __name__ == "__main__":
    # Fetch all jobs
    all_jobs = get_all_jobs()

    # Display summary
    print(f"✅ Total Jobs Found: {len(all_jobs)}\n")

    # Print each job in full detail
    for i, job in enumerate(all_jobs, start=1):
        print(f"🔹 JOB #{i}")
        print(json.dumps(job, indent=4))
        print("=" * 80)  # separator line
