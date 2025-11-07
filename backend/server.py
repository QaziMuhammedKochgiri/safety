from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form, Request, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
import shutil
import uuid

from models import (
    Client, ClientCreate,
    Document, DocumentUpload,
    Consent, ConsentCreate,
    ChatMessage, ChatMessageCreate,
    LandmarkCase,
    ClientRegister, ClientLogin, Token,
    Meeting, MeetingCreate
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
    get_current_client,
    get_current_admin
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
            data={"sub": client_number, "email": client_data.email, "role": "client"}
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
            data={
                "sub": client["clientNumber"], 
                "email": client["email"],
                "role": client.get("role", "client")
            }
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

# ==================== PAYMENT (STRIPE) ====================

from payment import create_consultation_checkout, get_checkout_status, handle_webhook
from pydantic import BaseModel

class CheckoutRequest(BaseModel):
    origin_url: str

@api_router.post("/payment/create-checkout")
async def create_checkout(
    request_data: CheckoutRequest,
    current_client: dict = Depends(get_current_client)
):
    """
    Create Stripe Checkout session for legal consultation
    Amount is defined on backend for security
    """
    try:
        result = await create_consultation_checkout(
            client_number=current_client["clientNumber"],
            client_email=current_client["email"],
            origin_url=request_data.origin_url,
            package_id="consultation"
        )
        
        if result["success"]:
            # Create payment transaction record
            payment_transaction = {
                "transaction_id": result["session_id"],
                "session_id": result["session_id"],
                "client_number": current_client["clientNumber"],
                "client_email": current_client["email"],
                "amount": result["amount"],
                "currency": result["currency"],
                "payment_status": "pending",
                "status": "initiated",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "metadata": {
                    "package_id": "consultation",
                    "service": "legal_consultation"
                }
            }
            await db.payment_transactions.insert_one(payment_transaction)
            
            return {
                "url": result["url"],
                "session_id": result["session_id"]
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Payment creation failed"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/payment/checkout/status/{session_id}")
async def check_checkout_status(
    session_id: str,
    current_client: dict = Depends(get_current_client)
):
    """
    Poll checkout session status
    Handles status updates and prevents duplicate processing
    """
    try:
        # Get status from Stripe
        result = await get_checkout_status(session_id)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Status check failed"))
        
        # Update payment transaction in database
        transaction = await db.payment_transactions.find_one({"session_id": session_id})
        
        if transaction:
            # Only update if status has changed to prevent duplicate processing
            if transaction.get("payment_status") != result["payment_status"]:
                update_data = {
                    "payment_status": result["payment_status"],
                    "status": result["status"],
                    "updated_at": datetime.utcnow()
                }
                
                # If payment is successful, mark as completed
                if result["payment_status"] == "paid" and transaction.get("payment_status") != "paid":
                    update_data["completed_at"] = datetime.utcnow()
                    # Here you can add logic to grant access to consultation, etc.
                
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": update_data}
                )
        
        return {
            "status": result["status"],
            "payment_status": result["payment_status"],
            "amount": result["amount_total"],
            "currency": result["currency"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events
    """
    try:
        payload = await request.body()
        signature = request.headers.get("Stripe-Signature", "")
        
        result = await handle_webhook(payload, signature)
        
        if result["success"]:
            # Update payment transaction based on webhook event
            session_id = result.get("session_id")
            if session_id:
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "payment_status": result["payment_status"],
                        "webhook_received": True,
                        "webhook_event_type": result["event_type"],
                        "updated_at": datetime.utcnow()
                    }}
                )
            
            return {"status": "success"}
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Webhook processing failed"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== FORENSICS ====================

from forensics.engine import SafeChildForensicsEngine

# Initialize forensics engine
forensics_engine = SafeChildForensicsEngine()

# Background task to run forensic analysis
async def run_forensic_analysis_task(
    file_path: Path,
    case_id: str,
    client_info: dict
):
    """Background task to run forensic analysis"""
    try:
        print(f"[Background Task] Starting analysis for {case_id}")
        
        result = await forensics_engine.analyze_android_backup(
            file_path,
            case_id,
            client_info
        )
        
        if result["success"]:
            # Update database with results
            await db.forensic_analyses.update_one(
                {"case_id": case_id},
                {"$set": {
                    "status": "completed",
                    "completed_at": datetime.utcnow(),
                    "report_txt": result.get("report_pdf"),  # Actually .txt for now
                    "report_html": result.get("report_html"),
                    "file_hash": result.get("file_hash"),
                    "statistics": result.get("statistics"),
                    "updated_at": datetime.utcnow()
                }}
            )
            print(f"[Background Task] ✅ Analysis completed: {case_id}")
        else:
            # Update with error
            await db.forensic_analyses.update_one(
                {"case_id": case_id},
                {"$set": {
                    "status": "failed",
                    "error": result.get("error"),
                    "updated_at": datetime.utcnow()
                }}
            )
            print(f"[Background Task] ❌ Analysis failed: {case_id}")
            
    except Exception as e:
        print(f"[Background Task] ❌ Exception: {str(e)}")
        await db.forensic_analyses.update_one(
            {"case_id": case_id},
            {"$set": {
                "status": "failed",
                "error": str(e),
                "updated_at": datetime.utcnow()
            }}
        )

@api_router.post("/forensics/analyze")
async def start_forensic_analysis(
    backup_file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_client: dict = Depends(get_current_client)
):
    """
    Upload device backup and start forensic analysis
    
    Supports:
    - .db files (WhatsApp msgstore.db, Telegram cache4.db, etc.)
    - .tar archives (Android backup)
    - .ab files (Android Backup format)
    
    Analysis runs in background, check status with /forensics/status/{case_id}
    """
    try:
        # Generate unique case ID
        case_id = f"CASE_{current_client['clientNumber']}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Validate file type
        file_ext = Path(backup_file.filename).suffix.lower()
        allowed_extensions = ['.db', '.tar', '.gz', '.tgz', '.ab', '.zip']
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save uploaded file
        upload_dir = Path("/tmp/forensics_uploads")
        upload_dir.mkdir(exist_ok=True, parents=True)
        
        file_path = upload_dir / f"{case_id}_{backup_file.filename}"
        
        with open(file_path, "wb") as buffer:
            content = await backup_file.read()
            buffer.write(content)
        
        file_size = len(content)
        
        print(f"[API] File uploaded: {file_path} ({file_size} bytes)")
        
        # Create forensic analysis record
        analysis_record = {
            "case_id": case_id,
            "client_number": current_client["clientNumber"],
            "client_email": current_client["email"],
            "status": "processing",
            "uploaded_file": str(file_path),
            "file_name": backup_file.filename,
            "file_size": file_size,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.forensic_analyses.insert_one(analysis_record)
        
        print(f"[API] Analysis record created: {case_id}")
        
        # Start analysis in background
        background_tasks.add_task(
            run_forensic_analysis_task,
            file_path,
            case_id,
            {
                "clientNumber": current_client["clientNumber"],
                "email": current_client["email"],
                "firstName": current_client.get("firstName", ""),
                "lastName": current_client.get("lastName", "")
            }
        )
        
        print(f"[API] Background task scheduled: {case_id}")
        
        return {
            "success": True,
            "case_id": case_id,
            "message": "Forensic analysis started. You will be notified when complete.",
            "estimated_time": "5-15 minutes",
            "status_url": f"/api/forensics/status/{case_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/forensics/status/{case_id}")
async def get_forensic_status(
    case_id: str,
    current_client: dict = Depends(get_current_client)
):
    """
    Get forensic analysis status
    
    Returns:
    - status: "processing", "completed", or "failed"
    - progress information
    - statistics (if completed)
    """
    try:
        analysis = await db.forensic_analyses.find_one({
            "case_id": case_id,
            "client_number": current_client["clientNumber"]
        }, {"_id": 0})
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Case not found")
        
        response = {
            "case_id": case_id,
            "status": analysis["status"],
            "file_name": analysis.get("file_name"),
            "file_size": analysis.get("file_size"),
            "created_at": analysis["created_at"],
            "updated_at": analysis["updated_at"]
        }
        
        if analysis["status"] == "completed":
            response["completed_at"] = analysis.get("completed_at")
            response["statistics"] = analysis.get("statistics", {})
            response["report_available"] = True
        elif analysis["status"] == "failed":
            response["error"] = analysis.get("error")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/forensics/report/{case_id}")
async def download_forensic_report(
    case_id: str,
    format: str = "txt",  # txt, html, pdf
    current_client: dict = Depends(get_current_client)
):
    """
    Download forensic report
    
    Formats:
    - txt: Plain text report (default)
    - html: HTML report (coming soon)
    - pdf: PDF report (coming soon)
    """
    try:
        analysis = await db.forensic_analyses.find_one({
            "case_id": case_id,
            "client_number": current_client["clientNumber"]
        })
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Case not found")
        
        if analysis["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Analysis not completed yet. Current status: {analysis['status']}"
            )
        
        # Get report path based on format
        report_key = f"report_{format}"
        report_path = analysis.get(report_key)
        
        if not report_path:
            report_path = analysis.get("report_txt")  # Fallback to txt
            format = "txt"
        
        if not report_path or not Path(report_path).exists():
            raise HTTPException(status_code=404, detail=f"Report file not found")
        
        # Determine media type
        media_types = {
            "txt": "text/plain",
            "html": "text/html",
            "pdf": "application/pdf"
        }
        
        return FileResponse(
            report_path,
            media_type=media_types.get(format, "text/plain"),
            filename=f"SafeChild_Report_{case_id}.{format}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/forensics/my-cases")
async def get_my_forensic_cases(
    current_client: dict = Depends(get_current_client),
    skip: int = 0,
    limit: int = 50
):
    """
    Get all forensic cases for current client
    
    Returns list of cases with status and statistics
    """
    try:
        cases = await db.forensic_analyses.find(
            {"client_number": current_client["clientNumber"]},
            {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        return {
            "total": len(cases),
            "cases": cases
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/forensics/case/{case_id}")
async def delete_forensic_case(
    case_id: str,
    current_client: dict = Depends(get_current_client)
):
    """
    Delete forensic case and associated files
    
    Only completed or failed cases can be deleted
    """
    try:
        analysis = await db.forensic_analyses.find_one({
            "case_id": case_id,
            "client_number": current_client["clientNumber"]
        })
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Case not found")
        
        if analysis["status"] == "processing":
            raise HTTPException(
                status_code=400,
                detail="Cannot delete case while processing"
            )
        
        # Delete files
        if analysis.get("uploaded_file"):
            try:
                Path(analysis["uploaded_file"]).unlink(missing_ok=True)
            except:
                pass
        
        if analysis.get("report_txt"):
            try:
                Path(analysis["report_txt"]).unlink(missing_ok=True)
            except:
                pass
        
        # Delete from database
        await db.forensic_analyses.delete_one({"case_id": case_id})
        
        return {"success": True, "message": "Case deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ADMIN PANEL ====================

@api_router.get("/admin/clients")
async def admin_get_all_clients(
    current_admin: dict = Depends(get_current_admin),
    skip: int = 0,
    limit: int = 100
):
    """Get all clients (admin only)"""
    try:
        clients = await db.clients.find(
            {},
            {"_id": 0, "hashedPassword": 0}
        ).skip(skip).limit(limit).to_list(limit)
        
        total = await db.clients.count_documents({})
        
        return {
            "clients": clients,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin/clients/{client_number}")
async def admin_get_client_details(
    client_number: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Get detailed client info including documents (admin only)"""
    try:
        client = await db.clients.find_one(
            {"clientNumber": client_number},
            {"_id": 0, "hashedPassword": 0}
        )
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get client's documents
        documents = await db.documents.find(
            {"clientNumber": client_number},
            {"_id": 0}
        ).to_list(100)
        
        # Get client's chat messages
        chat_messages = await db.chat_messages.find(
            {"clientNumber": client_number},
            {"_id": 0}
        ).sort("timestamp", -1).to_list(50)
        
        return {
            "client": client,
            "documents": documents,
            "chatMessages": chat_messages
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/admin/clients/{client_number}")
async def admin_update_client(
    client_number: str,
    update_data: dict,
    current_admin: dict = Depends(get_current_admin)
):
    """Update client information (admin only)"""
    try:
        # Remove fields that shouldn't be updated
        update_data.pop("clientNumber", None)
        update_data.pop("hashedPassword", None)
        update_data.pop("createdAt", None)
        update_data["updatedAt"] = datetime.utcnow()
        
        result = await db.clients.update_one(
            {"clientNumber": client_number},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Client not found")
        
        return {"success": True, "message": "Client updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/admin/clients/{client_number}")
async def admin_delete_client(
    client_number: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Delete client (admin only) - soft delete by setting status to 'deleted'"""
    try:
        result = await db.clients.update_one(
            {"clientNumber": client_number},
            {"$set": {"status": "deleted", "updatedAt": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Client not found")
        
        return {"success": True, "message": "Client deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin/documents")
async def admin_get_all_documents(
    current_admin: dict = Depends(get_current_admin),
    skip: int = 0,
    limit: int = 100
):
    """Get all documents (admin only)"""
    try:
        documents = await db.documents.find(
            {},
            {"_id": 0}
        ).skip(skip).limit(limit).to_list(limit)
        
        total = await db.documents.count_documents({})
        
        return {
            "documents": documents,
            "total": total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin/consents")
async def admin_get_all_consents(
    current_admin: dict = Depends(get_current_admin),
    skip: int = 0,
    limit: int = 100
):
    """Get all consent logs (admin only)"""
    try:
        consents = await db.consents.find(
            {},
            {"_id": 0}
        ).skip(skip).limit(limit).to_list(limit)
        
        total = await db.consents.count_documents({})
        
        return {
            "consents": consents,
            "total": total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin/stats")
async def admin_get_statistics(
    current_admin: dict = Depends(get_current_admin)
):
    """Get dashboard statistics (admin only)"""
    try:
        total_clients = await db.clients.count_documents({"role": "client"})
        active_clients = await db.clients.count_documents({"status": "active", "role": "client"})
        total_documents = await db.documents.count_documents({})
        total_consents = await db.consents.count_documents({})
        total_messages = await db.chat_messages.count_documents({})
        
        # Recent clients (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_clients = await db.clients.count_documents({
            "createdAt": {"$gte": seven_days_ago},
            "role": "client"
        })
        
        return {
            "totalClients": total_clients,
            "activeClients": active_clients,
            "totalDocuments": total_documents,
            "totalConsents": total_consents,
            "totalMessages": total_messages,
            "recentClients": recent_clients
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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