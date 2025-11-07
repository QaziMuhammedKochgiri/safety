"""
Comprehensive Backend API Testing for SafeChild Law Firm
Tests all backend endpoints with success and error scenarios
"""
import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "total": 0
}

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def log_test(test_name, passed, message=""):
    """Log test result"""
    test_results["total"] += 1
    if passed:
        test_results["passed"].append(test_name)
        print(f"{GREEN}✓{RESET} {test_name}")
        if message:
            print(f"  {message}")
    else:
        test_results["failed"].append(test_name)
        print(f"{RED}✗{RESET} {test_name}")
        if message:
            print(f"  {RED}{message}{RESET}")

def print_section(title):
    """Print section header"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

# Store test data
test_data = {
    "client_number": None,
    "document_number": None,
    "session_id": "test_session_123",
    "chat_session_id": "test_chat_456",
    "auth_token": None,
    "auth_client_number": None,
    "meeting_id": None,
    "case_id": None
}

def test_health_check():
    """Test API health check"""
    print_section("1. HEALTH CHECK")
    try:
        response = requests.get(f"{API_BASE}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            log_test("Health Check", True, f"Status: {data.get('status')}, Version: {data.get('version')}")
        else:
            log_test("Health Check", False, f"Status code: {response.status_code}")
    except Exception as e:
        log_test("Health Check", False, str(e))

def test_landmark_cases():
    """Test landmark cases endpoints"""
    print_section("2. LANDMARK CASES API")
    
    # Test GET all landmark cases
    try:
        response = requests.get(f"{API_BASE}/cases/landmark", timeout=10)
        if response.status_code == 200:
            data = response.json()
            cases = data.get('cases', [])
            if len(cases) == 3:
                log_test("GET /api/cases/landmark", True, f"Retrieved {len(cases)} landmark cases")
            else:
                log_test("GET /api/cases/landmark", False, f"Expected 3 cases, got {len(cases)}")
        else:
            log_test("GET /api/cases/landmark", False, f"Status code: {response.status_code}")
    except Exception as e:
        log_test("GET /api/cases/landmark", False, str(e))
    
    # Test GET specific landmark case
    try:
        response = requests.get(f"{API_BASE}/cases/landmark/SC2020-MONASKY", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('caseNumber') == 'SC2020-MONASKY':
                log_test("GET /api/cases/landmark/SC2020-MONASKY", True, f"Retrieved case: {data.get('title', {}).get('en', 'N/A')}")
            else:
                log_test("GET /api/cases/landmark/SC2020-MONASKY", False, "Case number mismatch")
        else:
            log_test("GET /api/cases/landmark/SC2020-MONASKY", False, f"Status code: {response.status_code}")
    except Exception as e:
        log_test("GET /api/cases/landmark/SC2020-MONASKY", False, str(e))
    
    # Test GET non-existent case (error scenario)
    try:
        response = requests.get(f"{API_BASE}/cases/landmark/INVALID-CASE", timeout=10)
        if response.status_code == 404:
            log_test("GET /api/cases/landmark/INVALID-CASE (404 expected)", True, "Correctly returned 404")
        else:
            log_test("GET /api/cases/landmark/INVALID-CASE (404 expected)", False, f"Expected 404, got {response.status_code}")
    except Exception as e:
        log_test("GET /api/cases/landmark/INVALID-CASE (404 expected)", False, str(e))

def test_client_management():
    """Test client management endpoints"""
    print_section("3. CLIENT MANAGEMENT API")
    
    # Test POST create client
    try:
        client_data = {
            "firstName": "Maria",
            "lastName": "Rodriguez",
            "email": "maria.rodriguez@example.com",
            "phone": "+31201234567",
            "country": "Netherlands",
            "caseType": "hague_convention"
        }
        response = requests.post(f"{API_BASE}/clients", json=client_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('clientNumber'):
                test_data['client_number'] = data['clientNumber']
                log_test("POST /api/clients", True, f"Client created: {test_data['client_number']}")
            else:
                log_test("POST /api/clients", False, "Missing success or clientNumber in response")
        else:
            log_test("POST /api/clients", False, f"Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_test("POST /api/clients", False, str(e))
    
    # Test POST create client with invalid email (error scenario)
    try:
        invalid_client = {
            "firstName": "Test",
            "lastName": "User",
            "email": "invalid-email",
            "phone": "+31201234567",
            "country": "Netherlands",
            "caseType": "hague_convention"
        }
        response = requests.post(f"{API_BASE}/clients", json=invalid_client, timeout=10)
        if response.status_code == 422:
            log_test("POST /api/clients (invalid email - 422 expected)", True, "Correctly rejected invalid email")
        else:
            log_test("POST /api/clients (invalid email - 422 expected)", False, f"Expected 422, got {response.status_code}")
    except Exception as e:
        log_test("POST /api/clients (invalid email - 422 expected)", False, str(e))
    
    # Test GET client details
    if test_data['client_number']:
        try:
            response = requests.get(f"{API_BASE}/clients/{test_data['client_number']}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('clientNumber') == test_data['client_number']:
                    log_test(f"GET /api/clients/{test_data['client_number']}", True, f"Retrieved client: {data.get('firstName')} {data.get('lastName')}")
                else:
                    log_test(f"GET /api/clients/{test_data['client_number']}", False, "Client number mismatch")
            else:
                log_test(f"GET /api/clients/{test_data['client_number']}", False, f"Status code: {response.status_code}")
        except Exception as e:
            log_test(f"GET /api/clients/{test_data['client_number']}", False, str(e))
    
    # Test GET non-existent client (error scenario)
    try:
        response = requests.get(f"{API_BASE}/clients/INVALID-CLIENT", timeout=10)
        if response.status_code == 404:
            log_test("GET /api/clients/INVALID-CLIENT (404 expected)", True, "Correctly returned 404")
        else:
            log_test("GET /api/clients/INVALID-CLIENT (404 expected)", False, f"Expected 404, got {response.status_code}")
    except Exception as e:
        log_test("GET /api/clients/INVALID-CLIENT (404 expected)", False, str(e))
    
    # Test validate client number
    if test_data['client_number']:
        try:
            response = requests.get(f"{API_BASE}/clients/{test_data['client_number']}/validate", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('valid') == True:
                    log_test(f"GET /api/clients/{test_data['client_number']}/validate", True, "Client number validated")
                else:
                    log_test(f"GET /api/clients/{test_data['client_number']}/validate", False, "Valid should be True")
            else:
                log_test(f"GET /api/clients/{test_data['client_number']}/validate", False, f"Status code: {response.status_code}")
        except Exception as e:
            log_test(f"GET /api/clients/{test_data['client_number']}/validate", False, str(e))
    
    # Test validate invalid client number
    try:
        response = requests.get(f"{API_BASE}/clients/INVALID-CLIENT/validate", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('valid') == False:
                log_test("GET /api/clients/INVALID-CLIENT/validate (valid=false expected)", True, "Correctly returned valid=false")
            else:
                log_test("GET /api/clients/INVALID-CLIENT/validate (valid=false expected)", False, "Expected valid=false")
        else:
            log_test("GET /api/clients/INVALID-CLIENT/validate (valid=false expected)", False, f"Status code: {response.status_code}")
    except Exception as e:
        log_test("GET /api/clients/INVALID-CLIENT/validate (valid=false expected)", False, str(e))

def test_document_management():
    """Test document upload and download endpoints"""
    print_section("4. DOCUMENT MANAGEMENT API")
    
    if not test_data['client_number']:
        print(f"{YELLOW}⚠ Skipping document tests - no valid client number{RESET}")
        return
    
    # Create a test file
    test_file_path = Path("/tmp/test_document.txt")
    test_file_content = "This is a test document for SafeChild Law Firm API testing.\nClient case documentation."
    test_file_path.write_text(test_file_content)
    
    # Test POST upload document
    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_document.txt', f, 'text/plain')}
            data = {'clientNumber': test_data['client_number']}
            response = requests.post(f"{API_BASE}/documents/upload", files=files, data=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('documentNumber'):
                    test_data['document_number'] = result['documentNumber']
                    log_test("POST /api/documents/upload", True, f"Document uploaded: {test_data['document_number']}")
                else:
                    log_test("POST /api/documents/upload", False, "Missing success or documentNumber in response")
            else:
                log_test("POST /api/documents/upload", False, f"Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_test("POST /api/documents/upload", False, str(e))
    
    # Test POST upload with invalid client number (error scenario)
    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_document.txt', f, 'text/plain')}
            data = {'clientNumber': 'INVALID-CLIENT'}
            response = requests.post(f"{API_BASE}/documents/upload", files=files, data=data, timeout=10)
            
            if response.status_code == 404:
                log_test("POST /api/documents/upload (invalid client - 404 expected)", True, "Correctly rejected invalid client")
            else:
                log_test("POST /api/documents/upload (invalid client - 404 expected)", False, f"Expected 404, got {response.status_code}")
    except Exception as e:
        log_test("POST /api/documents/upload (invalid client - 404 expected)", False, str(e))
    
    # Test POST upload with invalid file type (error scenario)
    try:
        invalid_file_path = Path("/tmp/test_invalid.exe")
        invalid_file_path.write_text("invalid file")
        
        with open(invalid_file_path, 'rb') as f:
            files = {'file': ('test_invalid.exe', f, 'application/octet-stream')}
            data = {'clientNumber': test_data['client_number']}
            response = requests.post(f"{API_BASE}/documents/upload", files=files, data=data, timeout=10)
            
            if response.status_code == 400:
                log_test("POST /api/documents/upload (invalid file type - 400 expected)", True, "Correctly rejected invalid file type")
            else:
                log_test("POST /api/documents/upload (invalid file type - 400 expected)", False, f"Expected 400, got {response.status_code}")
        
        invalid_file_path.unlink()
    except Exception as e:
        log_test("POST /api/documents/upload (invalid file type - 400 expected)", False, str(e))
    
    # Test GET download document
    if test_data['document_number']:
        try:
            response = requests.get(f"{API_BASE}/documents/{test_data['document_number']}/download", timeout=10)
            if response.status_code == 200:
                if len(response.content) > 0:
                    log_test(f"GET /api/documents/{test_data['document_number']}/download", True, f"Downloaded {len(response.content)} bytes")
                else:
                    log_test(f"GET /api/documents/{test_data['document_number']}/download", False, "Empty file content")
            else:
                log_test(f"GET /api/documents/{test_data['document_number']}/download", False, f"Status code: {response.status_code}")
        except Exception as e:
            log_test(f"GET /api/documents/{test_data['document_number']}/download", False, str(e))
    
    # Test GET download non-existent document (error scenario)
    try:
        response = requests.get(f"{API_BASE}/documents/INVALID-DOC/download", timeout=10)
        if response.status_code == 404:
            log_test("GET /api/documents/INVALID-DOC/download (404 expected)", True, "Correctly returned 404")
        else:
            log_test("GET /api/documents/INVALID-DOC/download (404 expected)", False, f"Expected 404, got {response.status_code}")
    except Exception as e:
        log_test("GET /api/documents/INVALID-DOC/download (404 expected)", False, str(e))
    
    # Test GET client documents
    try:
        response = requests.get(f"{API_BASE}/documents/client/{test_data['client_number']}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            documents = data.get('documents', [])
            if len(documents) > 0:
                log_test(f"GET /api/documents/client/{test_data['client_number']}", True, f"Retrieved {len(documents)} document(s)")
            else:
                log_test(f"GET /api/documents/client/{test_data['client_number']}", False, "No documents found")
        else:
            log_test(f"GET /api/documents/client/{test_data['client_number']}", False, f"Status code: {response.status_code}")
    except Exception as e:
        log_test(f"GET /api/documents/client/{test_data['client_number']}", False, str(e))
    
    # Cleanup
    test_file_path.unlink()

def test_consent_logging():
    """Test consent logging endpoints"""
    print_section("5. CONSENT LOGGING API")
    
    # Test POST log consent (BUG FIX VERIFICATION - ipAddress should NOT be in request body)
    try:
        consent_data = {
            "sessionId": test_data['session_id'],
            "permissions": {
                "location": True,
                "browser": True,
                "camera": False,
                "files": True,
                "forensic": True
            },
            "userAgent": "Mozilla/5.0 (Test Browser)"
            # NOTE: ipAddress is NOT included - server extracts it from request
        }
        response = requests.post(f"{API_BASE}/consent", json=consent_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('consentId'):
                log_test("POST /api/consent (BUG FIX VERIFIED)", True, f"Consent logged: {data['consentId']}")
            else:
                log_test("POST /api/consent (BUG FIX VERIFIED)", False, "Missing success or consentId in response")
        else:
            log_test("POST /api/consent (BUG FIX VERIFIED)", False, f"Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_test("POST /api/consent (BUG FIX VERIFIED)", False, str(e))
    
    # Test POST consent with missing fields (error scenario)
    try:
        invalid_consent = {
            "sessionId": "test_invalid",
            "permissions": {
                "location": True
            }
            # Missing required fields
        }
        response = requests.post(f"{API_BASE}/consent", json=invalid_consent, timeout=10)
        if response.status_code == 422:
            log_test("POST /api/consent (missing fields - 422 expected)", True, "Correctly rejected incomplete data")
        else:
            log_test("POST /api/consent (missing fields - 422 expected)", False, f"Expected 422, got {response.status_code}")
    except Exception as e:
        log_test("POST /api/consent (missing fields - 422 expected)", False, str(e))
    
    # Test GET consent
    try:
        response = requests.get(f"{API_BASE}/consent/{test_data['session_id']}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('sessionId') == test_data['session_id']:
                log_test(f"GET /api/consent/{test_data['session_id']}", True, "Retrieved consent data")
            else:
                log_test(f"GET /api/consent/{test_data['session_id']}", False, "Session ID mismatch")
        else:
            log_test(f"GET /api/consent/{test_data['session_id']}", False, f"Status code: {response.status_code}")
    except Exception as e:
        log_test(f"GET /api/consent/{test_data['session_id']}", False, str(e))
    
    # Test GET non-existent consent (error scenario)
    try:
        response = requests.get(f"{API_BASE}/consent/INVALID-SESSION", timeout=10)
        if response.status_code == 404:
            log_test("GET /api/consent/INVALID-SESSION (404 expected)", True, "Correctly returned 404")
        else:
            log_test("GET /api/consent/INVALID-SESSION (404 expected)", False, f"Expected 404, got {response.status_code}")
    except Exception as e:
        log_test("GET /api/consent/INVALID-SESSION (404 expected)", False, str(e))

def test_chat_messages():
    """Test chat message endpoints"""
    print_section("6. CHAT MESSAGES API")
    
    # Test POST send message
    try:
        message_data = {
            "sessionId": test_data['chat_session_id'],
            "sender": "client",
            "message": "Hello, I need help with my child custody case. Can you assist me?"
        }
        response = requests.post(f"{API_BASE}/chat/message", json=message_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('messageId'):
                log_test("POST /api/chat/message", True, f"Message sent: {data['messageId']}")
            else:
                log_test("POST /api/chat/message", False, "Missing success or messageId in response")
        else:
            log_test("POST /api/chat/message", False, f"Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_test("POST /api/chat/message", False, str(e))
    
    # Test POST another message
    try:
        message_data = {
            "sessionId": test_data['chat_session_id'],
            "sender": "bot",
            "message": "Hello! I'm here to help. Can you tell me more about your situation?"
        }
        response = requests.post(f"{API_BASE}/chat/message", json=message_data, timeout=10)
        if response.status_code == 200:
            log_test("POST /api/chat/message (second message)", True, "Second message sent")
        else:
            log_test("POST /api/chat/message (second message)", False, f"Status code: {response.status_code}")
    except Exception as e:
        log_test("POST /api/chat/message (second message)", False, str(e))
    
    # Test POST message with missing fields (error scenario)
    try:
        invalid_message = {
            "sessionId": "test_invalid",
            "sender": "client"
            # Missing message field
        }
        response = requests.post(f"{API_BASE}/chat/message", json=invalid_message, timeout=10)
        if response.status_code == 422:
            log_test("POST /api/chat/message (missing fields - 422 expected)", True, "Correctly rejected incomplete data")
        else:
            log_test("POST /api/chat/message (missing fields - 422 expected)", False, f"Expected 422, got {response.status_code}")
    except Exception as e:
        log_test("POST /api/chat/message (missing fields - 422 expected)", False, str(e))
    
    # Test GET chat history
    try:
        response = requests.get(f"{API_BASE}/chat/{test_data['chat_session_id']}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            messages = data.get('messages', [])
            if len(messages) >= 2:
                log_test(f"GET /api/chat/{test_data['chat_session_id']}", True, f"Retrieved {len(messages)} message(s)")
            else:
                log_test(f"GET /api/chat/{test_data['chat_session_id']}", False, f"Expected at least 2 messages, got {len(messages)}")
        else:
            log_test(f"GET /api/chat/{test_data['chat_session_id']}", False, f"Status code: {response.status_code}")
    except Exception as e:
        log_test(f"GET /api/chat/{test_data['chat_session_id']}", False, str(e))
    
    # Test GET chat history for non-existent session
    try:
        response = requests.get(f"{API_BASE}/chat/INVALID-SESSION", timeout=10)
        if response.status_code == 200:
            data = response.json()
            messages = data.get('messages', [])
            if len(messages) == 0:
                log_test("GET /api/chat/INVALID-SESSION (empty array expected)", True, "Correctly returned empty array")
            else:
                log_test("GET /api/chat/INVALID-SESSION (empty array expected)", False, f"Expected empty array, got {len(messages)} messages")
        else:
            log_test("GET /api/chat/INVALID-SESSION (empty array expected)", False, f"Status code: {response.status_code}")
    except Exception as e:
        log_test("GET /api/chat/INVALID-SESSION (empty array expected)", False, str(e))

def test_authentication():
    """Test authentication endpoints and get token for protected routes"""
    print_section("7. AUTHENTICATION API")
    
    # Test POST register client
    try:
        register_data = {
            "firstName": "Sarah",
            "lastName": "Johnson",
            "email": f"sarah.johnson.{datetime.now().timestamp()}@example.com",
            "phone": "+31612345678",
            "country": "Netherlands",
            "caseType": "custody_dispute",
            "password": "SecurePassword123!"
        }
        response = requests.post(f"{API_BASE}/auth/register", json=register_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('access_token') and data.get('clientNumber'):
                test_data['auth_token'] = data['access_token']
                test_data['auth_client_number'] = data['clientNumber']
                log_test("POST /api/auth/register", True, f"Client registered: {test_data['auth_client_number']}")
            else:
                log_test("POST /api/auth/register", False, "Missing access_token or clientNumber in response")
        else:
            log_test("POST /api/auth/register", False, f"Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_test("POST /api/auth/register", False, str(e))
    
    # Test POST register with duplicate email (error scenario)
    if test_data['auth_token']:
        try:
            duplicate_data = {
                "firstName": "Test",
                "lastName": "Duplicate",
                "email": register_data['email'],  # Same email
                "phone": "+31612345679",
                "country": "Netherlands",
                "caseType": "custody_dispute",
                "password": "Password123!"
            }
            response = requests.post(f"{API_BASE}/auth/register", json=duplicate_data, timeout=10)
            if response.status_code == 400:
                log_test("POST /api/auth/register (duplicate email - 400 expected)", True, "Correctly rejected duplicate email")
            else:
                log_test("POST /api/auth/register (duplicate email - 400 expected)", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            log_test("POST /api/auth/register (duplicate email - 400 expected)", False, str(e))
    
    # Test GET /auth/me (protected route)
    if test_data['auth_token']:
        try:
            headers = {"Authorization": f"Bearer {test_data['auth_token']}"}
            response = requests.get(f"{API_BASE}/auth/me", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('clientNumber') == test_data['auth_client_number']:
                    log_test("GET /api/auth/me (protected)", True, f"Retrieved authenticated user info")
                else:
                    log_test("GET /api/auth/me (protected)", False, "Client number mismatch")
            else:
                log_test("GET /api/auth/me (protected)", False, f"Status code: {response.status_code}")
        except Exception as e:
            log_test("GET /api/auth/me (protected)", False, str(e))

def test_video_meetings():
    """Test video meeting endpoints"""
    print_section("8. VIDEO MEETINGS API (NEW)")
    
    if not test_data['auth_token']:
        print(f"{YELLOW}⚠ Skipping meeting tests - no authentication token{RESET}")
        return
    
    headers = {"Authorization": f"Bearer {test_data['auth_token']}"}
    
    # Test POST create meeting
    try:
        from datetime import datetime, timedelta
        scheduled_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
        
        meeting_data = {
            "title": "Initial Custody Consultation",
            "description": "Discuss child custody case and legal options",
            "scheduledTime": scheduled_time,
            "duration": 60,
            "meetingType": "consultation"
        }
        response = requests.post(f"{API_BASE}/meetings/create", json=meeting_data, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('meetingId') and data.get('roomName'):
                test_data['meeting_id'] = data['meetingId']
                log_test("POST /api/meetings/create", True, f"Meeting created: {test_data['meeting_id']}, Room: {data['roomName']}")
            else:
                log_test("POST /api/meetings/create", False, "Missing success, meetingId, or roomName in response")
        else:
            log_test("POST /api/meetings/create", False, f"Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_test("POST /api/meetings/create", False, str(e))
    
    # Test POST create meeting without auth (error scenario)
    try:
        meeting_data = {
            "title": "Test Meeting",
            "duration": 30,
            "meetingType": "consultation"
        }
        response = requests.post(f"{API_BASE}/meetings/create", json=meeting_data, timeout=10)
        if response.status_code == 401 or response.status_code == 403:
            log_test("POST /api/meetings/create (no auth - 401/403 expected)", True, "Correctly rejected unauthenticated request")
        else:
            log_test("POST /api/meetings/create (no auth - 401/403 expected)", False, f"Expected 401/403, got {response.status_code}")
    except Exception as e:
        log_test("POST /api/meetings/create (no auth - 401/403 expected)", False, str(e))
    
    # Test GET my meetings
    try:
        response = requests.get(f"{API_BASE}/meetings/my-meetings", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            meetings = data.get('meetings', [])
            if len(meetings) > 0:
                log_test("GET /api/meetings/my-meetings", True, f"Retrieved {len(meetings)} meeting(s)")
            else:
                log_test("GET /api/meetings/my-meetings", False, "No meetings found")
        else:
            log_test("GET /api/meetings/my-meetings", False, f"Status code: {response.status_code}")
    except Exception as e:
        log_test("GET /api/meetings/my-meetings", False, str(e))
    
    # Test GET my meetings with status filter
    try:
        response = requests.get(f"{API_BASE}/meetings/my-meetings?status=scheduled", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            meetings = data.get('meetings', [])
            log_test("GET /api/meetings/my-meetings?status=scheduled", True, f"Retrieved {len(meetings)} scheduled meeting(s)")
        else:
            log_test("GET /api/meetings/my-meetings?status=scheduled", False, f"Status code: {response.status_code}")
    except Exception as e:
        log_test("GET /api/meetings/my-meetings?status=scheduled", False, str(e))
    
    # Test GET specific meeting details
    if test_data['meeting_id']:
        try:
            response = requests.get(f"{API_BASE}/meetings/{test_data['meeting_id']}", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('meetingId') == test_data['meeting_id']:
                    log_test(f"GET /api/meetings/{test_data['meeting_id']}", True, f"Retrieved meeting details")
                else:
                    log_test(f"GET /api/meetings/{test_data['meeting_id']}", False, "Meeting ID mismatch")
            else:
                log_test(f"GET /api/meetings/{test_data['meeting_id']}", False, f"Status code: {response.status_code}")
        except Exception as e:
            log_test(f"GET /api/meetings/{test_data['meeting_id']}", False, str(e))
    
    # Test GET non-existent meeting (error scenario)
    try:
        response = requests.get(f"{API_BASE}/meetings/INVALID-MEETING", headers=headers, timeout=10)
        if response.status_code == 404:
            log_test("GET /api/meetings/INVALID-MEETING (404 expected)", True, "Correctly returned 404")
        else:
            log_test("GET /api/meetings/INVALID-MEETING (404 expected)", False, f"Expected 404, got {response.status_code}")
    except Exception as e:
        log_test("GET /api/meetings/INVALID-MEETING (404 expected)", False, str(e))
    
    # Test PATCH update meeting status to in_progress
    if test_data['meeting_id']:
        try:
            response = requests.patch(
                f"{API_BASE}/meetings/{test_data['meeting_id']}/status?status=in_progress",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    log_test(f"PATCH /api/meetings/{test_data['meeting_id']}/status (in_progress)", True, "Status updated to in_progress")
                else:
                    log_test(f"PATCH /api/meetings/{test_data['meeting_id']}/status (in_progress)", False, "Missing success in response")
            else:
                log_test(f"PATCH /api/meetings/{test_data['meeting_id']}/status (in_progress)", False, f"Status code: {response.status_code}")
        except Exception as e:
            log_test(f"PATCH /api/meetings/{test_data['meeting_id']}/status (in_progress)", False, str(e))
    
    # Test DELETE meeting while in_progress (should fail)
    if test_data['meeting_id']:
        try:
            response = requests.delete(f"{API_BASE}/meetings/{test_data['meeting_id']}", headers=headers, timeout=10)
            if response.status_code == 400:
                log_test(f"DELETE /api/meetings/{test_data['meeting_id']} (in_progress - 400 expected)", True, "Correctly prevented deletion of in_progress meeting")
            else:
                log_test(f"DELETE /api/meetings/{test_data['meeting_id']} (in_progress - 400 expected)", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            log_test(f"DELETE /api/meetings/{test_data['meeting_id']} (in_progress - 400 expected)", False, str(e))
    
    # Test PATCH update meeting status to completed
    if test_data['meeting_id']:
        try:
            response = requests.patch(
                f"{API_BASE}/meetings/{test_data['meeting_id']}/status?status=completed",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                log_test(f"PATCH /api/meetings/{test_data['meeting_id']}/status (completed)", True, "Status updated to completed")
            else:
                log_test(f"PATCH /api/meetings/{test_data['meeting_id']}/status (completed)", False, f"Status code: {response.status_code}")
        except Exception as e:
            log_test(f"PATCH /api/meetings/{test_data['meeting_id']}/status (completed)", False, str(e))
    
    # Test PATCH with invalid status (error scenario)
    if test_data['meeting_id']:
        try:
            response = requests.patch(
                f"{API_BASE}/meetings/{test_data['meeting_id']}/status?status=invalid_status",
                headers=headers,
                timeout=10
            )
            if response.status_code == 400:
                log_test(f"PATCH /api/meetings/{test_data['meeting_id']}/status (invalid status - 400 expected)", True, "Correctly rejected invalid status")
            else:
                log_test(f"PATCH /api/meetings/{test_data['meeting_id']}/status (invalid status - 400 expected)", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            log_test(f"PATCH /api/meetings/{test_data['meeting_id']}/status (invalid status - 400 expected)", False, str(e))
    
    # Test DELETE meeting (should succeed now that it's completed)
    if test_data['meeting_id']:
        try:
            response = requests.delete(f"{API_BASE}/meetings/{test_data['meeting_id']}", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    log_test(f"DELETE /api/meetings/{test_data['meeting_id']}", True, "Meeting deleted successfully")
                else:
                    log_test(f"DELETE /api/meetings/{test_data['meeting_id']}", False, "Missing success in response")
            else:
                log_test(f"DELETE /api/meetings/{test_data['meeting_id']}", False, f"Status code: {response.status_code}")
        except Exception as e:
            log_test(f"DELETE /api/meetings/{test_data['meeting_id']}", False, str(e))

def test_forensics():
    """Test forensic analysis endpoints"""
    print_section("9. FORENSICS API")
    
    if not test_data['auth_token']:
        print(f"{YELLOW}⚠ Skipping forensics tests - no authentication token{RESET}")
        return
    
    headers = {"Authorization": f"Bearer {test_data['auth_token']}"}
    
    # Create a test forensic file (.db file)
    test_file_path = Path("/tmp/test_forensic.db")
    test_file_content = b"SQLite format 3\x00" + b"Test forensic database content for analysis" * 100
    test_file_path.write_bytes(test_file_content)
    
    # Test POST start forensic analysis
    try:
        with open(test_file_path, 'rb') as f:
            files = {'backup_file': ('whatsapp_msgstore.db', f, 'application/x-sqlite3')}
            response = requests.post(f"{API_BASE}/forensics/analyze", files=files, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('case_id'):
                    test_data['case_id'] = data['case_id']
                    log_test("POST /api/forensics/analyze", True, f"Analysis started: {test_data['case_id']}")
                else:
                    log_test("POST /api/forensics/analyze", False, "Missing success or case_id in response")
            else:
                log_test("POST /api/forensics/analyze", False, f"Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_test("POST /api/forensics/analyze", False, str(e))
    
    # Test POST with invalid file type (error scenario)
    try:
        invalid_file_path = Path("/tmp/test_invalid_forensic.txt")
        invalid_file_path.write_text("Invalid file type")
        
        with open(invalid_file_path, 'rb') as f:
            files = {'backup_file': ('invalid.txt', f, 'text/plain')}
            response = requests.post(f"{API_BASE}/forensics/analyze", files=files, headers=headers, timeout=10)
            
            if response.status_code == 400:
                log_test("POST /api/forensics/analyze (invalid file type - 400 expected)", True, "Correctly rejected invalid file type")
            else:
                log_test("POST /api/forensics/analyze (invalid file type - 400 expected)", False, f"Expected 400, got {response.status_code}")
        
        invalid_file_path.unlink()
    except Exception as e:
        log_test("POST /api/forensics/analyze (invalid file type - 400 expected)", False, str(e))
    
    # Test POST without auth (error scenario)
    try:
        with open(test_file_path, 'rb') as f:
            files = {'backup_file': ('test.db', f, 'application/x-sqlite3')}
            response = requests.post(f"{API_BASE}/forensics/analyze", files=files, timeout=10)
            
            if response.status_code == 401 or response.status_code == 403:
                log_test("POST /api/forensics/analyze (no auth - 401/403 expected)", True, "Correctly rejected unauthenticated request")
            else:
                log_test("POST /api/forensics/analyze (no auth - 401/403 expected)", False, f"Expected 401/403, got {response.status_code}")
    except Exception as e:
        log_test("POST /api/forensics/analyze (no auth - 401/403 expected)", False, str(e))
    
    # Test GET forensic status
    if test_data['case_id']:
        try:
            import time
            time.sleep(2)  # Wait a bit for processing to start
            
            response = requests.get(f"{API_BASE}/forensics/status/{test_data['case_id']}", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('case_id') == test_data['case_id'] and data.get('status'):
                    log_test(f"GET /api/forensics/status/{test_data['case_id']}", True, f"Status: {data['status']}")
                else:
                    log_test(f"GET /api/forensics/status/{test_data['case_id']}", False, "Missing case_id or status in response")
            else:
                log_test(f"GET /api/forensics/status/{test_data['case_id']}", False, f"Status code: {response.status_code}")
        except Exception as e:
            log_test(f"GET /api/forensics/status/{test_data['case_id']}", False, str(e))
    
    # Test GET status for non-existent case (error scenario)
    try:
        response = requests.get(f"{API_BASE}/forensics/status/INVALID-CASE", headers=headers, timeout=10)
        if response.status_code == 404:
            log_test("GET /api/forensics/status/INVALID-CASE (404 expected)", True, "Correctly returned 404")
        else:
            log_test("GET /api/forensics/status/INVALID-CASE (404 expected)", False, f"Expected 404, got {response.status_code}")
    except Exception as e:
        log_test("GET /api/forensics/status/INVALID-CASE (404 expected)", False, str(e))
    
    # Test GET my cases
    try:
        response = requests.get(f"{API_BASE}/forensics/my-cases", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            cases = data.get('cases', [])
            if len(cases) > 0:
                log_test("GET /api/forensics/my-cases", True, f"Retrieved {len(cases)} case(s)")
            else:
                log_test("GET /api/forensics/my-cases", False, "No cases found")
        else:
            log_test("GET /api/forensics/my-cases", False, f"Status code: {response.status_code}")
    except Exception as e:
        log_test("GET /api/forensics/my-cases", False, str(e))
    
    # Test GET report (may not be ready yet, but test the endpoint)
    if test_data['case_id']:
        try:
            response = requests.get(f"{API_BASE}/forensics/report/{test_data['case_id']}", headers=headers, timeout=10)
            if response.status_code == 200:
                log_test(f"GET /api/forensics/report/{test_data['case_id']}", True, f"Report downloaded ({len(response.content)} bytes)")
            elif response.status_code == 400:
                # Analysis not completed yet - this is expected
                log_test(f"GET /api/forensics/report/{test_data['case_id']} (not ready yet)", True, "Analysis still processing (expected)")
            else:
                log_test(f"GET /api/forensics/report/{test_data['case_id']}", False, f"Status code: {response.status_code}")
        except Exception as e:
            log_test(f"GET /api/forensics/report/{test_data['case_id']}", False, str(e))
    
    # Test DELETE case while processing (should fail)
    if test_data['case_id']:
        try:
            response = requests.delete(f"{API_BASE}/forensics/case/{test_data['case_id']}", headers=headers, timeout=10)
            if response.status_code == 400:
                log_test(f"DELETE /api/forensics/case/{test_data['case_id']} (processing - 400 expected)", True, "Correctly prevented deletion of processing case")
            elif response.status_code == 200:
                # Case might have completed or failed quickly
                log_test(f"DELETE /api/forensics/case/{test_data['case_id']}", True, "Case deleted (was not processing)")
            else:
                log_test(f"DELETE /api/forensics/case/{test_data['case_id']}", False, f"Status code: {response.status_code}")
        except Exception as e:
            log_test(f"DELETE /api/forensics/case/{test_data['case_id']}", False, str(e))
    
    # Cleanup
    test_file_path.unlink()

def print_summary():
    """Print test summary"""
    print_section("TEST SUMMARY")
    total = test_results['total']
    passed = len(test_results['passed'])
    failed = len(test_results['failed'])
    
    print(f"\nTotal Tests: {total}")
    print(f"{GREEN}Passed: {passed}{RESET}")
    print(f"{RED}Failed: {failed}{RESET}")
    
    if failed > 0:
        print(f"\n{RED}Failed Tests:{RESET}")
        for test in test_results['failed']:
            print(f"  {RED}✗{RESET} {test}")
    
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"\n{BLUE}Success Rate: {success_rate:.1f}%{RESET}")
    
    if failed == 0:
        print(f"\n{GREEN}🎉 All tests passed!{RESET}")
    else:
        print(f"\n{YELLOW}⚠ Some tests failed. Please review the errors above.{RESET}")

if __name__ == "__main__":
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}SafeChild Law Firm - Backend API Testing{RESET}")
    print(f"{BLUE}Backend URL: {BACKEND_URL}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    # Run all tests
    test_health_check()
    test_landmark_cases()
    test_client_management()
    test_document_management()
    test_consent_logging()
    test_chat_messages()
    test_authentication()
    test_video_meetings()
    test_forensics()
    
    # Print summary
    print_summary()
    
    # Exit with appropriate code
    exit(0 if len(test_results['failed']) == 0 else 1)
