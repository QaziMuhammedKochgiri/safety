"""
Multi-Device Comparison Module for SafeChild

Provides device pairing and comparison capabilities:
- Device Pairing: Parent-child device matching
- Discrepancy Detection: Deleted message detection, edit history
- Timeline Visualization: Side-by-side comparison
"""

from .device_comparison import (
    DeviceComparisonEngine,
    DevicePairing,
    TimelineSync,
    ContactMatcher,
    MessageThreadMatcher,
    DeviceInfo,
    DeviceRole,
    DeviceType,
    PairedDevices,
    SyncedTimeline,
    ContactOverlap,
    ThreadMatch
)

from .discrepancy_detection import (
    DiscrepancyDetector,
    DeletedMessageFinder,
    EditHistoryComparer,
    TimeGapAnalyzer,
    ScreenshotVerifier,
    Discrepancy,
    DiscrepancyType,
    DeletedMessage,
    EditHistory,
    TimeGap,
    ScreenshotMatch
)

from .visualization import (
    ComparisonVisualizer,
    TimelineRenderer,
    DiffRenderer,
    ConflictHighlighter,
    VisualizationFormat,
    TimelineView,
    DiffView,
    ConflictReport
)

__all__ = [
    # Device Comparison
    'DeviceComparisonEngine',
    'DevicePairing',
    'TimelineSync',
    'ContactMatcher',
    'MessageThreadMatcher',
    'DeviceInfo',
    'DeviceRole',
    'DeviceType',
    'PairedDevices',
    'SyncedTimeline',
    'ContactOverlap',
    'ThreadMatch',
    # Discrepancy Detection
    'DiscrepancyDetector',
    'DeletedMessageFinder',
    'EditHistoryComparer',
    'TimeGapAnalyzer',
    'ScreenshotVerifier',
    'Discrepancy',
    'DiscrepancyType',
    'DeletedMessage',
    'EditHistory',
    'TimeGap',
    'ScreenshotMatch',
    # Visualization
    'ComparisonVisualizer',
    'TimelineRenderer',
    'DiffRenderer',
    'ConflictHighlighter',
    'VisualizationFormat',
    'TimelineView',
    'DiffView',
    'ConflictReport'
]
