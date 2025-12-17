"""
USB Recovery Router
API endpoints for USB-connected phone recovery (admin-only).
Handles device detection, authorization, backup creation, and data extraction.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path
import logging
import uuid
import os

from backend.models import (
    USBDeviceInfo,
    StartUSBRecoveryRequest,
    RecoveryStatusResponse,
    PhoneRecoveryCase,
    RecoveryCustodyEvent,
    DeviceInfo,
    DataCategories,
    DeletionSchedule,
    RecoveryStatistics,
)
from backend.forensics.usb_device_manager import get_device_manager
from backend.forensics.android_extractor import AndroidExtractor
from backend.forensics.ios_extractor import iOSExtractor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/usb-recovery", tags=["USB Recovery"])

# In-memory storage for active recoveries (would use MongoDB in production)
active_recoveries = {}

# Base paths
RECOVERY_BASE = Path("/tmp/phone_recovery")
OUTPUT_BASE = Path("/tmp/recovery_output")


def get_db():
    """Get database connection - placeholder for dependency injection"""
    from backend.database import get_database
    return get_database()


@router.get("/devices", response_model=List[USBDeviceInfo])
async def list_connected_devices():
    """
    List all connected USB devices (Android and iOS).
    Returns device info including authorization status.
    """
    try:
        device_manager = get_device_manager()
        devices = await device_manager.scan_devices()

        return [
            USBDeviceInfo(
                device_id=d.device_id,
                device_type=d.device_type,
                device_model=d.device_model,
                serial_number=d.serial_number,
                is_authorized=d.is_authorized,
                storage_info={
                    "total": d.storage_total,
                    "manufacturer": d.manufacturer,
                    "os_version": d.os_version
                } if d.storage_total else None
            )
            for d in devices
        ]

    except Exception as e:
        logger.error(f"Error listing devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/devices/{device_id}/auth")
async def authorize_device(device_id: str):
    """
    Authorize a device for data extraction.
    For Android: Triggers ADB authorization (user must confirm on device).
    For iOS: Device must be trusted (user confirms on device).
    """
    try:
        device_manager = get_device_manager()
        success = await device_manager.authorize_device(device_id)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Authorization failed. Please confirm on the device and try again."
            )

        return {"success": True, "message": "Device authorized successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error authorizing device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices/{device_id}/info", response_model=USBDeviceInfo)
async def get_device_info(device_id: str):
    """Get detailed information for a specific connected device."""
    try:
        device_manager = get_device_manager()
        device = await device_manager.get_device_info(device_id)

        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        return USBDeviceInfo(
            device_id=device.device_id,
            device_type=device.device_type,
            device_model=device.device_model,
            serial_number=device.serial_number,
            is_authorized=device.is_authorized,
            storage_info={
                "total": device.storage_total,
                "manufacturer": device.manufacturer,
                "os_version": device.os_version
            } if device.storage_total else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_usb_recovery(
    request: StartUSBRecoveryRequest,
    background_tasks: BackgroundTasks
):
    """
    Start USB recovery process for a connected device.
    This creates a backup and extracts all data including deleted files.
    """
    try:
        device_manager = get_device_manager()
        device = await device_manager.get_device_info(request.device_id)

        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        if not device.is_authorized:
            raise HTTPException(
                status_code=400,
                detail="Device not authorized. Please authorize first."
            )

        # Generate case ID
        timestamp = datetime.now().strftime("%Y%m%d")
        case_id = f"RECOVERY_{request.client_number}_{timestamp}_{uuid.uuid4().hex[:6].upper()}"

        # Create recovery case
        recovery_case = PhoneRecoveryCase(
            case_id=case_id,
            client_number=request.client_number,
            recovery_method="usb",
            device_info=DeviceInfo(
                device_type=device.device_type,
                device_model=device.device_model,
                os_version=device.os_version,
                serial_number=device.serial_number,
                storage_total=device.storage_total,
                connection_type="usb"
            ),
            data_categories=request.data_categories or DataCategories(),
            status="processing",
            current_step="Initializing recovery...",
            deletion_schedule=DeletionSchedule(
                auto_delete_at=datetime.now(timezone.utc) + timedelta(days=15)
            ),
            chain_of_custody=[
                RecoveryCustodyEvent(
                    actor=f"System: USB Recovery",
                    action="RECOVERY_STARTED",
                    details=f"USB recovery initiated for device {device.device_model or device.device_id}"
                )
            ]
        )

        # Store in active recoveries
        active_recoveries[case_id] = recovery_case.model_dump()

        # Start background recovery process
        background_tasks.add_task(
            _process_usb_recovery,
            case_id,
            request.device_id,
            device.device_type,
            request.data_categories or DataCategories()
        )

        return {
            "success": True,
            "case_id": case_id,
            "message": "Recovery started. Monitor progress via /usb-recovery/cases/{case_id}/status"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting USB recovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _process_usb_recovery(
    case_id: str,
    device_id: str,
    device_type: str,
    data_categories: DataCategories
):
    """Background task to process USB recovery"""
    try:
        output_dir = OUTPUT_BASE / case_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Update status
        if case_id in active_recoveries:
            active_recoveries[case_id]["current_step"] = "Creating device backup..."
            active_recoveries[case_id]["progress_percent"] = 10

        if device_type == "android":
            await _process_android_recovery(case_id, device_id, output_dir, data_categories)
        else:
            await _process_ios_recovery(case_id, device_id, output_dir, data_categories)

    except Exception as e:
        logger.error(f"Error in USB recovery process: {e}")
        if case_id in active_recoveries:
            active_recoveries[case_id]["status"] = "failed"
            active_recoveries[case_id]["current_step"] = f"Error: {str(e)}"


async def _process_android_recovery(
    case_id: str,
    device_id: str,
    output_dir: Path,
    data_categories: DataCategories
):
    """Process Android device recovery"""
    extractor = AndroidExtractor(device_id, RECOVERY_BASE)

    stats = RecoveryStatistics()

    # Step 1: Create backup
    if case_id in active_recoveries:
        active_recoveries[case_id]["current_step"] = "Creating ADB backup (confirm on device)..."
        active_recoveries[case_id]["progress_percent"] = 15

    backup_result = await extractor.create_backup(
        output_path=RECOVERY_BASE / f"{case_id}.ab",
        include_shared=True
    )

    if not backup_result.success:
        raise Exception(f"Backup failed: {backup_result.error}")

    # Step 2: Extract backup
    if case_id in active_recoveries:
        active_recoveries[case_id]["current_step"] = "Extracting backup data..."
        active_recoveries[case_id]["progress_percent"] = 30

    extract_result = await extractor.extract_backup(
        backup_result.backup_path,
        output_dir / "extracted"
    )

    if extract_result.success:
        stats.photos = extract_result.categories.get("photos", 0)
        stats.videos = extract_result.categories.get("videos", 0)
        stats.messages = extract_result.categories.get("messages", 0)
        stats.app_files = extract_result.categories.get("app_data", 0)

    # Step 3: Pull additional media
    if data_categories.photos or data_categories.videos:
        if case_id in active_recoveries:
            active_recoveries[case_id]["current_step"] = "Pulling media files..."
            active_recoveries[case_id]["progress_percent"] = 50

        media_counts = await extractor.pull_media(output_dir / "media")
        stats.photos += media_counts.get("photos", 0)
        stats.videos += media_counts.get("videos", 0)

    # Step 4: Extract contacts and call logs
    if data_categories.contacts:
        if case_id in active_recoveries:
            active_recoveries[case_id]["current_step"] = "Extracting contacts..."
            active_recoveries[case_id]["progress_percent"] = 60

        contacts_path = output_dir / "contacts" / "contacts.txt"
        contacts_path.parent.mkdir(parents=True, exist_ok=True)
        await extractor.get_contacts(contacts_path)

    if data_categories.call_logs:
        if case_id in active_recoveries:
            active_recoveries[case_id]["current_step"] = "Extracting call history..."
            active_recoveries[case_id]["progress_percent"] = 65

        calls_path = output_dir / "call_logs" / "calls.txt"
        calls_path.parent.mkdir(parents=True, exist_ok=True)
        await extractor.get_call_log(calls_path)

    # Step 5: Extract SMS
    if data_categories.messages:
        if case_id in active_recoveries:
            active_recoveries[case_id]["current_step"] = "Extracting SMS messages..."
            active_recoveries[case_id]["progress_percent"] = 70

        sms_path = output_dir / "messages" / "sms.txt"
        sms_path.parent.mkdir(parents=True, exist_ok=True)
        await extractor.get_sms(sms_path)

    # Step 6: Extract app data (WhatsApp, Telegram, etc.)
    if data_categories.app_data:
        if case_id in active_recoveries:
            active_recoveries[case_id]["current_step"] = "Extracting app data..."
            active_recoveries[case_id]["progress_percent"] = 75

        app_results = await extractor.extract_app_data(output_dir=output_dir / "apps")

    # Step 7: Recover deleted files
    if data_categories.deleted_data:
        if case_id in active_recoveries:
            active_recoveries[case_id]["current_step"] = "Recovering deleted files..."
            active_recoveries[case_id]["progress_percent"] = 85

        # Use file carving module
        from backend.forensics.recovery.file_carving import carve_deleted_files
        deleted_count = await carve_deleted_files(
            output_dir / "extracted",
            output_dir / "deleted_recovered"
        )
        stats.deleted_files = deleted_count

    # Step 8: Package results
    if case_id in active_recoveries:
        active_recoveries[case_id]["current_step"] = "Packaging results..."
        active_recoveries[case_id]["progress_percent"] = 95

    await _package_results(case_id, output_dir, stats)


async def _process_ios_recovery(
    case_id: str,
    device_id: str,
    output_dir: Path,
    data_categories: DataCategories
):
    """Process iOS device recovery"""
    extractor = iOSExtractor(device_id, RECOVERY_BASE)

    stats = RecoveryStatistics()

    # Step 1: Create backup
    if case_id in active_recoveries:
        active_recoveries[case_id]["current_step"] = "Creating iOS backup (confirm on device)..."
        active_recoveries[case_id]["progress_percent"] = 15

    backup_result = await extractor.create_backup(
        output_path=RECOVERY_BASE / case_id
    )

    if not backup_result.success:
        raise Exception(f"Backup failed: {backup_result.error}")

    if backup_result.is_encrypted:
        raise Exception("Encrypted backup - cannot process without password")

    # Step 2: Extract backup
    if case_id in active_recoveries:
        active_recoveries[case_id]["current_step"] = "Extracting backup data..."
        active_recoveries[case_id]["progress_percent"] = 30

    extract_result = await extractor.extract_backup(
        backup_result.backup_path,
        output_dir / "extracted"
    )

    if extract_result.success:
        stats.photos = extract_result.categories.get("photos", 0)
        stats.videos = extract_result.categories.get("videos", 0)
        stats.messages = extract_result.categories.get("messages", 0)
        stats.app_files = extract_result.categories.get("app_data", 0)

    # Step 3: Extract messages
    if data_categories.messages:
        if case_id in active_recoveries:
            active_recoveries[case_id]["current_step"] = "Extracting iMessage/SMS..."
            active_recoveries[case_id]["progress_percent"] = 50

        msg_result = await extractor.extract_messages(
            backup_result.backup_path,
            output_dir / "messages" / "imessage.json"
        )
        if msg_result.success:
            stats.messages = msg_result.message_count

    # Step 4: Extract contacts
    if data_categories.contacts:
        if case_id in active_recoveries:
            active_recoveries[case_id]["current_step"] = "Extracting contacts..."
            active_recoveries[case_id]["progress_percent"] = 60

        await extractor.get_contacts(
            backup_result.backup_path,
            output_dir / "contacts" / "contacts.json"
        )

    # Step 5: Extract call history
    if data_categories.call_logs:
        if case_id in active_recoveries:
            active_recoveries[case_id]["current_step"] = "Extracting call history..."
            active_recoveries[case_id]["progress_percent"] = 65

        await extractor.get_call_history(
            backup_result.backup_path,
            output_dir / "call_logs" / "calls.json"
        )

    # Step 6: Extract WhatsApp
    if data_categories.app_data:
        if case_id in active_recoveries:
            active_recoveries[case_id]["current_step"] = "Extracting WhatsApp data..."
            active_recoveries[case_id]["progress_percent"] = 75

        wa_result = await extractor.extract_whatsapp(
            backup_result.backup_path,
            output_dir / "apps" / "whatsapp"
        )

    # Step 7: Recover deleted files
    if data_categories.deleted_data:
        if case_id in active_recoveries:
            active_recoveries[case_id]["current_step"] = "Recovering deleted files..."
            active_recoveries[case_id]["progress_percent"] = 85

        from backend.forensics.recovery.file_carving import carve_deleted_files
        deleted_count = await carve_deleted_files(
            output_dir / "extracted",
            output_dir / "deleted_recovered"
        )
        stats.deleted_files = deleted_count

    # Step 8: Package results
    if case_id in active_recoveries:
        active_recoveries[case_id]["current_step"] = "Packaging results..."
        active_recoveries[case_id]["progress_percent"] = 95

    await _package_results(case_id, output_dir, stats)


async def _package_results(case_id: str, output_dir: Path, stats: RecoveryStatistics):
    """Package recovery results into a ZIP file"""
    import shutil
    import hashlib
    import json

    # Calculate total size
    total_size = sum(f.stat().st_size for f in output_dir.rglob("*") if f.is_file())
    stats.total_size = total_size

    # Create metadata file
    metadata = {
        "case_id": case_id,
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

    # Create ZIP archive
    zip_path = OUTPUT_BASE / f"{case_id}.zip"
    shutil.make_archive(str(zip_path.with_suffix("")), "zip", output_dir)

    # Calculate checksum
    with open(zip_path, "rb") as f:
        checksum = hashlib.sha256(f.read()).hexdigest()

    # Update recovery case
    if case_id in active_recoveries:
        active_recoveries[case_id]["status"] = "completed"
        active_recoveries[case_id]["progress_percent"] = 100
        active_recoveries[case_id]["current_step"] = "Recovery complete"
        active_recoveries[case_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
        active_recoveries[case_id]["results"] = {
            "zip_path": str(zip_path),
            "zip_size": zip_path.stat().st_size,
            "checksum_sha256": checksum,
            "encrypted": False
        }
        active_recoveries[case_id]["processed"] = {
            "extracted_dir": str(output_dir),
            "statistics": stats.model_dump(),
            "deleted_files_recovered": stats.deleted_files
        }

        # Add custody event
        active_recoveries[case_id]["chain_of_custody"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": "System",
            "action": "RECOVERY_COMPLETED",
            "details": f"Recovery completed. {stats.total_size / (1024*1024):.2f} MB processed."
        })


@router.get("/cases/{case_id}/status", response_model=RecoveryStatusResponse)
async def get_recovery_status(case_id: str):
    """Get the current status and progress of a recovery operation."""
    if case_id not in active_recoveries:
        raise HTTPException(status_code=404, detail="Recovery case not found")

    recovery = active_recoveries[case_id]

    return RecoveryStatusResponse(
        case_id=case_id,
        status=recovery.get("status", "unknown"),
        progress_percent=recovery.get("progress_percent", 0),
        current_step=recovery.get("current_step"),
        statistics=recovery.get("processed", {}).get("statistics") if recovery.get("processed") else None,
        download_ready=recovery.get("status") == "completed"
    )


@router.get("/cases/{case_id}/download")
async def download_recovery_results(case_id: str):
    """Download the recovery results ZIP file."""
    if case_id not in active_recoveries:
        raise HTTPException(status_code=404, detail="Recovery case not found")

    recovery = active_recoveries[case_id]

    if recovery.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Recovery not yet completed")

    zip_path = recovery.get("results", {}).get("zip_path")
    if not zip_path or not Path(zip_path).exists():
        raise HTTPException(status_code=404, detail="Results file not found")

    # Log download event
    recovery["chain_of_custody"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": "Admin",
        "action": "RESULTS_DOWNLOADED",
        "details": "Recovery results ZIP downloaded"
    })

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{case_id}_recovery.zip"
    )


@router.get("/cases")
async def list_recovery_cases():
    """List all recovery cases (active and completed)."""
    cases = []
    for case_id, recovery in active_recoveries.items():
        cases.append({
            "case_id": case_id,
            "client_number": recovery.get("client_number"),
            "status": recovery.get("status"),
            "progress_percent": recovery.get("progress_percent", 0),
            "device_type": recovery.get("device_info", {}).get("device_type"),
            "created_at": recovery.get("created_at"),
            "completed_at": recovery.get("completed_at")
        })
    return cases


@router.delete("/cases/{case_id}")
async def delete_recovery_case(case_id: str):
    """Delete a recovery case and all associated files."""
    if case_id not in active_recoveries:
        raise HTTPException(status_code=404, detail="Recovery case not found")

    import shutil

    # Delete output directory
    output_dir = OUTPUT_BASE / case_id
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Delete ZIP file
    zip_path = OUTPUT_BASE / f"{case_id}.zip"
    if zip_path.exists():
        zip_path.unlink()

    # Delete backup files
    for backup_file in RECOVERY_BASE.glob(f"{case_id}*"):
        if backup_file.is_file():
            backup_file.unlink()
        elif backup_file.is_dir():
            shutil.rmtree(backup_file)

    # Remove from active recoveries
    del active_recoveries[case_id]

    return {"success": True, "message": f"Recovery case {case_id} deleted"}
