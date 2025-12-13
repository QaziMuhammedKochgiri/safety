"""
Outcome Correlator for Risk Prediction
Correlates risk factors with historical case outcomes.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
from datetime import datetime
import statistics
from collections import defaultdict


class OutcomeType(str, Enum):
    """Types of case outcomes."""
    CUSTODY_CHANGE = "custody_change"
    SUPERVISED_VISITATION = "supervised_visitation"
    PROTECTIVE_ORDER = "protective_order"
    CHILD_REMOVAL = "child_removal"
    REUNIFICATION = "reunification"
    NO_CHANGE = "no_change"
    ESCALATED_CONFLICT = "escalated_conflict"
    RESOLVED = "resolved"
    ABDUCTION = "abduction"
    CHILD_HARM = "child_harm"


@dataclass
class HistoricalOutcome:
    """A historical case outcome for learning."""
    case_id: str
    outcome_type: OutcomeType
    outcome_date: datetime
    risk_score_at_time: float
    risk_factors_present: List[str]
    interventions_applied: List[str]
    time_to_outcome_days: int
    severity_at_outcome: float
    notes: Optional[str] = None


@dataclass
class CorrelationResult:
    """Result of correlation analysis."""
    factor_id: str
    factor_name: str
    outcome_type: OutcomeType
    correlation_strength: float  # -1 to 1
    cases_analyzed: int
    confidence: float
    predictive_power: float  # 0-1
    avg_time_to_outcome: float  # days
    description: str


class OutcomeCorrelator:
    """Correlates risk factors with historical outcomes."""

    # Research-based outcome correlations
    BASELINE_CORRELATIONS = {
        # Physical harm correlations
        ("PHY001", OutcomeType.CHILD_HARM): {"correlation": 0.85, "avg_days": 30},
        ("PHY001", OutcomeType.PROTECTIVE_ORDER): {"correlation": 0.75, "avg_days": 14},
        ("PHY002", OutcomeType.CHILD_HARM): {"correlation": 0.70, "avg_days": 45},

        # Abduction risk correlations
        ("ABD001", OutcomeType.ABDUCTION): {"correlation": 0.80, "avg_days": 21},
        ("ABD002", OutcomeType.ABDUCTION): {"correlation": 0.75, "avg_days": 30},
        ("ABD001", OutcomeType.PROTECTIVE_ORDER): {"correlation": 0.65, "avg_days": 7},

        # Alienation correlations
        ("EMO001", OutcomeType.CUSTODY_CHANGE): {"correlation": 0.60, "avg_days": 180},
        ("EMO001", OutcomeType.SUPERVISED_VISITATION): {"correlation": 0.55, "avg_days": 90},

        # Domestic violence correlations
        ("DV001", OutcomeType.PROTECTIVE_ORDER): {"correlation": 0.85, "avg_days": 7},
        ("DV001", OutcomeType.CUSTODY_CHANGE): {"correlation": 0.70, "avg_days": 60},
        ("DV003", OutcomeType.CHILD_HARM): {"correlation": 0.55, "avg_days": 90},

        # Neglect correlations
        ("NEG001", OutcomeType.CHILD_REMOVAL): {"correlation": 0.70, "avg_days": 30},
        ("NEG002", OutcomeType.CHILD_REMOVAL): {"correlation": 0.65, "avg_days": 21},

        # Mental health correlations
        ("MH002", OutcomeType.CHILD_HARM): {"correlation": 0.60, "avg_days": 14},
        ("MH001", OutcomeType.SUPERVISED_VISITATION): {"correlation": 0.50, "avg_days": 60}
    }

    def __init__(self):
        self.historical_outcomes: List[HistoricalOutcome] = []
        self.correlation_cache: Dict[Tuple[str, OutcomeType], CorrelationResult] = {}

    def add_historical_outcome(self, outcome: HistoricalOutcome):
        """Add a historical outcome for learning."""
        self.historical_outcomes.append(outcome)
        # Invalidate cache
        self.correlation_cache.clear()

    def add_historical_outcomes_batch(self, outcomes: List[HistoricalOutcome]):
        """Add multiple historical outcomes."""
        self.historical_outcomes.extend(outcomes)
        self.correlation_cache.clear()

    def get_correlation(
        self,
        factor_id: str,
        outcome_type: OutcomeType
    ) -> CorrelationResult:
        """Get correlation between a risk factor and outcome."""
        cache_key = (factor_id, outcome_type)

        if cache_key in self.correlation_cache:
            return self.correlation_cache[cache_key]

        # Calculate from historical data if available
        relevant_outcomes = [
            o for o in self.historical_outcomes
            if factor_id in o.risk_factors_present
        ]

        if len(relevant_outcomes) >= 10:
            # Calculate actual correlation from data
            result = self._calculate_correlation(factor_id, outcome_type, relevant_outcomes)
        else:
            # Use baseline correlations
            baseline = self.BASELINE_CORRELATIONS.get(cache_key)
            if baseline:
                result = CorrelationResult(
                    factor_id=factor_id,
                    factor_name=factor_id,
                    outcome_type=outcome_type,
                    correlation_strength=baseline["correlation"],
                    cases_analyzed=len(relevant_outcomes),
                    confidence=0.6,  # Lower confidence for baseline
                    predictive_power=baseline["correlation"] * 0.8,
                    avg_time_to_outcome=baseline["avg_days"],
                    description=f"Baseline correlation from research"
                )
            else:
                # No data available
                result = CorrelationResult(
                    factor_id=factor_id,
                    factor_name=factor_id,
                    outcome_type=outcome_type,
                    correlation_strength=0.0,
                    cases_analyzed=0,
                    confidence=0.0,
                    predictive_power=0.0,
                    avg_time_to_outcome=0,
                    description="No correlation data available"
                )

        self.correlation_cache[cache_key] = result
        return result

    def _calculate_correlation(
        self,
        factor_id: str,
        outcome_type: OutcomeType,
        outcomes: List[HistoricalOutcome]
    ) -> CorrelationResult:
        """Calculate correlation from historical data."""
        # Filter to matching outcome type
        matching = [o for o in outcomes if o.outcome_type == outcome_type]
        total = len(outcomes)
        matching_count = len(matching)

        if total == 0:
            correlation = 0.0
        else:
            # Simple correlation: rate of matching outcome
            correlation = matching_count / total

        # Calculate average time to outcome
        if matching:
            avg_days = statistics.mean(o.time_to_outcome_days for o in matching)
        else:
            avg_days = 0

        # Calculate confidence based on sample size
        confidence = min(0.95, 0.5 + (total / 100) * 0.5)

        # Predictive power
        predictive_power = correlation * confidence

        return CorrelationResult(
            factor_id=factor_id,
            factor_name=factor_id,
            outcome_type=outcome_type,
            correlation_strength=round(correlation, 3),
            cases_analyzed=total,
            confidence=round(confidence, 2),
            predictive_power=round(predictive_power, 3),
            avg_time_to_outcome=round(avg_days, 1),
            description=f"Calculated from {total} historical cases"
        )

    def predict_outcome_probability(
        self,
        risk_factors: List[str],
        outcome_type: OutcomeType
    ) -> Dict[str, Any]:
        """Predict probability of a specific outcome given risk factors."""
        if not risk_factors:
            return {
                "probability": 0.0,
                "confidence": 0.0,
                "contributing_factors": [],
                "avg_time_to_outcome": None
            }

        correlations = []
        for factor in risk_factors:
            corr = self.get_correlation(factor, outcome_type)
            if corr.correlation_strength > 0:
                correlations.append(corr)

        if not correlations:
            return {
                "probability": 0.0,
                "confidence": 0.0,
                "contributing_factors": [],
                "avg_time_to_outcome": None
            }

        # Combined probability using noisy-OR model
        # P(outcome) = 1 - product(1 - P_i)
        complement_product = 1.0
        for corr in correlations:
            complement_product *= (1 - corr.correlation_strength)

        probability = 1 - complement_product

        # Weighted average confidence
        total_weight = sum(c.correlation_strength for c in correlations)
        if total_weight > 0:
            confidence = sum(
                c.confidence * c.correlation_strength
                for c in correlations
            ) / total_weight
        else:
            confidence = 0.0

        # Average time to outcome (weighted by correlation strength)
        times = [c.avg_time_to_outcome for c in correlations if c.avg_time_to_outcome > 0]
        avg_time = statistics.mean(times) if times else None

        # Contributing factors
        contributing = [
            {
                "factor_id": c.factor_id,
                "correlation": c.correlation_strength,
                "predictive_power": c.predictive_power
            }
            for c in sorted(correlations, key=lambda x: x.correlation_strength, reverse=True)
        ]

        return {
            "probability": round(probability, 3),
            "confidence": round(confidence, 2),
            "contributing_factors": contributing,
            "avg_time_to_outcome": round(avg_time, 1) if avg_time else None
        }

    def predict_all_outcomes(
        self,
        risk_factors: List[str]
    ) -> Dict[OutcomeType, Dict[str, Any]]:
        """Predict probabilities for all outcome types."""
        results = {}
        for outcome_type in OutcomeType:
            results[outcome_type] = self.predict_outcome_probability(
                risk_factors, outcome_type
            )
        return results

    def get_highest_risk_outcomes(
        self,
        risk_factors: List[str],
        top_n: int = 3
    ) -> List[Tuple[OutcomeType, Dict[str, Any]]]:
        """Get the most likely outcomes given risk factors."""
        all_predictions = self.predict_all_outcomes(risk_factors)

        sorted_outcomes = sorted(
            all_predictions.items(),
            key=lambda x: x[1]["probability"],
            reverse=True
        )

        return sorted_outcomes[:top_n]

    def analyze_intervention_effectiveness(
        self,
        intervention_type: str
    ) -> Dict[str, Any]:
        """Analyze how effective an intervention has been historically."""
        with_intervention = [
            o for o in self.historical_outcomes
            if intervention_type in o.interventions_applied
        ]

        without_intervention = [
            o for o in self.historical_outcomes
            if intervention_type not in o.interventions_applied
        ]

        if not with_intervention or not without_intervention:
            return {
                "effectiveness": None,
                "confidence": 0.0,
                "sample_size": len(with_intervention),
                "message": "Insufficient data for analysis"
            }

        # Compare negative outcome rates
        negative_outcomes = {
            OutcomeType.CHILD_HARM,
            OutcomeType.ABDUCTION,
            OutcomeType.ESCALATED_CONFLICT
        }

        neg_with = sum(
            1 for o in with_intervention
            if o.outcome_type in negative_outcomes
        )
        neg_without = sum(
            1 for o in without_intervention
            if o.outcome_type in negative_outcomes
        )

        rate_with = neg_with / len(with_intervention)
        rate_without = neg_without / len(without_intervention)

        # Effectiveness = reduction in negative outcomes
        if rate_without > 0:
            effectiveness = (rate_without - rate_with) / rate_without
        else:
            effectiveness = 0.0

        confidence = min(
            0.9,
            0.3 + min(len(with_intervention), len(without_intervention)) / 100
        )

        return {
            "effectiveness": round(effectiveness, 3),
            "confidence": round(confidence, 2),
            "sample_size_with": len(with_intervention),
            "sample_size_without": len(without_intervention),
            "negative_rate_with": round(rate_with, 3),
            "negative_rate_without": round(rate_without, 3)
        }

    def get_factor_outcome_matrix(self) -> Dict[str, Dict[str, float]]:
        """Get matrix of factor-outcome correlations."""
        matrix = {}

        # Get all unique factors
        all_factors = set()
        for outcome in self.historical_outcomes:
            all_factors.update(outcome.risk_factors_present)

        # Add baseline factors
        for key in self.BASELINE_CORRELATIONS.keys():
            all_factors.add(key[0])

        for factor in all_factors:
            matrix[factor] = {}
            for outcome_type in OutcomeType:
                corr = self.get_correlation(factor, outcome_type)
                matrix[factor][outcome_type.value] = corr.correlation_strength

        return matrix

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about historical data."""
        if not self.historical_outcomes:
            return {
                "total_outcomes": 0,
                "outcome_distribution": {},
                "avg_risk_score": None,
                "avg_time_to_outcome": None
            }

        # Outcome distribution
        distribution = defaultdict(int)
        for outcome in self.historical_outcomes:
            distribution[outcome.outcome_type.value] += 1

        # Average risk score
        avg_risk = statistics.mean(o.risk_score_at_time for o in self.historical_outcomes)

        # Average time to outcome
        avg_time = statistics.mean(o.time_to_outcome_days for o in self.historical_outcomes)

        # Most common risk factors
        factor_counts = defaultdict(int)
        for outcome in self.historical_outcomes:
            for factor in outcome.risk_factors_present:
                factor_counts[factor] += 1

        top_factors = sorted(
            factor_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        return {
            "total_outcomes": len(self.historical_outcomes),
            "outcome_distribution": dict(distribution),
            "avg_risk_score": round(avg_risk, 2),
            "avg_time_to_outcome": round(avg_time, 1),
            "most_common_factors": top_factors
        }
