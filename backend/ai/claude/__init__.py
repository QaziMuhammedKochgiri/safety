"""
Claude AI Integration Module
Centralized Claude API client for SafeChild platform.
"""

from .client import ClaudeClient, ClaudeConfig
from .risk_analyzer import RiskAnalyzer, RiskAnalysisResult
from .chat_assistant import ChatAssistant, ChatMessage, ChatSession
from .petition_generator import (
    PetitionGenerator,
    GeneratedPetition,
    PetitionRequest,
    PetitionType,
    CourtJurisdiction
)
from .legal_translator import (
    LegalTranslator,
    TranslationRequest,
    TranslationResult,
    TranslationType
)
from .alienation_detector import (
    AlienationDetector,
    AlienationAnalysisRequest,
    AlienationAnalysisResult,
    AlienationSeverity,
    AlienationTactic,
    AlienationEvidence,
    DetectedTactic
)
from .evidence_analyzer import (
    EvidenceAnalyzer,
    EvidenceAnalysisRequest,
    EvidenceAnalysisResult,
    EvidenceItem,
    EvidenceType,
    EvidenceRelevance,
    EvidenceCategory,
    AnalyzedEvidence
)
from .timeline_generator import (
    TimelineGenerator,
    TimelineGenerationRequest,
    TimelineGenerationResult,
    TimelineEvent,
    TimelinePeriod,
    EventType,
    EventSeverity
)
from .case_summary_generator import (
    CaseSummaryGenerator,
    CaseSummaryRequest,
    CaseSummaryResult
)

__all__ = [
    'ClaudeClient',
    'ClaudeConfig',
    'RiskAnalyzer',
    'RiskAnalysisResult',
    'ChatAssistant',
    'ChatMessage',
    'ChatSession',
    'PetitionGenerator',
    'GeneratedPetition',
    'PetitionRequest',
    'PetitionType',
    'CourtJurisdiction',
    'LegalTranslator',
    'TranslationRequest',
    'TranslationResult',
    'TranslationType',
    'AlienationDetector',
    'AlienationAnalysisRequest',
    'AlienationAnalysisResult',
    'AlienationSeverity',
    'AlienationTactic',
    'AlienationEvidence',
    'DetectedTactic',
    'EvidenceAnalyzer',
    'EvidenceAnalysisRequest',
    'EvidenceAnalysisResult',
    'EvidenceItem',
    'EvidenceType',
    'EvidenceRelevance',
    'EvidenceCategory',
    'AnalyzedEvidence',
    'TimelineGenerator',
    'TimelineGenerationRequest',
    'TimelineGenerationResult',
    'TimelineEvent',
    'TimelinePeriod',
    'EventType',
    'EventSeverity',
    'CaseSummaryGenerator',
    'CaseSummaryRequest',
    'CaseSummaryResult'
]
