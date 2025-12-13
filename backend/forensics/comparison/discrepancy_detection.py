"""
Discrepancy Detection for SafeChild
Detect deleted messages, edit history, time gaps, and screenshot verification.
"""

import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
import difflib
import re

logger = logging.getLogger(__name__)


class DiscrepancyType(Enum):
    """Types of discrepancies between devices."""
    DELETED_MESSAGE = "deleted_message"
    EDITED_MESSAGE = "edited_message"
    TIME_GAP = "time_gap"
    MISSING_CONTACT = "missing_contact"
    SCREENSHOT_MISMATCH = "screenshot_mismatch"
    TIMESTAMP_INCONSISTENCY = "timestamp_inconsistency"
    CONTENT_ALTERED = "content_altered"


class SeverityLevel(Enum):
    """Severity levels for discrepancies."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Discrepancy:
    """Base discrepancy record."""
    discrepancy_id: str
    discrepancy_type: DiscrepancyType
    severity: SeverityLevel
    device_a_id: str
    device_b_id: str
    timestamp: Optional[datetime]
    description: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    forensic_notes: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DeletedMessage:
    """A message that exists on one device but not the other."""
    message_id: str
    exists_on_device: str  # device_a or device_b
    missing_from_device: str
    sender: str
    recipient: str
    timestamp: datetime
    content_preview: str
    content_hash: str
    message_type: str  # SMS, WhatsApp, etc.
    is_incoming: bool
    severity: SeverityLevel = SeverityLevel.MEDIUM
    possible_reasons: List[str] = field(default_factory=list)


@dataclass
class EditHistory:
    """Edit history for a message."""
    message_id: str
    thread_id: str
    original_content: str
    edited_content: str
    original_timestamp: datetime
    edit_timestamp: Optional[datetime]
    device_a_version: str
    device_b_version: str
    edit_type: str  # text_change, deletion, addition
    change_summary: str
    severity: SeverityLevel = SeverityLevel.MEDIUM


@dataclass
class TimeGap:
    """Unexplained gap in timeline."""
    gap_id: str
    start_time: datetime
    end_time: datetime
    duration_hours: float
    device_id: str
    context_before: Optional[str]
    context_after: Optional[str]
    expected_activity: bool  # True if activity was expected during this time
    severity: SeverityLevel = SeverityLevel.LOW
    possible_explanations: List[str] = field(default_factory=list)


@dataclass
class ScreenshotMatch:
    """Result of screenshot vs original message verification."""
    match_id: str
    screenshot_path: str
    original_message_id: Optional[str]
    screenshot_content: str
    original_content: Optional[str]
    match_confidence: float
    discrepancies_found: List[str]
    timestamp_matches: bool
    sender_matches: bool
    content_matches: bool
    is_authentic: bool
    severity: SeverityLevel = SeverityLevel.LOW


class DeletedMessageFinder:
    """Find messages that exist on one device but not the other."""

    def __init__(self):
        self.time_tolerance = timedelta(seconds=10)

    def find_deleted_messages(
        self,
        messages_a: List[Dict[str, Any]],
        messages_b: List[Dict[str, Any]],
        device_a_id: str,
        device_b_id: str
    ) -> List[DeletedMessage]:
        """Find messages missing from either device."""
        deleted = []

        # Create fingerprint indices
        fingerprints_a = {self._fingerprint(m): m for m in messages_a}
        fingerprints_b = {self._fingerprint(m): m for m in messages_b}

        # Find messages in A but not in B
        for fp, msg in fingerprints_a.items():
            if fp not in fingerprints_b:
                deleted.append(self._create_deleted_message(
                    msg, device_a_id, device_b_id, "device_a", "device_b"
                ))

        # Find messages in B but not in A
        for fp, msg in fingerprints_b.items():
            if fp not in fingerprints_a:
                deleted.append(self._create_deleted_message(
                    msg, device_a_id, device_b_id, "device_b", "device_a"
                ))

        # Sort by timestamp
        deleted.sort(key=lambda d: d.timestamp or datetime.min)

        logger.info(f"Found {len(deleted)} deleted/missing messages")
        return deleted

    def _fingerprint(self, msg: Dict[str, Any]) -> str:
        """Create message fingerprint."""
        ts = msg.get("timestamp")
        if isinstance(ts, datetime):
            # Round to 10-second window
            ts_rounded = ts.replace(second=(ts.second // 10) * 10, microsecond=0)
            ts_str = ts_rounded.isoformat()
        else:
            ts_str = str(ts)[:19] if ts else ""

        # Normalize participants
        sender = self._normalize_phone(msg.get("sender", ""))
        recipient = self._normalize_phone(msg.get("recipient", ""))
        participants = ",".join(sorted([sender, recipient]))

        # Content (first 100 chars)
        content = str(msg.get("body", msg.get("content", "")))[:100].lower()
        content = re.sub(r'\s+', ' ', content).strip()

        return hashlib.md5(f"{ts_str}:{participants}:{content}".encode()).hexdigest()

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number."""
        if not phone:
            return ""
        digits = "".join(c for c in phone if c.isdigit())
        return digits[-10:] if len(digits) >= 10 else digits

    def _create_deleted_message(
        self,
        msg: Dict[str, Any],
        device_a_id: str,
        device_b_id: str,
        exists_on: str,
        missing_from: str
    ) -> DeletedMessage:
        """Create DeletedMessage record."""
        content = str(msg.get("body", msg.get("content", "")))
        timestamp = msg.get("timestamp")

        if not isinstance(timestamp, datetime):
            timestamp = datetime.utcnow()

        # Determine severity based on content
        severity = self._assess_severity(content, msg)

        # Determine possible reasons
        reasons = self._determine_possible_reasons(msg, exists_on)

        return DeletedMessage(
            message_id=hashlib.md5(self._fingerprint(msg).encode()).hexdigest()[:12],
            exists_on_device=exists_on,
            missing_from_device=missing_from,
            sender=msg.get("sender", "Unknown"),
            recipient=msg.get("recipient", "Unknown"),
            timestamp=timestamp,
            content_preview=content[:200] + "..." if len(content) > 200 else content,
            content_hash=hashlib.sha256(content.encode()).hexdigest()[:16],
            message_type=msg.get("source", msg.get("type", "Unknown")),
            is_incoming=msg.get("is_incoming", msg.get("direction") == "incoming"),
            severity=severity,
            possible_reasons=reasons
        )

    def _assess_severity(self, content: str, msg: Dict[str, Any]) -> SeverityLevel:
        """Assess severity of deleted message."""
        content_lower = content.lower()

        # High-risk keywords
        high_risk = [
            "tehdit", "threat", "kill", "öldür", "hurt", "zarar",
            "dava", "court", "lawyer", "avukat", "police", "polis",
            "custody", "velayet", "child", "çocuk"
        ]

        # Check for high-risk content
        for keyword in high_risk:
            if keyword in content_lower:
                return SeverityLevel.HIGH

        # Check message timing (recent messages are more suspicious)
        timestamp = msg.get("timestamp")
        if isinstance(timestamp, datetime):
            days_old = (datetime.utcnow() - timestamp).days
            if days_old < 7:
                return SeverityLevel.MEDIUM

        return SeverityLevel.LOW

    def _determine_possible_reasons(self, msg: Dict[str, Any], exists_on: str) -> List[str]:
        """Determine possible reasons for missing message."""
        reasons = []

        # Check message type
        msg_type = msg.get("source", msg.get("type", "")).lower()
        if "whatsapp" in msg_type:
            reasons.append("WhatsApp message deletion (by sender or recipient)")
            reasons.append("WhatsApp disappearing messages feature")

        # Check if it's a media message
        if msg.get("has_media") or msg.get("media_type"):
            reasons.append("Media file not backed up or synced")

        # General reasons
        reasons.extend([
            "Manual deletion by user",
            "Different backup timestamps",
            "Network sync delay",
            "App reinstallation"
        ])

        return reasons


class EditHistoryComparer:
    """Compare message edit histories between devices."""

    def __init__(self):
        self.similarity_threshold = 0.8

    def compare_edit_history(
        self,
        messages_a: List[Dict[str, Any]],
        messages_b: List[Dict[str, Any]]
    ) -> List[EditHistory]:
        """Find messages with different versions on each device."""
        edits = []

        # Index messages by thread and approximate time
        indexed_b = self._index_messages(messages_b)

        for msg_a in messages_a:
            potential_match = self._find_potential_match(msg_a, indexed_b)

            if potential_match:
                content_a = str(msg_a.get("body", msg_a.get("content", "")))
                content_b = str(potential_match.get("body", potential_match.get("content", "")))

                # Check if content differs
                if content_a != content_b:
                    similarity = difflib.SequenceMatcher(None, content_a, content_b).ratio()

                    # Only report if similar enough to be the same message but different
                    if 0.5 < similarity < 0.99:
                        edit_history = self._create_edit_history(
                            msg_a, potential_match, content_a, content_b, similarity
                        )
                        edits.append(edit_history)

        logger.info(f"Found {len(edits)} edited messages")
        return edits

    def _index_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Index messages by thread and time window."""
        index: Dict[str, List[Dict[str, Any]]] = {}

        for msg in messages:
            key = self._get_index_key(msg)
            if key not in index:
                index[key] = []
            index[key].append(msg)

        return index

    def _get_index_key(self, msg: Dict[str, Any]) -> str:
        """Get index key for message."""
        sender = self._normalize_phone(msg.get("sender", ""))
        recipient = self._normalize_phone(msg.get("recipient", ""))
        participants = ",".join(sorted([sender, recipient]))

        ts = msg.get("timestamp")
        if isinstance(ts, datetime):
            time_key = ts.strftime("%Y-%m-%d %H:%M")
        else:
            time_key = str(ts)[:16] if ts else ""

        return f"{participants}:{time_key}"

    def _find_potential_match(
        self,
        msg: Dict[str, Any],
        index: Dict[str, List[Dict[str, Any]]]
    ) -> Optional[Dict[str, Any]]:
        """Find potential matching message in index."""
        key = self._get_index_key(msg)

        if key in index:
            for candidate in index[key]:
                # Check if sender/recipient match
                if (self._normalize_phone(msg.get("sender", "")) ==
                    self._normalize_phone(candidate.get("sender", ""))):
                    return candidate

        return None

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number."""
        if not phone:
            return ""
        digits = "".join(c for c in phone if c.isdigit())
        return digits[-10:] if len(digits) >= 10 else digits

    def _create_edit_history(
        self,
        msg_a: Dict[str, Any],
        msg_b: Dict[str, Any],
        content_a: str,
        content_b: str,
        similarity: float
    ) -> EditHistory:
        """Create edit history record."""
        # Determine edit type
        if len(content_a) > len(content_b):
            edit_type = "deletion"
        elif len(content_a) < len(content_b):
            edit_type = "addition"
        else:
            edit_type = "text_change"

        # Create change summary
        diff = list(difflib.unified_diff(
            content_a.split(),
            content_b.split(),
            lineterm=""
        ))
        change_summary = " ".join(diff[:10]) if diff else "Minor text changes"

        timestamp_a = msg_a.get("timestamp")
        timestamp_b = msg_b.get("timestamp")

        return EditHistory(
            message_id=hashlib.md5(f"{content_a}:{content_b}".encode()).hexdigest()[:12],
            thread_id=self._get_index_key(msg_a).split(":")[0],
            original_content=content_a,
            edited_content=content_b,
            original_timestamp=timestamp_a if isinstance(timestamp_a, datetime) else datetime.utcnow(),
            edit_timestamp=timestamp_b if isinstance(timestamp_b, datetime) else None,
            device_a_version=content_a[:100],
            device_b_version=content_b[:100],
            edit_type=edit_type,
            change_summary=change_summary[:200],
            severity=SeverityLevel.MEDIUM if similarity < 0.7 else SeverityLevel.LOW
        )


class TimeGapAnalyzer:
    """Analyze time gaps in device activity."""

    def __init__(self):
        self.minimum_gap_hours = 6  # Minimum gap to report

    def analyze_gaps(
        self,
        events: List[Dict[str, Any]],
        device_id: str,
        expected_active_hours: Tuple[int, int] = (8, 22)  # 8 AM to 10 PM
    ) -> List[TimeGap]:
        """Find unexplained gaps in activity."""
        gaps = []

        # Sort events by timestamp
        sorted_events = sorted(
            [e for e in events if isinstance(e.get("timestamp"), datetime)],
            key=lambda e: e["timestamp"]
        )

        if len(sorted_events) < 2:
            return gaps

        for i in range(len(sorted_events) - 1):
            current = sorted_events[i]
            next_event = sorted_events[i + 1]

            current_ts = current["timestamp"]
            next_ts = next_event["timestamp"]

            gap_duration = next_ts - current_ts
            gap_hours = gap_duration.total_seconds() / 3600

            if gap_hours >= self.minimum_gap_hours:
                # Check if gap is during expected active hours
                expected_activity = self._is_expected_active(
                    current_ts, next_ts, expected_active_hours
                )

                # Assess severity
                severity = self._assess_gap_severity(gap_hours, expected_activity)

                gap = TimeGap(
                    gap_id=hashlib.md5(f"{device_id}:{current_ts}:{next_ts}".encode()).hexdigest()[:12],
                    start_time=current_ts,
                    end_time=next_ts,
                    duration_hours=gap_hours,
                    device_id=device_id,
                    context_before=str(current.get("body", current.get("content", "")))[:100],
                    context_after=str(next_event.get("body", next_event.get("content", "")))[:100],
                    expected_activity=expected_activity,
                    severity=severity,
                    possible_explanations=self._get_gap_explanations(gap_hours, expected_activity)
                )
                gaps.append(gap)

        logger.info(f"Found {len(gaps)} time gaps for device {device_id}")
        return gaps

    def _is_expected_active(
        self,
        start: datetime,
        end: datetime,
        active_hours: Tuple[int, int]
    ) -> bool:
        """Check if gap falls during expected active hours."""
        start_hour = active_hours[0]
        end_hour = active_hours[1]

        # Check multiple days if gap spans multiple days
        current = start
        while current < end:
            if start_hour <= current.hour < end_hour:
                return True
            current += timedelta(hours=1)

        return False

    def _assess_gap_severity(self, gap_hours: float, expected_activity: bool) -> SeverityLevel:
        """Assess severity of time gap."""
        if expected_activity:
            if gap_hours >= 24:
                return SeverityLevel.HIGH
            elif gap_hours >= 12:
                return SeverityLevel.MEDIUM
            else:
                return SeverityLevel.LOW
        else:
            # Overnight gaps are less concerning
            if gap_hours >= 48:
                return SeverityLevel.MEDIUM
            else:
                return SeverityLevel.LOW

    def _get_gap_explanations(self, gap_hours: float, expected_activity: bool) -> List[str]:
        """Get possible explanations for gap."""
        explanations = []

        if not expected_activity:
            explanations.append("Gap during typical sleep hours")

        if gap_hours < 12:
            explanations.extend([
                "Normal activity break",
                "Work/school hours",
                "Phone powered off or airplane mode"
            ])
        elif gap_hours < 24:
            explanations.extend([
                "Extended period without phone",
                "Device not synced during this period",
                "Possible data deletion"
            ])
        else:
            explanations.extend([
                "Extended absence from device",
                "Device factory reset",
                "Significant data deletion",
                "App reinstallation"
            ])

        return explanations


class ScreenshotVerifier:
    """Verify screenshots against original messages."""

    def __init__(self):
        self._ocr = None  # Lazy loaded

    def _load_ocr(self):
        """Lazy load OCR capability."""
        if self._ocr is None:
            try:
                import pytesseract
                self._ocr = pytesseract
                logger.info("Tesseract OCR loaded for screenshot verification")
            except ImportError:
                logger.warning("pytesseract not available, screenshot OCR disabled")
                self._ocr = False
        return self._ocr

    def verify_screenshot(
        self,
        screenshot_path: str,
        original_messages: List[Dict[str, Any]],
        screenshot_metadata: Optional[Dict[str, Any]] = None
    ) -> ScreenshotMatch:
        """Verify a screenshot against original messages."""

        # Extract text from screenshot
        screenshot_content = self._extract_text_from_screenshot(screenshot_path)

        if not screenshot_content:
            return ScreenshotMatch(
                match_id=hashlib.md5(screenshot_path.encode()).hexdigest()[:12],
                screenshot_path=screenshot_path,
                original_message_id=None,
                screenshot_content="[Could not extract text]",
                original_content=None,
                match_confidence=0.0,
                discrepancies_found=["Unable to extract text from screenshot"],
                timestamp_matches=False,
                sender_matches=False,
                content_matches=False,
                is_authentic=False,
                severity=SeverityLevel.HIGH
            )

        # Find best matching message
        best_match = None
        best_confidence = 0.0

        for msg in original_messages:
            content = str(msg.get("body", msg.get("content", "")))
            confidence = self._calculate_match_confidence(screenshot_content, content)

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = msg

        # Verify match
        if best_match and best_confidence > 0.7:
            discrepancies = self._find_discrepancies(
                screenshot_content,
                best_match,
                screenshot_metadata
            )

            return ScreenshotMatch(
                match_id=hashlib.md5(f"{screenshot_path}:{best_match.get('id', '')}".encode()).hexdigest()[:12],
                screenshot_path=screenshot_path,
                original_message_id=best_match.get("id", best_match.get("message_id")),
                screenshot_content=screenshot_content[:500],
                original_content=str(best_match.get("body", best_match.get("content", "")))[:500],
                match_confidence=best_confidence,
                discrepancies_found=discrepancies,
                timestamp_matches=len([d for d in discrepancies if "timestamp" in d.lower()]) == 0,
                sender_matches=len([d for d in discrepancies if "sender" in d.lower()]) == 0,
                content_matches=len([d for d in discrepancies if "content" in d.lower()]) == 0,
                is_authentic=len(discrepancies) == 0 and best_confidence > 0.9,
                severity=self._assess_screenshot_severity(discrepancies, best_confidence)
            )

        return ScreenshotMatch(
            match_id=hashlib.md5(screenshot_path.encode()).hexdigest()[:12],
            screenshot_path=screenshot_path,
            original_message_id=None,
            screenshot_content=screenshot_content[:500],
            original_content=None,
            match_confidence=best_confidence,
            discrepancies_found=["No matching original message found"],
            timestamp_matches=False,
            sender_matches=False,
            content_matches=False,
            is_authentic=False,
            severity=SeverityLevel.HIGH
        )

    def _extract_text_from_screenshot(self, screenshot_path: str) -> str:
        """Extract text from screenshot using OCR."""
        ocr = self._load_ocr()

        if not ocr:
            return ""

        try:
            from PIL import Image
            image = Image.open(screenshot_path)
            text = ocr.image_to_string(image, lang='eng+tur')
            return text.strip()
        except Exception as e:
            logger.error(f"OCR failed for {screenshot_path}: {e}")
            return ""

    def _calculate_match_confidence(self, screenshot_text: str, original_text: str) -> float:
        """Calculate confidence of match between screenshot and original."""
        if not screenshot_text or not original_text:
            return 0.0

        # Normalize texts
        screenshot_normalized = re.sub(r'\s+', ' ', screenshot_text.lower()).strip()
        original_normalized = re.sub(r'\s+', ' ', original_text.lower()).strip()

        # Calculate similarity
        return difflib.SequenceMatcher(None, screenshot_normalized, original_normalized).ratio()

    def _find_discrepancies(
        self,
        screenshot_content: str,
        original_message: Dict[str, Any],
        screenshot_metadata: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Find discrepancies between screenshot and original."""
        discrepancies = []

        original_content = str(original_message.get("body", original_message.get("content", "")))

        # Content comparison
        similarity = self._calculate_match_confidence(screenshot_content, original_content)
        if similarity < 0.95:
            discrepancies.append(f"Content similarity: {similarity:.1%} (expected >95%)")

        # Check for additions/deletions
        screenshot_words = set(screenshot_content.lower().split())
        original_words = set(original_content.lower().split())

        added_words = screenshot_words - original_words
        removed_words = original_words - screenshot_words

        if added_words:
            discrepancies.append(f"Words in screenshot not in original: {', '.join(list(added_words)[:5])}")

        if removed_words:
            discrepancies.append(f"Words in original not in screenshot: {', '.join(list(removed_words)[:5])}")

        return discrepancies

    def _assess_screenshot_severity(self, discrepancies: List[str], confidence: float) -> SeverityLevel:
        """Assess severity of screenshot verification result."""
        if len(discrepancies) == 0 and confidence > 0.95:
            return SeverityLevel.LOW  # Authentic
        elif confidence < 0.5 or len(discrepancies) > 3:
            return SeverityLevel.CRITICAL  # Likely fake
        elif confidence < 0.8 or len(discrepancies) > 1:
            return SeverityLevel.HIGH  # Suspicious
        else:
            return SeverityLevel.MEDIUM  # Minor discrepancies


class DiscrepancyDetector:
    """Main discrepancy detection engine."""

    def __init__(self):
        self.deleted_finder = DeletedMessageFinder()
        self.edit_comparer = EditHistoryComparer()
        self.gap_analyzer = TimeGapAnalyzer()
        self.screenshot_verifier = ScreenshotVerifier()

    def detect_all_discrepancies(
        self,
        messages_a: List[Dict[str, Any]],
        messages_b: List[Dict[str, Any]],
        device_a_id: str,
        device_b_id: str,
        screenshots: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Detect all types of discrepancies between devices."""

        # Find deleted messages
        deleted = self.deleted_finder.find_deleted_messages(
            messages_a, messages_b, device_a_id, device_b_id
        )

        # Find edited messages
        edits = self.edit_comparer.compare_edit_history(messages_a, messages_b)

        # Analyze time gaps
        gaps_a = self.gap_analyzer.analyze_gaps(messages_a, device_a_id)
        gaps_b = self.gap_analyzer.analyze_gaps(messages_b, device_b_id)

        # Verify screenshots if provided
        screenshot_results = []
        if screenshots:
            all_messages = messages_a + messages_b
            for screenshot_path in screenshots:
                result = self.screenshot_verifier.verify_screenshot(
                    screenshot_path, all_messages
                )
                screenshot_results.append(result)

        # Calculate summary
        total_discrepancies = len(deleted) + len(edits) + len(gaps_a) + len(gaps_b)
        high_severity = (
            sum(1 for d in deleted if d.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]) +
            sum(1 for e in edits if e.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]) +
            sum(1 for s in screenshot_results if not s.is_authentic)
        )

        return {
            "deleted_messages": {
                "count": len(deleted),
                "missing_on_a": sum(1 for d in deleted if d.missing_from_device == "device_a"),
                "missing_on_b": sum(1 for d in deleted if d.missing_from_device == "device_b"),
                "high_severity": sum(1 for d in deleted if d.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]),
                "details": [
                    {
                        "message_id": d.message_id,
                        "exists_on": d.exists_on_device,
                        "missing_from": d.missing_from_device,
                        "sender": d.sender,
                        "recipient": d.recipient,
                        "timestamp": d.timestamp.isoformat() if d.timestamp else None,
                        "content_preview": d.content_preview,
                        "type": d.message_type,
                        "severity": d.severity.value,
                        "reasons": d.possible_reasons
                    } for d in deleted
                ]
            },
            "edited_messages": {
                "count": len(edits),
                "details": [
                    {
                        "message_id": e.message_id,
                        "thread_id": e.thread_id,
                        "edit_type": e.edit_type,
                        "device_a_version": e.device_a_version,
                        "device_b_version": e.device_b_version,
                        "change_summary": e.change_summary,
                        "severity": e.severity.value
                    } for e in edits
                ]
            },
            "time_gaps": {
                "device_a": {
                    "count": len(gaps_a),
                    "total_hours": sum(g.duration_hours for g in gaps_a),
                    "details": [
                        {
                            "gap_id": g.gap_id,
                            "start": g.start_time.isoformat(),
                            "end": g.end_time.isoformat(),
                            "duration_hours": round(g.duration_hours, 1),
                            "expected_activity": g.expected_activity,
                            "severity": g.severity.value,
                            "explanations": g.possible_explanations
                        } for g in gaps_a
                    ]
                },
                "device_b": {
                    "count": len(gaps_b),
                    "total_hours": sum(g.duration_hours for g in gaps_b),
                    "details": [
                        {
                            "gap_id": g.gap_id,
                            "start": g.start_time.isoformat(),
                            "end": g.end_time.isoformat(),
                            "duration_hours": round(g.duration_hours, 1),
                            "expected_activity": g.expected_activity,
                            "severity": g.severity.value,
                            "explanations": g.possible_explanations
                        } for g in gaps_b
                    ]
                }
            },
            "screenshot_verification": {
                "total": len(screenshot_results),
                "authentic": sum(1 for s in screenshot_results if s.is_authentic),
                "suspicious": sum(1 for s in screenshot_results if not s.is_authentic),
                "details": [
                    {
                        "match_id": s.match_id,
                        "screenshot_path": s.screenshot_path,
                        "is_authentic": s.is_authentic,
                        "confidence": round(s.match_confidence, 2),
                        "discrepancies": s.discrepancies_found,
                        "severity": s.severity.value
                    } for s in screenshot_results
                ]
            },
            "summary": {
                "total_discrepancies": total_discrepancies,
                "high_severity_count": high_severity,
                "requires_investigation": high_severity > 0 or total_discrepancies > 20,
                "risk_level": "HIGH" if high_severity > 5 else "MEDIUM" if high_severity > 0 else "LOW"
            }
        }
