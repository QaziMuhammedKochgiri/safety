"""
Visualization for Multi-Device Comparison
Side-by-side timeline, diff view, and conflict highlighting.
"""

import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class VisualizationFormat(Enum):
    """Output formats for visualizations."""
    HTML = "html"
    JSON = "json"
    SVG = "svg"
    TEXT = "text"


class EventType(Enum):
    """Types of timeline events."""
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    CALL_OUTGOING = "call_outgoing"
    CALL_INCOMING = "call_incoming"
    CALL_MISSED = "call_missed"
    MEDIA_SHARED = "media_shared"
    LOCATION_SHARED = "location_shared"
    STATUS_UPDATE = "status_update"
    DELETED = "deleted"
    GAP = "gap"


class ConflictType(Enum):
    """Types of conflicts between devices."""
    MISSING_ON_A = "missing_on_a"
    MISSING_ON_B = "missing_on_b"
    CONTENT_MISMATCH = "content_mismatch"
    TIMESTAMP_MISMATCH = "timestamp_mismatch"
    SENDER_MISMATCH = "sender_mismatch"


@dataclass
class TimelineEvent:
    """Single event in timeline."""
    event_id: str
    timestamp: datetime
    event_type: EventType
    source_device: str  # device_a, device_b, or both
    content: str
    participants: List[str]
    has_conflict: bool = False
    conflict_type: Optional[ConflictType] = None
    conflict_details: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TimelineView:
    """Complete timeline view."""
    view_id: str
    device_a_name: str
    device_b_name: str
    start_time: datetime
    end_time: datetime
    events: List[TimelineEvent]
    total_conflicts: int
    total_gaps: int
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DiffLine:
    """Single line in diff view."""
    line_number: int
    device_a_content: Optional[str]
    device_b_content: Optional[str]
    status: str  # same, added, removed, modified
    highlight_positions: List[Tuple[int, int]] = field(default_factory=list)


@dataclass
class DiffView:
    """Diff view for conversation comparison."""
    diff_id: str
    thread_id: str
    participants: List[str]
    lines: List[DiffLine]
    total_same: int
    total_added: int
    total_removed: int
    total_modified: int
    similarity_score: float


@dataclass
class ConflictReport:
    """Report of all conflicts found."""
    report_id: str
    generated_at: datetime
    device_a_id: str
    device_b_id: str
    conflicts: List[Dict[str, Any]]
    severity_summary: Dict[str, int]
    recommendations: List[str]


class TimelineRenderer:
    """Render side-by-side timeline view."""

    def __init__(self):
        self.colors = {
            "device_a": "#3B82F6",  # Blue
            "device_b": "#10B981",  # Green
            "conflict": "#EF4444",  # Red
            "gap": "#F59E0B",       # Amber
            "both": "#8B5CF6"       # Purple
        }

    def render_timeline(
        self,
        events_a: List[Dict[str, Any]],
        events_b: List[Dict[str, Any]],
        device_a_name: str,
        device_b_name: str,
        format: VisualizationFormat = VisualizationFormat.HTML
    ) -> Tuple[TimelineView, str]:
        """Render side-by-side timeline."""

        # Merge and analyze events
        merged_events = self._merge_events(events_a, events_b)

        # Find time range
        all_timestamps = [e.timestamp for e in merged_events if e.timestamp]
        start_time = min(all_timestamps) if all_timestamps else datetime.utcnow()
        end_time = max(all_timestamps) if all_timestamps else datetime.utcnow()

        # Count conflicts and gaps
        total_conflicts = sum(1 for e in merged_events if e.has_conflict)
        total_gaps = sum(1 for e in merged_events if e.event_type == EventType.GAP)

        view = TimelineView(
            view_id=hashlib.md5(f"{device_a_name}:{device_b_name}:{datetime.utcnow()}".encode()).hexdigest()[:12],
            device_a_name=device_a_name,
            device_b_name=device_b_name,
            start_time=start_time,
            end_time=end_time,
            events=merged_events,
            total_conflicts=total_conflicts,
            total_gaps=total_gaps
        )

        # Render to format
        if format == VisualizationFormat.HTML:
            output = self._render_html(view)
        elif format == VisualizationFormat.JSON:
            output = self._render_json(view)
        elif format == VisualizationFormat.TEXT:
            output = self._render_text(view)
        else:
            output = self._render_json(view)

        return view, output

    def _merge_events(
        self,
        events_a: List[Dict[str, Any]],
        events_b: List[Dict[str, Any]]
    ) -> List[TimelineEvent]:
        """Merge events from both devices."""
        merged = []

        # Create fingerprint indices
        fingerprints_a = {}
        for event in events_a:
            fp = self._event_fingerprint(event)
            fingerprints_a[fp] = event

        fingerprints_b = {}
        for event in events_b:
            fp = self._event_fingerprint(event)
            fingerprints_b[fp] = event

        # Find common events
        common_fps = set(fingerprints_a.keys()) & set(fingerprints_b.keys())
        only_a_fps = set(fingerprints_a.keys()) - common_fps
        only_b_fps = set(fingerprints_b.keys()) - common_fps

        # Add common events
        for fp in common_fps:
            event = fingerprints_a[fp]
            timeline_event = self._create_timeline_event(event, "both")
            merged.append(timeline_event)

        # Add device A only events (missing on B = conflict)
        for fp in only_a_fps:
            event = fingerprints_a[fp]
            timeline_event = self._create_timeline_event(
                event, "device_a",
                has_conflict=True,
                conflict_type=ConflictType.MISSING_ON_B,
                conflict_details="Message exists on Device A but not on Device B"
            )
            merged.append(timeline_event)

        # Add device B only events (missing on A = conflict)
        for fp in only_b_fps:
            event = fingerprints_b[fp]
            timeline_event = self._create_timeline_event(
                event, "device_b",
                has_conflict=True,
                conflict_type=ConflictType.MISSING_ON_A,
                conflict_details="Message exists on Device B but not on Device A"
            )
            merged.append(timeline_event)

        # Sort by timestamp
        merged.sort(key=lambda e: e.timestamp or datetime.min)

        return merged

    def _event_fingerprint(self, event: Dict[str, Any]) -> str:
        """Create fingerprint for event matching."""
        ts = event.get("timestamp")
        if isinstance(ts, datetime):
            ts_str = ts.strftime("%Y-%m-%d %H:%M")
        else:
            ts_str = str(ts)[:16] if ts else ""

        content = str(event.get("body", event.get("content", "")))[:50].lower()
        sender = str(event.get("sender", ""))[-10:]

        return hashlib.md5(f"{ts_str}:{sender}:{content}".encode()).hexdigest()

    def _create_timeline_event(
        self,
        event: Dict[str, Any],
        source: str,
        has_conflict: bool = False,
        conflict_type: Optional[ConflictType] = None,
        conflict_details: Optional[str] = None
    ) -> TimelineEvent:
        """Create TimelineEvent from raw event."""

        # Determine event type
        event_type = EventType.MESSAGE_RECEIVED
        if event.get("type") == "call":
            direction = event.get("direction", event.get("call_type", ""))
            if "outgoing" in direction.lower():
                event_type = EventType.CALL_OUTGOING
            elif "missed" in direction.lower():
                event_type = EventType.CALL_MISSED
            else:
                event_type = EventType.CALL_INCOMING
        elif event.get("direction") == "outgoing" or event.get("is_outgoing"):
            event_type = EventType.MESSAGE_SENT
        elif event.get("has_media") or event.get("media_type"):
            event_type = EventType.MEDIA_SHARED

        # Get timestamp
        ts = event.get("timestamp")
        if not isinstance(ts, datetime):
            ts = datetime.utcnow()

        # Get participants
        participants = []
        if event.get("sender"):
            participants.append(event["sender"])
        if event.get("recipient"):
            participants.append(event["recipient"])

        return TimelineEvent(
            event_id=hashlib.md5(self._event_fingerprint(event).encode()).hexdigest()[:12],
            timestamp=ts,
            event_type=event_type,
            source_device=source,
            content=str(event.get("body", event.get("content", "")))[:200],
            participants=participants,
            has_conflict=has_conflict,
            conflict_type=conflict_type,
            conflict_details=conflict_details,
            metadata={
                "source_app": event.get("source", event.get("app", "Unknown")),
                "message_type": event.get("message_type", "text")
            }
        )

    def _render_html(self, view: TimelineView) -> str:
        """Render timeline as HTML."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Timeline Comparison: {view.device_a_name} vs {view.device_b_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .timeline-container {{ display: flex; gap: 20px; }}
                .device-column {{ flex: 1; border: 1px solid #e0e0e0; padding: 15px; }}
                .device-a {{ border-left: 4px solid {self.colors['device_a']}; }}
                .device-b {{ border-left: 4px solid {self.colors['device_b']}; }}
                .event {{ padding: 10px; margin: 5px 0; border-radius: 5px; }}
                .event-both {{ background: #f0f0f0; }}
                .event-conflict {{ background: #fee2e2; border-left: 3px solid {self.colors['conflict']}; }}
                .event-gap {{ background: #fef3c7; border-left: 3px solid {self.colors['gap']}; }}
                .timestamp {{ font-size: 0.8em; color: #666; }}
                .content {{ margin-top: 5px; }}
                .conflict-badge {{ background: {self.colors['conflict']}; color: white; padding: 2px 8px;
                                   border-radius: 10px; font-size: 0.75em; }}
                .summary {{ background: #f8f9fa; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
                .stat {{ display: inline-block; margin-right: 20px; }}
                .stat-value {{ font-size: 1.5em; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Timeline Comparison</h1>
                <p>{view.device_a_name} vs {view.device_b_name}</p>
                <p>Period: {view.start_time.strftime('%Y-%m-%d %H:%M')} to {view.end_time.strftime('%Y-%m-%d %H:%M')}</p>
            </div>

            <div class="summary">
                <div class="stat">
                    <div class="stat-value">{len(view.events)}</div>
                    <div>Total Events</div>
                </div>
                <div class="stat">
                    <div class="stat-value" style="color: {self.colors['conflict']}">{view.total_conflicts}</div>
                    <div>Conflicts</div>
                </div>
                <div class="stat">
                    <div class="stat-value" style="color: {self.colors['gap']}">{view.total_gaps}</div>
                    <div>Gaps</div>
                </div>
            </div>

            <div class="timeline-container">
                <div class="device-column device-a">
                    <h3>{view.device_a_name}</h3>
        """

        # Add events for device A
        for event in view.events:
            if event.source_device in ["device_a", "both"]:
                event_class = "event-conflict" if event.has_conflict else "event-both"
                conflict_badge = f'<span class="conflict-badge">{event.conflict_type.value if event.conflict_type else "CONFLICT"}</span>' if event.has_conflict else ""

                html += f"""
                    <div class="event {event_class}">
                        <div class="timestamp">{event.timestamp.strftime('%H:%M:%S')} {conflict_badge}</div>
                        <div class="content">{event.content[:100]}...</div>
                    </div>
                """

        html += """
                </div>
                <div class="device-column device-b">
                    <h3>""" + view.device_b_name + """</h3>
        """

        # Add events for device B
        for event in view.events:
            if event.source_device in ["device_b", "both"]:
                event_class = "event-conflict" if event.has_conflict else "event-both"
                conflict_badge = f'<span class="conflict-badge">{event.conflict_type.value if event.conflict_type else "CONFLICT"}</span>' if event.has_conflict else ""

                html += f"""
                    <div class="event {event_class}">
                        <div class="timestamp">{event.timestamp.strftime('%H:%M:%S')} {conflict_badge}</div>
                        <div class="content">{event.content[:100]}...</div>
                    </div>
                """

        html += """
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _render_json(self, view: TimelineView) -> str:
        """Render timeline as JSON."""
        return json.dumps({
            "view_id": view.view_id,
            "device_a": view.device_a_name,
            "device_b": view.device_b_name,
            "start_time": view.start_time.isoformat(),
            "end_time": view.end_time.isoformat(),
            "total_conflicts": view.total_conflicts,
            "total_gaps": view.total_gaps,
            "events": [
                {
                    "event_id": e.event_id,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                    "type": e.event_type.value,
                    "source": e.source_device,
                    "content": e.content,
                    "participants": e.participants,
                    "has_conflict": e.has_conflict,
                    "conflict_type": e.conflict_type.value if e.conflict_type else None,
                    "conflict_details": e.conflict_details
                }
                for e in view.events
            ]
        }, indent=2)

    def _render_text(self, view: TimelineView) -> str:
        """Render timeline as text."""
        lines = [
            f"Timeline Comparison: {view.device_a_name} vs {view.device_b_name}",
            f"Period: {view.start_time.strftime('%Y-%m-%d %H:%M')} to {view.end_time.strftime('%Y-%m-%d %H:%M')}",
            f"Total Events: {len(view.events)} | Conflicts: {view.total_conflicts} | Gaps: {view.total_gaps}",
            "=" * 80,
            ""
        ]

        for event in view.events:
            conflict_marker = "[CONFLICT]" if event.has_conflict else ""
            source_marker = f"[{event.source_device.upper()}]"
            lines.append(
                f"{event.timestamp.strftime('%Y-%m-%d %H:%M:%S')} {source_marker} {conflict_marker}"
            )
            lines.append(f"  {event.content[:100]}")
            if event.conflict_details:
                lines.append(f"  -> {event.conflict_details}")
            lines.append("")

        return "\n".join(lines)


class DiffRenderer:
    """Render diff view for conversation comparison."""

    def render_diff(
        self,
        messages_a: List[Dict[str, Any]],
        messages_b: List[Dict[str, Any]],
        thread_id: str,
        participants: List[str]
    ) -> DiffView:
        """Create diff view for a conversation thread."""

        # Sort messages by timestamp
        sorted_a = sorted(messages_a, key=lambda m: m.get("timestamp", datetime.min))
        sorted_b = sorted(messages_b, key=lambda m: m.get("timestamp", datetime.min))

        # Create content lists
        content_a = [str(m.get("body", m.get("content", ""))) for m in sorted_a]
        content_b = [str(m.get("body", m.get("content", ""))) for m in sorted_b]

        # Generate diff lines
        lines = []
        total_same = 0
        total_added = 0
        total_removed = 0
        total_modified = 0

        # Use sequence matcher for alignment
        import difflib
        matcher = difflib.SequenceMatcher(None, content_a, content_b)

        line_num = 1
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for i in range(i1, i2):
                    lines.append(DiffLine(
                        line_number=line_num,
                        device_a_content=content_a[i],
                        device_b_content=content_b[j1 + (i - i1)],
                        status="same"
                    ))
                    total_same += 1
                    line_num += 1

            elif tag == "delete":
                for i in range(i1, i2):
                    lines.append(DiffLine(
                        line_number=line_num,
                        device_a_content=content_a[i],
                        device_b_content=None,
                        status="removed"
                    ))
                    total_removed += 1
                    line_num += 1

            elif tag == "insert":
                for j in range(j1, j2):
                    lines.append(DiffLine(
                        line_number=line_num,
                        device_a_content=None,
                        device_b_content=content_b[j],
                        status="added"
                    ))
                    total_added += 1
                    line_num += 1

            elif tag == "replace":
                max_len = max(i2 - i1, j2 - j1)
                for k in range(max_len):
                    a_content = content_a[i1 + k] if i1 + k < i2 else None
                    b_content = content_b[j1 + k] if j1 + k < j2 else None

                    # Find changed positions
                    highlights = []
                    if a_content and b_content:
                        highlights = self._find_diff_positions(a_content, b_content)

                    lines.append(DiffLine(
                        line_number=line_num,
                        device_a_content=a_content,
                        device_b_content=b_content,
                        status="modified",
                        highlight_positions=highlights
                    ))
                    total_modified += 1
                    line_num += 1

        # Calculate similarity
        total = total_same + total_added + total_removed + total_modified
        similarity = total_same / total if total > 0 else 0.0

        return DiffView(
            diff_id=hashlib.md5(f"{thread_id}:{datetime.utcnow()}".encode()).hexdigest()[:12],
            thread_id=thread_id,
            participants=participants,
            lines=lines,
            total_same=total_same,
            total_added=total_added,
            total_removed=total_removed,
            total_modified=total_modified,
            similarity_score=similarity
        )

    def _find_diff_positions(self, text_a: str, text_b: str) -> List[Tuple[int, int]]:
        """Find positions of differences between two texts."""
        import difflib
        positions = []

        matcher = difflib.SequenceMatcher(None, text_a, text_b)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != "equal":
                positions.append((i1, i2))

        return positions

    def render_html(self, diff_view: DiffView) -> str:
        """Render diff as HTML."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Conversation Diff: {', '.join(diff_view.participants)}</title>
            <style>
                body {{ font-family: monospace; margin: 20px; }}
                .diff-container {{ display: flex; }}
                .diff-column {{ flex: 1; padding: 10px; }}
                .column-a {{ background: #fef2f2; }}
                .column-b {{ background: #f0fdf4; }}
                .line {{ padding: 5px; margin: 2px 0; border-radius: 3px; }}
                .same {{ background: white; }}
                .added {{ background: #dcfce7; }}
                .removed {{ background: #fee2e2; }}
                .modified {{ background: #fef9c3; }}
                .line-number {{ color: #999; width: 30px; display: inline-block; }}
                .highlight {{ background: #fbbf24; }}
                .summary {{ margin-bottom: 20px; padding: 15px; background: #f3f4f6; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>Conversation Diff</h1>
            <p>Thread: {diff_view.thread_id}</p>
            <p>Participants: {', '.join(diff_view.participants)}</p>

            <div class="summary">
                <strong>Similarity: {diff_view.similarity_score:.1%}</strong> |
                Same: {diff_view.total_same} |
                Added: {diff_view.total_added} |
                Removed: {diff_view.total_removed} |
                Modified: {diff_view.total_modified}
            </div>

            <div class="diff-container">
                <div class="diff-column column-a">
                    <h3>Device A</h3>
        """

        for line in diff_view.lines:
            content = line.device_a_content or "&nbsp;"
            if len(content) > 100:
                content = content[:100] + "..."
            html += f"""
                    <div class="line {line.status}">
                        <span class="line-number">{line.line_number}</span>
                        {content}
                    </div>
            """

        html += """
                </div>
                <div class="diff-column column-b">
                    <h3>Device B</h3>
        """

        for line in diff_view.lines:
            content = line.device_b_content or "&nbsp;"
            if len(content) > 100:
                content = content[:100] + "..."
            html += f"""
                    <div class="line {line.status}">
                        <span class="line-number">{line.line_number}</span>
                        {content}
                    </div>
            """

        html += """
                </div>
            </div>
        </body>
        </html>
        """

        return html


class ConflictHighlighter:
    """Highlight and report conflicts."""

    def generate_conflict_report(
        self,
        deleted_messages: List[Dict[str, Any]],
        edited_messages: List[Dict[str, Any]],
        time_gaps: List[Dict[str, Any]],
        screenshot_issues: List[Dict[str, Any]],
        device_a_id: str,
        device_b_id: str
    ) -> ConflictReport:
        """Generate comprehensive conflict report."""

        conflicts = []
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}

        # Process deleted messages
        for msg in deleted_messages:
            severity = msg.get("severity", "medium")
            severity_counts[severity] += 1

            conflicts.append({
                "type": "deleted_message",
                "severity": severity,
                "timestamp": msg.get("timestamp"),
                "description": f"Message missing on {msg.get('missing_from', 'device')}",
                "content_preview": msg.get("content_preview", "")[:100],
                "evidence": {
                    "exists_on": msg.get("exists_on_device"),
                    "missing_from": msg.get("missing_from_device"),
                    "possible_reasons": msg.get("reasons", [])
                }
            })

        # Process edited messages
        for edit in edited_messages:
            severity = edit.get("severity", "medium")
            severity_counts[severity] += 1

            conflicts.append({
                "type": "edited_message",
                "severity": severity,
                "description": f"Message content differs between devices ({edit.get('edit_type', 'unknown')})",
                "device_a_version": edit.get("device_a_version", "")[:100],
                "device_b_version": edit.get("device_b_version", "")[:100],
                "change_summary": edit.get("change_summary", "")
            })

        # Process time gaps
        for gap in time_gaps:
            severity = gap.get("severity", "low")
            severity_counts[severity] += 1

            conflicts.append({
                "type": "time_gap",
                "severity": severity,
                "start_time": gap.get("start"),
                "end_time": gap.get("end"),
                "duration_hours": gap.get("duration_hours"),
                "description": f"Unexplained gap of {gap.get('duration_hours', 0):.1f} hours",
                "explanations": gap.get("explanations", [])
            })

        # Process screenshot issues
        for screenshot in screenshot_issues:
            if not screenshot.get("is_authentic", True):
                severity = screenshot.get("severity", "high")
                severity_counts[severity] += 1

                conflicts.append({
                    "type": "screenshot_verification",
                    "severity": severity,
                    "is_authentic": False,
                    "confidence": screenshot.get("confidence", 0),
                    "discrepancies": screenshot.get("discrepancies", []),
                    "description": "Screenshot may not match original message"
                })

        # Generate recommendations
        recommendations = self._generate_recommendations(severity_counts, conflicts)

        return ConflictReport(
            report_id=hashlib.md5(f"{device_a_id}:{device_b_id}:{datetime.utcnow()}".encode()).hexdigest()[:12],
            generated_at=datetime.utcnow(),
            device_a_id=device_a_id,
            device_b_id=device_b_id,
            conflicts=conflicts,
            severity_summary=severity_counts,
            recommendations=recommendations
        )

    def _generate_recommendations(
        self,
        severity_counts: Dict[str, int],
        conflicts: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on conflicts."""
        recommendations = []

        # High severity recommendations
        if severity_counts.get("critical", 0) > 0:
            recommendations.append(
                "CRITICAL: Evidence of potential data tampering detected. "
                "Recommend immediate forensic review by certified examiner."
            )

        if severity_counts.get("high", 0) > 5:
            recommendations.append(
                "HIGH PRIORITY: Multiple high-severity discrepancies found. "
                "Consider obtaining additional device backups for verification."
            )

        # Specific conflict type recommendations
        deleted_count = sum(1 for c in conflicts if c["type"] == "deleted_message")
        if deleted_count > 10:
            recommendations.append(
                f"Found {deleted_count} potentially deleted messages. "
                "Request explanation from device owner or consider deleted data recovery."
            )

        screenshot_issues = [c for c in conflicts if c["type"] == "screenshot_verification"]
        if screenshot_issues:
            recommendations.append(
                "Screenshot verification issues detected. "
                "Original messages should be presented instead of screenshots."
            )

        # Gap recommendations
        large_gaps = [c for c in conflicts if c["type"] == "time_gap" and c.get("duration_hours", 0) > 24]
        if large_gaps:
            recommendations.append(
                f"Found {len(large_gaps)} gaps exceeding 24 hours. "
                "Investigate possible device resets or data deletions during these periods."
            )

        # General recommendations
        if not recommendations:
            recommendations.append(
                "No critical issues found. Continue standard evidence review process."
            )

        return recommendations


class ComparisonVisualizer:
    """Main visualization engine."""

    def __init__(self):
        self.timeline_renderer = TimelineRenderer()
        self.diff_renderer = DiffRenderer()
        self.conflict_highlighter = ConflictHighlighter()

    def create_full_visualization(
        self,
        comparison_result: Dict[str, Any],
        device_a_name: str,
        device_b_name: str,
        messages_a: List[Dict[str, Any]],
        messages_b: List[Dict[str, Any]],
        format: VisualizationFormat = VisualizationFormat.HTML
    ) -> Dict[str, Any]:
        """Create complete visualization package."""

        # Create timeline view
        timeline_view, timeline_output = self.timeline_renderer.render_timeline(
            messages_a, messages_b, device_a_name, device_b_name, format
        )

        # Create diff views for threads with discrepancies
        diff_views = []
        for thread in comparison_result.get("message_threads", {}).get("details", []):
            if thread.get("missing_on_a", 0) > 0 or thread.get("missing_on_b", 0) > 0:
                # Filter messages for this thread
                thread_participants = set(thread.get("participants", []))
                thread_msgs_a = [m for m in messages_a
                               if set([m.get("sender", ""), m.get("recipient", "")]) & thread_participants]
                thread_msgs_b = [m for m in messages_b
                               if set([m.get("sender", ""), m.get("recipient", "")]) & thread_participants]

                if thread_msgs_a or thread_msgs_b:
                    diff_view = self.diff_renderer.render_diff(
                        thread_msgs_a, thread_msgs_b,
                        thread.get("thread_id", ""),
                        thread.get("participants", [])
                    )
                    diff_views.append(diff_view)

        # Generate conflict report
        conflict_report = self.conflict_highlighter.generate_conflict_report(
            deleted_messages=comparison_result.get("deleted_messages", {}).get("details", []),
            edited_messages=comparison_result.get("edited_messages", {}).get("details", []),
            time_gaps=comparison_result.get("time_gaps", {}).get("device_a", {}).get("details", []) +
                     comparison_result.get("time_gaps", {}).get("device_b", {}).get("details", []),
            screenshot_issues=comparison_result.get("screenshot_verification", {}).get("details", []),
            device_a_id=device_a_name,
            device_b_id=device_b_name
        )

        return {
            "timeline": {
                "view_id": timeline_view.view_id,
                "total_events": len(timeline_view.events),
                "total_conflicts": timeline_view.total_conflicts,
                "output": timeline_output if format != VisualizationFormat.HTML else None,
                "html": timeline_output if format == VisualizationFormat.HTML else None
            },
            "diff_views": [
                {
                    "diff_id": dv.diff_id,
                    "thread_id": dv.thread_id,
                    "participants": dv.participants,
                    "similarity": dv.similarity_score,
                    "total_lines": len(dv.lines),
                    "same": dv.total_same,
                    "added": dv.total_added,
                    "removed": dv.total_removed,
                    "modified": dv.total_modified
                } for dv in diff_views
            ],
            "conflict_report": {
                "report_id": conflict_report.report_id,
                "total_conflicts": len(conflict_report.conflicts),
                "severity_summary": conflict_report.severity_summary,
                "recommendations": conflict_report.recommendations,
                "conflicts": conflict_report.conflicts
            }
        }
