"""
Stress Detector
Voice stress analysis for detecting psychological stress and potential deception.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import datetime

from .voice_features import VoiceFeatureExtractor, AudioFeatures, FeatureWindow


class StressLevel(str, Enum):
    """Levels of detected stress."""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class StressType(str, Enum):
    """Types of stress indicators."""
    COGNITIVE_LOAD = "cognitive_load"  # Mental effort
    EMOTIONAL_STRESS = "emotional_stress"  # Emotional disturbance
    PHYSICAL_STRESS = "physical_stress"  # Physical tension
    DECEPTION_INDICATOR = "deception_indicator"  # Possible deception markers


@dataclass
class StressIndicator:
    """A specific stress indicator detected in voice."""
    indicator_type: StressType
    indicator_name: str
    value: float
    baseline_value: float
    deviation: float  # How far from baseline
    significance: str  # Legal/clinical significance
    time_range: Tuple[float, float]


@dataclass
class DeceptionIndicator:
    """Indicators potentially associated with deception.

    Note: Voice-based deception detection is not scientifically validated
    for legal use. These are research indicators only.
    """
    indicator_name: str
    present: bool
    confidence: float
    description: str
    scientific_note: str  # Limitations


@dataclass
class StressResult:
    """Result of stress analysis for a segment."""
    start_time: float
    end_time: float
    overall_stress_level: StressLevel
    stress_score: float  # 0.0-1.0

    # Component scores
    cognitive_load: float
    emotional_stress: float
    physical_tension: float

    # Specific indicators
    indicators: List[StressIndicator]

    # Voice metrics
    micro_tremor_detected: bool
    pitch_instability: float
    jitter_elevation: float
    shimmer_elevation: float

    # Legal notes
    legal_significance: str
    requires_expert_review: bool


@dataclass
class VoiceStressAnalysis:
    """Complete voice stress analysis report."""
    audio_id: str
    duration_seconds: float
    analysis_timestamp: str

    # Overall results
    average_stress_level: StressLevel
    average_stress_score: float
    peak_stress_score: float
    peak_stress_time: float

    # Timeline
    stress_segments: List[StressResult]
    stress_timeline: List[Dict[str, Any]]

    # Deception analysis (with strong disclaimers)
    deception_indicators: List[DeceptionIndicator]
    deception_note: str  # Strong disclaimer about reliability

    # Summary
    high_stress_duration_seconds: float
    high_stress_percentage: float
    stress_volatility: float

    # Legal reporting
    legal_summary: str
    methodology_note: str
    limitations: List[str]
    warnings: List[str]


# Baseline reference values for stress detection
STRESS_BASELINES = {
    "jitter": {
        "normal": 0.015,
        "elevated": 0.025,
        "high": 0.04
    },
    "shimmer": {
        "normal": 0.035,
        "elevated": 0.055,
        "high": 0.08
    },
    "pitch_std": {
        "normal": 20.0,
        "elevated": 35.0,
        "high": 50.0
    },
    "hnr": {
        "normal": 18.0,
        "low": 12.0,
        "very_low": 8.0
    },
    "pause_ratio": {
        "normal": 0.15,
        "elevated": 0.25,
        "high": 0.35
    },
    "speech_rate_variation": {
        "normal": 0.15,
        "elevated": 0.25,
        "high": 0.40
    }
}


class StressDetector:
    """Detects stress patterns in voice recordings.

    Important: Voice stress analysis is not a validated lie detection
    method. Results should be interpreted with caution and alongside
    other evidence.
    """

    def __init__(
        self,
        window_size_seconds: float = 3.0,
        hop_size_seconds: float = 1.5,
        include_deception_analysis: bool = True
    ):
        self.window_size = window_size_seconds
        self.hop_size = hop_size_seconds
        self.include_deception_analysis = include_deception_analysis
        self.feature_extractor = VoiceFeatureExtractor()

    def analyze(
        self,
        audio_path: str,
        baseline_audio_path: Optional[str] = None
    ) -> VoiceStressAnalysis:
        """Perform voice stress analysis.

        Args:
            audio_path: Path to audio file to analyze
            baseline_audio_path: Optional baseline recording for comparison

        Returns:
            Complete stress analysis report
        """
        # Extract features
        features = self.feature_extractor.extract_features(audio_path)

        # Extract baseline if provided
        baseline_features = None
        if baseline_audio_path:
            baseline_features = self.feature_extractor.extract_features(baseline_audio_path)

        # Extract windowed features for timeline
        windows = self.feature_extractor.extract_windowed_features(
            audio_path,
            window_size_seconds=self.window_size,
            hop_size_seconds=self.hop_size
        )

        # Analyze each window
        stress_segments: List[StressResult] = []
        for window in windows:
            result = self._analyze_window(window, features, baseline_features)
            stress_segments.append(result)

        # Build stress timeline
        stress_timeline = [
            {
                "time": seg.start_time,
                "stress_score": seg.stress_score,
                "stress_level": seg.overall_stress_level.value
            }
            for seg in stress_segments
        ]

        # Calculate overall metrics
        if stress_segments:
            avg_score = sum(s.stress_score for s in stress_segments) / len(stress_segments)
            peak_seg = max(stress_segments, key=lambda s: s.stress_score)
            peak_score = peak_seg.stress_score
            peak_time = peak_seg.start_time
        else:
            avg_score = 0.0
            peak_score = 0.0
            peak_time = 0.0

        avg_level = self._score_to_level(avg_score)

        # Calculate high stress duration
        high_stress_segs = [s for s in stress_segments if s.stress_score > 0.6]
        high_stress_duration = sum(s.end_time - s.start_time for s in high_stress_segs)
        high_stress_pct = (high_stress_duration / features.duration_seconds * 100) if features.duration_seconds > 0 else 0.0

        # Calculate volatility
        if len(stress_segments) > 1:
            score_diffs = [
                abs(stress_segments[i].stress_score - stress_segments[i-1].stress_score)
                for i in range(1, len(stress_segments))
            ]
            volatility = sum(score_diffs) / len(score_diffs)
        else:
            volatility = 0.0

        # Deception analysis (with disclaimers)
        deception_indicators = []
        if self.include_deception_analysis:
            deception_indicators = self._analyze_deception_indicators(features, stress_segments)

        # Generate legal summary
        legal_summary = self._generate_legal_summary(
            avg_level, high_stress_pct, volatility, peak_time
        )

        warnings = []
        if avg_score > 0.7:
            warnings.append("High overall stress detected - recommend expert review")
        if volatility > 0.3:
            warnings.append("High stress volatility detected - emotional instability possible")

        return VoiceStressAnalysis(
            audio_id=features.audio_id,
            duration_seconds=features.duration_seconds,
            analysis_timestamp=datetime.datetime.now().isoformat(),
            average_stress_level=avg_level,
            average_stress_score=avg_score,
            peak_stress_score=peak_score,
            peak_stress_time=peak_time,
            stress_segments=stress_segments,
            stress_timeline=stress_timeline,
            deception_indicators=deception_indicators,
            deception_note=self._get_deception_disclaimer(),
            high_stress_duration_seconds=high_stress_duration,
            high_stress_percentage=high_stress_pct,
            stress_volatility=volatility,
            legal_summary=legal_summary,
            methodology_note=self._get_methodology_note(),
            limitations=self._get_limitations(),
            warnings=warnings
        )

    def _analyze_window(
        self,
        window: FeatureWindow,
        full_features: AudioFeatures,
        baseline: Optional[AudioFeatures]
    ) -> StressResult:
        """Analyze stress in a single window."""
        indicators: List[StressIndicator] = []

        # Use baseline or default reference values
        if baseline:
            ref_jitter = baseline.prosodic.jitter
            ref_shimmer = baseline.prosodic.shimmer
            ref_pitch_std = baseline.prosodic.pitch_std
        else:
            ref_jitter = STRESS_BASELINES["jitter"]["normal"]
            ref_shimmer = STRESS_BASELINES["shimmer"]["normal"]
            ref_pitch_std = STRESS_BASELINES["pitch_std"]["normal"]

        # Calculate component scores
        cognitive_load = self._calculate_cognitive_load(window, full_features)
        emotional_stress = self._calculate_emotional_stress(window, full_features)
        physical_tension = self._calculate_physical_tension(full_features)

        # Jitter analysis (voice instability)
        jitter_elevation = max(0, (full_features.prosodic.jitter - ref_jitter) / ref_jitter)
        if jitter_elevation > 0.5:
            indicators.append(StressIndicator(
                indicator_type=StressType.PHYSICAL_STRESS,
                indicator_name="Elevated jitter",
                value=full_features.prosodic.jitter,
                baseline_value=ref_jitter,
                deviation=jitter_elevation,
                significance="Vocal cord tension indicator",
                time_range=(window.start_time, window.end_time)
            ))

        # Shimmer analysis (amplitude instability)
        shimmer_elevation = max(0, (full_features.prosodic.shimmer - ref_shimmer) / ref_shimmer)
        if shimmer_elevation > 0.5:
            indicators.append(StressIndicator(
                indicator_type=StressType.PHYSICAL_STRESS,
                indicator_name="Elevated shimmer",
                value=full_features.prosodic.shimmer,
                baseline_value=ref_shimmer,
                deviation=shimmer_elevation,
                significance="Respiratory or muscular tension indicator",
                time_range=(window.start_time, window.end_time)
            ))

        # Pitch instability
        pitch_instability = max(0, (window.pitch_std - ref_pitch_std) / ref_pitch_std) if ref_pitch_std > 0 else 0
        if pitch_instability > 0.5:
            indicators.append(StressIndicator(
                indicator_type=StressType.EMOTIONAL_STRESS,
                indicator_name="Pitch instability",
                value=window.pitch_std,
                baseline_value=ref_pitch_std,
                deviation=pitch_instability,
                significance="Emotional arousal indicator",
                time_range=(window.start_time, window.end_time)
            ))

        # Micro-tremor detection (8-12 Hz modulation)
        # In production, this would analyze the actual frequency spectrum
        micro_tremor = full_features.prosodic.jitter > 0.03 and full_features.prosodic.shimmer > 0.06

        # Calculate overall stress score
        stress_score = (
            cognitive_load * 0.25 +
            emotional_stress * 0.35 +
            physical_tension * 0.25 +
            min(jitter_elevation, 1.0) * 0.075 +
            min(shimmer_elevation, 1.0) * 0.075
        )
        stress_score = min(1.0, stress_score)

        stress_level = self._score_to_level(stress_score)

        # Legal significance
        if stress_score > 0.7:
            legal_sig = "High stress indicators detected - may indicate distress or pressure during recording"
        elif stress_score > 0.5:
            legal_sig = "Moderate stress indicators present"
        else:
            legal_sig = "Normal stress levels within expected range"

        requires_review = stress_score > 0.7 or len(indicators) > 3

        return StressResult(
            start_time=window.start_time,
            end_time=window.end_time,
            overall_stress_level=stress_level,
            stress_score=stress_score,
            cognitive_load=cognitive_load,
            emotional_stress=emotional_stress,
            physical_tension=physical_tension,
            indicators=indicators,
            micro_tremor_detected=micro_tremor,
            pitch_instability=pitch_instability,
            jitter_elevation=jitter_elevation,
            shimmer_elevation=shimmer_elevation,
            legal_significance=legal_sig,
            requires_expert_review=requires_review
        )

    def _calculate_cognitive_load(
        self,
        window: FeatureWindow,
        features: AudioFeatures
    ) -> float:
        """Calculate cognitive load indicator."""
        score = 0.0

        # Higher pause ratio indicates cognitive load
        if features.prosodic.pause_ratio > STRESS_BASELINES["pause_ratio"]["elevated"]:
            score += 0.3
        elif features.prosodic.pause_ratio > STRESS_BASELINES["pause_ratio"]["normal"]:
            score += 0.15

        # Speech rate changes
        rate_ref = 4.5  # Average speech rate
        rate_deviation = abs(features.prosodic.speech_rate - rate_ref) / rate_ref
        if rate_deviation > 0.3:
            score += 0.2
        elif rate_deviation > 0.15:
            score += 0.1

        # Filled pauses would indicate cognitive load (not implemented in features)
        # In production, detect "um", "uh", etc.

        return min(1.0, score)

    def _calculate_emotional_stress(
        self,
        window: FeatureWindow,
        features: AudioFeatures
    ) -> float:
        """Calculate emotional stress indicator."""
        score = 0.0

        # Pitch elevation
        expected_pitch = 150.0  # General average
        if window.pitch_mean > expected_pitch * 1.3:
            score += 0.3
        elif window.pitch_mean > expected_pitch * 1.15:
            score += 0.15

        # Pitch variability
        if window.pitch_std > STRESS_BASELINES["pitch_std"]["high"]:
            score += 0.3
        elif window.pitch_std > STRESS_BASELINES["pitch_std"]["elevated"]:
            score += 0.15

        # Intensity variation
        if features.prosodic.intensity_std > 0.2:
            score += 0.2
        elif features.prosodic.intensity_std > 0.15:
            score += 0.1

        return min(1.0, score)

    def _calculate_physical_tension(self, features: AudioFeatures) -> float:
        """Calculate physical tension indicator."""
        score = 0.0

        # Jitter (vocal cord tension)
        if features.prosodic.jitter > STRESS_BASELINES["jitter"]["high"]:
            score += 0.3
        elif features.prosodic.jitter > STRESS_BASELINES["jitter"]["elevated"]:
            score += 0.15

        # Shimmer (respiratory control)
        if features.prosodic.shimmer > STRESS_BASELINES["shimmer"]["high"]:
            score += 0.3
        elif features.prosodic.shimmer > STRESS_BASELINES["shimmer"]["elevated"]:
            score += 0.15

        # Low HNR (voice quality degradation)
        if features.prosodic.hnr < STRESS_BASELINES["hnr"]["very_low"]:
            score += 0.3
        elif features.prosodic.hnr < STRESS_BASELINES["hnr"]["low"]:
            score += 0.15

        return min(1.0, score)

    def _score_to_level(self, score: float) -> StressLevel:
        """Convert stress score to level."""
        if score >= 0.8:
            return StressLevel.VERY_HIGH
        elif score >= 0.6:
            return StressLevel.HIGH
        elif score >= 0.4:
            return StressLevel.MODERATE
        elif score >= 0.2:
            return StressLevel.LOW
        else:
            return StressLevel.VERY_LOW

    def _analyze_deception_indicators(
        self,
        features: AudioFeatures,
        stress_segments: List[StressResult]
    ) -> List[DeceptionIndicator]:
        """Analyze potential deception indicators.

        IMPORTANT: Voice-based deception detection is NOT scientifically
        validated and should NOT be used as evidence. This is provided
        for research purposes only.
        """
        indicators = []

        # Response latency changes
        high_pause_segs = [s for s in stress_segments if s.cognitive_load > 0.5]
        if len(high_pause_segs) > len(stress_segments) * 0.4:
            indicators.append(DeceptionIndicator(
                indicator_name="Increased response latency",
                present=True,
                confidence=0.3,
                description="Speaker shows increased pause patterns",
                scientific_note="May indicate cognitive load, anxiety, or simply careful speech - NOT a reliable deception indicator"
            ))

        # Pitch elevation during specific segments
        pitch_elevations = [s for s in stress_segments if s.emotional_stress > 0.6]
        if pitch_elevations:
            indicators.append(DeceptionIndicator(
                indicator_name="Pitch elevation pattern",
                present=True,
                confidence=0.25,
                description="Speaker shows elevated pitch in some segments",
                scientific_note="Pitch elevation is associated with arousal, not specifically deception"
            ))

        # Micro-tremor presence
        tremor_segs = [s for s in stress_segments if s.micro_tremor_detected]
        if len(tremor_segs) > len(stress_segments) * 0.3:
            indicators.append(DeceptionIndicator(
                indicator_name="Voice micro-tremor",
                present=True,
                confidence=0.2,
                description="Voice tremor patterns detected",
                scientific_note="Voice tremor can indicate stress, emotion, age, or medical conditions - NOT specific to deception"
            ))

        return indicators

    def _get_deception_disclaimer(self) -> str:
        """Get strong disclaimer about deception analysis."""
        return (
            "IMPORTANT DISCLAIMER: Voice-based deception detection (voice stress analysis, "
            "layered voice analysis, etc.) is NOT scientifically validated. Multiple peer-reviewed "
            "studies have found no reliable correlation between voice characteristics and deception. "
            "The American Psychological Association and other professional bodies do not endorse "
            "voice-based lie detection. Any 'deception indicators' presented here are research "
            "markers only and MUST NOT be used as evidence or to make legal determinations. "
            "Stress indicators may reflect anxiety, emotional state, medical conditions, or "
            "countless other factors unrelated to truthfulness."
        )

    def _generate_legal_summary(
        self,
        avg_level: StressLevel,
        high_stress_pct: float,
        volatility: float,
        peak_time: float
    ) -> str:
        """Generate legal summary for court reporting."""
        parts = []

        # Overall stress assessment
        level_descriptions = {
            StressLevel.VERY_LOW: "minimal",
            StressLevel.LOW: "low",
            StressLevel.MODERATE: "moderate",
            StressLevel.HIGH: "elevated",
            StressLevel.VERY_HIGH: "high"
        }
        parts.append(f"Voice stress analysis indicates {level_descriptions[avg_level]} overall stress levels.")

        # High stress periods
        if high_stress_pct > 30:
            parts.append(f"Elevated stress was detected in {high_stress_pct:.0f}% of the recording.")
        elif high_stress_pct > 10:
            parts.append(f"Some elevated stress periods detected ({high_stress_pct:.0f}% of recording).")

        # Volatility
        if volatility > 0.3:
            parts.append("Significant stress level fluctuation was observed, suggesting emotional instability during the recording.")

        # Peak moment
        if peak_time > 0:
            parts.append(f"Peak stress was detected at approximately {peak_time:.1f} seconds into the recording.")

        # Standard disclaimer
        parts.append(
            "\n\nMethodological note: Voice stress analysis measures physiological indicators "
            "of arousal and tension. Elevated stress may result from numerous factors including "
            "emotional state, physical condition, environmental factors, or the recording situation "
            "itself. Results should be interpreted in context with other evidence."
        )

        return " ".join(parts)

    def _get_methodology_note(self) -> str:
        """Get methodology description."""
        return (
            "This analysis examines acoustic features associated with physiological stress: "
            "jitter (pitch perturbation), shimmer (amplitude perturbation), pitch patterns, "
            "speech rate, pause patterns, and harmonics-to-noise ratio. These features are "
            "analyzed against baseline values and/or reference recordings where available."
        )

    def _get_limitations(self) -> List[str]:
        """Get list of analysis limitations."""
        return [
            "Voice stress analysis cannot determine the cause of detected stress",
            "Individual baseline variation may affect accuracy",
            "Recording quality significantly impacts analysis reliability",
            "Cultural and linguistic factors may influence voice patterns",
            "Medical conditions, age, and fatigue can affect voice characteristics",
            "Results are probabilistic and should not be treated as definitive",
            "This analysis is NOT a validated lie detection method"
        ]

    def compare_with_baseline(
        self,
        analysis: VoiceStressAnalysis,
        baseline_analysis: VoiceStressAnalysis
    ) -> Dict[str, Any]:
        """Compare stress analysis with baseline recording."""
        return {
            "stress_score_difference": analysis.average_stress_score - baseline_analysis.average_stress_score,
            "stress_level_change": f"{baseline_analysis.average_stress_level.value} -> {analysis.average_stress_level.value}",
            "volatility_change": analysis.stress_volatility - baseline_analysis.stress_volatility,
            "peak_stress_change": analysis.peak_stress_score - baseline_analysis.peak_stress_score,
            "interpretation": self._interpret_comparison(analysis, baseline_analysis)
        }

    def _interpret_comparison(
        self,
        current: VoiceStressAnalysis,
        baseline: VoiceStressAnalysis
    ) -> str:
        """Interpret comparison between current and baseline."""
        diff = current.average_stress_score - baseline.average_stress_score

        if diff > 0.3:
            return "Subject shows significantly elevated stress compared to baseline recording"
        elif diff > 0.15:
            return "Subject shows moderately elevated stress compared to baseline"
        elif diff < -0.15:
            return "Subject shows lower stress than baseline recording"
        else:
            return "Stress levels are similar to baseline recording"
