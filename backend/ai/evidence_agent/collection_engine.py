"""
Evidence Collection Engine
Handles automated background evidence collection.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from enum import Enum
from datetime import datetime, timedelta
import hashlib
import asyncio
from pathlib import Path


class CollectionStatus(str, Enum):
    """Status of a collection task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class SyncMode(str, Enum):
    """Sync modes for collection."""
    FULL = "full"  # Collect everything
    INCREMENTAL = "incremental"  # Only new/changed items
    DIFFERENTIAL = "differential"  # Changes since last full sync
    STEALTH = "stealth"  # Low-profile collection


class DataSource(str, Enum):
    """Types of data sources."""
    WHATSAPP = "whatsapp"
    SMS = "sms"
    SIGNAL = "signal"
    TELEGRAM = "telegram"
    EMAIL = "email"
    PHOTOS = "photos"
    CALL_LOG = "call_log"
    CONTACTS = "contacts"
    LOCATION = "location"
    CLOUD_BACKUP = "cloud_backup"


@dataclass
class CollectionTask:
    """A collection task definition."""
    task_id: str
    case_id: str
    data_sources: List[DataSource]
    sync_mode: SyncMode
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: CollectionStatus = CollectionStatus.PENDING
    priority: int = 5  # 1-10, higher = more important
    battery_aware: bool = True
    wifi_only: bool = True
    stealth_mode: bool = False
    max_size_mb: Optional[int] = None
    last_sync_timestamp: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class CollectedItem:
    """A single collected evidence item."""
    item_id: str
    source: DataSource
    content_hash: str
    timestamp: datetime
    size_bytes: int
    metadata: Dict[str, Any]
    is_new: bool = True
    is_modified: bool = False
    previous_hash: Optional[str] = None


@dataclass
class CollectionResult:
    """Result of a collection task."""
    task_id: str
    case_id: str
    status: CollectionStatus
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    items_collected: int
    new_items: int
    modified_items: int
    total_size_bytes: int
    sources_processed: List[DataSource]
    sources_failed: List[DataSource]
    errors: List[str]
    items: List[CollectedItem]
    sync_checkpoint: str  # For incremental sync


class EvidenceCollector:
    """Automated evidence collection engine."""

    def __init__(self, storage_path: str = "/data/evidence"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.tasks: Dict[str, CollectionTask] = {}
        self.results: Dict[str, CollectionResult] = {}
        self.sync_checkpoints: Dict[str, Dict[str, datetime]] = {}
        self._collectors: Dict[DataSource, Callable] = {}
        self._register_default_collectors()

    def _register_default_collectors(self):
        """Register default collection handlers."""
        self._collectors = {
            DataSource.WHATSAPP: self._collect_whatsapp,
            DataSource.SMS: self._collect_sms,
            DataSource.SIGNAL: self._collect_signal,
            DataSource.TELEGRAM: self._collect_telegram,
            DataSource.PHOTOS: self._collect_photos,
            DataSource.CALL_LOG: self._collect_call_log,
            DataSource.CONTACTS: self._collect_contacts,
            DataSource.LOCATION: self._collect_location,
            DataSource.CLOUD_BACKUP: self._collect_cloud_backup,
        }

    def create_task(
        self,
        case_id: str,
        data_sources: List[DataSource],
        sync_mode: SyncMode = SyncMode.INCREMENTAL,
        scheduled_at: Optional[datetime] = None,
        priority: int = 5,
        battery_aware: bool = True,
        wifi_only: bool = True,
        stealth_mode: bool = False
    ) -> CollectionTask:
        """Create a new collection task."""
        task_id = f"task_{case_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Get last sync timestamp for incremental
        last_sync = None
        if sync_mode == SyncMode.INCREMENTAL:
            checkpoints = self.sync_checkpoints.get(case_id, {})
            if checkpoints:
                last_sync = max(checkpoints.values())

        task = CollectionTask(
            task_id=task_id,
            case_id=case_id,
            data_sources=data_sources,
            sync_mode=sync_mode,
            created_at=datetime.utcnow(),
            scheduled_at=scheduled_at,
            priority=priority,
            battery_aware=battery_aware,
            wifi_only=wifi_only,
            stealth_mode=stealth_mode,
            last_sync_timestamp=last_sync
        )

        self.tasks[task_id] = task
        return task

    async def execute_task(self, task_id: str) -> CollectionResult:
        """Execute a collection task."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        task.status = CollectionStatus.RUNNING
        task.started_at = datetime.utcnow()

        items_collected: List[CollectedItem] = []
        sources_processed: List[DataSource] = []
        sources_failed: List[DataSource] = []
        errors: List[str] = []

        for source in task.data_sources:
            try:
                collector = self._collectors.get(source)
                if not collector:
                    errors.append(f"No collector for source: {source}")
                    sources_failed.append(source)
                    continue

                # Apply stealth mode delays
                if task.stealth_mode:
                    await asyncio.sleep(5)  # Random-like delay

                items = await collector(task)
                items_collected.extend(items)
                sources_processed.append(source)

                # Update checkpoint
                if task.case_id not in self.sync_checkpoints:
                    self.sync_checkpoints[task.case_id] = {}
                self.sync_checkpoints[task.case_id][source.value] = datetime.utcnow()

            except Exception as e:
                errors.append(f"{source}: {str(e)}")
                sources_failed.append(source)

        completed_at = datetime.utcnow()
        task.completed_at = completed_at
        task.status = CollectionStatus.COMPLETED if not sources_failed else CollectionStatus.FAILED

        # Calculate statistics
        new_items = sum(1 for i in items_collected if i.is_new)
        modified_items = sum(1 for i in items_collected if i.is_modified)
        total_size = sum(i.size_bytes for i in items_collected)

        result = CollectionResult(
            task_id=task_id,
            case_id=task.case_id,
            status=task.status,
            started_at=task.started_at,
            completed_at=completed_at,
            duration_seconds=(completed_at - task.started_at).total_seconds(),
            items_collected=len(items_collected),
            new_items=new_items,
            modified_items=modified_items,
            total_size_bytes=total_size,
            sources_processed=sources_processed,
            sources_failed=sources_failed,
            errors=errors,
            items=items_collected,
            sync_checkpoint=self._generate_checkpoint(task.case_id)
        )

        self.results[task_id] = result
        return result

    def _generate_checkpoint(self, case_id: str) -> str:
        """Generate a sync checkpoint identifier."""
        checkpoints = self.sync_checkpoints.get(case_id, {})
        checkpoint_str = str(sorted(checkpoints.items()))
        return hashlib.md5(checkpoint_str.encode()).hexdigest()[:16]

    async def _collect_whatsapp(self, task: CollectionTask) -> List[CollectedItem]:
        """Collect WhatsApp data."""
        items = []

        # Simulate WhatsApp backup detection and collection
        # In production, this would:
        # 1. Check for WhatsApp backup files
        # 2. Parse msgstore.db (encrypted or decrypted)
        # 3. Extract messages, media, contacts

        # Placeholder for demonstration
        sample_item = CollectedItem(
            item_id=f"wa_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            source=DataSource.WHATSAPP,
            content_hash=hashlib.sha256(b"sample").hexdigest(),
            timestamp=datetime.utcnow(),
            size_bytes=1024,
            metadata={"type": "message", "count": 0},
            is_new=True
        )
        items.append(sample_item)

        return items

    async def _collect_sms(self, task: CollectionTask) -> List[CollectedItem]:
        """Collect SMS messages."""
        items = []
        # Implementation would read from SMS database
        return items

    async def _collect_signal(self, task: CollectionTask) -> List[CollectedItem]:
        """Collect Signal messages."""
        items = []
        # Implementation would read encrypted Signal database
        return items

    async def _collect_telegram(self, task: CollectionTask) -> List[CollectedItem]:
        """Collect Telegram messages."""
        items = []
        # Implementation would use Telegram API or database
        return items

    async def _collect_photos(self, task: CollectionTask) -> List[CollectedItem]:
        """Collect photos with metadata."""
        items = []
        # Implementation would scan photo directories
        return items

    async def _collect_call_log(self, task: CollectionTask) -> List[CollectedItem]:
        """Collect call history."""
        items = []
        # Implementation would read call log database
        return items

    async def _collect_contacts(self, task: CollectionTask) -> List[CollectedItem]:
        """Collect contacts."""
        items = []
        # Implementation would read contacts database
        return items

    async def _collect_location(self, task: CollectionTask) -> List[CollectedItem]:
        """Collect location history."""
        items = []
        # Implementation would read location databases
        return items

    async def _collect_cloud_backup(self, task: CollectionTask) -> List[CollectedItem]:
        """Collect from cloud backup services."""
        items = []
        # Implementation would access cloud APIs
        return items

    def get_task_status(self, task_id: str) -> Optional[CollectionTask]:
        """Get status of a collection task."""
        return self.tasks.get(task_id)

    def get_result(self, task_id: str) -> Optional[CollectionResult]:
        """Get result of a completed task."""
        return self.results.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task."""
        task = self.tasks.get(task_id)
        if task and task.status in [CollectionStatus.PENDING, CollectionStatus.RUNNING]:
            task.status = CollectionStatus.CANCELLED
            return True
        return False

    def get_pending_tasks(self) -> List[CollectionTask]:
        """Get all pending tasks."""
        return [
            t for t in self.tasks.values()
            if t.status == CollectionStatus.PENDING
        ]

    def get_case_history(self, case_id: str) -> List[CollectionResult]:
        """Get collection history for a case."""
        return [
            r for r in self.results.values()
            if r.case_id == case_id
        ]

    def estimate_collection_size(
        self,
        case_id: str,
        data_sources: List[DataSource]
    ) -> Dict[str, Any]:
        """Estimate size and time for collection."""
        # Based on historical data
        estimates = {
            DataSource.WHATSAPP: {"size_mb": 50, "time_minutes": 5},
            DataSource.SMS: {"size_mb": 5, "time_minutes": 1},
            DataSource.SIGNAL: {"size_mb": 30, "time_minutes": 3},
            DataSource.TELEGRAM: {"size_mb": 100, "time_minutes": 10},
            DataSource.PHOTOS: {"size_mb": 500, "time_minutes": 15},
            DataSource.CALL_LOG: {"size_mb": 1, "time_minutes": 1},
            DataSource.CONTACTS: {"size_mb": 2, "time_minutes": 1},
            DataSource.LOCATION: {"size_mb": 10, "time_minutes": 2},
            DataSource.CLOUD_BACKUP: {"size_mb": 1000, "time_minutes": 30}
        }

        total_size = 0
        total_time = 0

        for source in data_sources:
            est = estimates.get(source, {"size_mb": 10, "time_minutes": 2})
            total_size += est["size_mb"]
            total_time += est["time_minutes"]

        return {
            "estimated_size_mb": total_size,
            "estimated_time_minutes": total_time,
            "sources": [
                {"source": s.value, **estimates.get(s, {})}
                for s in data_sources
            ]
        }
