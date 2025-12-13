"""
Mobile-First PWA Module
Progressive Web App infrastructure for SafeChild mobile experience.

Q4 2026 Implementation
"""

from .offline_manager import (
    OfflineManager,
    CacheStrategy,
    CacheEntry,
    SyncItem,
    SyncConflict,
    ConflictResolution
)

from .push_notifications import (
    PushNotificationService,
    NotificationType,
    NotificationPriority,
    PushSubscription,
    NotificationPayload,
    NotificationDeliveryResult
)

from .device_manager import (
    DeviceManager,
    DeviceType,
    DeviceInfo,
    DeviceCapabilities,
    BiometricType,
    SecurityStatus
)

from .mobile_evidence import (
    MobileEvidenceCapture,
    CaptureType,
    MediaCapture,
    LocationCapture,
    VoiceRecording,
    PhotoCapture
)

from .app_shell import (
    AppShellManager,
    AppState,
    NavigationHistory,
    ShellConfig,
    ScreenOrientation
)

from .secure_storage import (
    SecureStorageManager,
    StorageEncryption,
    SecureItem,
    StorageQuota,
    EncryptionKey
)

__all__ = [
    # Offline Manager
    'OfflineManager',
    'CacheStrategy',
    'CacheEntry',
    'SyncItem',
    'SyncConflict',
    'ConflictResolution',

    # Push Notifications
    'PushNotificationService',
    'NotificationType',
    'NotificationPriority',
    'PushSubscription',
    'NotificationPayload',
    'NotificationDeliveryResult',

    # Device Manager
    'DeviceManager',
    'DeviceType',
    'DeviceInfo',
    'DeviceCapabilities',
    'BiometricType',
    'SecurityStatus',

    # Mobile Evidence
    'MobileEvidenceCapture',
    'CaptureType',
    'MediaCapture',
    'LocationCapture',
    'VoiceRecording',
    'PhotoCapture',

    # App Shell
    'AppShellManager',
    'AppState',
    'NavigationHistory',
    'ShellConfig',
    'ScreenOrientation',

    # Secure Storage
    'SecureStorageManager',
    'StorageEncryption',
    'SecureItem',
    'StorageQuota',
    'EncryptionKey'
]
