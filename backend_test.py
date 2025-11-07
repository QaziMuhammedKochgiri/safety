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
    
    # Print summary
    print_summary()
    
    # Exit with appropriate code
    exit(0 if len(test_results['failed']) == 0 else 1)
