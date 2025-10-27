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

# if __name__ == "__main__":
#     # Fetch all jobs
#     all_jobs = get_all_jobs()

#     # Display summary
#     print(f"✅ Total Jobs Found: {len(all_jobs)}\n")

#     # Print each job in full detail
#     for i, job in enumerate(all_jobs, start=1):
#         print(f"🔹 JOB #{i}")
#         print(json.dumps(job, indent=4))
#         print("=" * 80)  # separator line


import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

print(f"🔐 Environment Variables:")
print(f"   LANGFUSE_PUBLIC_KEY: {os.getenv('LANGFUSE_PUBLIC_KEY')[:10] + '...' if os.getenv('LANGFUSE_PUBLIC_KEY') else 'Not found'}")
print(f"   LANGFUSE_SECRET_KEY: {os.getenv('LANGFUSE_SECRET_KEY')[:10] + '...' if os.getenv('LANGFUSE_SECRET_KEY') else 'Not found'}")
print(f"   LANGFUSE_HOST: {os.getenv('LANGFUSE_HOST')}")
print(f"   LANGFUSE_ENABLED: {os.getenv('LANGFUSE_ENABLED')}")

from langfuse.langchain import CallbackHandler

# Create LangFuse handler (it will automatically read from environment variables)
try:
    langfuse_handler = CallbackHandler()
    print("✅ LangFuse CallbackHandler created successfully")
except Exception as e:
    print(f"❌ Failed to create LangFuse handler: {e}")
    langfuse_handler = None

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model_name="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"), temperature=0.7)
prompt = ChatPromptTemplate.from_template("Tell me a joke about {topic}")
chain = prompt | llm
 
print("\n🚀 Testing LangFuse integration...")
if langfuse_handler:
    response = chain.invoke(
        {"topic": "cats"}, 
        config={"callbacks": [langfuse_handler]}
    )
    print("✅ Response received with LangFuse tracking:")
else:
    response = chain.invoke({"topic": "cats"})
    print("✅ Response received without LangFuse:")

print(response.content)