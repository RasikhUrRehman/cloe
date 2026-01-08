
"""
Simplified Eligibility Report Generator
Uses conversation history from Xano + single LLM call to generate structured reports
"""
import json
import os
from datetime import datetime
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from chatbot.utils.config import settings
from chatbot.utils.utils import setup_logging
from chatbot.utils.xano_client import XanoClient

logger = setup_logging()


class ReportGenerator:
    """Simplified report generator using only conversation history and LLM analysis"""

    def __init__(self, xano_client=None):
        self.reports_dir = settings.REPORTS_DIR
        os.makedirs(self.reports_dir, exist_ok=True)
        self.xano_client = XanoClient()

    def generate_report(self, session_id: str) -> Dict[str, str]:
        """
        Generate JSON and PDF reports based solely on conversation history
        """
        # Fetch session to get job_id
        session = self._fetch_session_from_xano(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        job_id = session.get('job_id')
        if not job_id:
            logger.warning(f"No job_id found in session {session_id}, using default")
            job_id = "9b6ebbe5-8796-4851-8f6f-931a00755d3d"  # Default from main
        
        # Fetch job details
        job_data = self._fetch_job_from_xano(job_id)
        
        # Fetch conversation history from Xano
        conversation_history = self._fetch_conversation_history(session_id)
        if not conversation_history:
            raise ValueError(f"No conversation history found for session {session_id}")

        # Let LLM analyze the entire conversation and produce structured report
        report_data = self._analyze_conversation_with_llm(conversation_history, session_id, job_data)

        # Generate files
        json_path = self._generate_json_report(session_id, report_data)
        pdf_path = self._generate_pdf_report(session_id, report_data, conversation_history)

        # Extract fit_score and explanation from report_data
        fit_score_value = 0
        profile_summary = ""
        
        if "fit_score" in report_data:
            fit_score_value = report_data["fit_score"].get("total_score", 0)
            # Pass entire report JSON as string for profile_summary (as per requirement)
            import json
            profile_summary = json.dumps(report_data, indent=2)

        logger.info(f"Generated reports for session {session_id}")
        return {
            "json_report": json_path,
            "pdf_report": pdf_path,
            "session_id": session_id,
            "fit_score": fit_score_value,
            "profile_summary": profile_summary,
        }

    def _fetch_conversation_history(self, session_id: str) -> List[Dict]:
        """Fetch and format conversation messages from Xano"""
        if not self.xano_client:
            logger.warning("No Xano client provided")
            return []

        try:
            xano_session_id = int(session_id) if str(session_id).isdigit() else session_id
            messages = self.xano_client.get_messages_by_session_id(xano_session_id)
            if not messages:
                return []

            # Sort by timestamp
            messages.sort(key=lambda x: x.get('created_at', 0))

            formatted = []
            for msg in messages:
                formatted.append({
                    'role': 'human' if msg.get('MsgCreator') == 'User' else 'ai',
                    'content': msg.get('MsgContent', ''),
                    'timestamp': msg.get('created_at', '')
                })
            logger.info(f"Fetched {len(formatted)} messages for session {session_id}")
            return formatted
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return []

    def _fetch_session_from_xano(self, session_id: str) -> Dict:
        """Fetch session data from Xano"""
        if not self.xano_client:
            logger.warning("No Xano client provided")
            return None

        try:
            xano_session_id = int(session_id) if str(session_id).isdigit() else session_id
            session = self.xano_client.get_session_by_id(xano_session_id)
            if session:
                logger.info(f"Fetched session data for {session_id}")
                return session
            else:
                # Try searching through sessions
                sessions = self.xano_client.get_sessions()
                for s in sessions:
                    if str(s.get('id', '')) == str(session_id) or s.get('session_id') == session_id:
                        logger.info(f"Found session {session_id} in session list")
                        return s
                logger.warning(f"Session {session_id} not found")
                return None
        except Exception as e:
            logger.error(f"Error fetching session: {e}")
            return None

    def _fetch_job_from_xano(self, job_id: str) -> Dict:
        """Fetch job data from Xano"""
        if not self.xano_client:
            logger.warning("No Xano client provided")
            return None

        try:
            job = self.xano_client.get_job_by_id(job_id)
            if job:
                logger.info(f"Fetched job data for {job_id}")
                return job
            else:
                logger.warning(f"Job {job_id} not found")
                return None
        except Exception as e:
            logger.error(f"Error fetching job: {e}")
            return None

    def _analyze_conversation_with_llm(self, conversation_history: List[Dict], session_id: str, job_data: Dict = None) -> Dict[str, Any]:
        """Single LLM call to extract all relevant information and generate report structure"""
        # Format conversation as plain text
        conversation_text = "\n".join(
            f"{msg['role'].capitalize()}: {msg['content']}"
            for msg in conversation_history
        )

        # Format job details
        job_info = ""
        if job_data:
            job_title = job_data.get('job_title', 'Unknown Position')
            job_description = job_data.get('job_description', '')
            requirements = job_data.get('requirements', '')
            job_info = f"""
Job Details:
- Position: {job_title}
- Description: {job_description}
- Requirements: {requirements}
"""
        else:
            job_info = "\nJob Details: Not available\n"

        prompt = f"""You are an HR assistant analyzing a job application chat interview.

{job_info}

Conversation:
{conversation_text}

Extract and summarize ALL relevant information about the candidate for an eligibility report. Evaluate the candidate's fit for this specific job position based on the job requirements and their responses.

First, analyze the job requirements to determine what qualifications are needed for this position. Then evaluate the candidate against these dynamic requirements.

Return ONLY valid JSON in this exact structure:

{{
  "report_metadata": {{
    "session_id": "{session_id}",
    "generated_at": "{datetime.utcnow().isoformat()}",
    "report_version": "1.0"
  }},
  "applicant_information": {{
    "full_name": "<string or null>",
    "email": "<string or null>",
    "phone_number": "<string or null>",
    "address": "<string or null>"
  }},
  "qualification": {{
    "requirements": [
      {{
        "criterion": "<dynamic requirement based on job, e.g., 'Age 18+', 'Valid Driver License', 'Shift Flexibility'>",
        "met": true|false|null,
        "evidence": "<what the candidate said or didn't say>",
        "importance": "<High|Medium|Low>"
      }}
    ],
    "overall_qualified": true|false|null
  }},
  "experience": {{
    "years_experience": <number or null>,
    "job_title": "<string or null>",
    "previous_employer": "<string or null>",
    "skills": "<comma-separated string or null>",
    "relevant_experience": "<assessment of how well experience matches job requirements>"
  }},
  "fit_score": {{
    "total_score": <number 0-100>,
    "qualification_score": <number 0-100>,
    "experience_score": <number 0-100>,
    "personality_score": <number 0-100>,
    "rating": "<Excellent|Good|Fair|Below Average|Poor>",
    "explanation": "<detailed explanation of why this score was given, referencing specific job requirements and candidate qualifications>"
  }},
  "summary": {{
    "eligibility_status": "Eligible"|"Not Eligible"|"Pending Verification"|"Incomplete",
    "recommendation": "<short recommendation text>",
    "key_strengths": ["<strength1>", "<strength2>", ...],
    "concerns": ["<concern1>", "<concern2>", ...] or []
  }},
  "interview_notes": {{
    "notable_responses": ["<quote or summary 1>", "<quote or summary 2>", ...],
    "overall_impression": "<brief summary of candidate's communication, enthusiasm, professionalism>"
  }}
}}

Rules:
- Only use information explicitly mentioned or clearly implied in the conversation
- If something is not mentioned → use null (not "Not provided")
- Be accurate and conservative
- For qualification.requirements: Analyze the job requirements and create dynamic criteria based on what's needed for this specific job (e.g., age requirements, licenses, certifications, shift availability, transportation, etc.)
- For fit_score: Calculate based on how well the candidate matches the job requirements
  - qualification_score: Based on whether candidate meets the dynamic job-specific requirements
  - experience_score: Based on relevant experience and skills for this specific job
  - personality_score: Based on communication, enthusiasm, professionalism
  - explanation: Provide detailed reasoning referencing specific job requirements and candidate qualifications
- For eligibility_status: 
  - "Eligible" → meets key job requirements + verified + complete
  - "Not Eligible" → fails key job requirements
  - "Pending Verification" → meets requirements but ID not verified
  - "Incomplete" → missing major info
- key_strengths and concerns should be brief and relevant
"""

        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model=settings.OPENAI_CHAT_MODEL,
                temperature=0,
                openai_api_key=settings.OPENAI_API_KEY
            )

            response = llm.invoke(prompt)
            content = response.content.strip()

            # Clean up code block if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            report_data = json.loads(content)
            logger.info("LLM successfully generated structured report data")
            return report_data

        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            raise RuntimeError("Failed to generate report data from conversation")

    def _generate_json_report(self, session_id: str, report_data: Dict) -> str:
        filename = f"eligibility_report_{session_id}.json"
        filepath = os.path.join(self.reports_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        return filepath

    def _generate_pdf_report(self, session_id: str, report_data: Dict, conversation_history: List[Dict] = None) -> str:
        filename = f"eligibility_report_{session_id}.pdf"
        filepath = os.path.join(self.reports_dir, filename)
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph("Eligibility Report", styles["Title"]))
        story.append(Spacer(1, 0.3 * inch))

        # Metadata
        meta = report_data["report_metadata"]
        story.append(Paragraph(f"<b>Session ID:</b> {meta['session_id']}", styles["Normal"]))
        story.append(Paragraph(f"<b>Generated:</b> {meta['generated_at'][:19]} UTC", styles["Normal"]))
        story.append(Spacer(1, 0.4 * inch))

        # Applicant Info
        story.append(Paragraph("Applicant Information", styles["Heading2"]))
        applicant = report_data["applicant_information"]
        for key, value in applicant.items():
            if value is not None:
                label = key.replace("_", " ").title()
                # Ensure value is a string to avoid NoneType errors
                story.append(Paragraph(f"<b>{label}:</b> {str(value)}", styles["Normal"]))

        story.append(Spacer(1, 0.3 * inch))

        # Qualification Table
        story.append(Paragraph("Qualification Criteria", styles["Heading2"]))
        qual = report_data["qualification"]
        
        # Handle dynamic qualification requirements
        if qual.get("requirements"):
            data = [["Requirement", "Met", "Importance", "Evidence"]]
            for req in qual["requirements"]:
                status = "Yes" if req.get("met") is True else "No" if req.get("met") is False else "Unknown"
                importance = req.get("importance", "Medium")
                evidence = req.get("evidence", "N/A")
                
                # Use Paragraph objects for text wrapping in cells
                # Ensure evidence is not None to avoid reportlab errors
                evidence_text = evidence if evidence else "N/A"
                data.append([
                    Paragraph(req.get("criterion", "Unknown"), styles["Normal"]),
                    status,
                    importance,
                    Paragraph(str(evidence_text), styles["Normal"])
                ])
        else:
            # Fallback to old format if requirements not available
            data = [["Criterion", "Status"]]
            data += [
                ["Age Confirmed", "Yes" if qual.get("age_confirmed") else "No" if qual.get("age_confirmed") is False else "Unknown"],
                ["Work Authorization", "Yes" if qual.get("work_authorization") else "No" if qual.get("work_authorization") is False else "Unknown"],
                ["Transportation", "Yes" if qual.get("transportation") else "No" if qual.get("transportation") is False else "Unknown"],
                ["Shift Preference", qual.get("shift_preference") or "N/A"],
                ["Availability", qual.get("availability_start") or "N/A"],
                ["Hours Preference", qual.get("hours_preference") or "N/A"],
            ]
        
        table = Table(data, colWidths=[2.5 * inch, 0.8 * inch, 1 * inch, 2.2 * inch] if qual.get("requirements") else [3.5 * inch, 2.5 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("FONTSIZE", (0, 0), (-1, -1), 8),  # Smaller font for dynamic requirements
            ("VALIGN", (0, 0), (-1, -1), "TOP"),  # Align text to top
            ("WORDWRAP", (0, 0), (-1, -1), True),  # Enable word wrapping
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3 * inch))

        # Experience
        story.append(Paragraph("Experience", styles["Heading2"]))
        exp = report_data["experience"]
        if exp.get("years_experience") is not None:
            story.append(Paragraph(f"<b>Years of Experience:</b> {str(exp['years_experience'])}", styles["Normal"]))
        if exp.get("job_title"):
            story.append(Paragraph(f"<b>Recent Role:</b> {str(exp['job_title'])}", styles["Normal"]))
        if exp.get("previous_employer"):
            story.append(Paragraph(f"<b>Previous Employer:</b> {str(exp['previous_employer'])}", styles["Normal"]))
        if exp.get("skills"):
            story.append(Paragraph(f"<b>Skills:</b> {str(exp['skills'])}", styles["Normal"]))
        if exp.get("relevant_experience"):
            story.append(Paragraph(f"<b>Relevance to Position:</b> {str(exp['relevant_experience'])}", styles["Normal"]))

        story.append(Spacer(1, 0.3 * inch))

        # Summary & Recommendation
        story.append(Paragraph("Summary & Recommendation", styles["Heading2"]))
        summary = report_data["summary"]
        story.append(Paragraph(f"<b>Status:</b> {str(summary.get('eligibility_status', 'N/A'))}", styles["Normal"]))
        story.append(Paragraph(f"<b>Recommendation:</b> {str(summary.get('recommendation', 'N/A'))}", styles["Normal"]))

        if summary.get("key_strengths"):
            story.append(Paragraph("<b>Strengths:</b>", styles["Normal"]))
            for strength in summary["key_strengths"]:
                if strength:  # Ensure strength is not None
                    story.append(Paragraph(f"• {str(strength)}", styles["Normal"]))

        if summary.get("concerns"):
            story.append(Paragraph("<b>Concerns:</b>", styles["Normal"]))
            for concern in summary["concerns"]:
                if concern:  # Ensure concern is not None
                    story.append(Paragraph(f"• {str(concern)}", styles["Normal"]))

        story.append(Spacer(1, 0.3 * inch))

        # Interview Notes
        notes = report_data["interview_notes"]
        story.append(Paragraph("Interview Notes", styles["Heading2"]))
        overall_impression = notes.get("overall_impression") or "N/A"
        story.append(Paragraph(str(overall_impression), styles["Normal"]))
        if notes.get("notable_responses"):
            story.append(Paragraph("<b>Notable Responses:</b>", styles["Normal"]))
            for note in notes["notable_responses"]:
                if note:  # Ensure note is not None
                    story.append(Paragraph(f"• {str(note)}", styles["Normal"]))

        story.append(Spacer(1, 0.3 * inch))

        # Fit Score Analysis
        if "fit_score" in report_data:
            fit = report_data["fit_score"]
            story.append(Paragraph("Fit Score Analysis", styles["Heading2"]))
            
            # Summary scores
            story.append(Paragraph(f"<b>Total Score:</b> {fit['total_score']}/100 ({fit['rating']})", styles["Normal"]))
            story.append(Paragraph(f"<b>Qualification:</b> {fit['qualification_score']}/100 | <b>Experience:</b> {fit['experience_score']}/100 | <b>Personality:</b> {fit['personality_score']}/100", styles["Normal"]))
            
            # Detailed explanation
            if fit.get("explanation"):
                story.append(Spacer(1, 0.2 * inch))
                story.append(Paragraph("<b>Scoring Explanation:</b>", styles["Normal"]))
                explanation_style = ParagraphStyle(
                    "Explanation",
                    parent=styles["Normal"],
                    fontSize=10,
                    textColor=colors.HexColor("#2C3E50"),
                    spaceAfter=12,
                    leftIndent=20,
                )
                # Ensure explanation is not None
                explanation_text = str(fit["explanation"]) if fit["explanation"] else "N/A"
                story.append(Paragraph(explanation_text, explanation_style))

        story.append(Spacer(1, 0.3 * inch))

        # Full Conversation History
        if conversation_history:
            story.append(Paragraph("Full Conversation History", styles["Heading2"]))
            story.append(Spacer(1, 0.2 * inch))
            
            conversation_style = ParagraphStyle(
                "Conversation",
                parent=styles["Normal"],
                fontSize=9,
                leftIndent=10,
                spaceAfter=6,
            )
            
            for msg in conversation_history:
                role = "Assistant" if msg.get('role') == 'ai' else "Candidate"
                content = msg.get('content', '')
                
                # Ensure content is not None to avoid reportlab errors
                if content is None:
                    content = ''
                
                message_text = f"<b>{role}:</b> {str(content)}"
                
                story.append(Paragraph(message_text, conversation_style))
                story.append(Spacer(1, 0.1 * inch))

        doc.build(story)
        logger.info(f"PDF generated: {filepath}")
        return filepath


if __name__ == "__main__":
    generator = ReportGenerator()
    generator.generate_report("175")
    xano_client = XanoClient()