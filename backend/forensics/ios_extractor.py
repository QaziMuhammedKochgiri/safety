"""
iOS Extractor for Phone Recovery
Handles iOS device extraction via libimobiledevice including backup creation,
backup parsing, and data extraction from iTunes/Finder backups.
"""

import asyncio
import subprocess
import os
import shutil
import sqlite3
import plistlib
import hashlib
import logging
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class BackupResult:
    """Result of a backup operation"""
    success: bool
    backup_path: Optional[Path] = None
    backup_size: int = 0
    duration_seconds: float = 0
    is_encrypted: bool = False
    error: Optional[str] = None


@dataclass
class ExtractionResult:
    """Result of backup extraction"""
    success: bool
    extracted_dir: Optional[Path] = None
    file_count: int = 0
    total_size: int = 0
    categories: Dict[str, int] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class MessageResult:
    """Result of message extraction"""
    success: bool
    message_count: int = 0
    conversations: int = 0
    output_path: Optional[Path] = None
    error: Optional[str] = None


class iOSExtractor:
    """
    Handles iOS device data extraction via libimobiledevice.
    Also supports parsing existing iTunes/Finder backups.
    """

    # Known iOS app domain mappings
    APP_DOMAINS = {
        "sms": "HomeDomain",
        "contacts": "HomeDomain",
        "call_history": "HomeDomain",
        "photos": "CameraRollDomain",
        "whatsapp": "AppDomain-net.whatsapp.WhatsApp",
        "telegram": "AppDomain-ph.telegra.Telegraph",
        "signal": "AppDomain-org.whispersystems.signal",
    }

    # File mappings in iOS backup
    FILE_MAPPINGS = {
        "sms": "Library/SMS/sms.db",
        "contacts": "Library/AddressBook/AddressBook.sqlitedb",
        "call_history": "Library/CallHistoryDB/CallHistory.storedata",
        "notes": "Library/Notes/notes.sqlite",
        "calendar": "Library/Calendar/Calendar.sqlitedb",
        "voicemail": "Library/Voicemail/voicemail.db",
    }

    def __init__(self, device_id: str = None, output_base: Path = Path("/tmp/phone_recovery")):
        self.device_id = device_id
        self.output_base = output_base
        self._tools = self._find_tools()

    def _find_tools(self) -> Dict[str, str]:
        """Find libimobiledevice tool paths"""
        tools = {}
        tool_names = [
            "idevice_id", "ideviceinfo", "idevicebackup2",
            "idevicepair", "idevicename", "idevicedate"
        ]
        for tool in tool_names:
            try:
                result = subprocess.run(["which", tool], capture_output=True, text=True)
                if result.returncode == 0:
                    tools[tool] = result.stdout.strip()
            except Exception:
                tools[tool] = tool
        return tools

    async def create_backup(
        self,
        output_path: Optional[Path] = None,
        full_backup: bool = True
    ) -> BackupResult:
        """
        Create iOS backup using libimobiledevice.

        Args:
            output_path: Where to save the backup
            full_backup: Whether to create full backup (vs incremental)

        Returns:
            BackupResult with backup details
        """
        if not self.device_id:
            return BackupResult(success=False, error="No device ID specified")

        start_time = datetime.now()

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_base / f"ios_backup_{self.device_id}_{timestamp}"

        output_path.mkdir(parents=True, exist_ok=True)

        try:
            idevicebackup2 = self._tools.get("idevicebackup2", "idevicebackup2")

            # Build command
            cmd = [idevicebackup2]
            if self.device_id:
                cmd.extend(["-u", self.device_id])

            if full_backup:
                cmd.append("backup")
            else:
                cmd.append("backup")  # idevicebackup2 handles incremental automatically

            cmd.append(str(output_path))

            logger.info(f"Starting iOS backup for device {self.device_id}")
            logger.info(f"Command: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            duration = (datetime.now() - start_time).total_seconds()

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace")
                logger.error(f"iOS backup failed: {error_msg}")
                return BackupResult(
                    success=False,
                    error=error_msg,
                    duration_seconds=duration
                )

            # Calculate backup size
            backup_size = sum(
                f.stat().st_size for f in output_path.rglob("*") if f.is_file()
            )

            # Check if encrypted
            is_encrypted = await self._check_backup_encrypted(output_path)

            logger.info(f"iOS backup completed: {backup_size / (1024*1024):.2f} MB in {duration:.1f}s")

            return BackupResult(
                success=True,
                backup_path=output_path,
                backup_size=backup_size,
                duration_seconds=duration,
                is_encrypted=is_encrypted
            )

        except Exception as e:
            logger.error(f"Error creating iOS backup: {e}")
            return BackupResult(
                success=False,
                error=str(e),
                duration_seconds=(datetime.now() - start_time).total_seconds()
            )

    async def extract_backup(
        self,
        backup_path: Path,
        output_dir: Optional[Path] = None
    ) -> ExtractionResult:
        """
        Extract and organize iOS backup files.

        iOS Backup Format:
        - Manifest.db: SQLite database mapping file IDs to paths
        - Manifest.plist: Backup metadata
        - Info.plist: Device info
        - Status.plist: Backup status
        - Files are stored with SHA1 hash names in folders

        Args:
            backup_path: Path to iOS backup directory
            output_dir: Where to extract organized files

        Returns:
            ExtractionResult with extraction details
        """
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = self.output_base / f"ios_extracted_{timestamp}"

        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            manifest_db = backup_path / "Manifest.db"

            if not manifest_db.exists():
                # Try to find in subdirectory (backup folder structure varies)
                for subdir in backup_path.iterdir():
                    if subdir.is_dir():
                        potential_manifest = subdir / "Manifest.db"
                        if potential_manifest.exists():
                            backup_path = subdir
                            manifest_db = potential_manifest
                            break

            if not manifest_db.exists():
                return ExtractionResult(
                    success=False,
                    error="Manifest.db not found - invalid iOS backup"
                )

            # Check for encryption
            manifest_plist = backup_path / "Manifest.plist"
            if manifest_plist.exists():
                with open(manifest_plist, "rb") as f:
                    plist = plistlib.load(f)
                    if plist.get("IsEncrypted", False):
                        return ExtractionResult(
                            success=False,
                            error="Encrypted backup - password required"
                        )

            logger.info(f"Extracting iOS backup from {backup_path}")

            # Parse Manifest.db
            file_count = 0
            total_size = 0
            categories = {
                "photos": 0,
                "videos": 0,
                "messages": 0,
                "contacts": 0,
                "app_data": 0,
                "other": 0
            }

            conn = sqlite3.connect(str(manifest_db))
            cursor = conn.cursor()

            # Query all files from manifest
            cursor.execute("""
                SELECT fileID, domain, relativePath, flags
                FROM Files
                WHERE flags != 2
            """)

            for row in cursor.fetchall():
                file_id, domain, relative_path, flags = row

                if not file_id or not relative_path:
                    continue

                # Find the actual file in backup
                source_file = self._find_backup_file(backup_path, file_id)

                if not source_file or not source_file.exists():
                    continue

                # Create destination path
                dest_dir = output_dir / domain
                dest_path = dest_dir / relative_path

                try:
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_file, dest_path)

                    file_count += 1
                    total_size += dest_path.stat().st_size

                    # Categorize
                    category = self._categorize_file(relative_path, domain)
                    categories[category] = categories.get(category, 0) + 1

                except Exception as e:
                    logger.warning(f"Failed to copy {file_id}: {e}")

            conn.close()

            logger.info(f"Extracted {file_count} files ({total_size / (1024*1024):.2f} MB)")

            return ExtractionResult(
                success=True,
                extracted_dir=output_dir,
                file_count=file_count,
                total_size=total_size,
                categories=categories
            )

        except Exception as e:
            logger.error(f"Error extracting iOS backup: {e}")
            return ExtractionResult(
                success=False,
                error=str(e)
            )

    async def extract_messages(
        self,
        backup_path: Path,
        output_path: Optional[Path] = None
    ) -> MessageResult:
        """
        Extract SMS/iMessage from iOS backup.

        Args:
            backup_path: Path to iOS backup or extracted backup
            output_path: Where to save extracted messages

        Returns:
            MessageResult with extraction details
        """
        if output_path is None:
            output_path = self.output_base / "ios_messages.json"

        try:
            # Find sms.db
            sms_db = await self._find_file_in_backup(
                backup_path, "Library/SMS/sms.db", "HomeDomain"
            )

            if not sms_db or not sms_db.exists():
                return MessageResult(
                    success=False,
                    error="SMS database not found in backup"
                )

            logger.info(f"Extracting messages from {sms_db}")

            conn = sqlite3.connect(str(sms_db))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Extract messages
            cursor.execute("""
                SELECT
                    m.ROWID,
                    m.text,
                    m.date,
                    m.is_from_me,
                    m.handle_id,
                    h.id as contact_id
                FROM message m
                LEFT JOIN handle h ON m.handle_id = h.ROWID
                ORDER BY m.date
            """)

            messages = []
            conversations = set()

            for row in cursor.fetchall():
                msg = {
                    "id": row["ROWID"],
                    "text": row["text"],
                    "date": self._convert_ios_date(row["date"]),
                    "is_from_me": bool(row["is_from_me"]),
                    "contact": row["contact_id"]
                }
                messages.append(msg)
                if row["contact_id"]:
                    conversations.add(row["contact_id"])

            conn.close()

            # Save to file
            import json
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)

            logger.info(f"Extracted {len(messages)} messages from {len(conversations)} conversations")

            return MessageResult(
                success=True,
                message_count=len(messages),
                conversations=len(conversations),
                output_path=output_path
            )

        except Exception as e:
            logger.error(f"Error extracting messages: {e}")
            return MessageResult(
                success=False,
                error=str(e)
            )

    async def extract_whatsapp(
        self,
        backup_path: Path,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Extract WhatsApp data from iOS backup.

        Args:
            backup_path: Path to iOS backup
            output_dir: Where to save extracted data

        Returns:
            Dict with extraction results
        """
        if output_dir is None:
            output_dir = self.output_base / "ios_whatsapp"

        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Find WhatsApp database
            wa_db = await self._find_file_in_backup(
                backup_path,
                "ChatStorage.sqlite",
                "AppDomain-net.whatsapp.WhatsApp"
            )

            if not wa_db or not wa_db.exists():
                return {"success": False, "error": "WhatsApp database not found"}

            # Copy database
            dest_db = output_dir / "ChatStorage.sqlite"
            shutil.copy2(wa_db, dest_db)

            # Parse messages
            conn = sqlite3.connect(str(dest_db))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Count messages and chats
            cursor.execute("SELECT COUNT(*) FROM ZWAMESSAGE")
            message_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM ZWACHATSESSION")
            chat_count = cursor.fetchone()[0]

            conn.close()

            # Find media files
            media_count = 0
            media_dir = output_dir / "Media"
            media_dir.mkdir(exist_ok=True)

            # Look for WhatsApp media in backup
            for domain in ["AppDomain-net.whatsapp.WhatsApp", "AppDomainGroup-group.net.whatsapp.WhatsApp.shared"]:
                media_files = await self._find_files_by_domain(backup_path, domain)
                for src, relative_path in media_files:
                    if any(ext in relative_path.lower() for ext in [".jpg", ".mp4", ".opus", ".pdf"]):
                        dest = media_dir / Path(relative_path).name
                        try:
                            shutil.copy2(src, dest)
                            media_count += 1
                        except Exception:
                            pass

            return {
                "success": True,
                "messages": message_count,
                "chats": chat_count,
                "media_files": media_count,
                "output_dir": str(output_dir)
            }

        except Exception as e:
            logger.error(f"Error extracting WhatsApp: {e}")
            return {"success": False, "error": str(e)}

    async def get_contacts(self, backup_path: Path, output_path: Path) -> bool:
        """Extract contacts from iOS backup"""
        try:
            contacts_db = await self._find_file_in_backup(
                backup_path,
                "Library/AddressBook/AddressBook.sqlitedb",
                "HomeDomain"
            )

            if not contacts_db or not contacts_db.exists():
                return False

            conn = sqlite3.connect(str(contacts_db))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    p.ROWID,
                    p.First,
                    p.Last,
                    p.Organization,
                    mv.value as phone
                FROM ABPerson p
                LEFT JOIN ABMultiValue mv ON p.ROWID = mv.record_id
                WHERE mv.property = 3
            """)

            contacts = []
            for row in cursor.fetchall():
                contacts.append({
                    "id": row["ROWID"],
                    "first_name": row["First"],
                    "last_name": row["Last"],
                    "organization": row["Organization"],
                    "phone": row["phone"]
                })

            conn.close()

            import json
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(contacts, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            logger.error(f"Error extracting contacts: {e}")
            return False

    async def get_call_history(self, backup_path: Path, output_path: Path) -> bool:
        """Extract call history from iOS backup"""
        try:
            call_db = await self._find_file_in_backup(
                backup_path,
                "Library/CallHistoryDB/CallHistory.storedata",
                "HomeDomain"
            )

            if not call_db or not call_db.exists():
                return False

            conn = sqlite3.connect(str(call_db))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    ZADDRESS as phone,
                    ZDATE as date,
                    ZDURATION as duration,
                    ZCALLTYPE as call_type
                FROM ZCALLRECORD
                ORDER BY ZDATE DESC
            """)

            calls = []
            for row in cursor.fetchall():
                calls.append({
                    "phone": row["phone"],
                    "date": self._convert_ios_date(row["date"]),
                    "duration": row["duration"],
                    "type": "incoming" if row["call_type"] == 1 else "outgoing"
                })

            conn.close()

            import json
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(calls, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            logger.error(f"Error extracting call history: {e}")
            return False

    def _find_backup_file(self, backup_path: Path, file_id: str) -> Optional[Path]:
        """Find a file in iOS backup by its file ID (SHA1 hash)"""
        # iOS backups store files in subdirectories based on first 2 chars of hash
        subdir = file_id[:2]
        file_path = backup_path / subdir / file_id

        if file_path.exists():
            return file_path

        # Also check direct path (older backup formats)
        direct_path = backup_path / file_id
        if direct_path.exists():
            return direct_path

        return None

    async def _find_file_in_backup(
        self,
        backup_path: Path,
        relative_path: str,
        domain: str
    ) -> Optional[Path]:
        """Find a specific file in iOS backup using Manifest.db"""
        manifest_db = backup_path / "Manifest.db"

        # Check subdirectories
        if not manifest_db.exists():
            for subdir in backup_path.iterdir():
                if subdir.is_dir():
                    potential = subdir / "Manifest.db"
                    if potential.exists():
                        backup_path = subdir
                        manifest_db = potential
                        break

        if not manifest_db.exists():
            # Maybe it's an extracted backup
            direct_path = backup_path / domain / relative_path
            if direct_path.exists():
                return direct_path
            return None

        try:
            conn = sqlite3.connect(str(manifest_db))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT fileID FROM Files
                WHERE domain = ? AND relativePath = ?
            """, (domain, relative_path))

            row = cursor.fetchone()
            conn.close()

            if row:
                return self._find_backup_file(backup_path, row[0])

            # Try partial match
            conn = sqlite3.connect(str(manifest_db))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT fileID FROM Files
                WHERE domain LIKE ? AND relativePath LIKE ?
            """, (f"%{domain.split('-')[-1]}%", f"%{relative_path.split('/')[-1]}%"))

            row = cursor.fetchone()
            conn.close()

            if row:
                return self._find_backup_file(backup_path, row[0])

        except Exception as e:
            logger.error(f"Error finding file in backup: {e}")

        return None

    async def _find_files_by_domain(
        self,
        backup_path: Path,
        domain: str
    ) -> List[Tuple[Path, str]]:
        """Find all files for a specific domain in iOS backup"""
        files = []
        manifest_db = backup_path / "Manifest.db"

        if not manifest_db.exists():
            for subdir in backup_path.iterdir():
                if subdir.is_dir():
                    potential = subdir / "Manifest.db"
                    if potential.exists():
                        backup_path = subdir
                        manifest_db = potential
                        break

        if not manifest_db.exists():
            return files

        try:
            conn = sqlite3.connect(str(manifest_db))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT fileID, relativePath FROM Files
                WHERE domain = ? OR domain LIKE ?
            """, (domain, f"%{domain}%"))

            for row in cursor.fetchall():
                file_id, relative_path = row
                source = self._find_backup_file(backup_path, file_id)
                if source:
                    files.append((source, relative_path))

            conn.close()

        except Exception as e:
            logger.error(f"Error finding files by domain: {e}")

        return files

    async def _check_backup_encrypted(self, backup_path: Path) -> bool:
        """Check if an iOS backup is encrypted"""
        manifest_plist = backup_path / "Manifest.plist"
        if manifest_plist.exists():
            try:
                with open(manifest_plist, "rb") as f:
                    plist = plistlib.load(f)
                    return plist.get("IsEncrypted", False)
            except Exception:
                pass
        return False

    def _categorize_file(self, filepath: str, domain: str) -> str:
        """Categorize a file based on its path and domain"""
        filepath_lower = filepath.lower()
        domain_lower = domain.lower()

        # Photos
        if "cameraroll" in domain_lower or any(ext in filepath_lower for ext in [".jpg", ".jpeg", ".png", ".heic"]):
            return "photos"

        # Videos
        if any(ext in filepath_lower for ext in [".mp4", ".mov", ".m4v"]):
            return "videos"

        # Messages
        if "sms" in filepath_lower or "whatsapp" in domain_lower or "telegram" in domain_lower:
            return "messages"

        # Contacts
        if "addressbook" in filepath_lower:
            return "contacts"

        # App data
        if "appdomain" in domain_lower or filepath_lower.endswith(".db") or filepath_lower.endswith(".sqlite"):
            return "app_data"

        return "other"

    def _convert_ios_date(self, ios_timestamp: Optional[float]) -> Optional[str]:
        """Convert iOS timestamp (seconds since 2001-01-01) to ISO format"""
        if not ios_timestamp:
            return None
        try:
            # iOS epoch is 2001-01-01
            unix_timestamp = ios_timestamp + 978307200
            return datetime.fromtimestamp(unix_timestamp).isoformat()
        except Exception:
            return None
