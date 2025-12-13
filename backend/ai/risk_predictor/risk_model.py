"""
Child Safety Risk Prediction Model
Predicts risk levels and trajectories for child safety cases.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta
import math
import statistics
from collections import defaultdict


class RiskCategory(str, Enum):
    """Categories of risk factors."""
    PHYSICAL_HARM = "physical_harm"
    EMOTIONAL_ABUSE = "emotional_abuse"
    NEGLECT = "neglect"
    PARENTAL_ALIENATION = "parental_alienation"
    SUBSTANCE_ABUSE = "substance_abuse"
    DOMESTIC_VIOLENCE = "domestic_violence"
    ABDUCTION_RISK = "abduction_risk"
    MENTAL_HEALTH = "mental_health"
    SUPERVISION = "supervision"
    STABILITY = "stability"


class RiskLevel(str, Enum):
    """Risk severity levels."""
    MINIMAL = "minimal"  # 0-2
    LOW = "low"  # 2-4
    MODERATE = "moderate"  # 4-6
    HIGH = "high"  # 6-8
    CRITICAL = "critical"  # 8-10


class RiskTrajectory(str, Enum):
    """Risk trajectory over time."""
    IMPROVING = "improving"
    STABLE = "stable"
    WORSENING = "worsening"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"


@dataclass
class RiskFactor:
    """Individual risk factor with weight and evidence."""
    factor_id: str
    name: str
    category: RiskCategory
    description: str
    weight: float  # 0.0 - 1.0 importance weight
    score: float  # 0.0 - 10.0 severity score
    confidence: float  # 0.0 - 1.0 confidence in assessment
    evidence: List[str]  # Supporting evidence
    source: str  # Source of the factor
    timestamp: Optional[datetime] = None
    trend: Optional[str] = None  # increasing, stable, decreasing


@dataclass
class RiskPrediction:
    """Comprehensive risk prediction result."""
    prediction_id: str
    case_id: str
    generated_at: datetime

    # Overall risk assessment
    overall_risk_score: float  # 0-10
    risk_level: RiskLevel
    confidence: float

    # Category-specific risks
    category_risks: Dict[RiskCategory, float]

    # Risk factors
    risk_factors: List[RiskFactor]
    top_risk_factors: List[RiskFactor]  # Top 5 contributing factors

    # Trajectory analysis
    trajectory: RiskTrajectory
    trajectory_confidence: float
    predicted_risk_30_days: float
    predicted_risk_90_days: float

    # Warning signs
    warning_signs: List[str]
    protective_factors: List[str]

    # Thresholds
    alert_triggered: bool
    alert_reasons: List[str]

    # Recommendations
    immediate_actions: List[str]
    monitoring_recommendations: List[str]


# Risk factor definitions with research-based weights
RISK_FACTOR_DEFINITIONS = {
    # Physical harm factors
    "PHY001": {
        "name": "History of Physical Abuse",
        "category": RiskCategory.PHYSICAL_HARM,
        "weight": 0.95,
        "description": "Documented history of physical abuse or violence"
    },
    "PHY002": {
        "name": "Threats of Physical Violence",
        "category": RiskCategory.PHYSICAL_HARM,
        "weight": 0.85,
        "description": "Verbal or written threats of physical harm"
    },
    "PHY003": {
        "name": "Aggressive Behavior Patterns",
        "category": RiskCategory.PHYSICAL_HARM,
        "weight": 0.70,
        "description": "Pattern of aggressive behavior in communications"
    },

    # Emotional abuse factors
    "EMO001": {
        "name": "Severe Parental Alienation",
        "category": RiskCategory.PARENTAL_ALIENATION,
        "weight": 0.90,
        "description": "Documented severe alienation tactics"
    },
    "EMO002": {
        "name": "Emotional Manipulation",
        "category": RiskCategory.EMOTIONAL_ABUSE,
        "weight": 0.80,
        "description": "Pattern of emotional manipulation of child"
    },
    "EMO003": {
        "name": "Psychological Control",
        "category": RiskCategory.EMOTIONAL_ABUSE,
        "weight": 0.75,
        "description": "Coercive control tactics used on child"
    },
    "EMO004": {
        "name": "Child as Messenger",
        "category": RiskCategory.EMOTIONAL_ABUSE,
        "weight": 0.65,
        "description": "Using child to communicate between parents"
    },

    # Neglect factors
    "NEG001": {
        "name": "Basic Needs Neglect",
        "category": RiskCategory.NEGLECT,
        "weight": 0.90,
        "description": "Failure to provide basic necessities"
    },
    "NEG002": {
        "name": "Medical Neglect",
        "category": RiskCategory.NEGLECT,
        "weight": 0.85,
        "description": "Failure to provide necessary medical care"
    },
    "NEG003": {
        "name": "Educational Neglect",
        "category": RiskCategory.NEGLECT,
        "weight": 0.70,
        "description": "Failure to ensure school attendance"
    },
    "NEG004": {
        "name": "Supervision Concerns",
        "category": RiskCategory.SUPERVISION,
        "weight": 0.75,
        "description": "Inadequate supervision of child"
    },

    # Domestic violence factors
    "DV001": {
        "name": "Active Domestic Violence",
        "category": RiskCategory.DOMESTIC_VIOLENCE,
        "weight": 0.95,
        "description": "Ongoing domestic violence situation"
    },
    "DV002": {
        "name": "History of DV",
        "category": RiskCategory.DOMESTIC_VIOLENCE,
        "weight": 0.80,
        "description": "Past domestic violence incidents"
    },
    "DV003": {
        "name": "Exposure to DV",
        "category": RiskCategory.DOMESTIC_VIOLENCE,
        "weight": 0.85,
        "description": "Child witnessed domestic violence"
    },

    # Substance abuse factors
    "SUB001": {
        "name": "Active Substance Abuse",
        "category": RiskCategory.SUBSTANCE_ABUSE,
        "weight": 0.85,
        "description": "Current drug or alcohol abuse"
    },
    "SUB002": {
        "name": "Substance-Related Impairment",
        "category": RiskCategory.SUBSTANCE_ABUSE,
        "weight": 0.80,
        "description": "Impaired parenting due to substances"
    },

    # Abduction risk factors
    "ABD001": {
        "name": "Abduction Threats",
        "category": RiskCategory.ABDUCTION_RISK,
        "weight": 0.95,
        "description": "Threats to abduct or hide child"
    },
    "ABD002": {
        "name": "International Flight Risk",
        "category": RiskCategory.ABDUCTION_RISK,
        "weight": 0.90,
        "description": "Risk of taking child to another country"
    },
    "ABD003": {
        "name": "Passport/Document Concerns",
        "category": RiskCategory.ABDUCTION_RISK,
        "weight": 0.75,
        "description": "Attempts to obtain travel documents"
    },
    "ABD004": {
        "name": "Isolation Attempts",
        "category": RiskCategory.ABDUCTION_RISK,
        "weight": 0.70,
        "description": "Attempts to isolate child from other parent"
    },

    # Mental health factors
    "MH001": {
        "name": "Untreated Mental Illness",
        "category": RiskCategory.MENTAL_HEALTH,
        "weight": 0.80,
        "description": "Parent has untreated mental health condition"
    },
    "MH002": {
        "name": "Suicidal Ideation",
        "category": RiskCategory.MENTAL_HEALTH,
        "weight": 0.90,
        "description": "Parent expressed suicidal thoughts"
    },
    "MH003": {
        "name": "Delusional Beliefs",
        "category": RiskCategory.MENTAL_HEALTH,
        "weight": 0.85,
        "description": "Parent exhibits delusional thinking"
    },

    # Stability factors
    "STB001": {
        "name": "Housing Instability",
        "category": RiskCategory.STABILITY,
        "weight": 0.65,
        "description": "Unstable housing situation"
    },
    "STB002": {
        "name": "Financial Instability",
        "category": RiskCategory.STABILITY,
        "weight": 0.55,
        "description": "Significant financial problems"
    },
    "STB003": {
        "name": "Employment Instability",
        "category": RiskCategory.STABILITY,
        "weight": 0.50,
        "description": "Frequent job changes or unemployment"
    }
}

# Protective factor definitions
PROTECTIVE_FACTORS = {
    "PRO001": {"name": "Strong Support Network", "weight": 0.70},
    "PRO002": {"name": "Stable Employment", "weight": 0.50},
    "PRO003": {"name": "Engagement with Services", "weight": 0.60},
    "PRO004": {"name": "Positive Co-parenting", "weight": 0.75},
    "PRO005": {"name": "Child's Resilience", "weight": 0.65},
    "PRO006": {"name": "Therapeutic Involvement", "weight": 0.70},
    "PRO007": {"name": "Stable Housing", "weight": 0.55},
    "PRO008": {"name": "Extended Family Support", "weight": 0.60}
}


class RiskPredictor:
    """ML-based risk prediction for child safety cases."""

    # Alert thresholds
    CRITICAL_THRESHOLD = 8.0
    HIGH_THRESHOLD = 6.0
    MODERATE_THRESHOLD = 4.0

    # Category weights for overall score
    CATEGORY_WEIGHTS = {
        RiskCategory.PHYSICAL_HARM: 1.5,
        RiskCategory.DOMESTIC_VIOLENCE: 1.4,
        RiskCategory.ABDUCTION_RISK: 1.4,
        RiskCategory.MENTAL_HEALTH: 1.2,
        RiskCategory.EMOTIONAL_ABUSE: 1.1,
        RiskCategory.PARENTAL_ALIENATION: 1.1,
        RiskCategory.NEGLECT: 1.0,
        RiskCategory.SUBSTANCE_ABUSE: 1.0,
        RiskCategory.SUPERVISION: 0.9,
        RiskCategory.STABILITY: 0.8
    }

    def __init__(self):
        self.factor_definitions = RISK_FACTOR_DEFINITIONS
        self.protective_factors = PROTECTIVE_FACTORS

    def predict_risk(
        self,
        case_id: str,
        risk_factors: List[RiskFactor],
        protective_factors: Optional[List[str]] = None,
        historical_scores: Optional[List[Tuple[datetime, float]]] = None
    ) -> RiskPrediction:
        """Generate comprehensive risk prediction."""
        prediction_id = f"pred_{case_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Calculate category-specific risks
        category_risks = self._calculate_category_risks(risk_factors)

        # Calculate overall risk score
        overall_score, confidence = self._calculate_overall_risk(
            risk_factors, category_risks, protective_factors
        )

        # Determine risk level
        risk_level = self._get_risk_level(overall_score)

        # Get top risk factors
        top_factors = self._get_top_risk_factors(risk_factors)

        # Analyze trajectory
        trajectory, traj_confidence = self._analyze_trajectory(
            historical_scores or [], overall_score
        )

        # Predict future risk
        pred_30, pred_90 = self._predict_future_risk(
            overall_score, trajectory, risk_factors
        )

        # Identify warning signs
        warning_signs = self._identify_warning_signs(risk_factors, category_risks)

        # Identify protective factors present
        protective_present = self._identify_protective_factors(
            protective_factors or [], risk_factors
        )

        # Check alert thresholds
        alert_triggered, alert_reasons = self._check_alerts(
            overall_score, risk_factors, category_risks, trajectory
        )

        # Generate recommendations
        immediate_actions = self._generate_immediate_actions(
            risk_level, top_factors, alert_reasons
        )
        monitoring_recs = self._generate_monitoring_recommendations(
            risk_level, trajectory, category_risks
        )

        return RiskPrediction(
            prediction_id=prediction_id,
            case_id=case_id,
            generated_at=datetime.utcnow(),
            overall_risk_score=round(overall_score, 2),
            risk_level=risk_level,
            confidence=round(confidence, 2),
            category_risks={k: round(v, 2) for k, v in category_risks.items()},
            risk_factors=risk_factors,
            top_risk_factors=top_factors,
            trajectory=trajectory,
            trajectory_confidence=round(traj_confidence, 2),
            predicted_risk_30_days=round(pred_30, 2),
            predicted_risk_90_days=round(pred_90, 2),
            warning_signs=warning_signs,
            protective_factors=protective_present,
            alert_triggered=alert_triggered,
            alert_reasons=alert_reasons,
            immediate_actions=immediate_actions,
            monitoring_recommendations=monitoring_recs
        )

    def _calculate_category_risks(
        self,
        risk_factors: List[RiskFactor]
    ) -> Dict[RiskCategory, float]:
        """Calculate risk score for each category."""
        category_scores = defaultdict(list)

        for factor in risk_factors:
            weighted_score = factor.score * factor.weight * factor.confidence
            category_scores[factor.category].append(weighted_score)

        category_risks = {}
        for category in RiskCategory:
            scores = category_scores.get(category, [])
            if scores:
                # Use combination of max and mean for robustness
                category_risks[category] = (max(scores) * 0.6 + statistics.mean(scores) * 0.4)
            else:
                category_risks[category] = 0.0

        return category_risks

    def _calculate_overall_risk(
        self,
        risk_factors: List[RiskFactor],
        category_risks: Dict[RiskCategory, float],
        protective_factors: Optional[List[str]]
    ) -> Tuple[float, float]:
        """Calculate overall risk score and confidence."""
        if not risk_factors:
            return 0.0, 0.5

        # Weight categories
        weighted_sum = 0.0
        total_weight = 0.0

        for category, score in category_risks.items():
            weight = self.CATEGORY_WEIGHTS.get(category, 1.0)
            weighted_sum += score * weight
            total_weight += weight

        base_score = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Apply protective factor reduction
        protection_reduction = 0.0
        if protective_factors:
            for pf in protective_factors:
                if pf in self.protective_factors:
                    protection_reduction += self.protective_factors[pf]["weight"] * 0.5

        final_score = max(0, min(10, base_score - protection_reduction))

        # Calculate confidence based on number and quality of factors
        avg_confidence = statistics.mean(f.confidence for f in risk_factors)
        factor_count_confidence = min(1.0, len(risk_factors) / 5)
        confidence = (avg_confidence * 0.7 + factor_count_confidence * 0.3)

        return final_score, confidence

    def _get_risk_level(self, score: float) -> RiskLevel:
        """Convert score to risk level."""
        if score >= self.CRITICAL_THRESHOLD:
            return RiskLevel.CRITICAL
        elif score >= self.HIGH_THRESHOLD:
            return RiskLevel.HIGH
        elif score >= self.MODERATE_THRESHOLD:
            return RiskLevel.MODERATE
        elif score >= 2:
            return RiskLevel.LOW
        else:
            return RiskLevel.MINIMAL

    def _get_top_risk_factors(
        self,
        risk_factors: List[RiskFactor],
        top_n: int = 5
    ) -> List[RiskFactor]:
        """Get top contributing risk factors."""
        scored_factors = [
            (f, f.score * f.weight * f.confidence)
            for f in risk_factors
        ]
        scored_factors.sort(key=lambda x: x[1], reverse=True)
        return [f[0] for f in scored_factors[:top_n]]

    def _analyze_trajectory(
        self,
        historical_scores: List[Tuple[datetime, float]],
        current_score: float
    ) -> Tuple[RiskTrajectory, float]:
        """Analyze risk trajectory over time."""
        if len(historical_scores) < 2:
            return RiskTrajectory.UNKNOWN, 0.3

        # Sort by date
        sorted_scores = sorted(historical_scores, key=lambda x: x[0])
        scores = [s[1] for s in sorted_scores]
        scores.append(current_score)

        # Calculate trend
        n = len(scores)
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(scores)

        numerator = sum((i - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return RiskTrajectory.STABLE, 0.5

        slope = numerator / denominator
        relative_slope = slope / max(y_mean, 1)

        # Check for volatility
        if len(scores) >= 3:
            variance = statistics.variance(scores)
            cv = math.sqrt(variance) / max(y_mean, 0.1)
            if cv > 0.3:
                return RiskTrajectory.VOLATILE, 0.6

        # Determine trajectory
        confidence = min(0.9, 0.5 + len(historical_scores) * 0.1)

        if relative_slope > 0.15:
            return RiskTrajectory.WORSENING, confidence
        elif relative_slope < -0.15:
            return RiskTrajectory.IMPROVING, confidence
        else:
            return RiskTrajectory.STABLE, confidence

    def _predict_future_risk(
        self,
        current_score: float,
        trajectory: RiskTrajectory,
        risk_factors: List[RiskFactor]
    ) -> Tuple[float, float]:
        """Predict risk score 30 and 90 days out."""
        # Base prediction on trajectory
        trajectory_adjustments = {
            RiskTrajectory.WORSENING: (0.5, 1.5),
            RiskTrajectory.STABLE: (0.0, 0.0),
            RiskTrajectory.IMPROVING: (-0.5, -1.0),
            RiskTrajectory.VOLATILE: (0.3, 0.5),
            RiskTrajectory.UNKNOWN: (0.2, 0.3)
        }

        adj_30, adj_90 = trajectory_adjustments.get(
            trajectory, (0.0, 0.0)
        )

        # Adjust for high-risk factors with increasing trends
        escalating_factors = [
            f for f in risk_factors
            if f.trend == "increasing" and f.score >= 7
        ]

        if escalating_factors:
            adj_30 += 0.3 * len(escalating_factors)
            adj_90 += 0.6 * len(escalating_factors)

        pred_30 = min(10, max(0, current_score + adj_30))
        pred_90 = min(10, max(0, current_score + adj_90))

        return pred_30, pred_90

    def _identify_warning_signs(
        self,
        risk_factors: List[RiskFactor],
        category_risks: Dict[RiskCategory, float]
    ) -> List[str]:
        """Identify active warning signs."""
        warnings = []

        # High-score factors
        for factor in risk_factors:
            if factor.score >= 8:
                warnings.append(f"CRITICAL: {factor.name} (score: {factor.score})")
            elif factor.score >= 6 and factor.weight >= 0.8:
                warnings.append(f"HIGH: {factor.name}")

        # Category-level warnings
        for category, score in category_risks.items():
            if score >= 8:
                warnings.append(f"CRITICAL category risk: {category.value}")
            elif score >= 6:
                warnings.append(f"Elevated category risk: {category.value}")

        # Specific combinations
        if category_risks.get(RiskCategory.ABDUCTION_RISK, 0) >= 5:
            if category_risks.get(RiskCategory.DOMESTIC_VIOLENCE, 0) >= 5:
                warnings.append("WARNING: Combined abduction and DV risk")

        if category_risks.get(RiskCategory.MENTAL_HEALTH, 0) >= 6:
            if category_risks.get(RiskCategory.SUBSTANCE_ABUSE, 0) >= 5:
                warnings.append("WARNING: Combined mental health and substance issues")

        return warnings[:10]

    def _identify_protective_factors(
        self,
        protective_present: List[str],
        risk_factors: List[RiskFactor]
    ) -> List[str]:
        """Identify protective factors present in the case."""
        protections = []

        for pf_id in protective_present:
            if pf_id in self.protective_factors:
                protections.append(self.protective_factors[pf_id]["name"])

        # Infer from absence of certain risks
        risk_categories_present = set(f.category for f in risk_factors)

        if RiskCategory.SUBSTANCE_ABUSE not in risk_categories_present:
            protections.append("No substance abuse concerns")

        if RiskCategory.DOMESTIC_VIOLENCE not in risk_categories_present:
            protections.append("No domestic violence history")

        return protections

    def _check_alerts(
        self,
        overall_score: float,
        risk_factors: List[RiskFactor],
        category_risks: Dict[RiskCategory, float],
        trajectory: RiskTrajectory
    ) -> Tuple[bool, List[str]]:
        """Check if alert thresholds are triggered."""
        alert_triggered = False
        reasons = []

        # Overall score threshold
        if overall_score >= self.CRITICAL_THRESHOLD:
            alert_triggered = True
            reasons.append(f"Overall risk score critical: {overall_score}")
        elif overall_score >= self.HIGH_THRESHOLD:
            alert_triggered = True
            reasons.append(f"Overall risk score high: {overall_score}")

        # Category-specific thresholds
        critical_categories = [
            RiskCategory.PHYSICAL_HARM,
            RiskCategory.ABDUCTION_RISK,
            RiskCategory.DOMESTIC_VIOLENCE
        ]

        for cat in critical_categories:
            if category_risks.get(cat, 0) >= 7:
                alert_triggered = True
                reasons.append(f"Critical category threshold: {cat.value}")

        # Trajectory alert
        if trajectory == RiskTrajectory.WORSENING and overall_score >= 5:
            alert_triggered = True
            reasons.append("Risk trajectory worsening")

        # Specific factor alerts
        for factor in risk_factors:
            if factor.score >= 9 and factor.weight >= 0.9:
                alert_triggered = True
                reasons.append(f"Extreme risk factor: {factor.name}")

        return alert_triggered, reasons

    def _generate_immediate_actions(
        self,
        risk_level: RiskLevel,
        top_factors: List[RiskFactor],
        alert_reasons: List[str]
    ) -> List[str]:
        """Generate immediate action recommendations."""
        actions = []

        if risk_level == RiskLevel.CRITICAL:
            actions.append("IMMEDIATE: Contact emergency services if child in danger")
            actions.append("File emergency custody motion")
            actions.append("Request supervised visitation pending evaluation")
        elif risk_level == RiskLevel.HIGH:
            actions.append("Contact child protective services for assessment")
            actions.append("Request emergency hearing")
            actions.append("Increase monitoring of child's wellbeing")
        elif risk_level == RiskLevel.MODERATE:
            actions.append("Schedule custody evaluation")
            actions.append("Document all concerning incidents")
            actions.append("Consider family therapy referral")

        # Factor-specific actions
        for factor in top_factors:
            if factor.category == RiskCategory.ABDUCTION_RISK:
                actions.append("Review and secure travel documents")
                actions.append("Consider passport alert program")
            elif factor.category == RiskCategory.SUBSTANCE_ABUSE:
                actions.append("Request drug testing")
            elif factor.category == RiskCategory.MENTAL_HEALTH:
                actions.append("Request psychological evaluation")

        return actions[:8]

    def _generate_monitoring_recommendations(
        self,
        risk_level: RiskLevel,
        trajectory: RiskTrajectory,
        category_risks: Dict[RiskCategory, float]
    ) -> List[str]:
        """Generate monitoring recommendations."""
        recs = []

        # Frequency based on risk level
        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            recs.append("Daily check-ins with child")
            recs.append("Weekly professional supervision")
        elif risk_level == RiskLevel.MODERATE:
            recs.append("Weekly communication monitoring")
            recs.append("Bi-weekly welfare checks")
        else:
            recs.append("Regular documentation of interactions")
            recs.append("Monthly progress review")

        # Category-specific monitoring
        high_risk_cats = [k for k, v in category_risks.items() if v >= 5]

        for cat in high_risk_cats:
            if cat == RiskCategory.PARENTAL_ALIENATION:
                recs.append("Monitor child's statements about other parent")
                recs.append("Track visitation compliance")
            elif cat == RiskCategory.EMOTIONAL_ABUSE:
                recs.append("Regular child therapy sessions")
                recs.append("Monitor for behavioral changes")
            elif cat == RiskCategory.NEGLECT:
                recs.append("School attendance monitoring")
                recs.append("Medical appointment tracking")

        # Trajectory-based
        if trajectory == RiskTrajectory.WORSENING:
            recs.append("Increase monitoring frequency")
            recs.append("Establish escalation protocol")

        return recs[:8]

    def create_risk_factor(
        self,
        factor_id: str,
        score: float,
        confidence: float,
        evidence: List[str],
        source: str,
        timestamp: Optional[datetime] = None,
        trend: Optional[str] = None
    ) -> RiskFactor:
        """Create a risk factor from definition."""
        definition = self.factor_definitions.get(factor_id, {})

        return RiskFactor(
            factor_id=factor_id,
            name=definition.get("name", factor_id),
            category=definition.get("category", RiskCategory.STABILITY),
            description=definition.get("description", ""),
            weight=definition.get("weight", 0.5),
            score=min(10, max(0, score)),
            confidence=min(1, max(0, confidence)),
            evidence=evidence,
            source=source,
            timestamp=timestamp or datetime.utcnow(),
            trend=trend
        )

    def get_all_factor_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get all available risk factor definitions."""
        return self.factor_definitions.copy()

    def get_factors_by_category(
        self,
        category: RiskCategory
    ) -> List[Dict[str, Any]]:
        """Get factor definitions for a specific category."""
        return [
            {"id": fid, **fdef}
            for fid, fdef in self.factor_definitions.items()
            if fdef["category"] == category
        ]
