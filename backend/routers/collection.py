"""
Android Agent Collection Router for SafeChild
Handles mobile forensic data collection from Android devices
"""
from fastapi import APIRouter, HTTPException, Depends, Body, UploadFile, File
from fastapi.responses import FileResponse
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


import random
import string

def generate_short_code(length=8):
    """Generate a short, URL-safe code that's easy to click in messaging apps"""
    # Use only alphanumeric characters (no special chars that might break URL parsing)
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


# APK download paths
APK_PATH = Path("/app/backend/static/safechild-agent.apk")
APK_FALLBACK_PATH = Path(__file__).parent.parent / "static" / "safechild-agent.apk"


@router.get("/download-app")
async def download_android_app():
    """
    Download the SafeChild Android Agent APK.
    This endpoint is public - anyone with the link can download.
    """
    # Try primary path first, then fallback
    if APK_PATH.exists():
        apk_file = APK_PATH
    elif APK_FALLBACK_PATH.exists():
        apk_file = APK_FALLBACK_PATH
    else:
        raise HTTPException(
            status_code=404,
            detail="APK file not found. Please contact support."
        )

    return FileResponse(
        path=str(apk_file),
        filename="SafeChild-Agent.apk",
        media_type="application/vnd.android.package-archive"
    )


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

    # Generate SHORT token (8 chars) - easy to click in messaging apps
    short_code = generate_short_code(8)

    # Ensure uniqueness
    while await db.collection_requests.find_one({"shortCode": short_code}):
        short_code = generate_short_code(8)

    # Also keep a full UUID for internal reference
    full_token = uuid.uuid4().hex

    request_record = {
        "id": str(uuid.uuid4()),
        "token": full_token,
        "shortCode": short_code,  # NEW: Short code for URL
        "type": "mobile_collection",
        "clientNumber": client_number,
        "clientName": f"{client.get('firstName', '')} {client.get('lastName', '')}".strip(),
        "clientPhone": client.get("phone"),
        "deviceType": data.get("deviceType", "android"),
        "scenario_type": data.get("scenarioType", "standard"), # standard, elderly, chat_only
        "lawyerId": str(current_user.get("clientNumber", "admin")),
        "status": "pending",
        "expiresAt": datetime.utcnow() + timedelta(hours=48),  # 48 hour expiry
        "createdAt": datetime.utcnow(),
        "collectedData": None,
        "uploadedAt": None
    }

    await db.collection_requests.insert_one(request_record)

    # Build SHORT collection link - safechild.mom/c/abc12345
    frontend_url = os.environ.get("FRONTEND_URL", "https://safechild.mom")
    collection_link = f"{frontend_url}/c/{short_code}"

    # Also provide direct APK download link
    apk_download_link = f"{frontend_url}/api/collection/download-apk/{short_code}"

    logger.info(f"Mobile collection link created", extra={"extra_fields": {
        "client_number": client_number,
        "short_code": short_code,
        "device_type": request_record["deviceType"],
        "scenario_type": request_record["scenario_type"]
    }})

    return {
        "success": True,
        "token": short_code,
        "shortCode": short_code,
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
    Supports both shortCode and full token.
    """
    # Try shortCode first, then full token
    req = await db.collection_requests.find_one({"shortCode": token})
    if not req:
        req = await db.collection_requests.find_one({"token": token})
    if not req:
        raise HTTPException(status_code=404, detail="Invalid token")

    if req["expiresAt"] < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Token expired")

    if req["status"] == "completed":
        raise HTTPException(status_code=400, detail="Data already collected")

    # Build APK download link
    frontend_url = os.environ.get("FRONTEND_URL", "https://safechild.mom")
    short_code = req.get("shortCode", token)
    apk_download_link = f"{frontend_url}/api/collection/download-apk/{short_code}"

    return {
        "isValid": True,
        "clientNumber": req["clientNumber"],
        "clientName": req.get("clientName", "Client"),
        "deviceType": req["deviceType"],
        "scenario_type": req.get("scenario_type", "standard"),
        "shortCode": short_code,
        "apkDownloadLink": apk_download_link
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
    Returns the APK file for download.
    """
    # Try shortCode first, then full token
    req = await db.collection_requests.find_one({"shortCode": token})
    if not req:
        req = await db.collection_requests.find_one({"token": token})
    if not req:
        raise HTTPException(status_code=404, detail="Invalid token")

    if req["expiresAt"] < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Token expired")

    # Serve the APK file
    apk_path = Path(__file__).parent.parent / "static" / "safechild-agent.apk"
    if not apk_path.exists():
        raise HTTPException(status_code=404, detail="APK file not found")

    return FileResponse(
        path=str(apk_path),
        filename=f"SafeChild-{token}.apk",
        media_type="application/vnd.android.package-archive"
    )


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
    Supports both shortCode and full token.
    """
    # Validate token - try shortCode first, then full token
    req = await db.collection_requests.find_one({"shortCode": token})
    if not req:
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


# =============================================================================
# Chunked Upload Support (for large files from Android Agent)
# =============================================================================

CHUNK_DIR = Path("/tmp/chunks")
CHUNK_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload-chunk")
async def upload_chunk(
    token: str = Form(...),
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    file_name: str = Form(...),
    chunk: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Upload a single chunk of a large file.
    Used by Android Agent for files > 5MB.
    """
    # Validate token
    req = await db.collection_requests.find_one({"shortCode": token})
    if not req:
        req = await db.collection_requests.find_one({"token": token})
    if not req:
        raise HTTPException(status_code=404, detail="Invalid token")

    if req["expiresAt"] < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Token expired")

    try:
        # Create chunk directory for this upload
        upload_chunk_dir = CHUNK_DIR / upload_id
        upload_chunk_dir.mkdir(parents=True, exist_ok=True)

        # Save chunk
        chunk_path = upload_chunk_dir / f"chunk_{chunk_index:05d}"
        content = await chunk.read()
        with open(chunk_path, "wb") as f:
            f.write(content)

        # Save metadata
        meta_path = upload_chunk_dir / "meta.json"
        meta = {
            "token": token,
            "upload_id": upload_id,
            "file_name": file_name,
            "total_chunks": total_chunks,
            "client_number": req["clientNumber"],
            "started_at": datetime.utcnow().isoformat()
        }
        with open(meta_path, "w") as f:
            json.dump(meta, f)

        logger.info(f"Chunk uploaded: {chunk_index + 1}/{total_chunks}", extra={"extra_fields": {
            "upload_id": upload_id,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks
        }})

        return {
            "success": True,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks
        }

    except Exception as e:
        logger.error(f"Chunk upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-complete")
async def complete_chunked_upload(
    data: dict = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Finalize chunked upload - merge chunks and process.
    """
    token = data.get("token")
    upload_id = data.get("upload_id")
    file_name = data.get("file_name", "collection.zip")

    if not token or not upload_id:
        raise HTTPException(status_code=400, detail="token and upload_id required")

    # Validate token
    req = await db.collection_requests.find_one({"shortCode": token})
    if not req:
        req = await db.collection_requests.find_one({"token": token})
    if not req:
        raise HTTPException(status_code=404, detail="Invalid token")

    upload_chunk_dir = CHUNK_DIR / upload_id
    if not upload_chunk_dir.exists():
        raise HTTPException(status_code=404, detail="Upload not found")

    try:
        # Read metadata
        meta_path = upload_chunk_dir / "meta.json"
        with open(meta_path, "r") as f:
            meta = json.load(f)

        client_number = meta["client_number"]
        total_chunks = meta["total_chunks"]

        # Verify all chunks exist
        chunk_files = sorted(upload_chunk_dir.glob("chunk_*"))
        if len(chunk_files) != total_chunks:
            raise HTTPException(
                status_code=400,
                detail=f"Missing chunks: got {len(chunk_files)}, expected {total_chunks}"
            )

        # Create final directory
        collection_dir = UPLOAD_DIR / f"{client_number}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        collection_dir.mkdir(parents=True, exist_ok=True)

        # Merge chunks
        final_path = collection_dir / file_name
        with open(final_path, "wb") as outfile:
            for chunk_file in chunk_files:
                with open(chunk_file, "rb") as infile:
                    outfile.write(infile.read())

        # Encrypt the merged file
        with open(final_path, "rb") as f:
            content = f.read()

        encryption_result = security_service.encrypt_file(content)
        encrypted_path = collection_dir / f"{file_name}.enc"
        with open(encrypted_path, "wb") as f:
            f.write(encryption_result['encrypted_data'])

        enc_meta = {k: v for k, v in encryption_result.items() if k != 'encrypted_data'}

        # Process ZIP if applicable
        stats = {"sms": 0, "contacts": 0, "call_log": 0, "media": 0, "whatsapp": 0}
        metadata = {}
        extracted_dir = None

        if file_name.endswith(".zip"):
            try:
                extracted_dir = collection_dir / "extracted"
                with zipfile.ZipFile(final_path, 'r') as zf:
                    zf.extractall(extracted_dir)

                # Parse metadata
                metadata_file = extracted_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)

                # Count items
                for filename, key in [
                    ("sms.json", "sms"),
                    ("contacts.json", "contacts"),
                    ("call_log.json", "call_log"),
                    ("media.json", "media"),
                    ("whatsapp_msgstore.db", "whatsapp")
                ]:
                    filepath = extracted_dir / filename
                    if filepath.exists():
                        if filename.endswith(".json"):
                            with open(filepath, 'r') as f:
                                data = json.load(f)
                                stats[key] = len(data) if isinstance(data, list) else 1
                        else:
                            stats[key] = 1

                # Delete unencrypted ZIP
                final_path.unlink()

            except Exception as e:
                logger.warning(f"ZIP processing failed: {e}")

        # Create forensic record
        case_id = f"AGENT_{client_number}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        analysis_record = {
            "case_id": case_id,
            "client_number": client_number,
            "source": "android_agent",
            "status": "completed",
            "collection_token": token,
            "encrypted_file": str(encrypted_path),
            "extracted_dir": str(extracted_dir) if extracted_dir else None,
            "encryption_metadata": enc_meta,
            "device_info": metadata.get("device", {}),
            "statistics": stats,
            "chain_of_custody": [{
                "id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow(),
                "actor": f"Android Agent: {metadata.get('device', {}).get('model', 'Unknown')}",
                "action": "MOBILE_DATA_COLLECTION",
                "details": f"Collected via SafeChild Android Agent (chunked upload). Upload ID: {upload_id}"
            }],
            "created_at": datetime.utcnow()
        }

        await db.forensic_analyses.insert_one(analysis_record)

        # Update collection request
        await db.collection_requests.update_one(
            {"$or": [{"shortCode": token}, {"token": token}]},
            {
                "$set": {
                    "status": "completed",
                    "uploadedAt": datetime.utcnow(),
                    "caseId": case_id,
                    "statistics": stats
                }
            }
        )

        # Cleanup chunk directory
        shutil.rmtree(upload_chunk_dir, ignore_errors=True)

        logger.info(f"Chunked upload completed", extra={"extra_fields": {
            "case_id": case_id,
            "client_number": client_number,
            "stats": stats
        }})

        return {
            "success": True,
            "caseId": case_id,
            "statistics": stats,
            "message": "Data collected successfully"
        }

    except Exception as e:
        logger.error(f"Chunked upload completion failed: {e}")
        # Cleanup on error
        shutil.rmtree(upload_chunk_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))
