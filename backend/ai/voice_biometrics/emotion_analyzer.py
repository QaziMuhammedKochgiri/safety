"""
Emotion Analyzer
Voice-based emotion detection for legal evidence analysis.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import datetime

from .voice_features import VoiceFeatureExtractor, AudioFeatures, FeatureWindow


class EmotionType(str, Enum):
    """Types of emotions detectable from voice."""
    NEUTRAL = "neutral"
    ANGER = "anger"
    FEAR = "fear"
    SADNESS = "sadness"
    HAPPINESS = "happiness"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    CONTEMPT = "contempt"
    # Additional states relevant for legal context
    ANXIETY = "anxiety"
    DISTRESS = "distress"
    FRUSTRATION = "frustration"
    CALM = "calm"


class EmotionIntensity(str, Enum):
    """Intensity level of detected emotion."""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class EmotionResult:
    """Result of emotion detection for a segment."""
    primary_emotion: EmotionType
    primary_confidence: float
    intensity: EmotionIntensity

    # All emotion scores
    emotion_scores: Dict[EmotionType, float]

    # Arousal-Valence model
    arousal: float  # -1 (calm) to +1 (excited)
    valence: float  # -1 (negative) to +1 (positive)

    # Time range
    start_time: float
    end_time: float

    # Legal relevance
    legal_significance: str  # Description for court report
    requires_attention: bool  # Flag for concerning emotions


@dataclass
class EmotionTimeline:
    """Timeline of emotions throughout an audio file."""
    audio_id: str
    duration_seconds: float
    segments: List[EmotionResult]
    emotion_changes: List[Dict[str, Any]]  # Points where emotion changes significantly
    dominant_emotion: EmotionType
    emotional_volatility: float  # 0-1, how much emotions change


@dataclass
class EmotionSummary:
    """Summary of emotional analysis for legal reporting."""
    audio_id: str
    duration_seconds: float

    # Distribution
    emotion_distribution: Dict[EmotionType, float]  # Percentage of time
    average_arousal: float
    average_valence: float

    # Key findings
    dominant_emotions: List[Tuple[EmotionType, float]]  # Top 3 with percentages
    emotional_volatility: float
    peak_intensity_moments: List[Dict[str, Any]]

    # Legal analysis
    concerning_segments: List[EmotionResult]
    legal_interpretation: str
    confidence_level: str

    # Metadata
    analysis_timestamp: str
    warnings: List[str]


# Emotion detection rules based on acoustic features
EMOTION_FEATURE_PROFILES = {
    EmotionType.ANGER: {
        "pitch_mean": "high",
        "pitch_std": "high",
        "intensity_mean": "high",
        "speech_rate": "fast",
        "zcr": "high",
        "spectral_centroid": "high"
    },
    EmotionType.FEAR: {
        "pitch_mean": "high",
        "pitch_std": "high",
        "intensity_mean": "medium",
        "speech_rate": "fast",
        "jitter": "high",
        "shimmer": "high"
    },
    EmotionType.SADNESS: {
        "pitch_mean": "low",
        "pitch_std": "low",
        "intensity_mean": "low",
        "speech_rate": "slow",
        "spectral_centroid": "low"
    },
    EmotionType.HAPPINESS: {
        "pitch_mean": "high",
        "pitch_std": "medium",
        "intensity_mean": "high",
        "speech_rate": "fast",
        "hnr": "high"
    },
    EmotionType.NEUTRAL: {
        "pitch_mean": "medium",
        "pitch_std": "low",
        "intensity_mean": "medium",
        "speech_rate": "medium"
    },
    EmotionType.ANXIETY: {
        "pitch_mean": "high",
        "pitch_std": "high",
        "intensity_mean": "medium",
        "jitter": "high",
        "shimmer": "high",
        "speech_rate": "variable"
    },
    EmotionType.DISTRESS: {
        "pitch_mean": "high",
        "pitch_std": "very_high",
        "intensity_mean": "high",
        "jitter": "high",
        "speech_rate": "variable"
    },
    EmotionType.FRUSTRATION: {
        "pitch_mean": "medium_high",
        "pitch_std": "high",
        "intensity_mean": "medium_high",
        "speech_rate": "variable"
    },
    EmotionType.CALM: {
        "pitch_mean": "medium",
        "pitch_std": "very_low",
        "intensity_mean": "medium_low",
        "speech_rate": "slow"
    }
}


# Legal significance mappings
LEGAL_SIGNIFICANCE = {
    EmotionType.ANGER: {
        EmotionIntensity.VERY_HIGH: "Speaker displays extreme anger; may indicate aggression or threats",
        EmotionIntensity.HIGH: "Speaker shows significant anger; context important for interpretation",
        EmotionIntensity.MODERATE: "Speaker exhibits moderate frustration or anger",
        EmotionIntensity.LOW: "Mild irritation detected",
        EmotionIntensity.VERY_LOW: "Slight frustration, likely normal conversation"
    },
    EmotionType.FEAR: {
        EmotionIntensity.VERY_HIGH: "Speaker shows signs of extreme fear; may indicate intimidation",
        EmotionIntensity.HIGH: "Speaker appears significantly frightened or threatened",
        EmotionIntensity.MODERATE: "Speaker shows signs of nervousness or fear",
        EmotionIntensity.LOW: "Mild anxiety or concern detected",
        EmotionIntensity.VERY_LOW: "Slight nervousness, likely situational"
    },
    EmotionType.DISTRESS: {
        EmotionIntensity.VERY_HIGH: "Speaker shows extreme distress; requires immediate attention",
        EmotionIntensity.HIGH: "Speaker appears highly distressed",
        EmotionIntensity.MODERATE: "Speaker shows signs of emotional distress",
        EmotionIntensity.LOW: "Mild distress or discomfort detected",
        EmotionIntensity.VERY_LOW: "Slight discomfort noted"
    }
}


class EmotionAnalyzer:
    """Analyzes emotions from voice recordings."""

    def __init__(
        self,
        window_size_seconds: float = 2.0,
        hop_size_seconds: float = 1.0,
        min_confidence: float = 0.5
    ):
        self.window_size = window_size_seconds
        self.hop_size = hop_size_seconds
        self.min_confidence = min_confidence
        self.feature_extractor = VoiceFeatureExtractor()

        # Reference values for normalization (would be trained in production)
        self.reference_values = {
            "pitch_mean": {"low": 100, "medium": 150, "high": 200},
            "pitch_std": {"very_low": 5, "low": 15, "medium": 25, "high": 40, "very_high": 60},
            "intensity_mean": {"low": 0.2, "medium_low": 0.35, "medium": 0.5, "medium_high": 0.65, "high": 0.8},
            "speech_rate": {"slow": 3.0, "medium": 4.5, "fast": 6.0},
            "jitter": {"low": 0.01, "medium": 0.02, "high": 0.04},
            "shimmer": {"low": 0.03, "medium": 0.05, "high": 0.08},
            "hnr": {"low": 10, "medium": 15, "high": 20},
            "zcr": {"low": 0.03, "medium": 0.06, "high": 0.1},
            "spectral_centroid": {"low": 1500, "medium": 2500, "high": 3500}
        }

    def analyze(self, audio_path: str) -> EmotionSummary:
        """Perform full emotion analysis on audio file."""
        # Extract features
        features = self.feature_extractor.extract_features(audio_path)
        windows = self.feature_extractor.extract_windowed_features(
            audio_path,
            window_size_seconds=self.window_size,
            hop_size_seconds=self.hop_size
        )

        # Analyze each window
        segments: List[EmotionResult] = []
        for window in windows:
            emotion_result = self._analyze_window(window, features)
            segments.append(emotion_result)

        # Create timeline
        timeline = self._create_timeline(features.audio_id, features.duration_seconds, segments)

        # Generate summary
        summary = self._create_summary(features.audio_id, features.duration_seconds, segments, timeline)

        return summary

    def _analyze_window(
        self,
        window: FeatureWindow,
        full_features: AudioFeatures
    ) -> EmotionResult:
        """Analyze emotion for a single window."""
        # Calculate emotion scores based on feature matching
        emotion_scores: Dict[EmotionType, float] = {}

        for emotion, profile in EMOTION_FEATURE_PROFILES.items():
            score = self._calculate_emotion_score(window, full_features, profile)
            emotion_scores[emotion] = score

        # Normalize scores to probabilities
        total_score = sum(emotion_scores.values())
        if total_score > 0:
            emotion_scores = {k: v / total_score for k, v in emotion_scores.items()}

        # Find primary emotion
        primary_emotion = max(emotion_scores, key=emotion_scores.get)
        primary_confidence = emotion_scores[primary_emotion]

        # Calculate intensity
        intensity = self._calculate_intensity(window, full_features)

        # Calculate arousal-valence
        arousal = self._calculate_arousal(window, full_features)
        valence = self._calculate_valence(window, primary_emotion, emotion_scores)

        # Determine legal significance
        legal_sig = self._get_legal_significance(primary_emotion, intensity)
        requires_attention = (
            intensity in [EmotionIntensity.HIGH, EmotionIntensity.VERY_HIGH] and
            primary_emotion in [EmotionType.ANGER, EmotionType.FEAR, EmotionType.DISTRESS]
        )

        return EmotionResult(
            primary_emotion=primary_emotion,
            primary_confidence=primary_confidence,
            intensity=intensity,
            emotion_scores=emotion_scores,
            arousal=arousal,
            valence=valence,
            start_time=window.start_time,
            end_time=window.end_time,
            legal_significance=legal_sig,
            requires_attention=requires_attention
        )

    def _calculate_emotion_score(
        self,
        window: FeatureWindow,
        features: AudioFeatures,
        profile: Dict[str, str]
    ) -> float:
        """Calculate how well a window matches an emotion profile."""
        scores = []

        # Check pitch mean
        if "pitch_mean" in profile:
            ref = self.reference_values["pitch_mean"]
            if profile["pitch_mean"] == "high" and window.pitch_mean > ref["high"]:
                scores.append(1.0)
            elif profile["pitch_mean"] == "low" and window.pitch_mean < ref["low"]:
                scores.append(1.0)
            elif profile["pitch_mean"] == "medium":
                if ref["low"] <= window.pitch_mean <= ref["high"]:
                    scores.append(1.0)
                else:
                    scores.append(0.5)
            else:
                scores.append(0.3)

        # Check pitch variability
        if "pitch_std" in profile:
            ref = self.reference_values["pitch_std"]
            target = profile["pitch_std"]
            if target == "very_high" and window.pitch_std > ref["very_high"]:
                scores.append(1.0)
            elif target == "high" and window.pitch_std > ref["high"]:
                scores.append(1.0)
            elif target == "low" and window.pitch_std < ref["low"]:
                scores.append(1.0)
            elif target == "very_low" and window.pitch_std < ref["very_low"]:
                scores.append(1.0)
            else:
                scores.append(0.4)

        # Check intensity
        if "intensity_mean" in profile:
            ref = self.reference_values["intensity_mean"]
            target = profile["intensity_mean"]
            if target == "high" and window.intensity_mean > ref["high"]:
                scores.append(1.0)
            elif target == "low" and window.intensity_mean < ref["low"]:
                scores.append(1.0)
            elif "medium" in target:
                if ref["low"] <= window.intensity_mean <= ref["high"]:
                    scores.append(1.0)
                else:
                    scores.append(0.5)
            else:
                scores.append(0.4)

        # Check jitter (voice instability)
        if "jitter" in profile:
            ref = self.reference_values["jitter"]
            if profile["jitter"] == "high" and features.prosodic.jitter > ref["high"]:
                scores.append(1.0)
            elif profile["jitter"] == "low" and features.prosodic.jitter < ref["low"]:
                scores.append(1.0)
            else:
                scores.append(0.5)

        # Average all scores
        return sum(scores) / len(scores) if scores else 0.5

    def _calculate_intensity(
        self,
        window: FeatureWindow,
        features: AudioFeatures
    ) -> EmotionIntensity:
        """Calculate emotion intensity from features."""
        # Combine multiple intensity indicators
        intensity_score = 0.0

        # Pitch deviation from baseline
        pitch_dev = abs(window.pitch_mean - features.prosodic.pitch_mean)
        pitch_range = features.prosodic.pitch_range
        if pitch_range > 0:
            intensity_score += min(pitch_dev / pitch_range, 1.0) * 0.3

        # Intensity/loudness
        intensity_score += window.intensity_mean * 0.3

        # Pitch variability
        ref_std = self.reference_values["pitch_std"]
        if window.pitch_std > ref_std["high"]:
            intensity_score += 0.3
        elif window.pitch_std > ref_std["medium"]:
            intensity_score += 0.2
        else:
            intensity_score += 0.1

        # Voice quality (jitter/shimmer indicates stress)
        if features.prosodic.jitter > 0.03:
            intensity_score += 0.1

        # Map to intensity level
        if intensity_score > 0.8:
            return EmotionIntensity.VERY_HIGH
        elif intensity_score > 0.6:
            return EmotionIntensity.HIGH
        elif intensity_score > 0.4:
            return EmotionIntensity.MODERATE
        elif intensity_score > 0.2:
            return EmotionIntensity.LOW
        else:
            return EmotionIntensity.VERY_LOW

    def _calculate_arousal(
        self,
        window: FeatureWindow,
        features: AudioFeatures
    ) -> float:
        """Calculate arousal level (-1 calm to +1 excited)."""
        arousal = 0.0

        # High pitch = high arousal
        ref = self.reference_values["pitch_mean"]
        if window.pitch_mean > ref["high"]:
            arousal += 0.3
        elif window.pitch_mean < ref["low"]:
            arousal -= 0.3

        # High intensity = high arousal
        arousal += (window.intensity_mean - 0.5) * 0.4

        # High speech rate = high arousal
        ref_rate = self.reference_values["speech_rate"]
        if features.prosodic.speech_rate > ref_rate["fast"]:
            arousal += 0.2
        elif features.prosodic.speech_rate < ref_rate["slow"]:
            arousal -= 0.2

        # High pitch variability = high arousal
        if window.pitch_std > 30:
            arousal += 0.1

        return max(-1.0, min(1.0, arousal))

    def _calculate_valence(
        self,
        window: FeatureWindow,
        primary_emotion: EmotionType,
        emotion_scores: Dict[EmotionType, float]
    ) -> float:
        """Calculate valence (-1 negative to +1 positive)."""
        # Valence mappings
        valence_map = {
            EmotionType.HAPPINESS: 0.8,
            EmotionType.CALM: 0.4,
            EmotionType.NEUTRAL: 0.0,
            EmotionType.SURPRISE: 0.2,
            EmotionType.SADNESS: -0.6,
            EmotionType.FRUSTRATION: -0.4,
            EmotionType.ANGER: -0.7,
            EmotionType.FEAR: -0.8,
            EmotionType.DISTRESS: -0.9,
            EmotionType.ANXIETY: -0.5,
            EmotionType.DISGUST: -0.6,
            EmotionType.CONTEMPT: -0.5
        }

        # Weighted average based on emotion scores
        valence = 0.0
        for emotion, score in emotion_scores.items():
            if emotion in valence_map:
                valence += valence_map[emotion] * score

        return max(-1.0, min(1.0, valence))

    def _get_legal_significance(
        self,
        emotion: EmotionType,
        intensity: EmotionIntensity
    ) -> str:
        """Get legal significance description."""
        if emotion in LEGAL_SIGNIFICANCE:
            if intensity in LEGAL_SIGNIFICANCE[emotion]:
                return LEGAL_SIGNIFICANCE[emotion][intensity]

        # Default descriptions
        return f"Speaker shows {intensity.value.replace('_', ' ')} {emotion.value}"

    def _create_timeline(
        self,
        audio_id: str,
        duration: float,
        segments: List[EmotionResult]
    ) -> EmotionTimeline:
        """Create emotion timeline from segments."""
        # Detect emotion changes
        changes = []
        prev_emotion = None
        for seg in segments:
            if prev_emotion and seg.primary_emotion != prev_emotion:
                changes.append({
                    "time": seg.start_time,
                    "from_emotion": prev_emotion.value,
                    "to_emotion": seg.primary_emotion.value,
                    "confidence": seg.primary_confidence
                })
            prev_emotion = seg.primary_emotion

        # Calculate dominant emotion
        emotion_durations: Dict[EmotionType, float] = {}
        for seg in segments:
            duration_seg = seg.end_time - seg.start_time
            emotion_durations[seg.primary_emotion] = emotion_durations.get(seg.primary_emotion, 0) + duration_seg

        dominant = max(emotion_durations, key=emotion_durations.get) if emotion_durations else EmotionType.NEUTRAL

        # Calculate volatility (how often emotions change)
        volatility = len(changes) / (len(segments) + 1) if segments else 0.0

        return EmotionTimeline(
            audio_id=audio_id,
            duration_seconds=duration,
            segments=segments,
            emotion_changes=changes,
            dominant_emotion=dominant,
            emotional_volatility=volatility
        )

    def _create_summary(
        self,
        audio_id: str,
        duration: float,
        segments: List[EmotionResult],
        timeline: EmotionTimeline
    ) -> EmotionSummary:
        """Create emotion analysis summary for legal reporting."""
        warnings = []

        # Calculate emotion distribution
        emotion_distribution: Dict[EmotionType, float] = {}
        total_duration = 0.0
        for seg in segments:
            seg_duration = seg.end_time - seg.start_time
            emotion_distribution[seg.primary_emotion] = emotion_distribution.get(seg.primary_emotion, 0) + seg_duration
            total_duration += seg_duration

        if total_duration > 0:
            emotion_distribution = {k: v / total_duration for k, v in emotion_distribution.items()}

        # Average arousal and valence
        avg_arousal = sum(s.arousal for s in segments) / len(segments) if segments else 0.0
        avg_valence = sum(s.valence for s in segments) / len(segments) if segments else 0.0

        # Top 3 dominant emotions
        sorted_emotions = sorted(emotion_distribution.items(), key=lambda x: x[1], reverse=True)
        dominant_emotions = [(e, p) for e, p in sorted_emotions[:3]]

        # Find peak intensity moments
        peak_moments = [
            {
                "time": s.start_time,
                "emotion": s.primary_emotion.value,
                "intensity": s.intensity.value,
                "significance": s.legal_significance
            }
            for s in segments
            if s.intensity in [EmotionIntensity.HIGH, EmotionIntensity.VERY_HIGH]
        ]

        # Find concerning segments
        concerning = [s for s in segments if s.requires_attention]

        # Generate legal interpretation
        legal_interpretation = self._generate_legal_interpretation(
            dominant_emotions,
            concerning,
            timeline.emotional_volatility,
            avg_arousal,
            avg_valence
        )

        # Determine confidence level
        avg_confidence = sum(s.primary_confidence for s in segments) / len(segments) if segments else 0.0
        if avg_confidence > 0.8:
            confidence_level = "High"
        elif avg_confidence > 0.6:
            confidence_level = "Moderate"
        else:
            confidence_level = "Low"
            warnings.append("Low confidence in emotion detection - interpret with caution")

        return EmotionSummary(
            audio_id=audio_id,
            duration_seconds=duration,
            emotion_distribution=emotion_distribution,
            average_arousal=avg_arousal,
            average_valence=avg_valence,
            dominant_emotions=dominant_emotions,
            emotional_volatility=timeline.emotional_volatility,
            peak_intensity_moments=peak_moments,
            concerning_segments=concerning,
            legal_interpretation=legal_interpretation,
            confidence_level=confidence_level,
            analysis_timestamp=datetime.datetime.now().isoformat(),
            warnings=warnings
        )

    def _generate_legal_interpretation(
        self,
        dominant_emotions: List[Tuple[EmotionType, float]],
        concerning: List[EmotionResult],
        volatility: float,
        avg_arousal: float,
        avg_valence: float
    ) -> str:
        """Generate legal interpretation text."""
        parts = []

        # Dominant emotion analysis
        if dominant_emotions:
            top_emotion, top_percent = dominant_emotions[0]
            parts.append(
                f"The speaker primarily exhibits {top_emotion.value} "
                f"({top_percent*100:.0f}% of recording)."
            )

        # Emotional state
        if avg_arousal > 0.5:
            parts.append("The speaker shows high emotional arousal throughout.")
        elif avg_arousal < -0.3:
            parts.append("The speaker maintains a calm, subdued emotional state.")

        if avg_valence < -0.5:
            parts.append("The overall emotional tone is negative.")
        elif avg_valence > 0.3:
            parts.append("The overall emotional tone is positive.")

        # Volatility
        if volatility > 0.5:
            parts.append(
                "There is significant emotional volatility, with frequent "
                "changes in emotional state."
            )

        # Concerning segments
        if concerning:
            parts.append(
                f"The analysis identified {len(concerning)} segment(s) "
                "of concerning emotional content that may warrant further review."
            )

        # Disclaimer
        parts.append(
            "\n\nNote: Voice-based emotion analysis is probabilistic and should be "
            "interpreted alongside other evidence. Cultural and individual differences "
            "may affect emotional expression in voice."
        )

        return " ".join(parts)

    def get_emotion_at_time(
        self,
        segments: List[EmotionResult],
        time_seconds: float
    ) -> Optional[EmotionResult]:
        """Get emotion result at a specific time."""
        for seg in segments:
            if seg.start_time <= time_seconds < seg.end_time:
                return seg
        return None

    def compare_emotional_states(
        self,
        summary1: EmotionSummary,
        summary2: EmotionSummary
    ) -> Dict[str, Any]:
        """Compare emotional states between two recordings."""
        comparison = {
            "arousal_difference": summary1.average_arousal - summary2.average_arousal,
            "valence_difference": summary1.average_valence - summary2.average_valence,
            "volatility_difference": summary1.emotional_volatility - summary2.emotional_volatility,
            "shared_dominant_emotions": [],
            "different_dominant_emotions": []
        }

        # Compare dominant emotions
        emotions1 = set(e for e, _ in summary1.dominant_emotions)
        emotions2 = set(e for e, _ in summary2.dominant_emotions)

        comparison["shared_dominant_emotions"] = list(emotions1.intersection(emotions2))
        comparison["different_dominant_emotions"] = list(emotions1.symmetric_difference(emotions2))

        # Generate interpretation
        if comparison["arousal_difference"] > 0.3:
            comparison["interpretation"] = "Recording 1 shows higher emotional arousal than Recording 2"
        elif comparison["arousal_difference"] < -0.3:
            comparison["interpretation"] = "Recording 2 shows higher emotional arousal than Recording 1"
        else:
            comparison["interpretation"] = "Both recordings show similar arousal levels"

        return comparison
