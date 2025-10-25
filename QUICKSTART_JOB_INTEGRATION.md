# Quick Start Guide: Job-Specific Sessions

## What Changed?

Your Cleo chatbot now supports **job-specific sessions**! When creating a session, you can pass a `job_id`, and the system will:

✅ Fetch job details from Xano API  
✅ Store job info in session state  
✅ Give the agent full knowledge of the job  
✅ Guide the agent to assess applicant fit  

## How to Use

### Step 1: Find a Job ID

Run this to see all available jobs:
```bash
python list_jobs.py
```

Copy a job ID from the output (looks like: `93626fb0-a859-4d0e-afa7-9f4854380e77`)

### Step 2: Start the API

```bash
docker-compose up --build -d
```

Or:
```bash
python run_api.py
```

### Step 3: Create a Session with a Job

**Option A - Interactive Demo:**
```bash
python api_client_example_with_job.py
```

**Option B - API Request:**
```bash
curl -X POST http://localhost:8000/api/v1/session/create \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "YOUR-JOB-ID-HERE",
    "retrieval_method": "hybrid",
    "language": "en"
  }'
```

**Option C - Python Code:**
```python
import requests

response = requests.post("http://localhost:8000/api/v1/session/create", json={
    "job_id": "93626fb0-a859-4d0e-afa7-9f4854380e77",  # Your job ID
    "retrieval_method": "hybrid",
    "language": "en"
})

session = response.json()
session_id = session['session_id']
```

### Step 4: Chat!

The agent now knows everything about the job and will:
- Ask relevant questions based on job requirements
- Assess your fit for the position
- Give honest feedback about your match

## Files Modified

1. **`chatbot/utils/job_fetcher.py`** (NEW) - Fetches jobs from Xano API
2. **`chatbot/state/states.py`** - Added `job_details` to EngagementState
3. **`chatbot/api/app.py`** - Added `job_id` parameter to session creation
4. **`chatbot/core/agent.py`** - Passes job context to prompts
5. **`chatbot/prompts/prompts.py`** - Updated prompts with job-aware instructions

## Helper Scripts

- **`list_jobs.py`** - See all available jobs and their IDs
- **`api_client_example_with_job.py`** - Interactive demo with job-specific session

## Key Features

### Agent Behavior:
- ✅ Knows full job details (title, requirements, responsibilities, etc.)
- ✅ Doesn't overwhelm applicant with all info upfront
- ✅ Asks targeted questions based on job requirements
- ✅ Collects applicant info through natural conversation
- ✅ Compares applicant to job requirements
- ✅ Calculates and communicates fit score

### Fit Score Assessment:
After collecting info, agent evaluates:
- Skills match (do they have required skills?)
- Experience match (right level of experience?)
- Availability match (can they work the schedule?)
- Location match (are they in the right place?)

## Example Conversation

```
YOU: Hi
CLEO: Hi there! 👋 I'm Cleo. I'm here to help you apply for the 
      Software Engineer position at Tech Corp...

YOU: What does this job involve?
CLEO: This is a full-time position focused on backend development. 
      You'll be working with Python and databases. The role requires 
      3+ years of experience. Ready to get started?

YOU: Yes
CLEO: Great! First, are you at least 18 years old?

YOU: Yes, I'm 25
CLEO: Perfect! And are you legally authorized to work in the US?

[Conversation continues...]

CLEO: Based on everything you've shared, I think you'd be an excellent 
      fit for this position! Your 5 years of Python experience and your 
      work with PostgreSQL align perfectly with what we're looking for...
```

## Testing

1. Start API: `docker-compose up --build -d`
2. List jobs: `python list_jobs.py`
3. Test session: `python api_client_example_with_job.py`

That's it! Your chatbot now provides personalized, job-specific application experiences! 🎉
