"""
iOS Forensics Router for SafeChild
Handles iOS backup analysis endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Depends, Form
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import shutil
import os
import uuid
import zipfile
import tempfile
import json
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from .. import get_db
from ..auth import get_current_admin
from backend.forensics.parsers.ios_backup import iOSBackupParser, detect_ios_backup
from backend.forensics.analyzers import AIForensicAnalyzer, ChildSafetyRiskAssessor
from backend.security_service import security_service
import logging

router = APIRouter(prefix="/forensics/ios", tags=["iOS Forensics"])
logger = logging.getLogger(__name__)

# Initialize AI analyzer
ai_analyzer = AIForensicAnalyzer()
child_safety_assessor = ChildSafetyRiskAssessor(ai_analyzer)


class iOSAnalysisRequest(BaseModel):
    client_number: str
    backup_path: Optional[str] = None
    include_ai_analysis: bool = True
    language: str = "de"


class iOSAnalysisResponse(BaseModel):
    case_id: str
    status: str
    device_info: dict
    message_count: int
    contact_count: int
    call_count: int
    whatsapp_count: int


@router.post("/upload-backup")
async def upload_ios_backup(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    client_number: str = Form(...),
    include_ai_analysis: bool = Form(True),
    language: str = Form("de"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """
    Upload and analyze an iOS backup ZIP file.

    The ZIP should contain an unencrypted iTunes/Finder backup with:
    - Manifest.db
    - Info.plist
    - Status.plist (optional)
    - Files in 2-char hash directories
    """

    # Validate file type
    if not file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=400,
            detail="File must be a ZIP archive containing iOS backup"
        )

    # Generate case ID
    case_id = f"IOS_{client_number}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    # Create temp directory for extraction
    temp_dir = tempfile.mkdtemp(prefix=f"ios_backup_{case_id}_")
    backup_path = Path(temp_dir) / "backup"

    try:
        # Save uploaded file
        zip_path = Path(temp_dir) / file.filename
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extract ZIP
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(backup_path)

        # Find the actual backup directory (might be nested)
        actual_backup_path = find_backup_root(backup_path)

        if not actual_backup_path:
            raise HTTPException(
                status_code=400,
                detail="Invalid iOS backup: Manifest.db not found in archive"
            )

        # Parse the backup
        parser = iOSBackupParser(str(actual_backup_path))

        # Extract all data
        result = parser.extract_all(str(Path(temp_dir) / "extracted"))

        # Create chain of custody record
        coc_event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "actor": f"Admin: {admin.get('email', 'unknown')}",
            "action": "IOS_BACKUP_UPLOAD",
            "details": f"iOS backup uploaded for analysis. Device: {result['device_info'].get('device_name', 'Unknown')}",
            "file_hash": security_service.generate_hash(open(zip_path, 'rb').read())
        }

        # Prepare analysis record
        analysis_record = {
            "case_id": case_id,
            "client_number": client_number,
            "status": "completed",
            "analysis_type": "ios_backup",
            "device_info": result['device_info'],
            "extraction_summary": {
                "sms_count": len(result.get('sms', [])),
                "contacts_count": len(result.get('contacts', [])),
                "calls_count": len(result.get('call_history', [])),
                "whatsapp_count": len(result.get('whatsapp', []))
            },
            "chain_of_custody": [coc_event],
            "created_at": datetime.utcnow(),
            "created_by": admin.get('email', 'unknown')
        }

        # Store messages for analysis
        all_messages = []

        # Add SMS/iMessage
        for sms in result.get('sms', []):
            all_messages.append({
                "platform": "ios_sms",
                "text": sms.get('text', ''),
                "timestamp": sms.get('timestamp'),
                "is_from_me": sms.get('is_from_me', False),
                "contact": sms.get('phone_number', 'Unknown')
            })

        # Add WhatsApp
        for wa in result.get('whatsapp', []):
            all_messages.append({
                "platform": "whatsapp_ios",
                "text": wa.get('text', ''),
                "timestamp": wa.get('timestamp'),
                "is_from_me": wa.get('is_from_me', False),
                "contact": wa.get('contact_name') or wa.get('phone_number', 'Unknown')
            })

        analysis_record["messages"] = all_messages
        analysis_record["contacts"] = result.get('contacts', [])
        analysis_record["call_history"] = result.get('call_history', [])

        # Run AI analysis if requested
        if include_ai_analysis and all_messages:
            try:
                # Prepare text for AI analysis
                message_texts = [m.get('text', '') for m in all_messages if m.get('text')]

                if message_texts:
                    ai_result = await ai_analyzer.analyze_messages(
                        messages=message_texts[:500],  # Limit for API
                        language=language
                    )

                    analysis_record["ai_analysis"] = ai_result

                    # Child safety assessment
                    safety_result = await child_safety_assessor.assess_risk(
                        messages=message_texts[:500],
                        context={
                            "device_type": "ios",
                            "message_count": len(all_messages)
                        }
                    )

                    analysis_record["safety_assessment"] = safety_result

            except Exception as e:
                logger.error(f"AI analysis failed: {e}")
                analysis_record["ai_analysis"] = {"error": str(e)}

        # Save to database
        await db.forensic_analyses.insert_one(analysis_record)

        # Update client record
        await db.clients.update_one(
            {"clientNumber": client_number},
            {
                "$push": {"forensicCases": case_id},
                "$set": {"lastForensicAnalysis": datetime.utcnow()}
            }
        )

        # Cleanup temp files in background
        background_tasks.add_task(cleanup_temp_dir, temp_dir)

        return {
            "success": True,
            "case_id": case_id,
            "status": "completed",
            "device_info": result['device_info'],
            "extraction_summary": analysis_record["extraction_summary"],
            "ai_analysis_included": include_ai_analysis and bool(all_messages),
            "message": "iOS backup analyzed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"iOS backup analysis failed: {e}")
        # Cleanup on error
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/case/{case_id}")
async def get_ios_case(
    case_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """Get iOS forensic analysis case details."""

    case = await db.forensic_analyses.find_one({
        "case_id": case_id,
        "analysis_type": "ios_backup"
    })

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Remove MongoDB ObjectId for JSON serialization
    case.pop('_id', None)

    return case


@router.get("/cases/{client_number}")
async def list_ios_cases(
    client_number: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """List all iOS forensic cases for a client."""

    cases = await db.forensic_analyses.find({
        "client_number": client_number,
        "analysis_type": "ios_backup"
    }).sort("created_at", -1).to_list(100)

    # Clean up for JSON
    for case in cases:
        case.pop('_id', None)
        # Don't send full message list in listing
        case.pop('messages', None)

    return {"cases": cases, "total": len(cases)}


@router.get("/case/{case_id}/messages")
async def get_case_messages(
    case_id: str,
    platform: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """Get messages from an iOS forensic case with pagination."""

    case = await db.forensic_analyses.find_one({
        "case_id": case_id,
        "analysis_type": "ios_backup"
    })

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    messages = case.get('messages', [])

    # Filter by platform if specified
    if platform:
        messages = [m for m in messages if m.get('platform') == platform]

    # Paginate
    total = len(messages)
    messages = messages[offset:offset + limit]

    return {
        "messages": messages,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/case/{case_id}/timeline")
async def get_case_timeline(
    case_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """Get timeline data for visualization."""

    case = await db.forensic_analyses.find_one({
        "case_id": case_id,
        "analysis_type": "ios_backup"
    })

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    timeline_events = []

    # Add messages to timeline
    for msg in case.get('messages', []):
        if msg.get('timestamp'):
            timeline_events.append({
                "type": "message",
                "platform": msg.get('platform'),
                "timestamp": msg.get('timestamp'),
                "content": (msg.get('text', '')[:100] + '...') if len(msg.get('text', '')) > 100 else msg.get('text', ''),
                "direction": "outgoing" if msg.get('is_from_me') else "incoming",
                "contact": msg.get('contact')
            })

    # Add calls to timeline
    for call in case.get('call_history', []):
        if call.get('timestamp'):
            timeline_events.append({
                "type": "call",
                "platform": "ios_calls",
                "timestamp": call.get('timestamp'),
                "content": f"{call.get('direction', 'unknown')} call - {call.get('duration_seconds', 0)}s",
                "direction": call.get('direction'),
                "contact": call.get('phone_number')
            })

    # Sort by timestamp
    timeline_events.sort(key=lambda x: x.get('timestamp', ''))

    return {
        "case_id": case_id,
        "events": timeline_events,
        "total": len(timeline_events)
    }


def find_backup_root(extract_path: Path) -> Optional[Path]:
    """Find the actual iOS backup root directory (containing Manifest.db)."""

    # Check if Manifest.db is at root
    if (extract_path / "Manifest.db").exists():
        return extract_path

    # Search in subdirectories (backup might be in a folder)
    for item in extract_path.iterdir():
        if item.is_dir():
            if (item / "Manifest.db").exists():
                return item
            # One more level deep
            for subitem in item.iterdir():
                if subitem.is_dir() and (subitem / "Manifest.db").exists():
                    return subitem

    return None


def cleanup_temp_dir(temp_dir: str):
    """Cleanup temporary extraction directory."""
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.info(f"Cleaned up temp directory: {temp_dir}")
    except Exception as e:
        logger.error(f"Failed to cleanup temp directory: {e}")
