"""
Eligibility Report Generator
Creates structured JSON and PDF reports for completed applications
"""
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from states import SessionState, StateManager
from fit_score import FitScoreCalculator, FitScoreComponents
from config import settings
from utils import setup_logging

logger = setup_logging()


class ReportGenerator:
    """Generates eligibility reports for job applications"""
    
    def __init__(self):
        self.reports_dir = settings.REPORTS_DIR
        os.makedirs(self.reports_dir, exist_ok=True)
        self.fit_calculator = FitScoreCalculator()
    
    def generate_report(
        self,
        session_id: str,
        include_fit_score: bool = None
    ) -> Dict[str, str]:
        """
        Generate both JSON and PDF reports for a session
        
        Args:
            session_id: Session identifier
            include_fit_score: Whether to include fit score in report
        
        Returns:
            Dictionary with paths to generated reports
        """
        if include_fit_score is None:
            include_fit_score = settings.INCLUDE_FIT_SCORE_IN_REPORT
        
        # Load session data
        state_manager = StateManager()
        engagement = state_manager.load_engagement(session_id)
        qualification = state_manager.load_qualification(session_id)
        application = state_manager.load_application(session_id)
        verification = state_manager.load_verification(session_id)
        
        if not engagement:
            raise ValueError(f"No data found for session {session_id}")
        
        # Calculate fit score
        fit_score = self.fit_calculator.calculate_fit_score(
            qualification=qualification,
            application=application,
            verification=verification
        )
        
        # Generate report data
        report_data = self._create_report_data(
            session_id=session_id,
            engagement=engagement,
            qualification=qualification,
            application=application,
            verification=verification,
            fit_score=fit_score,
            include_fit_score=include_fit_score
        )
        
        # Generate JSON report
        json_path = self._generate_json_report(session_id, report_data)
        
        # Generate PDF report
        pdf_path = self._generate_pdf_report(session_id, report_data, include_fit_score)
        
        logger.info(f"Generated reports for session {session_id}")
        
        return {
            'json_report': json_path,
            'pdf_report': pdf_path,
            'session_id': session_id
        }
    
    def _create_report_data(
        self,
        session_id: str,
        engagement: Any,
        qualification: Any,
        application: Any,
        verification: Any,
        fit_score: FitScoreComponents,
        include_fit_score: bool
    ) -> Dict[str, Any]:
        """Create structured report data"""
        report = {
            'report_metadata': {
                'session_id': session_id,
                'generated_at': datetime.utcnow().isoformat(),
                'report_version': '1.0'
            },
            'applicant_information': {},
            'qualification_status': {},
            'application_details': {},
            'verification_status': {},
            'eligibility_summary': {}
        }
        
        # Applicant Information
        if application:
            report['applicant_information'] = {
                'full_name': application.full_name,
                'phone_number': application.phone_number,
                'email': application.email,
                'address': application.address,
                'communication_preference': application.communication_preference
            }
        
        # Qualification Status
        if qualification:
            report['qualification_status'] = {
                'age_confirmed': qualification.age_confirmed,
                'work_authorization': qualification.work_authorization,
                'shift_preference': qualification.shift_preference,
                'availability_start': qualification.availability_start,
                'transportation': qualification.transportation,
                'hours_preference': qualification.hours_preference,
                'status': qualification.qualification_status
            }
        
        # Application Details
        if application:
            report['application_details'] = {
                'previous_employer': application.previous_employer,
                'job_title': application.job_title,
                'years_experience': application.years_experience,
                'skills': application.skills,
                'references': application.references,
                'application_status': application.application_status
            }
        
        # Verification Status
        if verification:
            report['verification_status'] = {
                'id_uploaded': verification.id_uploaded,
                'id_type': verification.id_type,
                'verification_status': verification.verification_status,
                'timestamp_verified': verification.timestamp_verified
            }
        
        # Eligibility Summary
        report['eligibility_summary'] = {
            'qualified': qualification.qualification_status == 'qualified' if qualification else False,
            'verified': verification.verification_status == 'verified' if verification else False,
            'application_complete': application.application_status == 'submitted' if application else False,
            'recommendation': self._get_recommendation(qualification, verification, fit_score)
        }
        
        # Include fit score if requested (internal use only)
        if include_fit_score:
            report['fit_score'] = {
                'total_score': round(fit_score.total_score, 2),
                'rating': self.fit_calculator.get_fit_rating(fit_score.total_score),
                'qualification_score': round(fit_score.qualification_score, 2),
                'experience_score': round(fit_score.experience_score, 2),
                'verification_score': round(fit_score.verification_score, 2),
                'breakdown': fit_score.breakdown
            }
        
        return report
    
    def _get_recommendation(self, qualification, verification, fit_score: FitScoreComponents) -> str:
        """Generate recommendation based on application data"""
        if not qualification or qualification.qualification_status != 'qualified':
            return "Not Qualified - Does not meet basic requirements"
        
        if not verification or verification.verification_status != 'verified':
            return "Pending - Verification incomplete"
        
        total_score = fit_score.total_score
        
        if total_score >= 85:
            return "Highly Recommended - Excellent candidate"
        elif total_score >= 70:
            return "Recommended - Good candidate"
        elif total_score >= 55:
            return "Consider - Fair candidate, may need additional review"
        else:
            return "Review Required - Below average match"
    
    def _generate_json_report(self, session_id: str, report_data: Dict[str, Any]) -> str:
        """Generate JSON report file"""
        filename = f"eligibility_report_{session_id}.json"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Generated JSON report: {filepath}")
        return filepath
    
    def _generate_pdf_report(
        self,
        session_id: str,
        report_data: Dict[str, Any],
        include_fit_score: bool
    ) -> str:
        """Generate PDF report file"""
        filename = f"eligibility_report_{session_id}.pdf"
        filepath = os.path.join(self.reports_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30
        )
        story.append(Paragraph("Eligibility Report", title_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Metadata
        metadata = report_data['report_metadata']
        story.append(Paragraph(f"<b>Session ID:</b> {metadata['session_id']}", styles['Normal']))
        story.append(Paragraph(f"<b>Generated:</b> {metadata['generated_at']}", styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))
        
        # Applicant Information
        story.append(Paragraph("<b>Applicant Information</b>", styles['Heading2']))
        applicant = report_data.get('applicant_information', {})
        for key, value in applicant.items():
            if value:
                label = key.replace('_', ' ').title()
                story.append(Paragraph(f"<b>{label}:</b> {value}", styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))
        
        # Qualification Status
        story.append(Paragraph("<b>Qualification Status</b>", styles['Heading2']))
        qual = report_data.get('qualification_status', {})
        qual_data = [
            ['Criterion', 'Status'],
            ['Age Confirmed', '✓' if qual.get('age_confirmed') else '✗'],
            ['Work Authorization', '✓' if qual.get('work_authorization') else '✗'],
            ['Shift Preference', qual.get('shift_preference', 'N/A')],
            ['Availability Start', qual.get('availability_start', 'N/A')],
            ['Transportation', '✓' if qual.get('transportation') else '✗'],
            ['Hours Preference', qual.get('hours_preference', 'N/A')],
        ]
        qual_table = Table(qual_data, colWidths=[3 * inch, 3 * inch])
        qual_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(qual_table)
        story.append(Spacer(1, 0.3 * inch))
        
        # Application Details
        story.append(Paragraph("<b>Application Details</b>", styles['Heading2']))
        app = report_data.get('application_details', {})
        for key, value in app.items():
            if value is not None:
                label = key.replace('_', ' ').title()
                story.append(Paragraph(f"<b>{label}:</b> {value}", styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))
        
        # Verification Status
        story.append(Paragraph("<b>Verification Status</b>", styles['Heading2']))
        ver = report_data.get('verification_status', {})
        story.append(Paragraph(f"<b>ID Uploaded:</b> {'Yes' if ver.get('id_uploaded') else 'No'}", styles['Normal']))
        story.append(Paragraph(f"<b>ID Type:</b> {ver.get('id_type', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"<b>Status:</b> {ver.get('verification_status', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))
        
        # Eligibility Summary
        story.append(Paragraph("<b>Eligibility Summary</b>", styles['Heading2']))
        summary = report_data.get('eligibility_summary', {})
        story.append(Paragraph(f"<b>Qualified:</b> {'Yes' if summary.get('qualified') else 'No'}", styles['Normal']))
        story.append(Paragraph(f"<b>Verified:</b> {'Yes' if summary.get('verified') else 'No'}", styles['Normal']))
        story.append(Paragraph(f"<b>Recommendation:</b> {summary.get('recommendation', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))
        
        # Fit Score (if included)
        if include_fit_score and 'fit_score' in report_data:
            story.append(Paragraph("<b>Fit Score Analysis</b>", styles['Heading2']))
            fit = report_data['fit_score']
            story.append(Paragraph(f"<b>Total Score:</b> {fit['total_score']}/100", styles['Normal']))
            story.append(Paragraph(f"<b>Rating:</b> {fit['rating']}", styles['Normal']))
            story.append(Paragraph(f"<b>Qualification Score:</b> {fit['qualification_score']}/100", styles['Normal']))
            story.append(Paragraph(f"<b>Experience Score:</b> {fit['experience_score']}/100", styles['Normal']))
            story.append(Paragraph(f"<b>Verification Score:</b> {fit['verification_score']}/100", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        logger.info(f"Generated PDF report: {filepath}")
        return filepath


def main():
    """Example usage of report generator"""
    from config import ensure_directories
    from states import EngagementState, QualificationState, ApplicationState, VerificationState, StateManager
    
    ensure_directories()
    
    # Create sample session data
    session_id = "test-report-123"
    state_manager = StateManager()
    
    # Create and save sample states
    engagement = EngagementState(
        session_id=session_id,
        consent_given=True,
        company_id="COMP001",
        job_id="JOB001",
        stage_completed=True
    )
    
    qualification = QualificationState(
        session_id=session_id,
        age_confirmed=True,
        work_authorization=True,
        shift_preference="day",
        availability_start="2024-02-01",
        transportation=True,
        hours_preference="full-time",
        qualification_status="qualified",
        stage_completed=True
    )
    
    application = ApplicationState(
        session_id=session_id,
        full_name="John Doe",
        phone_number="555-0123",
        email="john.doe@example.com",
        address="123 Main St, City, State 12345",
        previous_employer="ABC Corp",
        job_title="Warehouse Associate",
        years_experience=3.5,
        skills="forklift, inventory, packing",
        references="Available upon request",
        application_status="submitted",
        stage_completed=True
    )
    
    verification = VerificationState(
        session_id=session_id,
        id_uploaded=True,
        id_type="driver_license",
        verification_status="verified",
        timestamp_verified=datetime.utcnow().isoformat(),
        stage_completed=True
    )
    
    # Save states
    state_manager.save_engagement(engagement)
    state_manager.save_qualification(qualification)
    state_manager.save_application(application)
    state_manager.save_verification(verification)
    
    # Generate report
    generator = ReportGenerator()
    result = generator.generate_report(session_id, include_fit_score=True)
    
    print(f"\n=== Report Generated ===")
    print(f"JSON Report: {result['json_report']}")
    print(f"PDF Report: {result['pdf_report']}")


if __name__ == "__main__":
    main()
