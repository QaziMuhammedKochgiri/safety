"""
AI Module for SafeChild

Provides AI-powered analysis capabilities:
- Speech-to-Text: Whisper transcription for voice notes
- Image Analysis: Face detection, scene classification
- Advanced AI: Risk detection, parental alienation analysis
"""

from .speech_to_text import (
    SpeechToTextEngine,
    WhisperTranscriber,
    AudioProcessor,
    TranscriptAnalyzer,
    TranscriptionResult,
    TranscriptSegment,
    AudioFormat,
    TranscriptionSource,
    extract_whatsapp_voice_notes
)

from .image_analysis import (
    ImageAnalysisEngine,
    FaceDetector,
    ImageCategorizer,
    OCRExtractor,
    SafetyChecker,
    ImageAnalysisResult,
    DetectedFace,
    FaceLocation,
    ImageCategory,
    SafetyLevel
)

from .advanced_ai import (
    AdvancedAIEngine,
    LLMRouter,
    OllamaClient,
    ClaudeClient,
    RiskDetector,
    CourtReportGenerator,
    RiskAssessment,
    RiskIndicator,
    AlienationEvidence,
    RiskCategory,
    AlienationTactic,
    analyze_for_risks
)

__all__ = [
    # Speech-to-Text
    'SpeechToTextEngine',
    'WhisperTranscriber',
    'AudioProcessor',
    'TranscriptAnalyzer',
    'TranscriptionResult',
    'TranscriptSegment',
    'AudioFormat',
    'TranscriptionSource',
    'extract_whatsapp_voice_notes',
    # Image Analysis
    'ImageAnalysisEngine',
    'FaceDetector',
    'ImageCategorizer',
    'OCRExtractor',
    'SafetyChecker',
    'ImageAnalysisResult',
    'DetectedFace',
    'FaceLocation',
    'ImageCategory',
    'SafetyLevel'
]
