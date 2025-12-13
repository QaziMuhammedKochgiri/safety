"""
One-Click Court Package Generator
Automated court document preparation for family law cases.

Modules:
- evidence_selector: Smart evidence selection wizard
- relevance_scorer: AI-based relevance scoring
- redundancy_remover: Duplicate and near-duplicate detection
- document_compiler: Page limit compliance and formatting
- exhibit_manager: Numbered exhibits with chain of custody
- court_formats: German, Turkish, EU E001 court format templates
"""

from .evidence_selector import (
    EvidenceSelector,
    EvidenceItem,
    EvidenceCategory,
    SelectionCriteria,
    SelectionResult
)

from .relevance_scorer import (
    RelevanceScorer,
    RelevanceScore,
    RelevanceFactor,
    ScoringContext
)

from .redundancy_remover import (
    RedundancyRemover,
    DuplicateGroup,
    SimilarityType,
    DeduplicationResult
)

from .document_compiler import (
    DocumentCompiler,
    CourtDocument,
    PageLimitConfig,
    CompilationResult
)

from .exhibit_manager import (
    ExhibitManager,
    Exhibit,
    ExhibitIndex,
    ChainOfCustody,
    CustodyEvent
)

from .court_formats import (
    CourtFormatGenerator,
    CourtFormat,
    GermanFamilyCourt,
    TurkishFamilyCourt,
    EUE001Format,
    CoverPage,
    TableOfContents
)

__all__ = [
    # Evidence Selection
    'EvidenceSelector',
    'EvidenceItem',
    'EvidenceCategory',
    'SelectionCriteria',
    'SelectionResult',

    # Relevance Scoring
    'RelevanceScorer',
    'RelevanceScore',
    'RelevanceFactor',
    'ScoringContext',

    # Redundancy Removal
    'RedundancyRemover',
    'DuplicateGroup',
    'SimilarityType',
    'DeduplicationResult',

    # Document Compilation
    'DocumentCompiler',
    'CourtDocument',
    'PageLimitConfig',
    'CompilationResult',

    # Exhibit Management
    'ExhibitManager',
    'Exhibit',
    'ExhibitIndex',
    'ChainOfCustody',
    'CustodyEvent',

    # Court Formats
    'CourtFormatGenerator',
    'CourtFormat',
    'GermanFamilyCourt',
    'TurkishFamilyCourt',
    'EUE001Format',
    'CoverPage',
    'TableOfContents'
]

__version__ = "1.0.0"
