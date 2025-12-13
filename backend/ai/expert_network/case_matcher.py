"""
Case Matcher
AI-powered case-expert matching system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import datetime

from .expert_profile import ExpertProfile, ExpertSpecialization, VerificationStatus


class CaseComplexity(str, Enum):
    """Complexity level of a case."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    HIGHLY_COMPLEX = "highly_complex"


class Urgency(str, Enum):
    """Case urgency level."""
    ROUTINE = "routine"
    ELEVATED = "elevated"
    URGENT = "urgent"
    EMERGENCY = "emergency"


@dataclass
class MatchCriteria:
    """Criteria for matching experts to cases."""
    case_id: str
    case_type: str  # custody, protection, divorce, etc.
    required_specializations: List[ExpertSpecialization]
    preferred_specializations: List[ExpertSpecialization]
    jurisdictions: List[str]
    languages: List[str]
    complexity: CaseComplexity
    urgency: Urgency
    budget_range: Optional[Tuple[float, float]]  # Min, max
    pro_bono_eligible: bool
    requires_court_testimony: bool
    specific_skills: List[str]  # e.g., "parental alienation", "digital forensics"
    cultural_considerations: List[str]
    case_description: str


@dataclass
class MatchScore:
    """Detailed matching score breakdown."""
    total_score: float  # 0-100
    specialization_score: float
    jurisdiction_score: float
    language_score: float
    experience_score: float
    availability_score: float
    rating_score: float
    response_time_score: float
    budget_score: float
    skill_match_score: float
    verification_score: float


@dataclass
class ExpertRecommendation:
    """A recommended expert for a case."""
    expert: ExpertProfile
    match_score: MatchScore
    ranking: int
    match_reasons: List[str]
    concerns: List[str]
    estimated_response_time: str
    estimated_cost: Optional[str]


@dataclass
class MatchResult:
    """Result of case-expert matching."""
    case_id: str
    matched_at: str
    total_experts_considered: int
    recommendations: List[ExpertRecommendation]
    unmatched_reasons: List[str]  # Why some criteria couldn't be matched
    alternative_suggestions: List[str]  # Suggestions if no good matches


class CaseMatcher:
    """Matches cases with appropriate experts."""

    def __init__(self, expert_profiles: Dict[str, ExpertProfile]):
        self.experts = expert_profiles

        # Weights for scoring
        self.weights = {
            "specialization": 0.25,
            "jurisdiction": 0.15,
            "language": 0.10,
            "experience": 0.10,
            "availability": 0.10,
            "rating": 0.10,
            "response_time": 0.05,
            "budget": 0.05,
            "skill_match": 0.05,
            "verification": 0.05
        }

        # Specialization compatibility matrix
        self.specialization_compatibility = self._build_compatibility_matrix()

    def _build_compatibility_matrix(self) -> Dict[str, List[ExpertSpecialization]]:
        """Build matrix of related specializations."""
        return {
            "custody": [
                ExpertSpecialization.CUSTODY_LAW,
                ExpertSpecialization.FAMILY_LAW,
                ExpertSpecialization.CHILD_PSYCHOLOGY,
                ExpertSpecialization.GUARDIAN_AD_LITEM,
                ExpertSpecialization.FAMILY_THERAPY
            ],
            "protection": [
                ExpertSpecialization.CHILD_PROTECTION,
                ExpertSpecialization.CHILD_WELFARE,
                ExpertSpecialization.SOCIAL_SERVICES,
                ExpertSpecialization.TRAUMA_SPECIALIST
            ],
            "domestic_violence": [
                ExpertSpecialization.DOMESTIC_VIOLENCE,
                ExpertSpecialization.TRAUMA_SPECIALIST,
                ExpertSpecialization.FAMILY_LAW,
                ExpertSpecialization.FORENSIC_PSYCHOLOGY
            ],
            "alienation": [
                ExpertSpecialization.PARENTAL_ALIENATION,
                ExpertSpecialization.CHILD_PSYCHOLOGY,
                ExpertSpecialization.FORENSIC_PSYCHOLOGY,
                ExpertSpecialization.FAMILY_THERAPY
            ],
            "international": [
                ExpertSpecialization.INTERNATIONAL_FAMILY_LAW,
                ExpertSpecialization.FAMILY_LAW,
                ExpertSpecialization.TRANSLATION,
                ExpertSpecialization.CULTURAL_MEDIATION
            ],
            "forensic": [
                ExpertSpecialization.DIGITAL_FORENSICS,
                ExpertSpecialization.VOICE_ANALYSIS,
                ExpertSpecialization.DOCUMENT_ANALYSIS,
                ExpertSpecialization.FORENSIC_PSYCHOLOGY
            ]
        }

    def match(
        self,
        criteria: MatchCriteria,
        max_recommendations: int = 5
    ) -> MatchResult:
        """Match a case with suitable experts."""
        recommendations: List[ExpertRecommendation] = []
        unmatched_reasons: List[str] = []

        # Filter and score experts
        scored_experts: List[Tuple[ExpertProfile, MatchScore, List[str], List[str]]] = []

        for expert in self.experts.values():
            # Basic eligibility checks
            if not expert.is_active:
                continue

            if expert.verification_status != VerificationStatus.VERIFIED:
                continue

            if not expert.availability.accepts_new_cases:
                continue

            # Check availability capacity
            if expert.availability.current_active_cases >= expert.availability.max_active_cases:
                continue

            # Pro bono check
            if criteria.pro_bono_eligible and not expert.availability.pro_bono_available:
                continue

            # Calculate match score
            score, reasons, concerns = self._calculate_match_score(expert, criteria)

            if score.total_score >= 30:  # Minimum threshold
                scored_experts.append((expert, score, reasons, concerns))

        # Sort by total score
        scored_experts.sort(key=lambda x: x[1].total_score, reverse=True)

        # Create recommendations
        for rank, (expert, score, reasons, concerns) in enumerate(scored_experts[:max_recommendations], 1):
            rec = ExpertRecommendation(
                expert=expert,
                match_score=score,
                ranking=rank,
                match_reasons=reasons,
                concerns=concerns,
                estimated_response_time=f"{expert.availability.response_time_hours} hours",
                estimated_cost=self._estimate_cost(expert, criteria)
            )
            recommendations.append(rec)

        # Identify unmatched criteria
        unmatched_reasons = self._identify_unmatched(criteria, scored_experts)

        # Generate alternative suggestions
        alternative_suggestions = self._generate_alternatives(criteria, recommendations)

        return MatchResult(
            case_id=criteria.case_id,
            matched_at=datetime.datetime.now().isoformat(),
            total_experts_considered=len(self.experts),
            recommendations=recommendations,
            unmatched_reasons=unmatched_reasons,
            alternative_suggestions=alternative_suggestions
        )

    def _calculate_match_score(
        self,
        expert: ExpertProfile,
        criteria: MatchCriteria
    ) -> Tuple[MatchScore, List[str], List[str]]:
        """Calculate detailed match score."""
        reasons = []
        concerns = []

        # Specialization score
        spec_score = self._score_specialization(expert, criteria)
        if spec_score > 0.8:
            reasons.append(f"Strong specialization match: {expert.primary_specialization.value}")
        elif spec_score < 0.4:
            concerns.append("Limited specialization match")

        # Jurisdiction score
        jur_score = self._score_jurisdiction(expert, criteria)
        if jur_score >= 1.0:
            reasons.append(f"Serves required jurisdictions: {', '.join(criteria.jurisdictions[:2])}")

        # Language score
        lang_score = self._score_language(expert, criteria)
        if lang_score >= 1.0:
            reasons.append(f"Speaks required languages")
        elif lang_score < 0.5:
            concerns.append("May require interpreter")

        # Experience score
        exp_score = self._score_experience(expert, criteria)
        if exp_score > 0.8:
            reasons.append(f"{expert.years_experience} years of experience")

        # Availability score
        avail_score = self._score_availability(expert, criteria)
        if avail_score < 0.5:
            concerns.append("Limited availability")

        # Rating score
        rating_score = min(expert.average_rating / 5.0, 1.0) if expert.total_reviews > 0 else 0.5
        if expert.average_rating >= 4.5 and expert.total_reviews >= 5:
            reasons.append(f"Highly rated: {expert.average_rating:.1f}/5.0 ({expert.total_reviews} reviews)")

        # Response time score
        response_score = self._score_response_time(expert, criteria)
        if criteria.urgency == Urgency.EMERGENCY and expert.availability.response_time_hours > 24:
            concerns.append("Response time may not meet emergency needs")

        # Budget score
        budget_score = 1.0  # Simplified - would need pricing data
        if criteria.pro_bono_eligible and expert.availability.pro_bono_available:
            reasons.append("Pro bono available")

        # Skill match score
        skill_score = self._score_skills(expert, criteria)
        if skill_score > 0.7:
            reasons.append("Strong skill match for case requirements")

        # Verification score
        verif_score = expert.verification_level / 3.0

        # Calculate total
        total = (
            spec_score * self.weights["specialization"] +
            jur_score * self.weights["jurisdiction"] +
            lang_score * self.weights["language"] +
            exp_score * self.weights["experience"] +
            avail_score * self.weights["availability"] +
            rating_score * self.weights["rating"] +
            response_score * self.weights["response_time"] +
            budget_score * self.weights["budget"] +
            skill_score * self.weights["skill_match"] +
            verif_score * self.weights["verification"]
        ) * 100

        score = MatchScore(
            total_score=total,
            specialization_score=spec_score,
            jurisdiction_score=jur_score,
            language_score=lang_score,
            experience_score=exp_score,
            availability_score=avail_score,
            rating_score=rating_score,
            response_time_score=response_score,
            budget_score=budget_score,
            skill_match_score=skill_score,
            verification_score=verif_score
        )

        return score, reasons, concerns

    def _score_specialization(
        self,
        expert: ExpertProfile,
        criteria: MatchCriteria
    ) -> float:
        """Score based on specialization match."""
        score = 0.0

        # Check required specializations
        required_matches = sum(
            1 for s in criteria.required_specializations
            if s in expert.specializations
        )
        if criteria.required_specializations:
            score += (required_matches / len(criteria.required_specializations)) * 0.7

        # Check preferred specializations
        preferred_matches = sum(
            1 for s in criteria.preferred_specializations
            if s in expert.specializations
        )
        if criteria.preferred_specializations:
            score += (preferred_matches / len(criteria.preferred_specializations)) * 0.3

        # Check related specializations
        case_related = self.specialization_compatibility.get(criteria.case_type, [])
        if case_related:
            related_matches = sum(1 for s in case_related if s in expert.specializations)
            score = max(score, (related_matches / len(case_related)) * 0.6)

        return min(score, 1.0)

    def _score_jurisdiction(
        self,
        expert: ExpertProfile,
        criteria: MatchCriteria
    ) -> float:
        """Score based on jurisdiction coverage."""
        if not criteria.jurisdictions:
            return 1.0

        matches = sum(
            1 for j in criteria.jurisdictions
            if j in expert.availability.jurisdictions_served
        )
        return matches / len(criteria.jurisdictions)

    def _score_language(
        self,
        expert: ExpertProfile,
        criteria: MatchCriteria
    ) -> float:
        """Score based on language capability."""
        if not criteria.languages:
            return 1.0

        matches = sum(
            1 for l in criteria.languages
            if l in expert.availability.languages
        )
        return matches / len(criteria.languages)

    def _score_experience(
        self,
        expert: ExpertProfile,
        criteria: MatchCriteria
    ) -> float:
        """Score based on experience level."""
        complexity_years = {
            CaseComplexity.SIMPLE: 2,
            CaseComplexity.MODERATE: 5,
            CaseComplexity.COMPLEX: 10,
            CaseComplexity.HIGHLY_COMPLEX: 15
        }

        required_years = complexity_years.get(criteria.complexity, 5)

        if expert.years_experience >= required_years:
            return 1.0
        else:
            return expert.years_experience / required_years

    def _score_availability(
        self,
        expert: ExpertProfile,
        criteria: MatchCriteria
    ) -> float:
        """Score based on availability."""
        # Calculate remaining capacity
        remaining_capacity = (
            expert.availability.max_active_cases -
            expert.availability.current_active_cases
        )

        if remaining_capacity <= 0:
            return 0.0

        capacity_ratio = remaining_capacity / expert.availability.max_active_cases

        # Consider hours available
        complexity_hours = {
            CaseComplexity.SIMPLE: 5,
            CaseComplexity.MODERATE: 10,
            CaseComplexity.COMPLEX: 15,
            CaseComplexity.HIGHLY_COMPLEX: 20
        }

        needed_hours = complexity_hours.get(criteria.complexity, 10)
        hours_available = expert.availability.available_hours_per_week

        hours_score = min(hours_available / needed_hours, 1.0)

        return (capacity_ratio + hours_score) / 2

    def _score_response_time(
        self,
        expert: ExpertProfile,
        criteria: MatchCriteria
    ) -> float:
        """Score based on response time vs urgency."""
        urgency_hours = {
            Urgency.ROUTINE: 72,
            Urgency.ELEVATED: 48,
            Urgency.URGENT: 24,
            Urgency.EMERGENCY: 4
        }

        max_acceptable = urgency_hours.get(criteria.urgency, 48)
        expert_response = expert.availability.response_time_hours

        if expert_response <= max_acceptable:
            return 1.0
        else:
            return max(0, 1 - (expert_response - max_acceptable) / max_acceptable)

    def _score_skills(
        self,
        expert: ExpertProfile,
        criteria: MatchCriteria
    ) -> float:
        """Score based on specific skill requirements."""
        if not criteria.specific_skills:
            return 0.7  # Neutral score if no specific skills required

        # Map skills to specializations
        skill_specialization_map = {
            "parental alienation": ExpertSpecialization.PARENTAL_ALIENATION,
            "digital forensics": ExpertSpecialization.DIGITAL_FORENSICS,
            "trauma": ExpertSpecialization.TRAUMA_SPECIALIST,
            "child psychology": ExpertSpecialization.CHILD_PSYCHOLOGY,
            "mediation": ExpertSpecialization.MEDIATION,
            "international": ExpertSpecialization.INTERNATIONAL_FAMILY_LAW,
            "voice analysis": ExpertSpecialization.VOICE_ANALYSIS,
            "cultural": ExpertSpecialization.CULTURAL_MEDIATION
        }

        matches = 0
        for skill in criteria.specific_skills:
            skill_lower = skill.lower()
            for keyword, spec in skill_specialization_map.items():
                if keyword in skill_lower and spec in expert.specializations:
                    matches += 1
                    break

        return matches / len(criteria.specific_skills) if criteria.specific_skills else 0.7

    def _estimate_cost(
        self,
        expert: ExpertProfile,
        criteria: MatchCriteria
    ) -> Optional[str]:
        """Estimate cost for engagement."""
        if criteria.pro_bono_eligible and expert.availability.pro_bono_available:
            return "Pro bono available"

        # Simplified cost estimation
        complexity_hours = {
            CaseComplexity.SIMPLE: "5-10 hours",
            CaseComplexity.MODERATE: "10-20 hours",
            CaseComplexity.COMPLEX: "20-40 hours",
            CaseComplexity.HIGHLY_COMPLEX: "40+ hours"
        }

        return f"Estimated: {complexity_hours.get(criteria.complexity, 'Variable')}"

    def _identify_unmatched(
        self,
        criteria: MatchCriteria,
        scored_experts: List
    ) -> List[str]:
        """Identify criteria that couldn't be fully matched."""
        unmatched = []

        if not scored_experts:
            unmatched.append("No experts found matching minimum requirements")
            return unmatched

        # Check if any required specializations were fully matched
        for spec in criteria.required_specializations:
            has_match = any(
                spec in expert.specializations
                for expert, _, _, _ in scored_experts[:5]
            )
            if not has_match:
                unmatched.append(f"Limited availability for specialization: {spec.value}")

        # Check jurisdiction coverage
        for jur in criteria.jurisdictions:
            has_match = any(
                jur in expert.availability.jurisdictions_served
                for expert, _, _, _ in scored_experts[:5]
            )
            if not has_match:
                unmatched.append(f"Limited expert coverage in jurisdiction: {jur}")

        # Check language coverage
        for lang in criteria.languages:
            has_match = any(
                lang in expert.availability.languages
                for expert, _, _, _ in scored_experts[:5]
            )
            if not has_match:
                unmatched.append(f"Limited experts speaking: {lang}")

        return unmatched

    def _generate_alternatives(
        self,
        criteria: MatchCriteria,
        recommendations: List[ExpertRecommendation]
    ) -> List[str]:
        """Generate alternative suggestions."""
        suggestions = []

        if len(recommendations) < 3:
            suggestions.append("Consider broadening jurisdiction requirements")
            suggestions.append("Consider experts from related specializations")

        if criteria.urgency == Urgency.EMERGENCY and not recommendations:
            suggestions.append("For emergency cases, consider contacting local bar association")
            suggestions.append("Legal aid hotlines may provide immediate assistance")

        if criteria.pro_bono_eligible and len(recommendations) == 0:
            suggestions.append("Pro bono capacity is limited - consider partial fee assistance programs")
            suggestions.append("University law clinics may offer free assistance")

        return suggestions

    def quick_match(
        self,
        case_type: str,
        jurisdiction: str,
        urgency: Urgency = Urgency.ROUTINE
    ) -> List[ExpertRecommendation]:
        """Quick match with minimal criteria."""
        criteria = MatchCriteria(
            case_id="quick_match",
            case_type=case_type,
            required_specializations=self.specialization_compatibility.get(case_type, [])[:2],
            preferred_specializations=[],
            jurisdictions=[jurisdiction],
            languages=["en"],
            complexity=CaseComplexity.MODERATE,
            urgency=urgency,
            budget_range=None,
            pro_bono_eligible=False,
            requires_court_testimony=False,
            specific_skills=[],
            cultural_considerations=[],
            case_description=""
        )

        result = self.match(criteria, max_recommendations=3)
        return result.recommendations
