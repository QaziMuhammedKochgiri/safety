"""
Android Agent Collection Router for SafeChild
Handles mobile forensic data collection from Android devices
"""
from fastapi import APIRouter, HTTPException, Depends, Body, UploadFile, File
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid
from pathlib import Path
import os
import json
import zipfile
import shutil

from .. import get_db
from ..auth import get_current_admin
from ..security_service import security_service
from ..logging_config import get_logger

router = APIRouter(prefix="/collection", tags=["Mobile Collection"])
logger = get_logger("safechild.collection")

UPLOAD_DIR = Path("/app/uploads/mobile")
try:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
except PermissionError:
    # Fallback to temp directory if /app/uploads is not writable
    UPLOAD_DIR = Path("/tmp/mobile_uploads")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/create-link")
async def create_collection_link(
    data: dict = Body(...),
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Admin creates a collection link for a client's mobile device.
    Data: {
        "clientNumber": "SC2025001",
        "deviceType": "android",  # android | ios
        "sendSms": false
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
        "type": "mobile_collection",
        "clientNumber": client_number,
        "clientName": f"{client.get('firstName', '')} {client.get('lastName', '')}".strip(),
        "clientPhone": client.get("phone"),
        "deviceType": data.get("deviceType", "android"),
        "lawyerId": str(current_user.get("clientNumber", "admin")),
        "status": "pending",
        "expiresAt": datetime.utcnow() + timedelta(hours=48),  # 48 hour expiry
        "createdAt": datetime.utcnow(),
        "collectedData": None,
        "uploadedAt": None
    }

    await db.collection_requests.insert_one(request_record)

    # Build the collection link
    frontend_url = os.environ.get("FRONTEND_URL", "https://safechild.mom")
    collection_link = f"{frontend_url}/collect/{token}"

    # Also provide direct APK download link
    apk_download_link = f"{frontend_url}/api/collection/download-apk/{token}"

    logger.info(f"Mobile collection link created", extra={"extra_fields": {
        "client_number": client_number,
        "token_prefix": token[:8],
        "device_type": request_record["deviceType"]
    }})

    return {
        "success": True,
        "token": token,
        "collectionLink": collection_link,
        "apkDownloadLink": apk_download_link,
        "expiresAt": request_record["expiresAt"].isoformat()
    }


@router.get("/validate/{token}")
async def validate_collection_token(
    token: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Public endpoint for Android app to validate token.
    Returns client info if valid.
    """
    req = await db.collection_requests.find_one({"token": token})
    if not req:
        raise HTTPException(status_code=404, detail="Invalid token")

    if req["expiresAt"] < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Token expired")

    if req["status"] == "completed":
        raise HTTPException(status_code=400, detail="Data already collected")

    return {
        "isValid": True,
        "clientNumber": req["clientNumber"],
        "clientName": req.get("clientName", "Client"),
        "deviceType": req["deviceType"]
    }


@router.post("/upload")
async def upload_collection_data(
    token: str = Body(...),
    clientNumber: str = Body(...),
    file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Receives ZIP file with collected data from Android app.
    """
    # Validate token
    req = await db.collection_requests.find_one({"token": token})
    if not req:
        raise HTTPException(status_code=404, detail="Invalid token")

    if req["expiresAt"] < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Token expired")

    try:
        # Create directory for this collection
        collection_dir = UPLOAD_DIR / f"{clientNumber}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        collection_dir.mkdir(parents=True, exist_ok=True)

        # Save uploaded ZIP
        zip_path = collection_dir / "collection.zip"
        content = await file.read()

        # Encrypt the file
        encryption_result = security_service.encrypt_file(content)
        encrypted_path = collection_dir / "collection.zip.enc"
        with open(encrypted_path, "wb") as f:
            f.write(encryption_result['encrypted_data'])

        # Save encryption metadata
        enc_meta = {k: v for k, v in encryption_result.items() if k != 'encrypted_data'}

        # Also save unencrypted for processing (will be deleted after)
        with open(zip_path, "wb") as f:
            f.write(content)

        # Extract and process the ZIP
        extracted_dir = collection_dir / "extracted"
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extracted_dir)

        # Parse metadata
        metadata = {}
        metadata_file = extracted_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

        # Count collected items
        stats = {
            "sms": 0,
            "contacts": 0,
            "call_log": 0,
            "media": 0
        }

        for filename, key in [("sms.json", "sms"), ("contacts.json", "contacts"),
                               ("call_log.json", "call_log"), ("media_list.json", "media")]:
            filepath = extracted_dir / filename
            if filepath.exists():
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    stats[key] = len(data) if isinstance(data, list) else 0

        # Delete unencrypted ZIP (keep only encrypted)
        zip_path.unlink()

        # Create forensic analysis record
        case_id = f"MOBILE_{clientNumber}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        analysis_record = {
            "case_id": case_id,
            "client_number": clientNumber,
            "source": "android_agent",
            "status": "completed",
            "collection_token": token,
            "encrypted_file": str(encrypted_path),
            "extracted_dir": str(extracted_dir),
            "encryption_metadata": enc_meta,
            "device_info": metadata.get("deviceInfo", {}),
            "statistics": stats,
            "chain_of_custody": [{
                "id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow(),
                "actor": f"Android Agent: {metadata.get('deviceInfo', {}).get('model', 'Unknown')}",
                "action": "MOBILE_DATA_COLLECTION",
                "details": f"Collected via SafeChild Android Agent. Token: {token[:8]}..."
            }],
            "created_at": datetime.utcnow()
        }

        await db.forensic_analyses.insert_one(analysis_record)

        # Update collection request
        await db.collection_requests.update_one(
            {"token": token},
            {
                "$set": {
                    "status": "completed",
                    "uploadedAt": datetime.utcnow(),
                    "caseId": case_id,
                    "statistics": stats
                }
            }
        )

        logger.info(f"Mobile collection completed", extra={"extra_fields": {
            "case_id": case_id,
            "client_number": clientNumber,
            "stats": stats
        }})

        return {
            "success": True,
            "caseId": case_id,
            "message": "Data collected successfully"
        }

    except Exception as e:
        logger.error(f"Collection upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-media")
async def upload_media_file(
    token: str = Body(...),
    media: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Upload individual media files (for large files).
    """
    req = await db.collection_requests.find_one({"token": token})
    if not req:
        raise HTTPException(status_code=404, detail="Invalid token")

    try:
        # Find the collection directory
        client_number = req["clientNumber"]
        # Save to a media subdirectory
        media_dir = UPLOAD_DIR / f"{client_number}_media"
        media_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = media_dir / media.filename
        content = await media.read()

        # Encrypt and save
        encryption_result = security_service.encrypt_file(content)
        encrypted_path = media_dir / f"{media.filename}.enc"
        with open(encrypted_path, "wb") as f:
            f.write(encryption_result['encrypted_data'])

        return {"success": True, "filename": media.filename}

    except Exception as e:
        logger.error(f"Media upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download-apk/{token}")
async def download_apk(
    token: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Provides APK download with embedded token.
    For now, returns instructions. Later can serve actual APK.
    """
    req = await db.collection_requests.find_one({"token": token})
    if not req:
        raise HTTPException(status_code=404, detail="Invalid token")

    if req["expiresAt"] < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Token expired")

    # For now, return download instructions
    # In production, this would serve the actual APK
    return {
        "message": "APK download will be available soon",
        "token": token,
        "instructions": [
            "1. Download the SafeChild Agent APK",
            "2. Install it on the target device",
            "3. Open the app and follow the instructions",
            "4. Grant the requested permissions",
            "5. Wait for data collection to complete"
        ]
    }


@router.get("/list")
async def list_collection_requests(
    current_user: dict = Depends(get_current_admin),
    status: str = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    List all collection requests (admin only).
    """
    query = {"type": "mobile_collection"}
    if status:
        query["status"] = status

    requests_cursor = db.collection_requests.find(
        query,
        {"_id": 0}
    ).sort("createdAt", -1).limit(100)

    requests_list = await requests_cursor.to_list(length=None)

    return {"requests": requests_list, "total": len(requests_list)}


@router.delete("/{token}")
async def revoke_collection_request(
    token: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Revoke a collection request (admin only).
    """
    result = await db.collection_requests.delete_one({"token": token})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Request not found")

    return {"success": True, "message": "Collection request revoked"}


# =============================================================================
# Web-based Multi-File Upload (for mobile browser collection)
# =============================================================================

from fastapi import Form
from typing import List

@router.post("/upload-files")
async def upload_multiple_files(
    token: str = Form(...),
    type: str = Form(...),  # photos, videos, files
    files: List[UploadFile] = File(...),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Upload multiple files from web browser (mobile collection page).
    Accepts photos, videos, or other files.
    """
    # Validate token
    req = await db.collection_requests.find_one({"token": token})
    if not req:
        raise HTTPException(status_code=404, detail="Invalid token")

    if req["expiresAt"] < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Token expired")

    client_number = req["clientNumber"]

    try:
        # Create directory structure
        base_dir = UPLOAD_DIR / client_number
        type_dir = base_dir / type
        type_dir.mkdir(parents=True, exist_ok=True)

        uploaded_files = []
        total_size = 0

        for file in files:
            # Generate unique filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            unique_id = uuid.uuid4().hex[:8]
            ext = Path(file.filename).suffix if file.filename else ''
            safe_filename = f"{timestamp}_{unique_id}{ext}"

            # Read file content
            content = await file.read()
            file_size = len(content)
            total_size += file_size

            # Save file (optionally encrypt for sensitive data)
            file_path = type_dir / safe_filename
            with open(file_path, "wb") as f:
                f.write(content)

            uploaded_files.append({
                "original_name": file.filename,
                "saved_name": safe_filename,
                "size": file_size,
                "content_type": file.content_type,
                "uploaded_at": datetime.utcnow().isoformat()
            })

        # Update or create forensic record
        case_id = f"WEB_{client_number}_{datetime.utcnow().strftime('%Y%m%d')}"

        existing_record = await db.forensic_analyses.find_one({
            "client_number": client_number,
            "source": "web_collection"
        })

        if existing_record:
            # Update existing record
            await db.forensic_analyses.update_one(
                {"_id": existing_record["_id"]},
                {
                    "$push": {
                        f"collected_{type}": {"$each": uploaded_files},
                        "chain_of_custody": {
                            "id": str(uuid.uuid4()),
                            "timestamp": datetime.utcnow(),
                            "actor": "Web Collection",
                            "action": f"FILES_UPLOADED",
                            "details": f"Uploaded {len(files)} {type} files ({total_size} bytes)"
                        }
                    },
                    "$set": {"updated_at": datetime.utcnow()},
                    "$inc": {f"statistics.{type}": len(files)}
                }
            )
        else:
            # Create new record
            analysis_record = {
                "case_id": case_id,
                "client_number": client_number,
                "source": "web_collection",
                "status": "in_progress",
                "collection_token": token,
                "upload_dir": str(base_dir),
                f"collected_{type}": uploaded_files,
                "statistics": {
                    "photos": len(files) if type == "photos" else 0,
                    "videos": len(files) if type == "videos" else 0,
                    "files": len(files) if type == "files" else 0
                },
                "chain_of_custody": [{
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.utcnow(),
                    "actor": "Web Collection",
                    "action": "COLLECTION_STARTED",
                    "details": f"Web-based collection started. First upload: {len(files)} {type} files"
                }],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await db.forensic_analyses.insert_one(analysis_record)

        logger.info(f"Web collection upload: {len(files)} {type} files", extra={"extra_fields": {
            "client_number": client_number,
            "type": type,
            "file_count": len(files),
            "total_size": total_size
        }})

        return {
            "success": True,
            "uploaded": len(files),
            "totalSize": total_size,
            "message": f"{len(files)} dosya başarıyla yüklendi"
        }

    except Exception as e:
        logger.error(f"Web collection upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
