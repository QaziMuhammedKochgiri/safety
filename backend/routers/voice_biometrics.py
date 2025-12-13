"""
Voice Biometrics API Router
Provides endpoints for voice analysis, speaker identification, and emotion detection.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import io
import base64
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..ai.voice_biometrics.voice_features import VoiceFeatureExtractor
from ..ai.voice_biometrics.speaker_identifier import SpeakerIdentifier
from ..ai.voice_biometrics.emotion_analyzer import EmotionAnalyzer
from ..ai.voice_biometrics.stress_detector import StressDetector
from ..ai.voice_biometrics.audio_enhancer import AudioEnhancer
from ..ai.voice_biometrics.voice_comparison import VoiceComparison
from .. import db

router = APIRouter(
    prefix="/voice",
    tags=["voice-biometrics"],
    responses={404: {"description": "Not found"}},
)


# =============================================================================
# Pydantic Models
# =============================================================================

class AudioInput(BaseModel):
    """Input model for audio data."""
    audio_base64: str
    format: str = "wav"  # wav, mp3, m4a, ogg
    sample_rate: Optional[int] = None
    channels: Optional[int] = None


class AnalysisRequest(BaseModel):
    """Request model for voice analysis."""
    case_id: str
    audio: AudioInput
    include_emotions: bool = True
    include_stress: bool = True
    include_speaker_id: bool = True


class EmotionResult(BaseModel):
    """Result of emotion analysis."""
    emotion: str
    confidence: float
    arousal: float
    valence: float
    intensity: str


class StressResult(BaseModel):
    """Result of stress analysis."""
    stress_level: float  # 0-1
    stress_category: str  # low, moderate, high, severe
    cognitive_load: float
    indicators: List[str]
    disclaimer: str


class SpeakerInfo(BaseModel):
    """Speaker identification result."""
    speaker_id: str
    confidence: float
    is_known: bool
    name: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Response model for voice analysis."""
    case_id: str
    duration_seconds: float
    speaker: Optional[SpeakerInfo] = None
    emotions: Optional[List[EmotionResult]] = None
    stress: Optional[StressResult] = None
    features: Dict[str, float]
    quality_score: float
    analyzed_at: datetime


class EnhanceRequest(BaseModel):
    """Request for audio enhancement."""
    audio: AudioInput
    reduce_noise: bool = True
    normalize: bool = True
    enhance_speech: bool = True


class ComparisonRequest(BaseModel):
    """Request for voice comparison."""
    case_id: str
    sample_1: AudioInput
    sample_2: AudioInput
    include_forensic_report: bool = False


class ComparisonResult(BaseModel):
    """Result of voice comparison."""
    case_id: str
    likelihood_ratio: float
    match_confidence: float
    match_verdict: str  # match, probable_match, inconclusive, no_match
    feature_comparison: Dict[str, float]
    forensic_disclaimer: str


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_voice(request: AnalysisRequest):
    """
    Comprehensive voice analysis.

    Analyzes audio for speaker identification, emotion detection,
    and stress indicators.
    """
    try:
        # Decode audio
        audio_bytes = base64.b64decode(request.audio.audio_base64)

        # Initialize components
        feature_extractor = VoiceFeatureExtractor()
        speaker_identifier = SpeakerIdentifier()
        emotion_analyzer = EmotionAnalyzer()
        stress_detector = StressDetector()

        # Extract features
        features = feature_extractor.extract(
            audio_data=audio_bytes,
            format=request.audio.format,
            sample_rate=request.audio.sample_rate
        )

        # Speaker identification if requested
        speaker = None
        if request.include_speaker_id:
            speaker_result = speaker_identifier.identify(features)
            speaker = SpeakerInfo(
                speaker_id=speaker_result.speaker_id,
                confidence=speaker_result.confidence,
                is_known=speaker_result.is_known,
                name=speaker_result.name
            )

        # Emotion analysis if requested
        emotions = None
        if request.include_emotions:
            emotion_results = emotion_analyzer.analyze(features)
            emotions = [
                EmotionResult(
                    emotion=e.emotion,
                    confidence=e.confidence,
                    arousal=e.arousal,
                    valence=e.valence,
                    intensity=e.intensity
                )
                for e in emotion_results
            ]

        # Stress analysis if requested
        stress = None
        if request.include_stress:
            stress_result = stress_detector.detect(features)
            stress = StressResult(
                stress_level=stress_result.level,
                stress_category=stress_result.category,
                cognitive_load=stress_result.cognitive_load,
                indicators=stress_result.indicators,
                disclaimer="Stress detection is experimental and should not be used as sole evidence"
            )

        # Calculate quality score
        quality_score = _calculate_quality_score(features)

        # Store analysis in database
        analysis_doc = {
            "case_id": request.case_id,
            "type": "voice_analysis",
            "duration": features.get("duration", 0),
            "speaker_id": speaker.speaker_id if speaker else None,
            "emotions": [e.dict() for e in emotions] if emotions else [],
            "stress_level": stress.stress_level if stress else None,
            "quality_score": quality_score,
            "analyzed_at": datetime.utcnow()
        }
        await db.db.voice_analyses.insert_one(analysis_doc)

        return AnalysisResponse(
            case_id=request.case_id,
            duration_seconds=features.get("duration", 0),
            speaker=speaker,
            emotions=emotions,
            stress=stress,
            features={k: v for k, v in features.items() if isinstance(v, (int, float))},
            quality_score=quality_score,
            analyzed_at=datetime.utcnow()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice analysis failed: {str(e)}")


@router.post("/identify")
async def identify_speaker(
    case_id: str,
    audio: AudioInput,
    known_speakers: Optional[List[str]] = None
):
    """
    Identify speaker from audio.

    Compares voice against enrolled speakers in the case
    and returns identification results.
    """
    try:
        audio_bytes = base64.b64decode(audio.audio_base64)

        feature_extractor = VoiceFeatureExtractor()
        speaker_identifier = SpeakerIdentifier()

        features = feature_extractor.extract(
            audio_data=audio_bytes,
            format=audio.format
        )

        # Get enrolled speakers for case
        enrolled = await db.db.speaker_enrollments.find({
            "case_id": case_id
        }).to_list(length=100)

        if known_speakers:
            enrolled = [e for e in enrolled if e.get("speaker_id") in known_speakers]

        # Compare against enrolled speakers
        results = []
        for enrollment in enrolled:
            match_score = speaker_identifier.compare(
                features,
                enrollment.get("voice_features", {})
            )
            results.append({
                "speaker_id": enrollment.get("speaker_id"),
                "name": enrollment.get("name"),
                "match_score": match_score,
                "is_match": match_score > 0.8
            })

        # Sort by match score
        results.sort(key=lambda x: x["match_score"], reverse=True)

        best_match = results[0] if results else None

        return {
            "case_id": case_id,
            "identified_speaker": best_match.get("speaker_id") if best_match and best_match["is_match"] else None,
            "confidence": best_match.get("match_score", 0) if best_match else 0,
            "all_matches": results[:5],
            "total_enrolled": len(enrolled)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speaker identification failed: {str(e)}")


@router.post("/emotion")
async def analyze_emotion(
    audio: AudioInput,
    detailed: bool = Query(False, description="Include detailed temporal analysis")
):
    """
    Analyze emotions in voice.

    Detects emotional content including arousal-valence mapping
    and intensity levels.
    """
    try:
        audio_bytes = base64.b64decode(audio.audio_base64)

        feature_extractor = VoiceFeatureExtractor()
        emotion_analyzer = EmotionAnalyzer()

        features = feature_extractor.extract(
            audio_data=audio_bytes,
            format=audio.format
        )

        if detailed:
            # Temporal analysis - segment by segment
            temporal_results = emotion_analyzer.analyze_temporal(features)
            return {
                "overall_emotion": temporal_results.dominant_emotion,
                "confidence": temporal_results.confidence,
                "arousal": temporal_results.avg_arousal,
                "valence": temporal_results.avg_valence,
                "segments": [
                    {
                        "start_time": s.start,
                        "end_time": s.end,
                        "emotion": s.emotion,
                        "confidence": s.confidence
                    }
                    for s in temporal_results.segments
                ],
                "emotion_flow": temporal_results.emotion_flow
            }
        else:
            results = emotion_analyzer.analyze(features)
            primary = results[0] if results else None

            return {
                "emotions": [
                    {
                        "emotion": e.emotion,
                        "confidence": e.confidence,
                        "arousal": e.arousal,
                        "valence": e.valence,
                        "intensity": e.intensity
                    }
                    for e in results
                ],
                "primary_emotion": primary.emotion if primary else "neutral",
                "primary_confidence": primary.confidence if primary else 0
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Emotion analysis failed: {str(e)}")


@router.post("/stress")
async def analyze_stress(audio: AudioInput):
    """
    Analyze stress indicators in voice.

    Detects vocal stress patterns and cognitive load indicators.
    NOTE: Results are experimental and should not be used as sole evidence.
    """
    try:
        audio_bytes = base64.b64decode(audio.audio_base64)

        feature_extractor = VoiceFeatureExtractor()
        stress_detector = StressDetector()

        features = feature_extractor.extract(
            audio_data=audio_bytes,
            format=audio.format
        )

        result = stress_detector.detect(features)

        return {
            "stress_level": result.level,
            "stress_category": result.category,
            "cognitive_load": result.cognitive_load,
            "indicators": result.indicators,
            "detailed_metrics": {
                "pitch_variability": result.metrics.get("pitch_var", 0),
                "speech_rate": result.metrics.get("speech_rate", 0),
                "pause_frequency": result.metrics.get("pause_freq", 0),
                "voice_tremor": result.metrics.get("tremor", 0)
            },
            "disclaimer": (
                "IMPORTANT: Voice stress analysis is not a reliable indicator of deception. "
                "Results should be interpreted with caution and never used as sole evidence. "
                "Multiple factors including illness, fatigue, and anxiety can affect results."
            )
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stress analysis failed: {str(e)}")


@router.post("/enhance")
async def enhance_audio(request: EnhanceRequest):
    """
    Enhance audio quality.

    Applies forensic-grade audio enhancement including
    noise reduction and speech clarity improvement.
    """
    try:
        audio_bytes = base64.b64decode(request.audio.audio_base64)

        enhancer = AudioEnhancer()

        enhanced_audio = enhancer.enhance(
            audio_data=audio_bytes,
            format=request.audio.format,
            reduce_noise=request.reduce_noise,
            normalize=request.normalize,
            enhance_speech=request.enhance_speech
        )

        # Calculate improvement metrics
        original_snr = enhancer.calculate_snr(audio_bytes)
        enhanced_snr = enhancer.calculate_snr(enhanced_audio)

        return {
            "enhanced_audio_base64": base64.b64encode(enhanced_audio).decode(),
            "format": request.audio.format,
            "original_snr_db": original_snr,
            "enhanced_snr_db": enhanced_snr,
            "improvement_db": enhanced_snr - original_snr,
            "processing_applied": [
                p for p in ["noise_reduction", "normalization", "speech_enhancement"]
                if getattr(request, p.replace("_", "_"), False)
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio enhancement failed: {str(e)}")


@router.post("/compare", response_model=ComparisonResult)
async def compare_voices(request: ComparisonRequest):
    """
    Compare two voice samples.

    Performs forensic voice comparison using likelihood ratio
    methodology.
    """
    try:
        sample1_bytes = base64.b64decode(request.sample_1.audio_base64)
        sample2_bytes = base64.b64decode(request.sample_2.audio_base64)

        feature_extractor = VoiceFeatureExtractor()
        voice_comparison = VoiceComparison()

        # Extract features from both samples
        features1 = feature_extractor.extract(
            audio_data=sample1_bytes,
            format=request.sample_1.format
        )
        features2 = feature_extractor.extract(
            audio_data=sample2_bytes,
            format=request.sample_2.format
        )

        # Perform comparison
        result = voice_comparison.compare(features1, features2)

        # Determine verdict
        verdict = _get_comparison_verdict(result.likelihood_ratio)

        # Store comparison in database
        comparison_doc = {
            "case_id": request.case_id,
            "type": "voice_comparison",
            "likelihood_ratio": result.likelihood_ratio,
            "match_confidence": result.confidence,
            "verdict": verdict,
            "compared_at": datetime.utcnow()
        }
        await db.db.voice_comparisons.insert_one(comparison_doc)

        return ComparisonResult(
            case_id=request.case_id,
            likelihood_ratio=result.likelihood_ratio,
            match_confidence=result.confidence,
            match_verdict=verdict,
            feature_comparison=result.feature_scores,
            forensic_disclaimer=(
                "This comparison uses likelihood ratio methodology. "
                "A likelihood ratio > 100 provides moderate support for same-speaker hypothesis. "
                "Results should be interpreted by qualified forensic phoneticians."
            )
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice comparison failed: {str(e)}")


@router.post("/enroll/{case_id}")
async def enroll_speaker(
    case_id: str,
    speaker_name: str = Form(...),
    audio: UploadFile = File(...)
):
    """
    Enroll a speaker for future identification.

    Adds voice profile to the case's speaker database.
    """
    try:
        audio_bytes = await audio.read()

        feature_extractor = VoiceFeatureExtractor()
        features = feature_extractor.extract(
            audio_data=audio_bytes,
            format=audio.filename.split(".")[-1] if audio.filename else "wav"
        )

        # Generate speaker ID
        speaker_id = f"SPK-{case_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Store enrollment
        enrollment_doc = {
            "case_id": case_id,
            "speaker_id": speaker_id,
            "name": speaker_name,
            "voice_features": features,
            "enrolled_at": datetime.utcnow()
        }
        await db.db.speaker_enrollments.insert_one(enrollment_doc)

        return {
            "case_id": case_id,
            "speaker_id": speaker_id,
            "name": speaker_name,
            "enrolled": True,
            "feature_count": len([k for k in features.keys() if isinstance(features[k], (int, float))])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speaker enrollment failed: {str(e)}")


@router.get("/speakers/{case_id}")
async def get_enrolled_speakers(case_id: str):
    """Get all enrolled speakers for a case."""
    try:
        enrollments = await db.db.speaker_enrollments.find({
            "case_id": case_id
        }).to_list(length=100)

        return {
            "case_id": case_id,
            "total_speakers": len(enrollments),
            "speakers": [
                {
                    "speaker_id": e.get("speaker_id"),
                    "name": e.get("name"),
                    "enrolled_at": e.get("enrolled_at")
                }
                for e in enrollments
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get speakers: {str(e)}")


# =============================================================================
# Helper Functions
# =============================================================================

def _calculate_quality_score(features: Dict) -> float:
    """Calculate audio quality score from features."""
    snr = features.get("snr", 0)
    duration = features.get("duration", 0)

    score = 0.0

    # SNR contribution (0-50 points)
    if snr > 30:
        score += 50
    elif snr > 20:
        score += 40
    elif snr > 10:
        score += 25
    else:
        score += 10

    # Duration contribution (0-30 points)
    if duration > 10:
        score += 30
    elif duration > 5:
        score += 20
    elif duration > 2:
        score += 10

    # Sample rate contribution (0-20 points)
    sample_rate = features.get("sample_rate", 16000)
    if sample_rate >= 44100:
        score += 20
    elif sample_rate >= 22050:
        score += 15
    elif sample_rate >= 16000:
        score += 10

    return min(score, 100) / 100  # Normalize to 0-1


def _get_comparison_verdict(likelihood_ratio: float) -> str:
    """Get verdict from likelihood ratio."""
    if likelihood_ratio > 1000:
        return "match"
    elif likelihood_ratio > 100:
        return "probable_match"
    elif likelihood_ratio > 1:
        return "inconclusive"
    else:
        return "no_match"
