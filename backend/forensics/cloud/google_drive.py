"""
Google Drive Integration for SafeChild Forensics
Extracts WhatsApp backups from Google Drive (with user consent)

Requires:
- google-api-python-client
- google-auth-oauthlib
- wa-crypt-tools (for decryption)
"""

import os
import io
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

try:
    from wa_crypt_tools.wadecrypt import decrypt_backup
    WA_CRYPT_AVAILABLE = True
except ImportError:
    WA_CRYPT_AVAILABLE = False

logger = logging.getLogger(__name__)

# Scopes required for WhatsApp backup access
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly'
]

# WhatsApp backup file patterns
WHATSAPP_BACKUP_PATTERNS = [
    'msgstore.db.crypt14',
    'msgstore.db.crypt15',
    'msgstore.db.crypt12',
    'wa.db',
]


class GoogleDriveWhatsAppExtractor:
    """
    Extracts WhatsApp backups from Google Drive.

    Flow:
    1. User provides OAuth consent
    2. Find WhatsApp backup folder
    3. Download encrypted backup
    4. Decrypt with key (if available)
    """

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize extractor.

        Args:
            credentials_path: Path to OAuth client credentials JSON
        """
        if not GOOGLE_API_AVAILABLE:
            raise ImportError(
                "Google API libraries not installed. "
                "Run: pip install google-api-python-client google-auth-oauthlib"
            )

        self.credentials_path = credentials_path
        self.credentials: Optional[Credentials] = None
        self.service = None

    def authenticate_with_token(self, token_data: Dict[str, Any]) -> bool:
        """
        Authenticate using existing token data.

        Args:
            token_data: Token dictionary from previous auth

        Returns:
            True if authentication successful
        """
        try:
            self.credentials = Credentials.from_authorized_user_info(token_data, SCOPES)

            # Refresh if expired
            if self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())

            self.service = build('drive', 'v3', credentials=self.credentials)
            return True

        except Exception as e:
            logger.error(f"Token authentication failed: {e}")
            return False

    def get_auth_url(self, client_config: Dict[str, Any], redirect_uri: str) -> str:
        """
        Get OAuth authorization URL for user consent.

        Args:
            client_config: OAuth client configuration
            redirect_uri: Redirect URI after consent

        Returns:
            Authorization URL
        """
        flow = InstalledAppFlow.from_client_config(
            client_config,
            SCOPES,
            redirect_uri=redirect_uri
        )

        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        return auth_url

    def exchange_code(self, client_config: Dict[str, Any],
                      code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens.

        Args:
            client_config: OAuth client configuration
            code: Authorization code from redirect
            redirect_uri: Same redirect URI used in auth

        Returns:
            Token data dictionary
        """
        flow = InstalledAppFlow.from_client_config(
            client_config,
            SCOPES,
            redirect_uri=redirect_uri
        )

        flow.fetch_token(code=code)
        self.credentials = flow.credentials
        self.service = build('drive', 'v3', credentials=self.credentials)

        return {
            'token': self.credentials.token,
            'refresh_token': self.credentials.refresh_token,
            'token_uri': self.credentials.token_uri,
            'client_id': self.credentials.client_id,
            'client_secret': self.credentials.client_secret,
            'scopes': list(self.credentials.scopes),
            'expiry': self.credentials.expiry.isoformat() if self.credentials.expiry else None
        }

    def find_whatsapp_backups(self) -> List[Dict[str, Any]]:
        """
        Find WhatsApp backup files in Google Drive.

        Returns:
            List of backup file metadata
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate first.")

        backups = []

        try:
            # Search for WhatsApp backup folder
            folder_query = "name = 'WhatsApp' and mimeType = 'application/vnd.google-apps.folder'"
            folder_results = self.service.files().list(
                q=folder_query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            whatsapp_folders = folder_results.get('files', [])

            for folder in whatsapp_folders:
                folder_id = folder['id']

                # Search for backup files in folder and subfolders
                for pattern in WHATSAPP_BACKUP_PATTERNS:
                    file_query = f"name contains '{pattern}'"

                    file_results = self.service.files().list(
                        q=file_query,
                        spaces='drive',
                        fields='files(id, name, size, modifiedTime, mimeType)',
                        orderBy='modifiedTime desc'
                    ).execute()

                    for file in file_results.get('files', []):
                        backups.append({
                            'id': file['id'],
                            'name': file['name'],
                            'size': int(file.get('size', 0)),
                            'modified': file.get('modifiedTime'),
                            'mime_type': file.get('mimeType'),
                            'is_encrypted': 'crypt' in file['name'].lower()
                        })

            logger.info(f"Found {len(backups)} WhatsApp backup files")
            return backups

        except Exception as e:
            logger.error(f"Failed to search for backups: {e}")
            raise

    def download_backup(self, file_id: str, output_path: str) -> Path:
        """
        Download a backup file from Google Drive.

        Args:
            file_id: Google Drive file ID
            output_path: Local path to save file

        Returns:
            Path to downloaded file
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate first.")

        try:
            request = self.service.files().get_media(fileId=file_id)

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        logger.debug(f"Download progress: {int(status.progress() * 100)}%")

            logger.info(f"Downloaded backup to {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Failed to download backup: {e}")
            raise

    def decrypt_backup(self, encrypted_path: str, key_path: str,
                       output_path: str) -> Optional[Path]:
        """
        Decrypt WhatsApp backup using key file.

        Args:
            encrypted_path: Path to encrypted backup
            key_path: Path to key file (extracted from device)
            output_path: Path for decrypted output

        Returns:
            Path to decrypted file, or None if failed
        """
        if not WA_CRYPT_AVAILABLE:
            logger.error("wa-crypt-tools not installed")
            return None

        try:
            decrypt_backup(
                encrypted_path,
                key_path,
                output_path
            )

            logger.info(f"Decrypted backup to {output_path}")
            return Path(output_path)

        except Exception as e:
            logger.error(f"Failed to decrypt backup: {e}")
            return None


def check_google_drive_available() -> bool:
    """Check if Google Drive API is available."""
    return GOOGLE_API_AVAILABLE


def check_wa_decrypt_available() -> bool:
    """Check if WhatsApp decryption is available."""
    return WA_CRYPT_AVAILABLE
