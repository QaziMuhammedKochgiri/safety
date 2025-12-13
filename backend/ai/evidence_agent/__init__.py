"""
Automated Evidence Collection Agent
Background sync, change detection, and automated evidence gathering.
"""

from .collection_engine import (
    EvidenceCollector,
    CollectionTask,
    CollectionResult,
    CollectionStatus,
    SyncMode
)

from .change_detector import (
    ChangeDetector,
    ChangeType,
    DetectedChange,
    ChangeReport
)

from .alert_system import (
    AlertManager,
    Alert,
    AlertPriority,
    AlertType,
    AlertChannel
)

from .scheduler import (
    CollectionScheduler,
    ScheduleConfig,
    ScheduledTask,
    ScheduleFrequency
)

from .digest_generator import (
    DigestGenerator,
    WeeklyDigest,
    DigestSection,
    DigestFormat
)

__all__ = [
    # Collection Engine
    'EvidenceCollector',
    'CollectionTask',
    'CollectionResult',
    'CollectionStatus',
    'SyncMode',
    # Change Detector
    'ChangeDetector',
    'ChangeType',
    'DetectedChange',
    'ChangeReport',
    # Alert System
    'AlertManager',
    'Alert',
    'AlertPriority',
    'AlertType',
    'AlertChannel',
    # Scheduler
    'CollectionScheduler',
    'ScheduleConfig',
    'ScheduledTask',
    'ScheduleFrequency',
    # Digest Generator
    'DigestGenerator',
    'WeeklyDigest',
    'DigestSection',
    'DigestFormat'
]
