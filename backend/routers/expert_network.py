"""
Expert Network API Router
Provides endpoints for managing expert network, consultations, and knowledge base.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..ai.expert_network.expert_profile import ExpertManager, ExpertSpecialization
from ..ai.expert_network.case_matcher import CaseMatcher
from ..ai.expert_network.consultation import ConsultationManager
from ..ai.expert_network.review_system import ReviewSystem
from ..ai.expert_network.knowledge_base import KnowledgeBase
from ..ai.expert_network.pro_bono import ProBonoCoordinator
from .. import db

router = APIRouter(
    prefix="/experts",
    tags=["expert-network"],
    responses={404: {"description": "Not found"}},
)


# =============================================================================
# Enums
# =============================================================================

class ConsultationStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ExpertAvailability(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    ON_LEAVE = "on_leave"
    UNAVAILABLE = "unavailable"


# =============================================================================
# Pydantic Models
# =============================================================================

class ExpertCreate(BaseModel):
    """Model for creating expert profile."""
    name: str
    email: EmailStr
    phone: Optional[str] = None
    specializations: List[str]  # List of specialization IDs
    languages: List[str] = ["en"]
    bio: Optional[str] = None
    credentials: Optional[List[str]] = []
    hourly_rate: Optional[float] = None
    pro_bono_hours: Optional[int] = 0
    location: Optional[str] = None


class ExpertUpdate(BaseModel):
    """Model for updating expert profile."""
    name: Optional[str] = None
    phone: Optional[str] = None
    specializations: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    bio: Optional[str] = None
    credentials: Optional[List[str]] = None
    hourly_rate: Optional[float] = None
    availability: Optional[str] = None


class ExpertProfile(BaseModel):
    """Expert profile response model."""
    id: str
    name: str
    email: str
    specializations: List[str]
    languages: List[str]
    bio: Optional[str]
    credentials: List[str]
    hourly_rate: Optional[float]
    pro_bono_available: bool
    rating: float
    total_reviews: int
    availability: str
    verified: bool


class ConsultationCreate(BaseModel):
    """Model for creating consultation."""
    case_id: str
    expert_id: str
    client_id: str
    topic: str
    description: str
    preferred_date: datetime
    duration_minutes: int = 60
    is_pro_bono: bool = False


class ConsultationResponse(BaseModel):
    """Consultation response model."""
    id: str
    case_id: str
    expert_id: str
    expert_name: str
    client_id: str
    topic: str
    status: str
    scheduled_at: Optional[datetime]
    duration_minutes: int
    is_pro_bono: bool
    meeting_link: Optional[str]


class ReviewCreate(BaseModel):
    """Model for creating review."""
    consultation_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    anonymous: bool = False


class CaseMatchRequest(BaseModel):
    """Request for expert-case matching."""
    case_id: str
    case_type: str  # custody, alienation, forensics, etc
    required_languages: List[str] = []
    urgency: str = "normal"  # urgent, normal, low
    budget: Optional[float] = None
    pro_bono_eligible: bool = False


class MatchResult(BaseModel):
    """Expert match result."""
    expert_id: str
    expert_name: str
    match_score: float
    specialization_match: float
    language_match: float
    availability_match: float
    rating: float
    reasons: List[str]


class KnowledgeArticle(BaseModel):
    """Knowledge base article model."""
    id: str
    title: str
    category: str
    content: str
    tags: List[str]
    author_id: Optional[str]
    created_at: datetime
    views: int


# =============================================================================
# Expert CRUD Endpoints
# =============================================================================

@router.post("/", response_model=ExpertProfile)
async def create_expert(expert: ExpertCreate):
    """Create a new expert profile."""
    try:
        expert_manager = ExpertManager()

        # Check if email already exists
        existing = await db.db.experts.find_one({"email": expert.email})
        if existing:
            raise HTTPException(status_code=400, detail="Expert with this email already exists")

        # Create expert
        expert_id = f"EXP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        expert_doc = {
            "id": expert_id,
            "name": expert.name,
            "email": expert.email,
            "phone": expert.phone,
            "specializations": expert.specializations,
            "languages": expert.languages,
            "bio": expert.bio,
            "credentials": expert.credentials,
            "hourly_rate": expert.hourly_rate,
            "pro_bono_hours": expert.pro_bono_hours,
            "location": expert.location,
            "rating": 0.0,
            "total_reviews": 0,
            "availability": "available",
            "verified": False,
            "created_at": datetime.utcnow()
        }

        await db.db.experts.insert_one(expert_doc)

        return ExpertProfile(
            id=expert_id,
            name=expert.name,
            email=expert.email,
            specializations=expert.specializations,
            languages=expert.languages,
            bio=expert.bio,
            credentials=expert.credentials or [],
            hourly_rate=expert.hourly_rate,
            pro_bono_available=expert.pro_bono_hours > 0 if expert.pro_bono_hours else False,
            rating=0.0,
            total_reviews=0,
            availability="available",
            verified=False
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create expert: {str(e)}")


@router.get("/", response_model=List[ExpertProfile])
async def list_experts(
    specialization: Optional[str] = Query(None, description="Filter by specialization"),
    language: Optional[str] = Query(None, description="Filter by language"),
    availability: Optional[str] = Query(None, description="Filter by availability"),
    pro_bono_only: bool = Query(False, description="Only show pro bono available"),
    min_rating: Optional[float] = Query(None, ge=0, le=5)
):
    """List all experts with optional filters."""
    try:
        query = {}

        if specialization:
            query["specializations"] = specialization
        if language:
            query["languages"] = language
        if availability:
            query["availability"] = availability
        if pro_bono_only:
            query["pro_bono_hours"] = {"$gt": 0}
        if min_rating:
            query["rating"] = {"$gte": min_rating}

        experts = await db.db.experts.find(query).to_list(length=100)

        return [
            ExpertProfile(
                id=e.get("id"),
                name=e.get("name"),
                email=e.get("email"),
                specializations=e.get("specializations", []),
                languages=e.get("languages", []),
                bio=e.get("bio"),
                credentials=e.get("credentials", []),
                hourly_rate=e.get("hourly_rate"),
                pro_bono_available=e.get("pro_bono_hours", 0) > 0,
                rating=e.get("rating", 0),
                total_reviews=e.get("total_reviews", 0),
                availability=e.get("availability", "unknown"),
                verified=e.get("verified", False)
            )
            for e in experts
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list experts: {str(e)}")


@router.get("/{expert_id}", response_model=ExpertProfile)
async def get_expert(expert_id: str):
    """Get expert by ID."""
    try:
        expert = await db.db.experts.find_one({"id": expert_id})

        if not expert:
            raise HTTPException(status_code=404, detail="Expert not found")

        return ExpertProfile(
            id=expert.get("id"),
            name=expert.get("name"),
            email=expert.get("email"),
            specializations=expert.get("specializations", []),
            languages=expert.get("languages", []),
            bio=expert.get("bio"),
            credentials=expert.get("credentials", []),
            hourly_rate=expert.get("hourly_rate"),
            pro_bono_available=expert.get("pro_bono_hours", 0) > 0,
            rating=expert.get("rating", 0),
            total_reviews=expert.get("total_reviews", 0),
            availability=expert.get("availability", "unknown"),
            verified=expert.get("verified", False)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get expert: {str(e)}")


@router.put("/{expert_id}", response_model=ExpertProfile)
async def update_expert(expert_id: str, update: ExpertUpdate):
    """Update expert profile."""
    try:
        expert = await db.db.experts.find_one({"id": expert_id})

        if not expert:
            raise HTTPException(status_code=404, detail="Expert not found")

        # Build update document
        update_doc = {k: v for k, v in update.dict().items() if v is not None}
        update_doc["updated_at"] = datetime.utcnow()

        await db.db.experts.update_one(
            {"id": expert_id},
            {"$set": update_doc}
        )

        # Get updated expert
        updated = await db.db.experts.find_one({"id": expert_id})

        return ExpertProfile(
            id=updated.get("id"),
            name=updated.get("name"),
            email=updated.get("email"),
            specializations=updated.get("specializations", []),
            languages=updated.get("languages", []),
            bio=updated.get("bio"),
            credentials=updated.get("credentials", []),
            hourly_rate=updated.get("hourly_rate"),
            pro_bono_available=updated.get("pro_bono_hours", 0) > 0,
            rating=updated.get("rating", 0),
            total_reviews=updated.get("total_reviews", 0),
            availability=updated.get("availability", "unknown"),
            verified=updated.get("verified", False)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update expert: {str(e)}")


@router.delete("/{expert_id}")
async def delete_expert(expert_id: str):
    """Delete expert profile."""
    try:
        result = await db.db.experts.delete_one({"id": expert_id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Expert not found")

        return {"message": "Expert deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete expert: {str(e)}")


# =============================================================================
# Matching Endpoints
# =============================================================================

@router.post("/match", response_model=List[MatchResult])
async def match_experts(request: CaseMatchRequest):
    """
    Find best matching experts for a case.

    Uses AI-powered matching based on specializations,
    languages, availability, and case requirements.
    """
    try:
        case_matcher = CaseMatcher()

        # Get all available experts
        query = {"availability": {"$in": ["available", "busy"]}}
        if request.pro_bono_eligible:
            query["pro_bono_hours"] = {"$gt": 0}

        experts = await db.db.experts.find(query).to_list(length=100)

        if not experts:
            return []

        # Match experts
        matches = case_matcher.find_matches(
            case_type=request.case_type,
            required_languages=request.required_languages,
            urgency=request.urgency,
            budget=request.budget,
            experts=experts
        )

        return [
            MatchResult(
                expert_id=m.expert_id,
                expert_name=m.expert_name,
                match_score=m.overall_score,
                specialization_match=m.specialization_score,
                language_match=m.language_score,
                availability_match=m.availability_score,
                rating=m.rating,
                reasons=m.reasons
            )
            for m in matches[:10]  # Return top 10
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")


# =============================================================================
# Consultation Endpoints
# =============================================================================

@router.post("/consultations", response_model=ConsultationResponse)
async def create_consultation(consultation: ConsultationCreate):
    """Create a new consultation request."""
    try:
        # Verify expert exists
        expert = await db.db.experts.find_one({"id": consultation.expert_id})
        if not expert:
            raise HTTPException(status_code=404, detail="Expert not found")

        consultation_id = f"CON-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        consultation_doc = {
            "id": consultation_id,
            "case_id": consultation.case_id,
            "expert_id": consultation.expert_id,
            "client_id": consultation.client_id,
            "topic": consultation.topic,
            "description": consultation.description,
            "preferred_date": consultation.preferred_date,
            "duration_minutes": consultation.duration_minutes,
            "is_pro_bono": consultation.is_pro_bono,
            "status": "pending",
            "scheduled_at": None,
            "meeting_link": None,
            "created_at": datetime.utcnow()
        }

        await db.db.consultations.insert_one(consultation_doc)

        return ConsultationResponse(
            id=consultation_id,
            case_id=consultation.case_id,
            expert_id=consultation.expert_id,
            expert_name=expert.get("name"),
            client_id=consultation.client_id,
            topic=consultation.topic,
            status="pending",
            scheduled_at=None,
            duration_minutes=consultation.duration_minutes,
            is_pro_bono=consultation.is_pro_bono,
            meeting_link=None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create consultation: {str(e)}")


@router.get("/consultations/{consultation_id}", response_model=ConsultationResponse)
async def get_consultation(consultation_id: str):
    """Get consultation details."""
    try:
        consultation = await db.db.consultations.find_one({"id": consultation_id})

        if not consultation:
            raise HTTPException(status_code=404, detail="Consultation not found")

        expert = await db.db.experts.find_one({"id": consultation.get("expert_id")})

        return ConsultationResponse(
            id=consultation.get("id"),
            case_id=consultation.get("case_id"),
            expert_id=consultation.get("expert_id"),
            expert_name=expert.get("name") if expert else "Unknown",
            client_id=consultation.get("client_id"),
            topic=consultation.get("topic"),
            status=consultation.get("status"),
            scheduled_at=consultation.get("scheduled_at"),
            duration_minutes=consultation.get("duration_minutes"),
            is_pro_bono=consultation.get("is_pro_bono"),
            meeting_link=consultation.get("meeting_link")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get consultation: {str(e)}")


@router.post("/consultations/{consultation_id}/schedule")
async def schedule_consultation(
    consultation_id: str,
    scheduled_at: datetime = Body(...),
    meeting_link: Optional[str] = Body(None)
):
    """Schedule a consultation."""
    try:
        result = await db.db.consultations.update_one(
            {"id": consultation_id},
            {
                "$set": {
                    "status": "scheduled",
                    "scheduled_at": scheduled_at,
                    "meeting_link": meeting_link,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Consultation not found")

        return {"message": "Consultation scheduled", "scheduled_at": scheduled_at}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule consultation: {str(e)}")


@router.post("/consultations/{consultation_id}/complete")
async def complete_consultation(
    consultation_id: str,
    notes: Optional[str] = Body(None)
):
    """Mark consultation as completed."""
    try:
        result = await db.db.consultations.update_one(
            {"id": consultation_id},
            {
                "$set": {
                    "status": "completed",
                    "notes": notes,
                    "completed_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Consultation not found")

        # If pro bono, deduct hours from expert
        consultation = await db.db.consultations.find_one({"id": consultation_id})
        if consultation and consultation.get("is_pro_bono"):
            hours = consultation.get("duration_minutes", 60) / 60
            await db.db.experts.update_one(
                {"id": consultation.get("expert_id")},
                {"$inc": {"pro_bono_hours": -hours}}
            )

        return {"message": "Consultation completed"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete consultation: {str(e)}")


# =============================================================================
# Review Endpoints
# =============================================================================

@router.post("/reviews")
async def create_review(review: ReviewCreate):
    """Create a review for a consultation."""
    try:
        # Verify consultation exists and is completed
        consultation = await db.db.consultations.find_one({"id": review.consultation_id})
        if not consultation:
            raise HTTPException(status_code=404, detail="Consultation not found")

        if consultation.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Can only review completed consultations")

        review_doc = {
            "consultation_id": review.consultation_id,
            "expert_id": consultation.get("expert_id"),
            "rating": review.rating,
            "comment": review.comment,
            "anonymous": review.anonymous,
            "created_at": datetime.utcnow()
        }

        await db.db.expert_reviews.insert_one(review_doc)

        # Update expert rating
        reviews = await db.db.expert_reviews.find({
            "expert_id": consultation.get("expert_id")
        }).to_list(length=1000)

        avg_rating = sum(r.get("rating", 0) for r in reviews) / len(reviews)

        await db.db.experts.update_one(
            {"id": consultation.get("expert_id")},
            {
                "$set": {
                    "rating": round(avg_rating, 2),
                    "total_reviews": len(reviews)
                }
            }
        )

        return {"message": "Review submitted", "rating": review.rating}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create review: {str(e)}")


@router.get("/reviews/{expert_id}")
async def get_expert_reviews(expert_id: str):
    """Get all reviews for an expert."""
    try:
        reviews = await db.db.expert_reviews.find({
            "expert_id": expert_id
        }).sort("created_at", -1).to_list(length=100)

        return {
            "expert_id": expert_id,
            "total_reviews": len(reviews),
            "reviews": [
                {
                    "rating": r.get("rating"),
                    "comment": r.get("comment") if not r.get("anonymous") else None,
                    "created_at": r.get("created_at")
                }
                for r in reviews
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get reviews: {str(e)}")


# =============================================================================
# Knowledge Base Endpoints
# =============================================================================

@router.get("/knowledge", response_model=List[KnowledgeArticle])
async def list_knowledge_articles(
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """List knowledge base articles."""
    try:
        query = {}

        if category:
            query["category"] = category
        if tag:
            query["tags"] = tag
        if search:
            query["$text"] = {"$search": search}

        articles = await db.db.knowledge_articles.find(query).sort("created_at", -1).to_list(length=50)

        return [
            KnowledgeArticle(
                id=a.get("id"),
                title=a.get("title"),
                category=a.get("category"),
                content=a.get("content")[:500] + "..." if len(a.get("content", "")) > 500 else a.get("content"),
                tags=a.get("tags", []),
                author_id=a.get("author_id"),
                created_at=a.get("created_at"),
                views=a.get("views", 0)
            )
            for a in articles
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list articles: {str(e)}")


@router.get("/knowledge/{article_id}", response_model=KnowledgeArticle)
async def get_knowledge_article(article_id: str):
    """Get a knowledge base article."""
    try:
        article = await db.db.knowledge_articles.find_one({"id": article_id})

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        # Increment views
        await db.db.knowledge_articles.update_one(
            {"id": article_id},
            {"$inc": {"views": 1}}
        )

        return KnowledgeArticle(
            id=article.get("id"),
            title=article.get("title"),
            category=article.get("category"),
            content=article.get("content"),
            tags=article.get("tags", []),
            author_id=article.get("author_id"),
            created_at=article.get("created_at"),
            views=article.get("views", 0) + 1
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get article: {str(e)}")


# =============================================================================
# Specializations Endpoint
# =============================================================================

@router.get("/specializations")
async def get_specializations():
    """Get list of expert specializations."""
    try:
        return {
            "specializations": [
                {"id": "child_psychology", "name": "Child Psychology", "description": "Child behavioral and developmental psychology"},
                {"id": "family_law", "name": "Family Law", "description": "Legal expertise in family matters"},
                {"id": "forensic_psychology", "name": "Forensic Psychology", "description": "Psychological assessment for legal cases"},
                {"id": "parental_alienation", "name": "Parental Alienation", "description": "Specialist in parental alienation syndrome"},
                {"id": "digital_forensics", "name": "Digital Forensics", "description": "Technical analysis of digital evidence"},
                {"id": "child_protection", "name": "Child Protection", "description": "Child welfare and protection expertise"},
                {"id": "social_work", "name": "Social Work", "description": "Social work and family services"},
                {"id": "mediation", "name": "Mediation", "description": "Family mediation and conflict resolution"},
                {"id": "translation", "name": "Translation", "description": "Legal document translation"},
                {"id": "custody_evaluation", "name": "Custody Evaluation", "description": "Professional custody assessments"}
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get specializations: {str(e)}")
