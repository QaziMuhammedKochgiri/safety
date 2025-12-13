"""
Change Detector for Evidence Collection
Detects changes, deletions, and modifications in collected data.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set
from enum import Enum
from datetime import datetime, timedelta
import hashlib


class ChangeType(str, Enum):
    """Types of detected changes."""
    NEW = "new"  # New item added
    MODIFIED = "modified"  # Existing item changed
    DELETED = "deleted"  # Item removed
    MOVED = "moved"  # Item relocated
    EDITED = "edited"  # Content edited (messages)
    UNSENT = "unsent"  # Message unsent/recalled
    SUSPICIOUS = "suspicious"  # Suspicious pattern


@dataclass
class DetectedChange:
    """A single detected change."""
    change_id: str
    change_type: ChangeType
    source: str
    item_id: str
    timestamp: datetime
    detection_timestamp: datetime
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    confidence: float = 1.0
    is_suspicious: bool = False
    suspicion_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChangeReport:
    """Report of changes detected."""
    report_id: str
    case_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    total_changes: int
    changes_by_type: Dict[ChangeType, int]
    changes_by_source: Dict[str, int]
    suspicious_changes: List[DetectedChange]
    all_changes: List[DetectedChange]
    summary: str


class ChangeDetector:
    """Detects changes in collected evidence."""

    def __init__(self):
        self.snapshots: Dict[str, Dict[str, str]] = {}  # case_id -> {item_id: hash}
        self.change_history: Dict[str, List[DetectedChange]] = {}  # case_id -> changes

    def take_snapshot(
        self,
        case_id: str,
        items: List[Dict[str, Any]]
    ) -> str:
        """Take a snapshot of current state."""
        snapshot_id = f"snap_{case_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        item_hashes = {}
        for item in items:
            item_id = item.get("id") or item.get("item_id")
            content = str(item.get("content") or item.get("body") or item)
            item_hash = hashlib.sha256(content.encode()).hexdigest()
            item_hashes[item_id] = item_hash

        self.snapshots[case_id] = item_hashes
        return snapshot_id

    def detect_changes(
        self,
        case_id: str,
        current_items: List[Dict[str, Any]],
        previous_snapshot_id: Optional[str] = None
    ) -> List[DetectedChange]:
        """Detect changes between current state and last snapshot."""
        changes: List[DetectedChange] = []
        detection_time = datetime.utcnow()

        # Get previous snapshot
        previous_hashes = self.snapshots.get(case_id, {})

        # Build current hash map
        current_hashes = {}
        current_items_map = {}

        for item in current_items:
            item_id = item.get("id") or item.get("item_id")
            content = str(item.get("content") or item.get("body") or item)
            item_hash = hashlib.sha256(content.encode()).hexdigest()
            current_hashes[item_id] = item_hash
            current_items_map[item_id] = item

        # Detect new items
        for item_id, item_hash in current_hashes.items():
            if item_id not in previous_hashes:
                item = current_items_map[item_id]
                change = DetectedChange(
                    change_id=f"chg_{item_id}_{detection_time.timestamp()}",
                    change_type=ChangeType.NEW,
                    source=item.get("source", "unknown"),
                    item_id=item_id,
                    timestamp=item.get("timestamp", detection_time),
                    detection_timestamp=detection_time,
                    new_value=item.get("content") or item.get("body"),
                    new_hash=item_hash
                )
                changes.append(change)

        # Detect modified items
        for item_id, item_hash in current_hashes.items():
            if item_id in previous_hashes and previous_hashes[item_id] != item_hash:
                item = current_items_map[item_id]
                change = DetectedChange(
                    change_id=f"chg_{item_id}_{detection_time.timestamp()}",
                    change_type=ChangeType.MODIFIED,
                    source=item.get("source", "unknown"),
                    item_id=item_id,
                    timestamp=item.get("timestamp", detection_time),
                    detection_timestamp=detection_time,
                    new_value=item.get("content") or item.get("body"),
                    old_hash=previous_hashes[item_id],
                    new_hash=item_hash,
                    is_suspicious=True,
                    suspicion_reason="Message content changed after initial collection"
                )
                changes.append(change)

        # Detect deleted items
        for item_id, old_hash in previous_hashes.items():
            if item_id not in current_hashes:
                change = DetectedChange(
                    change_id=f"chg_{item_id}_{detection_time.timestamp()}",
                    change_type=ChangeType.DELETED,
                    source="unknown",
                    item_id=item_id,
                    timestamp=detection_time,
                    detection_timestamp=detection_time,
                    old_hash=old_hash,
                    is_suspicious=True,
                    suspicion_reason="Item deleted between collections"
                )
                changes.append(change)

        # Update snapshot
        self.snapshots[case_id] = current_hashes

        # Store in history
        if case_id not in self.change_history:
            self.change_history[case_id] = []
        self.change_history[case_id].extend(changes)

        # Check for suspicious patterns
        self._analyze_suspicious_patterns(case_id, changes)

        return changes

    def _analyze_suspicious_patterns(
        self,
        case_id: str,
        changes: List[DetectedChange]
    ):
        """Analyze changes for suspicious patterns."""
        # Pattern 1: Mass deletion
        deletions = [c for c in changes if c.change_type == ChangeType.DELETED]
        if len(deletions) >= 5:
            for change in deletions:
                change.is_suspicious = True
                change.suspicion_reason = f"Mass deletion detected ({len(deletions)} items)"

        # Pattern 2: Rapid modifications
        modifications = [c for c in changes if c.change_type == ChangeType.MODIFIED]
        if len(modifications) >= 3:
            for change in modifications:
                change.is_suspicious = True
                change.suspicion_reason = f"Multiple modifications detected ({len(modifications)} items)"

        # Pattern 3: Timeline gaps (check history)
        history = self.change_history.get(case_id, [])
        if len(history) >= 10:
            # Check for periods with suspiciously few changes
            self._detect_timeline_gaps(history)

    def _detect_timeline_gaps(self, history: List[DetectedChange]):
        """Detect suspicious gaps in timeline."""
        if len(history) < 2:
            return

        sorted_changes = sorted(history, key=lambda c: c.timestamp)

        for i in range(1, len(sorted_changes)):
            gap = (sorted_changes[i].timestamp - sorted_changes[i-1].timestamp).days
            if gap > 7:  # 7 day gap might indicate deletion of evidence
                # Mark surrounding changes as suspicious
                sorted_changes[i].is_suspicious = True
                sorted_changes[i].suspicion_reason = f"Detected after {gap}-day gap in timeline"

    def detect_edited_messages(
        self,
        case_id: str,
        messages: List[Dict[str, Any]]
    ) -> List[DetectedChange]:
        """Specifically detect edited messages in messaging apps."""
        changes = []
        detection_time = datetime.utcnow()

        for msg in messages:
            # Check for edit indicators
            is_edited = (
                msg.get("is_edited", False) or
                msg.get("edited", False) or
                msg.get("edit_timestamp") is not None
            )

            if is_edited:
                change = DetectedChange(
                    change_id=f"edit_{msg.get('id')}_{detection_time.timestamp()}",
                    change_type=ChangeType.EDITED,
                    source=msg.get("source", "unknown"),
                    item_id=msg.get("id") or msg.get("message_id"),
                    timestamp=msg.get("edit_timestamp") or msg.get("timestamp"),
                    detection_timestamp=detection_time,
                    new_value=msg.get("content") or msg.get("body"),
                    old_value=msg.get("original_content"),
                    is_suspicious=True,
                    suspicion_reason="Message was edited after sending",
                    metadata={
                        "original_timestamp": msg.get("timestamp"),
                        "edit_timestamp": msg.get("edit_timestamp")
                    }
                )
                changes.append(change)

        return changes

    def detect_unsent_messages(
        self,
        case_id: str,
        previous_messages: List[Dict[str, Any]],
        current_messages: List[Dict[str, Any]]
    ) -> List[DetectedChange]:
        """Detect messages that were unsent/recalled."""
        changes = []
        detection_time = datetime.utcnow()

        previous_ids = {m.get("id") or m.get("message_id") for m in previous_messages}
        current_ids = {m.get("id") or m.get("message_id") for m in current_messages}

        # Find messages that disappeared
        unsent_ids = previous_ids - current_ids

        # Build lookup for previous messages
        prev_lookup = {
            m.get("id") or m.get("message_id"): m
            for m in previous_messages
        }

        for msg_id in unsent_ids:
            msg = prev_lookup.get(msg_id)
            if msg:
                change = DetectedChange(
                    change_id=f"unsent_{msg_id}_{detection_time.timestamp()}",
                    change_type=ChangeType.UNSENT,
                    source=msg.get("source", "unknown"),
                    item_id=msg_id,
                    timestamp=detection_time,
                    detection_timestamp=detection_time,
                    old_value=msg.get("content") or msg.get("body"),
                    is_suspicious=True,
                    suspicion_reason="Message was deleted/unsent after being sent",
                    metadata={
                        "original_timestamp": msg.get("timestamp"),
                        "sender": msg.get("sender")
                    }
                )
                changes.append(change)

        return changes

    def generate_report(
        self,
        case_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> ChangeReport:
        """Generate a change report for a case."""
        history = self.change_history.get(case_id, [])

        # Filter by period
        if period_start:
            history = [c for c in history if c.detection_timestamp >= period_start]
        if period_end:
            history = [c for c in history if c.detection_timestamp <= period_end]

        # Calculate statistics
        changes_by_type: Dict[ChangeType, int] = {}
        changes_by_source: Dict[str, int] = {}
        suspicious_changes: List[DetectedChange] = []

        for change in history:
            # By type
            changes_by_type[change.change_type] = changes_by_type.get(change.change_type, 0) + 1

            # By source
            changes_by_source[change.source] = changes_by_source.get(change.source, 0) + 1

            # Suspicious
            if change.is_suspicious:
                suspicious_changes.append(change)

        # Generate summary
        summary = self._generate_summary(
            len(history),
            changes_by_type,
            len(suspicious_changes)
        )

        return ChangeReport(
            report_id=f"report_{case_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            case_id=case_id,
            generated_at=datetime.utcnow(),
            period_start=period_start or (history[0].detection_timestamp if history else datetime.utcnow()),
            period_end=period_end or datetime.utcnow(),
            total_changes=len(history),
            changes_by_type=changes_by_type,
            changes_by_source=changes_by_source,
            suspicious_changes=suspicious_changes,
            all_changes=history,
            summary=summary
        )

    def _generate_summary(
        self,
        total: int,
        by_type: Dict[ChangeType, int],
        suspicious_count: int
    ) -> str:
        """Generate a summary of changes."""
        if total == 0:
            return "No changes detected during this period."

        parts = [f"Detected {total} change(s)."]

        if ChangeType.NEW in by_type:
            parts.append(f"{by_type[ChangeType.NEW]} new item(s).")

        if ChangeType.MODIFIED in by_type:
            parts.append(f"{by_type[ChangeType.MODIFIED]} modified item(s).")

        if ChangeType.DELETED in by_type:
            parts.append(f"{by_type[ChangeType.DELETED]} deleted item(s).")

        if ChangeType.EDITED in by_type:
            parts.append(f"{by_type[ChangeType.EDITED]} edited message(s).")

        if ChangeType.UNSENT in by_type:
            parts.append(f"{by_type[ChangeType.UNSENT]} unsent/recalled message(s).")

        if suspicious_count > 0:
            parts.append(f"WARNING: {suspicious_count} suspicious change(s) require attention.")

        return " ".join(parts)

    def get_suspicious_changes(
        self,
        case_id: str,
        min_confidence: float = 0.0
    ) -> List[DetectedChange]:
        """Get all suspicious changes for a case."""
        history = self.change_history.get(case_id, [])
        return [
            c for c in history
            if c.is_suspicious and c.confidence >= min_confidence
        ]

    def clear_history(self, case_id: str):
        """Clear change history for a case."""
        if case_id in self.change_history:
            del self.change_history[case_id]
        if case_id in self.snapshots:
            del self.snapshots[case_id]
