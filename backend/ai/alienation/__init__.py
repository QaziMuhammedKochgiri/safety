"""
Parental Alienation Expert System
Advanced detection and analysis of parental alienation tactics.
"""

from .tactics_database import (
    AlienationTacticDB,
    ManipulationTactic,
    TacticCategory,
    TacticSeverity,
    CaseLawReference,
    LiteratureReference
)

from .pattern_matcher import (
    PatternMatcher,
    PatternMatch,
    PatternType,
    MatchConfidence
)

from .severity_scorer import (
    SeverityScorer,
    SeverityScore,
    EvidenceStrength,
    RiskLevel
)

from .timeline_analyzer import (
    AlienationTimelineAnalyzer,
    AlienationEvent,
    TimelinePattern,
    EscalationTrend
)

from .expert_report import (
    ExpertReportGenerator,
    ExpertReport,
    ReportSection,
    Recommendation
)

__all__ = [
    # Tactics Database
    'AlienationTacticDB',
    'ManipulationTactic',
    'TacticCategory',
    'TacticSeverity',
    'CaseLawReference',
    'LiteratureReference',
    # Pattern Matcher
    'PatternMatcher',
    'PatternMatch',
    'PatternType',
    'MatchConfidence',
    # Severity Scorer
    'SeverityScorer',
    'SeverityScore',
    'EvidenceStrength',
    'RiskLevel',
    # Timeline Analyzer
    'AlienationTimelineAnalyzer',
    'AlienationEvent',
    'TimelinePattern',
    'EscalationTrend',
    # Expert Report
    'ExpertReportGenerator',
    'ExpertReport',
    'ReportSection',
    'Recommendation'
]
