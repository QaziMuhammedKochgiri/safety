from fastapi import APIRouter, Depends, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from .. import get_db
from ..models import Consent, ConsentCreate

router = APIRouter(prefix="/consent", tags=["Consent Management"])

@router.post("")
async def log_consent(consent_data: ConsentCreate, request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Log user consent"""
    try:
        ip_address = request.client.host
        
        consent_dict = consent_data.model_dump()
        consent_dict['ipAddress'] = ip_address
        
        consent = Consent.model_validate(consent_dict)
        
        await db.consents.insert_one(consent.model_dump())
        
        return {
            "success": True,
            "consentId": str(consent.id),
            "timestamp": consent.timestamp
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
async def get_all_consent_logs(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get all consent logs (admin only)"""
    try:
        logs = await db.consents.find({}).sort("timestamp", -1).to_list(length=None)
        # Convert ObjectId to string for JSON serialization
        for log in logs:
            if "_id" in log:
                log["_id"] = str(log["_id"])
            if "timestamp" in log:
                log["timestamp"] = log["timestamp"].isoformat() if hasattr(log["timestamp"], 'isoformat') else str(log["timestamp"])
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}")
async def get_consent(session_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get consent details for a session"""
    consent = await db.consents.find_one({"sessionId": session_id}, {"_id": 0})
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")
    return consent
