"""
Feature Extractor for Risk Prediction
Extracts features from case data for ML risk prediction.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


@dataclass
class CommunicationFeatures:
    """Features extracted from communications."""
    total_messages: int
    message_frequency: float  # per day
    avg_message_length: float
    sentiment_score: float  # -1 to 1
    hostility_score: float  # 0-10
    threat_count: int
    profanity_count: int
    manipulation_indicators: int
    accusation_count: int
    child_mention_frequency: float


@dataclass
class BehavioralFeatures:
    """Features from behavioral patterns."""
    visitation_compliance_rate: float  # 0-1
    communication_responsiveness: float  # 0-1
    court_order_violations: int
    documented_incidents: int
    escalation_pattern: bool
    cooperation_score: float  # 0-10
    consistency_score: float  # 0-10


@dataclass
class TemporalFeatures:
    """Time-based features."""
    case_duration_days: int
    incident_frequency: float  # per week
    recent_incident_spike: bool
    time_since_last_incident: int  # days
    seasonal_pattern: Optional[str]
    weekday_incident_rate: float
    weekend_incident_rate: float


@dataclass
class CaseFeatures:
    """Complete feature set for a case."""
    case_id: str
    extraction_date: datetime
    communication: CommunicationFeatures
    behavioral: BehavioralFeatures
    temporal: TemporalFeatures

    # Derived features
    overall_hostility: float
    escalation_risk: float
    compliance_risk: float

    # Metadata
    data_completeness: float  # 0-1
    feature_confidence: float


class FeatureExtractor:
    """Extracts features from case data for risk prediction."""

    def __init__(self):
        self.hostile_keywords = [
            "hate", "kill", "destroy", "never see", "take away",
            "regret", "suffer", "punish", "revenge", "eliminate"
        ]
        self.threat_patterns = [
            "i will", "you'll see", "wait until", "gonna make",
            "you'll regret", "i swear", "better watch"
        ]
        self.manipulation_patterns = [
            "if you loved", "your fault", "because of you",
            "don't tell", "our secret", "choose"
        ]

    def extract_features(
        self,
        case_id: str,
        messages: List[Dict[str, Any]],
        incidents: List[Dict[str, Any]],
        visitation_records: Optional[List[Dict[str, Any]]] = None,
        court_orders: Optional[List[Dict[str, Any]]] = None
    ) -> CaseFeatures:
        """Extract all features from case data."""
        # Extract communication features
        comm_features = self._extract_communication_features(messages)

        # Extract behavioral features
        behav_features = self._extract_behavioral_features(
            incidents, visitation_records, court_orders
        )

        # Extract temporal features
        temp_features = self._extract_temporal_features(messages, incidents)

        # Calculate derived features
        overall_hostility = self._calculate_overall_hostility(comm_features, incidents)
        escalation_risk = self._calculate_escalation_risk(temp_features, incidents)
        compliance_risk = self._calculate_compliance_risk(behav_features)

        # Calculate data completeness
        data_completeness = self._calculate_data_completeness(
            messages, incidents, visitation_records
        )

        # Calculate feature confidence
        feature_confidence = data_completeness * 0.7 + 0.3 * min(1.0, len(messages) / 100)

        return CaseFeatures(
            case_id=case_id,
            extraction_date=datetime.utcnow(),
            communication=comm_features,
            behavioral=behav_features,
            temporal=temp_features,
            overall_hostility=round(overall_hostility, 2),
            escalation_risk=round(escalation_risk, 2),
            compliance_risk=round(compliance_risk, 2),
            data_completeness=round(data_completeness, 2),
            feature_confidence=round(feature_confidence, 2)
        )

    def _extract_communication_features(
        self,
        messages: List[Dict[str, Any]]
    ) -> CommunicationFeatures:
        """Extract features from messages."""
        if not messages:
            return CommunicationFeatures(
                total_messages=0,
                message_frequency=0,
                avg_message_length=0,
                sentiment_score=0,
                hostility_score=0,
                threat_count=0,
                profanity_count=0,
                manipulation_indicators=0,
                accusation_count=0,
                child_mention_frequency=0
            )

        total = len(messages)

        # Calculate frequency
        timestamps = [m.get("timestamp") for m in messages if m.get("timestamp")]
        if len(timestamps) >= 2:
            if isinstance(timestamps[0], str):
                timestamps = [datetime.fromisoformat(t.replace('Z', '+00:00')) for t in timestamps]
            span_days = max(1, (max(timestamps) - min(timestamps)).days)
            frequency = total / span_days
        else:
            frequency = 0

        # Message lengths
        lengths = [len(m.get("content", m.get("body", ""))) for m in messages]
        avg_length = statistics.mean(lengths) if lengths else 0

        # Content analysis
        all_text = " ".join(
            m.get("content", m.get("body", "")).lower()
            for m in messages
        )

        # Count hostile keywords
        hostility_count = sum(1 for kw in self.hostile_keywords if kw in all_text)
        hostility_score = min(10, hostility_count * 1.5)

        # Count threats
        threat_count = sum(1 for p in self.threat_patterns if p in all_text)

        # Count manipulation indicators
        manipulation_count = sum(1 for p in self.manipulation_patterns if p in all_text)

        # Simple sentiment estimation
        positive_words = ["love", "happy", "good", "great", "thank", "please"]
        negative_words = ["hate", "bad", "terrible", "awful", "angry", "sad"]
        pos_count = sum(1 for w in positive_words if w in all_text)
        neg_count = sum(1 for w in negative_words if w in all_text)
        total_sentiment = pos_count + neg_count
        sentiment = (pos_count - neg_count) / max(1, total_sentiment)

        # Child mentions
        child_keywords = ["child", "kid", "son", "daughter", "baby", "children"]
        child_mentions = sum(all_text.count(kw) for kw in child_keywords)
        child_frequency = child_mentions / total if total > 0 else 0

        return CommunicationFeatures(
            total_messages=total,
            message_frequency=round(frequency, 2),
            avg_message_length=round(avg_length, 1),
            sentiment_score=round(sentiment, 2),
            hostility_score=round(hostility_score, 2),
            threat_count=threat_count,
            profanity_count=0,  # Would need profanity list
            manipulation_indicators=manipulation_count,
            accusation_count=all_text.count("you ") + all_text.count("your "),
            child_mention_frequency=round(child_frequency, 3)
        )

    def _extract_behavioral_features(
        self,
        incidents: List[Dict[str, Any]],
        visitation_records: Optional[List[Dict[str, Any]]],
        court_orders: Optional[List[Dict[str, Any]]]
    ) -> BehavioralFeatures:
        """Extract behavioral features."""
        # Visitation compliance
        if visitation_records:
            complied = sum(1 for v in visitation_records if v.get("complied", True))
            compliance_rate = complied / len(visitation_records)
        else:
            compliance_rate = 1.0  # Assume compliant if no records

        # Court order violations
        violations = 0
        if court_orders:
            violations = sum(1 for o in court_orders if o.get("violated", False))

        # Incident analysis
        documented_incidents = len(incidents)

        # Check for escalation pattern
        if len(incidents) >= 3:
            severities = [i.get("severity", 5) for i in incidents[-5:]]
            escalation_pattern = severities[-1] > severities[0] if len(severities) >= 2 else False
        else:
            escalation_pattern = False

        # Cooperation and consistency scores (would come from evaluations)
        cooperation_score = 5.0  # Default middle
        consistency_score = 5.0

        return BehavioralFeatures(
            visitation_compliance_rate=round(compliance_rate, 2),
            communication_responsiveness=0.5,  # Would need response time analysis
            court_order_violations=violations,
            documented_incidents=documented_incidents,
            escalation_pattern=escalation_pattern,
            cooperation_score=cooperation_score,
            consistency_score=consistency_score
        )

    def _extract_temporal_features(
        self,
        messages: List[Dict[str, Any]],
        incidents: List[Dict[str, Any]]
    ) -> TemporalFeatures:
        """Extract time-based features."""
        # Case duration
        all_timestamps = []

        for m in messages:
            ts = m.get("timestamp")
            if ts:
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                all_timestamps.append(ts)

        for i in incidents:
            ts = i.get("timestamp") or i.get("date")
            if ts:
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                all_timestamps.append(ts)

        if all_timestamps:
            duration = (max(all_timestamps) - min(all_timestamps)).days
            time_since_last = (datetime.utcnow() - max(all_timestamps)).days
        else:
            duration = 0
            time_since_last = 999

        # Incident frequency
        weeks = max(1, duration / 7)
        incident_frequency = len(incidents) / weeks if incidents else 0

        # Check for recent spike
        if incidents and len(incidents) >= 3:
            recent = [i for i in incidents if self._is_recent(i.get("timestamp"), 14)]
            older = [i for i in incidents if not self._is_recent(i.get("timestamp"), 14)]
            recent_spike = len(recent) > len(older) / max(1, duration / 14 - 1)
        else:
            recent_spike = False

        # Weekday vs weekend analysis
        weekday_incidents = 0
        weekend_incidents = 0

        for i in incidents:
            ts = i.get("timestamp")
            if ts:
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                if ts.weekday() < 5:
                    weekday_incidents += 1
                else:
                    weekend_incidents += 1

        total_incidents = weekday_incidents + weekend_incidents
        weekday_rate = weekday_incidents / max(1, total_incidents)
        weekend_rate = weekend_incidents / max(1, total_incidents)

        return TemporalFeatures(
            case_duration_days=duration,
            incident_frequency=round(incident_frequency, 2),
            recent_incident_spike=recent_spike,
            time_since_last_incident=time_since_last,
            seasonal_pattern=None,
            weekday_incident_rate=round(weekday_rate, 2),
            weekend_incident_rate=round(weekend_rate, 2)
        )

    def _is_recent(self, timestamp: Any, days: int) -> bool:
        """Check if timestamp is within recent days."""
        if not timestamp:
            return False
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return (datetime.utcnow() - timestamp).days <= days

    def _calculate_overall_hostility(
        self,
        comm_features: CommunicationFeatures,
        incidents: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall hostility score."""
        comm_hostility = comm_features.hostility_score
        threat_factor = min(5, comm_features.threat_count * 1.5)
        manipulation_factor = min(3, comm_features.manipulation_indicators * 0.5)

        # Incident severity contribution
        if incidents:
            incident_severities = [i.get("severity", 5) for i in incidents]
            incident_factor = statistics.mean(incident_severities) * 0.3
        else:
            incident_factor = 0

        return min(10, comm_hostility + threat_factor + manipulation_factor + incident_factor)

    def _calculate_escalation_risk(
        self,
        temp_features: TemporalFeatures,
        incidents: List[Dict[str, Any]]
    ) -> float:
        """Calculate risk of escalation."""
        risk = 0.0

        # Recent spike increases risk
        if temp_features.recent_incident_spike:
            risk += 3.0

        # High frequency increases risk
        if temp_features.incident_frequency > 1:  # More than 1 per week
            risk += 2.0
        elif temp_features.incident_frequency > 0.5:
            risk += 1.0

        # Short time since last incident
        if temp_features.time_since_last_incident < 7:
            risk += 2.0
        elif temp_features.time_since_last_incident < 14:
            risk += 1.0

        # Check severity trend in incidents
        if len(incidents) >= 3:
            severities = [i.get("severity", 5) for i in incidents]
            if severities[-1] > statistics.mean(severities):
                risk += 2.0

        return min(10, risk)

    def _calculate_compliance_risk(
        self,
        behav_features: BehavioralFeatures
    ) -> float:
        """Calculate risk based on compliance history."""
        risk = 0.0

        # Low visitation compliance
        if behav_features.visitation_compliance_rate < 0.5:
            risk += 4.0
        elif behav_features.visitation_compliance_rate < 0.8:
            risk += 2.0

        # Court order violations
        risk += min(4, behav_features.court_order_violations * 2)

        # Escalation pattern
        if behav_features.escalation_pattern:
            risk += 2.0

        return min(10, risk)

    def _calculate_data_completeness(
        self,
        messages: List[Dict[str, Any]],
        incidents: List[Dict[str, Any]],
        visitation_records: Optional[List[Dict[str, Any]]]
    ) -> float:
        """Calculate completeness of available data."""
        completeness = 0.0

        # Messages contribute 40%
        if len(messages) >= 50:
            completeness += 0.4
        elif len(messages) >= 20:
            completeness += 0.3
        elif len(messages) >= 5:
            completeness += 0.2
        elif messages:
            completeness += 0.1

        # Incidents contribute 30%
        if len(incidents) >= 10:
            completeness += 0.3
        elif len(incidents) >= 5:
            completeness += 0.2
        elif incidents:
            completeness += 0.1

        # Visitation records contribute 30%
        if visitation_records:
            if len(visitation_records) >= 10:
                completeness += 0.3
            elif len(visitation_records) >= 5:
                completeness += 0.2
            else:
                completeness += 0.1

        return completeness
