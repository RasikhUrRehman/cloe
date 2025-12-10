"""
Applications Routes
Handles application-related API endpoints including PDF generation
All data is managed by Xano - no local storage
"""
import io
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from chatbot.utils.config import settings
from chatbot.utils.fit_score import FitScoreCalculator
from chatbot.utils.utils import setup_logging
from chatbot.utils.xano_client import get_xano_client

logger = setup_logging()
router = APIRouter(prefix="/api/v1/applications", tags=["Applications"])

# Store for active sessions - will be shared from main app
active_sessions: Dict[str, Any] = {}


def set_active_sessions(sessions: Dict[str, Any]):
    """Set the reference to active sessions from main app"""
    global active_sessions
    active_sessions = sessions


# Response Models
class ApplicationResponse(BaseModel):
    """Response model for application data"""
    session_id: int  # Xano session ID
    candidate_id: Optional[int] = None
    timestamp: Any  # Can be int or str
    job: Optional[Dict[str, Any]] = None
    company: Optional[Dict[str, Any]] = None
    applicant: Optional[Dict[str, Any]] = None
    application_file: Optional[Dict[str, Any]] = None
    fit_score: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    conversation_summary: Optional[Dict[str, Any]] = None  # Contains discussion_summary, strengths, weaknesses, overall_impression


class ApplicationSummary(BaseModel):
    """Summary model for application list"""
    session_id: int  # Xano session ID
    candidate_id: Optional[int] = None
    timestamp: Optional[Any] = None  # Can be int or str
    applicant_name: Optional[str] = None
    applicant_email: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    status: Optional[str] = None
    fit_score: Optional[float] = None
    rating: Optional[str] = None


def _build_application_data_from_xano(session_id: int) -> Dict[str, Any]:
    """
    Build application data entirely from Xano.
    
    Session only contains: candidate_id and Status
    Candidate contains: Name, Score, Email, Phone, Report_pdf, job_id, company_id, 
                       Status, user_id, session_id, Application
    """
    xano_client = get_xano_client()
    
    # Get session from Xano (only has candidate_id and Status)
    session = xano_client.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found in Xano")
    
    # Get candidate data using candidate_id from session
    candidate_data = None
    candidate_id = session.get('candidate_id')
    if candidate_id:
        candidate_data = xano_client.get_candidate_by_id(candidate_id)
    
    if not candidate_data:
        raise HTTPException(status_code=404, detail=f"Candidate not found for session {session_id}")
    
    # Get messages from Xano
    messages = xano_client.get_messages_by_session_id(session_id) or []
    
    # Build applicant info from candidate data
    applicant_info = {
        "name": candidate_data.get("Name"),
        "email": candidate_data.get("Email"),
        "phone": candidate_data.get("Phone"),
        "score": candidate_data.get("Score"),
        "status": candidate_data.get("Status"),
        "report_pdf": candidate_data.get("Report_pdf"),
        "user_id": candidate_data.get("user_id"),
    }
    
    # Get job details using job_id from candidate data
    job_details = None
    job_id = candidate_data.get('job_id')
    if job_id:
        job_details = xano_client.get_job_by_id(job_id)
    
    # Get company details using company_id from candidate data
    company_details = None
    company_id = candidate_data.get('company_id')
    if company_id:
        company_details = xano_client.get_company_by_id(company_id)
    
    # Get application file info from candidate
    application_file = candidate_data.get('Application')
    
    # Build fit score from candidate Score
    fit_score_data = None
    candidate_score = candidate_data.get('Score')
    if candidate_score is not None:
        fit_score_data = {
            "total_score": candidate_score,
            "rating": _get_rating_from_score(candidate_score),
        }
    
    # Generate conversation summary from messages using LLM
    conversation_summary = _generate_conversation_summary(messages, job_details)
    
    return {
        "session_id": session_id,
        "candidate_id": candidate_id,
        "timestamp": session.get('created_at'),
        "job": job_details,
        "company": company_details,
        "applicant": applicant_info,
        "application_file": application_file,
        "fit_score": fit_score_data,
        "status": session.get('Status', candidate_data.get('Status', 'unknown')),
        "conversation_summary": conversation_summary,
    }


def _generate_conversation_summary(messages: List[Dict[str, Any]], job_details: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Use LLM to generate a comprehensive summary of the conversation,
    including candidate strengths and weaknesses.
    """
    if not messages:
        return {
            "discussion_summary": "No conversation recorded.",
            "strengths": [],
            "weaknesses": [],
            "overall_impression": "Unable to assess - no conversation data.",
        }
    
    # Build conversation transcript for the LLM
    transcript_lines = []
    for msg in messages:
        creator = msg.get('MsgCreator', 'Unknown')
        content = msg.get('MsgContent', '')
        role = "Candidate" if creator == 'User' else "Interviewer"
        transcript_lines.append(f"{role}: {content}")
    
    transcript = "\n".join(transcript_lines)
    
    # Build job context if available
    job_context = ""
    if job_details:
        job_context = f"""
Job Position: {job_details.get('job_title', 'N/A')}
Company: {job_details.get('company', 'N/A')}
Location: {job_details.get('location', 'N/A')}
Requirements: {job_details.get('requirements', 'N/A')}
"""
    
    # Create prompt for the LLM
    summary_prompt = f"""Analyze the following job application conversation and provide a structured assessment.

{f"JOB DETAILS:{job_context}" if job_context else ""}

CONVERSATION TRANSCRIPT:
{transcript}

Please provide your analysis in the following exact format (use these exact headers):

DISCUSSION SUMMARY:
[Provide a 2-3 sentence summary of what was discussed during the conversation]

CANDIDATE STRENGTHS:
- [Strength 1]
- [Strength 2]
- [Strength 3]
(List 3-5 key strengths demonstrated by the candidate)

CANDIDATE WEAKNESSES:
- [Weakness 1]
- [Weakness 2]
(List any concerns, gaps, or areas for improvement. If none apparent, state "No significant weaknesses identified")

OVERALL IMPRESSION:
[1-2 sentences giving an overall hiring recommendation or impression]
"""
    
    try:
        # Use LLM to generate the summary
        llm = ChatOpenAI(
            model=settings.model_name,
            temperature=0.3,
            api_key=settings.openai_api_key,
        )
        
        response = llm.invoke(summary_prompt)
        response_text = response.content
        
        # Parse the response
        summary_data = _parse_llm_summary(response_text)
        return summary_data
        
    except Exception as e:
        logger.error(f"Error generating LLM summary: {e}")
        # Fallback to basic summary
        user_messages = [m for m in messages if m.get('MsgCreator') == 'User']
        return {
            "discussion_summary": f"Conversation with {len(messages)} messages exchanged.",
            "strengths": ["Engaged in the application process"],
            "weaknesses": ["Unable to perform detailed analysis"],
            "overall_impression": "Manual review recommended.",
        }


def _parse_llm_summary(response_text: str) -> Dict[str, Any]:
    """Parse the LLM response into structured data"""
    result = {
        "discussion_summary": "",
        "strengths": [],
        "weaknesses": [],
        "overall_impression": "",
    }
    
    lines = response_text.strip().split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect section headers
        if 'DISCUSSION SUMMARY:' in line.upper():
            current_section = 'summary'
            # Check if content is on the same line
            content = line.split(':', 1)[-1].strip()
            if content:
                result["discussion_summary"] = content
        elif 'CANDIDATE STRENGTHS:' in line.upper() or 'STRENGTHS:' in line.upper():
            current_section = 'strengths'
        elif 'CANDIDATE WEAKNESSES:' in line.upper() or 'WEAKNESSES:' in line.upper():
            current_section = 'weaknesses'
        elif 'OVERALL IMPRESSION:' in line.upper():
            current_section = 'impression'
            content = line.split(':', 1)[-1].strip()
            if content:
                result["overall_impression"] = content
        else:
            # Add content to current section
            if current_section == 'summary' and not result["discussion_summary"]:
                result["discussion_summary"] = line
            elif current_section == 'strengths' and line.startswith('-'):
                result["strengths"].append(line[1:].strip())
            elif current_section == 'weaknesses' and line.startswith('-'):
                result["weaknesses"].append(line[1:].strip())
            elif current_section == 'impression' and not result["overall_impression"]:
                result["overall_impression"] = line
            elif current_section == 'summary':
                result["discussion_summary"] += " " + line
            elif current_section == 'impression':
                result["overall_impression"] += " " + line
    
    # Ensure we have at least some default values
    if not result["discussion_summary"]:
        result["discussion_summary"] = "Application conversation completed."
    if not result["strengths"]:
        result["strengths"] = ["Completed the application process"]
    if not result["weaknesses"]:
        result["weaknesses"] = ["No significant weaknesses identified"]
    if not result["overall_impression"]:
        result["overall_impression"] = "Review recommended."
    
    return result


def _get_rating_from_score(score: float) -> str:
    """Get rating string from score"""
    if score >= 80:
        return "Excellent Fit"
    elif score >= 60:
        return "Good Fit"
    elif score >= 40:
        return "Moderate Fit"
    else:
        return "Needs Review"


def _generate_pdf_from_data(application_data: Dict[str, Any]) -> bytes:
    """Generate PDF report from application data - summary of discussion and fit score"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    elements = []
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=12,
        textColor=colors.HexColor('#1a1a2e'),
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=12,
        spaceAfter=6,
        textColor=colors.HexColor('#16213e'),
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceBefore=8,
        spaceAfter=4,
        textColor=colors.HexColor('#2d3436'),
    )
    
    normal_style = styles['Normal']
    
    # Title
    elements.append(Paragraph("Candidate Application Report", title_style))
    elements.append(Spacer(1, 12))
    
    # Session info
    elements.append(Paragraph(f"Session ID: {application_data.get('session_id', 'N/A')}", normal_style))
    elements.append(Paragraph(f"Generated: {application_data.get('timestamp', datetime.utcnow().isoformat())}", normal_style))
    elements.append(Paragraph(f"Status: {application_data.get('status', 'N/A')}", normal_style))
    elements.append(Spacer(1, 12))
    
    # Applicant Information
    applicant = application_data.get('applicant', {})
    if applicant:
        elements.append(Paragraph("Candidate Information", heading_style))
        applicant_data = [
            ["Name:", str(applicant.get('name', 'N/A'))],
            ["Email:", str(applicant.get('email', 'N/A'))],
            ["Phone:", str(applicant.get('phone', 'N/A'))],
            ["Status:", str(applicant.get('status', 'N/A'))],
        ]
        
        table = Table(applicant_data, colWidths=[1.5*inch, 4.5*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))
    
    # Job Information
    job = application_data.get('job', {})
    if job:
        elements.append(Paragraph("Job Information", heading_style))
        job_data = [
            ["Title:", str(job.get('job_title', 'N/A'))],
            ["Company:", str(job.get('company', 'N/A'))],
            ["Location:", str(job.get('location', 'N/A'))],
        ]
        if job.get('description'):
            job_data.append(["Description:", str(job.get('description', 'N/A'))[:100] + "..."])
        
        table = Table(job_data, colWidths=[1.5*inch, 4.5*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))
    
    # Company Information
    company = application_data.get('company', {})
    if company:
        elements.append(Paragraph("Company Information", heading_style))
        company_data = [
            ["Company Name:", str(company.get('name', company.get('company_name', 'N/A')))],
        ]
        if company.get('industry'):
            company_data.append(["Industry:", str(company.get('industry', 'N/A'))])
        if company.get('location'):
            company_data.append(["Location:", str(company.get('location', 'N/A'))])
        
        table = Table(company_data, colWidths=[1.5*inch, 4.5*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))
    
    # Application File Info
    application_file = application_data.get('application_file', {})
    if application_file and isinstance(application_file, dict):
        elements.append(Paragraph("Application Document", heading_style))
        file_data = [
            ["File Name:", str(application_file.get('name', 'N/A'))],
            ["File Type:", str(application_file.get('type', application_file.get('mime', 'N/A')))],
            ["Access:", str(application_file.get('access', 'N/A'))],
        ]
        if application_file.get('size'):
            size_kb = application_file.get('size', 0) / 1024
            file_data.append(["Size:", f"{size_kb:.2f} KB"])
        
        table = Table(file_data, colWidths=[1.5*inch, 4.5*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))
    
    # Fit Score
    fit_score = application_data.get('fit_score', {})
    if fit_score:
        elements.append(Paragraph("Fit Score Analysis", heading_style))
        
        total_score = fit_score.get('total_score', 0)
        # Handle both int and float scores
        if isinstance(total_score, (int, float)):
            score_display = f"{total_score:.1f}/100"
        else:
            score_display = f"{total_score}/100"
        
        score_data = [
            ["Total Score:", score_display],
            ["Rating:", str(fit_score.get('rating', 'N/A'))],
        ]
        
        table = Table(score_data, colWidths=[1.5*inch, 2*inch])
        
        # Color based on rating
        rating = fit_score.get('rating', '')
        if 'Excellent' in str(rating):
            bg_color = colors.HexColor('#d4edda')
        elif 'Good' in str(rating):
            bg_color = colors.HexColor('#fff3cd')
        else:
            bg_color = colors.HexColor('#f8d7da')
        
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.gray),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))
    
    # Conversation Summary
    conversation_summary = application_data.get('conversation_summary', {})
    if conversation_summary:
        # Discussion Summary
        elements.append(Paragraph("Discussion Summary", heading_style))
        discussion_text = conversation_summary.get('discussion_summary', 'No summary available.')
        elements.append(Paragraph(discussion_text, normal_style))
        elements.append(Spacer(1, 12))
        
        # Candidate Strengths
        elements.append(Paragraph("Candidate Strengths", heading_style))
        strengths = conversation_summary.get('strengths', [])
        if strengths:
            for strength in strengths:
                # Use bullet point style
                elements.append(Paragraph(f"• {strength}", normal_style))
                elements.append(Spacer(1, 2))
        else:
            elements.append(Paragraph("No strengths identified.", normal_style))
        elements.append(Spacer(1, 12))
        
        # Candidate Weaknesses
        elements.append(Paragraph("Areas for Improvement", heading_style))
        weaknesses = conversation_summary.get('weaknesses', [])
        if weaknesses:
            for weakness in weaknesses:
                elements.append(Paragraph(f"• {weakness}", normal_style))
                elements.append(Spacer(1, 2))
        else:
            elements.append(Paragraph("No significant concerns identified.", normal_style))
        elements.append(Spacer(1, 12))
        
        # Overall Impression
        elements.append(Paragraph("Overall Assessment", heading_style))
        overall = conversation_summary.get('overall_impression', 'Review recommended.')
        
        # Create a styled box for overall impression
        impression_style = ParagraphStyle(
            'Impression',
            parent=normal_style,
            fontSize=11,
            leading=14,
            spaceAfter=6,
        )
        elements.append(Paragraph(overall, impression_style))
        elements.append(Spacer(1, 12))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


@router.get("/{session_id}", response_model=ApplicationResponse)
async def get_application(session_id: int):
    """
    Get the application data for a Xano session
    
    Args:
        session_id: Xano session ID (integer)
    """
    try:
        application_data = _build_application_data_from_xano(session_id)
        return application_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving application: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve application: {str(e)}")


@router.get("/{session_id}/pdf")
async def get_application_pdf(session_id: int):
    """
    Generate and return a PDF application report for a Xano session
    
    Args:
        session_id: Xano session ID (integer)
    """
    try:
        # Build application data from Xano
        application_data = _build_application_data_from_xano(session_id)
        
        # Generate PDF
        pdf_bytes = _generate_pdf_from_data(application_data)
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=application_{session_id}.pdf"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating application PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")


@router.get("", response_model=List[ApplicationSummary])
async def list_applications(session_ids: Optional[str] = None, limit: int = 100, offset: int = 0):
    """
    List applications by fetching each session by ID from Xano
    
    Args:
        session_ids: Comma-separated list of Xano session IDs to fetch (e.g., "1,2,3")
        limit: Maximum number of applications to return
        offset: Number of applications to skip
    """
    try:
        xano_client = get_xano_client()
        applications = []
        
        if session_ids:
            # Parse session IDs from comma-separated string
            try:
                ids = [int(sid.strip()) for sid in session_ids.split(",") if sid.strip()]
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid session_ids format. Use comma-separated integers.")
            
            # Fetch each session by ID
            for sid in ids[offset:offset + limit]:
                session = xano_client.get_session_by_id(sid)
                if session:
                    app_summary = _build_application_summary(session, xano_client)
                    applications.append(app_summary)
        else:
            # Get all sessions if no specific IDs provided
            sessions = xano_client.get_sessions() or []
            for session in sessions[offset:offset + limit]:
                app_summary = _build_application_summary(session, xano_client)
                applications.append(app_summary)
        
        return applications
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing applications: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list applications: {str(e)}")


def _build_application_summary(session: Dict[str, Any], xano_client) -> ApplicationSummary:
    """
    Build application summary from session data.
    Session only has: candidate_id and Status.
    Candidate has: Name, Score, Email, Phone, job_id, company_id, Status, etc.
    """
    session_id = session.get('id')
    candidate_id = session.get('candidate_id')
    applicant_name = None
    applicant_email = None
    fit_score = None
    rating = None
    job_title = None
    company = None
    
    # Get candidate info if linked - candidate has job_id and company_id
    if candidate_id:
        candidate = xano_client.get_candidate_by_id(candidate_id)
        if candidate:
            applicant_name = candidate.get('Name')
            applicant_email = candidate.get('Email')
            fit_score = candidate.get('Score')
            if fit_score is not None:
                rating = _get_rating_from_score(fit_score)
            
            # Get job info using job_id from candidate (not session)
            job_id = candidate.get('job_id')
            if job_id:
                job = xano_client.get_job_by_id(job_id)
                if job:
                    job_title = job.get('job_title')
                    company = job.get('company')
            
            # If no company from job, try to get from company_id
            if not company:
                company_id = candidate.get('company_id')
                if company_id:
                    company_data = xano_client.get_company_by_id(company_id)
                    if company_data:
                        company = company_data.get('name', company_data.get('company_name'))
    
    return ApplicationSummary(
        session_id=session_id,
        candidate_id=candidate_id,
        timestamp=session.get('created_at'),
        applicant_name=applicant_name,
        applicant_email=applicant_email,
        job_title=job_title,
        company=company,
        status=session.get('Status', 'unknown'),
        fit_score=fit_score,
        rating=rating,
    )


@router.post("/{session_id}/calculate_fit_score")
async def calculate_fit_score(session_id: int):
    """
    Calculate fit score for a Xano session and update candidate
    
    Args:
        session_id: Xano session ID (integer)
    """
    try:
        xano_client = get_xano_client()
        
        # Get session from Xano
        session = xano_client.get_session_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Get messages for personality analysis
        messages = xano_client.get_messages_by_session_id(session_id) or []
        
        chat_history = []
        for msg in messages:
            chat_history.append({
                "role": "human" if msg.get("MsgCreator") == "User" else "ai",
                "content": msg.get("MsgContent", ""),
            })
        
        # Get stored application data
        stored_app_data = session.get('application_data')
        if stored_app_data:
            import json
            if isinstance(stored_app_data, str):
                try:
                    stored_app_data = json.loads(stored_app_data)
                except:
                    stored_app_data = {}
        else:
            stored_app_data = {}
        
        # Calculate basic score from chat analysis if no structured data
        # This is a simplified scoring when full qualification/application data isn't available
        total_messages = len(messages)
        user_messages = len([m for m in messages if m.get('MsgCreator') == 'User'])
        
        # Basic engagement score
        engagement_score = min(40, user_messages * 5)  # Max 40 points for engagement
        
        # Check for completion signals in messages
        completion_keywords = ['completed', 'finished', 'done', 'submitted', 'thank you']
        completion_score = 0
        for msg in messages:
            content = (msg.get('MsgContent') or '').lower()
            if any(kw in content for kw in completion_keywords):
                completion_score = 30
                break
        
        # Response quality score (based on message length)
        avg_user_msg_len = 0
        if user_messages > 0:
            total_len = sum(len(m.get('MsgContent', '')) for m in messages if m.get('MsgCreator') == 'User')
            avg_user_msg_len = total_len / user_messages
        quality_score = min(30, avg_user_msg_len / 5)  # Max 30 points
        
        total_score = engagement_score + completion_score + quality_score
        rating = _get_rating_from_score(total_score)
        
        # Update candidate score in Xano if candidate exists
        candidate_id = session.get('candidate_id')
        if candidate_id:
            xano_client.update_candidate(candidate_id, {"Score": total_score, "Status": rating})
        
        
        logger.info(f"Fit score calculated for session {session_id}: {total_score}")
        
        return {
            "session_id": session_id,
            "fit_score": {
                "total_score": total_score,
                "rating": rating,
                "engagement_score": engagement_score,
                "completion_score": completion_score,
                "quality_score": quality_score,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating fit score: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate fit score: {str(e)}")
