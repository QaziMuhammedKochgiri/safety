"""
Digest Generator
Generates weekly summary digests of collected evidence.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime, timedelta
import statistics


class DigestFormat(str, Enum):
    """Output formats for digests."""
    HTML = "html"
    TEXT = "text"
    JSON = "json"
    EMAIL = "email"


@dataclass
class DigestSection:
    """A section of the digest."""
    section_id: str
    title: str
    content: str
    priority: int = 5  # 1-10
    has_alerts: bool = False
    items: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class WeeklyDigest:
    """Weekly summary digest."""
    digest_id: str
    case_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime

    # Summary stats
    total_items_collected: int
    new_items: int
    changes_detected: int
    alerts_triggered: int

    # Sections
    sections: List[DigestSection]

    # Key findings
    key_findings: List[str]
    risk_summary: str
    trend_analysis: str

    # Action items
    action_items: List[str]
    urgent_items: List[str]


class DigestGenerator:
    """Generates weekly digest reports."""

    def __init__(self):
        pass

    def generate_digest(
        self,
        case_id: str,
        collection_results: List[Dict[str, Any]],
        changes: List[Dict[str, Any]],
        alerts: List[Dict[str, Any]],
        risk_data: Optional[Dict[str, Any]] = None,
        period_days: int = 7
    ) -> WeeklyDigest:
        """Generate a weekly digest."""
        digest_id = f"digest_{case_id}_{datetime.utcnow().strftime('%Y%m%d')}"
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=period_days)

        # Calculate statistics
        total_items = sum(r.get("items_collected", 0) for r in collection_results)
        new_items = sum(r.get("new_items", 0) for r in collection_results)
        changes_detected = len(changes)
        alerts_triggered = len(alerts)

        # Generate sections
        sections = self._generate_sections(
            collection_results, changes, alerts, risk_data
        )

        # Generate key findings
        key_findings = self._extract_key_findings(
            collection_results, changes, alerts, risk_data
        )

        # Generate risk summary
        risk_summary = self._generate_risk_summary(risk_data, alerts)

        # Generate trend analysis
        trend_analysis = self._generate_trend_analysis(collection_results, changes)

        # Generate action items
        action_items, urgent_items = self._generate_action_items(
            alerts, changes, risk_data
        )

        return WeeklyDigest(
            digest_id=digest_id,
            case_id=case_id,
            generated_at=datetime.utcnow(),
            period_start=period_start,
            period_end=period_end,
            total_items_collected=total_items,
            new_items=new_items,
            changes_detected=changes_detected,
            alerts_triggered=alerts_triggered,
            sections=sections,
            key_findings=key_findings,
            risk_summary=risk_summary,
            trend_analysis=trend_analysis,
            action_items=action_items,
            urgent_items=urgent_items
        )

    def _generate_sections(
        self,
        results: List[Dict[str, Any]],
        changes: List[Dict[str, Any]],
        alerts: List[Dict[str, Any]],
        risk_data: Optional[Dict[str, Any]]
    ) -> List[DigestSection]:
        """Generate digest sections."""
        sections = []

        # Collection summary section
        if results:
            section = DigestSection(
                section_id="collection_summary",
                title="Collection Summary",
                content=self._format_collection_summary(results),
                priority=3,
                items=[
                    {"source": r.get("source"), "count": r.get("items_collected")}
                    for r in results
                ]
            )
            sections.append(section)

        # Alerts section (highest priority if any)
        if alerts:
            critical_alerts = [a for a in alerts if a.get("priority") == "critical"]
            section = DigestSection(
                section_id="alerts",
                title="Alerts & Warnings",
                content=self._format_alerts_summary(alerts),
                priority=1 if critical_alerts else 2,
                has_alerts=True,
                items=alerts
            )
            sections.append(section)

        # Changes section
        if changes:
            suspicious = [c for c in changes if c.get("is_suspicious")]
            section = DigestSection(
                section_id="changes",
                title="Detected Changes",
                content=self._format_changes_summary(changes),
                priority=2 if suspicious else 4,
                has_alerts=bool(suspicious),
                items=changes[:10]  # Top 10 changes
            )
            sections.append(section)

        # Risk assessment section
        if risk_data:
            section = DigestSection(
                section_id="risk",
                title="Risk Assessment",
                content=self._format_risk_summary(risk_data),
                priority=risk_data.get("risk_level_priority", 5)
            )
            sections.append(section)

        # Sort by priority
        sections.sort(key=lambda s: s.priority)

        return sections

    def _format_collection_summary(self, results: List[Dict[str, Any]]) -> str:
        """Format collection summary content."""
        total = sum(r.get("items_collected", 0) for r in results)
        new = sum(r.get("new_items", 0) for r in results)

        lines = [
            f"Total items collected: {total}",
            f"New items since last period: {new}",
            "",
            "By source:"
        ]

        sources = {}
        for r in results:
            source = r.get("source", "unknown")
            count = r.get("items_collected", 0)
            sources[source] = sources.get(source, 0) + count

        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  - {source}: {count} items")

        return "\n".join(lines)

    def _format_alerts_summary(self, alerts: List[Dict[str, Any]]) -> str:
        """Format alerts summary."""
        by_priority = {}
        for alert in alerts:
            priority = alert.get("priority", "medium")
            by_priority[priority] = by_priority.get(priority, 0) + 1

        lines = [f"Total alerts: {len(alerts)}", ""]

        if "critical" in by_priority:
            lines.append(f"  CRITICAL: {by_priority['critical']} alert(s) require immediate attention")
        if "high" in by_priority:
            lines.append(f"  HIGH: {by_priority['high']} alert(s)")
        if "medium" in by_priority:
            lines.append(f"  MEDIUM: {by_priority['medium']} alert(s)")

        # List critical alerts
        critical = [a for a in alerts if a.get("priority") == "critical"]
        if critical:
            lines.extend(["", "Critical alerts:"])
            for alert in critical[:5]:
                lines.append(f"  ! {alert.get('title', 'Alert')}: {alert.get('message', '')[:100]}")

        return "\n".join(lines)

    def _format_changes_summary(self, changes: List[Dict[str, Any]]) -> str:
        """Format changes summary."""
        by_type = {}
        for change in changes:
            change_type = change.get("change_type", "unknown")
            by_type[change_type] = by_type.get(change_type, 0) + 1

        lines = [f"Total changes detected: {len(changes)}", ""]

        for change_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  - {change_type}: {count}")

        suspicious = [c for c in changes if c.get("is_suspicious")]
        if suspicious:
            lines.extend(["", f"WARNING: {len(suspicious)} suspicious change(s) detected"])
            for change in suspicious[:3]:
                reason = change.get("suspicion_reason", "Unknown reason")
                lines.append(f"  ! {reason}")

        return "\n".join(lines)

    def _format_risk_summary(self, risk_data: Dict[str, Any]) -> str:
        """Format risk assessment summary."""
        lines = [
            f"Overall Risk Score: {risk_data.get('overall_score', 'N/A')}/10",
            f"Risk Level: {risk_data.get('risk_level', 'Unknown').upper()}",
            f"Trajectory: {risk_data.get('trajectory', 'Unknown')}",
            ""
        ]

        top_factors = risk_data.get("top_risk_factors", [])
        if top_factors:
            lines.append("Top Risk Factors:")
            for factor in top_factors[:5]:
                lines.append(f"  - {factor}")

        return "\n".join(lines)

    def _extract_key_findings(
        self,
        results: List[Dict[str, Any]],
        changes: List[Dict[str, Any]],
        alerts: List[Dict[str, Any]],
        risk_data: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Extract key findings for the period."""
        findings = []

        # Alert-based findings
        critical_alerts = [a for a in alerts if a.get("priority") == "critical"]
        if critical_alerts:
            findings.append(f"{len(critical_alerts)} critical alert(s) were triggered")

        # Change-based findings
        suspicious = [c for c in changes if c.get("is_suspicious")]
        if suspicious:
            findings.append(f"{len(suspicious)} suspicious change(s) detected in evidence")

        deletions = [c for c in changes if c.get("change_type") == "deleted"]
        if deletions:
            findings.append(f"{len(deletions)} item(s) were deleted during this period")

        # Risk-based findings
        if risk_data:
            if risk_data.get("trajectory") == "worsening":
                findings.append("Risk level is trending upward")
            elif risk_data.get("trajectory") == "improving":
                findings.append("Risk level shows improvement")

            score = risk_data.get("overall_score", 0)
            if score >= 8:
                findings.append("Risk assessment indicates critical level")

        # Collection-based findings
        new_items = sum(r.get("new_items", 0) for r in results)
        if new_items > 100:
            findings.append(f"High volume of new evidence ({new_items} items)")

        return findings

    def _generate_risk_summary(
        self,
        risk_data: Optional[Dict[str, Any]],
        alerts: List[Dict[str, Any]]
    ) -> str:
        """Generate risk summary text."""
        if not risk_data:
            if alerts:
                critical = len([a for a in alerts if a.get("priority") == "critical"])
                if critical:
                    return f"No formal risk assessment, but {critical} critical alert(s) require attention."
            return "No risk data available for this period."

        score = risk_data.get("overall_score", 0)
        level = risk_data.get("risk_level", "unknown")
        trajectory = risk_data.get("trajectory", "unknown")

        if score >= 8:
            return f"CRITICAL: Risk score is {score}/10 ({level}). Immediate intervention may be needed. Trend: {trajectory}."
        elif score >= 6:
            return f"HIGH: Risk score is {score}/10 ({level}). Close monitoring required. Trend: {trajectory}."
        elif score >= 4:
            return f"MODERATE: Risk score is {score}/10 ({level}). Continue monitoring. Trend: {trajectory}."
        else:
            return f"LOW: Risk score is {score}/10 ({level}). Situation appears stable. Trend: {trajectory}."

    def _generate_trend_analysis(
        self,
        results: List[Dict[str, Any]],
        changes: List[Dict[str, Any]]
    ) -> str:
        """Generate trend analysis."""
        if not results:
            return "Insufficient data for trend analysis."

        total_items = sum(r.get("items_collected", 0) for r in results)
        new_items = sum(r.get("new_items", 0) for r in results)

        lines = []

        # Collection trend
        new_rate = new_items / max(1, total_items)
        if new_rate > 0.5:
            lines.append("High rate of new evidence being generated.")
        elif new_rate < 0.1:
            lines.append("Low rate of new evidence - may indicate reduced communication.")

        # Changes trend
        suspicious = len([c for c in changes if c.get("is_suspicious")])
        if suspicious > 10:
            lines.append(f"Elevated suspicious activity ({suspicious} incidents).")
        elif suspicious > 0:
            lines.append(f"Some suspicious activity detected ({suspicious} incidents).")

        deletions = len([c for c in changes if c.get("change_type") == "deleted"])
        if deletions > 5:
            lines.append(f"Notable deletion activity ({deletions} items).")

        if not lines:
            lines.append("Activity levels appear normal for this period.")

        return " ".join(lines)

    def _generate_action_items(
        self,
        alerts: List[Dict[str, Any]],
        changes: List[Dict[str, Any]],
        risk_data: Optional[Dict[str, Any]]
    ) -> tuple:
        """Generate action items and urgent items."""
        action_items = []
        urgent_items = []

        # From alerts
        critical_alerts = [a for a in alerts if a.get("priority") == "critical"]
        for alert in critical_alerts:
            urgent_items.append(f"Address alert: {alert.get('title')}")

        unacknowledged = [a for a in alerts if a.get("status") == "pending"]
        if unacknowledged:
            action_items.append(f"Review {len(unacknowledged)} unacknowledged alert(s)")

        # From changes
        suspicious = [c for c in changes if c.get("is_suspicious")]
        if suspicious:
            if len(suspicious) >= 5:
                urgent_items.append("Investigate mass suspicious changes")
            else:
                action_items.append(f"Review {len(suspicious)} suspicious change(s)")

        # From risk data
        if risk_data:
            score = risk_data.get("overall_score", 0)
            if score >= 8:
                urgent_items.append("Schedule immediate case review")
            elif score >= 6:
                action_items.append("Consider intervention planning")

            if risk_data.get("trajectory") == "worsening":
                action_items.append("Monitor risk trajectory closely")

        # Default items
        if not action_items and not urgent_items:
            action_items.append("Continue routine monitoring")

        return action_items, urgent_items

    def format_digest(
        self,
        digest: WeeklyDigest,
        format: DigestFormat = DigestFormat.HTML
    ) -> str:
        """Format digest for output."""
        if format == DigestFormat.HTML:
            return self._format_html(digest)
        elif format == DigestFormat.TEXT:
            return self._format_text(digest)
        elif format == DigestFormat.EMAIL:
            return self._format_email(digest)
        else:
            return self._format_json(digest)

    def _format_text(self, digest: WeeklyDigest) -> str:
        """Format as plain text."""
        lines = [
            "=" * 60,
            f"WEEKLY DIGEST - Case {digest.case_id}",
            f"Period: {digest.period_start.strftime('%Y-%m-%d')} to {digest.period_end.strftime('%Y-%m-%d')}",
            "=" * 60,
            "",
            "SUMMARY",
            "-" * 30,
            f"Items collected: {digest.total_items_collected}",
            f"New items: {digest.new_items}",
            f"Changes detected: {digest.changes_detected}",
            f"Alerts triggered: {digest.alerts_triggered}",
            "",
        ]

        if digest.urgent_items:
            lines.extend([
                "URGENT ITEMS",
                "-" * 30
            ])
            for item in digest.urgent_items:
                lines.append(f"  ! {item}")
            lines.append("")

        lines.extend([
            "RISK ASSESSMENT",
            "-" * 30,
            digest.risk_summary,
            "",
            "TREND ANALYSIS",
            "-" * 30,
            digest.trend_analysis,
            ""
        ])

        if digest.key_findings:
            lines.extend([
                "KEY FINDINGS",
                "-" * 30
            ])
            for finding in digest.key_findings:
                lines.append(f"  * {finding}")
            lines.append("")

        for section in digest.sections:
            lines.extend([
                section.title.upper(),
                "-" * 30,
                section.content,
                ""
            ])

        if digest.action_items:
            lines.extend([
                "ACTION ITEMS",
                "-" * 30
            ])
            for item in digest.action_items:
                lines.append(f"  [ ] {item}")

        return "\n".join(lines)

    def _format_html(self, digest: WeeklyDigest) -> str:
        """Format as HTML."""
        sections_html = ""
        for section in digest.sections:
            alert_badge = '<span class="badge-alert">!</span>' if section.has_alerts else ''
            sections_html += f"""
            <div class="section">
                <h3>{alert_badge}{section.title}</h3>
                <pre>{section.content}</pre>
            </div>
            """

        urgent_html = ""
        if digest.urgent_items:
            items = "".join(f"<li class='urgent'>{i}</li>" for i in digest.urgent_items)
            urgent_html = f"<div class='urgent-section'><h3>URGENT</h3><ul>{items}</ul></div>"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; }}
                .summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 20px 0; }}
                .stat {{ background: #ecf0f1; padding: 15px; text-align: center; }}
                .stat .value {{ font-size: 24px; font-weight: bold; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
                .urgent-section {{ background: #e74c3c; color: white; padding: 15px; }}
                .badge-alert {{ background: #e74c3c; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; }}
                .urgent {{ font-weight: bold; }}
                pre {{ white-space: pre-wrap; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Weekly Digest</h1>
                <p>Case: {digest.case_id}</p>
                <p>Period: {digest.period_start.strftime('%Y-%m-%d')} to {digest.period_end.strftime('%Y-%m-%d')}</p>
            </div>

            {urgent_html}

            <div class="summary">
                <div class="stat"><div class="value">{digest.total_items_collected}</div><div>Items Collected</div></div>
                <div class="stat"><div class="value">{digest.new_items}</div><div>New Items</div></div>
                <div class="stat"><div class="value">{digest.changes_detected}</div><div>Changes</div></div>
                <div class="stat"><div class="value">{digest.alerts_triggered}</div><div>Alerts</div></div>
            </div>

            <div class="section">
                <h3>Risk Summary</h3>
                <p>{digest.risk_summary}</p>
            </div>

            <div class="section">
                <h3>Trend Analysis</h3>
                <p>{digest.trend_analysis}</p>
            </div>

            {sections_html}
        </body>
        </html>
        """

    def _format_email(self, digest: WeeklyDigest) -> str:
        """Format for email delivery."""
        # Use HTML format but with email-safe styling
        return self._format_html(digest)

    def _format_json(self, digest: WeeklyDigest) -> str:
        """Format as JSON."""
        import json
        return json.dumps({
            "digest_id": digest.digest_id,
            "case_id": digest.case_id,
            "generated_at": digest.generated_at.isoformat(),
            "period_start": digest.period_start.isoformat(),
            "period_end": digest.period_end.isoformat(),
            "statistics": {
                "total_items": digest.total_items_collected,
                "new_items": digest.new_items,
                "changes": digest.changes_detected,
                "alerts": digest.alerts_triggered
            },
            "risk_summary": digest.risk_summary,
            "trend_analysis": digest.trend_analysis,
            "key_findings": digest.key_findings,
            "urgent_items": digest.urgent_items,
            "action_items": digest.action_items,
            "sections": [
                {
                    "title": s.title,
                    "content": s.content,
                    "has_alerts": s.has_alerts
                }
                for s in digest.sections
            ]
        }, indent=2)
