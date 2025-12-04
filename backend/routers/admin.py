from fastapi import APIRouter, HTTPException, Depends, Body
from datetime import datetime, timedelta, timezone
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from pathlib import Path

from .. import get_db
from ..auth import get_current_admin, get_password_hash

router = APIRouter(prefix="/admin", tags=["Admin Panel"])


@router.post("/clients")
async def admin_create_client(
    client_data: dict,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create a new client (admin only)"""
    try:
        client_data["clientNumber"] = f"SC{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        client_data["hashedPassword"] = get_password_hash("defaultpassword")
        client_data["createdAt"] = datetime.now(timezone.utc)
        client_data["updatedAt"] = datetime.now(timezone.utc)
        client_data["role"] = "client"
        client_data["status"] = "active"

        await db.clients.insert_one(client_data)

        return {"success": True, "clientNumber": client_data["clientNumber"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clients")
async def admin_get_all_clients(
    current_admin: dict = Depends(get_current_admin),
    skip: int = 0,
    limit: int = 100,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all clients (admin only)"""
    try:
        clients_cursor = db.clients.find(
            {},
            {"_id": 0, "hashedPassword": 0}
        ).skip(skip).limit(limit)
        clients = await clients_cursor.to_list(length=None)
        
        total = await db.clients.count_documents({})
        
        return {
            "clients": clients,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clients/{client_number}")
async def admin_get_client_details(
    client_number: str,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get detailed client info including documents (admin only)"""
    try:
        client = await db.clients.find_one(
            {"clientNumber": client_number},
            {"_id": 0, "hashedPassword": 0}
        )
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        documents = await db.documents.find(
            {"clientNumber": client_number},
            {"_id": 0}
        ).to_list(length=None)
        
        chat_messages = await db.chat_messages.find(
            {"clientNumber": client_number},
            {"_id": 0}
        ).sort("timestamp", -1).limit(50).to_list(length=None)
        
        return {
            "client": client,
            "documents": documents,
            "chatMessages": chat_messages
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/clients/{client_number}")
async def admin_update_client(
    client_number: str,
    update_data: dict,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update client information (admin only)"""
    try:
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

@router.delete("/clients/{client_number}")
async def admin_delete_client(
    client_number: str,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
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

@router.get("/documents")
async def admin_get_all_documents(
    current_admin: dict = Depends(get_current_admin),
    skip: int = 0,
    limit: int = 100,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all documents (admin only)"""
    try:
        documents = await db.documents.find(
            {},
            {"_id": 0}
        ).skip(skip).limit(limit).to_list(length=None)
        
        total = await db.documents.count_documents({})
        
        return {
            "documents": documents,
            "total": total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/consents")
async def admin_get_all_consents(
    current_admin: dict = Depends(get_current_admin),
    skip: int = 0,
    limit: int = 100,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all consent logs (admin only)"""
    try:
        consents = await db.consents.find(
            {},
            {"_id": 0}
        ).skip(skip).limit(limit).to_list(length=None)
        
        total = await db.consents.count_documents({})
        
        return {
            "consents": consents,
            "total": total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def admin_get_statistics(
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get dashboard statistics (admin only)"""
    try:
        total_clients = await db.clients.count_documents({"role": "client"})
        active_clients = await db.clients.count_documents({"status": "active", "role": "client"})
        total_documents = await db.documents.count_documents({})
        total_consents = await db.consents.count_documents({})
        total_messages = await db.chat_messages.count_documents({})
        
        total_forensic_cases = await db.forensic_analyses.count_documents({})
        processing_cases = await db.forensic_analyses.count_documents({"status": "processing"})
        completed_cases = await db.forensic_analyses.count_documents({"status": "completed"})
        failed_cases = await db.forensic_analyses.count_documents({"status": "failed"})
        
        total_meetings = await db.meetings.count_documents({})
        scheduled_meetings = await db.meetings.count_documents({"status": "scheduled"})
        completed_meetings = await db.meetings.count_documents({"status": "completed"})
        
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
            "totalForensicCases": total_forensic_cases,
            "processingCases": processing_cases,
            "completedCases": completed_cases,
            "failedCases": failed_cases,
            "totalMeetings": total_meetings,
            "scheduledMeetings": scheduled_meetings,
            "completedMeetings": completed_meetings,
            "recentClients": recent_clients
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/forensics")
async def admin_get_all_forensic_cases(
    current_admin: dict = Depends(get_current_admin),
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all forensic cases (admin only)"""
    try:
        query = {}
        if status:
            query["status"] = status
        
        cases = await db.forensic_analyses.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(length=None)
        
        total = await db.forensic_analyses.count_documents(query)
        
        return {
            "cases": cases,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/forensics/{case_id}")
async def admin_get_forensic_case_details(
    case_id: str,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get detailed forensic case info (admin only)"""
    try:
        case = await db.forensic_analyses.find_one(
            {"case_id": case_id},
            {"_id": 0}
        )
        
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        return case
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/forensics/{case_id}")
async def admin_delete_forensic_case(
    case_id: str,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete forensic case (admin only) - force delete regardless of status"""
    try:
        case = await db.forensic_analyses.find_one({"case_id": case_id})
        
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        if case.get("uploaded_file"):
            try:
                Path(case["uploaded_file"]).unlink(missing_ok=True)
            except:
                pass
        
        if case.get("report_txt"):
            try:
                Path(case["report_txt"]).unlink(missing_ok=True)
            except:
                pass
        
        if case.get("report_pdf"):
            try:
                Path(case["report_pdf"]).unlink(missing_ok=True)
            except:
                pass
        
        await db.forensic_analyses.delete_one({"case_id": case_id})
        
        return {"success": True, "message": "Forensic case deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/meetings")
async def admin_get_all_meetings(
    current_admin: dict = Depends(get_current_admin),
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all meetings (admin only)"""
    try:
        query = {}
        if status:
            query["status"] = status
        
        meetings = await db.meetings.find(
            query,
            {"_id": 0}
        ).sort("createdAt", -1).skip(skip).limit(limit).to_list(length=None)
        
        total = await db.meetings.count_documents(query)
        
        return {
            "meetings": meetings,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/meetings/{meeting_id}")
async def admin_get_meeting_details(
    meeting_id: str,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get detailed meeting info (admin only)"""
    try:
        meeting = await db.meetings.find_one(
            {"meetingId": meeting_id},
            {"_id": 0}
        )
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        return meeting
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/meetings/{meeting_id}")
async def admin_update_meeting(
    meeting_id: str,
    update_data: dict,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update meeting (admin only)"""
    try:
        meeting = await db.meetings.find_one({"meetingId": meeting_id})
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        update_data.pop("meetingId", None)
        update_data.pop("createdAt", None)
        update_data["updatedAt"] = datetime.utcnow()
        
        await db.meetings.update_one(
            {"meetingId": meeting_id},
            {"$set": update_data}
        )
        
        return {"success": True, "message": "Meeting updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/meetings/{meeting_id}")
async def admin_delete_meeting(
    meeting_id: str,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete meeting (admin only) - force delete regardless of status"""
    try:
        meeting = await db.meetings.find_one({"meetingId": meeting_id})
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        await db.meetings.delete_one({"meetingId": meeting_id})
        
        return {"success": True, "message": "Meeting deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/forensics/{case_id}/share")
async def admin_share_forensic_case(
    case_id: str,
    days: int = 7,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Generate a shareable public link for a forensic report (admin only)"""
    try:
        case = await db.forensic_analyses.find_one({"case_id": case_id})
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
            
        if case.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Case analysis not completed yet")

        import uuid
        token = uuid.uuid4().hex
        
        share_link = {
            "id": str(uuid.uuid4()),
            "token": token,
            "caseId": case_id,
            "generatedBy": str(current_admin.get("_id", "admin")),
            "expiresAt": datetime.utcnow() + timedelta(days=days),
            "createdAt": datetime.utcnow(),
            "isRevoked": False
        }
        
        await db.shared_reports.insert_one(share_link)
        
        # In production, use env var for domain
        # Assuming the frontend/user will access via NGINX on port 443/80 which proxies /api to backend
        # But for the link returned, we want the external URL.
        # For now, we'll return a relative path or a constructed one.
        # If accessed via browser, it should be /api/public/reports/{token}
        
        full_url = f"/api/public/reports/{token}"
        
        return {
            "success": True,
            "url": full_url,
            "expires_at": share_link["expiresAt"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
