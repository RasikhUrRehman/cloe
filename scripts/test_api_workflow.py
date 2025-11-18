"""
Complete API Workflow Test Script
Tests all API endpoints with a realistic conversation flow
"""

import json
import requests
import time
from typing import Dict, Any
import sys

# API Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_response(response: Any):
    """Print formatted response"""
    if isinstance(response, dict):
        print(f"{Colors.OKBLUE}{json.dumps(response, indent=2)}{Colors.ENDC}")
    else:
        print(f"{Colors.OKBLUE}{response}{Colors.ENDC}")


def test_health_check() -> bool:
    """Test health check endpoint"""
    print_header("TEST 1: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        data = response.json()
        
        print_success(f"Health check passed")
        print_info(f"Status: {data.get('status')}")
        print_info(f"Version: {data.get('version')}")
        print_info(f"Timestamp: {data.get('timestamp')}")
        return True
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False


def test_create_session() -> Dict[str, Any]:
    """Test session creation"""
    print_header("TEST 2: Create Session")
    
    try:
        payload = {
            "job_id": "job_warehouse_001",  # Optional job ID
            "retrieval_method": "hybrid",
            "language": "en"
        }
        
        print_info("Creating session with payload:")
        print_response(payload)
        
        response = requests.post(f"{API_BASE}/session/create", json=payload)
        response.raise_for_status()
        data = response.json()
        
        print_success("Session created successfully")
        print_info(f"Session ID: {data.get('session_id')}")
        print_info(f"Current Stage: {data.get('current_stage')}")
        print_info(f"Initial Message: {data.get('message')}")
        
        return data
    except Exception as e:
        print_error(f"Session creation failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print_error(f"Response: {e.response.text}")
        return {}


def test_chat_engagement(session_id: str) -> bool:
    """Test engagement stage chat"""
    print_header("TEST 3: Engagement Stage Chat")
    
    messages = [
        "Hi, I'm interested in the position",
        "Yes, I'd like to proceed with the application"
    ]
    
    try:
        for i, message in enumerate(messages, 1):
            print_info(f"Message {i}: {message}")
            
            payload = {
                "session_id": session_id,
                "message": message
            }
            
            response = requests.post(f"{API_BASE}/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            
            print_success(f"Response received (Stage: {data.get('current_stage')})")
            
            responses = data.get('responses', [])
            for j, resp in enumerate(responses, 1):
                print(f"{Colors.BOLD}Response {j}:{Colors.ENDC} {resp}\n")
            
            time.sleep(1)  # Simulate natural conversation pace
        
        return True
    except Exception as e:
        print_error(f"Engagement chat failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print_error(f"Response: {e.response.text}")
        return False


def test_chat_qualification(session_id: str) -> bool:
    """Test qualification stage chat"""
    print_header("TEST 4: Qualification Stage Chat")
    
    messages = [
        "Yes, I'm over 18 years old",
        "Yes, I'm authorized to work in the US",
        "I prefer the morning shift",
        "I can start immediately",
        "Yes, I have reliable transportation",
        "I'm looking for full-time work"
    ]
    
    try:
        for i, message in enumerate(messages, 1):
            print_info(f"Message {i}: {message}")
            
            payload = {
                "session_id": session_id,
                "message": message
            }
            
            response = requests.post(f"{API_BASE}/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            
            print_success(f"Response received (Stage: {data.get('current_stage')})")
            
            responses = data.get('responses', [])
            for j, resp in enumerate(responses, 1):
                print(f"{Colors.BOLD}Response {j}:{Colors.ENDC} {resp}\n")
            
            time.sleep(1)
        
        return True
    except Exception as e:
        print_error(f"Qualification chat failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print_error(f"Response: {e.response.text}")
        return False


def test_chat_application(session_id: str) -> bool:
    """Test application stage chat"""
    print_header("TEST 5: Application Stage Chat")
    
    messages = [
        "My name is John Smith",
        "My phone number is 555-123-4567",
        "My email is john.smith@example.com",
        "I have 3 years of experience in warehouse operations"
    ]
    
    try:
        for i, message in enumerate(messages, 1):
            print_info(f"Message {i}: {message}")
            
            payload = {
                "session_id": session_id,
                "message": message
            }
            
            response = requests.post(f"{API_BASE}/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            
            print_success(f"Response received (Stage: {data.get('current_stage')})")
            
            responses = data.get('responses', [])
            for j, resp in enumerate(responses, 1):
                print(f"{Colors.BOLD}Response {j}:{Colors.ENDC} {resp}\n")
            
            time.sleep(1)
        
        return True
    except Exception as e:
        print_error(f"Application chat failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print_error(f"Response: {e.response.text}")
        return False


def test_session_status(session_id: str) -> bool:
    """Test session status endpoint"""
    print_header("TEST 6: Session Status")
    
    try:
        response = requests.get(f"{API_BASE}/session/{session_id}/status")
        response.raise_for_status()
        data = response.json()
        
        print_success("Session status retrieved")
        print_response(data)
        
        return True
    except Exception as e:
        print_error(f"Session status failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print_error(f"Response: {e.response.text}")
        return False


def test_session_details(session_id: str) -> bool:
    """Test session details endpoint"""
    print_header("TEST 7: Session Details")
    
    try:
        response = requests.get(f"{API_BASE}/session/{session_id}")
        response.raise_for_status()
        data = response.json()
        
        print_success("Session details retrieved")
        print_info(f"Session ID: {data.get('session_id')}")
        print_info(f"Current Stage: {data.get('current_stage')}")
        print_info(f"Created At: {data.get('created_at')}")
        print_info(f"Updated At: {data.get('updated_at')}")
        
        # Show status
        status = data.get('status', {})
        print_info(f"Engagement Complete: {status.get('engagement_complete')}")
        print_info(f"Qualification Complete: {status.get('qualification_complete')}")
        print_info(f"Application Complete: {status.get('application_complete')}")
        print_info(f"Ready for Verification: {status.get('ready_for_verification')}")
        
        # Show chat history count
        chat_history = data.get('chat_history', [])
        print_info(f"Chat History: {len(chat_history)} messages")
        
        return True
    except Exception as e:
        print_error(f"Session details failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print_error(f"Response: {e.response.text}")
        return False


def test_get_application(session_id: str) -> bool:
    """Test get application endpoint"""
    print_header("TEST 8: Get Application")
    
    try:
        response = requests.get(f"{API_BASE}/session/{session_id}/application")
        response.raise_for_status()
        data = response.json()
        
        print_success("Application retrieved successfully")
        print_info(f"Session ID: {data.get('session_id')}")
        print_info(f"Status: {data.get('status')}")
        print_info(f"Timestamp: {data.get('timestamp')}")
        
        # Show applicant info
        applicant = data.get('applicant', {})
        if applicant:
            print_info(f"Applicant: {applicant.get('name')} ({applicant.get('email')})")
        
        # Show fit score if available
        fit_score = data.get('fit_score')
        if fit_score:
            print_info(f"Fit Score: {fit_score.get('total_score')}/100 ({fit_score.get('rating')})")
        
        return True
    except Exception as e:
        print_error(f"Get application failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print_error(f"Response: {e.response.text}")
        return False


def test_list_applications() -> bool:
    """Test list applications endpoint"""
    print_header("TEST 9: List Applications")
    
    try:
        response = requests.get(f"{API_BASE}/applications?limit=10&offset=0")
        response.raise_for_status()
        data = response.json()
        
        print_success("Applications list retrieved")
        print_info(f"Total Count: {data.get('total_count')}")
        print_info(f"Limit: {data.get('limit')}")
        print_info(f"Offset: {data.get('offset')}")
        
        applications = data.get('applications', [])
        print_info(f"Applications returned: {len(applications)}")
        
        for i, app in enumerate(applications[:3], 1):  # Show first 3
            print(f"\n{Colors.BOLD}Application {i}:{Colors.ENDC}")
            print(f"  Session ID: {app.get('session_id')}")
            print(f"  Applicant: {app.get('applicant_name')} ({app.get('applicant_email')})")
            print(f"  Job: {app.get('job_title')} at {app.get('company')}")
            print(f"  Status: {app.get('status')}")
            if app.get('fit_score'):
                print(f"  Fit Score: {app.get('fit_score')}/100 ({app.get('rating')})")
        
        return True
    except Exception as e:
        print_error(f"List applications failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print_error(f"Response: {e.response.text}")
        return False


def test_fit_score(session_id: str) -> bool:
    """Test fit score endpoint"""
    print_header("TEST 10: Get Fit Score")
    
    try:
        response = requests.get(f"{API_BASE}/session/{session_id}/fit_score")
        response.raise_for_status()
        data = response.json()
        
        print_success("Fit score retrieved")
        
        fit_score = data.get('fit_score', {})
        print_info(f"Total Score: {fit_score.get('total_score')}/100")
        print_info(f"Rating: {fit_score.get('rating')}")
        print_info(f"Qualification Score: {fit_score.get('qualification_score')}/100")
        print_info(f"Experience Score: {fit_score.get('experience_score')}/100")
        print_info(f"Personality Score: {fit_score.get('personality_score')}/100")
        
        return True
    except Exception as e:
        print_error(f"Get fit score failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print_error(f"Response: {e.response.text}")
        return False


def run_complete_workflow():
    """Run complete API workflow test"""
    print_header("API WORKFLOW TEST SUITE")
    print_info("Testing all API endpoints with realistic conversation flow")
    
    results = {
        "passed": 0,
        "failed": 0,
        "total": 0
    }
    
    # Test 1: Health Check
    results["total"] += 1
    if test_health_check():
        results["passed"] += 1
    else:
        results["failed"] += 1
        print_error("Cannot continue without healthy API")
        return results
    
    time.sleep(1)
    
    # Test 2: Create Session
    results["total"] += 1
    session_data = test_create_session()
    if session_data and session_data.get('session_id'):
        results["passed"] += 1
        session_id = session_data.get('session_id')
    else:
        results["failed"] += 1
        print_error("Cannot continue without session")
        return results
    
    time.sleep(1)
    
    # Test 3: Engagement Stage
    results["total"] += 1
    if test_chat_engagement(session_id):
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    time.sleep(2)
    
    # Test 4: Qualification Stage
    results["total"] += 1
    if test_chat_qualification(session_id):
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    time.sleep(2)
    
    # Test 5: Application Stage
    results["total"] += 1
    if test_chat_application(session_id):
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    time.sleep(2)
    
    # Test 6: Session Status
    results["total"] += 1
    if test_session_status(session_id):
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    time.sleep(1)
    
    # Test 7: Session Details
    results["total"] += 1
    if test_session_details(session_id):
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    time.sleep(1)
    
    # Test 8: Get Application
    results["total"] += 1
    if test_get_application(session_id):
        results["passed"] += 1
    else:
        results["failed"] += 1
        print_warning("Application may not be complete yet. This is expected if conversation didn't finish.")
    
    time.sleep(1)
    
    # Test 9: List Applications
    results["total"] += 1
    if test_list_applications():
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    time.sleep(1)
    
    # Test 10: Fit Score (may fail if application not complete)
    results["total"] += 1
    if test_fit_score(session_id):
        results["passed"] += 1
    else:
        results["failed"] += 1
        print_warning("Fit score may not be available if application is not complete")
    
    # Print summary
    print_header("TEST SUMMARY")
    print_info(f"Total Tests: {results['total']}")
    print_success(f"Passed: {results['passed']}")
    if results['failed'] > 0:
        print_error(f"Failed: {results['failed']}")
    else:
        print_success(f"Failed: {results['failed']}")
    
    success_rate = (results['passed'] / results['total']) * 100 if results['total'] > 0 else 0
    print_info(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print_success("\n🎉 All tests passed!")
    elif success_rate >= 80:
        print_warning("\n⚠️  Most tests passed, but some issues detected")
    else:
        print_error("\n❌ Multiple tests failed")
    
    return results


if __name__ == "__main__":
    try:
        results = run_complete_workflow()
        
        # Exit with appropriate code
        if results['failed'] == 0:
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print_warning("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
