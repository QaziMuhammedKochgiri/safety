"""
Evidence Request (Magic Link) Router for SafeChild
Handles creation and processing of secure evidence upload links
"""
from fastapi import APIRouter, HTTPException, Depends, Body, UploadFile, File, BackgroundTasks
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid
from pathlib import Path
import os

from .. import get_db
from ..auth import get_current_admin
from ..models import EvidenceRequest
from ..routers.forensics import run_forensic_analysis_task
from ..security_service import security_service
from ..email_service import EmailService
from ..logging_config import get_logger

router = APIRouter(prefix="/requests", tags=["Evidence Requests"])
logger = get_logger("safechild.requests")


class CreateRequestModel(BaseModel):
    client_number: str
    case_id: Optional[str] = None
    request_type: str = "upload"  # upload, consent, info
    scenario_type: Optional[str] = "standard"  # standard, elderly, chat_only
    expiry_days: int = 7
    notes: Optional[str] = ""

@router.post("/create")
async def create_evidence_request(
    request: CreateRequestModel,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create a new evidence request link"""
    
    # Check if client exists
    client = await db.clients.find_one({"clientNumber": request.client_number})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    # Generate unique token
    token = secrets.token_urlsafe(32)
    
    # Calculate expiry
    expires_at = datetime.utcnow() + timedelta(days=request.expiry_days)
    
    request_record = {
        "client_number": request.client_number,
        "case_id": request.case_id,
        "request_type": request.request_type,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": expires_at.isoformat(),
        "token": token,
        "scenario_type": request.scenario_type,
        "created_by": current_user.get("email"),
        "notes": request.notes
    }
    
    await db.evidence_requests.insert_one(request_record)
    
    # Generate link
    base_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
    
    # Use short URL for mobile collection
    if request.request_type == "mobile_collection":
        link = f"{base_url}/c/{token}"
    else:
        link = f"{base_url}/upload-request/{token}"
    
    return {
        "success": True, 
        "link": link,
        "token": token,
        "expires_at": expires_at.isoformat(),
        "scenario_type": request.scenario_type
    }


@router.get("/list")
async def list_evidence_requests(
    current_user: dict = Depends(get_current_admin),
    status: str = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    List all evidence requests (admin only).
    Optional filter by status: pending, completed, expired
    """
    query = {}
    if status:
        if status == "expired":
            query["expiresAt"] = {"$lt": datetime.utcnow()}
        else:
            query["status"] = status
            query["expiresAt"] = {"$gte": datetime.utcnow()}

    requests_cursor = db.evidence_requests.find(
        query,
        {"_id": 0}
    ).sort("createdAt", -1).limit(100)

    requests_list = await requests_cursor.to_list(length=None)

    return {"requests": requests_list, "total": len(requests_list)}


@router.get("/{token}")
async def get_request_details(
    token: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Public endpoint for the client to see what is requested.
    No login required, Token is the key.
    """
    req = await db.evidence_requests.find_one({"token": token})
    if not req:
        raise HTTPException(status_code=404, detail="Invalid or expired link.")

    if req["expiresAt"] < datetime.utcnow():
        raise HTTPException(status_code=410, detail="This link has expired.")

    return {
        "clientName": req.get("clientName", "Valued Client"),
        "requestedTypes": req["requestedTypes"],
        "status": req["status"],
        "expiresAt": req["expiresAt"].isoformat(),
        "uploadCount": req.get("uploadCount", 0)
    }


@router.post("/{token}/upload")
async def upload_requested_evidence(
    token: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Public upload endpoint secured by Token.
    """
    req = await db.evidence_requests.find_one({"token": token})
    if not req:
        raise HTTPException(status_code=404, detail="Invalid link.")

    if req["expiresAt"] < datetime.utcnow():
        raise HTTPException(status_code=410, detail="This link has expired.")

    # Process the file
    case_id = f"REQ_{req['clientNumber']}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    upload_dir = Path("/tmp/forensics_uploads")
    upload_dir.mkdir(exist_ok=True, parents=True)

    file_path = upload_dir / f"{case_id}_{file.filename}.enc"

    content = await file.read()
    file_size = len(content)

    # Encrypt the file
    encryption_result = security_service.encrypt_file(content)
    with open(file_path, "wb") as buffer:
        buffer.write(encryption_result['encrypted_data'])

    encryption_metadata = {k: v for k, v in encryption_result.items() if k != 'encrypted_data'}

    # Determine analysis type based on extension
    file_ext = Path(file.filename).suffix.lower()
    forensic_extensions = ['.db', '.tar', '.gz', '.tgz', '.ab', '.zip', '.sqlite', '.sqlite3']
    analysis_type = "forensic_parsing" if file_ext in forensic_extensions else "direct_evidence"

    # Chain of Custody entry
    coc_event = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow(),
        "actor": f"Client (via Magic Link): {req['clientNumber']}",
        "action": "EVIDENCE_UPLOAD_MAGIC_LINK",
        "details": f"File uploaded via magic link. Token: {token[:8]}..., File: {file.filename}",
        "hashAtEvent": None
    }

    analysis_record = {
        "case_id": case_id,
        "client_number": req["clientNumber"],
        "client_email": req.get("clientEmail", ""),
        "request_token": token,
        "status": "processing",
        "analysis_type": analysis_type,
        "uploaded_file": str(file_path),
        "file_name": file.filename,
        "file_size": file_size,
        "encryption_metadata": encryption_metadata,
        "chain_of_custody": [coc_event],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    await db.forensic_analyses.insert_one(analysis_record)

    # Update request record
    await db.evidence_requests.update_one(
        {"token": token},
        {
            "$set": {
                "status": "uploaded",
                "lastUploadAt": datetime.utcnow()
            },
            "$inc": {"uploadCount": 1}
        }
    )

    logger.info(f"Evidence uploaded via magic link", extra={"extra_fields": {
        "case_id": case_id,
        "client_number": req["clientNumber"],
        "file_name": file.filename,
        "file_size": file_size
    }})

    # Get client info for background task
    client = await db.clients.find_one({"clientNumber": req["clientNumber"]})
    client_info = {
        "clientNumber": req["clientNumber"],
        "email": client.get("email") if client else req.get("clientEmail", ""),
        "firstName": client.get("firstName", "") if client else "",
        "lastName": client.get("lastName", "") if client else ""
    }

    # Start forensic analysis in background
    background_tasks.add_task(
        run_forensic_analysis_task,
        file_path,
        encryption_metadata,
        case_id,
        client_info,
        db
    )

    return {
        "success": True,
        "message": "File uploaded successfully. Analysis in progress.",
        "case_id": case_id
    }


@router.delete("/{token}")
async def revoke_evidence_request(
    token: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Revoke/delete an evidence request (admin only).
    """
    result = await db.evidence_requests.delete_one({"token": token})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Request not found")

    logger.info(f"Evidence request revoked", extra={"extra_fields": {
        "token_prefix": token[:8],
        "revoked_by": current_user.get("clientNumber", "admin")
    }})

    return {"success": True, "message": "Evidence request revoked"}


# =============================================================================
# Social Media Connection Links (WhatsApp/Telegram)
# =============================================================================

@router.post("/social/create")
async def create_social_connection_request(
    data: dict = Body(...),
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Admin creates a secure link for client to connect their WhatsApp/Telegram.
    Data: {
        "clientNumber": "SC2025001",
        "platforms": ["whatsapp", "telegram"],  # which platforms to allow
        "sendEmail": true
    }
    """
    client_number = data.get("clientNumber")
    if not client_number:
        raise HTTPException(status_code=400, detail="clientNumber is required")

    # Get client info
    client = await db.clients.find_one({"clientNumber": client_number})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Generate secure token
    token = uuid.uuid4().hex

    request_record = {
        "id": str(uuid.uuid4()),
        "token": token,
        "type": "social_connection",
        "clientNumber": client_number,
        "clientEmail": client.get("email"),
        "clientName": f"{client.get('firstName', '')} {client.get('lastName', '')}".strip(),
        "lawyerId": str(current_user.get("clientNumber", "admin")),
        "platforms": data.get("platforms", ["whatsapp", "telegram"]),
        "status": "pending",
        "expiresAt": datetime.utcnow() + timedelta(hours=24),  # 24 hour expiry
        "createdAt": datetime.utcnow(),
        "connectedPlatforms": [],
        "extractedData": []
    }

    await db.social_connection_requests.insert_one(request_record)

    # Build the connection link
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
    connection_link = f"{frontend_url}/connect-social/{token}"

    logger.info(f"Social connection link created for client {client_number}", extra={"extra_fields": {
        "client_number": client_number,
        "token_prefix": token[:8],
        "platforms": request_record["platforms"]
    }})

    # Send email notification if requested
    if data.get("sendEmail", False) and client.get("email"):
        try:
            # Use generic email for now - can be customized later
            email_result = EmailService.send_magic_link_email(
                recipient_email=client.get("email"),
                recipient_name=request_record["clientName"] or "Valued Client",
                magic_link=connection_link,
                requested_types=["WhatsApp/Telegram Connection"],
                expires_at=request_record["expiresAt"]
            )
            if email_result.get("success"):
                logger.info(f"Social connection email sent to {client.get('email')}")
        except Exception as e:
            logger.error(f"Error sending social connection email: {e}")

    return {
        "success": True,
        "connection_link": connection_link,
        "token": token,
        "platforms": request_record["platforms"],
        "expiresAt": request_record["expiresAt"].isoformat()
    }


@router.get("/social/{token}")
async def get_social_connection_details(
    token: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Public endpoint for client to see connection request details.
    No login required - token is the key.
    """
    req = await db.social_connection_requests.find_one({"token": token})
    if not req:
        raise HTTPException(status_code=404, detail="Invalid or expired link.")

    if req["expiresAt"] < datetime.utcnow():
        raise HTTPException(status_code=410, detail="This link has expired.")

    return {
        "clientNumber": req["clientNumber"],
        "clientName": req.get("clientName", "Valued Client"),
        "platforms": req["platforms"],
        "status": req["status"],
        "expiresAt": req["expiresAt"].isoformat(),
        "connectedPlatforms": req.get("connectedPlatforms", [])
    }


@router.post("/social/{token}/complete")
async def mark_social_connection_complete(
    token: str,
    data: dict = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Called when social media extraction is complete.
    Data: {
        "platform": "whatsapp",
        "sessionId": "wa_xxx",
        "messageCount": 100,
        "chatCount": 50
    }
    """
    req = await db.social_connection_requests.find_one({"token": token})
    if not req:
        raise HTTPException(status_code=404, detail="Invalid token.")

    platform = data.get("platform")
    extraction_info = {
        "platform": platform,
        "sessionId": data.get("sessionId"),
        "messageCount": data.get("messageCount", 0),
        "chatCount": data.get("chatCount", 0),
        "completedAt": datetime.utcnow()
    }

    # Update the request
    await db.social_connection_requests.update_one(
        {"token": token},
        {
            "$addToSet": {"connectedPlatforms": platform},
            "$push": {"extractedData": extraction_info},
            "$set": {"status": "completed", "updatedAt": datetime.utcnow()}
        }
    )

    logger.info(f"Social connection completed", extra={"extra_fields": {
        "token_prefix": token[:8],
        "platform": platform,
        "message_count": extraction_info["messageCount"]
    }})

    return {"success": True, "message": f"{platform} data extracted successfully"}
