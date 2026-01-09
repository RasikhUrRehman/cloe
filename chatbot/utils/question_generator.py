"""
Question Generator Utility
Generates interview questions from job details using AI
"""
import json
from typing import Dict, Any, List, Optional

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from chatbot.utils.utils import setup_logging
from chatbot.utils.config import settings
from chatbot.utils.xano_client import get_xano_client

logger = setup_logging()


# Prompt template for generating questions from job details
QUESTION_GENERATION_PROMPT = """You are an expert HR interviewer and recruitment specialist. Your task is to generate thoughtful, relevant interview questions based on the provided job description.

JOB DESCRIPTION:
{job_description}

REQUIREMENTS:
- Generate exactly {num_questions} interview questions
- Question types to focus on: {question_types}
- Difficulty level: {difficulty_level}

MANDATORY EXPERIENCE QUESTIONS (MUST INCLUDE):
You MUST include these specific questions to capture structured experience data:
1. "How many years of relevant work experience do you have?" (type: experience)
2. "What was your job title or role in your most recent position?" (type: experience)
3. "Which company or organization were you previously employed with?" (type: experience)
4. "What key skills or tools have you worked with in your professional experience?" (type: experience)

GUIDELINES:
1. Qualification Questions: Ensure the candidate meets basic job requirements (e.g., age, work authorization)
2. Technical Questions: Test specific skills, tools, and knowledge mentioned in the job description
3. Behavioral Questions: Use the STAR method format (Situation, Task, Action, Result) - start with "Tell me about a time..." or "Describe a situation..."
4. Situational Questions: Present hypothetical scenarios relevant to the role - start with "What would you do if..." or "How would you handle..."
5. Experience Questions: Probe into relevant past experience and qualifications

IMPORTANT:
- ALWAYS include all the qualification questions listed above or in the job description
- ALWAYS include the 4 mandatory experience questions listed above
- Make remaining questions specific to the role and requirements mentioned
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


async def generate_questions_from_job_details(
    job_details: Dict[str, Any],
    num_questions: int = 15,
    question_types: Optional[List[str]] = None,
    difficulty_level: str = "mixed"
) -> List[Dict[str, str]]:
    """
    Generate interview questions from job details JSON.
    
    Args:
        job_details: Dictionary containing job information
        num_questions: Number of questions to generate (default: 15, includes 4 mandatory experience questions)
        question_types: Types of questions (technical, behavioral, etc.)
        difficulty_level: Difficulty level (easy, medium, hard, mixed)
        
    Returns:
        List of question dictionaries with 'question', 'type', and 'purpose' keys
    """
    try:
        # Fetch company details from Xano if company ID is available
        company_info = None
        if job_details.get("related_company"):
            try:
                xano_client = get_xano_client()
                company_id = job_details["related_company"]
                company_info = xano_client.get_company_by_id(company_id)
                logger.info(f"Fetched company details for company_id: {company_id}")
            except Exception as e:
                logger.warning(f"Failed to fetch company details: {e}")
                # Try to use embedded company info if available
                if job_details.get("_related_company"):
                    company_info = job_details["_related_company"]
        
        # Build comprehensive job description from all available fields
        job_description_parts = []
        
        # Job title
        if job_details.get("job_title"):
            job_description_parts.append(f"Job Title: {job_details['job_title']}")
        
        # Company information
        if company_info:
            if company_info.get("company_name"):
                job_description_parts.append(f"Company: {company_info['company_name']}")
            if company_info.get("industry"):
                job_description_parts.append(f"Industry: {company_info['industry']}")
            if company_info.get("description"):
                job_description_parts.append(f"Company Description: {company_info['description']}")
        
        # Job type and work details
        if job_details.get("job_type"):
            job_description_parts.append(f"Job Type: {job_details['job_type']}")
        
        if job_details.get("Shift"):
            job_description_parts.append(f"Shift: {job_details['Shift']}")
        
        if job_details.get("Starting_Date"):
            job_description_parts.append(f"Start Date: {job_details['Starting_Date']}")
        
        # Pay and compensation
        if job_details.get("PayRate"):
            job_description_parts.append(f"Pay Rate: ${job_details['PayRate']}/hour")
        
        if job_details.get("Perks_Benefits"):
            perks = job_details["Perks_Benefits"]
            if isinstance(perks, list):
                perks = ", ".join(perks)
            job_description_parts.append(f"Perks & Benefits: {perks}")
        
        # Job description
        if job_details.get("description"):
            job_description_parts.append(f"\nJob Description:\n{job_details['description']}")
        
        # Eligibility criteria
        if job_details.get("Eligibility_Criteria"):
            job_description_parts.append(f"\nEligibility Criteria:\n{job_details['Eligibility_Criteria']}")
        
        # Screening questions (if provided)
        if job_details.get("Screening_Questions"):
            job_description_parts.append(f"\nScreening Questions:\n{job_details['Screening_Questions']}")
        
        # Age requirements
        if job_details.get("Age_18_Above"):
            job_description_parts.append("Age Requirement: 18 years or older")
        elif job_details.get("Age_16_above"):
            job_description_parts.append("Age Requirement: 16 years or older")
        
        # Experience required
        if job_details.get("required_experience"):
            job_description_parts.append(f"Required Experience: {job_details['required_experience']} years")
        
        # Additional requirements
        additional_req = []
        if job_details.get("Background_check_Req"):
            additional_req.append("Background check required")
        if job_details.get("ID_Verification_req"):
            additional_req.append("ID verification required")
        if job_details.get("Uniform_Provided"):
            additional_req.append("Uniform provided")
        
        if additional_req:
            job_description_parts.append(f"\nAdditional Requirements: {', '.join(additional_req)}")
        
        # Legacy fields (for backward compatibility)
        if job_details.get("requirements"):
            requirements = job_details["requirements"]
            if isinstance(requirements, list):
                requirements = "\n- ".join(requirements)
            job_description_parts.append(f"\nRequirements:\n- {requirements}")
        
        if job_details.get("responsibilities"):
            responsibilities = job_details["responsibilities"]
            if isinstance(responsibilities, list):
                responsibilities = "\n- ".join(responsibilities)
            job_description_parts.append(f"\nResponsibilities:\n- {responsibilities}")
        
        if job_details.get("salary_range"):
            job_description_parts.append(f"\nSalary Range: {job_details['salary_range']}")
        
        job_description = "\n".join(job_description_parts)
        
        if not job_description.strip():
            logger.warning("Job details do not contain enough information to generate questions")
            return []
        
        # Initialize the LLM
        llm = ChatOpenAI(
            model=settings.OPENAI_CHAT_MODEL,
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        
        # Prepare question types
        if not question_types:
            question_types = ["technical", "behavioral", "situational", "experience"]
        question_types_str = ", ".join(question_types)
        
        # Create the prompt
        prompt = ChatPromptTemplate.from_template(QUESTION_GENERATION_PROMPT)
        
        # Format the prompt with the data
        formatted_prompt = prompt.format(
            job_description=job_description,
            num_questions=num_questions,
            question_types=question_types_str,
            difficulty_level=difficulty_level
        )
        
        # Get the response from the LLM
        response = await llm.ainvoke(formatted_prompt)
        
        # Parse the response
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
            
            # Extract questions
            questions = [
                {
                    "question": q["question"],
                    "type": q["type"],
                    "purpose": q["purpose"]
                }
                for q in parsed_response.get("questions", [])
            ]
            
            logger.info(f"Successfully generated {len(questions)} interview questions")
            return questions
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response was: {response_text}")
            return []
            
    except Exception as e:
        logger.error(f"Error generating questions from job details: {e}")
        return []


def format_questions_for_prompt(questions: List[Dict[str, str]]) -> str:
    """
    Format questions for inclusion in agent system prompt.
    
    Args:
        questions: List of question dictionaries
        
    Returns:
        Formatted string of questions
    """
    if not questions:
        return ""
    
    formatted = []
    for i, q in enumerate(questions, 1):
        formatted.append(
            f"{i}. {q.get('question', '')} "
            f"(Type: {q.get('type', 'general')}, "
            f"Purpose: {q.get('purpose', 'N/A')})"
        )
    
    return "\n".join(formatted)
