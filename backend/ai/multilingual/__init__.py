"""
Multilingual AI with Cultural Context
Cultural-aware NLP processing for family law cases.

Modules:
- cultural_context: Cultural norms and context database
- language_detector: Automatic language detection
- cultural_analyzer: Culture-aware text analysis
- idiom_translator: Idiom and expression translation
- legal_terminology: Legal term translation with jurisdiction context
"""

from .cultural_context import (
    CulturalContext,
    CulturalNorm,
    CultureProfile,
    CulturalRegion,
    FamilyStructure,
    CommunicationStyle
)

from .language_detector import (
    LanguageDetector,
    DetectionResult,
    LanguageCode,
    ScriptType
)

from .cultural_analyzer import (
    CulturalAnalyzer,
    CulturalAnalysis,
    CulturalIndicator,
    ContextualMeaning
)

from .idiom_translator import (
    IdiomTranslator,
    Idiom,
    IdiomCategory,
    TranslationResult
)

from .legal_terminology import (
    LegalTerminology,
    LegalTerm,
    JurisdictionContext,
    TermEquivalent
)

__all__ = [
    # Cultural Context
    'CulturalContext',
    'CulturalNorm',
    'CultureProfile',
    'CulturalRegion',
    'FamilyStructure',
    'CommunicationStyle',

    # Language Detection
    'LanguageDetector',
    'DetectionResult',
    'LanguageCode',
    'ScriptType',

    # Cultural Analysis
    'CulturalAnalyzer',
    'CulturalAnalysis',
    'CulturalIndicator',
    'ContextualMeaning',

    # Idiom Translation
    'IdiomTranslator',
    'Idiom',
    'IdiomCategory',
    'TranslationResult',

    # Legal Terminology
    'LegalTerminology',
    'LegalTerm',
    'JurisdictionContext',
    'TermEquivalent'
]

__version__ = "1.0.0"
