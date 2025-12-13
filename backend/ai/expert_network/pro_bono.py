"""
Pro Bono Coordinator
Pro bono case coordination for family law.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import datetime
import hashlib


class ProBonoStatus(str, Enum):
    """Status of a pro bono case."""
    PENDING_ELIGIBILITY = "pending_eligibility"
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    SEEKING_EXPERT = "seeking_expert"
    MATCHED = "matched"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class IncomeLevel(str, Enum):
    """Income level categories."""
    VERY_LOW = "very_low"  # Below poverty line
    LOW = "low"  # 100-150% poverty line
    MODERATE = "moderate"  # 150-200% poverty line
    ABOVE = "above"  # Above 200% poverty line


@dataclass
class EligibilityCriteria:
    """Criteria for pro bono eligibility."""
    income_level: IncomeLevel
    household_size: int
    monthly_income: float
    currency: str
    has_legal_representation: bool
    case_merit_score: float  # 0-1, how strong is the case
    urgency_score: float  # 0-1, how urgent
    child_safety_concerns: bool
    domestic_violence_involved: bool
    international_element: bool
    previous_pro_bono: bool
    assets_value: float
    jurisdiction: str
    case_type: str


@dataclass
class EligibilityResult:
    """Result of eligibility assessment."""
    is_eligible: bool
    eligibility_score: float  # 0-100
    income_eligible: bool
    merit_eligible: bool
    priority_level: int  # 1-5, 1 is highest priority
    reasons: List[str]
    recommendations: List[str]
    required_documents: List[str]
    assessed_at: str


@dataclass
class ProBonoCase:
    """A pro bono case."""
    case_id: str
    client_id: str
    client_name: str

    # Case details
    case_type: str
    case_description: str
    jurisdiction: str
    urgency: str
    estimated_hours: float

    # Eligibility
    eligibility: EligibilityResult
    supporting_documents: List[str]

    # Status
    status: ProBonoStatus
    priority_level: int

    # Matching
    required_specializations: List[str]
    matched_expert_id: Optional[str]
    matched_at: Optional[str]
    match_attempts: int

    # Progress
    hours_donated: float
    milestones: List[Dict[str, Any]]
    outcome: Optional[str]

    # Metadata
    created_at: str
    updated_at: str
    completed_at: Optional[str]
    notes: str


@dataclass
class ProBonoCommitment:
    """An expert's pro bono commitment."""
    commitment_id: str
    expert_id: str
    expert_name: str

    # Commitment details
    hours_per_month: float
    specializations: List[str]
    jurisdictions: List[str]
    case_types: List[str]
    max_active_cases: int
    current_active_cases: int

    # Track record
    total_hours_donated: float
    cases_completed: int
    average_rating: float
    clients_helped: int

    # Status
    is_active: bool
    available_from: str
    commitment_start: str
    commitment_end: Optional[str]

    # Recognition
    badges: List[str]
    recognition_level: str  # bronze, silver, gold, platinum


# Income thresholds by jurisdiction (simplified)
INCOME_THRESHOLDS = {
    "germany": {
        "very_low": 1000,  # EUR/month single
        "low": 1500,
        "moderate": 2000,
        "household_multiplier": 0.5  # Per additional person
    },
    "turkey": {
        "very_low": 5000,  # TRY/month single
        "low": 7500,
        "moderate": 10000,
        "household_multiplier": 0.5
    },
    "default": {
        "very_low": 1000,
        "low": 1500,
        "moderate": 2000,
        "household_multiplier": 0.5
    }
}


class ProBonoCoordinator:
    """Coordinates pro bono legal assistance."""

    def __init__(self):
        self.cases: Dict[str, ProBonoCase] = {}
        self.commitments: Dict[str, ProBonoCommitment] = {}
        self.waiting_list: List[str] = []  # Case IDs

    def assess_eligibility(
        self,
        criteria: EligibilityCriteria
    ) -> EligibilityResult:
        """Assess eligibility for pro bono assistance."""
        reasons = []
        recommendations = []
        required_docs = []

        # Get income thresholds for jurisdiction
        thresholds = INCOME_THRESHOLDS.get(
            criteria.jurisdiction.lower(),
            INCOME_THRESHOLDS["default"]
        )

        # Calculate adjusted threshold based on household size
        adjusted_threshold = (
            thresholds["moderate"] +
            (criteria.household_size - 1) * thresholds["moderate"] * thresholds["household_multiplier"]
        )

        # Income eligibility
        income_eligible = criteria.monthly_income <= adjusted_threshold

        if criteria.income_level == IncomeLevel.VERY_LOW:
            reasons.append("Applicant meets very low income criteria")
            required_docs.append("Proof of income (last 3 months)")
        elif criteria.income_level == IncomeLevel.LOW:
            reasons.append("Applicant meets low income criteria")
            required_docs.append("Proof of income (last 3 months)")
        elif not income_eligible:
            reasons.append("Income exceeds eligibility threshold")
            recommendations.append("Consider reduced-fee services")

        # Check assets
        if criteria.assets_value > adjusted_threshold * 6:
            income_eligible = False
            reasons.append("Assets exceed eligibility threshold")
            recommendations.append("May need to use some assets for legal costs")

        # Already has representation
        if criteria.has_legal_representation:
            reasons.append("Applicant already has legal representation")
            recommendations.append("Contact existing lawyer about fee arrangements")

        # Merit assessment
        merit_eligible = criteria.case_merit_score >= 0.4

        if criteria.case_merit_score >= 0.7:
            reasons.append("Case has strong merit")
        elif criteria.case_merit_score >= 0.4:
            reasons.append("Case has reasonable merit")
        else:
            reasons.append("Case merit is uncertain - further review needed")
            recommendations.append("Consider case evaluation consultation")

        # Priority factors
        priority_score = 0

        if criteria.child_safety_concerns:
            priority_score += 30
            reasons.append("Child safety concerns increase priority")
            required_docs.append("Evidence of safety concerns")

        if criteria.domestic_violence_involved:
            priority_score += 25
            reasons.append("Domestic violence involvement increases priority")
            required_docs.append("Police reports or protection orders if available")

        if criteria.urgency_score > 0.7:
            priority_score += 20
            reasons.append("High urgency case")

        if criteria.international_element:
            priority_score += 10
            reasons.append("International element requires specialized assistance")

        # Calculate eligibility
        is_eligible = (
            income_eligible and
            merit_eligible and
            not criteria.has_legal_representation
        )

        # Calculate eligibility score
        eligibility_score = 0.0
        if income_eligible:
            eligibility_score += 40
        if merit_eligible:
            eligibility_score += 30
        eligibility_score += priority_score

        # Determine priority level
        if eligibility_score >= 80:
            priority_level = 1
        elif eligibility_score >= 60:
            priority_level = 2
        elif eligibility_score >= 40:
            priority_level = 3
        elif eligibility_score >= 20:
            priority_level = 4
        else:
            priority_level = 5

        # Standard required documents
        required_docs.extend([
            "ID document",
            "Case summary",
            "Relevant court documents (if any)"
        ])

        return EligibilityResult(
            is_eligible=is_eligible,
            eligibility_score=min(eligibility_score, 100),
            income_eligible=income_eligible,
            merit_eligible=merit_eligible,
            priority_level=priority_level,
            reasons=reasons,
            recommendations=recommendations,
            required_documents=list(set(required_docs)),
            assessed_at=datetime.datetime.now().isoformat()
        )

    def create_case(
        self,
        client_id: str,
        client_name: str,
        case_type: str,
        case_description: str,
        jurisdiction: str,
        eligibility: EligibilityResult,
        required_specializations: List[str],
        urgency: str = "routine",
        estimated_hours: float = 10.0,
        supporting_documents: Optional[List[str]] = None
    ) -> ProBonoCase:
        """Create a pro bono case."""
        case_id = hashlib.md5(
            f"{client_id}-{case_type}-{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        now = datetime.datetime.now().isoformat()

        case = ProBonoCase(
            case_id=case_id,
            client_id=client_id,
            client_name=client_name,
            case_type=case_type,
            case_description=case_description,
            jurisdiction=jurisdiction,
            urgency=urgency,
            estimated_hours=estimated_hours,
            eligibility=eligibility,
            supporting_documents=supporting_documents or [],
            status=ProBonoStatus.ELIGIBLE if eligibility.is_eligible else ProBonoStatus.NOT_ELIGIBLE,
            priority_level=eligibility.priority_level,
            required_specializations=required_specializations,
            matched_expert_id=None,
            matched_at=None,
            match_attempts=0,
            hours_donated=0.0,
            milestones=[],
            outcome=None,
            created_at=now,
            updated_at=now,
            completed_at=None,
            notes=""
        )

        self.cases[case_id] = case

        # Add to waiting list if eligible
        if eligibility.is_eligible:
            self._add_to_waiting_list(case_id)

        return case

    def _add_to_waiting_list(self, case_id: str):
        """Add case to waiting list in priority order."""
        case = self.cases[case_id]

        # Find correct position based on priority
        insert_pos = 0
        for i, existing_id in enumerate(self.waiting_list):
            existing = self.cases.get(existing_id)
            if existing and existing.priority_level > case.priority_level:
                insert_pos = i
                break
            insert_pos = i + 1

        self.waiting_list.insert(insert_pos, case_id)

    def register_commitment(
        self,
        expert_id: str,
        expert_name: str,
        hours_per_month: float,
        specializations: List[str],
        jurisdictions: List[str],
        case_types: Optional[List[str]] = None,
        max_active_cases: int = 2
    ) -> ProBonoCommitment:
        """Register an expert's pro bono commitment."""
        commitment_id = hashlib.md5(
            f"{expert_id}-probono".encode()
        ).hexdigest()[:10]

        commitment = ProBonoCommitment(
            commitment_id=commitment_id,
            expert_id=expert_id,
            expert_name=expert_name,
            hours_per_month=hours_per_month,
            specializations=specializations,
            jurisdictions=jurisdictions,
            case_types=case_types or ["all"],
            max_active_cases=max_active_cases,
            current_active_cases=0,
            total_hours_donated=0.0,
            cases_completed=0,
            average_rating=0.0,
            clients_helped=0,
            is_active=True,
            available_from=datetime.datetime.now().isoformat(),
            commitment_start=datetime.datetime.now().isoformat(),
            commitment_end=None,
            badges=[],
            recognition_level="bronze"
        )

        self.commitments[expert_id] = commitment
        return commitment

    def find_available_experts(
        self,
        case: ProBonoCase
    ) -> List[Tuple[ProBonoCommitment, float]]:
        """Find available experts for a pro bono case."""
        matches: List[Tuple[ProBonoCommitment, float]] = []

        for commitment in self.commitments.values():
            if not commitment.is_active:
                continue

            if commitment.current_active_cases >= commitment.max_active_cases:
                continue

            # Calculate match score
            score = 0.0

            # Specialization match
            spec_matches = sum(
                1 for s in case.required_specializations
                if s in commitment.specializations
            )
            if case.required_specializations:
                score += (spec_matches / len(case.required_specializations)) * 40

            # Jurisdiction match
            if case.jurisdiction in commitment.jurisdictions:
                score += 30
            elif "all" in commitment.jurisdictions:
                score += 15

            # Case type match
            if case.case_type in commitment.case_types or "all" in commitment.case_types:
                score += 20

            # Experience bonus
            if commitment.cases_completed > 5:
                score += 10
            elif commitment.cases_completed > 0:
                score += 5

            if score >= 30:  # Minimum match threshold
                matches.append((commitment, score))

        # Sort by score
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def match_case(
        self,
        case_id: str,
        expert_id: str
    ) -> bool:
        """Match a case with an expert."""
        if case_id not in self.cases:
            return False

        if expert_id not in self.commitments:
            return False

        case = self.cases[case_id]
        commitment = self.commitments[expert_id]

        if commitment.current_active_cases >= commitment.max_active_cases:
            return False

        # Update case
        case.status = ProBonoStatus.MATCHED
        case.matched_expert_id = expert_id
        case.matched_at = datetime.datetime.now().isoformat()
        case.updated_at = datetime.datetime.now().isoformat()

        # Update commitment
        commitment.current_active_cases += 1

        # Remove from waiting list
        if case_id in self.waiting_list:
            self.waiting_list.remove(case_id)

        return True

    def start_case(self, case_id: str) -> bool:
        """Start working on a case."""
        if case_id not in self.cases:
            return False

        case = self.cases[case_id]
        if case.status != ProBonoStatus.MATCHED:
            return False

        case.status = ProBonoStatus.IN_PROGRESS
        case.updated_at = datetime.datetime.now().isoformat()

        case.milestones.append({
            "type": "started",
            "timestamp": datetime.datetime.now().isoformat(),
            "description": "Case work started"
        })

        return True

    def log_hours(
        self,
        case_id: str,
        hours: float,
        description: str
    ) -> bool:
        """Log pro bono hours for a case."""
        if case_id not in self.cases:
            return False

        case = self.cases[case_id]
        case.hours_donated += hours
        case.updated_at = datetime.datetime.now().isoformat()

        case.milestones.append({
            "type": "hours_logged",
            "timestamp": datetime.datetime.now().isoformat(),
            "hours": hours,
            "description": description
        })

        # Update expert commitment
        if case.matched_expert_id and case.matched_expert_id in self.commitments:
            commitment = self.commitments[case.matched_expert_id]
            commitment.total_hours_donated += hours

        return True

    def complete_case(
        self,
        case_id: str,
        outcome: str,
        client_rating: Optional[float] = None
    ) -> bool:
        """Complete a pro bono case."""
        if case_id not in self.cases:
            return False

        case = self.cases[case_id]
        now = datetime.datetime.now().isoformat()

        case.status = ProBonoStatus.COMPLETED
        case.outcome = outcome
        case.completed_at = now
        case.updated_at = now

        case.milestones.append({
            "type": "completed",
            "timestamp": now,
            "outcome": outcome
        })

        # Update expert commitment
        if case.matched_expert_id and case.matched_expert_id in self.commitments:
            commitment = self.commitments[case.matched_expert_id]
            commitment.current_active_cases -= 1
            commitment.cases_completed += 1
            commitment.clients_helped += 1

            # Update rating
            if client_rating:
                total_rating = commitment.average_rating * (commitment.cases_completed - 1)
                commitment.average_rating = (total_rating + client_rating) / commitment.cases_completed

            # Update recognition level
            commitment.recognition_level = self._calculate_recognition_level(commitment)

        return True

    def _calculate_recognition_level(
        self,
        commitment: ProBonoCommitment
    ) -> str:
        """Calculate recognition level based on contribution."""
        if commitment.total_hours_donated >= 200 and commitment.cases_completed >= 20:
            return "platinum"
        elif commitment.total_hours_donated >= 100 and commitment.cases_completed >= 10:
            return "gold"
        elif commitment.total_hours_donated >= 50 and commitment.cases_completed >= 5:
            return "silver"
        else:
            return "bronze"

    def get_waiting_list_position(self, case_id: str) -> Optional[int]:
        """Get a case's position in the waiting list."""
        try:
            return self.waiting_list.index(case_id) + 1
        except ValueError:
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get pro bono program statistics."""
        total_cases = len(self.cases)
        completed = len([c for c in self.cases.values() if c.status == ProBonoStatus.COMPLETED])
        in_progress = len([c for c in self.cases.values() if c.status == ProBonoStatus.IN_PROGRESS])
        waiting = len(self.waiting_list)

        total_hours = sum(c.hours_donated for c in self.cases.values())
        active_experts = len([c for c in self.commitments.values() if c.is_active])

        return {
            "total_cases": total_cases,
            "completed_cases": completed,
            "in_progress_cases": in_progress,
            "waiting_cases": waiting,
            "total_hours_donated": total_hours,
            "active_experts": active_experts,
            "total_committed_hours_per_month": sum(
                c.hours_per_month for c in self.commitments.values() if c.is_active
            ),
            "average_case_duration_hours": total_hours / completed if completed > 0 else 0,
            "clients_helped": sum(c.clients_helped for c in self.commitments.values())
        }

    def get_top_contributors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top pro bono contributors."""
        contributors = [
            {
                "expert_id": c.expert_id,
                "expert_name": c.expert_name,
                "hours_donated": c.total_hours_donated,
                "cases_completed": c.cases_completed,
                "recognition_level": c.recognition_level,
                "average_rating": c.average_rating
            }
            for c in self.commitments.values()
            if c.total_hours_donated > 0
        ]

        contributors.sort(key=lambda x: x["hours_donated"], reverse=True)
        return contributors[:limit]
