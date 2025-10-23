"""
Mock Verification Service
Simulates ID verification API for demonstration purposes
"""
import random
import time
from typing import Dict, Any, Optional
from datetime import datetime
from utils import setup_logging, get_current_timestamp

logger = setup_logging()


class MockVerificationService:
    """Mock verification service for ID verification"""
    
    def __init__(self, success_rate: float = 0.9, delay_seconds: float = 1.0):
        """
        Initialize mock verification service
        
        Args:
            success_rate: Probability of successful verification (0.0 to 1.0)
            delay_seconds: Simulated API delay
        """
        self.success_rate = success_rate
        self.delay_seconds = delay_seconds
    
    def verify_id(
        self,
        id_type: str,
        id_data: Dict[str, Any],
        applicant_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simulate ID verification
        
        Args:
            id_type: Type of ID (driver_license, passport, state_id)
            id_data: ID document data (in real system, this would be extracted from image)
            applicant_info: Applicant information to cross-reference
        
        Returns:
            Verification result dictionary
        """
        logger.info(f"Starting verification for ID type: {id_type}")
        
        # Simulate API delay
        time.sleep(self.delay_seconds)
        
        # Simulate verification process
        is_successful = random.random() < self.success_rate
        
        result = {
            'verification_id': self._generate_verification_id(),
            'timestamp': get_current_timestamp(),
            'id_type': id_type,
            'status': 'verified' if is_successful else 'failed',
            'confidence_score': random.uniform(0.85, 0.99) if is_successful else random.uniform(0.3, 0.6),
            'checks_performed': [
                'document_authenticity',
                'photo_match',
                'data_extraction',
                'expiration_check',
                'watchlist_screening'
            ],
            'details': {}
        }
        
        if is_successful:
            result['details'] = {
                'document_valid': True,
                'photo_match_score': random.uniform(0.9, 0.99),
                'expiration_status': 'valid',
                'document_number': self._generate_document_number(id_type),
                'issuing_authority': self._get_issuing_authority(id_type),
                'watchlist_clear': True
            }
            logger.info(f"Verification successful: {result['verification_id']}")
        else:
            # Simulate random failure reasons
            failure_reasons = [
                'document_quality_insufficient',
                'photo_match_below_threshold',
                'document_expired',
                'information_mismatch',
                'image_quality_too_low'
            ]
            result['details'] = {
                'failure_reason': random.choice(failure_reasons),
                'retry_allowed': True,
                'suggestions': 'Please ensure document is clear, not expired, and photo is visible'
            }
            logger.warning(f"Verification failed: {result['details']['failure_reason']}")
        
        return result
    
    def verify_background_check(
        self,
        applicant_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simulate background check
        
        Args:
            applicant_info: Applicant information
        
        Returns:
            Background check result
        """
        logger.info("Starting background check")
        
        # Simulate longer processing time
        time.sleep(self.delay_seconds * 2)
        
        # Simulate high success rate for background checks
        is_clear = random.random() < 0.95
        
        result = {
            'check_id': self._generate_verification_id(),
            'timestamp': get_current_timestamp(),
            'status': 'clear' if is_clear else 'review_required',
            'checks_completed': [
                'criminal_record',
                'employment_verification',
                'education_verification',
                'reference_check'
            ],
            'details': {}
        }
        
        if is_clear:
            result['details'] = {
                'criminal_record': 'clear',
                'employment_verified': True,
                'education_verified': True,
                'references_contacted': 2,
                'references_positive': 2,
                'overall_assessment': 'approved'
            }
        else:
            result['details'] = {
                'review_reason': 'Additional verification needed for previous employment',
                'action_required': 'Manual review by HR',
                'estimated_completion': '2-3 business days'
            }
        
        logger.info(f"Background check complete: {result['status']}")
        return result
    
    def _generate_verification_id(self) -> str:
        """Generate mock verification ID"""
        import uuid
        return f"VER-{uuid.uuid4().hex[:12].upper()}"
    
    def _generate_document_number(self, id_type: str) -> str:
        """Generate mock document number"""
        if id_type == 'driver_license':
            return f"DL{random.randint(100000, 999999)}"
        elif id_type == 'passport':
            return f"P{random.randint(10000000, 99999999)}"
        elif id_type == 'state_id':
            return f"ID{random.randint(100000, 999999)}"
        else:
            return f"DOC{random.randint(100000, 999999)}"
    
    def _get_issuing_authority(self, id_type: str) -> str:
        """Get mock issuing authority"""
        if id_type == 'driver_license':
            states = ['CA', 'NY', 'TX', 'FL', 'IL', 'PA', 'OH']
            return f"{random.choice(states)} DMV"
        elif id_type == 'passport':
            return "U.S. Department of State"
        elif id_type == 'state_id':
            states = ['CA', 'NY', 'TX', 'FL', 'IL', 'PA', 'OH']
            return f"{random.choice(states)} State"
        else:
            return "Unknown"


class VerificationIntegration:
    """Integration layer for verification services"""
    
    def __init__(self, use_mock: bool = True):
        """
        Initialize verification integration
        
        Args:
            use_mock: Whether to use mock service (True) or real API (False)
        """
        self.use_mock = use_mock
        
        if use_mock:
            self.service = MockVerificationService()
            logger.info("Using mock verification service")
        else:
            # In production, initialize real API client here
            logger.info("Real verification service not implemented")
            raise NotImplementedError("Real verification API not configured")
    
    def verify_applicant(
        self,
        id_type: str,
        id_image_path: Optional[str] = None,
        applicant_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Verify applicant identity
        
        Args:
            id_type: Type of ID document
            id_image_path: Path to ID image (not used in mock)
            applicant_data: Applicant information
        
        Returns:
            Verification result
        """
        # In real implementation, extract data from ID image
        id_data = {
            'document_type': id_type,
            'image_path': id_image_path
        }
        
        return self.service.verify_id(
            id_type=id_type,
            id_data=id_data,
            applicant_info=applicant_data or {}
        )
    
    def run_background_check(
        self,
        applicant_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run background check on applicant
        
        Args:
            applicant_data: Applicant information
        
        Returns:
            Background check result
        """
        return self.service.verify_background_check(applicant_data)


def main():
    """Test verification service"""
    print("\n" + "="*60)
    print("MOCK VERIFICATION SERVICE TEST")
    print("="*60 + "\n")
    
    # Initialize verification
    verification = VerificationIntegration(use_mock=True)
    
    # Test ID verification
    print("Testing ID Verification...")
    applicant = {
        'full_name': 'John Doe',
        'date_of_birth': '1990-05-15',
        'address': '123 Main St, City, ST 12345'
    }
    
    result = verification.verify_applicant(
        id_type='driver_license',
        applicant_data=applicant
    )
    
    print(f"\nVerification ID: {result['verification_id']}")
    print(f"Status: {result['status']}")
    print(f"Confidence Score: {result['confidence_score']:.2%}")
    print(f"\nDetails:")
    for key, value in result['details'].items():
        print(f"  {key}: {value}")
    
    # Test background check
    print("\n" + "-"*60)
    print("\nTesting Background Check...")
    
    bg_result = verification.run_background_check(applicant)
    
    print(f"\nCheck ID: {bg_result['check_id']}")
    print(f"Status: {bg_result['status']}")
    print(f"\nChecks Completed:")
    for check in bg_result['checks_completed']:
        print(f"  • {check}")
    print(f"\nDetails:")
    for key, value in bg_result['details'].items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*60)
    print("✓ Verification service test complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
