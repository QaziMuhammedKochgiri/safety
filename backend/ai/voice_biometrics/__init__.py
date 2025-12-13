"""
Voice Biometrics AI Module
Speaker identification, verification, and emotion analysis for family law evidence.

Modules:
- voice_features: Audio feature extraction (MFCC, spectral, prosodic)
- speaker_identifier: Speaker identification and verification
- emotion_analyzer: Emotion detection from voice
- stress_detector: Stress and deception indicators
- audio_enhancer: Audio quality enhancement and noise reduction
- voice_comparison: Forensic voice comparison for court
"""

from .voice_features import (
    VoiceFeatureExtractor,
    AudioFeatures,
    MFCCFeatures,
    SpectralFeatures,
    ProsodicFeatures
)

from .speaker_identifier import (
    SpeakerIdentifier,
    SpeakerProfile,
    IdentificationResult,
    VerificationResult,
    SpeakerSegment
)

from .emotion_analyzer import (
    EmotionAnalyzer,
    EmotionResult,
    EmotionType,
    EmotionTimeline,
    EmotionSummary
)

from .stress_detector import (
    StressDetector,
    StressResult,
    StressIndicator,
    DeceptionIndicator,
    VoiceStressAnalysis
)

from .audio_enhancer import (
    AudioEnhancer,
    EnhancementResult,
    NoiseProfile,
    AudioQuality
)

from .voice_comparison import (
    VoiceComparison,
    ComparisonResult,
    ForensicReport,
    SimilarityScore,
    LikelihoodRatio
)

__all__ = [
    # Voice Features
    'VoiceFeatureExtractor',
    'AudioFeatures',
    'MFCCFeatures',
    'SpectralFeatures',
    'ProsodicFeatures',

    # Speaker Identification
    'SpeakerIdentifier',
    'SpeakerProfile',
    'IdentificationResult',
    'VerificationResult',
    'SpeakerSegment',

    # Emotion Analysis
    'EmotionAnalyzer',
    'EmotionResult',
    'EmotionType',
    'EmotionTimeline',
    'EmotionSummary',

    # Stress Detection
    'StressDetector',
    'StressResult',
    'StressIndicator',
    'DeceptionIndicator',
    'VoiceStressAnalysis',

    # Audio Enhancement
    'AudioEnhancer',
    'EnhancementResult',
    'NoiseProfile',
    'AudioQuality',

    # Voice Comparison
    'VoiceComparison',
    'ComparisonResult',
    'ForensicReport',
    'SimilarityScore',
    'LikelihoodRatio'
]

__version__ = "1.0.0"
