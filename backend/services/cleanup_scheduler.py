"""
Cleanup Scheduler for Phone Recovery
Handles automatic deletion of recovery data after 15-day retention period.
Uses APScheduler for scheduled tasks.
"""

import asyncio
import shutil
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Base paths for recovery data
RECOVERY_PATHS = {
    "uploads": Path("/tmp/recovery_uploads"),
    "output": Path("/tmp/recovery_output"),
    "phone_recovery": Path("/tmp/phone_recovery"),
}

# Retention period in days
RETENTION_DAYS = 15


class RecoveryCleanupScheduler:
    """
    Scheduler for automatic cleanup of expired recovery data.

    - Runs daily at 2 AM
    - Deletes data older than 15 days
    - Logs all deletions for audit trail
    """

    def __init__(self, db=None):
        self.db = db
        self._scheduler = None
        self._running = False

    async def start(self):
        """Start the cleanup scheduler."""
        if self._running:
            return

        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            from apscheduler.triggers.cron import CronTrigger

            self._scheduler = AsyncIOScheduler()

            # Schedule daily cleanup at 2 AM
            self._scheduler.add_job(
                self.cleanup_expired_recoveries,
                CronTrigger(hour=2, minute=0),
                id="recovery_cleanup",
                name="Recovery Data Cleanup",
                replace_existing=True
            )

            # Also run every 6 hours for more frequent cleanup
            self._scheduler.add_job(
                self.cleanup_expired_recoveries,
                CronTrigger(hour="*/6"),
                id="recovery_cleanup_frequent",
                name="Recovery Data Cleanup (Frequent)",
                replace_existing=True
            )

            self._scheduler.start()
            self._running = True
            logger.info("Recovery cleanup scheduler started")

        except ImportError:
            logger.warning("APScheduler not available. Using fallback timer-based cleanup.")
            asyncio.create_task(self._fallback_scheduler())
            self._running = True

    async def _fallback_scheduler(self):
        """Fallback scheduler using asyncio sleep."""
        while self._running:
            try:
                await self.cleanup_expired_recoveries()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

            # Sleep for 6 hours
            await asyncio.sleep(6 * 60 * 60)

    async def stop(self):
        """Stop the cleanup scheduler."""
        self._running = False
        if self._scheduler:
            self._scheduler.shutdown()
            self._scheduler = None
        logger.info("Recovery cleanup scheduler stopped")

    async def cleanup_expired_recoveries(self):
        """
        Main cleanup task - delete all recovery data older than retention period.
        """
        logger.info("Starting recovery data cleanup...")
        cleanup_count = 0
        total_size_freed = 0

        cutoff_time = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)

        # Cleanup from database if available
        if self.db:
            cleanup_count += await self._cleanup_database_records(cutoff_time)

        # Cleanup from filesystem
        for name, base_path in RECOVERY_PATHS.items():
            if not base_path.exists():
                continue

            count, size = await self._cleanup_directory(base_path, cutoff_time)
            cleanup_count += count
            total_size_freed += size

        logger.info(
            f"Cleanup complete. Deleted {cleanup_count} items, "
            f"freed {total_size_freed / (1024*1024):.2f} MB"
        )

        return cleanup_count, total_size_freed

    async def _cleanup_database_records(self, cutoff_time: datetime) -> int:
        """Cleanup expired records from MongoDB."""
        try:
            # Find expired recovery cases
            expired_cases = await self.db.phone_recovery_cases.find({
                "$or": [
                    {"deletion_schedule.auto_delete_at": {"$lt": cutoff_time}},
                    {"expires_at": {"$lt": cutoff_time}}
                ],
                "deletion_schedule.deleted_at": None
            }).to_list(None)

            deleted_count = 0

            for case in expired_cases:
                case_id = case.get("case_id")
                logger.info(f"Deleting expired recovery case: {case_id}")

                # Delete associated files
                await self._delete_case_files(case_id)

                # Update record with deletion timestamp
                await self.db.phone_recovery_cases.update_one(
                    {"_id": case["_id"]},
                    {
                        "$set": {
                            "deletion_schedule.deleted_at": datetime.now(timezone.utc),
                            "status": "deleted"
                        },
                        "$push": {
                            "chain_of_custody": {
                                "timestamp": datetime.now(timezone.utc),
                                "actor": "System: Cleanup Scheduler",
                                "action": "AUTO_DELETION",
                                "details": f"15-day retention period expired. All files securely deleted."
                            }
                        }
                    }
                )

                deleted_count += 1

            return deleted_count

        except Exception as e:
            logger.error(f"Database cleanup error: {e}")
            return 0

    async def _delete_case_files(self, case_id: str):
        """Delete all files associated with a recovery case."""
        for base_path in RECOVERY_PATHS.values():
            # Delete case directory
            case_dir = base_path / case_id
            if case_dir.exists():
                await self._secure_delete_directory(case_dir)

            # Delete case ZIP file
            zip_file = base_path / f"{case_id}.zip"
            if zip_file.exists():
                await self._secure_delete_file(zip_file)

            # Delete any files matching case_id pattern
            for file_path in base_path.glob(f"{case_id}*"):
                if file_path.is_file():
                    await self._secure_delete_file(file_path)
                elif file_path.is_dir():
                    await self._secure_delete_directory(file_path)

    async def _cleanup_directory(self, base_path: Path, cutoff_time: datetime) -> tuple:
        """
        Cleanup files and directories older than cutoff time.

        Returns:
            Tuple of (items_deleted, bytes_freed)
        """
        items_deleted = 0
        bytes_freed = 0

        try:
            for item in base_path.iterdir():
                # Check modification time
                try:
                    mtime = datetime.fromtimestamp(item.stat().st_mtime, tz=timezone.utc)
                except OSError:
                    continue

                if mtime < cutoff_time:
                    if item.is_file():
                        size = item.stat().st_size
                        await self._secure_delete_file(item)
                        items_deleted += 1
                        bytes_freed += size
                    elif item.is_dir():
                        size = await self._get_directory_size(item)
                        await self._secure_delete_directory(item)
                        items_deleted += 1
                        bytes_freed += size

        except Exception as e:
            logger.error(f"Error cleaning directory {base_path}: {e}")

        return items_deleted, bytes_freed

    async def _secure_delete_file(self, file_path: Path):
        """
        Securely delete a file by overwriting before unlinking.
        """
        try:
            # Overwrite with zeros for security
            size = file_path.stat().st_size
            if size > 0 and size < 100 * 1024 * 1024:  # Only overwrite files < 100MB
                with open(file_path, "wb") as f:
                    f.write(b'\x00' * size)
                    f.flush()

            file_path.unlink()
            logger.debug(f"Securely deleted file: {file_path}")

        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            # Try regular delete as fallback
            try:
                file_path.unlink()
            except Exception:
                pass

    async def _secure_delete_directory(self, dir_path: Path):
        """Securely delete a directory and all contents."""
        try:
            # First, securely delete all files
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    await self._secure_delete_file(file_path)

            # Then remove the directory tree
            shutil.rmtree(dir_path, ignore_errors=True)
            logger.debug(f"Securely deleted directory: {dir_path}")

        except Exception as e:
            logger.error(f"Error deleting directory {dir_path}: {e}")

    async def _get_directory_size(self, dir_path: Path) -> int:
        """Calculate total size of directory contents."""
        total = 0
        try:
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    total += file_path.stat().st_size
        except Exception:
            pass
        return total

    async def force_cleanup_case(self, case_id: str):
        """
        Force immediate cleanup of a specific case.
        Used when admin manually deletes a case.
        """
        logger.info(f"Force cleanup requested for case: {case_id}")
        await self._delete_case_files(case_id)

        if self.db:
            await self.db.phone_recovery_cases.update_one(
                {"case_id": case_id},
                {
                    "$set": {
                        "deletion_schedule.deleted_at": datetime.now(timezone.utc),
                        "status": "deleted"
                    },
                    "$push": {
                        "chain_of_custody": {
                            "timestamp": datetime.now(timezone.utc),
                            "actor": "Admin: Manual Deletion",
                            "action": "MANUAL_DELETION",
                            "details": "Case manually deleted by administrator"
                        }
                    }
                }
            )


# Singleton instance
_cleanup_scheduler: Optional[RecoveryCleanupScheduler] = None


def get_cleanup_scheduler(db=None) -> RecoveryCleanupScheduler:
    """Get or create the cleanup scheduler instance."""
    global _cleanup_scheduler
    if _cleanup_scheduler is None:
        _cleanup_scheduler = RecoveryCleanupScheduler(db)
    return _cleanup_scheduler


async def start_cleanup_scheduler(db=None):
    """Start the cleanup scheduler."""
    scheduler = get_cleanup_scheduler(db)
    await scheduler.start()
    return scheduler


async def stop_cleanup_scheduler():
    """Stop the cleanup scheduler."""
    global _cleanup_scheduler
    if _cleanup_scheduler:
        await _cleanup_scheduler.stop()
        _cleanup_scheduler = None
