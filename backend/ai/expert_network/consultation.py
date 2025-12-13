"""
Consultation Management
Consultation scheduling and management system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import datetime
import hashlib


class ConsultationType(str, Enum):
    """Types of consultations."""
    VIDEO_CALL = "video_call"
    PHONE_CALL = "phone_call"
    IN_PERSON = "in_person"
    EMAIL = "email"
    DOCUMENT_REVIEW = "document_review"
    COURT_TESTIMONY = "court_testimony"
    MEDIATION = "mediation"
    EXPERT_REPORT = "expert_report"


class ConsultationStatus(str, Enum):
    """Status of a consultation."""
    REQUESTED = "requested"
    PENDING_PAYMENT = "pending_payment"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


@dataclass
class ConsultationRequest:
    """Request for a consultation."""
    request_id: str
    case_id: str
    client_id: str
    expert_id: str
    consultation_type: ConsultationType
    requested_at: str
    preferred_times: List[str]  # ISO datetime strings
    duration_minutes: int
    urgency: str
    description: str
    documents_attached: List[str]
    is_pro_bono: bool
    status: ConsultationStatus


@dataclass
class Consultation:
    """A scheduled consultation."""
    consultation_id: str
    request_id: str
    case_id: str
    client_id: str
    expert_id: str

    # Scheduling
    consultation_type: ConsultationType
    scheduled_start: str
    scheduled_end: str
    timezone: str
    location: Optional[str]  # For in-person or video link

    # Status
    status: ConsultationStatus
    actual_start: Optional[str]
    actual_end: Optional[str]
    actual_duration_minutes: Optional[int]

    # Content
    agenda: str
    notes: str
    outcomes: List[str]
    action_items: List[str]
    documents_discussed: List[str]
    documents_produced: List[str]

    # Follow-up
    follow_up_required: bool
    follow_up_date: Optional[str]
    next_steps: List[str]

    # Billing
    is_pro_bono: bool
    fee_amount: Optional[float]
    fee_currency: str
    payment_status: str
    invoice_id: Optional[str]

    # Metadata
    created_at: str
    updated_at: str
    cancelled_at: Optional[str]
    cancellation_reason: Optional[str]


@dataclass
class ConsultationFeedback:
    """Feedback after a consultation."""
    feedback_id: str
    consultation_id: str
    from_client: bool  # True if from client, False if from expert
    rating: int  # 1-5
    communication_rating: int
    expertise_rating: int
    professionalism_rating: int
    value_rating: int
    would_recommend: bool
    comments: str
    submitted_at: str
    is_public: bool


class ConsultationManager:
    """Manages consultations between clients and experts."""

    def __init__(self):
        self.requests: Dict[str, ConsultationRequest] = {}
        self.consultations: Dict[str, Consultation] = {}
        self.feedback: Dict[str, ConsultationFeedback] = {}

    def create_request(
        self,
        case_id: str,
        client_id: str,
        expert_id: str,
        consultation_type: ConsultationType,
        preferred_times: List[str],
        duration_minutes: int,
        description: str,
        urgency: str = "routine",
        documents: Optional[List[str]] = None,
        is_pro_bono: bool = False
    ) -> ConsultationRequest:
        """Create a consultation request."""
        request_id = hashlib.md5(
            f"{case_id}-{expert_id}-{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        request = ConsultationRequest(
            request_id=request_id,
            case_id=case_id,
            client_id=client_id,
            expert_id=expert_id,
            consultation_type=consultation_type,
            requested_at=datetime.datetime.now().isoformat(),
            preferred_times=preferred_times,
            duration_minutes=duration_minutes,
            urgency=urgency,
            description=description,
            documents_attached=documents or [],
            is_pro_bono=is_pro_bono,
            status=ConsultationStatus.REQUESTED
        )

        self.requests[request_id] = request
        return request

    def schedule_consultation(
        self,
        request_id: str,
        scheduled_start: str,
        scheduled_end: str,
        timezone: str,
        location: Optional[str] = None,
        agenda: str = "",
        fee_amount: Optional[float] = None,
        fee_currency: str = "EUR"
    ) -> Consultation:
        """Schedule a consultation from a request."""
        if request_id not in self.requests:
            raise ValueError(f"Request {request_id} not found")

        request = self.requests[request_id]
        consultation_id = hashlib.md5(
            f"{request_id}-{scheduled_start}".encode()
        ).hexdigest()[:12]

        now = datetime.datetime.now().isoformat()

        consultation = Consultation(
            consultation_id=consultation_id,
            request_id=request_id,
            case_id=request.case_id,
            client_id=request.client_id,
            expert_id=request.expert_id,
            consultation_type=request.consultation_type,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            timezone=timezone,
            location=location,
            status=ConsultationStatus.SCHEDULED,
            actual_start=None,
            actual_end=None,
            actual_duration_minutes=None,
            agenda=agenda,
            notes="",
            outcomes=[],
            action_items=[],
            documents_discussed=request.documents_attached,
            documents_produced=[],
            follow_up_required=False,
            follow_up_date=None,
            next_steps=[],
            is_pro_bono=request.is_pro_bono,
            fee_amount=fee_amount if not request.is_pro_bono else None,
            fee_currency=fee_currency,
            payment_status="pending" if fee_amount else "not_applicable",
            invoice_id=None,
            created_at=now,
            updated_at=now,
            cancelled_at=None,
            cancellation_reason=None
        )

        self.consultations[consultation_id] = consultation
        request.status = ConsultationStatus.SCHEDULED

        return consultation

    def start_consultation(self, consultation_id: str) -> bool:
        """Mark a consultation as started."""
        if consultation_id not in self.consultations:
            return False

        consultation = self.consultations[consultation_id]
        consultation.status = ConsultationStatus.IN_PROGRESS
        consultation.actual_start = datetime.datetime.now().isoformat()
        consultation.updated_at = datetime.datetime.now().isoformat()
        return True

    def complete_consultation(
        self,
        consultation_id: str,
        notes: str,
        outcomes: List[str],
        action_items: List[str],
        documents_produced: Optional[List[str]] = None,
        follow_up_required: bool = False,
        follow_up_date: Optional[str] = None,
        next_steps: Optional[List[str]] = None
    ) -> bool:
        """Complete a consultation with details."""
        if consultation_id not in self.consultations:
            return False

        consultation = self.consultations[consultation_id]
        now = datetime.datetime.now()

        consultation.status = ConsultationStatus.COMPLETED
        consultation.actual_end = now.isoformat()

        if consultation.actual_start:
            start = datetime.datetime.fromisoformat(consultation.actual_start)
            consultation.actual_duration_minutes = int((now - start).total_seconds() / 60)

        consultation.notes = notes
        consultation.outcomes = outcomes
        consultation.action_items = action_items
        consultation.documents_produced = documents_produced or []
        consultation.follow_up_required = follow_up_required
        consultation.follow_up_date = follow_up_date
        consultation.next_steps = next_steps or []
        consultation.updated_at = now.isoformat()

        return True

    def cancel_consultation(
        self,
        consultation_id: str,
        reason: str,
        cancelled_by: str  # "client" or "expert"
    ) -> bool:
        """Cancel a consultation."""
        if consultation_id not in self.consultations:
            return False

        consultation = self.consultations[consultation_id]
        now = datetime.datetime.now().isoformat()

        consultation.status = ConsultationStatus.CANCELLED
        consultation.cancelled_at = now
        consultation.cancellation_reason = f"{cancelled_by}: {reason}"
        consultation.updated_at = now

        # Update request status
        if consultation.request_id in self.requests:
            self.requests[consultation.request_id].status = ConsultationStatus.CANCELLED

        return True

    def reschedule_consultation(
        self,
        consultation_id: str,
        new_start: str,
        new_end: str,
        reason: str
    ) -> Optional[Consultation]:
        """Reschedule a consultation."""
        if consultation_id not in self.consultations:
            return None

        old_consultation = self.consultations[consultation_id]
        old_consultation.status = ConsultationStatus.RESCHEDULED
        old_consultation.updated_at = datetime.datetime.now().isoformat()

        # Create new consultation
        new_consultation = Consultation(
            consultation_id=hashlib.md5(
                f"{consultation_id}-reschedule-{new_start}".encode()
            ).hexdigest()[:12],
            request_id=old_consultation.request_id,
            case_id=old_consultation.case_id,
            client_id=old_consultation.client_id,
            expert_id=old_consultation.expert_id,
            consultation_type=old_consultation.consultation_type,
            scheduled_start=new_start,
            scheduled_end=new_end,
            timezone=old_consultation.timezone,
            location=old_consultation.location,
            status=ConsultationStatus.SCHEDULED,
            actual_start=None,
            actual_end=None,
            actual_duration_minutes=None,
            agenda=old_consultation.agenda,
            notes=f"Rescheduled from {consultation_id}: {reason}",
            outcomes=[],
            action_items=[],
            documents_discussed=old_consultation.documents_discussed,
            documents_produced=[],
            follow_up_required=False,
            follow_up_date=None,
            next_steps=[],
            is_pro_bono=old_consultation.is_pro_bono,
            fee_amount=old_consultation.fee_amount,
            fee_currency=old_consultation.fee_currency,
            payment_status=old_consultation.payment_status,
            invoice_id=None,
            created_at=datetime.datetime.now().isoformat(),
            updated_at=datetime.datetime.now().isoformat(),
            cancelled_at=None,
            cancellation_reason=None
        )

        self.consultations[new_consultation.consultation_id] = new_consultation
        return new_consultation

    def submit_feedback(
        self,
        consultation_id: str,
        from_client: bool,
        rating: int,
        communication_rating: int,
        expertise_rating: int,
        professionalism_rating: int,
        value_rating: int,
        would_recommend: bool,
        comments: str,
        is_public: bool = True
    ) -> ConsultationFeedback:
        """Submit feedback for a consultation."""
        if consultation_id not in self.consultations:
            raise ValueError(f"Consultation {consultation_id} not found")

        feedback_id = hashlib.md5(
            f"{consultation_id}-{'client' if from_client else 'expert'}".encode()
        ).hexdigest()[:10]

        feedback = ConsultationFeedback(
            feedback_id=feedback_id,
            consultation_id=consultation_id,
            from_client=from_client,
            rating=max(1, min(5, rating)),
            communication_rating=max(1, min(5, communication_rating)),
            expertise_rating=max(1, min(5, expertise_rating)),
            professionalism_rating=max(1, min(5, professionalism_rating)),
            value_rating=max(1, min(5, value_rating)),
            would_recommend=would_recommend,
            comments=comments,
            submitted_at=datetime.datetime.now().isoformat(),
            is_public=is_public
        )

        self.feedback[feedback_id] = feedback
        return feedback

    def get_expert_consultations(
        self,
        expert_id: str,
        status: Optional[ConsultationStatus] = None
    ) -> List[Consultation]:
        """Get consultations for an expert."""
        consultations = [
            c for c in self.consultations.values()
            if c.expert_id == expert_id
        ]

        if status:
            consultations = [c for c in consultations if c.status == status]

        return sorted(consultations, key=lambda c: c.scheduled_start, reverse=True)

    def get_client_consultations(
        self,
        client_id: str,
        status: Optional[ConsultationStatus] = None
    ) -> List[Consultation]:
        """Get consultations for a client."""
        consultations = [
            c for c in self.consultations.values()
            if c.client_id == client_id
        ]

        if status:
            consultations = [c for c in consultations if c.status == status]

        return sorted(consultations, key=lambda c: c.scheduled_start, reverse=True)

    def get_upcoming_consultations(
        self,
        expert_id: Optional[str] = None,
        days_ahead: int = 7
    ) -> List[Consultation]:
        """Get upcoming consultations."""
        now = datetime.datetime.now()
        cutoff = now + datetime.timedelta(days=days_ahead)

        upcoming = []
        for c in self.consultations.values():
            if c.status != ConsultationStatus.SCHEDULED:
                continue

            if expert_id and c.expert_id != expert_id:
                continue

            scheduled = datetime.datetime.fromisoformat(c.scheduled_start)
            if now <= scheduled <= cutoff:
                upcoming.append(c)

        return sorted(upcoming, key=lambda c: c.scheduled_start)

    def get_consultation_statistics(
        self,
        expert_id: str
    ) -> Dict[str, Any]:
        """Get statistics for an expert's consultations."""
        consultations = [
            c for c in self.consultations.values()
            if c.expert_id == expert_id
        ]

        completed = [c for c in consultations if c.status == ConsultationStatus.COMPLETED]

        # Calculate average duration
        durations = [c.actual_duration_minutes for c in completed if c.actual_duration_minutes]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Get feedback
        expert_feedback = [
            f for f in self.feedback.values()
            if f.consultation_id in [c.consultation_id for c in completed]
            and f.from_client
        ]

        avg_rating = sum(f.rating for f in expert_feedback) / len(expert_feedback) if expert_feedback else 0

        return {
            "total_consultations": len(consultations),
            "completed": len(completed),
            "scheduled": len([c for c in consultations if c.status == ConsultationStatus.SCHEDULED]),
            "cancelled": len([c for c in consultations if c.status == ConsultationStatus.CANCELLED]),
            "average_duration_minutes": avg_duration,
            "average_rating": avg_rating,
            "total_feedback": len(expert_feedback),
            "pro_bono_completed": len([c for c in completed if c.is_pro_bono])
        }
