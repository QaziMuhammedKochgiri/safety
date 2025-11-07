from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import shutil

from models import (
    Client, ClientCreate,
    Document, DocumentUpload,
    Consent, ConsentCreate,
    ChatMessage, ChatMessageCreate,
    LandmarkCase,
    ClientRegister, ClientLogin, Token
)
from utils import (
    generate_client_number,
    generate_document_number,
    get_upload_directory,
    sanitize_filename,
    is_allowed_file_type
)
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_client
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
mongo_client = AsyncIOMotorClient(mongo_url)
db = mongo_client[os.environ.get('DB_NAME', 'safechild')]

# File upload configuration
UPLOAD_DIR = Path("/app/backend/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.txt']

# Create the main app without a prefix
app = FastAPI(title="SafeChild Law Firm API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ==================== AUTHENTICATION ====================

@api_router.post("/auth/register", response_model=Token)
async def register_client(client_data: ClientRegister):
    """Register a new client with login credentials"""
    try:
        # Check if email already exists
        existing_client = await db.clients.find_one({"email": client_data.email})
        if existing_client:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Generate client number
        client_number = generate_client_number()
        
        # Hash password
        hashed_password = get_password_hash(client_data.password)
        
        # Create client
        client = Client(
            clientNumber=client_number,
            firstName=client_data.firstName,
            lastName=client_data.lastName,
            email=client_data.email,
            phone=client_data.phone,
            country=client_data.country,
            caseType=client_data.caseType,
            hashedPassword=hashed_password
        )
        
        await db.clients.insert_one(client.dict())
        
        # Create access token
        access_token = create_access_token(
            data={"sub": client_number, "email": client_data.email}
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            clientNumber=client_number,
            email=client_data.email,
            firstName=client_data.firstName,
            lastName=client_data.lastName
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/login", response_model=Token)
async def login_client(credentials: ClientLogin):
    """Login with email and password"""
    try:
        # Find client by email
        client = await db.clients.find_one({"email": credentials.email})
        
        if not client or not client.get("hashedPassword"):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(credentials.password, client["hashedPassword"]):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": client["clientNumber"], "email": client["email"]}
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            clientNumber=client["clientNumber"],
            email=client["email"],
            firstName=client["firstName"],
            lastName=client["lastName"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/auth/me")
async def get_current_user_info(current_client: dict = Depends(get_current_client)):
    """Get current authenticated client info"""
    try:
        client = await db.clients.find_one(
            {"clientNumber": current_client["clientNumber"]},
            {"_id": 0, "hashedPassword": 0}
        )
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        return client
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CLIENT MANAGEMENT ====================

@api_router.post("/clients")
async def create_client(client_data: ClientCreate):
    """Create a new client and generate client number"""
    try:
        client_number = generate_client_number()
        
        # Check if client number already exists (unlikely but safety check)
        existing = await db.clients.find_one({"clientNumber": client_number})
        while existing:
            client_number = generate_client_number()
            existing = await db.clients.find_one({"clientNumber": client_number})
        
        client = Client(
            clientNumber=client_number,
            **client_data.dict()
        )
        
        await db.clients.insert_one(client.dict())
        
        return {
            "success": True,
            "clientNumber": client_number,
            "message": "Client registered successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/clients/{client_number}")
async def get_client(client_number: str):
    """Get client details by client number"""
    client = await db.clients.find_one({"clientNumber": client_number}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@api_router.get("/clients/{client_number}/validate")
async def validate_client_number(client_number: str):
    """Validate if client number exists"""
    client = await db.clients.find_one({"clientNumber": client_number}, {"_id": 0})
    return {
        "valid": client is not None,
        "client": client if client else None
    }

# ==================== DOCUMENT MANAGEMENT ====================

@api_router.post("/documents/upload")
async def upload_document(
    clientNumber: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload document for a client"""
    try:
        # Validate client number
        client = await db.clients.find_one({"clientNumber": clientNumber})
        if not client:
            raise HTTPException(status_code=404, detail="Invalid client number")
        
        # Validate file type
        if not is_allowed_file_type(file.filename, ALLOWED_FILE_TYPES):
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_FILE_TYPES)}"
            )
        
        # Validate file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        # Generate document number and sanitize filename
        doc_number = generate_document_number()
        safe_filename = sanitize_filename(file.filename)
        
        # Create client upload directory
        client_dir = get_upload_directory(clientNumber)
        file_path = Path(client_dir) / f"{doc_number}_{safe_filename}"
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create document record
        document = Document(
            documentNumber=doc_number,
            clientNumber=clientNumber,
            fileName=safe_filename,
            fileSize=file_size,
            fileType=Path(safe_filename).suffix,
            filePath=str(file_path),
            uploadedBy="client"
        )
        
        await db.documents.insert_one(document.dict())
        
        return {
            "success": True,
            "documentNumber": doc_number,
            "fileName": safe_filename,
            "uploadedAt": document.uploadedAt
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/documents/{document_number}/download")
async def download_document(document_number: str):
    """Download document by document number"""
    document = await db.documents.find_one({"documentNumber": document_number}, {"_id": 0})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = Path(document['filePath'])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")
    
    return FileResponse(
        path=file_path,
        filename=document['fileName'],
        media_type='application/octet-stream'
    )

@api_router.get("/documents/client/{client_number}")
async def get_client_documents(client_number: str):
    """Get all documents for a client"""
    documents = await db.documents.find({"clientNumber": client_number}, {"_id": 0}).to_list(100)
    return {"documents": documents}

@api_router.get("/portal/documents")
async def get_my_documents(current_client: dict = Depends(get_current_client)):
    """Get authenticated client's documents (protected route)"""
    try:
        documents = await db.documents.find(
            {"clientNumber": current_client["clientNumber"]},
            {"_id": 0}
        ).to_list(100)
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/portal/documents/upload")
async def upload_my_document(
    file: UploadFile = File(...),
    current_client: dict = Depends(get_current_client)
):
    """Upload document for authenticated client (protected route)"""
    try:
        client_number = current_client["clientNumber"]
        
        # Validate file type
        if not is_allowed_file_type(file.filename, ALLOWED_FILE_TYPES):
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_FILE_TYPES)}"
            )
        
        # Validate file size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        # Generate document number and sanitize filename
        doc_number = generate_document_number()
        safe_filename = sanitize_filename(file.filename)
        
        # Create client upload directory
        client_dir = get_upload_directory(client_number)
        file_path = Path(client_dir) / f"{doc_number}_{safe_filename}"
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create document record
        document = Document(
            documentNumber=doc_number,
            clientNumber=client_number,
            fileName=safe_filename,
            fileSize=file_size,
            fileType=Path(safe_filename).suffix,
            filePath=str(file_path),
            uploadedBy="client"
        )
        
        await db.documents.insert_one(document.dict())
        
        return {
            "success": True,
            "documentNumber": doc_number,
            "fileName": safe_filename,
            "uploadedAt": document.uploadedAt
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CONSENT MANAGEMENT ====================

@api_router.post("/consent")
async def log_consent(consent_data: ConsentCreate, request: Request):
    """Log user consent"""
    try:
        # Get IP address from request
        ip_address = request.client.host
        
        consent = Consent(
            **consent_data.dict(),
            ipAddress=ip_address
        )
        
        await db.consents.insert_one(consent.dict())
        
        return {
            "success": True,
            "consentId": consent.id,
            "timestamp": consent.timestamp
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/consent/{session_id}")
async def get_consent(session_id: str):
    """Get consent details for a session"""
    consent = await db.consents.find_one({"sessionId": session_id}, {"_id": 0})
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")
    return consent

# ==================== CHAT MANAGEMENT ====================

@api_router.post("/chat/message")
async def send_message(message_data: ChatMessageCreate):
    """Send a chat message"""
    try:
        message = ChatMessage(**message_data.dict())
        await db.chat_messages.insert_one(message.dict())
        
        return {
            "success": True,
            "messageId": message.id,
            "timestamp": message.timestamp
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/chat/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    messages = await db.chat_messages.find({"sessionId": session_id}, {"_id": 0}).sort("timestamp", 1).to_list(1000)
    return {"messages": messages}

# ==================== LANDMARK CASES ====================

@api_router.get("/cases/landmark")
async def get_landmark_cases():
    """Get all landmark cases"""
    cases = await db.landmark_cases.find({}, {"_id": 0}).to_list(100)
    return {"cases": cases}

@api_router.get("/cases/landmark/{case_number}")
async def get_landmark_case(case_number: str):
    """Get specific landmark case"""
    case = await db.landmark_cases.find_one({"caseNumber": case_number}, {"_id": 0})
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {
        "message": "SafeChild Law Firm API",
        "status": "operational",
        "version": "1.0.0"
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    mongo_client.close()