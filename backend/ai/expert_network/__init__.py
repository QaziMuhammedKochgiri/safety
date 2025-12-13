"""
Community Expert Network
Platform for connecting family law cases with verified experts.

Modules:
- expert_profile: Expert profile management and verification
- case_matcher: AI-powered case-expert matching
- consultation: Consultation scheduling and management
- review_system: Expert review and rating system
- knowledge_base: Community knowledge sharing
- pro_bono: Pro bono case coordination
"""

from .expert_profile import (
    ExpertProfile,
    ExpertSpecialization,
    VerificationStatus,
    ExpertCredential,
    ExpertAvailability,
    ExpertManager
)

from .case_matcher import (
    CaseMatcher,
    MatchResult,
    MatchCriteria,
    ExpertRecommendation,
    MatchScore
)

from .consultation import (
    ConsultationManager,
    Consultation,
    ConsultationType,
    ConsultationStatus,
    ConsultationRequest,
    ConsultationFeedback
)

from .review_system import (
    ReviewSystem,
    ExpertReview,
    ReviewMetrics,
    QualityScore,
    ReviewCategory
)

from .knowledge_base import (
    KnowledgeBase,
    Article,
    LegalPrecedent,
    FAQ,
    ResourceType,
    ArticleContribution
)

from .pro_bono import (
    ProBonoCoordinator,
    ProBonoCase,
    ProBonoStatus,
    EligibilityCriteria,
    ProBonoCommitment
)

__all__ = [
    # Expert Profile
    'ExpertProfile',
    'ExpertSpecialization',
    'VerificationStatus',
    'ExpertCredential',
    'ExpertAvailability',
    'ExpertManager',

    # Case Matching
    'CaseMatcher',
    'MatchResult',
    'MatchCriteria',
    'ExpertRecommendation',
    'MatchScore',

    # Consultation
    'ConsultationManager',
    'Consultation',
    'ConsultationType',
    'ConsultationStatus',
    'ConsultationRequest',
    'ConsultationFeedback',

    # Review System
    'ReviewSystem',
    'ExpertReview',
    'ReviewMetrics',
    'QualityScore',
    'ReviewCategory',

    # Knowledge Base
    'KnowledgeBase',
    'Article',
    'LegalPrecedent',
    'FAQ',
    'ResourceType',
    'ArticleContribution',

    # Pro Bono
    'ProBonoCoordinator',
    'ProBonoCase',
    'ProBonoStatus',
    'EligibilityCriteria',
    'ProBonoCommitment'
]

__version__ = "1.0.0"
