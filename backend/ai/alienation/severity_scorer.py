"""
Severity Scorer for Parental Alienation
Literature-backed scoring system with evidence strength indicators.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from .tactics_database import AlienationTacticDB, ManipulationTactic, TacticCategory, TacticSeverity
from .pattern_matcher import PatternMatch, MatchConfidence


class EvidenceStrength(str, Enum):
    """Strength of evidence."""
    WEAK = "weak"  # Single instance, low confidence
    MODERATE = "moderate"  # Multiple instances or high confidence
    STRONG = "strong"  # Pattern over time with high confidence
    COMPELLING = "compelling"  # Clear pattern, multiple tactics, documentary evidence


class RiskLevel(str, Enum):
    """Overall risk level."""
    MINIMAL = "minimal"  # Score 0-2
    LOW = "low"  # Score 2-4
    MODERATE = "moderate"  # Score 4-6
    HIGH = "high"  # Score 6-8
    SEVERE = "severe"  # Score 8-10


@dataclass
class SeverityScore:
    """Comprehensive severity score with breakdown."""
    score_id: str
    overall_score: float  # 0-10
    risk_level: RiskLevel
    evidence_strength: EvidenceStrength

    # Score components
    frequency_score: float  # Based on how often tactics appear
    intensity_score: float  # Based on severity of tactics used
    pattern_score: float  # Based on escalation/consistency patterns
    diversity_score: float  # Based on variety of tactics used

    # Evidence breakdown
    tactic_scores: Dict[str, float]  # Per-tactic scores
    category_scores: Dict[str, float]  # Per-category scores
    temporal_trend: str  # escalating, stable, de-escalating

    # Supporting data
    total_matches: int
    unique_tactics: int
    time_span_days: int
    messages_analyzed: int

    # Confidence in assessment
    assessment_confidence: float
    confidence_factors: List[str]

    # Recommendations
    recommendations: List[str]
    urgency_level: str


@dataclass
class TacticScoreDetail:
    """Detailed score for a specific tactic."""
    tactic_id: str
    tactic_name: str
    category: TacticCategory
    base_severity: int
    frequency: int
    weighted_score: float
    evidence_quality: EvidenceStrength
    example_quotes: List[str]
    timestamps: List[datetime]
    trend: str  # increasing, stable, decreasing


class SeverityScorer:
    """Literature-backed severity scoring system."""

    # Weights based on research literature
    CATEGORY_WEIGHTS = {
        TacticCategory.FALSE_ALLEGATIONS: 1.5,  # Highest impact
        TacticCategory.CHILD_WEAPONIZATION: 1.4,
        TacticCategory.EMOTIONAL_MANIPULATION: 1.3,
        TacticCategory.IDENTITY_ERASURE: 1.2,
        TacticCategory.INTERFERENCE: 1.1,
        TacticCategory.DENIGRATION: 1.0,
        TacticCategory.INFORMATION_CONTROL: 0.9,
        TacticCategory.GATEKEEPING: 1.0,
        TacticCategory.PSYCHOLOGICAL_CONTROL: 1.3,
        TacticCategory.LEGAL_ABUSE: 1.1
    }

    # Frequency multipliers
    FREQUENCY_MULTIPLIERS = {
        1: 0.6,    # Single instance
        2: 0.8,    # Two instances
        3: 1.0,    # Three instances
        5: 1.2,    # Five instances
        10: 1.4,   # Ten instances
        20: 1.5,   # Twenty+ instances
    }

    def __init__(self, db: Optional[AlienationTacticDB] = None):
        self.db = db or AlienationTacticDB()

    def calculate_severity(
        self,
        matches: List[PatternMatch],
        messages_analyzed: int = 0,
        time_span_days: int = 0
    ) -> SeverityScore:
        """Calculate comprehensive severity score from matches."""
        if not matches:
            return self._create_minimal_score(messages_analyzed)

        # Group matches by tactic and category
        tactic_matches = defaultdict(list)
        category_matches = defaultdict(list)
        timestamps = []

        for match in matches:
            tactic_matches[match.tactic_id].append(match)
            category_matches[match.category].append(match)
            if match.timestamp:
                timestamps.append(match.timestamp)

        # Calculate component scores
        frequency_score = self._calculate_frequency_score(tactic_matches, messages_analyzed)
        intensity_score = self._calculate_intensity_score(matches)
        pattern_score = self._calculate_pattern_score(timestamps, tactic_matches)
        diversity_score = self._calculate_diversity_score(tactic_matches, category_matches)

        # Calculate per-tactic and per-category scores
        tactic_scores = self._calculate_tactic_scores(tactic_matches)
        category_scores = self._calculate_category_scores(category_matches)

        # Determine temporal trend
        temporal_trend = self._determine_temporal_trend(timestamps, matches)

        # Calculate overall score
        overall_score = self._calculate_overall_score(
            frequency_score, intensity_score, pattern_score, diversity_score
        )

        # Determine risk level and evidence strength
        risk_level = self._get_risk_level(overall_score)
        evidence_strength = self._assess_evidence_strength(matches, tactic_matches, timestamps)

        # Calculate assessment confidence
        assessment_confidence, confidence_factors = self._calculate_assessment_confidence(
            matches, messages_analyzed, time_span_days
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            overall_score, risk_level, category_matches, temporal_trend
        )

        # Determine urgency
        urgency_level = self._determine_urgency(overall_score, temporal_trend, evidence_strength)

        return SeverityScore(
            score_id=f"sev_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            overall_score=round(overall_score, 2),
            risk_level=risk_level,
            evidence_strength=evidence_strength,
            frequency_score=round(frequency_score, 2),
            intensity_score=round(intensity_score, 2),
            pattern_score=round(pattern_score, 2),
            diversity_score=round(diversity_score, 2),
            tactic_scores=tactic_scores,
            category_scores=category_scores,
            temporal_trend=temporal_trend,
            total_matches=len(matches),
            unique_tactics=len(tactic_matches),
            time_span_days=time_span_days,
            messages_analyzed=messages_analyzed,
            assessment_confidence=round(assessment_confidence, 2),
            confidence_factors=confidence_factors,
            recommendations=recommendations,
            urgency_level=urgency_level
        )

    def _create_minimal_score(self, messages_analyzed: int) -> SeverityScore:
        """Create a minimal score when no matches found."""
        return SeverityScore(
            score_id=f"sev_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            overall_score=0.0,
            risk_level=RiskLevel.MINIMAL,
            evidence_strength=EvidenceStrength.WEAK,
            frequency_score=0.0,
            intensity_score=0.0,
            pattern_score=0.0,
            diversity_score=0.0,
            tactic_scores={},
            category_scores={},
            temporal_trend="stable",
            total_matches=0,
            unique_tactics=0,
            time_span_days=0,
            messages_analyzed=messages_analyzed,
            assessment_confidence=1.0 if messages_analyzed > 50 else 0.5,
            confidence_factors=["No alienation patterns detected"],
            recommendations=["Continue monitoring", "No immediate concerns identified"],
            urgency_level="low"
        )

    def _calculate_frequency_score(
        self,
        tactic_matches: Dict[str, List[PatternMatch]],
        messages_analyzed: int
    ) -> float:
        """Calculate score based on frequency of tactics."""
        if not tactic_matches or messages_analyzed == 0:
            return 0.0

        total_matches = sum(len(m) for m in tactic_matches.values())
        rate = total_matches / messages_analyzed

        # Convert rate to score (0-10)
        # 0% = 0, 5% = 5, 10%+ = 10
        score = min(10, rate * 100)

        return score

    def _calculate_intensity_score(self, matches: List[PatternMatch]) -> float:
        """Calculate score based on severity of detected tactics."""
        if not matches:
            return 0.0

        # Weight by confidence
        weighted_severities = []
        for match in matches:
            weighted = match.severity_score * match.confidence
            weighted_severities.append(weighted)

        avg_severity = statistics.mean(weighted_severities)
        return avg_severity

    def _calculate_pattern_score(
        self,
        timestamps: List[datetime],
        tactic_matches: Dict[str, List[PatternMatch]]
    ) -> float:
        """Calculate score based on patterns over time."""
        score = 0.0

        # Consistency bonus: same tactics appearing repeatedly
        for tactic_id, matches in tactic_matches.items():
            if len(matches) >= 3:
                score += 1.0
            if len(matches) >= 5:
                score += 1.0
            if len(matches) >= 10:
                score += 1.0

        # Temporal spread bonus: patterns over extended time
        if len(timestamps) >= 2:
            timestamps_sorted = sorted(timestamps)
            span = (timestamps_sorted[-1] - timestamps_sorted[0]).days
            if span >= 7:
                score += 1.0
            if span >= 30:
                score += 1.0
            if span >= 90:
                score += 1.0

        return min(10, score)

    def _calculate_diversity_score(
        self,
        tactic_matches: Dict[str, List[PatternMatch]],
        category_matches: Dict[TacticCategory, List[PatternMatch]]
    ) -> float:
        """Calculate score based on variety of tactics used."""
        # More diverse tactics indicate more systematic alienation
        unique_tactics = len(tactic_matches)
        unique_categories = len(category_matches)

        tactic_score = min(5, unique_tactics)  # Up to 5 for tactic variety
        category_score = min(5, unique_categories * 1.25)  # Up to 5 for category variety

        return tactic_score + category_score

    def _calculate_tactic_scores(
        self,
        tactic_matches: Dict[str, List[PatternMatch]]
    ) -> Dict[str, float]:
        """Calculate individual scores for each tactic."""
        scores = {}

        for tactic_id, matches in tactic_matches.items():
            tactic = self.db.get_tactic(tactic_id)
            if not tactic:
                continue

            # Base score from tactic severity
            base = tactic.severity_base

            # Frequency multiplier
            freq_mult = self._get_frequency_multiplier(len(matches))

            # Confidence modifier
            avg_confidence = statistics.mean(m.confidence for m in matches)

            # Category weight
            category_weight = self.CATEGORY_WEIGHTS.get(tactic.category, 1.0)

            final_score = base * freq_mult * avg_confidence * category_weight
            scores[tactic_id] = round(min(10, final_score), 2)

        return scores

    def _calculate_category_scores(
        self,
        category_matches: Dict[TacticCategory, List[PatternMatch]]
    ) -> Dict[str, float]:
        """Calculate scores for each category."""
        scores = {}

        for category, matches in category_matches.items():
            # Average severity of matches in category
            avg_severity = statistics.mean(m.severity_score for m in matches)

            # Frequency in category
            freq_mult = self._get_frequency_multiplier(len(matches))

            # Category weight
            weight = self.CATEGORY_WEIGHTS.get(category, 1.0)

            score = avg_severity * freq_mult * weight
            scores[category.value] = round(min(10, score), 2)

        return scores

    def _get_frequency_multiplier(self, count: int) -> float:
        """Get frequency multiplier for a count."""
        for threshold, mult in sorted(self.FREQUENCY_MULTIPLIERS.items(), reverse=True):
            if count >= threshold:
                return mult
        return 0.5

    def _determine_temporal_trend(
        self,
        timestamps: List[datetime],
        matches: List[PatternMatch]
    ) -> str:
        """Determine if alienation is escalating, stable, or de-escalating."""
        if len(timestamps) < 4:
            return "insufficient_data"

        # Sort matches by timestamp
        timed_matches = [(m, m.timestamp) for m in matches if m.timestamp]
        if len(timed_matches) < 4:
            return "insufficient_data"

        timed_matches.sort(key=lambda x: x[1])

        # Split into two halves
        mid = len(timed_matches) // 2
        first_half = timed_matches[:mid]
        second_half = timed_matches[mid:]

        # Compare average severity
        first_avg = statistics.mean(m[0].severity_score * m[0].confidence for m in first_half)
        second_avg = statistics.mean(m[0].severity_score * m[0].confidence for m in second_half)

        # Compare frequency (matches per day)
        first_days = max(1, (first_half[-1][1] - first_half[0][1]).days)
        second_days = max(1, (second_half[-1][1] - second_half[0][1]).days)

        first_rate = len(first_half) / first_days
        second_rate = len(second_half) / second_days

        severity_change = (second_avg - first_avg) / max(first_avg, 0.1)
        rate_change = (second_rate - first_rate) / max(first_rate, 0.1)

        combined_change = (severity_change + rate_change) / 2

        if combined_change > 0.2:
            return "escalating"
        elif combined_change < -0.2:
            return "de_escalating"
        else:
            return "stable"

    def _calculate_overall_score(
        self,
        frequency: float,
        intensity: float,
        pattern: float,
        diversity: float
    ) -> float:
        """Calculate weighted overall score."""
        # Weights for each component
        weights = {
            "frequency": 0.2,
            "intensity": 0.35,
            "pattern": 0.25,
            "diversity": 0.2
        }

        overall = (
            frequency * weights["frequency"] +
            intensity * weights["intensity"] +
            pattern * weights["pattern"] +
            diversity * weights["diversity"]
        )

        return min(10, overall)

    def _get_risk_level(self, score: float) -> RiskLevel:
        """Convert score to risk level."""
        if score < 2:
            return RiskLevel.MINIMAL
        elif score < 4:
            return RiskLevel.LOW
        elif score < 6:
            return RiskLevel.MODERATE
        elif score < 8:
            return RiskLevel.HIGH
        else:
            return RiskLevel.SEVERE

    def _assess_evidence_strength(
        self,
        matches: List[PatternMatch],
        tactic_matches: Dict[str, List[PatternMatch]],
        timestamps: List[datetime]
    ) -> EvidenceStrength:
        """Assess overall strength of evidence."""
        # Factors that strengthen evidence
        factors = 0

        # Multiple high-confidence matches
        high_conf_matches = [m for m in matches if m.confidence >= 0.8]
        if len(high_conf_matches) >= 5:
            factors += 2
        elif len(high_conf_matches) >= 2:
            factors += 1

        # Multiple tactics detected
        if len(tactic_matches) >= 5:
            factors += 2
        elif len(tactic_matches) >= 3:
            factors += 1

        # Extended time period
        if timestamps:
            span = (max(timestamps) - min(timestamps)).days
            if span >= 90:
                factors += 2
            elif span >= 30:
                factors += 1

        # Severe tactics present
        severe_count = sum(1 for m in matches if m.severity_score >= 8)
        if severe_count >= 3:
            factors += 2
        elif severe_count >= 1:
            factors += 1

        if factors >= 6:
            return EvidenceStrength.COMPELLING
        elif factors >= 4:
            return EvidenceStrength.STRONG
        elif factors >= 2:
            return EvidenceStrength.MODERATE
        else:
            return EvidenceStrength.WEAK

    def _calculate_assessment_confidence(
        self,
        matches: List[PatternMatch],
        messages_analyzed: int,
        time_span_days: int
    ) -> Tuple[float, List[str]]:
        """Calculate confidence in the assessment."""
        confidence = 0.5  # Base confidence
        factors = []

        # More messages analyzed = higher confidence
        if messages_analyzed >= 100:
            confidence += 0.2
            factors.append(f"Large sample size ({messages_analyzed} messages)")
        elif messages_analyzed >= 50:
            confidence += 0.1
            factors.append(f"Moderate sample size ({messages_analyzed} messages)")

        # Longer time span = higher confidence
        if time_span_days >= 90:
            confidence += 0.15
            factors.append(f"Extended observation period ({time_span_days} days)")
        elif time_span_days >= 30:
            confidence += 0.1
            factors.append(f"Moderate observation period ({time_span_days} days)")

        # High-confidence matches boost overall confidence
        avg_match_conf = statistics.mean(m.confidence for m in matches) if matches else 0.5
        if avg_match_conf >= 0.8:
            confidence += 0.1
            factors.append("High-confidence pattern matches")

        # Multiple corroborating tactics
        unique_tactics = len(set(m.tactic_id for m in matches))
        if unique_tactics >= 5:
            confidence += 0.1
            factors.append(f"Multiple corroborating tactics ({unique_tactics} types)")

        return min(0.95, confidence), factors

    def _generate_recommendations(
        self,
        overall_score: float,
        risk_level: RiskLevel,
        category_matches: Dict[TacticCategory, List[PatternMatch]],
        temporal_trend: str
    ) -> List[str]:
        """Generate recommendations based on assessment."""
        recommendations = []

        # General recommendations based on risk level
        if risk_level == RiskLevel.SEVERE:
            recommendations.append("Immediate professional intervention recommended")
            recommendations.append("Consider emergency custody modification motion")
            recommendations.append("Document all evidence for court proceedings")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("Seek evaluation by child custody evaluator")
            recommendations.append("Consider family therapy with alienation-informed therapist")
            recommendations.append("Maintain detailed documentation of all incidents")
        elif risk_level == RiskLevel.MODERATE:
            recommendations.append("Monitor situation closely for escalation")
            recommendations.append("Consider mediation with trained professional")
            recommendations.append("Document concerning communications")
        elif risk_level == RiskLevel.LOW:
            recommendations.append("Continue monitoring communications")
            recommendations.append("Encourage healthy co-parenting communication")

        # Category-specific recommendations
        if TacticCategory.FALSE_ALLEGATIONS in category_matches:
            recommendations.append("Document timeline of allegations carefully")
            recommendations.append("Consider polygraph examination if appropriate")

        if TacticCategory.INTERFERENCE in category_matches:
            recommendations.append("Keep detailed log of visitation compliance")
            recommendations.append("Consider motion to enforce visitation order")

        if TacticCategory.EMOTIONAL_MANIPULATION in category_matches:
            recommendations.append("Individual therapy for child recommended")
            recommendations.append("Reunification therapy may be appropriate")

        # Trend-based recommendations
        if temporal_trend == "escalating":
            recommendations.append("URGENT: Situation is escalating - immediate action needed")

        return recommendations[:8]  # Limit to top 8

    def _determine_urgency(
        self,
        overall_score: float,
        temporal_trend: str,
        evidence_strength: EvidenceStrength
    ) -> str:
        """Determine urgency level for action."""
        if overall_score >= 8 or temporal_trend == "escalating":
            return "critical"
        elif overall_score >= 6 or evidence_strength == EvidenceStrength.COMPELLING:
            return "high"
        elif overall_score >= 4:
            return "medium"
        else:
            return "low"

    def get_tactic_details(
        self,
        matches: List[PatternMatch]
    ) -> List[TacticScoreDetail]:
        """Get detailed scoring information for each tactic."""
        tactic_matches = defaultdict(list)
        for match in matches:
            tactic_matches[match.tactic_id].append(match)

        details = []
        for tactic_id, tactic_match_list in tactic_matches.items():
            tactic = self.db.get_tactic(tactic_id)
            if not tactic:
                continue

            timestamps = [m.timestamp for m in tactic_match_list if m.timestamp]
            quotes = [m.matched_text for m in tactic_match_list[:5]]  # Top 5 quotes

            # Calculate trend for this tactic
            if len(timestamps) >= 4:
                timestamps.sort()
                mid = len(timestamps) // 2
                first_count = mid
                second_count = len(timestamps) - mid
                first_days = max(1, (timestamps[mid-1] - timestamps[0]).days)
                second_days = max(1, (timestamps[-1] - timestamps[mid]).days)
                first_rate = first_count / first_days
                second_rate = second_count / second_days
                if second_rate > first_rate * 1.2:
                    trend = "increasing"
                elif second_rate < first_rate * 0.8:
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"

            # Calculate weighted score
            freq_mult = self._get_frequency_multiplier(len(tactic_match_list))
            avg_conf = statistics.mean(m.confidence for m in tactic_match_list)
            weighted_score = tactic.severity_base * freq_mult * avg_conf

            # Assess evidence quality for this tactic
            if len(tactic_match_list) >= 5 and avg_conf >= 0.8:
                evidence_quality = EvidenceStrength.COMPELLING
            elif len(tactic_match_list) >= 3 and avg_conf >= 0.6:
                evidence_quality = EvidenceStrength.STRONG
            elif len(tactic_match_list) >= 2:
                evidence_quality = EvidenceStrength.MODERATE
            else:
                evidence_quality = EvidenceStrength.WEAK

            detail = TacticScoreDetail(
                tactic_id=tactic_id,
                tactic_name=tactic.name,
                category=tactic.category,
                base_severity=tactic.severity_base,
                frequency=len(tactic_match_list),
                weighted_score=round(weighted_score, 2),
                evidence_quality=evidence_quality,
                example_quotes=quotes,
                timestamps=timestamps,
                trend=trend
            )
            details.append(detail)

        # Sort by weighted score
        details.sort(key=lambda d: d.weighted_score, reverse=True)
        return details
