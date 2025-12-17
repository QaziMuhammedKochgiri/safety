"""
Phone Recovery Router
API endpoints for phone data recovery supporting two scenarios:
1. Client HAS computer: WebUSB-based extraction via browser
2. Client has NO computer: Mobile agent (APK/MDM) extraction

Admin creates a recovery link, sends to client, client extracts data.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path
import logging
import uuid
import secrets
import hashlib
import os
import shutil
import json

from backend.models import (
    CreateRecoveryLinkRequest,
    CreateRecoveryLinkResponse,
    RecoveryStatusResponse,
    PhoneRecoveryCase,
    RecoveryCustodyEvent,
    DeviceInfo,
    DataCategories,
    DeletionSchedule,
    BackupFileInfo,
    RecoveryStatistics,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recovery", tags=["Phone Recovery"])

# In-memory storage (would use MongoDB in production)
recovery_cases = {}
recovery_codes = {}  # Maps short codes to case_ids

# Base paths
UPLOAD_BASE = Path("/tmp/recovery_uploads")
OUTPUT_BASE = Path("/tmp/recovery_output")

# Chunk size for uploads (100MB)
CHUNK_SIZE = 100 * 1024 * 1024

# Base URL for recovery links
BASE_URL = os.getenv("BASE_URL", "https://portal.safechild-rechtsanwalt.de")


def generate_short_code() -> str:
    """Generate 8-character short code for recovery link"""
    return secrets.token_urlsafe(6)[:8].lower()


# =============================================================================
# Admin Endpoints
# =============================================================================

@router.post("/create-link", response_model=CreateRecoveryLinkResponse)
async def create_recovery_link(request: CreateRecoveryLinkRequest):
    """
    Create a recovery link for a client.
    Admin sends this link to the client who then uploads their backup.
    """
    try:
        # Generate unique identifiers
        short_code = generate_short_code()
        full_token = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d")
        case_id = f"RECOVERY_{request.client_number}_{timestamp}_{short_code.upper()}"

        # Calculate expiration
        expires_at = datetime.now(timezone.utc) + timedelta(days=request.expires_in_days)

        # Create recovery case
        recovery_case = PhoneRecoveryCase(
            case_id=case_id,
            client_number=request.client_number,
            recovery_method="wireless",
            recovery_code=short_code,
            full_token=full_token,
            expires_at=expires_at,
            device_info=DeviceInfo(
                device_type=request.device_type,
                connection_type="wireless"
            ),
            data_categories=request.data_categories or DataCategories(),
            status="pending",
            current_step="Waiting for client to upload backup",
            deletion_schedule=DeletionSchedule(
                auto_delete_at=datetime.now(timezone.utc) + timedelta(days=15)
            ),
            chain_of_custody=[
                RecoveryCustodyEvent(
                    actor="Admin",
                    action="LINK_CREATED",
                    details=f"Recovery link created for {request.device_type} device"
                )
            ]
        )

        # Store case
        recovery_cases[case_id] = recovery_case.model_dump()
        recovery_codes[short_code] = case_id

        # Generate links
        recovery_link = f"{BASE_URL}/recover/{short_code}"
        # Always include APK link (client page will show based on device type)
        apk_link = f"{BASE_URL}/download/safechild-recovery.apk"

        logger.info(f"Created recovery link for client {request.client_number}: {recovery_link}")

        return CreateRecoveryLinkResponse(
            case_id=case_id,
            recovery_code=short_code,
            recovery_link=recovery_link,
            apk_download_link=apk_link,
            expires_at=expires_at
        )

    except Exception as e:
        logger.error(f"Error creating recovery link: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_recovery_requests():
    """List all wireless recovery requests (admin endpoint)."""
    cases = []
    for case_id, case in recovery_cases.items():
        cases.append({
            "case_id": case_id,
            "client_number": case.get("client_number"),
            "recovery_code": case.get("recovery_code"),
            "device_type": case.get("device_info", {}).get("device_type"),
            "status": case.get("status"),
            "progress_percent": case.get("progress_percent", 0),
            "expires_at": case.get("expires_at"),
            "created_at": case.get("created_at"),
            "completed_at": case.get("completed_at")
        })
    return cases


@router.get("/cases/{case_id}/download")
async def download_recovery_results_admin(case_id: str):
    """Download recovery results (admin endpoint)."""
    if case_id not in recovery_cases:
        raise HTTPException(status_code=404, detail="Recovery case not found")

    case = recovery_cases[case_id]

    if case.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Recovery not yet completed")

    zip_path = case.get("results", {}).get("zip_path")
    if not zip_path or not Path(zip_path).exists():
        raise HTTPException(status_code=404, detail="Results file not found")

    # Log download
    case["chain_of_custody"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": "Admin",
        "action": "RESULTS_DOWNLOADED",
        "details": "Recovery results downloaded by admin"
    })

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{case_id}_recovery.zip"
    )


# =============================================================================
# Public Endpoints (Token-based access for clients)
# =============================================================================

@router.get("/validate/{code}")
async def validate_recovery_code(code: str):
    """
    Validate a recovery code and return case info.
    Public endpoint - clients use this to verify their link is valid.
    """
    code = code.lower()

    if code not in recovery_codes:
        raise HTTPException(status_code=404, detail="Invalid recovery code")

    case_id = recovery_codes[code]
    case = recovery_cases.get(case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")

    # Check expiration
    expires_at = case.get("expires_at")
    if expires_at:
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expires_at:
            case["status"] = "expired"
            raise HTTPException(status_code=410, detail="Recovery link has expired")

    # Check if already completed
    if case.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Recovery already completed")

    device_info = case.get("device_info", {})
    data_categories = case.get("data_categories", {})
    device_type = device_info.get("device_type", "auto")

    return {
        "valid": True,
        "case_id": case_id,
        "device_type": device_type,  # "android", "ios", or "auto" (client auto-detects)
        "data_categories": data_categories,
        "expires_at": case.get("expires_at"),
        "status": case.get("status"),
        "instructions": _get_backup_instructions(device_type) if device_type != "auto" else None
    }


def _get_backup_instructions(device_type: str) -> dict:
    """Get backup creation instructions for device type"""
    if device_type == "android":
        return {
            "title": "Android Backup Instructions",
            "steps": [
                "1. Enable USB debugging in Developer Options",
                "2. Download and install the SafeChild Recovery app (APK)",
                "3. Open the app and grant all requested permissions",
                "4. Tap 'Create Backup' and wait for completion",
                "5. Upload the generated backup file below"
            ],
            "supported_formats": [".ab", ".tar", ".zip"],
            "max_size_gb": 128
        }
    else:
        return {
            "title": "iOS Backup Instructions",
            "steps": [
                "1. Connect your iPhone to a computer with iTunes/Finder",
                "2. Trust the computer when prompted on your device",
                "3. In iTunes/Finder, select your device",
                "4. Click 'Back Up Now' (ensure encryption is OFF)",
                "5. Wait for backup to complete",
                "6. Find the backup folder and compress it to ZIP",
                "7. Upload the ZIP file below"
            ],
            "backup_locations": {
                "windows": "C:\\Users\\[username]\\Apple\\MobileSync\\Backup\\",
                "mac": "~/Library/Application Support/MobileSync/Backup/"
            },
            "supported_formats": [".zip"],
            "max_size_gb": 128
        }


@router.post("/upload-backup/{code}")
async def upload_backup(
    code: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    chunk_index: int = Form(default=0),
    total_chunks: int = Form(default=1),
    checksum: Optional[str] = Form(default=None)
):
    """
    Upload backup file (supports chunked uploads for large files).

    For large files (>100MB), upload in chunks:
    - chunk_index: 0-based index of current chunk
    - total_chunks: total number of chunks
    - checksum: SHA256 of the complete file (sent with last chunk)
    """
    code = code.lower()

    if code not in recovery_codes:
        raise HTTPException(status_code=404, detail="Invalid recovery code")

    case_id = recovery_codes[code]
    case = recovery_cases.get(case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")

    # Check expiration and status
    if case.get("status") in ["completed", "expired", "processing"]:
        raise HTTPException(status_code=400, detail=f"Cannot upload: recovery is {case.get('status')}")

    try:
        # Create upload directory
        upload_dir = UPLOAD_BASE / case_id
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Handle chunked upload
        if total_chunks > 1:
            chunk_path = upload_dir / f"chunk_{chunk_index:04d}"
            with open(chunk_path, "wb") as f:
                content = await file.read()
                f.write(content)

            # Update progress
            progress = int((chunk_index + 1) / total_chunks * 30)  # Upload = 30% of total
            case["progress_percent"] = progress
            case["current_step"] = f"Uploading backup: {chunk_index + 1}/{total_chunks} chunks"

            # If this is the last chunk, combine them
            if chunk_index == total_chunks - 1:
                final_path = upload_dir / f"backup_{file.filename}"
                await _combine_chunks(upload_dir, final_path, total_chunks)

                # Verify checksum if provided
                if checksum:
                    actual_checksum = await _calculate_checksum(final_path)
                    if actual_checksum != checksum:
                        raise HTTPException(status_code=400, detail="Checksum mismatch - upload corrupted")

                # Update case with backup info
                case["backup_file"] = {
                    "file_name": file.filename,
                    "file_size": final_path.stat().st_size,
                    "uploaded_at": datetime.now(timezone.utc).isoformat(),
                    "checksum_sha256": checksum or await _calculate_checksum(final_path),
                    "encrypted_path": str(final_path)
                }
                case["status"] = "backup_ready"

                # Log custody event
                case["chain_of_custody"].append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "actor": f"Client: {case.get('client_number')}",
                    "action": "BACKUP_UPLOADED",
                    "details": f"Backup uploaded: {file.filename} ({final_path.stat().st_size / (1024*1024):.2f} MB)"
                })

                # Start processing in background
                background_tasks.add_task(_process_phone_recovery, case_id)

                return {
                    "success": True,
                    "message": "Upload complete. Processing started.",
                    "case_id": case_id,
                    "file_size": final_path.stat().st_size
                }

            return {
                "success": True,
                "message": f"Chunk {chunk_index + 1}/{total_chunks} uploaded",
                "chunks_remaining": total_chunks - chunk_index - 1
            }

        else:
            # Single file upload
            final_path = upload_dir / f"backup_{file.filename}"
            with open(final_path, "wb") as f:
                content = await file.read()
                f.write(content)

            # Update case
            file_size = final_path.stat().st_size
            file_checksum = await _calculate_checksum(final_path)

            case["backup_file"] = {
                "file_name": file.filename,
                "file_size": file_size,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "checksum_sha256": file_checksum,
                "encrypted_path": str(final_path)
            }
            case["status"] = "backup_ready"
            case["progress_percent"] = 30

            # Log custody event
            case["chain_of_custody"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "actor": f"Client: {case.get('client_number')}",
                "action": "BACKUP_UPLOADED",
                "details": f"Backup uploaded: {file.filename} ({file_size / (1024*1024):.2f} MB)"
            })

            # Start processing
            background_tasks.add_task(_process_phone_recovery, case_id)

            return {
                "success": True,
                "message": "Upload complete. Processing started.",
                "case_id": case_id,
                "file_size": file_size
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _combine_chunks(upload_dir: Path, output_path: Path, total_chunks: int):
    """Combine uploaded chunks into single file"""
    with open(output_path, "wb") as outfile:
        for i in range(total_chunks):
            chunk_path = upload_dir / f"chunk_{i:04d}"
            if chunk_path.exists():
                with open(chunk_path, "rb") as chunk:
                    outfile.write(chunk.read())
                chunk_path.unlink()  # Delete chunk after combining


async def _calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of file"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


async def _process_phone_recovery(case_id: str):
    """Background task to process wireless recovery"""
    try:
        case = recovery_cases.get(case_id)
        if not case:
            return

        case["status"] = "processing"
        case["current_step"] = "Processing backup..."
        case["progress_percent"] = 35

        backup_path = Path(case["backup_file"]["encrypted_path"])
        device_type = case.get("device_info", {}).get("device_type", "android")
        data_categories = DataCategories(**case.get("data_categories", {}))

        output_dir = OUTPUT_BASE / case_id
        output_dir.mkdir(parents=True, exist_ok=True)

        stats = RecoveryStatistics()

        # Determine backup type and extract
        if device_type == "android":
            await _process_android_backup(case_id, backup_path, output_dir, data_categories, stats)
        else:
            await _process_ios_backup(case_id, backup_path, output_dir, data_categories, stats)

        # Package results
        case["current_step"] = "Packaging results..."
        case["progress_percent"] = 95

        await _package_recovery_results(case_id, output_dir, stats)

    except Exception as e:
        logger.error(f"Error processing wireless recovery: {e}")
        if case_id in recovery_cases:
            recovery_cases[case_id]["status"] = "failed"
            recovery_cases[case_id]["current_step"] = f"Error: {str(e)}"


async def _process_android_backup(
    case_id: str,
    backup_path: Path,
    output_dir: Path,
    data_categories: DataCategories,
    stats: RecoveryStatistics
):
    """Process uploaded Android backup"""
    from backend.forensics.android_extractor import AndroidExtractor

    case = recovery_cases[case_id]
    case["current_step"] = "Extracting Android backup..."
    case["progress_percent"] = 40

    # Create dummy extractor for backup extraction
    extractor = AndroidExtractor("dummy", backup_path.parent)

    # Check if it's an ADB backup or other format
    if backup_path.suffix == ".ab":
        result = await extractor.extract_backup(backup_path, output_dir / "extracted")
        if result.success:
            stats.photos = result.categories.get("photos", 0)
            stats.videos = result.categories.get("videos", 0)
            stats.messages = result.categories.get("messages", 0)
            stats.app_files = result.categories.get("app_data", 0)
    elif backup_path.suffix in [".zip", ".tar"]:
        # Extract archive
        import tarfile
        import zipfile

        extract_dir = output_dir / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)

        if backup_path.suffix == ".zip":
            with zipfile.ZipFile(backup_path, "r") as zf:
                zf.extractall(extract_dir)
        else:
            with tarfile.open(backup_path, "r:*") as tf:
                tf.extractall(extract_dir)

        # Count files by type
        for f in extract_dir.rglob("*"):
            if f.is_file():
                ext = f.suffix.lower()
                if ext in [".jpg", ".jpeg", ".png", ".heic"]:
                    stats.photos += 1
                elif ext in [".mp4", ".mov", ".avi"]:
                    stats.videos += 1
                elif ext == ".db" or "message" in f.name.lower():
                    stats.messages += 1

    # Recover deleted files
    if data_categories.deleted_data:
        case["current_step"] = "Recovering deleted files..."
        case["progress_percent"] = 75

        from backend.forensics.recovery.file_carving import carve_deleted_files
        deleted_count = await carve_deleted_files(
            output_dir / "extracted",
            output_dir / "deleted_recovered"
        )
        stats.deleted_files = deleted_count


async def _process_ios_backup(
    case_id: str,
    backup_path: Path,
    output_dir: Path,
    data_categories: DataCategories,
    stats: RecoveryStatistics
):
    """Process uploaded iOS backup"""
    from backend.forensics.ios_extractor import iOSExtractor

    case = recovery_cases[case_id]
    case["current_step"] = "Extracting iOS backup..."
    case["progress_percent"] = 40

    # Extract ZIP if needed
    extract_dir = output_dir / "backup"
    extract_dir.mkdir(parents=True, exist_ok=True)

    if backup_path.suffix == ".zip":
        import zipfile
        with zipfile.ZipFile(backup_path, "r") as zf:
            zf.extractall(extract_dir)
        backup_path = extract_dir

    # Create extractor and process
    extractor = iOSExtractor(output_base=output_dir)

    case["current_step"] = "Parsing iOS backup structure..."
    case["progress_percent"] = 50

    result = await extractor.extract_backup(backup_path, output_dir / "extracted")
    if result.success:
        stats.photos = result.categories.get("photos", 0)
        stats.videos = result.categories.get("videos", 0)
        stats.messages = result.categories.get("messages", 0)
        stats.app_files = result.categories.get("app_data", 0)

    # Extract messages
    if data_categories.messages:
        case["current_step"] = "Extracting messages..."
        case["progress_percent"] = 60

        msg_result = await extractor.extract_messages(
            backup_path,
            output_dir / "messages" / "imessage.json"
        )
        if msg_result.success:
            stats.messages = msg_result.message_count

    # Extract WhatsApp
    if data_categories.app_data:
        case["current_step"] = "Extracting WhatsApp..."
        case["progress_percent"] = 70

        await extractor.extract_whatsapp(
            backup_path,
            output_dir / "apps" / "whatsapp"
        )

    # Recover deleted files
    if data_categories.deleted_data:
        case["current_step"] = "Recovering deleted files..."
        case["progress_percent"] = 85

        from backend.forensics.recovery.file_carving import carve_deleted_files
        deleted_count = await carve_deleted_files(
            output_dir / "extracted",
            output_dir / "deleted_recovered"
        )
        stats.deleted_files = deleted_count


async def _package_recovery_results(case_id: str, output_dir: Path, stats: RecoveryStatistics):
    """Package recovery results for wireless recovery"""
    case = recovery_cases.get(case_id)
    if not case:
        return

    # Calculate total size
    total_size = sum(f.stat().st_size for f in output_dir.rglob("*") if f.is_file())
    stats.total_size = total_size

    # Create metadata
    metadata = {
        "case_id": case_id,
        "client_number": case.get("client_number"),
        "device_type": case.get("device_info", {}).get("device_type"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "statistics": {
            "photos": stats.photos,
            "videos": stats.videos,
            "messages": stats.messages,
            "contacts": stats.contacts,
            "call_logs": stats.call_logs,
            "deleted_files": stats.deleted_files,
            "app_files": stats.app_files,
            "total_size": stats.total_size
        }
    }

    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    # Create ZIP
    zip_path = OUTPUT_BASE / f"{case_id}.zip"
    shutil.make_archive(str(zip_path.with_suffix("")), "zip", output_dir)

    # Calculate checksum
    checksum = await _calculate_checksum(zip_path)

    # Update case
    case["status"] = "completed"
    case["progress_percent"] = 100
    case["current_step"] = "Recovery complete"
    case["completed_at"] = datetime.now(timezone.utc).isoformat()
    case["results"] = {
        "zip_path": str(zip_path),
        "zip_size": zip_path.stat().st_size,
        "checksum_sha256": checksum,
        "encrypted": False
    }
    case["processed"] = {
        "extracted_dir": str(output_dir),
        "statistics": {
            "photos": stats.photos,
            "videos": stats.videos,
            "messages": stats.messages,
            "contacts": stats.contacts,
            "call_logs": stats.call_logs,
            "deleted_files": stats.deleted_files,
            "app_files": stats.app_files,
            "total_size": stats.total_size
        },
        "deleted_files_recovered": stats.deleted_files
    }

    # Log completion
    case["chain_of_custody"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": "System",
        "action": "PROCESSING_COMPLETED",
        "details": f"Recovery completed. {total_size / (1024*1024):.2f} MB processed. {stats.deleted_files} deleted files recovered."
    })


@router.get("/status/{code}", response_model=RecoveryStatusResponse)
async def get_recovery_status(code: str):
    """
    Get recovery status (public endpoint for clients).
    Client polls this to see processing progress.
    """
    code = code.lower()

    if code not in recovery_codes:
        raise HTTPException(status_code=404, detail="Invalid recovery code")

    case_id = recovery_codes[code]
    case = recovery_cases.get(case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")

    return RecoveryStatusResponse(
        case_id=case_id,
        status=case.get("status", "unknown"),
        progress_percent=case.get("progress_percent", 0),
        current_step=case.get("current_step"),
        statistics=case.get("processed", {}).get("statistics") if case.get("processed") else None,
        download_ready=case.get("status") == "completed"
    )


# =============================================================================
# WebUSB Agent Endpoints (Scenario 1: Client has computer)
# =============================================================================

@router.post("/device-connected/{code}")
async def notify_device_connected(code: str, request: Request):
    """
    Notify backend that a device has been connected via WebUSB.
    Called by WebUSBRecoveryAgent when device is detected.
    """
    code = code.lower()

    if code not in recovery_codes:
        raise HTTPException(status_code=404, detail="Invalid recovery code")

    case_id = recovery_codes[code]
    case = recovery_cases.get(case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")

    try:
        body = await request.json()
        device_info = body.get("device_info", {})

        # Update device info
        case["device_info"]["device_model"] = device_info.get("product", "Unknown")
        case["device_info"]["serial_number"] = device_info.get("serial", "Unknown")
        case["device_info"]["connection_type"] = device_info.get("connection_type", "webusb")

        # Log custody event
        case["chain_of_custody"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": f"WebUSB Agent",
            "action": "DEVICE_CONNECTED",
            "details": f"Device connected: {device_info.get('manufacturer', '')} {device_info.get('product', '')} (SN: {device_info.get('serial', 'N/A')})"
        })

        case["status"] = "device_connected"
        case["current_step"] = "Device connected, waiting for passcode"

        logger.info(f"Device connected for case {case_id}: {device_info}")

        return {"success": True, "message": "Device connection recorded"}

    except Exception as e:
        logger.error(f"Error recording device connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start-extraction/{code}")
async def start_extraction(code: str, request: Request, background_tasks: BackgroundTasks):
    """
    Start data extraction via WebUSB.
    Called when client provides screen lock code and clicks start.
    """
    code = code.lower()

    if code not in recovery_codes:
        raise HTTPException(status_code=404, detail="Invalid recovery code")

    case_id = recovery_codes[code]
    case = recovery_cases.get(case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")

    try:
        body = await request.json()
        screen_lock = body.get("screen_lock")
        device_serial = body.get("device_serial")
        connection_type = body.get("connection_type", "webusb")

        if not screen_lock or len(screen_lock) < 4:
            raise HTTPException(status_code=400, detail="Screen lock code is required (min 4 characters)")

        # Store screen lock securely (encrypted in production)
        case["screen_lock_hash"] = hashlib.sha256(screen_lock.encode()).hexdigest()

        # Update status
        case["status"] = "extracting"
        case["current_step"] = "Starting data extraction..."
        case["progress_percent"] = 5

        # Log custody event
        case["chain_of_custody"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": f"Client: {case.get('client_number')}",
            "action": "EXTRACTION_STARTED",
            "details": f"Extraction started via {connection_type}"
        })

        logger.info(f"Extraction started for case {case_id}")

        return {
            "success": True,
            "message": "Extraction initiated",
            "case_id": case_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting extraction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-data/{code}")
async def upload_data_batch(code: str, request: Request):
    """
    Upload extracted data batch from WebUSB agent.
    Called incrementally as data is extracted.
    """
    code = code.lower()

    if code not in recovery_codes:
        raise HTTPException(status_code=404, detail="Invalid recovery code")

    case_id = recovery_codes[code]
    case = recovery_cases.get(case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")

    try:
        body = await request.json()
        data_type = body.get("data_type")
        count = body.get("count", 0)
        device_serial = body.get("device_serial")

        # Update statistics
        if "extracted_stats" not in case:
            case["extracted_stats"] = {
                "photos": 0,
                "videos": 0,
                "messages": 0,
                "contacts": 0,
                "callLogs": 0,
                "deletedFiles": 0
            }

        if data_type in case["extracted_stats"]:
            case["extracted_stats"][data_type] = count

        # Calculate progress based on data type weights
        weights = {
            "photos": 30,
            "videos": 25,
            "messages": 15,
            "contacts": 10,
            "callLogs": 10,
            "deletedFiles": 10
        }

        completed_weight = sum(
            weights.get(k, 0)
            for k, v in case["extracted_stats"].items()
            if v > 0
        )
        case["progress_percent"] = min(5 + completed_weight, 95)
        case["current_step"] = f"Extracted {data_type}: {count} items"

        logger.info(f"Data batch uploaded for case {case_id}: {data_type} = {count}")

        return {"success": True, "data_type": data_type, "count": count}

    except Exception as e:
        logger.error(f"Error uploading data batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/finalize/{code}")
async def finalize_extraction(code: str, request: Request):
    """
    Finalize WebUSB extraction and create results package.
    Called when all data has been extracted.
    """
    code = code.lower()

    if code not in recovery_codes:
        raise HTTPException(status_code=404, detail="Invalid recovery code")

    case_id = recovery_codes[code]
    case = recovery_cases.get(case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")

    try:
        body = await request.json()
        statistics = body.get("statistics", {})
        device_serial = body.get("device_serial")

        # Create output directory
        output_dir = OUTPUT_BASE / case_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save statistics and metadata
        metadata = {
            "case_id": case_id,
            "client_number": case.get("client_number"),
            "device_type": case.get("device_info", {}).get("device_type"),
            "device_serial": device_serial,
            "extraction_method": "webusb",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "statistics": statistics
        }

        metadata_path = output_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        # Create ZIP archive
        zip_path = OUTPUT_BASE / f"{case_id}.zip"
        shutil.make_archive(str(zip_path.with_suffix("")), "zip", output_dir)

        # Calculate checksum
        checksum = await _calculate_checksum(zip_path)

        # Update case
        case["status"] = "completed"
        case["progress_percent"] = 100
        case["current_step"] = "Recovery complete"
        case["completed_at"] = datetime.now(timezone.utc).isoformat()
        case["results"] = {
            "zip_path": str(zip_path),
            "zip_size": zip_path.stat().st_size if zip_path.exists() else 0,
            "checksum_sha256": checksum,
            "encrypted": False
        }
        case["processed"] = {
            "extracted_dir": str(output_dir),
            "statistics": statistics,
            "deleted_files_recovered": statistics.get("deletedFiles", 0)
        }

        # Log completion
        case["chain_of_custody"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": "WebUSB Agent",
            "action": "EXTRACTION_COMPLETED",
            "details": f"WebUSB extraction completed. Stats: {statistics}"
        })

        logger.info(f"Extraction finalized for case {case_id}")

        return {
            "success": True,
            "message": "Extraction finalized",
            "case_id": case_id,
            "statistics": statistics
        }

    except Exception as e:
        logger.error(f"Error finalizing extraction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Mobile Agent Endpoints (Scenario 2: Client has no computer)
# =============================================================================

@router.post("/start-agent/{code}")
async def start_mobile_agent(code: str, request: Request):
    """
    Start mobile agent recovery (APK or MDM).
    Called when client enters screen lock on mobile device.
    """
    code = code.lower()

    if code not in recovery_codes:
        raise HTTPException(status_code=404, detail="Invalid recovery code")

    case_id = recovery_codes[code]
    case = recovery_cases.get(case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")

    try:
        body = await request.json()
        screen_lock = body.get("screen_lock")
        is_mobile = body.get("is_mobile", True)
        platform = body.get("platform", "android")

        if not screen_lock or len(screen_lock) < 4:
            raise HTTPException(status_code=400, detail="Screen lock code is required (min 4 characters)")

        # Store screen lock securely (encrypted in production)
        case["screen_lock_hash"] = hashlib.sha256(screen_lock.encode()).hexdigest()
        case["agent_platform"] = platform
        case["is_mobile_recovery"] = is_mobile

        # Update status
        case["status"] = "agent_started"
        case["current_step"] = f"Mobile agent started on {platform}"
        case["progress_percent"] = 5

        # Log custody event
        case["chain_of_custody"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": f"Client: {case.get('client_number')}",
            "action": "MOBILE_AGENT_STARTED",
            "details": f"Mobile agent recovery started on {platform}"
        })

        logger.info(f"Mobile agent started for case {case_id} on {platform}")

        return {
            "success": True,
            "message": "Mobile agent recovery initiated",
            "case_id": case_id,
            "platform": platform
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting mobile agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ios-profile/{code}")
async def download_ios_mdm_profile(code: str):
    """
    Generate and download iOS MDM profile for mobile-only recovery.
    This is a placeholder - real MDM requires Apple Developer Account.
    """
    code = code.lower()

    if code not in recovery_codes:
        raise HTTPException(status_code=404, detail="Invalid recovery code")

    case_id = recovery_codes[code]
    case = recovery_cases.get(case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")

    # Generate MDM profile (placeholder)
    # In production, this would be a signed .mobileconfig file
    # from an Apple Developer Enterprise account

    profile_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>PayloadContent</key>
    <array>
        <dict>
            <key>PayloadDescription</key>
            <string>SafeChild Data Recovery Profile</string>
            <key>PayloadDisplayName</key>
            <string>SafeChild Recovery</string>
            <key>PayloadIdentifier</key>
            <string>com.safechild.recovery.{case_id}</string>
            <key>PayloadType</key>
            <string>com.apple.mdm</string>
            <key>PayloadUUID</key>
            <string>{uuid.uuid4()}</string>
            <key>PayloadVersion</key>
            <integer>1</integer>
        </dict>
    </array>
    <key>PayloadDescription</key>
    <string>SafeChild forensic data recovery profile. This profile enables secure data extraction for legal proceedings.</string>
    <key>PayloadDisplayName</key>
    <string>SafeChild Recovery - {case.get('client_number', 'Unknown')}</string>
    <key>PayloadIdentifier</key>
    <string>com.safechild.mdm.{code}</string>
    <key>PayloadOrganization</key>
    <string>SafeChild Law Firm</string>
    <key>PayloadRemovalDisallowed</key>
    <false/>
    <key>PayloadType</key>
    <string>Configuration</string>
    <key>PayloadUUID</key>
    <string>{uuid.uuid4()}</string>
    <key>PayloadVersion</key>
    <integer>1</integer>
</dict>
</plist>
"""

    # Log profile download
    case["chain_of_custody"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": f"Client: {case.get('client_number')}",
        "action": "MDM_PROFILE_DOWNLOADED",
        "details": "iOS MDM profile downloaded for installation"
    })

    from fastapi.responses import Response
    return Response(
        content=profile_content,
        media_type="application/x-apple-aspen-config",
        headers={
            "Content-Disposition": f"attachment; filename=SafeChild_Recovery_{code}.mobileconfig"
        }
    )


@router.get("/apk-download-link/{code}")
async def get_apk_download_link(code: str):
    """
    Get APK download link for Android mobile-only recovery.
    """
    code = code.lower()

    if code not in recovery_codes:
        raise HTTPException(status_code=404, detail="Invalid recovery code")

    case_id = recovery_codes[code]
    case = recovery_cases.get(case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")

    # Log APK download intent
    case["chain_of_custody"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": f"Client: {case.get('client_number')}",
        "action": "APK_DOWNLOAD_REQUESTED",
        "details": "Android APK download link requested"
    })

    return {
        "download_url": f"{BASE_URL}/download/safechild-recovery.apk",
        "recovery_code": code,
        "instructions": [
            "1. APK dosyasini indirin",
            "2. 'Bilinmeyen kaynaklara izin ver' secenegini acin",
            "3. APK'yi yukleyin",
            "4. Uygulamayi acin ve kurtarma kodunu girin",
            "5. Istenen izinleri verin",
            "6. 'Baslat' butonuna basin"
        ]
    }


# =============================================================================
# Admin Delete Endpoint
# =============================================================================

@router.delete("/cases/{case_id}")
async def delete_recovery_case(case_id: str):
    """Delete a recovery case and all associated files (admin endpoint)."""
    if case_id not in recovery_cases:
        raise HTTPException(status_code=404, detail="Recovery case not found")

    case = recovery_cases[case_id]

    # Delete files
    upload_dir = UPLOAD_BASE / case_id
    if upload_dir.exists():
        shutil.rmtree(upload_dir)

    output_dir = OUTPUT_BASE / case_id
    if output_dir.exists():
        shutil.rmtree(output_dir)

    zip_path = OUTPUT_BASE / f"{case_id}.zip"
    if zip_path.exists():
        zip_path.unlink()

    # Remove from storage
    recovery_code = case.get("recovery_code")
    if recovery_code and recovery_code in recovery_codes:
        del recovery_codes[recovery_code]

    del recovery_cases[case_id]

    return {"success": True, "message": f"Recovery case {case_id} deleted"}
