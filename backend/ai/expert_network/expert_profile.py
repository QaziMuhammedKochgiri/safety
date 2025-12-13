"""
Expert Profile
Expert profile management and verification system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import datetime
import hashlib


class ExpertSpecialization(str, Enum):
    """Areas of expert specialization."""
    # Legal
    FAMILY_LAW = "family_law"
    CUSTODY_LAW = "custody_law"
    CHILD_PROTECTION = "child_protection"
    DOMESTIC_VIOLENCE = "domestic_violence"
    INTERNATIONAL_FAMILY_LAW = "international_family_law"
    MEDIATION = "mediation"

    # Mental Health
    CHILD_PSYCHOLOGY = "child_psychology"
    FORENSIC_PSYCHOLOGY = "forensic_psychology"
    TRAUMA_SPECIALIST = "trauma_specialist"
    FAMILY_THERAPY = "family_therapy"
    PARENTAL_ALIENATION = "parental_alienation"

    # Social Work
    CHILD_WELFARE = "child_welfare"
    SOCIAL_SERVICES = "social_services"
    GUARDIAN_AD_LITEM = "guardian_ad_litem"

    # Forensics
    DIGITAL_FORENSICS = "digital_forensics"
    VOICE_ANALYSIS = "voice_analysis"
    DOCUMENT_ANALYSIS = "document_analysis"

    # Other
    FINANCIAL_ANALYSIS = "financial_analysis"
    TRANSLATION = "translation"
    CULTURAL_MEDIATION = "cultural_mediation"


class VerificationStatus(str, Enum):
    """Expert verification status."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class CredentialType(str, Enum):
    """Types of professional credentials."""
    BAR_ADMISSION = "bar_admission"
    LICENSE = "license"
    CERTIFICATION = "certification"
    DEGREE = "degree"
    PROFESSIONAL_MEMBERSHIP = "professional_membership"
    COURT_REGISTRATION = "court_registration"
    SPECIALIZATION_CERT = "specialization_cert"


@dataclass
class ExpertCredential:
    """A professional credential or certification."""
    credential_id: str
    credential_type: CredentialType
    issuer: str
    credential_number: str
    title: str
    issue_date: str
    expiry_date: Optional[str]
    jurisdiction: str
    verification_status: VerificationStatus
    verification_date: Optional[str]
    verification_method: str
    document_hash: Optional[str]  # Hash of uploaded document
    notes: str = ""


@dataclass
class ExpertAvailability:
    """Expert availability settings."""
    accepts_new_cases: bool
    max_active_cases: int
    current_active_cases: int
    available_hours_per_week: float
    timezone: str
    preferred_consultation_types: List[str]
    languages: List[str]
    jurisdictions_served: List[str]
    pro_bono_available: bool
    pro_bono_hours_per_month: float
    response_time_hours: int  # Typical response time


@dataclass
class ExpertProfile:
    """Complete expert profile."""
    expert_id: str
    user_id: str  # Link to user account

    # Basic info
    title: str  # Dr., Prof., etc.
    first_name: str
    last_name: str
    display_name: str
    email: str
    phone: Optional[str]

    # Professional info
    specializations: List[ExpertSpecialization]
    primary_specialization: ExpertSpecialization
    credentials: List[ExpertCredential]
    years_experience: int
    bio: str
    practice_name: Optional[str]
    practice_address: Optional[str]

    # Verification
    verification_status: VerificationStatus
    verification_level: int  # 1-3, higher is more verified
    verified_date: Optional[str]
    last_verification_check: Optional[str]

    # Availability
    availability: ExpertAvailability

    # Statistics
    total_consultations: int
    total_cases_assisted: int
    average_rating: float
    total_reviews: int
    pro_bono_cases_completed: int
    articles_contributed: int

    # Profile
    profile_photo_url: Optional[str]
    website_url: Optional[str]
    linkedin_url: Optional[str]
    professional_memberships: List[str]

    # Metadata
    created_at: str
    updated_at: str
    last_active: str
    is_active: bool


@dataclass
class VerificationRequest:
    """Request for expert verification."""
    request_id: str
    expert_id: str
    credential_ids: List[str]
    submitted_at: str
    status: VerificationStatus
    reviewer_notes: str
    documents_submitted: List[str]
    verification_deadline: Optional[str]


class ExpertManager:
    """Manages expert profiles and verification."""

    def __init__(self):
        self.experts: Dict[str, ExpertProfile] = {}
        self.verification_requests: Dict[str, VerificationRequest] = {}
        self.verification_log: List[Dict[str, Any]] = []

    def create_profile(
        self,
        user_id: str,
        first_name: str,
        last_name: str,
        email: str,
        specializations: List[ExpertSpecialization],
        years_experience: int,
        bio: str,
        title: str = "",
        practice_name: Optional[str] = None
    ) -> ExpertProfile:
        """Create a new expert profile."""
        expert_id = hashlib.md5(f"{user_id}-{email}".encode()).hexdigest()[:12]

        # Default availability
        availability = ExpertAvailability(
            accepts_new_cases=True,
            max_active_cases=10,
            current_active_cases=0,
            available_hours_per_week=20.0,
            timezone="UTC",
            preferred_consultation_types=["video", "phone", "email"],
            languages=["en"],
            jurisdictions_served=["germany"],
            pro_bono_available=False,
            pro_bono_hours_per_month=0.0,
            response_time_hours=48
        )

        now = datetime.datetime.now().isoformat()

        profile = ExpertProfile(
            expert_id=expert_id,
            user_id=user_id,
            title=title,
            first_name=first_name,
            last_name=last_name,
            display_name=f"{title} {first_name} {last_name}".strip(),
            email=email,
            phone=None,
            specializations=specializations,
            primary_specialization=specializations[0] if specializations else ExpertSpecialization.FAMILY_LAW,
            credentials=[],
            years_experience=years_experience,
            bio=bio,
            practice_name=practice_name,
            practice_address=None,
            verification_status=VerificationStatus.PENDING,
            verification_level=0,
            verified_date=None,
            last_verification_check=None,
            availability=availability,
            total_consultations=0,
            total_cases_assisted=0,
            average_rating=0.0,
            total_reviews=0,
            pro_bono_cases_completed=0,
            articles_contributed=0,
            profile_photo_url=None,
            website_url=None,
            linkedin_url=None,
            professional_memberships=[],
            created_at=now,
            updated_at=now,
            last_active=now,
            is_active=True
        )

        self.experts[expert_id] = profile
        return profile

    def add_credential(
        self,
        expert_id: str,
        credential_type: CredentialType,
        issuer: str,
        credential_number: str,
        title: str,
        issue_date: str,
        jurisdiction: str,
        expiry_date: Optional[str] = None,
        document_path: Optional[str] = None
    ) -> ExpertCredential:
        """Add a credential to an expert profile."""
        if expert_id not in self.experts:
            raise ValueError(f"Expert {expert_id} not found")

        credential_id = hashlib.md5(
            f"{expert_id}-{credential_number}".encode()
        ).hexdigest()[:10]

        # Calculate document hash if provided
        document_hash = None
        if document_path:
            document_hash = self._calculate_file_hash(document_path)

        credential = ExpertCredential(
            credential_id=credential_id,
            credential_type=credential_type,
            issuer=issuer,
            credential_number=credential_number,
            title=title,
            issue_date=issue_date,
            expiry_date=expiry_date,
            jurisdiction=jurisdiction,
            verification_status=VerificationStatus.PENDING,
            verification_date=None,
            verification_method="manual_review",
            document_hash=document_hash
        )

        self.experts[expert_id].credentials.append(credential)
        self.experts[expert_id].updated_at = datetime.datetime.now().isoformat()

        return credential

    def request_verification(
        self,
        expert_id: str,
        credential_ids: Optional[List[str]] = None
    ) -> VerificationRequest:
        """Request verification for an expert."""
        if expert_id not in self.experts:
            raise ValueError(f"Expert {expert_id} not found")

        expert = self.experts[expert_id]

        # If no specific credentials, request verification for all pending ones
        if credential_ids is None:
            credential_ids = [
                c.credential_id for c in expert.credentials
                if c.verification_status == VerificationStatus.PENDING
            ]

        request_id = hashlib.md5(
            f"{expert_id}-{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        request = VerificationRequest(
            request_id=request_id,
            expert_id=expert_id,
            credential_ids=credential_ids,
            submitted_at=datetime.datetime.now().isoformat(),
            status=VerificationStatus.IN_REVIEW,
            reviewer_notes="",
            documents_submitted=[
                c.document_hash for c in expert.credentials
                if c.credential_id in credential_ids and c.document_hash
            ],
            verification_deadline=(
                datetime.datetime.now() + datetime.timedelta(days=14)
            ).isoformat()
        )

        self.verification_requests[request_id] = request

        # Update expert status
        expert.verification_status = VerificationStatus.IN_REVIEW
        expert.updated_at = datetime.datetime.now().isoformat()

        return request

    def complete_verification(
        self,
        request_id: str,
        approved: bool,
        reviewer_notes: str,
        verification_level: int = 1
    ) -> Tuple[bool, str]:
        """Complete a verification request."""
        if request_id not in self.verification_requests:
            return False, "Verification request not found"

        request = self.verification_requests[request_id]
        expert = self.experts.get(request.expert_id)

        if not expert:
            return False, "Expert not found"

        now = datetime.datetime.now().isoformat()

        if approved:
            request.status = VerificationStatus.VERIFIED

            # Update credentials
            for cred in expert.credentials:
                if cred.credential_id in request.credential_ids:
                    cred.verification_status = VerificationStatus.VERIFIED
                    cred.verification_date = now

            # Update expert profile
            expert.verification_status = VerificationStatus.VERIFIED
            expert.verification_level = verification_level
            expert.verified_date = now
            expert.last_verification_check = now

            message = f"Expert {expert.display_name} verified at level {verification_level}"
        else:
            request.status = VerificationStatus.REJECTED

            # Update credentials
            for cred in expert.credentials:
                if cred.credential_id in request.credential_ids:
                    cred.verification_status = VerificationStatus.REJECTED

            expert.verification_status = VerificationStatus.REJECTED
            message = f"Expert {expert.display_name} verification rejected"

        request.reviewer_notes = reviewer_notes
        expert.updated_at = now

        # Log verification
        self.verification_log.append({
            "request_id": request_id,
            "expert_id": expert.expert_id,
            "approved": approved,
            "verification_level": verification_level if approved else 0,
            "reviewer_notes": reviewer_notes,
            "timestamp": now
        })

        return True, message

    def update_availability(
        self,
        expert_id: str,
        availability: ExpertAvailability
    ) -> bool:
        """Update expert availability settings."""
        if expert_id not in self.experts:
            return False

        self.experts[expert_id].availability = availability
        self.experts[expert_id].updated_at = datetime.datetime.now().isoformat()
        return True

    def search_experts(
        self,
        specializations: Optional[List[ExpertSpecialization]] = None,
        jurisdictions: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        verified_only: bool = True,
        pro_bono_only: bool = False,
        min_rating: float = 0.0,
        max_results: int = 20
    ) -> List[ExpertProfile]:
        """Search for experts based on criteria."""
        results = []

        for expert in self.experts.values():
            # Active check
            if not expert.is_active:
                continue

            # Verification check
            if verified_only and expert.verification_status != VerificationStatus.VERIFIED:
                continue

            # Availability check
            if not expert.availability.accepts_new_cases:
                continue

            # Pro bono check
            if pro_bono_only and not expert.availability.pro_bono_available:
                continue

            # Rating check
            if expert.average_rating < min_rating:
                continue

            # Specialization check
            if specializations:
                if not any(s in expert.specializations for s in specializations):
                    continue

            # Jurisdiction check
            if jurisdictions:
                if not any(j in expert.availability.jurisdictions_served for j in jurisdictions):
                    continue

            # Language check
            if languages:
                if not any(l in expert.availability.languages for l in languages):
                    continue

            results.append(expert)

        # Sort by rating and verification level
        results.sort(
            key=lambda e: (e.verification_level, e.average_rating),
            reverse=True
        )

        return results[:max_results]

    def get_expert(self, expert_id: str) -> Optional[ExpertProfile]:
        """Get an expert by ID."""
        return self.experts.get(expert_id)

    def get_experts_by_specialization(
        self,
        specialization: ExpertSpecialization
    ) -> List[ExpertProfile]:
        """Get all experts with a specific specialization."""
        return [
            e for e in self.experts.values()
            if specialization in e.specializations
            and e.is_active
            and e.verification_status == VerificationStatus.VERIFIED
        ]

    def update_statistics(
        self,
        expert_id: str,
        consultation_completed: bool = False,
        case_assisted: bool = False,
        new_rating: Optional[float] = None,
        pro_bono_completed: bool = False,
        article_contributed: bool = False
    ):
        """Update expert statistics."""
        if expert_id not in self.experts:
            return

        expert = self.experts[expert_id]

        if consultation_completed:
            expert.total_consultations += 1

        if case_assisted:
            expert.total_cases_assisted += 1

        if new_rating is not None:
            # Calculate new average
            total_rating = expert.average_rating * expert.total_reviews
            expert.total_reviews += 1
            expert.average_rating = (total_rating + new_rating) / expert.total_reviews

        if pro_bono_completed:
            expert.pro_bono_cases_completed += 1

        if article_contributed:
            expert.articles_contributed += 1

        expert.last_active = datetime.datetime.now().isoformat()
        expert.updated_at = datetime.datetime.now().isoformat()

    def deactivate_expert(self, expert_id: str, reason: str) -> bool:
        """Deactivate an expert profile."""
        if expert_id not in self.experts:
            return False

        expert = self.experts[expert_id]
        expert.is_active = False
        expert.updated_at = datetime.datetime.now().isoformat()

        self.verification_log.append({
            "event": "deactivation",
            "expert_id": expert_id,
            "reason": reason,
            "timestamp": datetime.datetime.now().isoformat()
        })

        return True

    def check_credential_expiry(self) -> List[Dict[str, Any]]:
        """Check for expiring credentials."""
        expiring = []
        now = datetime.datetime.now()
        warning_period = datetime.timedelta(days=30)

        for expert in self.experts.values():
            for cred in expert.credentials:
                if cred.expiry_date:
                    expiry = datetime.datetime.fromisoformat(cred.expiry_date)
                    if expiry <= now + warning_period:
                        expiring.append({
                            "expert_id": expert.expert_id,
                            "expert_name": expert.display_name,
                            "credential_id": cred.credential_id,
                            "credential_title": cred.title,
                            "expiry_date": cred.expiry_date,
                            "is_expired": expiry <= now
                        })

        return expiring

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file."""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return hashlib.sha256(file_path.encode()).hexdigest()

    def export_expert_directory(
        self,
        verified_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Export expert directory for public listing."""
        directory = []

        for expert in self.experts.values():
            if not expert.is_active:
                continue
            if verified_only and expert.verification_status != VerificationStatus.VERIFIED:
                continue

            directory.append({
                "expert_id": expert.expert_id,
                "display_name": expert.display_name,
                "title": expert.title,
                "specializations": [s.value for s in expert.specializations],
                "primary_specialization": expert.primary_specialization.value,
                "years_experience": expert.years_experience,
                "verification_level": expert.verification_level,
                "average_rating": expert.average_rating,
                "total_reviews": expert.total_reviews,
                "jurisdictions_served": expert.availability.jurisdictions_served,
                "languages": expert.availability.languages,
                "accepts_new_cases": expert.availability.accepts_new_cases,
                "pro_bono_available": expert.availability.pro_bono_available,
                "response_time_hours": expert.availability.response_time_hours
            })

        return directory
