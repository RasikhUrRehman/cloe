"""
Fit Score Computation Module
Calculates candidate fit score based on qualification, experience, and verification
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from chatbot.state.states import ApplicationState, QualificationState, VerificationState
from chatbot.utils.config import settings
from chatbot.utils.utils import setup_logging

logger = setup_logging()


@dataclass
class FitScoreComponents:
    """Individual components of the fit score"""

    qualification_score: float
    experience_score: float
    verification_score: float
    total_score: float
    breakdown: Dict[str, Any]


class FitScoreCalculator:
    """Calculates fit scores for job applicants"""

    def __init__(
        self,
        qualification_weight: float = None,
        experience_weight: float = None,
        verification_weight: float = None,
    ):
        """
        Initialize fit score calculator with weights

        Args:
            qualification_weight: Weight for qualification score (default from settings)
            experience_weight: Weight for experience score (default from settings)
            verification_weight: Weight for verification score (default from settings)
        """
        self.qualification_weight = (
            qualification_weight or settings.QUALIFICATION_WEIGHT
        )
        self.experience_weight = experience_weight or settings.EXPERIENCE_WEIGHT
        self.verification_weight = verification_weight or settings.VERIFICATION_WEIGHT

        # Ensure weights sum to 1.0
        total = (
            self.qualification_weight
            + self.experience_weight
            + self.verification_weight
        )
        if abs(total - 1.0) > 0.01:
            logger.warning(f"Weights sum to {total}, normalizing...")
            self.qualification_weight /= total
            self.experience_weight /= total
            self.verification_weight /= total

    def calculate_qualification_score(
        self, qualification: QualificationState
    ) -> Dict[str, Any]:
        """
        Calculate qualification score based on basic eligibility criteria

        Args:
            qualification: QualificationState object

        Returns:
            Dictionary with score and breakdown
        """
        score = 0.0
        breakdown = {}
        max_score = 100.0

        # Age confirmation (20 points)
        if qualification.age_confirmed:
            score += 20
            breakdown["age_confirmed"] = 20
        else:
            breakdown["age_confirmed"] = 0

        # Work authorization (25 points)
        if qualification.work_authorization:
            score += 25
            breakdown["work_authorization"] = 25
        else:
            breakdown["work_authorization"] = 0

        # Shift preference match (15 points)
        if qualification.shift_preference:
            # In a real system, compare with job requirements
            score += 15
            breakdown["shift_preference"] = 15
        else:
            breakdown["shift_preference"] = 0

        # Availability (20 points)
        if qualification.availability_start:
            # In a real system, check if start date is acceptable
            score += 20
            breakdown["availability"] = 20
        else:
            breakdown["availability"] = 0

        # Transportation (10 points)
        if qualification.transportation:
            score += 10
            breakdown["transportation"] = 10
        else:
            breakdown["transportation"] = 0

        # Hours preference (10 points)
        if qualification.hours_preference:
            score += 10
            breakdown["hours_preference"] = 10
        else:
            breakdown["hours_preference"] = 0

        # Normalize to 0-100
        final_score = (score / max_score) * 100

        logger.info(f"Qualification score: {final_score:.2f}/100")

        return {
            "score": final_score,
            "breakdown": breakdown,
            "qualified": qualification.qualification_status == "qualified",
        }

    def calculate_experience_score(
        self, application: ApplicationState
    ) -> Dict[str, Any]:
        """
        Calculate experience score based on work history and skills

        Args:
            application: ApplicationState object

        Returns:
            Dictionary with score and breakdown
        """
        score = 0.0
        breakdown = {}
        max_score = 100.0

        # Years of experience (40 points max)
        if application.years_experience is not None:
            years = application.years_experience
            # Score curve: 0-1 years = 10pts, 1-3 = 25pts, 3-5 = 35pts, 5+ = 40pts
            if years >= 5:
                exp_points = 40
            elif years >= 3:
                exp_points = 35
            elif years >= 1:
                exp_points = 25
            else:
                exp_points = 10
            score += exp_points
            breakdown["years_experience"] = exp_points
        else:
            breakdown["years_experience"] = 0

        # Previous employment (15 points)
        if application.previous_employer:
            score += 15
            breakdown["previous_employer"] = 15
        else:
            breakdown["previous_employer"] = 0

        # Job title relevance (15 points)
        if application.job_title:
            # In a real system, match against relevant job titles
            score += 15
            breakdown["job_title"] = 15
        else:
            breakdown["job_title"] = 0

        # Skills (20 points)
        if application.skills:
            # Count number of skills (simple heuristic)
            skills_list = [s.strip() for s in application.skills.split(",")]
            skill_points = min(len(skills_list) * 4, 20)  # 4 points per skill, max 20
            score += skill_points
            breakdown["skills"] = skill_points
        else:
            breakdown["skills"] = 0

        # References (10 points)
        if application.references:
            score += 10
            breakdown["references"] = 10
        else:
            breakdown["references"] = 0

        # Normalize to 0-100
        final_score = (score / max_score) * 100

        logger.info(f"Experience score: {final_score:.2f}/100")

        return {"score": final_score, "breakdown": breakdown}

    def calculate_verification_score(
        self, verification: VerificationState
    ) -> Dict[str, Any]:
        """
        Calculate verification score based on document verification

        Args:
            verification: VerificationState object

        Returns:
            Dictionary with score and breakdown
        """
        score = 0.0
        breakdown = {}

        # ID uploaded (40 points)
        if verification.id_uploaded:
            score += 40
            breakdown["id_uploaded"] = 40
        else:
            breakdown["id_uploaded"] = 0

        # Verification status (60 points)
        if verification.verification_status == "verified":
            score += 60
            breakdown["verification_status"] = 60
        elif verification.verification_status == "pending":
            score += 30
            breakdown["verification_status"] = 30
        else:
            breakdown["verification_status"] = 0

        logger.info(f"Verification score: {score:.2f}/100")

        return {
            "score": score,
            "breakdown": breakdown,
            "verified": verification.verification_status == "verified",
        }

    def calculate_fit_score(
        self,
        qualification: Optional[QualificationState] = None,
        application: Optional[ApplicationState] = None,
        verification: Optional[VerificationState] = None,
    ) -> FitScoreComponents:
        """
        Calculate overall fit score from all components

        Args:
            qualification: QualificationState object
            application: ApplicationState object
            verification: VerificationState object

        Returns:
            FitScoreComponents with all scores and breakdown
        """
        # Calculate individual scores
        qual_result = (
            self.calculate_qualification_score(qualification)
            if qualification
            else {"score": 0, "breakdown": {}}
        )
        exp_result = (
            self.calculate_experience_score(application)
            if application
            else {"score": 0, "breakdown": {}}
        )
        ver_result = (
            self.calculate_verification_score(verification)
            if verification
            else {"score": 0, "breakdown": {}}
        )

        qualification_score = qual_result["score"]
        experience_score = exp_result["score"]
        verification_score = ver_result["score"]

        # Calculate weighted total
        total_score = (
            qualification_score * self.qualification_weight
            + experience_score * self.experience_weight
            + verification_score * self.verification_weight
        )

        # Create detailed breakdown
        breakdown = {
            "qualification": {
                "score": qualification_score,
                "weight": self.qualification_weight,
                "weighted_score": qualification_score * self.qualification_weight,
                "details": qual_result["breakdown"],
            },
            "experience": {
                "score": experience_score,
                "weight": self.experience_weight,
                "weighted_score": experience_score * self.experience_weight,
                "details": exp_result["breakdown"],
            },
            "verification": {
                "score": verification_score,
                "weight": self.verification_weight,
                "weighted_score": verification_score * self.verification_weight,
                "details": ver_result["breakdown"],
            },
        }

        logger.info(f"Total fit score: {total_score:.2f}/100")

        return FitScoreComponents(
            qualification_score=qualification_score,
            experience_score=experience_score,
            verification_score=verification_score,
            total_score=total_score,
            breakdown=breakdown,
        )

    def get_fit_rating(self, fit_score: float) -> str:
        """
        Convert numerical fit score to qualitative rating

        Args:
            fit_score: Numerical score (0-100)

        Returns:
            Qualitative rating string
        """
        if fit_score >= 85:
            return "Excellent"
        elif fit_score >= 70:
            return "Good"
        elif fit_score >= 55:
            return "Fair"
        elif fit_score >= 40:
            return "Below Average"
        else:
            return "Poor"


def main():
    """Example usage of fit score calculator"""
    from chatbot.state.states import (
        ApplicationState,
        QualificationState,
        VerificationState,
    )

    # Create sample states
    qualification = QualificationState(
        session_id="test-123",
        age_confirmed=True,
        work_authorization=True,
        shift_preference="day",
        availability_start="2024-01-15",
        transportation=True,
        hours_preference="full-time",
        qualification_status="qualified",
    )

    application = ApplicationState(
        session_id="test-123",
        full_name="John Doe",
        years_experience=3.5,
        previous_employer="ABC Corp",
        job_title="Warehouse Associate",
        skills="forklift, inventory management, packing",
        references="Available upon request",
    )

    verification = VerificationState(
        session_id="test-123",
        id_uploaded=True,
        id_type="driver_license",
        verification_status="verified",
    )

    # Calculate fit score
    calculator = FitScoreCalculator()
    fit_score = calculator.calculate_fit_score(
        qualification=qualification, application=application, verification=verification
    )

    print(f"\n=== Fit Score Results ===")
    print(f"Qualification Score: {fit_score.qualification_score:.2f}/100")
    print(f"Experience Score: {fit_score.experience_score:.2f}/100")
    print(f"Verification Score: {fit_score.verification_score:.2f}/100")
    print(f"\nTotal Fit Score: {fit_score.total_score:.2f}/100")
    print(f"Rating: {calculator.get_fit_rating(fit_score.total_score)}")

    print(f"\n=== Detailed Breakdown ===")
    import json

    print(json.dumps(fit_score.breakdown, indent=2))


if __name__ == "__main__":
    main()
