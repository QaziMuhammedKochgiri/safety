"""
Risk Explainer for Explainable AI
Provides human-readable explanations for risk predictions.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


class ExplanationType(str, Enum):
    """Types of explanations."""
    FACTOR_CONTRIBUTION = "factor_contribution"
    THRESHOLD_BREACH = "threshold_breach"
    PATTERN_DETECTION = "pattern_detection"
    COMPARISON = "comparison"
    TREND_ANALYSIS = "trend_analysis"
    COUNTERFACTUAL = "counterfactual"


@dataclass
class FeatureContribution:
    """Contribution of a feature to the prediction."""
    feature_name: str
    feature_value: Any
    contribution: float  # Positive = increases risk, negative = decreases
    importance_rank: int
    explanation: str
    evidence: List[str]


@dataclass
class Explanation:
    """A single explanation for a prediction."""
    explanation_id: str
    explanation_type: ExplanationType
    title: str
    description: str
    confidence: float
    supporting_data: Dict[str, Any]
    visualization_hint: Optional[str] = None


@dataclass
class RiskExplanation:
    """Complete explanation for a risk prediction."""
    prediction_id: str
    case_id: str
    generated_at: datetime

    # Summary
    summary: str
    risk_level_explanation: str

    # Detailed explanations
    explanations: List[Explanation]
    feature_contributions: List[FeatureContribution]

    # Specific insights
    top_risk_drivers: List[str]
    protective_factors: List[str]
    what_if_scenarios: List[Dict[str, Any]]

    # Plain language summary
    plain_language_summary: str
    key_takeaways: List[str]


class RiskExplainer:
    """Generates explanations for risk predictions."""

    RISK_LEVEL_DESCRIPTIONS = {
        "critical": "The highest level of concern, indicating immediate danger to the child",
        "high": "Significant risk factors present that require urgent attention",
        "moderate": "Notable concerns that warrant monitoring and intervention",
        "low": "Minor concerns present but situation is relatively stable",
        "minimal": "Few to no significant risk factors identified"
    }

    FACTOR_EXPLANATIONS = {
        "PHY001": "History of physical abuse is one of the strongest predictors of future harm",
        "PHY002": "Verbal threats of violence often precede actual physical incidents",
        "EMO001": "Severe parental alienation can cause lasting psychological damage",
        "EMO002": "Emotional manipulation undermines the child's sense of security",
        "ABD001": "Abduction threats require immediate protective measures",
        "ABD002": "International flight risk significantly complicates recovery efforts",
        "DV001": "Active domestic violence creates an unsafe environment",
        "DV003": "Witnessing violence is traumatic and affects child development",
        "NEG001": "Basic needs neglect threatens the child's physical wellbeing",
        "SUB001": "Active substance abuse impairs parenting ability",
        "MH001": "Untreated mental illness may affect judgment and behavior",
        "MH002": "Suicidal ideation in a parent is a serious safety concern"
    }

    def __init__(self):
        pass

    def explain_prediction(
        self,
        prediction_id: str,
        case_id: str,
        overall_score: float,
        risk_level: str,
        risk_factors: List[Dict[str, Any]],
        category_scores: Dict[str, float],
        trajectory: str,
        protective_factors: Optional[List[str]] = None
    ) -> RiskExplanation:
        """Generate comprehensive explanation for a prediction."""
        # Generate summary
        summary = self._generate_summary(
            overall_score, risk_level, len(risk_factors), trajectory
        )

        # Explain risk level
        risk_level_explanation = self._explain_risk_level(
            risk_level, overall_score, category_scores
        )

        # Generate detailed explanations
        explanations = self._generate_explanations(
            risk_factors, category_scores, trajectory
        )

        # Calculate feature contributions
        feature_contributions = self._calculate_contributions(
            risk_factors, overall_score
        )

        # Identify top risk drivers
        top_drivers = self._identify_top_drivers(risk_factors)

        # Generate what-if scenarios
        what_if = self._generate_what_if_scenarios(
            risk_factors, overall_score, category_scores
        )

        # Generate plain language summary
        plain_summary = self._generate_plain_language_summary(
            risk_level, top_drivers, trajectory, protective_factors
        )

        # Key takeaways
        takeaways = self._generate_key_takeaways(
            risk_level, risk_factors, trajectory
        )

        return RiskExplanation(
            prediction_id=prediction_id,
            case_id=case_id,
            generated_at=datetime.utcnow(),
            summary=summary,
            risk_level_explanation=risk_level_explanation,
            explanations=explanations,
            feature_contributions=feature_contributions,
            top_risk_drivers=top_drivers,
            protective_factors=protective_factors or [],
            what_if_scenarios=what_if,
            plain_language_summary=plain_summary,
            key_takeaways=takeaways
        )

    def _generate_summary(
        self,
        score: float,
        risk_level: str,
        factor_count: int,
        trajectory: str
    ) -> str:
        """Generate a brief summary."""
        trajectory_desc = {
            "improving": "showing signs of improvement",
            "stable": "remaining stable",
            "worsening": "showing concerning deterioration",
            "volatile": "fluctuating unpredictably",
            "unknown": "with limited trend data"
        }

        return (
            f"Risk assessment score: {score:.1f}/10 ({risk_level.upper()}). "
            f"Based on {factor_count} identified risk factor(s), "
            f"the situation is {trajectory_desc.get(trajectory, 'being monitored')}."
        )

    def _explain_risk_level(
        self,
        risk_level: str,
        score: float,
        category_scores: Dict[str, float]
    ) -> str:
        """Explain why this risk level was assigned."""
        base_explanation = self.RISK_LEVEL_DESCRIPTIONS.get(
            risk_level, "Risk level determined by multiple factors"
        )

        # Find highest category
        if category_scores:
            highest_cat = max(category_scores.items(), key=lambda x: x[1])
            category_contribution = (
                f"The {highest_cat[0].replace('_', ' ')} category "
                f"contributes most significantly (score: {highest_cat[1]:.1f})."
            )
        else:
            category_contribution = ""

        return f"{base_explanation}. {category_contribution}"

    def _generate_explanations(
        self,
        risk_factors: List[Dict[str, Any]],
        category_scores: Dict[str, float],
        trajectory: str
    ) -> List[Explanation]:
        """Generate detailed explanations."""
        explanations = []

        # Explain top factors
        sorted_factors = sorted(
            risk_factors,
            key=lambda x: x.get("score", 0) * x.get("weight", 1),
            reverse=True
        )

        for i, factor in enumerate(sorted_factors[:3]):
            factor_id = factor.get("factor_id", "")
            factor_explanation = self.FACTOR_EXPLANATIONS.get(
                factor_id,
                f"This factor contributes to the risk assessment"
            )

            explanations.append(Explanation(
                explanation_id=f"exp_factor_{i}",
                explanation_type=ExplanationType.FACTOR_CONTRIBUTION,
                title=f"Key Factor: {factor.get('name', factor_id)}",
                description=factor_explanation,
                confidence=factor.get("confidence", 0.7),
                supporting_data={
                    "factor_id": factor_id,
                    "score": factor.get("score"),
                    "weight": factor.get("weight"),
                    "evidence": factor.get("evidence", [])
                },
                visualization_hint="bar_chart"
            ))

        # Explain trajectory
        if trajectory in ["worsening", "improving"]:
            explanations.append(Explanation(
                explanation_id="exp_trajectory",
                explanation_type=ExplanationType.TREND_ANALYSIS,
                title=f"Trend: {trajectory.capitalize()}",
                description=self._get_trajectory_explanation(trajectory),
                confidence=0.7,
                supporting_data={"trajectory": trajectory},
                visualization_hint="line_chart"
            ))

        # Explain category patterns
        high_categories = [
            (cat, score) for cat, score in category_scores.items()
            if score >= 6
        ]

        if high_categories:
            explanations.append(Explanation(
                explanation_id="exp_categories",
                explanation_type=ExplanationType.PATTERN_DETECTION,
                title="High-Risk Categories",
                description=self._explain_high_categories(high_categories),
                confidence=0.8,
                supporting_data={"categories": dict(high_categories)},
                visualization_hint="radar_chart"
            ))

        return explanations

    def _get_trajectory_explanation(self, trajectory: str) -> str:
        """Get explanation for trajectory."""
        explanations = {
            "worsening": (
                "The risk indicators show an increasing trend over time. "
                "This suggests the situation may continue to deteriorate "
                "without intervention. Proactive measures are recommended."
            ),
            "improving": (
                "The risk indicators show a decreasing trend. "
                "Current interventions or circumstances appear to be "
                "having a positive effect. Continued monitoring is advised."
            ),
            "volatile": (
                "Risk levels have been fluctuating significantly. "
                "This unpredictability may indicate situational triggers "
                "that require identification and management."
            ),
            "stable": (
                "Risk levels have remained relatively constant. "
                "While this provides some predictability, the underlying "
                "issues have not resolved."
            )
        }
        return explanations.get(trajectory, "Trend analysis inconclusive.")

    def _explain_high_categories(
        self,
        categories: List[tuple]
    ) -> str:
        """Explain high-risk categories."""
        cat_names = [cat.replace("_", " ") for cat, _ in categories]

        if len(cat_names) == 1:
            return f"The {cat_names[0]} category shows elevated risk levels."
        else:
            return (
                f"Multiple categories show elevated risk: "
                f"{', '.join(cat_names[:-1])} and {cat_names[-1]}. "
                f"This combination warrants comprehensive intervention."
            )

    def _calculate_contributions(
        self,
        risk_factors: List[Dict[str, Any]],
        overall_score: float
    ) -> List[FeatureContribution]:
        """Calculate contribution of each feature."""
        contributions = []

        if not risk_factors or overall_score == 0:
            return contributions

        # Calculate weighted contributions
        total_weighted = sum(
            f.get("score", 0) * f.get("weight", 1) * f.get("confidence", 1)
            for f in risk_factors
        )

        for rank, factor in enumerate(sorted(
            risk_factors,
            key=lambda x: x.get("score", 0) * x.get("weight", 1),
            reverse=True
        )):
            weighted_score = (
                factor.get("score", 0) *
                factor.get("weight", 1) *
                factor.get("confidence", 1)
            )

            contribution = (weighted_score / total_weighted) * overall_score if total_weighted > 0 else 0

            factor_id = factor.get("factor_id", "")
            contributions.append(FeatureContribution(
                feature_name=factor.get("name", factor_id),
                feature_value=factor.get("score"),
                contribution=round(contribution, 2),
                importance_rank=rank + 1,
                explanation=self.FACTOR_EXPLANATIONS.get(
                    factor_id,
                    "This factor contributes to the overall risk"
                ),
                evidence=factor.get("evidence", [])
            ))

        return contributions

    def _identify_top_drivers(
        self,
        risk_factors: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify top risk drivers."""
        drivers = []

        sorted_factors = sorted(
            risk_factors,
            key=lambda x: x.get("score", 0) * x.get("weight", 1),
            reverse=True
        )

        for factor in sorted_factors[:5]:
            driver = f"{factor.get('name', factor.get('factor_id'))}"
            if factor.get("trend") == "increasing":
                driver += " (trending up)"
            drivers.append(driver)

        return drivers

    def _generate_what_if_scenarios(
        self,
        risk_factors: List[Dict[str, Any]],
        current_score: float,
        category_scores: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Generate counterfactual scenarios."""
        scenarios = []

        # Scenario: Remove top risk factor
        if risk_factors:
            top_factor = max(
                risk_factors,
                key=lambda x: x.get("score", 0) * x.get("weight", 1)
            )

            reduction = top_factor.get("score", 0) * top_factor.get("weight", 1) * 0.3
            new_score = max(0, current_score - reduction)

            scenarios.append({
                "scenario": f"If {top_factor.get('name')} were addressed",
                "current_score": current_score,
                "projected_score": round(new_score, 1),
                "change": round(-reduction, 1),
                "interventions_needed": [
                    f"Address {top_factor.get('name')} through appropriate intervention"
                ]
            })

        # Scenario: Address highest category
        if category_scores:
            highest_cat = max(category_scores.items(), key=lambda x: x[1])
            reduction = highest_cat[1] * 0.2
            new_score = max(0, current_score - reduction)

            scenarios.append({
                "scenario": f"If {highest_cat[0].replace('_', ' ')} risks were reduced",
                "current_score": current_score,
                "projected_score": round(new_score, 1),
                "change": round(-reduction, 1),
                "interventions_needed": [
                    f"Targeted interventions for {highest_cat[0].replace('_', ' ')}"
                ]
            })

        # Scenario: All moderate improvements
        total_reduction = sum(
            f.get("score", 0) * f.get("weight", 1) * 0.15
            for f in risk_factors
        )
        new_score = max(0, current_score - total_reduction)

        scenarios.append({
            "scenario": "If all risk factors showed moderate improvement",
            "current_score": current_score,
            "projected_score": round(new_score, 1),
            "change": round(-total_reduction, 1),
            "interventions_needed": [
                "Comprehensive intervention plan",
                "Regular monitoring and adjustment"
            ]
        })

        return scenarios

    def _generate_plain_language_summary(
        self,
        risk_level: str,
        top_drivers: List[str],
        trajectory: str,
        protective_factors: Optional[List[str]]
    ) -> str:
        """Generate a plain language summary for non-experts."""
        # Opening
        openings = {
            "critical": "This case requires immediate attention.",
            "high": "This case shows significant concerns.",
            "moderate": "This case has some notable concerns.",
            "low": "This case shows relatively few concerns.",
            "minimal": "This case currently shows minimal risk."
        }

        summary = openings.get(risk_level, "This case has been assessed for risk.")

        # Main concerns
        if top_drivers:
            if len(top_drivers) == 1:
                summary += f" The main concern is {top_drivers[0].lower()}."
            else:
                summary += f" The main concerns are {top_drivers[0].lower()} and {top_drivers[1].lower()}."

        # Trajectory
        trajectory_text = {
            "worsening": " The situation appears to be getting worse over time.",
            "improving": " Encouragingly, the situation shows signs of improvement.",
            "volatile": " The situation has been unpredictable, with ups and downs.",
            "stable": " The situation has remained relatively unchanged."
        }
        summary += trajectory_text.get(trajectory, "")

        # Protective factors
        if protective_factors:
            summary += f" On a positive note, {protective_factors[0].lower()} provides some protection."

        return summary

    def _generate_key_takeaways(
        self,
        risk_level: str,
        risk_factors: List[Dict[str, Any]],
        trajectory: str
    ) -> List[str]:
        """Generate key takeaways."""
        takeaways = []

        # Risk level takeaway
        level_messages = {
            "critical": "Immediate action is required to ensure child safety",
            "high": "This case should be prioritized for intervention",
            "moderate": "Regular monitoring and targeted interventions are recommended",
            "low": "Continue standard monitoring protocols",
            "minimal": "No immediate concerns, but maintain awareness"
        }
        takeaways.append(level_messages.get(risk_level, "Review and assess"))

        # Factor count
        high_severity = sum(1 for f in risk_factors if f.get("score", 0) >= 7)
        if high_severity > 0:
            takeaways.append(f"{high_severity} high-severity risk factor(s) identified")

        # Trajectory
        if trajectory == "worsening":
            takeaways.append("Risk is increasing - proactive intervention needed")
        elif trajectory == "improving":
            takeaways.append("Current approach appears to be working")

        # Specific high-risk factors
        for factor in risk_factors:
            if factor.get("score", 0) >= 8:
                takeaways.append(f"Critical: {factor.get('name')} requires immediate attention")
                break

        return takeaways[:5]

    def format_for_court(
        self,
        explanation: RiskExplanation
    ) -> str:
        """Format explanation for court presentation."""
        lines = [
            "RISK ASSESSMENT EXPLANATION",
            "=" * 40,
            "",
            f"Case ID: {explanation.case_id}",
            f"Assessment Date: {explanation.generated_at.strftime('%Y-%m-%d')}",
            "",
            "SUMMARY",
            "-" * 20,
            explanation.summary,
            "",
            "RISK LEVEL EXPLANATION",
            "-" * 20,
            explanation.risk_level_explanation,
            "",
            "KEY RISK DRIVERS",
            "-" * 20
        ]

        for i, driver in enumerate(explanation.top_risk_drivers, 1):
            lines.append(f"{i}. {driver}")

        lines.extend([
            "",
            "FACTOR CONTRIBUTIONS",
            "-" * 20
        ])

        for contrib in explanation.feature_contributions[:5]:
            lines.append(
                f"- {contrib.feature_name}: +{contrib.contribution:.1f} points "
                f"(Rank #{contrib.importance_rank})"
            )

        if explanation.protective_factors:
            lines.extend([
                "",
                "PROTECTIVE FACTORS",
                "-" * 20
            ])
            for factor in explanation.protective_factors:
                lines.append(f"- {factor}")

        lines.extend([
            "",
            "KEY TAKEAWAYS",
            "-" * 20
        ])

        for takeaway in explanation.key_takeaways:
            lines.append(f"* {takeaway}")

        return "\n".join(lines)
