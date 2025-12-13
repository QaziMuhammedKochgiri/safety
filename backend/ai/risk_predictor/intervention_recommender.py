"""
Intervention Recommender for Child Safety
Recommends interventions based on risk assessment.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


class InterventionType(str, Enum):
    """Types of interventions."""
    EMERGENCY = "emergency"  # Immediate action required
    LEGAL = "legal"  # Court/legal action
    THERAPEUTIC = "therapeutic"  # Therapy/counseling
    PROTECTIVE = "protective"  # Protective measures
    MONITORING = "monitoring"  # Enhanced monitoring
    EDUCATIONAL = "educational"  # Parent education
    SUPPORT = "support"  # Support services
    MEDICAL = "medical"  # Medical intervention


class InterventionPriority(str, Enum):
    """Priority levels for interventions."""
    CRITICAL = "critical"  # Within hours
    URGENT = "urgent"  # Within 24-48 hours
    HIGH = "high"  # Within 1 week
    MEDIUM = "medium"  # Within 2-4 weeks
    LOW = "low"  # Within 1-3 months


@dataclass
class Intervention:
    """A recommended intervention."""
    intervention_id: str
    name: str
    description: str
    intervention_type: InterventionType
    priority: InterventionPriority
    rationale: str
    target_risk_factors: List[str]
    expected_effectiveness: float  # 0-1
    estimated_cost: str  # low, medium, high
    time_to_implement: str
    prerequisites: List[str] = field(default_factory=list)
    contraindications: List[str] = field(default_factory=list)
    success_indicators: List[str] = field(default_factory=list)


@dataclass
class InterventionPlan:
    """Complete intervention plan for a case."""
    plan_id: str
    case_id: str
    generated_at: datetime
    risk_level: str
    interventions: List[Intervention]
    implementation_order: List[str]  # Intervention IDs in order
    total_interventions: int
    critical_count: int
    estimated_risk_reduction: float
    monitoring_schedule: Dict[str, str]
    success_criteria: List[str]
    review_date: datetime


# Intervention definitions
INTERVENTION_CATALOG = {
    # Emergency interventions
    "INT_EM_001": {
        "name": "Emergency Services Contact",
        "description": "Immediate contact with emergency services (911/police)",
        "type": InterventionType.EMERGENCY,
        "default_priority": InterventionPriority.CRITICAL,
        "target_factors": ["PHY001", "PHY002", "DV001", "ABD001"],
        "effectiveness": 0.9,
        "cost": "low",
        "time": "Immediate"
    },
    "INT_EM_002": {
        "name": "Emergency Custody Motion",
        "description": "File emergency motion for temporary custody change",
        "type": InterventionType.LEGAL,
        "default_priority": InterventionPriority.CRITICAL,
        "target_factors": ["PHY001", "ABD001", "DV001", "NEG001"],
        "effectiveness": 0.75,
        "cost": "medium",
        "time": "24-48 hours"
    },
    "INT_EM_003": {
        "name": "Child Removal by CPS",
        "description": "Request CPS evaluation and potential removal",
        "type": InterventionType.PROTECTIVE,
        "default_priority": InterventionPriority.CRITICAL,
        "target_factors": ["PHY001", "NEG001", "DV001", "SUB001"],
        "effectiveness": 0.85,
        "cost": "medium",
        "time": "24-72 hours"
    },

    # Legal interventions
    "INT_LG_001": {
        "name": "Protective Order",
        "description": "Obtain restraining/protective order",
        "type": InterventionType.LEGAL,
        "default_priority": InterventionPriority.URGENT,
        "target_factors": ["PHY001", "PHY002", "DV001", "DV002", "ABD001"],
        "effectiveness": 0.70,
        "cost": "medium",
        "time": "1-7 days"
    },
    "INT_LG_002": {
        "name": "Supervised Visitation Order",
        "description": "Request court-ordered supervised visitation",
        "type": InterventionType.LEGAL,
        "default_priority": InterventionPriority.HIGH,
        "target_factors": ["PHY001", "EMO001", "SUB001", "MH001", "NEG004"],
        "effectiveness": 0.65,
        "cost": "medium",
        "time": "2-4 weeks"
    },
    "INT_LG_003": {
        "name": "Custody Evaluation",
        "description": "Request comprehensive custody evaluation",
        "type": InterventionType.LEGAL,
        "default_priority": InterventionPriority.MEDIUM,
        "target_factors": ["EMO001", "EMO002", "MH001", "NEG001"],
        "effectiveness": 0.60,
        "cost": "high",
        "time": "4-8 weeks"
    },
    "INT_LG_004": {
        "name": "Passport Surrender",
        "description": "Court order to surrender passports",
        "type": InterventionType.LEGAL,
        "default_priority": InterventionPriority.URGENT,
        "target_factors": ["ABD001", "ABD002", "ABD003"],
        "effectiveness": 0.80,
        "cost": "low",
        "time": "1-2 weeks"
    },

    # Therapeutic interventions
    "INT_TH_001": {
        "name": "Child Therapy",
        "description": "Individual therapy for child with trauma-informed therapist",
        "type": InterventionType.THERAPEUTIC,
        "default_priority": InterventionPriority.HIGH,
        "target_factors": ["EMO001", "EMO002", "EMO003", "DV003"],
        "effectiveness": 0.70,
        "cost": "medium",
        "time": "Ongoing"
    },
    "INT_TH_002": {
        "name": "Parent Therapy",
        "description": "Therapy for concerning parent",
        "type": InterventionType.THERAPEUTIC,
        "default_priority": InterventionPriority.MEDIUM,
        "target_factors": ["MH001", "EMO002", "PHY003"],
        "effectiveness": 0.55,
        "cost": "medium",
        "time": "Ongoing"
    },
    "INT_TH_003": {
        "name": "Family Therapy",
        "description": "Family therapy sessions",
        "type": InterventionType.THERAPEUTIC,
        "default_priority": InterventionPriority.MEDIUM,
        "target_factors": ["EMO001", "EMO004"],
        "effectiveness": 0.50,
        "cost": "medium",
        "time": "Ongoing"
    },
    "INT_TH_004": {
        "name": "Reunification Therapy",
        "description": "Specialized therapy for parent-child reunification",
        "type": InterventionType.THERAPEUTIC,
        "default_priority": InterventionPriority.MEDIUM,
        "target_factors": ["EMO001", "WEP004"],
        "effectiveness": 0.60,
        "cost": "high",
        "time": "3-6 months"
    },

    # Protective interventions
    "INT_PR_001": {
        "name": "Safety Planning",
        "description": "Develop comprehensive safety plan",
        "type": InterventionType.PROTECTIVE,
        "default_priority": InterventionPriority.HIGH,
        "target_factors": ["PHY001", "DV001", "ABD001"],
        "effectiveness": 0.65,
        "cost": "low",
        "time": "1-2 days"
    },
    "INT_PR_002": {
        "name": "School Safety Alert",
        "description": "Notify school of custody situation and pickup restrictions",
        "type": InterventionType.PROTECTIVE,
        "default_priority": InterventionPriority.HIGH,
        "target_factors": ["ABD001", "ABD002", "ABD004"],
        "effectiveness": 0.75,
        "cost": "low",
        "time": "Same day"
    },
    "INT_PR_003": {
        "name": "Safe Exchange Location",
        "description": "Establish police station or monitored location for custody exchanges",
        "type": InterventionType.PROTECTIVE,
        "default_priority": InterventionPriority.HIGH,
        "target_factors": ["PHY001", "DV001", "PHY002"],
        "effectiveness": 0.70,
        "cost": "low",
        "time": "Immediate"
    },

    # Monitoring interventions
    "INT_MO_001": {
        "name": "Communication Monitoring",
        "description": "Systematic monitoring of co-parent communications",
        "type": InterventionType.MONITORING,
        "default_priority": InterventionPriority.MEDIUM,
        "target_factors": ["EMO001", "EMO002", "WEP001"],
        "effectiveness": 0.55,
        "cost": "low",
        "time": "Ongoing"
    },
    "INT_MO_002": {
        "name": "Visitation Documentation",
        "description": "Detailed documentation of all visitations",
        "type": InterventionType.MONITORING,
        "default_priority": InterventionPriority.MEDIUM,
        "target_factors": ["INT001", "INT005"],
        "effectiveness": 0.50,
        "cost": "low",
        "time": "Ongoing"
    },
    "INT_MO_003": {
        "name": "Welfare Checks",
        "description": "Regular welfare checks during custody periods",
        "type": InterventionType.MONITORING,
        "default_priority": InterventionPriority.HIGH,
        "target_factors": ["NEG001", "SUB001", "MH002"],
        "effectiveness": 0.60,
        "cost": "medium",
        "time": "Ongoing"
    },

    # Medical interventions
    "INT_MD_001": {
        "name": "Substance Testing",
        "description": "Court-ordered drug/alcohol testing",
        "type": InterventionType.MEDICAL,
        "default_priority": InterventionPriority.HIGH,
        "target_factors": ["SUB001", "SUB002"],
        "effectiveness": 0.65,
        "cost": "medium",
        "time": "1-2 weeks"
    },
    "INT_MD_002": {
        "name": "Psychological Evaluation",
        "description": "Comprehensive psychological evaluation",
        "type": InterventionType.MEDICAL,
        "default_priority": InterventionPriority.MEDIUM,
        "target_factors": ["MH001", "MH002", "MH003"],
        "effectiveness": 0.60,
        "cost": "high",
        "time": "2-4 weeks"
    },

    # Educational interventions
    "INT_ED_001": {
        "name": "Parenting Classes",
        "description": "Court-ordered parenting education",
        "type": InterventionType.EDUCATIONAL,
        "default_priority": InterventionPriority.MEDIUM,
        "target_factors": ["NEG001", "NEG004", "EMO004"],
        "effectiveness": 0.45,
        "cost": "low",
        "time": "4-12 weeks"
    },
    "INT_ED_002": {
        "name": "Co-Parenting Education",
        "description": "Education on healthy co-parenting",
        "type": InterventionType.EDUCATIONAL,
        "default_priority": InterventionPriority.LOW,
        "target_factors": ["EMO001", "WEP001", "INT003"],
        "effectiveness": 0.40,
        "cost": "low",
        "time": "4-8 weeks"
    },

    # Support interventions
    "INT_SP_001": {
        "name": "Domestic Violence Shelter",
        "description": "Safe housing at DV shelter",
        "type": InterventionType.SUPPORT,
        "default_priority": InterventionPriority.URGENT,
        "target_factors": ["DV001", "DV002"],
        "effectiveness": 0.80,
        "cost": "low",
        "time": "Immediate"
    },
    "INT_SP_002": {
        "name": "Case Management",
        "description": "Assign case manager for ongoing support",
        "type": InterventionType.SUPPORT,
        "default_priority": InterventionPriority.MEDIUM,
        "target_factors": ["STB001", "STB002", "STB003"],
        "effectiveness": 0.55,
        "cost": "medium",
        "time": "1-2 weeks"
    }
}


class InterventionRecommender:
    """Recommends interventions based on risk assessment."""

    def __init__(self):
        self.catalog = INTERVENTION_CATALOG

    def recommend_interventions(
        self,
        case_id: str,
        risk_factors: List[str],
        risk_level: str,
        existing_interventions: Optional[List[str]] = None
    ) -> InterventionPlan:
        """Generate intervention plan based on risk factors."""
        existing = set(existing_interventions or [])

        # Match interventions to risk factors
        matched_interventions = []

        for int_id, int_def in self.catalog.items():
            if int_id in existing:
                continue  # Skip already implemented

            # Check if any target factors are present
            matching_factors = [
                f for f in risk_factors
                if f in int_def["target_factors"]
            ]

            if matching_factors:
                # Create intervention
                intervention = self._create_intervention(
                    int_id, int_def, matching_factors, risk_level
                )
                matched_interventions.append(intervention)

        # Sort by priority
        priority_order = {
            InterventionPriority.CRITICAL: 0,
            InterventionPriority.URGENT: 1,
            InterventionPriority.HIGH: 2,
            InterventionPriority.MEDIUM: 3,
            InterventionPriority.LOW: 4
        }

        matched_interventions.sort(
            key=lambda x: (priority_order[x.priority], -x.expected_effectiveness)
        )

        # Limit to manageable number
        selected = matched_interventions[:12]

        # Create implementation order
        implementation_order = [i.intervention_id for i in selected]

        # Calculate critical count
        critical_count = sum(
            1 for i in selected
            if i.priority in [InterventionPriority.CRITICAL, InterventionPriority.URGENT]
        )

        # Estimate risk reduction
        risk_reduction = self._estimate_risk_reduction(selected)

        # Generate monitoring schedule
        monitoring_schedule = self._generate_monitoring_schedule(selected, risk_level)

        # Define success criteria
        success_criteria = self._define_success_criteria(selected, risk_factors)

        # Set review date based on risk level
        review_days = {
            "critical": 7,
            "high": 14,
            "moderate": 30,
            "low": 60,
            "minimal": 90
        }
        review_date = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        from datetime import timedelta
        review_date += timedelta(days=review_days.get(risk_level, 30))

        return InterventionPlan(
            plan_id=f"plan_{case_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            case_id=case_id,
            generated_at=datetime.utcnow(),
            risk_level=risk_level,
            interventions=selected,
            implementation_order=implementation_order,
            total_interventions=len(selected),
            critical_count=critical_count,
            estimated_risk_reduction=round(risk_reduction, 2),
            monitoring_schedule=monitoring_schedule,
            success_criteria=success_criteria,
            review_date=review_date
        )

    def _create_intervention(
        self,
        int_id: str,
        int_def: Dict[str, Any],
        matching_factors: List[str],
        risk_level: str
    ) -> Intervention:
        """Create an intervention from definition."""
        # Adjust priority based on risk level
        priority = int_def["default_priority"]
        if risk_level in ["critical", "high"]:
            # Escalate priorities
            if priority == InterventionPriority.MEDIUM:
                priority = InterventionPriority.HIGH
            elif priority == InterventionPriority.LOW:
                priority = InterventionPriority.MEDIUM

        # Generate rationale
        rationale = f"Recommended due to presence of: {', '.join(matching_factors)}"

        return Intervention(
            intervention_id=int_id,
            name=int_def["name"],
            description=int_def["description"],
            intervention_type=int_def["type"],
            priority=priority,
            rationale=rationale,
            target_risk_factors=matching_factors,
            expected_effectiveness=int_def["effectiveness"],
            estimated_cost=int_def["cost"],
            time_to_implement=int_def["time"],
            prerequisites=self._get_prerequisites(int_id),
            contraindications=self._get_contraindications(int_id),
            success_indicators=self._get_success_indicators(int_id)
        )

    def _get_prerequisites(self, int_id: str) -> List[str]:
        """Get prerequisites for an intervention."""
        prerequisites = {
            "INT_LG_002": ["Attorney representation", "Court filing fee"],
            "INT_LG_003": ["Court order", "Qualified evaluator"],
            "INT_TH_004": ["Both parents' cooperation", "Trained therapist"],
            "INT_MD_002": ["Court order or consent", "Licensed psychologist"]
        }
        return prerequisites.get(int_id, [])

    def _get_contraindications(self, int_id: str) -> List[str]:
        """Get contraindications for an intervention."""
        contraindications = {
            "INT_TH_003": ["Active domestic violence", "Severe alienation"],
            "INT_TH_004": ["Child's strong resistance", "Safety concerns"],
            "INT_ED_002": ["High conflict situation", "Active litigation"]
        }
        return contraindications.get(int_id, [])

    def _get_success_indicators(self, int_id: str) -> List[str]:
        """Get success indicators for an intervention."""
        indicators = {
            "INT_LG_001": ["Order granted", "Compliance maintained"],
            "INT_LG_002": ["Visits completed without incident", "Child's comfort improves"],
            "INT_TH_001": ["Child reports feeling safer", "Behavioral improvements"],
            "INT_TH_004": ["Positive contact established", "Reduced resistance"],
            "INT_PR_001": ["Plan followed", "No safety incidents"],
            "INT_MD_001": ["Clean test results", "Consistent compliance"]
        }
        return indicators.get(int_id, ["Implementation completed", "Positive feedback"])

    def _estimate_risk_reduction(self, interventions: List[Intervention]) -> float:
        """Estimate overall risk reduction from interventions."""
        if not interventions:
            return 0.0

        # Using diminishing returns model
        remaining_risk = 1.0

        for intervention in interventions:
            reduction = intervention.expected_effectiveness * 0.3  # Cap individual impact
            remaining_risk *= (1 - reduction)

        total_reduction = (1 - remaining_risk) * 10  # Scale to 0-10
        return min(5.0, total_reduction)  # Cap at 50% reduction

    def _generate_monitoring_schedule(
        self,
        interventions: List[Intervention],
        risk_level: str
    ) -> Dict[str, str]:
        """Generate monitoring schedule."""
        schedule = {}

        # Base frequency on risk level
        base_frequencies = {
            "critical": "Daily",
            "high": "Every 2-3 days",
            "moderate": "Weekly",
            "low": "Bi-weekly",
            "minimal": "Monthly"
        }

        schedule["general_monitoring"] = base_frequencies.get(risk_level, "Weekly")

        # Add intervention-specific monitoring
        for intervention in interventions:
            if intervention.intervention_type == InterventionType.THERAPEUTIC:
                schedule[f"therapy_progress_{intervention.intervention_id}"] = "After each session"
            elif intervention.intervention_type == InterventionType.LEGAL:
                schedule[f"compliance_{intervention.intervention_id}"] = "Ongoing"
            elif intervention.intervention_type == InterventionType.MEDICAL:
                schedule[f"test_results_{intervention.intervention_id}"] = "As completed"

        return schedule

    def _define_success_criteria(
        self,
        interventions: List[Intervention],
        risk_factors: List[str]
    ) -> List[str]:
        """Define success criteria for the intervention plan."""
        criteria = [
            "No new safety incidents",
            "Risk score decrease of at least 1 point",
            "Compliance with all court orders"
        ]

        # Add factor-specific criteria
        if any("PHY" in f for f in risk_factors):
            criteria.append("No physical harm incidents")

        if any("ABD" in f for f in risk_factors):
            criteria.append("All travel documents secured")
            criteria.append("Child location verified daily")

        if any("EMO" in f for f in risk_factors):
            criteria.append("Reduced alienation behaviors documented")
            criteria.append("Child reports improved relationship with both parents")

        if any("SUB" in f for f in risk_factors):
            criteria.append("Consistent clean test results")

        return criteria[:8]

    def get_intervention_details(self, intervention_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an intervention."""
        return self.catalog.get(intervention_id)

    def get_interventions_by_type(
        self,
        intervention_type: InterventionType
    ) -> List[Dict[str, Any]]:
        """Get all interventions of a specific type."""
        return [
            {"id": int_id, **int_def}
            for int_id, int_def in self.catalog.items()
            if int_def["type"] == intervention_type
        ]

    def get_interventions_for_factor(self, factor_id: str) -> List[Dict[str, Any]]:
        """Get interventions targeting a specific risk factor."""
        return [
            {"id": int_id, **int_def}
            for int_id, int_def in self.catalog.items()
            if factor_id in int_def["target_factors"]
        ]
