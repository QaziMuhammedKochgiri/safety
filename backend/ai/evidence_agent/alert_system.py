"""
Alert System for Evidence Collection
Manages alerts for high-risk findings and pattern changes.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from enum import Enum
from datetime import datetime, timedelta
import asyncio


class AlertPriority(str, Enum):
    """Alert priority levels."""
    CRITICAL = "critical"  # Immediate attention required
    HIGH = "high"  # Same-day response needed
    MEDIUM = "medium"  # Within 48 hours
    LOW = "low"  # Informational
    INFO = "info"  # For logging only


class AlertType(str, Enum):
    """Types of alerts."""
    HIGH_RISK_MESSAGE = "high_risk_message"
    PATTERN_CHANGE = "pattern_change"
    MASS_DELETION = "mass_deletion"
    NEW_THREAT = "new_threat"
    COLLECTION_FAILED = "collection_failed"
    TIMELINE_GAP = "timeline_gap"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    ESCALATION_DETECTED = "escalation_detected"
    CHILD_SAFETY = "child_safety"
    ABDUCTION_RISK = "abduction_risk"


class AlertChannel(str, Enum):
    """Channels for alert delivery."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class AlertStatus(str, Enum):
    """Alert status."""
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    FAILED = "failed"


@dataclass
class Alert:
    """An alert notification."""
    alert_id: str
    case_id: str
    alert_type: AlertType
    priority: AlertPriority
    title: str
    message: str
    created_at: datetime
    evidence_ids: List[str] = field(default_factory=list)
    status: AlertStatus = AlertStatus.PENDING
    channels: List[AlertChannel] = field(default_factory=list)
    sent_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0


@dataclass
class AlertRule:
    """Rule for triggering alerts."""
    rule_id: str
    name: str
    description: str
    alert_type: AlertType
    priority: AlertPriority
    conditions: Dict[str, Any]
    channels: List[AlertChannel]
    enabled: bool = True
    cooldown_minutes: int = 60  # Prevent duplicate alerts


class AlertManager:
    """Manages alert creation, delivery, and tracking."""

    # Default alert rules
    DEFAULT_RULES = [
        {
            "rule_id": "rule_threat",
            "name": "Threat Detection",
            "description": "Alert on detected threats of violence",
            "alert_type": AlertType.NEW_THREAT,
            "priority": AlertPriority.CRITICAL,
            "conditions": {"keywords": ["kill", "hurt", "harm", "destroy"]},
            "channels": [AlertChannel.PUSH, AlertChannel.EMAIL]
        },
        {
            "rule_id": "rule_abduction",
            "name": "Abduction Risk",
            "description": "Alert on abduction-related keywords",
            "alert_type": AlertType.ABDUCTION_RISK,
            "priority": AlertPriority.CRITICAL,
            "conditions": {"keywords": ["take away", "won't see", "disappear", "passport", "flight"]},
            "channels": [AlertChannel.PUSH, AlertChannel.SMS, AlertChannel.EMAIL]
        },
        {
            "rule_id": "rule_deletion",
            "name": "Mass Deletion",
            "description": "Alert when many items deleted",
            "alert_type": AlertType.MASS_DELETION,
            "priority": AlertPriority.HIGH,
            "conditions": {"deletion_count": 5},
            "channels": [AlertChannel.PUSH, AlertChannel.EMAIL]
        },
        {
            "rule_id": "rule_escalation",
            "name": "Escalation Detection",
            "description": "Alert when hostility increases",
            "alert_type": AlertType.ESCALATION_DETECTED,
            "priority": AlertPriority.HIGH,
            "conditions": {"severity_increase": 2},
            "channels": [AlertChannel.PUSH, AlertChannel.EMAIL]
        },
        {
            "rule_id": "rule_child_safety",
            "name": "Child Safety Concern",
            "description": "Alert on child safety keywords",
            "alert_type": AlertType.CHILD_SAFETY,
            "priority": AlertPriority.CRITICAL,
            "conditions": {"keywords": ["abuse", "neglect", "unsafe", "scared", "help me"]},
            "channels": [AlertChannel.PUSH, AlertChannel.SMS, AlertChannel.EMAIL]
        }
    ]

    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.rules: Dict[str, AlertRule] = {}
        self.delivery_handlers: Dict[AlertChannel, Callable] = {}
        self.alert_history: Dict[str, List[str]] = {}  # case_id -> alert_ids
        self.cooldowns: Dict[str, datetime] = {}  # rule_id_case_id -> last_triggered

        # Initialize default rules
        for rule_data in self.DEFAULT_RULES:
            rule = AlertRule(**rule_data)
            self.rules[rule.rule_id] = rule

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default delivery handlers."""
        self.delivery_handlers = {
            AlertChannel.EMAIL: self._send_email,
            AlertChannel.SMS: self._send_sms,
            AlertChannel.PUSH: self._send_push,
            AlertChannel.IN_APP: self._send_in_app,
            AlertChannel.WEBHOOK: self._send_webhook
        }

    def create_alert(
        self,
        case_id: str,
        alert_type: AlertType,
        title: str,
        message: str,
        priority: AlertPriority = AlertPriority.MEDIUM,
        channels: Optional[List[AlertChannel]] = None,
        evidence_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create a new alert."""
        alert_id = f"alert_{case_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        alert = Alert(
            alert_id=alert_id,
            case_id=case_id,
            alert_type=alert_type,
            priority=priority,
            title=title,
            message=message,
            created_at=datetime.utcnow(),
            channels=channels or [AlertChannel.IN_APP],
            evidence_ids=evidence_ids or [],
            metadata=metadata or {}
        )

        self.alerts[alert_id] = alert

        # Track in history
        if case_id not in self.alert_history:
            self.alert_history[case_id] = []
        self.alert_history[case_id].append(alert_id)

        return alert

    async def send_alert(self, alert_id: str) -> bool:
        """Send an alert through configured channels."""
        alert = self.alerts.get(alert_id)
        if not alert:
            return False

        success = True
        for channel in alert.channels:
            handler = self.delivery_handlers.get(channel)
            if handler:
                try:
                    await handler(alert)
                except Exception as e:
                    success = False
                    alert.metadata["delivery_error"] = str(e)

        if success:
            alert.status = AlertStatus.SENT
            alert.sent_at = datetime.utcnow()
        else:
            alert.retry_count += 1
            if alert.retry_count >= 3:
                alert.status = AlertStatus.FAILED

        return success

    async def _send_email(self, alert: Alert):
        """Send alert via email."""
        # Implementation would use email service (resend, SMTP, etc.)
        # For now, just log
        print(f"[EMAIL] {alert.priority.value.upper()}: {alert.title}")

    async def _send_sms(self, alert: Alert):
        """Send alert via SMS."""
        # Implementation would use SMS service (Twilio, etc.)
        print(f"[SMS] {alert.priority.value.upper()}: {alert.title}")

    async def _send_push(self, alert: Alert):
        """Send push notification."""
        # Implementation would use push service
        print(f"[PUSH] {alert.priority.value.upper()}: {alert.title}")

    async def _send_in_app(self, alert: Alert):
        """Send in-app notification."""
        # Would update database for in-app notifications
        print(f"[IN-APP] {alert.priority.value.upper()}: {alert.title}")

    async def _send_webhook(self, alert: Alert):
        """Send to webhook."""
        # Implementation would make HTTP request
        print(f"[WEBHOOK] {alert.priority.value.upper()}: {alert.title}")

    def check_rules(
        self,
        case_id: str,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Alert]:
        """Check content against alert rules and create alerts."""
        alerts_created = []
        content_lower = content.lower()
        context = context or {}

        for rule in self.rules.values():
            if not rule.enabled:
                continue

            # Check cooldown
            cooldown_key = f"{rule.rule_id}_{case_id}"
            if cooldown_key in self.cooldowns:
                last_triggered = self.cooldowns[cooldown_key]
                if datetime.utcnow() - last_triggered < timedelta(minutes=rule.cooldown_minutes):
                    continue

            # Check conditions
            triggered = False
            trigger_reason = ""

            conditions = rule.conditions

            # Keyword matching
            if "keywords" in conditions:
                for keyword in conditions["keywords"]:
                    if keyword.lower() in content_lower:
                        triggered = True
                        trigger_reason = f"Keyword detected: '{keyword}'"
                        break

            # Deletion count
            if "deletion_count" in conditions and not triggered:
                deletion_count = context.get("deletion_count", 0)
                if deletion_count >= conditions["deletion_count"]:
                    triggered = True
                    trigger_reason = f"Mass deletion: {deletion_count} items"

            # Severity increase
            if "severity_increase" in conditions and not triggered:
                severity_change = context.get("severity_change", 0)
                if severity_change >= conditions["severity_increase"]:
                    triggered = True
                    trigger_reason = f"Severity increased by {severity_change}"

            if triggered:
                alert = self.create_alert(
                    case_id=case_id,
                    alert_type=rule.alert_type,
                    title=rule.name,
                    message=trigger_reason,
                    priority=rule.priority,
                    channels=rule.channels,
                    metadata={"rule_id": rule.rule_id, "trigger_reason": trigger_reason}
                )
                alerts_created.append(alert)
                self.cooldowns[cooldown_key] = datetime.utcnow()

        return alerts_created

    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str
    ) -> bool:
        """Mark an alert as acknowledged."""
        alert = self.alerts.get(alert_id)
        if not alert:
            return False

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = acknowledged_by
        return True

    def resolve_alert(
        self,
        alert_id: str,
        resolution_note: Optional[str] = None
    ) -> bool:
        """Mark an alert as resolved."""
        alert = self.alerts.get(alert_id)
        if not alert:
            return False

        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        if resolution_note:
            alert.metadata["resolution_note"] = resolution_note
        return True

    def escalate_alert(
        self,
        alert_id: str,
        new_priority: AlertPriority,
        reason: str
    ) -> bool:
        """Escalate an alert to higher priority."""
        alert = self.alerts.get(alert_id)
        if not alert:
            return False

        alert.priority = new_priority
        alert.status = AlertStatus.ESCALATED
        alert.metadata["escalation_reason"] = reason
        alert.metadata["escalated_at"] = datetime.utcnow().isoformat()
        return True

    def get_pending_alerts(
        self,
        case_id: Optional[str] = None,
        priority: Optional[AlertPriority] = None
    ) -> List[Alert]:
        """Get pending alerts, optionally filtered."""
        pending = [
            a for a in self.alerts.values()
            if a.status in [AlertStatus.PENDING, AlertStatus.SENT]
        ]

        if case_id:
            pending = [a for a in pending if a.case_id == case_id]

        if priority:
            pending = [a for a in pending if a.priority == priority]

        # Sort by priority
        priority_order = {
            AlertPriority.CRITICAL: 0,
            AlertPriority.HIGH: 1,
            AlertPriority.MEDIUM: 2,
            AlertPriority.LOW: 3,
            AlertPriority.INFO: 4
        }

        return sorted(pending, key=lambda a: priority_order.get(a.priority, 5))

    def get_case_alerts(
        self,
        case_id: str,
        include_resolved: bool = False
    ) -> List[Alert]:
        """Get all alerts for a case."""
        alert_ids = self.alert_history.get(case_id, [])
        alerts = [self.alerts[aid] for aid in alert_ids if aid in self.alerts]

        if not include_resolved:
            alerts = [a for a in alerts if a.status != AlertStatus.RESOLVED]

        return sorted(alerts, key=lambda a: a.created_at, reverse=True)

    def add_rule(self, rule: AlertRule) -> str:
        """Add a custom alert rule."""
        self.rules[rule.rule_id] = rule
        return rule.rule_id

    def update_rule(
        self,
        rule_id: str,
        enabled: Optional[bool] = None,
        priority: Optional[AlertPriority] = None,
        channels: Optional[List[AlertChannel]] = None
    ) -> bool:
        """Update an existing rule."""
        rule = self.rules.get(rule_id)
        if not rule:
            return False

        if enabled is not None:
            rule.enabled = enabled
        if priority is not None:
            rule.priority = priority
        if channels is not None:
            rule.channels = channels

        return True

    def get_alert_statistics(
        self,
        case_id: Optional[str] = None,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Get alert statistics."""
        cutoff = datetime.utcnow() - timedelta(days=period_days)

        alerts = list(self.alerts.values())
        if case_id:
            alerts = [a for a in alerts if a.case_id == case_id]

        alerts = [a for a in alerts if a.created_at >= cutoff]

        by_type = {}
        by_priority = {}
        by_status = {}

        for alert in alerts:
            by_type[alert.alert_type.value] = by_type.get(alert.alert_type.value, 0) + 1
            by_priority[alert.priority.value] = by_priority.get(alert.priority.value, 0) + 1
            by_status[alert.status.value] = by_status.get(alert.status.value, 0) + 1

        return {
            "total_alerts": len(alerts),
            "by_type": by_type,
            "by_priority": by_priority,
            "by_status": by_status,
            "period_days": period_days
        }
