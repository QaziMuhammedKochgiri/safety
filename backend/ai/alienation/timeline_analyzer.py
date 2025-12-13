"""
Alienation Timeline Analyzer
Tracks alienation patterns over time with escalation detection.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from .tactics_database import AlienationTacticDB, TacticCategory
from .pattern_matcher import PatternMatch


class EscalationTrend(str, Enum):
    """Escalation trend types."""
    RAPID_ESCALATION = "rapid_escalation"  # Significant increase in short time
    GRADUAL_ESCALATION = "gradual_escalation"  # Slow but steady increase
    STABLE = "stable"  # No significant change
    DE_ESCALATING = "de_escalating"  # Improving
    FLUCTUATING = "fluctuating"  # Irregular pattern


class EventType(str, Enum):
    """Types of timeline events."""
    TACTIC_DETECTED = "tactic_detected"
    ESCALATION_POINT = "escalation_point"
    NEW_TACTIC_INTRODUCED = "new_tactic_introduced"
    SEVERITY_SPIKE = "severity_spike"
    GAP_IN_MONITORING = "gap_in_monitoring"
    PATTERN_CHANGE = "pattern_change"


@dataclass
class AlienationEvent:
    """A single event in the alienation timeline."""
    event_id: str
    event_type: EventType
    timestamp: datetime
    tactic_id: Optional[str]
    tactic_name: Optional[str]
    category: Optional[TacticCategory]
    severity: float
    description: str
    matched_text: Optional[str] = None
    context: Optional[str] = None
    significance: str = "normal"  # low, normal, high, critical
    related_events: List[str] = field(default_factory=list)


@dataclass
class TimelinePattern:
    """A detected pattern in the timeline."""
    pattern_id: str
    pattern_type: str
    start_date: datetime
    end_date: datetime
    frequency: float  # Events per day
    avg_severity: float
    tactics_involved: List[str]
    categories_involved: List[TacticCategory]
    description: str
    significance: str


@dataclass
class TimelineSummary:
    """Summary of the alienation timeline."""
    case_id: str
    analysis_date: datetime
    time_span: timedelta
    total_events: int
    escalation_trend: EscalationTrend
    key_events: List[AlienationEvent]
    patterns: List[TimelinePattern]
    severity_by_week: Dict[str, float]
    category_distribution: Dict[str, int]
    first_detection: Optional[datetime]
    most_recent: Optional[datetime]
    peak_period: Optional[Tuple[datetime, datetime]]
    recommendations: List[str]


class AlienationTimelineAnalyzer:
    """Analyzes alienation patterns over time."""

    def __init__(self, db: Optional[AlienationTacticDB] = None):
        self.db = db or AlienationTacticDB()

    def build_timeline(
        self,
        matches: List[PatternMatch],
        case_id: str = "default"
    ) -> TimelineSummary:
        """Build comprehensive timeline from pattern matches."""
        if not matches:
            return self._empty_timeline(case_id)

        # Sort matches by timestamp
        timed_matches = [m for m in matches if m.timestamp]
        timed_matches.sort(key=lambda m: m.timestamp)

        if not timed_matches:
            return self._empty_timeline(case_id)

        # Create events from matches
        events = self._create_events(timed_matches)

        # Detect special events (escalations, new tactics, etc.)
        special_events = self._detect_special_events(events, timed_matches)
        events.extend(special_events)
        events.sort(key=lambda e: e.timestamp)

        # Analyze patterns
        patterns = self._analyze_patterns(events, timed_matches)

        # Calculate statistics
        time_span = timed_matches[-1].timestamp - timed_matches[0].timestamp
        severity_by_week = self._calculate_weekly_severity(timed_matches)
        category_distribution = self._calculate_category_distribution(timed_matches)
        escalation_trend = self._determine_escalation_trend(timed_matches, severity_by_week)
        peak_period = self._find_peak_period(timed_matches)
        key_events = self._identify_key_events(events)
        recommendations = self._generate_timeline_recommendations(
            escalation_trend, patterns, key_events
        )

        return TimelineSummary(
            case_id=case_id,
            analysis_date=datetime.utcnow(),
            time_span=time_span,
            total_events=len(events),
            escalation_trend=escalation_trend,
            key_events=key_events,
            patterns=patterns,
            severity_by_week=severity_by_week,
            category_distribution=category_distribution,
            first_detection=timed_matches[0].timestamp if timed_matches else None,
            most_recent=timed_matches[-1].timestamp if timed_matches else None,
            peak_period=peak_period,
            recommendations=recommendations
        )

    def _empty_timeline(self, case_id: str) -> TimelineSummary:
        """Create empty timeline summary."""
        return TimelineSummary(
            case_id=case_id,
            analysis_date=datetime.utcnow(),
            time_span=timedelta(0),
            total_events=0,
            escalation_trend=EscalationTrend.STABLE,
            key_events=[],
            patterns=[],
            severity_by_week={},
            category_distribution={},
            first_detection=None,
            most_recent=None,
            peak_period=None,
            recommendations=["Continue monitoring for alienation patterns"]
        )

    def _create_events(self, matches: List[PatternMatch]) -> List[AlienationEvent]:
        """Create timeline events from matches."""
        events = []
        for i, match in enumerate(matches):
            event = AlienationEvent(
                event_id=f"evt_{i:04d}",
                event_type=EventType.TACTIC_DETECTED,
                timestamp=match.timestamp,
                tactic_id=match.tactic_id,
                tactic_name=match.tactic_name,
                category=match.category,
                severity=match.severity_score * match.confidence,
                description=f"Detected: {match.tactic_name}",
                matched_text=match.matched_text,
                context=f"{match.context_before}...{match.context_after}",
                significance=self._assess_significance(match)
            )
            events.append(event)
        return events

    def _assess_significance(self, match: PatternMatch) -> str:
        """Assess significance of a single match."""
        score = match.severity_score * match.confidence
        if score >= 8:
            return "critical"
        elif score >= 6:
            return "high"
        elif score >= 4:
            return "normal"
        else:
            return "low"

    def _detect_special_events(
        self,
        events: List[AlienationEvent],
        matches: List[PatternMatch]
    ) -> List[AlienationEvent]:
        """Detect special events like escalations, new tactics, etc."""
        special_events = []
        seen_tactics = set()
        window_size = 7  # days

        for i, match in enumerate(matches):
            # Detect new tactic introduction
            if match.tactic_id not in seen_tactics:
                if len(seen_tactics) > 0:  # Not the first tactic
                    event = AlienationEvent(
                        event_id=f"special_new_{len(special_events):04d}",
                        event_type=EventType.NEW_TACTIC_INTRODUCED,
                        timestamp=match.timestamp,
                        tactic_id=match.tactic_id,
                        tactic_name=match.tactic_name,
                        category=match.category,
                        severity=match.severity_score,
                        description=f"New tactic introduced: {match.tactic_name}",
                        significance="high"
                    )
                    special_events.append(event)
                seen_tactics.add(match.tactic_id)

            # Detect severity spikes
            if i >= 3:
                recent = matches[max(0, i-3):i]
                avg_recent = statistics.mean(m.severity_score for m in recent)
                if match.severity_score > avg_recent * 1.5 and match.severity_score >= 7:
                    event = AlienationEvent(
                        event_id=f"special_spike_{len(special_events):04d}",
                        event_type=EventType.SEVERITY_SPIKE,
                        timestamp=match.timestamp,
                        tactic_id=match.tactic_id,
                        tactic_name=match.tactic_name,
                        category=match.category,
                        severity=match.severity_score,
                        description=f"Severity spike: {match.tactic_name} (severity {match.severity_score})",
                        significance="critical"
                    )
                    special_events.append(event)

        # Detect escalation points (significant increase in frequency)
        if len(matches) >= 10:
            weekly_counts = self._get_weekly_counts(matches)
            weeks = sorted(weekly_counts.keys())

            for i in range(1, len(weeks)):
                prev_count = weekly_counts[weeks[i-1]]
                curr_count = weekly_counts[weeks[i]]

                if curr_count > prev_count * 2 and curr_count >= 5:
                    # Parse week start date
                    week_start = datetime.strptime(weeks[i] + '-1', '%Y-W%W-%w')
                    event = AlienationEvent(
                        event_id=f"special_esc_{len(special_events):04d}",
                        event_type=EventType.ESCALATION_POINT,
                        timestamp=week_start,
                        tactic_id=None,
                        tactic_name=None,
                        category=None,
                        severity=8.0,
                        description=f"Escalation detected: incidents doubled from {prev_count} to {curr_count}",
                        significance="critical"
                    )
                    special_events.append(event)

        return special_events

    def _get_weekly_counts(self, matches: List[PatternMatch]) -> Dict[str, int]:
        """Get match counts by week."""
        weekly = defaultdict(int)
        for match in matches:
            if match.timestamp:
                week = match.timestamp.strftime('%Y-W%W')
                weekly[week] += 1
        return dict(weekly)

    def _analyze_patterns(
        self,
        events: List[AlienationEvent],
        matches: List[PatternMatch]
    ) -> List[TimelinePattern]:
        """Analyze and identify patterns in timeline."""
        patterns = []

        if len(matches) < 5:
            return patterns

        # Pattern 1: Clustering around specific periods
        clusters = self._find_temporal_clusters(matches)
        for cluster_id, cluster in enumerate(clusters):
            if len(cluster) >= 3:
                start = min(m.timestamp for m in cluster)
                end = max(m.timestamp for m in cluster)
                days = max(1, (end - start).days)

                pattern = TimelinePattern(
                    pattern_id=f"cluster_{cluster_id}",
                    pattern_type="temporal_cluster",
                    start_date=start,
                    end_date=end,
                    frequency=len(cluster) / days,
                    avg_severity=statistics.mean(m.severity_score for m in cluster),
                    tactics_involved=list(set(m.tactic_id for m in cluster)),
                    categories_involved=list(set(m.category for m in cluster)),
                    description=f"Cluster of {len(cluster)} incidents over {days} days",
                    significance="high" if len(cluster) >= 5 else "normal"
                )
                patterns.append(pattern)

        # Pattern 2: Category-specific patterns
        category_matches = defaultdict(list)
        for match in matches:
            category_matches[match.category].append(match)

        for category, cat_matches in category_matches.items():
            if len(cat_matches) >= 5:
                start = min(m.timestamp for m in cat_matches)
                end = max(m.timestamp for m in cat_matches)
                days = max(1, (end - start).days)

                pattern = TimelinePattern(
                    pattern_id=f"category_{category.value}",
                    pattern_type="category_pattern",
                    start_date=start,
                    end_date=end,
                    frequency=len(cat_matches) / days,
                    avg_severity=statistics.mean(m.severity_score for m in cat_matches),
                    tactics_involved=list(set(m.tactic_id for m in cat_matches)),
                    categories_involved=[category],
                    description=f"Persistent {category.value} pattern ({len(cat_matches)} incidents)",
                    significance="high"
                )
                patterns.append(pattern)

        # Pattern 3: Escalation pattern
        if len(matches) >= 10:
            mid = len(matches) // 2
            first_half = matches[:mid]
            second_half = matches[mid:]

            first_avg = statistics.mean(m.severity_score for m in first_half)
            second_avg = statistics.mean(m.severity_score for m in second_half)

            if second_avg > first_avg * 1.3:
                pattern = TimelinePattern(
                    pattern_id="escalation_pattern",
                    pattern_type="severity_escalation",
                    start_date=first_half[0].timestamp,
                    end_date=second_half[-1].timestamp,
                    frequency=len(matches) / max(1, (second_half[-1].timestamp - first_half[0].timestamp).days),
                    avg_severity=statistics.mean(m.severity_score for m in matches),
                    tactics_involved=list(set(m.tactic_id for m in matches)),
                    categories_involved=list(set(m.category for m in matches)),
                    description=f"Severity escalation: avg increased from {first_avg:.1f} to {second_avg:.1f}",
                    significance="critical"
                )
                patterns.append(pattern)

        return patterns

    def _find_temporal_clusters(
        self,
        matches: List[PatternMatch],
        gap_threshold_days: int = 7
    ) -> List[List[PatternMatch]]:
        """Find clusters of matches separated by gaps."""
        if not matches:
            return []

        clusters = []
        current_cluster = [matches[0]]

        for i in range(1, len(matches)):
            gap = (matches[i].timestamp - matches[i-1].timestamp).days
            if gap <= gap_threshold_days:
                current_cluster.append(matches[i])
            else:
                if len(current_cluster) >= 2:
                    clusters.append(current_cluster)
                current_cluster = [matches[i]]

        if len(current_cluster) >= 2:
            clusters.append(current_cluster)

        return clusters

    def _calculate_weekly_severity(
        self,
        matches: List[PatternMatch]
    ) -> Dict[str, float]:
        """Calculate average severity by week."""
        weekly_scores = defaultdict(list)

        for match in matches:
            if match.timestamp:
                week = match.timestamp.strftime('%Y-W%W')
                weekly_scores[week].append(match.severity_score * match.confidence)

        return {
            week: round(statistics.mean(scores), 2)
            for week, scores in sorted(weekly_scores.items())
        }

    def _calculate_category_distribution(
        self,
        matches: List[PatternMatch]
    ) -> Dict[str, int]:
        """Calculate distribution of matches by category."""
        distribution = defaultdict(int)
        for match in matches:
            distribution[match.category.value] += 1
        return dict(distribution)

    def _determine_escalation_trend(
        self,
        matches: List[PatternMatch],
        severity_by_week: Dict[str, float]
    ) -> EscalationTrend:
        """Determine overall escalation trend."""
        if len(severity_by_week) < 3:
            return EscalationTrend.STABLE

        weeks = sorted(severity_by_week.keys())
        severities = [severity_by_week[w] for w in weeks]

        # Calculate trend using linear regression approximation
        n = len(severities)
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(severities)

        numerator = sum((i - x_mean) * (severities[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return EscalationTrend.STABLE

        slope = numerator / denominator
        relative_slope = slope / max(y_mean, 0.1)

        # Check for fluctuation
        variance = statistics.variance(severities) if len(severities) > 1 else 0
        cv = (variance ** 0.5) / max(y_mean, 0.1)  # Coefficient of variation

        if cv > 0.5:
            return EscalationTrend.FLUCTUATING

        if relative_slope > 0.3:
            # Check if rapid (significant change in short time)
            if len(weeks) <= 4 and severities[-1] > severities[0] * 1.5:
                return EscalationTrend.RAPID_ESCALATION
            return EscalationTrend.GRADUAL_ESCALATION
        elif relative_slope < -0.2:
            return EscalationTrend.DE_ESCALATING
        else:
            return EscalationTrend.STABLE

    def _find_peak_period(
        self,
        matches: List[PatternMatch]
    ) -> Optional[Tuple[datetime, datetime]]:
        """Find the peak period of alienation activity."""
        if len(matches) < 5:
            return None

        # Use sliding window to find highest activity period
        window_days = 14
        best_start = None
        best_count = 0
        best_severity = 0

        for i, match in enumerate(matches):
            window_start = match.timestamp
            window_end = window_start + timedelta(days=window_days)

            window_matches = [
                m for m in matches
                if window_start <= m.timestamp <= window_end
            ]

            count = len(window_matches)
            severity = sum(m.severity_score for m in window_matches)

            if count > best_count or (count == best_count and severity > best_severity):
                best_count = count
                best_severity = severity
                best_start = window_start

        if best_start:
            return (best_start, best_start + timedelta(days=window_days))
        return None

    def _identify_key_events(
        self,
        events: List[AlienationEvent]
    ) -> List[AlienationEvent]:
        """Identify the most significant events."""
        # Sort by significance and severity
        significance_order = {"critical": 4, "high": 3, "normal": 2, "low": 1}

        sorted_events = sorted(
            events,
            key=lambda e: (significance_order.get(e.significance, 0), e.severity),
            reverse=True
        )

        # Return top events, ensuring diversity
        key_events = []
        seen_types = set()

        for event in sorted_events:
            if len(key_events) >= 10:
                break

            # Ensure we get different types of events
            if event.event_type not in seen_types or event.significance == "critical":
                key_events.append(event)
                seen_types.add(event.event_type)

        return key_events

    def _generate_timeline_recommendations(
        self,
        trend: EscalationTrend,
        patterns: List[TimelinePattern],
        key_events: List[AlienationEvent]
    ) -> List[str]:
        """Generate recommendations based on timeline analysis."""
        recommendations = []

        # Trend-based recommendations
        if trend == EscalationTrend.RAPID_ESCALATION:
            recommendations.append("URGENT: Rapid escalation detected - immediate professional intervention recommended")
            recommendations.append("Consider emergency court filing")
        elif trend == EscalationTrend.GRADUAL_ESCALATION:
            recommendations.append("Escalation trend detected - proactive intervention recommended")
            recommendations.append("Schedule evaluation with custody expert")
        elif trend == EscalationTrend.DE_ESCALATING:
            recommendations.append("Positive trend observed - continue current approach")
            recommendations.append("Document improvement for court records")
        elif trend == EscalationTrend.FLUCTUATING:
            recommendations.append("Irregular pattern detected - may indicate response to specific triggers")
            recommendations.append("Identify and document trigger events")

        # Pattern-based recommendations
        for pattern in patterns:
            if pattern.significance == "critical":
                if pattern.pattern_type == "severity_escalation":
                    recommendations.append("Document severity escalation pattern for legal proceedings")
                elif pattern.pattern_type == "temporal_cluster":
                    recommendations.append(f"Investigate events during {pattern.start_date.strftime('%Y-%m-%d')} cluster period")

        # Event-based recommendations
        critical_events = [e for e in key_events if e.significance == "critical"]
        if len(critical_events) >= 3:
            recommendations.append("Multiple critical incidents documented - strong evidence for court")

        # Add general monitoring recommendation
        if not recommendations:
            recommendations.append("Continue systematic monitoring and documentation")

        return recommendations[:8]

    def get_timeline_visualization_data(
        self,
        summary: TimelineSummary
    ) -> Dict[str, Any]:
        """Get data formatted for timeline visualization."""
        return {
            "case_id": summary.case_id,
            "time_range": {
                "start": summary.first_detection.isoformat() if summary.first_detection else None,
                "end": summary.most_recent.isoformat() if summary.most_recent else None,
                "span_days": summary.time_span.days
            },
            "trend": summary.escalation_trend.value,
            "events": [
                {
                    "id": e.event_id,
                    "type": e.event_type.value,
                    "timestamp": e.timestamp.isoformat(),
                    "tactic": e.tactic_name,
                    "category": e.category.value if e.category else None,
                    "severity": e.severity,
                    "significance": e.significance,
                    "description": e.description
                }
                for e in summary.key_events
            ],
            "weekly_severity": summary.severity_by_week,
            "category_distribution": summary.category_distribution,
            "patterns": [
                {
                    "id": p.pattern_id,
                    "type": p.pattern_type,
                    "start": p.start_date.isoformat(),
                    "end": p.end_date.isoformat(),
                    "description": p.description,
                    "significance": p.significance
                }
                for p in summary.patterns
            ],
            "peak_period": {
                "start": summary.peak_period[0].isoformat(),
                "end": summary.peak_period[1].isoformat()
            } if summary.peak_period else None,
            "recommendations": summary.recommendations
        }
