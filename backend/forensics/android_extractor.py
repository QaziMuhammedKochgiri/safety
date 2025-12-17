"""
Android Extractor for Phone Recovery
Handles Android device full extraction via ADB including backup creation,
data extraction, and app data retrieval.
"""

import asyncio
import subprocess
import os
import shutil
import tarfile
import zlib
import struct
import logging
from typing import Optional, List, Dict, Any
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
class AppDataResult:
    """Result of app-specific data extraction"""
    success: bool
    app_name: str
    data_path: Optional[Path] = None
    databases: List[str] = field(default_factory=list)
    error: Optional[str] = None


class AndroidExtractor:
    """
    Handles Android device data extraction via ADB.
    Supports full backup, partial backup, and app-specific extraction.
    """

    # Known app package names for messaging apps
    MESSAGING_APPS = {
        "whatsapp": "com.whatsapp",
        "telegram": "org.telegram.messenger",
        "signal": "org.thoughtcrime.securesms",
        "messenger": "com.facebook.orca",
        "sms": "com.android.providers.telephony",
    }

    def __init__(self, device_id: str, output_base: Path = Path("/tmp/phone_recovery")):
        self.device_id = device_id
        self.output_base = output_base
        self._adb_path = self._find_adb()

    def _find_adb(self) -> str:
        """Find ADB binary path"""
        try:
            result = subprocess.run(["which", "adb"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "adb"

    async def create_backup(
        self,
        output_path: Optional[Path] = None,
        include_apk: bool = False,
        include_shared: bool = True,
        packages: Optional[List[str]] = None
    ) -> BackupResult:
        """
        Create ADB backup (.ab format) of the device.

        Args:
            output_path: Where to save the backup file
            include_apk: Include APK files in backup
            include_shared: Include shared storage (sdcard)
            packages: Specific packages to backup (None = all)

        Returns:
            BackupResult with backup details
        """
        start_time = datetime.now()

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_base / f"backup_{self.device_id}_{timestamp}.ab"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Build ADB backup command
            cmd = [
                self._adb_path, "-s", self.device_id, "backup",
                "-f", str(output_path),
            ]

            if include_apk:
                cmd.append("-apk")
            else:
                cmd.append("-noapk")

            if include_shared:
                cmd.append("-shared")
            else:
                cmd.append("-noshared")

            cmd.append("-all")  # Backup all apps

            if packages:
                cmd.extend(packages)

            logger.info(f"Starting ADB backup for device {self.device_id}")
            logger.info(f"Command: {' '.join(cmd)}")

            # Note: ADB backup requires user confirmation on device
            # This will wait for the user to confirm
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait for backup to complete (can take a long time)
            stdout, stderr = await process.communicate()

            duration = (datetime.now() - start_time).total_seconds()

            if process.returncode != 0 or not output_path.exists():
                error_msg = stderr.decode("utf-8", errors="replace")
                logger.error(f"ADB backup failed: {error_msg}")
                return BackupResult(
                    success=False,
                    error=error_msg or "Backup failed - user may have declined",
                    duration_seconds=duration
                )

            backup_size = output_path.stat().st_size

            # Verify it's a valid backup (check header)
            with open(output_path, "rb") as f:
                header = f.read(24)
                if not header.startswith(b"ANDROID BACKUP"):
                    logger.error("Invalid backup file format")
                    return BackupResult(
                        success=False,
                        error="Invalid backup file format",
                        duration_seconds=duration
                    )

            logger.info(f"Backup completed: {backup_size / (1024*1024):.2f} MB in {duration:.1f}s")

            return BackupResult(
                success=True,
                backup_path=output_path,
                backup_size=backup_size,
                duration_seconds=duration
            )

        except Exception as e:
            logger.error(f"Error creating backup: {e}")
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
        Extract TAR-compressed ADB backup (.ab file).

        Android Backup Format:
        1. Header (24 bytes): "ANDROID BACKUP\n1\n1\nnone\n" or with encryption
        2. Compressed TAR data (zlib)

        Args:
            backup_path: Path to .ab backup file
            output_dir: Where to extract files

        Returns:
            ExtractionResult with extraction details
        """
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = self.output_base / f"extracted_{timestamp}"

        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            logger.info(f"Extracting backup: {backup_path}")

            with open(backup_path, "rb") as f:
                # Read and parse header
                header_line = f.readline()  # "ANDROID BACKUP\n"
                if not header_line.startswith(b"ANDROID BACKUP"):
                    return ExtractionResult(
                        success=False,
                        error="Not a valid Android backup file"
                    )

                version = f.readline().strip()  # Version number
                compressed = f.readline().strip()  # 1 = compressed
                encryption = f.readline().strip()  # none, AES-256, etc.

                logger.info(f"Backup version: {version}, compressed: {compressed}, encryption: {encryption}")

                if encryption != b"none":
                    return ExtractionResult(
                        success=False,
                        error=f"Encrypted backups not supported: {encryption.decode()}"
                    )

                # Read compressed data
                compressed_data = f.read()

            # Decompress with zlib
            try:
                decompressed_data = zlib.decompress(compressed_data)
            except zlib.error as e:
                logger.error(f"Decompression failed: {e}")
                return ExtractionResult(
                    success=False,
                    error=f"Failed to decompress backup: {e}"
                )

            # Write to temporary TAR file
            tar_path = output_dir / "backup.tar"
            with open(tar_path, "wb") as f:
                f.write(decompressed_data)

            # Extract TAR archive
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

            with tarfile.open(tar_path, "r") as tar:
                for member in tar.getmembers():
                    if member.isfile():
                        file_count += 1
                        total_size += member.size

                        # Categorize file
                        category = self._categorize_file(member.name)
                        categories[category] = categories.get(category, 0) + 1

                # Extract all files
                tar.extractall(path=output_dir)

            # Clean up temp tar
            tar_path.unlink()

            logger.info(f"Extracted {file_count} files ({total_size / (1024*1024):.2f} MB)")

            return ExtractionResult(
                success=True,
                extracted_dir=output_dir,
                file_count=file_count,
                total_size=total_size,
                categories=categories
            )

        except Exception as e:
            logger.error(f"Error extracting backup: {e}")
            return ExtractionResult(
                success=False,
                error=str(e)
            )

    async def extract_app_data(
        self,
        apps: Optional[List[str]] = None,
        output_dir: Optional[Path] = None
    ) -> List[AppDataResult]:
        """
        Extract specific app databases directly from device.
        Requires root access or debug build for most apps.

        Args:
            apps: List of app names (whatsapp, telegram, etc.) or package names
            output_dir: Where to save extracted data

        Returns:
            List of AppDataResult for each app
        """
        if apps is None:
            apps = list(self.MESSAGING_APPS.keys())

        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = self.output_base / f"app_data_{timestamp}"

        output_dir.mkdir(parents=True, exist_ok=True)
        results = []

        for app in apps:
            # Get package name
            package = self.MESSAGING_APPS.get(app.lower(), app)

            app_result = await self._extract_single_app(package, output_dir)
            results.append(app_result)

        return results

    async def _extract_single_app(self, package: str, output_dir: Path) -> AppDataResult:
        """Extract data for a single app"""
        app_dir = output_dir / package
        app_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Try to pull app data (requires root or run-as)
            data_paths = [
                f"/data/data/{package}/databases/",
                f"/data/data/{package}/shared_prefs/",
                f"/data/data/{package}/files/",
            ]

            databases = []

            for data_path in data_paths:
                # Try using run-as (works for debuggable apps)
                result = await self._run_adb_command([
                    "shell", "run-as", package, "ls", data_path
                ])

                if result.returncode == 0:
                    files = result.stdout.strip().split("\n")
                    for file in files:
                        if file.endswith(".db") or file.endswith(".db-wal") or file.endswith(".db-shm"):
                            # Pull the file
                            pull_result = await self._pull_app_file(
                                package, f"{data_path}{file}", app_dir / file
                            )
                            if pull_result:
                                databases.append(file)

            if not databases:
                # Try backup method as fallback
                backup_result = await self.create_backup(
                    output_path=app_dir / "backup.ab",
                    packages=[package]
                )
                if backup_result.success:
                    extract_result = await self.extract_backup(
                        backup_result.backup_path,
                        app_dir / "extracted"
                    )
                    if extract_result.success:
                        # Find databases in extracted data
                        for db_file in app_dir.rglob("*.db"):
                            databases.append(str(db_file.relative_to(app_dir)))

            return AppDataResult(
                success=len(databases) > 0,
                app_name=package,
                data_path=app_dir if databases else None,
                databases=databases
            )

        except Exception as e:
            logger.error(f"Error extracting app data for {package}: {e}")
            return AppDataResult(
                success=False,
                app_name=package,
                error=str(e)
            )

    async def _pull_app_file(self, package: str, remote_path: str, local_path: Path) -> bool:
        """Pull a file from an app's data directory"""
        try:
            # Use run-as to access app data
            temp_path = f"/sdcard/temp_{local_path.name}"

            # Copy to accessible location
            result = await self._run_adb_command([
                "shell", "run-as", package, "cp", remote_path, temp_path
            ])

            if result.returncode != 0:
                return False

            # Pull from accessible location
            result = await self._run_adb_command([
                "pull", temp_path, str(local_path)
            ])

            # Clean up temp file
            await self._run_adb_command(["shell", "rm", temp_path])

            return result.returncode == 0

        except Exception as e:
            logger.error(f"Error pulling file {remote_path}: {e}")
            return False

    async def pull_media(self, output_dir: Path, media_types: Optional[List[str]] = None) -> Dict[str, int]:
        """
        Pull media files from device storage.

        Args:
            output_dir: Where to save media files
            media_types: Types to pull (photos, videos, audio, documents)

        Returns:
            Dict with counts of each media type pulled
        """
        if media_types is None:
            media_types = ["photos", "videos", "audio", "documents"]

        output_dir.mkdir(parents=True, exist_ok=True)
        counts = {}

        media_paths = {
            "photos": ["/sdcard/DCIM/", "/sdcard/Pictures/"],
            "videos": ["/sdcard/DCIM/", "/sdcard/Movies/"],
            "audio": ["/sdcard/Music/", "/sdcard/Recordings/"],
            "documents": ["/sdcard/Documents/", "/sdcard/Download/"],
        }

        for media_type in media_types:
            if media_type not in media_paths:
                continue

            type_dir = output_dir / media_type
            type_dir.mkdir(exist_ok=True)
            count = 0

            for path in media_paths[media_type]:
                result = await self._run_adb_command([
                    "pull", path, str(type_dir)
                ])
                if result.returncode == 0:
                    # Count pulled files
                    for f in type_dir.rglob("*"):
                        if f.is_file():
                            count += 1

            counts[media_type] = count

        return counts

    async def get_contacts(self, output_path: Path) -> bool:
        """Export contacts to VCF file"""
        try:
            # Query contacts content provider
            result = await self._run_adb_command([
                "shell", "content", "query",
                "--uri", "content://contacts/people"
            ])

            if result.returncode == 0:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(result.stdout)
                return True

            return False

        except Exception as e:
            logger.error(f"Error exporting contacts: {e}")
            return False

    async def get_call_log(self, output_path: Path) -> bool:
        """Export call log"""
        try:
            result = await self._run_adb_command([
                "shell", "content", "query",
                "--uri", "content://call_log/calls"
            ])

            if result.returncode == 0:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(result.stdout)
                return True

            return False

        except Exception as e:
            logger.error(f"Error exporting call log: {e}")
            return False

    async def get_sms(self, output_path: Path) -> bool:
        """Export SMS messages"""
        try:
            result = await self._run_adb_command([
                "shell", "content", "query",
                "--uri", "content://sms"
            ])

            if result.returncode == 0:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(result.stdout)
                return True

            return False

        except Exception as e:
            logger.error(f"Error exporting SMS: {e}")
            return False

    def _categorize_file(self, filepath: str) -> str:
        """Categorize a file based on its path and extension"""
        filepath_lower = filepath.lower()

        # Photos
        if any(ext in filepath_lower for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"]):
            return "photos"

        # Videos
        if any(ext in filepath_lower for ext in [".mp4", ".mov", ".avi", ".mkv", ".webm", ".3gp"]):
            return "videos"

        # Messages (database files in messaging apps)
        if any(app in filepath_lower for app in ["whatsapp", "telegram", "signal", "messenger"]):
            return "messages"

        # Contacts
        if "contacts" in filepath_lower or filepath_lower.endswith(".vcf"):
            return "contacts"

        # App data (databases)
        if filepath_lower.endswith(".db") or "databases" in filepath_lower:
            return "app_data"

        return "other"

    async def _run_adb_command(self, args: List[str], timeout: int = 300) -> subprocess.CompletedProcess:
        """Run an ADB command for this device"""
        cmd = [self._adb_path, "-s", self.device_id] + args

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            return subprocess.CompletedProcess(
                cmd,
                process.returncode,
                stdout.decode("utf-8", errors="replace"),
                stderr.decode("utf-8", errors="replace")
            )
        except asyncio.TimeoutError:
            logger.error(f"ADB command timed out: {' '.join(args)}")
            return subprocess.CompletedProcess(cmd, -1, "", "Timeout")
        except Exception as e:
            logger.error(f"Error running ADB command: {e}")
            return subprocess.CompletedProcess(cmd, -1, "", str(e))
