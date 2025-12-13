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
    'extract_whatsapp_voice_notes'
]
