"""
Device Comparison Engine for SafeChild
Multi-device pairing, timeline sync, and contact/message matching.
"""

import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict
import difflib

logger = logging.getLogger(__name__)


class DeviceRole(Enum):
    """Role of device in parent-child relationship."""
    PARENT = "parent"
    CHILD = "child"
    UNKNOWN = "unknown"


class DeviceType(Enum):
    """Type of mobile device."""
    ANDROID = "android"
    IOS = "ios"
    UNKNOWN = "unknown"


@dataclass
class DeviceInfo:
    """Information about a device."""
    device_id: str
    device_name: str
    device_type: DeviceType
    device_role: DeviceRole
    owner_name: str
    phone_number: Optional[str] = None
    imei: Optional[str] = None
    serial_number: Optional[str] = None
    os_version: Optional[str] = None
    extraction_date: Optional[datetime] = None
    data_range_start: Optional[datetime] = None
    data_range_end: Optional[datetime] = None
    total_messages: int = 0
    total_contacts: int = 0
    total_calls: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PairedDevices:
    """Result of device pairing operation."""
    pairing_id: str
    device_a: DeviceInfo
    device_b: DeviceInfo
    relationship: str  # e.g., "parent-child", "spouse-spouse"
    common_contacts: int
    common_threads: int
    overlap_period: Tuple[datetime, datetime]
    pairing_confidence: float  # 0.0 to 1.0
    paired_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SyncedTimeline:
    """Timeline synchronized between two devices."""
    timeline_id: str
    device_a_id: str
    device_b_id: str
    start_time: datetime
    end_time: datetime
    events: List[Dict[str, Any]] = field(default_factory=list)
    gaps: List[Tuple[datetime, datetime]] = field(default_factory=list)
    sync_quality: float = 0.0  # 0.0 to 1.0


@dataclass
class ContactOverlap:
    """Contact overlap between devices."""
    contact_id: str
    name_device_a: str
    name_device_b: str
    phone_numbers: List[str]
    match_confidence: float
    exists_on_a: bool = True
    exists_on_b: bool = True
    name_mismatch: bool = False


@dataclass
class ThreadMatch:
    """Matched message thread between devices."""
    thread_id: str
    participants: List[str]
    device_a_message_count: int
    device_b_message_count: int
    common_messages: int
    missing_on_a: int
    missing_on_b: int
    match_confidence: float


class DevicePairing:
    """Pair devices based on common data patterns."""

    def __init__(self):
        self.paired_devices: List[PairedDevices] = []

    def pair_devices(
        self,
        device_a: DeviceInfo,
        device_b: DeviceInfo,
        contacts_a: List[Dict[str, Any]],
        contacts_b: List[Dict[str, Any]],
        messages_a: List[Dict[str, Any]],
        messages_b: List[Dict[str, Any]]
    ) -> PairedDevices:
        """Pair two devices and analyze their relationship."""

        # Find common contacts
        common_contacts = self._find_common_contacts(contacts_a, contacts_b)

        # Find common message threads
        common_threads = self._find_common_threads(messages_a, messages_b)

        # Calculate overlap period
        overlap_start = max(
            device_a.data_range_start or datetime.min,
            device_b.data_range_start or datetime.min
        )
        overlap_end = min(
            device_a.data_range_end or datetime.max,
            device_b.data_range_end or datetime.max
        )

        # Determine relationship
        relationship = self._determine_relationship(device_a, device_b)

        # Calculate pairing confidence
        confidence = self._calculate_pairing_confidence(
            common_contacts=len(common_contacts),
            common_threads=len(common_threads),
            total_contacts_a=len(contacts_a),
            total_contacts_b=len(contacts_b),
            messages_a=messages_a,
            messages_b=messages_b
        )

        # Generate pairing ID
        pairing_id = hashlib.sha256(
            f"{device_a.device_id}:{device_b.device_id}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]

        pairing = PairedDevices(
            pairing_id=pairing_id,
            device_a=device_a,
            device_b=device_b,
            relationship=relationship,
            common_contacts=len(common_contacts),
            common_threads=len(common_threads),
            overlap_period=(overlap_start, overlap_end),
            pairing_confidence=confidence
        )

        self.paired_devices.append(pairing)
        logger.info(f"Paired devices {device_a.device_id} and {device_b.device_id} with confidence {confidence:.2f}")

        return pairing

    def _find_common_contacts(
        self,
        contacts_a: List[Dict[str, Any]],
        contacts_b: List[Dict[str, Any]]
    ) -> List[ContactOverlap]:
        """Find contacts that exist on both devices."""
        common = []

        # Create phone number index for device B
        phone_index_b: Dict[str, Dict[str, Any]] = {}
        for contact in contacts_b:
            for phone in contact.get("phone_numbers", []):
                normalized = self._normalize_phone(phone)
                phone_index_b[normalized] = contact

        # Match contacts from device A
        for contact_a in contacts_a:
            for phone in contact_a.get("phone_numbers", []):
                normalized = self._normalize_phone(phone)
                if normalized in phone_index_b:
                    contact_b = phone_index_b[normalized]

                    # Check name match
                    name_a = contact_a.get("name", "")
                    name_b = contact_b.get("name", "")
                    name_mismatch = name_a.lower() != name_b.lower() if name_a and name_b else False

                    overlap = ContactOverlap(
                        contact_id=hashlib.md5(normalized.encode()).hexdigest()[:12],
                        name_device_a=name_a,
                        name_device_b=name_b,
                        phone_numbers=[phone],
                        match_confidence=1.0 if not name_mismatch else 0.8,
                        name_mismatch=name_mismatch
                    )
                    common.append(overlap)
                    break

        return common

    def _find_common_threads(
        self,
        messages_a: List[Dict[str, Any]],
        messages_b: List[Dict[str, Any]]
    ) -> List[ThreadMatch]:
        """Find message threads that exist on both devices."""
        threads_a = self._group_by_thread(messages_a)
        threads_b = self._group_by_thread(messages_b)

        common_threads = []

        for thread_key, msgs_a in threads_a.items():
            if thread_key in threads_b:
                msgs_b = threads_b[thread_key]

                # Count common messages by timestamp/content
                common_count = self._count_common_messages(msgs_a, msgs_b)

                thread_match = ThreadMatch(
                    thread_id=hashlib.md5(thread_key.encode()).hexdigest()[:12],
                    participants=list(thread_key.split(",")),
                    device_a_message_count=len(msgs_a),
                    device_b_message_count=len(msgs_b),
                    common_messages=common_count,
                    missing_on_a=len(msgs_b) - common_count,
                    missing_on_b=len(msgs_a) - common_count,
                    match_confidence=common_count / max(len(msgs_a), len(msgs_b)) if msgs_a or msgs_b else 0
                )
                common_threads.append(thread_match)

        return common_threads

    def _group_by_thread(self, messages: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group messages by thread (conversation participants)."""
        threads: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for msg in messages:
            # Create thread key from participants
            participants = set()
            if msg.get("sender"):
                participants.add(self._normalize_phone(msg["sender"]))
            if msg.get("recipient"):
                participants.add(self._normalize_phone(msg["recipient"]))

            thread_key = ",".join(sorted(participants))
            threads[thread_key].append(msg)

        return dict(threads)

    def _count_common_messages(
        self,
        msgs_a: List[Dict[str, Any]],
        msgs_b: List[Dict[str, Any]]
    ) -> int:
        """Count messages that appear in both lists."""
        # Create fingerprints for messages
        fingerprints_b = set()
        for msg in msgs_b:
            fp = self._message_fingerprint(msg)
            fingerprints_b.add(fp)

        common = 0
        for msg in msgs_a:
            fp = self._message_fingerprint(msg)
            if fp in fingerprints_b:
                common += 1

        return common

    def _message_fingerprint(self, msg: Dict[str, Any]) -> str:
        """Create a fingerprint for message matching."""
        # Use timestamp (within 5 second window) + content hash
        timestamp = msg.get("timestamp")
        if isinstance(timestamp, datetime):
            # Round to 5-second window
            ts_rounded = timestamp.replace(second=(timestamp.second // 5) * 5, microsecond=0)
            ts_str = ts_rounded.isoformat()
        else:
            ts_str = str(timestamp)[:19] if timestamp else ""

        content = msg.get("body", msg.get("content", ""))[:100]
        return hashlib.md5(f"{ts_str}:{content}".encode()).hexdigest()

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number for comparison."""
        if not phone:
            return ""
        # Remove all non-digits except leading +
        digits = "".join(c for c in phone if c.isdigit())
        # Keep last 10 digits for matching
        return digits[-10:] if len(digits) >= 10 else digits

    def _determine_relationship(self, device_a: DeviceInfo, device_b: DeviceInfo) -> str:
        """Determine relationship between device owners."""
        if device_a.device_role == DeviceRole.PARENT and device_b.device_role == DeviceRole.CHILD:
            return "parent-child"
        elif device_a.device_role == DeviceRole.CHILD and device_b.device_role == DeviceRole.PARENT:
            return "child-parent"
        elif device_a.device_role == device_b.device_role:
            return f"{device_a.device_role.value}-{device_b.device_role.value}"
        return "unknown"

    def _calculate_pairing_confidence(
        self,
        common_contacts: int,
        common_threads: int,
        total_contacts_a: int,
        total_contacts_b: int,
        messages_a: List[Dict[str, Any]],
        messages_b: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence score for device pairing."""
        scores = []

        # Contact overlap score
        if total_contacts_a > 0 and total_contacts_b > 0:
            contact_score = common_contacts / min(total_contacts_a, total_contacts_b)
            scores.append(min(contact_score * 2, 1.0))  # Double weight, cap at 1.0

        # Thread overlap score
        threads_a = len(self._group_by_thread(messages_a))
        threads_b = len(self._group_by_thread(messages_b))
        if threads_a > 0 and threads_b > 0:
            thread_score = common_threads / min(threads_a, threads_b)
            scores.append(min(thread_score * 2, 1.0))

        # Minimum requirements
        if common_contacts < 3 or common_threads < 1:
            return min(max(scores) * 0.5, 0.3) if scores else 0.1

        return sum(scores) / len(scores) if scores else 0.0


class TimelineSync:
    """Synchronize timelines between paired devices."""

    def __init__(self):
        self.time_tolerance = timedelta(seconds=5)

    def sync_timelines(
        self,
        events_a: List[Dict[str, Any]],
        events_b: List[Dict[str, Any]],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> SyncedTimeline:
        """Create a synchronized timeline from two devices."""

        # Determine time range
        all_timestamps = []
        for event in events_a + events_b:
            ts = event.get("timestamp")
            if isinstance(ts, datetime):
                all_timestamps.append(ts)

        if not all_timestamps:
            return SyncedTimeline(
                timeline_id=hashlib.md5(str(datetime.utcnow()).encode()).hexdigest()[:12],
                device_a_id="",
                device_b_id="",
                start_time=start_time or datetime.utcnow(),
                end_time=end_time or datetime.utcnow(),
                sync_quality=0.0
            )

        actual_start = start_time or min(all_timestamps)
        actual_end = end_time or max(all_timestamps)

        # Merge and sort events
        merged_events = []

        for event in events_a:
            merged_events.append({
                **event,
                "_source": "device_a",
                "_matched": False
            })

        for event in events_b:
            merged_events.append({
                **event,
                "_source": "device_b",
                "_matched": False
            })

        # Sort by timestamp
        merged_events.sort(key=lambda e: e.get("timestamp", datetime.max))

        # Match corresponding events
        self._match_events(merged_events)

        # Find gaps
        gaps = self._find_gaps(merged_events, actual_start, actual_end)

        # Calculate sync quality
        matched_count = sum(1 for e in merged_events if e.get("_matched"))
        sync_quality = matched_count / len(merged_events) if merged_events else 0.0

        return SyncedTimeline(
            timeline_id=hashlib.md5(f"{actual_start}:{actual_end}".encode()).hexdigest()[:12],
            device_a_id="",
            device_b_id="",
            start_time=actual_start,
            end_time=actual_end,
            events=merged_events,
            gaps=gaps,
            sync_quality=sync_quality
        )

    def _match_events(self, events: List[Dict[str, Any]]):
        """Match corresponding events between devices."""
        # Group events by approximate time window
        windows: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for event in events:
            ts = event.get("timestamp")
            if isinstance(ts, datetime):
                # 10-second window
                window_key = ts.strftime("%Y-%m-%d %H:%M:") + str(ts.second // 10)
                windows[window_key].append(event)

        # Within each window, match events
        for window_events in windows.values():
            device_a_events = [e for e in window_events if e.get("_source") == "device_a"]
            device_b_events = [e for e in window_events if e.get("_source") == "device_b"]

            for event_a in device_a_events:
                for event_b in device_b_events:
                    if self._events_match(event_a, event_b):
                        event_a["_matched"] = True
                        event_b["_matched"] = True
                        event_a["_matched_with"] = event_b.get("event_id")
                        event_b["_matched_with"] = event_a.get("event_id")
                        break

    def _events_match(self, event_a: Dict[str, Any], event_b: Dict[str, Any]) -> bool:
        """Check if two events match."""
        # Same type
        if event_a.get("type") != event_b.get("type"):
            return False

        # Similar content
        content_a = str(event_a.get("body", event_a.get("content", "")))[:100]
        content_b = str(event_b.get("body", event_b.get("content", "")))[:100]

        if content_a and content_b:
            similarity = difflib.SequenceMatcher(None, content_a, content_b).ratio()
            return similarity > 0.9

        return True  # If no content, match by type and time only

    def _find_gaps(
        self,
        events: List[Dict[str, Any]],
        start: datetime,
        end: datetime
    ) -> List[Tuple[datetime, datetime]]:
        """Find time gaps in the timeline."""
        gaps = []
        gap_threshold = timedelta(hours=6)  # 6 hour gap is significant

        sorted_events = sorted(
            [e for e in events if isinstance(e.get("timestamp"), datetime)],
            key=lambda e: e["timestamp"]
        )

        if not sorted_events:
            return [(start, end)]

        # Check gap at start
        if sorted_events[0]["timestamp"] - start > gap_threshold:
            gaps.append((start, sorted_events[0]["timestamp"]))

        # Check gaps between events
        for i in range(len(sorted_events) - 1):
            current_ts = sorted_events[i]["timestamp"]
            next_ts = sorted_events[i + 1]["timestamp"]

            if next_ts - current_ts > gap_threshold:
                gaps.append((current_ts, next_ts))

        # Check gap at end
        if end - sorted_events[-1]["timestamp"] > gap_threshold:
            gaps.append((sorted_events[-1]["timestamp"], end))

        return gaps


class ContactMatcher:
    """Match contacts between devices."""

    def match_contacts(
        self,
        contacts_a: List[Dict[str, Any]],
        contacts_b: List[Dict[str, Any]]
    ) -> Tuple[List[ContactOverlap], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Match contacts between two devices.

        Returns:
            Tuple of (matched contacts, only on A, only on B)
        """
        matched = []
        only_on_a = []
        only_on_b = []

        # Index contacts by normalized phone
        indexed_b: Dict[str, Dict[str, Any]] = {}
        matched_b_ids: Set[str] = set()

        for contact in contacts_b:
            contact_id = contact.get("id", str(hash(str(contact))))
            for phone in contact.get("phone_numbers", []):
                normalized = self._normalize_phone(phone)
                indexed_b[normalized] = {**contact, "_id": contact_id}

        # Match contacts from A
        for contact_a in contacts_a:
            found_match = False
            for phone in contact_a.get("phone_numbers", []):
                normalized = self._normalize_phone(phone)
                if normalized in indexed_b:
                    contact_b = indexed_b[normalized]
                    matched_b_ids.add(contact_b["_id"])

                    overlap = ContactOverlap(
                        contact_id=hashlib.md5(normalized.encode()).hexdigest()[:12],
                        name_device_a=contact_a.get("name", ""),
                        name_device_b=contact_b.get("name", ""),
                        phone_numbers=[phone],
                        match_confidence=1.0,
                        name_mismatch=contact_a.get("name", "").lower() != contact_b.get("name", "").lower()
                    )
                    matched.append(overlap)
                    found_match = True
                    break

            if not found_match:
                only_on_a.append(contact_a)

        # Find contacts only on B
        for contact in contacts_b:
            contact_id = contact.get("id", str(hash(str(contact))))
            if contact_id not in matched_b_ids:
                only_on_b.append(contact)

        return matched, only_on_a, only_on_b

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number."""
        if not phone:
            return ""
        digits = "".join(c for c in phone if c.isdigit())
        return digits[-10:] if len(digits) >= 10 else digits


class MessageThreadMatcher:
    """Match message threads between devices."""

    def match_threads(
        self,
        messages_a: List[Dict[str, Any]],
        messages_b: List[Dict[str, Any]]
    ) -> List[ThreadMatch]:
        """Match message threads between two devices."""
        threads_a = self._group_by_thread(messages_a)
        threads_b = self._group_by_thread(messages_b)

        all_thread_keys = set(threads_a.keys()) | set(threads_b.keys())
        matches = []

        for thread_key in all_thread_keys:
            msgs_a = threads_a.get(thread_key, [])
            msgs_b = threads_b.get(thread_key, [])

            # Find common messages
            common_count = self._count_common(msgs_a, msgs_b)

            thread_match = ThreadMatch(
                thread_id=hashlib.md5(thread_key.encode()).hexdigest()[:12],
                participants=thread_key.split(",") if thread_key else [],
                device_a_message_count=len(msgs_a),
                device_b_message_count=len(msgs_b),
                common_messages=common_count,
                missing_on_a=max(0, len(msgs_b) - common_count),
                missing_on_b=max(0, len(msgs_a) - common_count),
                match_confidence=self._calculate_match_confidence(msgs_a, msgs_b, common_count)
            )
            matches.append(thread_match)

        return matches

    def _group_by_thread(self, messages: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group messages by thread."""
        threads: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for msg in messages:
            participants = set()
            sender = msg.get("sender", "")
            recipient = msg.get("recipient", "")

            if sender:
                participants.add(self._normalize_phone(sender))
            if recipient:
                participants.add(self._normalize_phone(recipient))

            thread_key = ",".join(sorted(participants))
            threads[thread_key].append(msg)

        return dict(threads)

    def _count_common(
        self,
        msgs_a: List[Dict[str, Any]],
        msgs_b: List[Dict[str, Any]]
    ) -> int:
        """Count common messages."""
        fingerprints_b = set()
        for msg in msgs_b:
            fp = self._fingerprint(msg)
            fingerprints_b.add(fp)

        count = 0
        for msg in msgs_a:
            fp = self._fingerprint(msg)
            if fp in fingerprints_b:
                count += 1

        return count

    def _fingerprint(self, msg: Dict[str, Any]) -> str:
        """Create message fingerprint."""
        ts = msg.get("timestamp")
        if isinstance(ts, datetime):
            ts_str = ts.strftime("%Y-%m-%d %H:%M")
        else:
            ts_str = str(ts)[:16] if ts else ""

        content = str(msg.get("body", msg.get("content", "")))[:50]
        return hashlib.md5(f"{ts_str}:{content}".encode()).hexdigest()

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number."""
        if not phone:
            return ""
        digits = "".join(c for c in phone if c.isdigit())
        return digits[-10:] if len(digits) >= 10 else digits

    def _calculate_match_confidence(
        self,
        msgs_a: List[Dict[str, Any]],
        msgs_b: List[Dict[str, Any]],
        common: int
    ) -> float:
        """Calculate thread match confidence."""
        total = max(len(msgs_a), len(msgs_b))
        if total == 0:
            return 0.0
        return common / total


class DeviceComparisonEngine:
    """Main engine for multi-device comparison."""

    def __init__(self):
        self.device_pairing = DevicePairing()
        self.timeline_sync = TimelineSync()
        self.contact_matcher = ContactMatcher()
        self.thread_matcher = MessageThreadMatcher()

    def compare_devices(
        self,
        device_a: DeviceInfo,
        device_b: DeviceInfo,
        contacts_a: List[Dict[str, Any]],
        contacts_b: List[Dict[str, Any]],
        messages_a: List[Dict[str, Any]],
        messages_b: List[Dict[str, Any]],
        calls_a: Optional[List[Dict[str, Any]]] = None,
        calls_b: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive comparison between two devices.

        Returns complete comparison report.
        """
        calls_a = calls_a or []
        calls_b = calls_b or []

        # Pair devices
        pairing = self.device_pairing.pair_devices(
            device_a, device_b,
            contacts_a, contacts_b,
            messages_a, messages_b
        )

        # Match contacts
        matched_contacts, only_a_contacts, only_b_contacts = self.contact_matcher.match_contacts(
            contacts_a, contacts_b
        )

        # Match message threads
        thread_matches = self.thread_matcher.match_threads(messages_a, messages_b)

        # Sync timelines
        all_events_a = [
            {**m, "type": "message"} for m in messages_a
        ] + [
            {**c, "type": "call"} for c in calls_a
        ]

        all_events_b = [
            {**m, "type": "message"} for m in messages_b
        ] + [
            {**c, "type": "call"} for c in calls_b
        ]

        synced_timeline = self.timeline_sync.sync_timelines(all_events_a, all_events_b)

        # Calculate statistics
        total_discrepancies = (
            len(only_a_contacts) + len(only_b_contacts) +
            sum(t.missing_on_a + t.missing_on_b for t in thread_matches)
        )

        return {
            "pairing": {
                "pairing_id": pairing.pairing_id,
                "relationship": pairing.relationship,
                "confidence": pairing.pairing_confidence,
                "overlap_period": {
                    "start": pairing.overlap_period[0].isoformat() if pairing.overlap_period[0] != datetime.min else None,
                    "end": pairing.overlap_period[1].isoformat() if pairing.overlap_period[1] != datetime.max else None
                }
            },
            "contacts": {
                "matched": len(matched_contacts),
                "only_on_device_a": len(only_a_contacts),
                "only_on_device_b": len(only_b_contacts),
                "name_mismatches": sum(1 for c in matched_contacts if c.name_mismatch),
                "details": [
                    {
                        "contact_id": c.contact_id,
                        "name_a": c.name_device_a,
                        "name_b": c.name_device_b,
                        "phones": c.phone_numbers,
                        "mismatch": c.name_mismatch
                    } for c in matched_contacts[:50]  # Limit for response size
                ]
            },
            "message_threads": {
                "total_threads": len(thread_matches),
                "threads_with_discrepancies": sum(1 for t in thread_matches if t.missing_on_a > 0 or t.missing_on_b > 0),
                "total_missing_on_a": sum(t.missing_on_a for t in thread_matches),
                "total_missing_on_b": sum(t.missing_on_b for t in thread_matches),
                "details": [
                    {
                        "thread_id": t.thread_id,
                        "participants": t.participants,
                        "device_a_count": t.device_a_message_count,
                        "device_b_count": t.device_b_message_count,
                        "common": t.common_messages,
                        "missing_on_a": t.missing_on_a,
                        "missing_on_b": t.missing_on_b,
                        "confidence": t.match_confidence
                    } for t in thread_matches
                ]
            },
            "timeline": {
                "timeline_id": synced_timeline.timeline_id,
                "start": synced_timeline.start_time.isoformat(),
                "end": synced_timeline.end_time.isoformat(),
                "total_events": len(synced_timeline.events),
                "sync_quality": synced_timeline.sync_quality,
                "gaps": [
                    {"start": g[0].isoformat(), "end": g[1].isoformat()}
                    for g in synced_timeline.gaps
                ]
            },
            "summary": {
                "total_discrepancies": total_discrepancies,
                "pairing_confidence": pairing.pairing_confidence,
                "sync_quality": synced_timeline.sync_quality,
                "requires_investigation": total_discrepancies > 10 or pairing.pairing_confidence < 0.5
            }
        }
