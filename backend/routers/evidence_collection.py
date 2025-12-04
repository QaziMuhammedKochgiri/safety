"""
Evidence Collection Router for SafeChild

Provides API endpoints for the Advanced Social Media Evidence Collector
"""

from fastapi import APIRouter, HTTPException, Depends, Body, UploadFile, File
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from .. import get_db
from ..auth import get_current_admin, get_current_user
from ..logging_config import get_logger
from ..forensics.social_evidence_collector import (
    SocialEvidenceCollector,
    ScreenshotCollector,
    Platform,
    EvidenceType,
    EvidenceStatus
)

router = APIRouter(prefix="/evidence", tags=["Evidence Collection"])
logger = get_logger("safechild.evidence")


# =============================================================================
# Request/Response Models
# =============================================================================

class CreateSessionRequest(BaseModel):
    case_id: str
    client_number: str
    platforms: List[str]
    notes: Optional[str] = ""


class StartCollectionRequest(BaseModel):
    platform: str
    options: Optional[dict] = None


class AddEvidenceRequest(BaseModel):
    platform: str
    evidence_type: str
    content: dict
    source_identifier: str
    file_path: Optional[str] = None


class VerifyEvidenceRequest(BaseModel):
    verification_notes: Optional[str] = ""


class ScreenshotRequest(BaseModel):
    platform: str
    source_url: str
    notes: Optional[str] = ""


class ScreenshotUploadMetadata(BaseModel):
    user_agent: Optional[str] = None
    viewport_size: Optional[str] = None
    page_title: Optional[str] = None


# =============================================================================
# Evidence Session Endpoints
# =============================================================================

@router.post("/sessions")
async def create_evidence_session(
    request: CreateSessionRequest,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create a new evidence collection session"""

    collector = SocialEvidenceCollector(db)

    # Validate platforms
    valid_platforms = [p.value for p in Platform]
    for platform in request.platforms:
        if platform not in valid_platforms:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platform: {platform}. Valid options: {valid_platforms}"
            )

    # Verify client exists
    client = await db.clients.find_one({"clientNumber": request.client_number})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    try:
        session = await collector.create_collection_session(
            case_id=request.case_id,
            client_number=request.client_number,
            platforms=request.platforms,
            created_by=current_user.get("email", "admin"),
            notes=request.notes
        )

        logger.info(f"Evidence session created: {session['session_id']}")
        return session

    except Exception as e:
        logger.error(f"Failed to create evidence session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_evidence_sessions(
    case_id: Optional[str] = None,
    client_number: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List evidence collection sessions with optional filters"""

    collector = SocialEvidenceCollector(db)

    sessions = await collector.list_sessions(
        case_id=case_id,
        client_number=client_number,
        status=status,
        limit=limit
    )

    return {"sessions": sessions, "count": len(sessions)}


@router.get("/sessions/{session_id}")
async def get_evidence_session(
    session_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get a specific evidence collection session"""

    collector = SocialEvidenceCollector(db)
    session = await collector.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get evidence summary
    evidence_list = await collector.list_evidence(session_id, limit=1000)

    # Calculate platform breakdown
    platform_breakdown = {}
    for evidence in evidence_list:
        platform = evidence.get("platform")
        if platform not in platform_breakdown:
            platform_breakdown[platform] = {"messages": 0, "media": 0, "other": 0}

        etype = evidence.get("evidence_type")
        if etype == "message":
            platform_breakdown[platform]["messages"] += 1
        elif etype in ["media", "screenshot"]:
            platform_breakdown[platform]["media"] += 1
        else:
            platform_breakdown[platform]["other"] += 1

    session["platform_breakdown"] = platform_breakdown
    session["_id"] = str(session.get("_id", ""))

    return session


@router.post("/sessions/{session_id}/start")
async def start_platform_collection(
    session_id: str,
    request: StartCollectionRequest,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Start evidence collection for a specific platform"""

    collector = SocialEvidenceCollector(db)

    result = await collector.start_platform_collection(
        session_id=session_id,
        platform=request.platform,
        actor=current_user.get("email", "admin"),
        options=request.options or {}
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to start collection")
        )

    logger.info(f"Collection started for {request.platform} in session {session_id}")
    return result


@router.post("/sessions/{session_id}/status")
async def update_session_status(
    session_id: str,
    status: str = Body(..., embed=True),
    notes: str = Body("", embed=True),
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update session status"""

    collector = SocialEvidenceCollector(db)

    try:
        evidence_status = EvidenceStatus(status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Valid options: {[s.value for s in EvidenceStatus]}"
        )

    success = await collector.update_session_status(
        session_id=session_id,
        status=evidence_status,
        actor=current_user.get("email", "admin"),
        notes=notes
    )

    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"success": True, "status": status}


@router.post("/sessions/{session_id}/correlate")
async def correlate_session_contacts(
    session_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Run cross-platform contact correlation"""

    collector = SocialEvidenceCollector(db)

    result = await collector.correlate_contacts(session_id)

    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.post("/sessions/{session_id}/package")
async def generate_evidence_package(
    session_id: str,
    include_ai_analysis: bool = True,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Generate a forensic evidence package for court use"""

    collector = SocialEvidenceCollector(db)

    package = await collector.generate_evidence_package(
        session_id=session_id,
        actor=current_user.get("email", "admin"),
        include_ai_analysis=include_ai_analysis
    )

    if package.get("error"):
        raise HTTPException(status_code=404, detail=package["error"])

    logger.info(f"Evidence package generated: {package.get('package_id')}")
    return package


# =============================================================================
# Evidence Item Endpoints
# =============================================================================

@router.post("/sessions/{session_id}/evidence")
async def add_evidence_item(
    session_id: str,
    request: AddEvidenceRequest,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Add an evidence item to a session"""

    collector = SocialEvidenceCollector(db)

    # Validate evidence type
    try:
        evidence_type = EvidenceType(request.evidence_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid evidence type. Valid options: {[e.value for e in EvidenceType]}"
        )

    evidence = await collector.add_evidence(
        session_id=session_id,
        platform=request.platform,
        evidence_type=request.evidence_type,
        content=request.content,
        source_identifier=request.source_identifier,
        actor=current_user.get("email", "admin"),
        file_path=request.file_path
    )

    return evidence


@router.get("/sessions/{session_id}/evidence")
async def list_session_evidence(
    session_id: str,
    platform: Optional[str] = None,
    evidence_type: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List evidence items for a session"""

    collector = SocialEvidenceCollector(db)

    evidence_list = await collector.list_evidence(
        session_id=session_id,
        platform=platform,
        evidence_type=evidence_type,
        limit=limit
    )

    # Convert ObjectId to string
    for item in evidence_list:
        item["_id"] = str(item.get("_id", ""))

    return {"evidence": evidence_list, "count": len(evidence_list)}


@router.get("/items/{evidence_id}")
async def get_evidence_item(
    evidence_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get a specific evidence item"""

    collector = SocialEvidenceCollector(db)
    evidence = await collector.get_evidence(evidence_id)

    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    evidence["_id"] = str(evidence.get("_id", ""))
    return evidence


@router.post("/items/{evidence_id}/verify")
async def verify_evidence_item(
    evidence_id: str,
    request: VerifyEvidenceRequest,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Mark evidence as verified"""

    collector = SocialEvidenceCollector(db)

    success = await collector.verify_evidence(
        evidence_id=evidence_id,
        actor=current_user.get("email", "admin"),
        verification_notes=request.verification_notes
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Verification failed - evidence not found or hash mismatch"
        )

    return {"success": True, "evidence_id": evidence_id, "verified": True}


# =============================================================================
# Screenshot Endpoints
# =============================================================================

@router.post("/sessions/{session_id}/screenshots")
async def capture_screenshot(
    session_id: str,
    request: ScreenshotRequest,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Initiate a screenshot capture"""

    screenshot_collector = ScreenshotCollector(db)

    record = await screenshot_collector.capture_screenshot(
        session_id=session_id,
        platform=request.platform,
        source_url=request.source_url,
        actor=current_user.get("email", "admin"),
        notes=request.notes
    )

    return record


@router.post("/screenshots/{screenshot_id}/upload")
async def upload_screenshot(
    screenshot_id: str,
    file: UploadFile = File(...),
    user_agent: Optional[str] = None,
    viewport_size: Optional[str] = None,
    page_title: Optional[str] = None,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Upload a screenshot file"""

    screenshot_collector = ScreenshotCollector(db)

    # Read file content
    file_content = await file.read()

    metadata = {
        "user_agent": user_agent,
        "viewport_size": viewport_size,
        "page_title": page_title
    }

    result = await screenshot_collector.upload_screenshot(
        screenshot_id=screenshot_id,
        file_content=file_content,
        metadata=metadata,
        actor=current_user.get("email", "admin")
    )

    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/sessions/{session_id}/screenshots")
async def list_session_screenshots(
    session_id: str,
    platform: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List screenshots for a session"""

    screenshot_collector = ScreenshotCollector(db)

    screenshots = await screenshot_collector.list_screenshots(
        session_id=session_id,
        platform=platform,
        limit=limit
    )

    # Convert ObjectId to string
    for item in screenshots:
        item["_id"] = str(item.get("_id", ""))

    return {"screenshots": screenshots, "count": len(screenshots)}


# =============================================================================
# Dashboard Endpoints
# =============================================================================

@router.get("/dashboard")
async def get_evidence_dashboard(
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get evidence collection dashboard statistics"""

    collector = SocialEvidenceCollector(db)
    stats = await collector.get_dashboard_stats()

    return stats


@router.get("/platforms")
async def get_available_platforms():
    """Get list of available platforms for evidence collection"""

    platforms = [
        {
            "id": Platform.WHATSAPP.value,
            "name": "WhatsApp",
            "icon": "smartphone",
            "color": "green",
            "collection_type": "automated",
            "description": {
                "de": "Automatische Erfassung von WhatsApp-Nachrichten und Medien",
                "en": "Automated collection of WhatsApp messages and media"
            }
        },
        {
            "id": Platform.TELEGRAM.value,
            "name": "Telegram",
            "icon": "send",
            "color": "blue",
            "collection_type": "automated",
            "description": {
                "de": "Automatische Erfassung von Telegram-Nachrichten",
                "en": "Automated collection of Telegram messages"
            }
        },
        {
            "id": Platform.INSTAGRAM.value,
            "name": "Instagram",
            "icon": "camera",
            "color": "pink",
            "collection_type": "manual",
            "description": {
                "de": "Manuelle Erfassung von Instagram DMs, Stories und Posts",
                "en": "Manual collection of Instagram DMs, Stories, and Posts"
            }
        },
        {
            "id": Platform.FACEBOOK.value,
            "name": "Facebook",
            "icon": "users",
            "color": "blue",
            "collection_type": "manual",
            "description": {
                "de": "Manuelle Erfassung von Facebook Messenger und Posts",
                "en": "Manual collection of Facebook Messenger and Posts"
            }
        },
        {
            "id": Platform.TIKTOK.value,
            "name": "TikTok",
            "icon": "video",
            "color": "black",
            "collection_type": "url_archive",
            "description": {
                "de": "Archivierung von TikTok-Videos per URL",
                "en": "Archiving of TikTok videos via URL"
            }
        },
        {
            "id": Platform.EMAIL.value,
            "name": "Email",
            "icon": "mail",
            "color": "gray",
            "collection_type": "manual",
            "description": {
                "de": "Manuelle E-Mail-Erfassung und -Archivierung",
                "en": "Manual email collection and archiving"
            }
        },
        {
            "id": Platform.SMS.value,
            "name": "SMS",
            "icon": "message-square",
            "color": "green",
            "collection_type": "manual",
            "description": {
                "de": "SMS-Nachrichten-Erfassung",
                "en": "SMS message collection"
            }
        }
    ]

    return {"platforms": platforms}


# =============================================================================
# Collection Tasks (for manual collection)
# =============================================================================

@router.get("/tasks")
async def list_collection_tasks(
    session_id: Optional[str] = None,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List manual collection tasks"""

    query = {}
    if session_id:
        query["session_id"] = session_id
    if platform:
        query["platform"] = platform
    if status:
        query["status"] = status

    cursor = db.collection_tasks.find(query).sort("created_at", -1).limit(limit)
    tasks = await cursor.to_list(length=limit)

    for task in tasks:
        task["_id"] = str(task.get("_id", ""))

    return {"tasks": tasks, "count": len(tasks)}


@router.post("/tasks/{task_id}/complete")
async def complete_collection_task(
    task_id: str,
    notes: str = Body("", embed=True),
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Mark a collection task as completed"""

    result = await db.collection_tasks.update_one(
        {"task_id": task_id},
        {
            "$set": {
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
                "completed_by": current_user.get("email", "admin"),
                "completion_notes": notes
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"success": True, "task_id": task_id, "status": "completed"}
