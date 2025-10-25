# Job-Specific Session Integration

## Overview

This update integrates job-specific information into the Cleo chatbot system. When creating a session, you can now specify a `job_id`, and the system will:

1. Fetch the job details from the Xano API
2. Store the job information in the session state
3. Pass the job details to the agent's system prompt
4. Guide the agent to assess applicant fit based on the specific job requirements

## Key Changes

### 1. New Job Fetcher Utility (`chatbot/utils/job_fetcher.py`)

This module provides functions to:
- Fetch all jobs from the Xano API
- Get a specific job by ID
- Format job details for the agent

**Functions:**
- `get_all_jobs()` - Fetch all available jobs
- `get_job_by_id(job_id)` - Get a specific job by ID
- `format_job_details(job)` - Format job info for system prompt
- `get_job_summary(job)` - Get concise job summary

### 2. Updated Session State (`chatbot/state/states.py`)

The `EngagementState` model now includes:
- `job_id`: The ID of the job being applied for
- `job_details`: Full job information from the API

### 3. Enhanced API Endpoint (`chatbot/api/app.py`)

**Session Creation:**
```python
POST /api/v1/session/create
{
    "job_id": "uuid-of-job",  // NEW: Optional job ID
    "retrieval_method": "hybrid",
    "language": "en"
}
```

The endpoint now:
- Accepts a `job_id` parameter
- Fetches job details from Xano API
- Stores job information in session state
- Refreshes agent with job context

### 4. Updated Agent (`chatbot/core/agent.py`)

The agent now:
- Includes job context in system prompt
- Has a `_refresh_agent_with_job_context()` method
- Passes job details to the prompt generator

### 5. Enhanced Prompts (`chatbot/prompts/prompts.py`)

**Updated System Prompt:**
- Includes full job details when available
- Instructs agent NOT to reveal all job info upfront
- Guides agent to collect applicant info first
- Enables fit score calculation

**Key Instructions for Agent:**
- Collect applicant information through natural conversation
- Use job requirements to guide qualification questions
- Compare applicant profile to job requirements
- Calculate and communicate fit score
- Be honest but encouraging about fit

### 6. New Helper Scripts

**`list_jobs.py`** - List all available jobs with their IDs
```bash
python list_jobs.py
```

**`api_client_example_with_job.py`** - Interactive demo with job-specific session
```bash
python api_client_example_with_job.py
```

## Usage

### 1. List Available Jobs

First, see what jobs are available:

```bash
python list_jobs.py
```

This will show all jobs with their IDs, titles, and basic info.

### 2. Create a Session with a Job

**Via API:**
```python
import requests

response = requests.post("http://localhost:8000/api/v1/session/create", json={
    "job_id": "93626fb0-a859-4d0e-afa7-9f4854380e77",
    "retrieval_method": "hybrid",
    "language": "en"
})

session = response.json()
print(f"Session ID: {session['session_id']}")
```

**Via Example Script:**
```bash
python api_client_example_with_job.py
```

### 3. Chat with the Agent

The agent will now:
1. Know all details about the specific job
2. Guide the conversation through engagement, qualification, and application stages
3. Ask targeted questions based on job requirements
4. Assess the applicant's fit for the position
5. Provide honest feedback about their match

## Agent Behavior

### What the Agent Knows:
- Complete job details (title, description, requirements, responsibilities, benefits, etc.)
- All job requirements and qualifications
- Company information
- Salary range and job type

### How the Agent Uses This Information:

**During Engagement:**
- Can answer questions about the job
- Doesn't overwhelm applicant with all details

**During Qualification:**
- Asks targeted questions based on job requirements
- Verifies eligibility for this specific position
- Checks availability matches job schedule

**During Application:**
- Collects information relevant to the job
- Focuses on skills and experience needed for the role
- Assesses fit throughout the conversation

**Fit Score Calculation:**
After collecting applicant information, the agent assesses:
- Skills match (0-100%)
- Experience match (0-100%)
- Availability match (0-100%)
- Location match (0-100%)
- Overall fit score

The agent communicates this naturally:
- "Based on your background, you'd be a great fit for this position!"
- "Your Python skills align perfectly with what we're looking for."
- "While you have great experience, this role specifically needs [X]..."

## Example Flow

```
User: Hi
Agent: Hi there! 👋 I'm Cleo, your AI assistant. I'm here to help you through 
       the application process for [Job Title] at [Company]...

User: What's this job about?
Agent: This is a [Job Type] position where you'll be [brief description]. 
       The role focuses on [key responsibilities]. Would you like to learn 
       more before we get started?

User: Sure, let's start
Agent: Great! Let's begin with a few quick questions to make sure you meet 
       the basic requirements for this position...

[Conversation continues through qualification and application stages]

Agent: Based on everything you've shared, I think you'd be an excellent fit 
       for this position! Your experience with [X] and skills in [Y] align 
       perfectly with what we're looking for...
```

## Testing

### 1. Start the API
```bash
docker-compose up --build -d
# OR
python run_api.py
```

### 2. List Jobs
```bash
python list_jobs.py
```

### 3. Test with Interactive Client
```bash
python api_client_example_with_job.py
```

Enter a job ID when prompted (or use the demo ID), then chat with Cleo!

### 4. Test via cURL
```bash
# Create session with job
curl -X POST http://localhost:8000/api/v1/session/create \
  -H "Content-Type: application/json" \
  -d '{"job_id": "YOUR-JOB-ID-HERE"}'

# Chat
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "SESSION-ID", "message": "Hi"}'
```

## Architecture

```
User Request (job_id)
    ↓
API Endpoint (/api/v1/session/create)
    ↓
Job Fetcher (get_job_by_id)
    ↓
Xano API (fetch job details)
    ↓
Session State (store job_details)
    ↓
Agent (with job context in system prompt)
    ↓
Conversation (job-aware interaction)
```

## Benefits

1. **Personalized Experience**: Each session is tailored to the specific job
2. **Targeted Questions**: Agent asks relevant questions based on job requirements
3. **Better Assessment**: Agent can accurately assess fit for the role
4. **Honest Feedback**: Applicants get clear feedback about their match
5. **Efficient Process**: No generic applications - everything is job-specific

## Future Enhancements

- [ ] Multi-job applications (compare fit across multiple jobs)
- [ ] Job recommendations based on applicant profile
- [ ] Automated fit score storage and ranking
- [ ] Integration with ATS (Applicant Tracking System)
- [ ] Skills gap analysis and recommendations
