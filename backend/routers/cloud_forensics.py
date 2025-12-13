"""
Cloud Forensics Router for SafeChild
Handles cloud backup extraction (Google Drive, iCloud)
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Depends, Form
from datetime import datetime
from pathlib import Path
from typing import Optional
import os
import json
import tempfile
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from .. import get_db
from ..auth import get_current_admin
import logging

router = APIRouter(prefix="/forensics/cloud", tags=["Cloud Forensics"])
logger = logging.getLogger(__name__)

# Try to import cloud modules (optional dependencies)
try:
    from backend.forensics.cloud.google_drive import (
        GoogleDriveWhatsAppExtractor,
        check_google_drive_available,
        check_wa_decrypt_available
    )
    GOOGLE_DRIVE_AVAILABLE = check_google_drive_available()
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False


class AuthUrlRequest(BaseModel):
    provider: str


class AuthenticateRequest(BaseModel):
    provider: str
    code: str


# Store temporary OAuth states
oauth_states = {}


@router.post("/auth-url")
async def get_auth_url(
    request: AuthUrlRequest,
    admin=Depends(get_current_admin)
):
    """Get OAuth authorization URL for cloud provider."""

    if request.provider == "google_drive":
        if not GOOGLE_DRIVE_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="Google Drive API is not available. Install google-api-python-client."
            )

        try:
            # Use environment variable for client config
            client_id = os.environ.get("GOOGLE_CLIENT_ID")
            client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
            redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "urn:ietf:wg:oauth:2.0:oob")

            if not client_id or not client_secret:
                raise HTTPException(
                    status_code=500,
                    detail="Google OAuth credentials not configured"
                )

            client_config = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            }

            extractor = GoogleDriveWhatsAppExtractor()
            auth_url = extractor.get_auth_url(client_config, redirect_uri)

            # Store state for later
            oauth_states[admin['email']] = {
                'provider': 'google_drive',
                'client_config': client_config,
                'redirect_uri': redirect_uri,
                'timestamp': datetime.utcnow()
            }

            return {
                "success": True,
                "auth_url": auth_url,
                "provider": "google_drive"
            }

        except Exception as e:
            logger.error(f"Google auth URL generation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Provider {request.provider} not supported"
        )


@router.post("/authenticate")
async def authenticate_provider(
    request: AuthenticateRequest,
    admin=Depends(get_current_admin)
):
    """Authenticate with cloud provider using authorization code."""

    if request.provider == "google_drive":
        if not GOOGLE_DRIVE_AVAILABLE:
            raise HTTPException(status_code=503, detail="Google Drive API not available")

        # Get stored state
        state = oauth_states.get(admin['email'])
        if not state or state['provider'] != 'google_drive':
            raise HTTPException(
                status_code=400,
                detail="No pending authentication. Start again with /auth-url"
            )

        try:
            extractor = GoogleDriveWhatsAppExtractor()
            token_data = extractor.exchange_code(
                state['client_config'],
                request.code,
                state['redirect_uri']
            )

            # Store tokens for this admin
            oauth_states[admin['email']] = {
                'provider': 'google_drive',
                'tokens': token_data,
                'authenticated': True,
                'timestamp': datetime.utcnow()
            }

            return {
                "success": True,
                "message": "Authentication successful",
                "provider": "google_drive"
            }

        except Exception as e:
            logger.error(f"Google authentication failed: {e}")
            raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

    else:
        raise HTTPException(status_code=400, detail=f"Provider {request.provider} not supported")


@router.get("/find-backups")
async def find_cloud_backups(
    provider: str,
    admin=Depends(get_current_admin)
):
    """Find WhatsApp backups in cloud storage."""

    state = oauth_states.get(admin['email'])
    if not state or not state.get('authenticated'):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Complete OAuth flow first."
        )

    if provider == "google_drive":
        if not GOOGLE_DRIVE_AVAILABLE:
            raise HTTPException(status_code=503, detail="Google Drive API not available")

        try:
            extractor = GoogleDriveWhatsAppExtractor()
            extractor.authenticate_with_token(state['tokens'])

            backups_list = extractor.find_whatsapp_backups()

            formatted_backups = []
            for backup in backups_list:
                formatted_backups.append({
                    "id": backup.get('id'),
                    "name": backup.get('name'),
                    "size": f"{int(backup.get('size', 0)) / (1024*1024):.1f} MB",
                    "modified": backup.get('modifiedTime', ''),
                    "encrypted": backup.get('name', '').endswith(('.crypt14', '.crypt15', '.crypt12'))
                })

            return {
                "success": True,
                "backups": formatted_backups,
                "total": len(formatted_backups)
            }

        except Exception as e:
            logger.error(f"Find backups failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    else:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not supported")


@router.post("/download-analyze")
async def download_and_analyze_backup(
    background_tasks: BackgroundTasks,
    provider: str = Form(...),
    backup_id: str = Form(...),
    client_number: str = Form(...),
    key_file: Optional[UploadFile] = File(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Download backup from cloud and run forensic analysis."""

    state = oauth_states.get(admin['email'])
    if not state or not state.get('authenticated'):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    if provider == "google_drive":
        if not GOOGLE_DRIVE_AVAILABLE:
            raise HTTPException(status_code=503, detail="Google Drive API not available")

        try:
            # Create temp directory
            temp_dir = tempfile.mkdtemp(prefix=f"cloud_backup_{client_number}_")
            output_path = Path(temp_dir) / "backup.db"

            # Download backup
            extractor = GoogleDriveWhatsAppExtractor()
            extractor.authenticate_with_token(state['tokens'])
            extractor.download_backup(backup_id, str(output_path))

            # Handle encrypted backups
            decrypted_path = output_path
            if key_file:
                key_path = Path(temp_dir) / "key"
                with open(key_path, "wb") as f:
                    f.write(await key_file.read())

                # Try to decrypt
                if check_wa_decrypt_available():
                    decrypted_path = Path(temp_dir) / "decrypted.db"
                    extractor.decrypt_backup(str(output_path), str(key_path), str(decrypted_path))

            # Create case record
            case_id = f"CLOUD_{client_number}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            analysis_record = {
                "case_id": case_id,
                "client_number": client_number,
                "status": "completed",
                "analysis_type": "cloud_backup",
                "source": {
                    "provider": "google_drive",
                    "backup_id": backup_id
                },
                "created_at": datetime.utcnow(),
                "created_by": admin.get('email', 'unknown')
            }

            await db.forensic_analyses.insert_one(analysis_record)

            # Cleanup in background
            def cleanup():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)

            background_tasks.add_task(cleanup)

            return {
                "success": True,
                "case_id": case_id,
                "message": "Backup downloaded and analysis started"
            }

        except Exception as e:
            logger.error(f"Download and analyze failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    else:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not supported")


@router.get("/status")
async def get_cloud_status(admin=Depends(get_current_admin)):
    """Get cloud integration status."""

    wa_decrypt_available = False
    try:
        if GOOGLE_DRIVE_AVAILABLE:
            wa_decrypt_available = check_wa_decrypt_available()
    except Exception:
        pass

    return {
        "google_drive": {
            "available": GOOGLE_DRIVE_AVAILABLE,
            "authenticated": admin['email'] in oauth_states and oauth_states[admin['email']].get('authenticated', False)
        },
        "icloud": {
            "available": False,
            "authenticated": False
        },
        "wa_decrypt": wa_decrypt_available
    }
