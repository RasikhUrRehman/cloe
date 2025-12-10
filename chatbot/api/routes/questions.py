"""
Questions Routes
Handles AI-generated interview questions from job descriptions
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from chatbot.utils.utils import setup_logging
from chatbot.utils.config import settings

logger = setup_logging()
router = APIRouter(prefix="/api/v1/questions", tags=["Questions"])


# Request/Response Models
class GenerateQuestionsRequest(BaseModel):
    """Request model for generating interview questions"""
    job_description: str = Field(..., description="The job description to generate questions from")
    num_questions: Optional[int] = Field(default=10, ge=1, le=20, description="Number of questions to generate (1-20)")
    question_types: Optional[List[str]] = Field(
        default=None,
        description="Types of questions to generate (e.g., 'technical', 'behavioral', 'situational', 'experience')"
    )
    difficulty_level: Optional[str] = Field(
        default="mixed",
        description="Difficulty level: 'easy', 'medium', 'hard', or 'mixed'"
    )


class Question(BaseModel):
    """Model for a single interview question"""
    question: str = Field(..., description="The interview question")
    type: str = Field(..., description="Type of question (technical, behavioral, situational, experience)")
    purpose: str = Field(..., description="What this question aims to assess")


class GenerateQuestionsResponse(BaseModel):
    """Response model for generated questions"""
    questions: List[Question]
    job_title: Optional[str] = None
    total_questions: int


# Prompt template for generating questions
QUESTION_GENERATION_PROMPT = """You are an expert HR interviewer and recruitment specialist. Your task is to generate thoughtful, relevant interview questions based on the provided job description.

JOB DESCRIPTION:
{job_description}

REQUIREMENTS:
- Generate exactly {num_questions} interview questions
- Question types to focus on: {question_types}
- Difficulty level: {difficulty_level}

GUIDELINES:
1. Technical Questions: Test specific skills, tools, and knowledge mentioned in the job description
2. Behavioral Questions: Use the STAR method format (Situation, Task, Action, Result) - start with "Tell me about a time..." or "Describe a situation..."
3. Situational Questions: Present hypothetical scenarios relevant to the role - start with "What would you do if..." or "How would you handle..."
4. Experience Questions: Probe into relevant past experience and qualifications

IMPORTANT:
- Make questions specific to the role and requirements mentioned
- Avoid generic questions that could apply to any job
- Ensure questions are open-ended to encourage detailed responses
- Questions should help assess candidate fit for this specific position

Return the questions in the following JSON format:
{{
    "job_title": "extracted or inferred job title from the description",
    "questions": [
        {{
            "question": "The interview question text",
            "type": "technical|behavioral|situational|experience",
            "purpose": "Brief description of what this question assesses"
        }}
    ]
}}

Generate the questions now:"""


@router.post("", response_model=GenerateQuestionsResponse)
async def generate_questions(request: GenerateQuestionsRequest):
    """
    Generate interview questions from a job description using AI.
    
    This endpoint takes a job description and generates relevant interview
    questions that can be used to assess candidates for the position.
    """
    try:
        # Initialize the LLM
        llm = ChatOpenAI(
            model=settings.OPENAI_CHAT_MODEL,
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        
        # Prepare question types
        question_types = request.question_types or ["technical", "behavioral", "situational", "experience"]
        question_types_str = ", ".join(question_types)
        
        # Create the prompt
        prompt = ChatPromptTemplate.from_template(QUESTION_GENERATION_PROMPT)
        
        # Format the prompt with the request data
        formatted_prompt = prompt.format(
            job_description=request.job_description,
            num_questions=request.num_questions,
            question_types=question_types_str,
            difficulty_level=request.difficulty_level
        )
        
        # Get the response from the LLM
        response = await llm.ainvoke(formatted_prompt)
        
        # Parse the response
        import json
        response_text = response.content
        
        # Try to extract JSON from the response
        try:
            # Find JSON in the response (it might be wrapped in markdown code blocks)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            parsed_response = json.loads(response_text)
            
            # Build the response
            questions = [
                Question(
                    question=q["question"],
                    type=q["type"],
                    purpose=q["purpose"]
                )
                for q in parsed_response.get("questions", [])
            ]
            
            logger.info(f"Generated {len(questions)} interview questions")
            
            return GenerateQuestionsResponse(
                questions=questions,
                job_title=parsed_response.get("job_title"),
                total_questions=len(questions)
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response was: {response_text}")
            raise HTTPException(
                status_code=500,
                detail="Failed to parse AI response. Please try again."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")


@router.post("/from-job/{job_id}", response_model=GenerateQuestionsResponse)
async def generate_questions_from_job(
    job_id: str,
    num_questions: Optional[int] = 10,
    question_types: Optional[List[str]] = None,
    difficulty_level: Optional[str] = "mixed"
):
    """
    Generate interview questions from an existing job by its ID.
    
    This endpoint fetches the job description from the database and generates
    relevant interview questions for that position.
    """
    try:
        from chatbot.utils.xano_client import get_xano_client
        
        # Fetch the job from Xano
        xano_client = get_xano_client()
        job = xano_client.get_job_by_id(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        # Build job description from job data
        job_description_parts = []
        
        if job.get("job_title"):
            job_description_parts.append(f"Job Title: {job['job_title']}")
        
        if job.get("company"):
            job_description_parts.append(f"Company: {job['company']}")
        
        if job.get("location"):
            job_description_parts.append(f"Location: {job['location']}")
        
        if job.get("job_type"):
            job_description_parts.append(f"Job Type: {job['job_type']}")
        
        if job.get("description"):
            job_description_parts.append(f"\nDescription:\n{job['description']}")
        
        if job.get("requirements"):
            requirements = job["requirements"]
            if isinstance(requirements, list):
                requirements = "\n- ".join(requirements)
            job_description_parts.append(f"\nRequirements:\n- {requirements}")
        
        if job.get("salary_range"):
            job_description_parts.append(f"\nSalary Range: {job['salary_range']}")
        
        job_description = "\n".join(job_description_parts)
        
        if not job_description.strip():
            raise HTTPException(
                status_code=400,
                detail="Job has no description or details to generate questions from"
            )
        
        # Use the main generate_questions endpoint logic
        request = GenerateQuestionsRequest(
            job_description=job_description,
            num_questions=num_questions,
            question_types=question_types,
            difficulty_level=difficulty_level
        )
        
        return await generate_questions(request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating questions from job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")
