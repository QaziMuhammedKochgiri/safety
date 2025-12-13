"""
Push Notification Service
Handles push notifications for the SafeChild PWA.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import datetime
import hashlib
import json


class NotificationType(str, Enum):
    """Types of notifications."""
    # Urgent alerts
    EMERGENCY_ALERT = "emergency_alert"
    COURT_DEADLINE = "court_deadline"
    SAFETY_WARNING = "safety_warning"

    # Case updates
    CASE_UPDATE = "case_update"
    EVIDENCE_ADDED = "evidence_added"
    DOCUMENT_READY = "document_ready"

    # Expert network
    EXPERT_RESPONSE = "expert_response"
    CONSULTATION_REMINDER = "consultation_reminder"
    PRO_BONO_MATCH = "pro_bono_match"

    # Community
    FORUM_REPLY = "forum_reply"
    SUPPORT_MESSAGE = "support_message"

    # System
    SYNC_COMPLETE = "sync_complete"
    BACKUP_COMPLETE = "backup_complete"
    APP_UPDATE = "app_update"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    URGENT = "urgent"  # Immediate display, sound, vibration
    HIGH = "high"  # Display immediately
    NORMAL = "normal"  # Standard delivery
    LOW = "low"  # Silent, badge only


@dataclass
class PushSubscription:
    """A push notification subscription."""
    subscription_id: str
    user_id: str
    device_id: str
    endpoint: str
    p256dh_key: str  # Public key for encryption
    auth_key: str  # Authentication key

    # Device info
    device_name: Optional[str]
    device_type: str  # web, android, ios
    browser: Optional[str]

    # Preferences
    enabled_types: List[NotificationType]
    quiet_hours_start: Optional[str]  # HH:MM
    quiet_hours_end: Optional[str]
    timezone: str

    # Status
    is_active: bool
    created_at: str
    last_used: Optional[str]
    expires_at: Optional[str]


@dataclass
class NotificationPayload:
    """A notification payload."""
    notification_id: str
    type: NotificationType
    priority: NotificationPriority

    # Content
    title: str
    body: str
    icon: Optional[str]
    badge: Optional[str]
    image: Optional[str]

    # Actions
    actions: List[Dict[str, str]]  # [{action: "open", title: "View", url: "/case/123"}]
    click_url: Optional[str]
    data: Dict[str, Any]

    # Display options
    tag: Optional[str]  # Group notifications
    renotify: bool  # Sound again for same tag
    require_interaction: bool  # Don't auto-dismiss
    silent: bool
    vibrate: Optional[List[int]]  # Vibration pattern

    # Timing
    timestamp: str
    ttl_seconds: int  # Time to live
    scheduled_for: Optional[str]


@dataclass
class NotificationDeliveryResult:
    """Result of notification delivery."""
    notification_id: str
    subscription_id: str
    success: bool
    delivered_at: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]
    should_retry: bool
    subscription_expired: bool


@dataclass
class NotificationPreferences:
    """User notification preferences."""
    user_id: str
    email_enabled: bool
    push_enabled: bool
    sms_enabled: bool

    # By type
    type_settings: Dict[NotificationType, Dict[str, bool]]
    # e.g., {COURT_DEADLINE: {push: True, email: True, sms: True}}

    # Quiet hours
    quiet_hours_enabled: bool
    quiet_hours_start: str  # HH:MM
    quiet_hours_end: str
    quiet_hours_timezone: str

    # Emergency override
    allow_emergency_during_quiet: bool

    # Digest
    daily_digest_enabled: bool
    daily_digest_time: str  # HH:MM

    updated_at: str


class PushNotificationService:
    """Manages push notifications for the PWA."""

    # Default vibration patterns
    VIBRATE_PATTERNS = {
        NotificationPriority.URGENT: [200, 100, 200, 100, 200],
        NotificationPriority.HIGH: [200, 100, 200],
        NotificationPriority.NORMAL: [200],
        NotificationPriority.LOW: []
    }

    # Default TTL by priority (seconds)
    DEFAULT_TTL = {
        NotificationPriority.URGENT: 86400,  # 24 hours
        NotificationPriority.HIGH: 43200,  # 12 hours
        NotificationPriority.NORMAL: 21600,  # 6 hours
        NotificationPriority.LOW: 3600  # 1 hour
    }

    # Notification icons by type
    ICONS = {
        NotificationType.EMERGENCY_ALERT: "/icons/emergency.png",
        NotificationType.COURT_DEADLINE: "/icons/court.png",
        NotificationType.SAFETY_WARNING: "/icons/warning.png",
        NotificationType.CASE_UPDATE: "/icons/case.png",
        NotificationType.EVIDENCE_ADDED: "/icons/evidence.png",
        NotificationType.DOCUMENT_READY: "/icons/document.png",
        NotificationType.EXPERT_RESPONSE: "/icons/expert.png",
        NotificationType.CONSULTATION_REMINDER: "/icons/calendar.png",
        NotificationType.PRO_BONO_MATCH: "/icons/match.png",
        NotificationType.FORUM_REPLY: "/icons/forum.png",
        NotificationType.SUPPORT_MESSAGE: "/icons/support.png",
        NotificationType.SYNC_COMPLETE: "/icons/sync.png",
        NotificationType.BACKUP_COMPLETE: "/icons/backup.png",
        NotificationType.APP_UPDATE: "/icons/update.png"
    }

    def __init__(self):
        self.subscriptions: Dict[str, PushSubscription] = {}
        self.user_subscriptions: Dict[str, List[str]] = {}  # user_id -> [subscription_ids]
        self.preferences: Dict[str, NotificationPreferences] = {}
        self.notification_history: Dict[str, NotificationPayload] = {}
        self.delivery_results: Dict[str, List[NotificationDeliveryResult]] = {}
        self.scheduled_notifications: Dict[str, NotificationPayload] = {}

    def register_subscription(
        self,
        user_id: str,
        device_id: str,
        endpoint: str,
        p256dh_key: str,
        auth_key: str,
        device_type: str,
        device_name: Optional[str] = None,
        browser: Optional[str] = None,
        timezone: str = "UTC"
    ) -> PushSubscription:
        """Register a push subscription."""
        subscription_id = hashlib.md5(
            f"{user_id}-{device_id}-{endpoint}".encode()
        ).hexdigest()[:12]

        subscription = PushSubscription(
            subscription_id=subscription_id,
            user_id=user_id,
            device_id=device_id,
            endpoint=endpoint,
            p256dh_key=p256dh_key,
            auth_key=auth_key,
            device_name=device_name,
            device_type=device_type,
            browser=browser,
            enabled_types=list(NotificationType),  # Enable all by default
            quiet_hours_start=None,
            quiet_hours_end=None,
            timezone=timezone,
            is_active=True,
            created_at=datetime.datetime.now().isoformat(),
            last_used=None,
            expires_at=None
        )

        self.subscriptions[subscription_id] = subscription

        # Track user subscriptions
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = []
        if subscription_id not in self.user_subscriptions[user_id]:
            self.user_subscriptions[user_id].append(subscription_id)

        return subscription

    def unregister_subscription(self, subscription_id: str) -> bool:
        """Unregister a push subscription."""
        if subscription_id not in self.subscriptions:
            return False

        subscription = self.subscriptions[subscription_id]
        user_id = subscription.user_id

        # Remove from user subscriptions
        if user_id in self.user_subscriptions:
            if subscription_id in self.user_subscriptions[user_id]:
                self.user_subscriptions[user_id].remove(subscription_id)

        del self.subscriptions[subscription_id]
        return True

    def create_notification(
        self,
        notification_type: NotificationType,
        title: str,
        body: str,
        priority: Optional[NotificationPriority] = None,
        click_url: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        actions: Optional[List[Dict[str, str]]] = None,
        tag: Optional[str] = None,
        image: Optional[str] = None,
        scheduled_for: Optional[str] = None
    ) -> NotificationPayload:
        """Create a notification payload."""
        # Determine priority based on type if not specified
        if priority is None:
            priority = self._get_default_priority(notification_type)

        notification_id = hashlib.md5(
            f"{notification_type}-{title}-{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        payload = NotificationPayload(
            notification_id=notification_id,
            type=notification_type,
            priority=priority,
            title=title,
            body=body,
            icon=self.ICONS.get(notification_type, "/icons/default.png"),
            badge="/badge.png",
            image=image,
            actions=actions or [],
            click_url=click_url,
            data=data or {},
            tag=tag,
            renotify=priority in [NotificationPriority.URGENT, NotificationPriority.HIGH],
            require_interaction=priority == NotificationPriority.URGENT,
            silent=priority == NotificationPriority.LOW,
            vibrate=self.VIBRATE_PATTERNS.get(priority),
            timestamp=datetime.datetime.now().isoformat(),
            ttl_seconds=self.DEFAULT_TTL.get(priority, 21600),
            scheduled_for=scheduled_for
        )

        if scheduled_for:
            self.scheduled_notifications[notification_id] = payload
        else:
            self.notification_history[notification_id] = payload

        return payload

    def send_to_user(
        self,
        user_id: str,
        notification: NotificationPayload
    ) -> List[NotificationDeliveryResult]:
        """Send notification to all user's devices."""
        results = []

        subscription_ids = self.user_subscriptions.get(user_id, [])
        for subscription_id in subscription_ids:
            subscription = self.subscriptions.get(subscription_id)
            if not subscription or not subscription.is_active:
                continue

            # Check if notification type is enabled
            if notification.type not in subscription.enabled_types:
                continue

            # Check quiet hours
            if self._is_quiet_hours(subscription) and notification.priority != NotificationPriority.URGENT:
                continue

            result = self._deliver_notification(subscription, notification)
            results.append(result)

            # Handle expired subscriptions
            if result.subscription_expired:
                subscription.is_active = False

        # Store delivery results
        self.delivery_results[notification.notification_id] = results

        return results

    def send_to_subscriptions(
        self,
        subscription_ids: List[str],
        notification: NotificationPayload
    ) -> List[NotificationDeliveryResult]:
        """Send notification to specific subscriptions."""
        results = []

        for subscription_id in subscription_ids:
            subscription = self.subscriptions.get(subscription_id)
            if not subscription or not subscription.is_active:
                continue

            result = self._deliver_notification(subscription, notification)
            results.append(result)

            if result.subscription_expired:
                subscription.is_active = False

        self.delivery_results[notification.notification_id] = results
        return results

    def broadcast(
        self,
        notification: NotificationPayload,
        user_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Broadcast notification to multiple users."""
        results = {
            "total_subscriptions": 0,
            "delivered": 0,
            "failed": 0,
            "skipped": 0,
            "expired": 0
        }

        target_users = user_ids or list(self.user_subscriptions.keys())

        for user_id in target_users:
            user_results = self.send_to_user(user_id, notification)
            results["total_subscriptions"] += len(user_results)

            for result in user_results:
                if result.success:
                    results["delivered"] += 1
                elif result.subscription_expired:
                    results["expired"] += 1
                else:
                    results["failed"] += 1

        return results

    def process_scheduled_notifications(self) -> Dict[str, Any]:
        """Process scheduled notifications that are due."""
        now = datetime.datetime.now()
        results = {
            "processed": 0,
            "sent": 0,
            "failed": 0
        }

        notifications_to_remove = []

        for notification_id, notification in self.scheduled_notifications.items():
            if notification.scheduled_for:
                scheduled_time = datetime.datetime.fromisoformat(notification.scheduled_for)
                if scheduled_time <= now:
                    notifications_to_remove.append(notification_id)
                    results["processed"] += 1

                    # Get user from data
                    user_id = notification.data.get("user_id")
                    if user_id:
                        delivery_results = self.send_to_user(user_id, notification)
                        if any(r.success for r in delivery_results):
                            results["sent"] += 1
                        else:
                            results["failed"] += 1

        for notification_id in notifications_to_remove:
            del self.scheduled_notifications[notification_id]

        return results

    def set_user_preferences(
        self,
        user_id: str,
        email_enabled: bool = True,
        push_enabled: bool = True,
        sms_enabled: bool = False,
        quiet_hours_enabled: bool = False,
        quiet_hours_start: str = "22:00",
        quiet_hours_end: str = "07:00",
        quiet_hours_timezone: str = "UTC",
        allow_emergency_during_quiet: bool = True,
        daily_digest_enabled: bool = False,
        daily_digest_time: str = "08:00"
    ) -> NotificationPreferences:
        """Set user notification preferences."""
        # Default type settings - all enabled for push and email
        type_settings = {}
        for ntype in NotificationType:
            is_urgent = ntype in [
                NotificationType.EMERGENCY_ALERT,
                NotificationType.COURT_DEADLINE,
                NotificationType.SAFETY_WARNING
            ]
            type_settings[ntype] = {
                "push": True,
                "email": True,
                "sms": is_urgent  # SMS only for urgent types by default
            }

        preferences = NotificationPreferences(
            user_id=user_id,
            email_enabled=email_enabled,
            push_enabled=push_enabled,
            sms_enabled=sms_enabled,
            type_settings=type_settings,
            quiet_hours_enabled=quiet_hours_enabled,
            quiet_hours_start=quiet_hours_start,
            quiet_hours_end=quiet_hours_end,
            quiet_hours_timezone=quiet_hours_timezone,
            allow_emergency_during_quiet=allow_emergency_during_quiet,
            daily_digest_enabled=daily_digest_enabled,
            daily_digest_time=daily_digest_time,
            updated_at=datetime.datetime.now().isoformat()
        )

        self.preferences[user_id] = preferences
        return preferences

    def update_subscription_types(
        self,
        subscription_id: str,
        enabled_types: List[NotificationType]
    ) -> bool:
        """Update which notification types a subscription receives."""
        if subscription_id not in self.subscriptions:
            return False

        self.subscriptions[subscription_id].enabled_types = enabled_types
        return True

    def get_user_subscriptions(self, user_id: str) -> List[PushSubscription]:
        """Get all subscriptions for a user."""
        subscription_ids = self.user_subscriptions.get(user_id, [])
        return [
            self.subscriptions[sid]
            for sid in subscription_ids
            if sid in self.subscriptions
        ]

    def get_delivery_status(
        self,
        notification_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get delivery status for a notification."""
        results = self.delivery_results.get(notification_id, [])
        if not results:
            return None

        return {
            "notification_id": notification_id,
            "total_attempts": len(results),
            "successful": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success),
            "expired_subscriptions": sum(1 for r in results if r.subscription_expired),
            "results": [
                {
                    "subscription_id": r.subscription_id,
                    "success": r.success,
                    "delivered_at": r.delivered_at,
                    "error": r.error_message
                }
                for r in results
            ]
        }

    def cleanup_expired_subscriptions(self) -> int:
        """Remove expired subscriptions."""
        now = datetime.datetime.now()
        count = 0

        expired_ids = []
        for sub_id, subscription in self.subscriptions.items():
            if subscription.expires_at:
                expires = datetime.datetime.fromisoformat(subscription.expires_at)
                if now > expires:
                    expired_ids.append(sub_id)

        for sub_id in expired_ids:
            self.unregister_subscription(sub_id)
            count += 1

        return count

    def get_notification_statistics(
        self,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get notification statistics."""
        if user_id:
            # User-specific stats
            user_notifications = [
                n for n in self.notification_history.values()
                if n.data.get("user_id") == user_id
            ]
        else:
            user_notifications = list(self.notification_history.values())

        by_type = {}
        by_priority = {}
        for notification in user_notifications:
            type_key = notification.type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

            priority_key = notification.priority.value
            by_priority[priority_key] = by_priority.get(priority_key, 0) + 1

        # Calculate delivery rates
        total_deliveries = sum(len(r) for r in self.delivery_results.values())
        successful_deliveries = sum(
            sum(1 for d in r if d.success)
            for r in self.delivery_results.values()
        )

        return {
            "total_notifications": len(user_notifications),
            "by_type": by_type,
            "by_priority": by_priority,
            "scheduled_pending": len(self.scheduled_notifications),
            "total_deliveries": total_deliveries,
            "successful_deliveries": successful_deliveries,
            "delivery_rate": round(successful_deliveries / total_deliveries * 100, 2)
            if total_deliveries > 0 else 0
        }

    def _get_default_priority(self, notification_type: NotificationType) -> NotificationPriority:
        """Get default priority for a notification type."""
        urgent_types = [
            NotificationType.EMERGENCY_ALERT,
            NotificationType.SAFETY_WARNING
        ]
        high_types = [
            NotificationType.COURT_DEADLINE,
            NotificationType.CONSULTATION_REMINDER
        ]
        low_types = [
            NotificationType.SYNC_COMPLETE,
            NotificationType.BACKUP_COMPLETE,
            NotificationType.APP_UPDATE
        ]

        if notification_type in urgent_types:
            return NotificationPriority.URGENT
        elif notification_type in high_types:
            return NotificationPriority.HIGH
        elif notification_type in low_types:
            return NotificationPriority.LOW
        else:
            return NotificationPriority.NORMAL

    def _is_quiet_hours(self, subscription: PushSubscription) -> bool:
        """Check if it's currently quiet hours for a subscription."""
        if not subscription.quiet_hours_start or not subscription.quiet_hours_end:
            return False

        # Get current time in subscription's timezone
        # (Simplified - in production, use proper timezone handling)
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")

        start = subscription.quiet_hours_start
        end = subscription.quiet_hours_end

        # Handle overnight quiet hours (e.g., 22:00 to 07:00)
        if start > end:
            return current_time >= start or current_time < end
        else:
            return start <= current_time < end

    def _deliver_notification(
        self,
        subscription: PushSubscription,
        notification: NotificationPayload
    ) -> NotificationDeliveryResult:
        """Deliver a notification to a subscription."""
        # In production, this would use Web Push protocol
        # Here we simulate the delivery

        # Update last used
        subscription.last_used = datetime.datetime.now().isoformat()

        # Simulate successful delivery
        # In production, handle actual push service response
        return NotificationDeliveryResult(
            notification_id=notification.notification_id,
            subscription_id=subscription.subscription_id,
            success=True,
            delivered_at=datetime.datetime.now().isoformat(),
            error_code=None,
            error_message=None,
            should_retry=False,
            subscription_expired=False
        )
