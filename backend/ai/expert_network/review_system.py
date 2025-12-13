"""
Review System
Expert review and rating system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import datetime
import hashlib


class ReviewCategory(str, Enum):
    """Categories for reviews."""
    EXPERTISE = "expertise"
    COMMUNICATION = "communication"
    PROFESSIONALISM = "professionalism"
    RESPONSIVENESS = "responsiveness"
    VALUE = "value"
    OUTCOME = "outcome"


@dataclass
class ExpertReview:
    """A review of an expert."""
    review_id: str
    expert_id: str
    reviewer_id: str
    consultation_id: Optional[str]
    case_id: Optional[str]

    # Ratings (1-5)
    overall_rating: int
    category_ratings: Dict[ReviewCategory, int]

    # Content
    title: str
    review_text: str
    pros: List[str]
    cons: List[str]

    # Case context
    case_type: str
    jurisdiction: str
    outcome_achieved: bool

    # Verification
    is_verified: bool  # Verified client
    is_moderated: bool
    moderation_notes: Optional[str]

    # Engagement
    helpful_votes: int
    not_helpful_votes: int

    # Metadata
    submitted_at: str
    updated_at: str
    is_public: bool
    expert_response: Optional[str]
    expert_response_at: Optional[str]


@dataclass
class ReviewMetrics:
    """Aggregated metrics for an expert."""
    expert_id: str
    total_reviews: int
    average_rating: float
    rating_distribution: Dict[int, int]  # 1-5 -> count
    category_averages: Dict[ReviewCategory, float]
    recommendation_rate: float  # % who would recommend
    verified_review_count: int
    recent_trend: str  # "improving", "stable", "declining"
    response_rate: float  # % of reviews with expert response
    last_updated: str


@dataclass
class QualityScore:
    """Quality score calculation for an expert."""
    expert_id: str
    overall_score: float  # 0-100
    components: Dict[str, float]
    rank_percentile: float  # Top X%
    badges_earned: List[str]
    improvement_suggestions: List[str]
    calculated_at: str


class ReviewSystem:
    """Manages expert reviews and ratings."""

    def __init__(self):
        self.reviews: Dict[str, ExpertReview] = {}
        self.metrics_cache: Dict[str, ReviewMetrics] = {}

    def submit_review(
        self,
        expert_id: str,
        reviewer_id: str,
        overall_rating: int,
        category_ratings: Dict[ReviewCategory, int],
        title: str,
        review_text: str,
        case_type: str,
        jurisdiction: str,
        consultation_id: Optional[str] = None,
        case_id: Optional[str] = None,
        pros: Optional[List[str]] = None,
        cons: Optional[List[str]] = None,
        outcome_achieved: bool = False,
        is_public: bool = True
    ) -> ExpertReview:
        """Submit a review for an expert."""
        review_id = hashlib.md5(
            f"{expert_id}-{reviewer_id}-{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        now = datetime.datetime.now().isoformat()

        review = ExpertReview(
            review_id=review_id,
            expert_id=expert_id,
            reviewer_id=reviewer_id,
            consultation_id=consultation_id,
            case_id=case_id,
            overall_rating=max(1, min(5, overall_rating)),
            category_ratings={
                cat: max(1, min(5, rating))
                for cat, rating in category_ratings.items()
            },
            title=title,
            review_text=review_text,
            pros=pros or [],
            cons=cons or [],
            case_type=case_type,
            jurisdiction=jurisdiction,
            outcome_achieved=outcome_achieved,
            is_verified=False,  # Set after verification
            is_moderated=False,
            moderation_notes=None,
            helpful_votes=0,
            not_helpful_votes=0,
            submitted_at=now,
            updated_at=now,
            is_public=is_public,
            expert_response=None,
            expert_response_at=None
        )

        self.reviews[review_id] = review

        # Invalidate metrics cache
        if expert_id in self.metrics_cache:
            del self.metrics_cache[expert_id]

        return review

    def verify_review(
        self,
        review_id: str,
        verified: bool = True
    ) -> bool:
        """Mark a review as verified (from verified client)."""
        if review_id not in self.reviews:
            return False

        self.reviews[review_id].is_verified = verified
        self.reviews[review_id].updated_at = datetime.datetime.now().isoformat()
        return True

    def moderate_review(
        self,
        review_id: str,
        approved: bool,
        notes: str = ""
    ) -> bool:
        """Moderate a review."""
        if review_id not in self.reviews:
            return False

        review = self.reviews[review_id]
        review.is_moderated = True
        review.moderation_notes = notes
        review.is_public = approved
        review.updated_at = datetime.datetime.now().isoformat()
        return True

    def add_expert_response(
        self,
        review_id: str,
        expert_id: str,
        response: str
    ) -> bool:
        """Add expert response to a review."""
        if review_id not in self.reviews:
            return False

        review = self.reviews[review_id]
        if review.expert_id != expert_id:
            return False

        review.expert_response = response
        review.expert_response_at = datetime.datetime.now().isoformat()
        review.updated_at = datetime.datetime.now().isoformat()
        return True

    def vote_review(
        self,
        review_id: str,
        helpful: bool
    ) -> bool:
        """Vote on whether a review was helpful."""
        if review_id not in self.reviews:
            return False

        review = self.reviews[review_id]
        if helpful:
            review.helpful_votes += 1
        else:
            review.not_helpful_votes += 1
        return True

    def get_expert_reviews(
        self,
        expert_id: str,
        public_only: bool = True,
        min_rating: Optional[int] = None,
        case_type: Optional[str] = None,
        limit: int = 50
    ) -> List[ExpertReview]:
        """Get reviews for an expert."""
        reviews = [
            r for r in self.reviews.values()
            if r.expert_id == expert_id
        ]

        if public_only:
            reviews = [r for r in reviews if r.is_public]

        if min_rating:
            reviews = [r for r in reviews if r.overall_rating >= min_rating]

        if case_type:
            reviews = [r for r in reviews if r.case_type == case_type]

        # Sort by helpful votes and recency
        reviews.sort(
            key=lambda r: (r.helpful_votes - r.not_helpful_votes, r.submitted_at),
            reverse=True
        )

        return reviews[:limit]

    def calculate_metrics(self, expert_id: str) -> ReviewMetrics:
        """Calculate aggregated metrics for an expert."""
        # Check cache
        if expert_id in self.metrics_cache:
            cached = self.metrics_cache[expert_id]
            # Cache valid for 1 hour
            cache_time = datetime.datetime.fromisoformat(cached.last_updated)
            if datetime.datetime.now() - cache_time < datetime.timedelta(hours=1):
                return cached

        reviews = [
            r for r in self.reviews.values()
            if r.expert_id == expert_id and r.is_public
        ]

        if not reviews:
            metrics = ReviewMetrics(
                expert_id=expert_id,
                total_reviews=0,
                average_rating=0.0,
                rating_distribution={i: 0 for i in range(1, 6)},
                category_averages={cat: 0.0 for cat in ReviewCategory},
                recommendation_rate=0.0,
                verified_review_count=0,
                recent_trend="stable",
                response_rate=0.0,
                last_updated=datetime.datetime.now().isoformat()
            )
            self.metrics_cache[expert_id] = metrics
            return metrics

        # Calculate metrics
        total = len(reviews)
        avg_rating = sum(r.overall_rating for r in reviews) / total

        # Rating distribution
        distribution = {i: 0 for i in range(1, 6)}
        for r in reviews:
            distribution[r.overall_rating] += 1

        # Category averages
        category_totals: Dict[ReviewCategory, List[int]] = {cat: [] for cat in ReviewCategory}
        for r in reviews:
            for cat, rating in r.category_ratings.items():
                category_totals[cat].append(rating)

        category_averages = {
            cat: sum(ratings) / len(ratings) if ratings else 0.0
            for cat, ratings in category_totals.items()
        }

        # Recommendation rate (4+ stars)
        recommenders = sum(1 for r in reviews if r.overall_rating >= 4)
        recommendation_rate = recommenders / total * 100

        # Verified count
        verified_count = sum(1 for r in reviews if r.is_verified)

        # Recent trend
        recent_trend = self._calculate_trend(reviews)

        # Response rate
        responses = sum(1 for r in reviews if r.expert_response)
        response_rate = responses / total * 100

        metrics = ReviewMetrics(
            expert_id=expert_id,
            total_reviews=total,
            average_rating=avg_rating,
            rating_distribution=distribution,
            category_averages=category_averages,
            recommendation_rate=recommendation_rate,
            verified_review_count=verified_count,
            recent_trend=recent_trend,
            response_rate=response_rate,
            last_updated=datetime.datetime.now().isoformat()
        )

        self.metrics_cache[expert_id] = metrics
        return metrics

    def _calculate_trend(self, reviews: List[ExpertReview]) -> str:
        """Calculate recent rating trend."""
        if len(reviews) < 5:
            return "stable"

        # Sort by date
        sorted_reviews = sorted(reviews, key=lambda r: r.submitted_at)

        # Compare recent vs older
        midpoint = len(sorted_reviews) // 2
        older = sorted_reviews[:midpoint]
        recent = sorted_reviews[midpoint:]

        older_avg = sum(r.overall_rating for r in older) / len(older)
        recent_avg = sum(r.overall_rating for r in recent) / len(recent)

        diff = recent_avg - older_avg
        if diff > 0.3:
            return "improving"
        elif diff < -0.3:
            return "declining"
        else:
            return "stable"

    def calculate_quality_score(
        self,
        expert_id: str,
        all_expert_ids: List[str]
    ) -> QualityScore:
        """Calculate comprehensive quality score."""
        metrics = self.calculate_metrics(expert_id)

        # Component scores (0-100)
        components = {}

        # Rating score (40% weight)
        components["rating"] = (metrics.average_rating / 5.0) * 100 if metrics.average_rating > 0 else 50

        # Volume score (15% weight) - more reviews = more reliable
        volume_score = min(metrics.total_reviews / 20, 1.0) * 100
        components["volume"] = volume_score

        # Verification score (15% weight)
        if metrics.total_reviews > 0:
            verified_ratio = metrics.verified_review_count / metrics.total_reviews
            components["verification"] = verified_ratio * 100
        else:
            components["verification"] = 0

        # Recommendation rate (15% weight)
        components["recommendation"] = metrics.recommendation_rate

        # Response engagement (10% weight)
        components["engagement"] = metrics.response_rate

        # Trend bonus (5% weight)
        trend_scores = {"improving": 100, "stable": 70, "declining": 40}
        components["trend"] = trend_scores.get(metrics.recent_trend, 70)

        # Calculate overall
        weights = {
            "rating": 0.40,
            "volume": 0.15,
            "verification": 0.15,
            "recommendation": 0.15,
            "engagement": 0.10,
            "trend": 0.05
        }
        overall = sum(components[k] * weights[k] for k in weights)

        # Calculate rank percentile
        all_scores = []
        for eid in all_expert_ids:
            m = self.calculate_metrics(eid)
            score = (m.average_rating / 5.0) * 100 if m.average_rating > 0 else 0
            all_scores.append((eid, score))

        all_scores.sort(key=lambda x: x[1], reverse=True)
        rank = next(
            (i for i, (eid, _) in enumerate(all_scores) if eid == expert_id),
            len(all_scores)
        )
        percentile = ((len(all_scores) - rank) / len(all_scores) * 100) if all_scores else 0

        # Determine badges
        badges = []
        if metrics.average_rating >= 4.8 and metrics.total_reviews >= 10:
            badges.append("Top Rated")
        if metrics.response_rate >= 90:
            badges.append("Highly Responsive")
        if metrics.verified_review_count >= 10:
            badges.append("Verified Expert")
        if metrics.recent_trend == "improving":
            badges.append("Rising Star")

        # Improvement suggestions
        suggestions = []
        if metrics.response_rate < 50:
            suggestions.append("Consider responding to more reviews to boost engagement")
        if metrics.total_reviews < 5:
            suggestions.append("Encourage satisfied clients to leave reviews")
        if components["rating"] < 70:
            suggestions.append("Focus on improving client satisfaction")

        return QualityScore(
            expert_id=expert_id,
            overall_score=overall,
            components=components,
            rank_percentile=percentile,
            badges_earned=badges,
            improvement_suggestions=suggestions,
            calculated_at=datetime.datetime.now().isoformat()
        )

    def get_top_reviewed_experts(
        self,
        min_reviews: int = 5,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top reviewed experts."""
        expert_ids = set(r.expert_id for r in self.reviews.values())
        expert_scores = []

        for expert_id in expert_ids:
            metrics = self.calculate_metrics(expert_id)
            if metrics.total_reviews >= min_reviews:
                expert_scores.append({
                    "expert_id": expert_id,
                    "average_rating": metrics.average_rating,
                    "total_reviews": metrics.total_reviews,
                    "recommendation_rate": metrics.recommendation_rate,
                    "trend": metrics.recent_trend
                })

        expert_scores.sort(key=lambda x: x["average_rating"], reverse=True)
        return expert_scores[:limit]

    def flag_review(
        self,
        review_id: str,
        reason: str,
        flagged_by: str
    ) -> bool:
        """Flag a review for moderation."""
        if review_id not in self.reviews:
            return False

        review = self.reviews[review_id]
        review.is_moderated = False  # Reset moderation status
        review.moderation_notes = f"Flagged by {flagged_by}: {reason}"
        review.updated_at = datetime.datetime.now().isoformat()
        return True
