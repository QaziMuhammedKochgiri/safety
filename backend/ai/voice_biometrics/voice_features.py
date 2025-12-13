"""
Voice Feature Extraction
Extracts acoustic features from audio for speaker identification and emotion analysis.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import math
import hashlib


class AudioFormat(str, Enum):
    """Supported audio formats."""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    FLAC = "flac"
    M4A = "m4a"
    WEBM = "webm"


@dataclass
class MFCCFeatures:
    """Mel-Frequency Cepstral Coefficients features."""
    coefficients: List[List[float]]  # Time x Coefficients (usually 13 or 20)
    num_coefficients: int
    frame_length_ms: float
    hop_length_ms: float
    sample_rate: int
    delta_coefficients: Optional[List[List[float]]] = None  # First derivative
    delta_delta_coefficients: Optional[List[List[float]]] = None  # Second derivative

    def get_mean(self) -> List[float]:
        """Get mean of each coefficient across all frames."""
        if not self.coefficients:
            return []
        num_frames = len(self.coefficients)
        num_coeffs = len(self.coefficients[0])
        means = []
        for c in range(num_coeffs):
            total = sum(self.coefficients[f][c] for f in range(num_frames))
            means.append(total / num_frames)
        return means

    def get_std(self) -> List[float]:
        """Get standard deviation of each coefficient."""
        if not self.coefficients:
            return []
        means = self.get_mean()
        num_frames = len(self.coefficients)
        num_coeffs = len(self.coefficients[0])
        stds = []
        for c in range(num_coeffs):
            variance = sum((self.coefficients[f][c] - means[c]) ** 2 for f in range(num_frames)) / num_frames
            stds.append(math.sqrt(variance))
        return stds


@dataclass
class SpectralFeatures:
    """Spectral domain features."""
    spectral_centroid: List[float]  # Center of mass of spectrum over time
    spectral_bandwidth: List[float]  # Spread around centroid
    spectral_rolloff: List[float]  # Frequency below which 85% energy
    spectral_flatness: List[float]  # How noise-like vs tonal
    spectral_contrast: List[List[float]]  # Difference between peaks and valleys
    zero_crossing_rate: List[float]  # Rate of sign changes in signal
    chroma_features: Optional[List[List[float]]] = None  # 12 pitch classes

    def get_spectral_statistics(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all spectral features."""
        stats = {}

        for name, values in [
            ("centroid", self.spectral_centroid),
            ("bandwidth", self.spectral_bandwidth),
            ("rolloff", self.spectral_rolloff),
            ("flatness", self.spectral_flatness),
            ("zcr", self.zero_crossing_rate)
        ]:
            if values:
                mean = sum(values) / len(values)
                variance = sum((v - mean) ** 2 for v in values) / len(values)
                stats[name] = {
                    "mean": mean,
                    "std": math.sqrt(variance),
                    "min": min(values),
                    "max": max(values)
                }

        return stats


@dataclass
class ProsodicFeatures:
    """Prosodic (pitch, rhythm, intensity) features."""
    # Pitch (F0) features
    pitch_values: List[float]  # Fundamental frequency over time
    pitch_mean: float
    pitch_std: float
    pitch_min: float
    pitch_max: float
    pitch_range: float

    # Intensity/Energy features
    intensity_values: List[float]  # RMS energy over time
    intensity_mean: float
    intensity_std: float
    intensity_range: float

    # Rhythm features
    speech_rate: float  # Syllables per second (estimated)
    articulation_rate: float  # Speech rate excluding pauses
    pause_ratio: float  # Proportion of silence
    mean_pause_duration: float  # Average pause length

    # Voice quality
    jitter: float  # Pitch variation (0.0-1.0)
    shimmer: float  # Amplitude variation (0.0-1.0)
    hnr: float  # Harmonics-to-noise ratio (dB)

    def get_pitch_contour_type(self) -> str:
        """Classify the pitch contour type."""
        if not self.pitch_values or len(self.pitch_values) < 10:
            return "unknown"

        # Simple contour analysis
        first_quarter = sum(self.pitch_values[:len(self.pitch_values)//4]) / (len(self.pitch_values)//4 + 1)
        last_quarter = sum(self.pitch_values[-len(self.pitch_values)//4:]) / (len(self.pitch_values)//4 + 1)

        diff = last_quarter - first_quarter
        threshold = self.pitch_std * 0.5

        if diff > threshold:
            return "rising"
        elif diff < -threshold:
            return "falling"
        elif self.pitch_std > self.pitch_mean * 0.2:
            return "variable"
        else:
            return "flat"


@dataclass
class AudioFeatures:
    """Complete audio feature set for voice analysis."""
    audio_id: str
    duration_seconds: float
    sample_rate: int
    num_channels: int
    format: AudioFormat

    # Feature sets
    mfcc: MFCCFeatures
    spectral: SpectralFeatures
    prosodic: ProsodicFeatures

    # Quality metrics
    snr_db: float  # Signal-to-noise ratio
    clipping_ratio: float  # Percentage of clipped samples
    silence_ratio: float  # Percentage of silence

    # Metadata
    extraction_timestamp: str
    extraction_duration_ms: float
    file_hash: str

    def get_quality_score(self) -> float:
        """Calculate overall audio quality score (0-1)."""
        score = 1.0

        # SNR penalty (good > 20dB)
        if self.snr_db < 10:
            score *= 0.5
        elif self.snr_db < 15:
            score *= 0.7
        elif self.snr_db < 20:
            score *= 0.9

        # Clipping penalty
        if self.clipping_ratio > 0.1:
            score *= 0.5
        elif self.clipping_ratio > 0.05:
            score *= 0.7
        elif self.clipping_ratio > 0.01:
            score *= 0.9

        # Excessive silence penalty
        if self.silence_ratio > 0.8:
            score *= 0.5
        elif self.silence_ratio > 0.6:
            score *= 0.8

        return score

    def is_suitable_for_identification(self) -> Tuple[bool, List[str]]:
        """Check if audio is suitable for speaker identification."""
        issues = []

        if self.duration_seconds < 3.0:
            issues.append("Duration too short (minimum 3 seconds)")

        if self.snr_db < 10:
            issues.append(f"SNR too low ({self.snr_db:.1f}dB, minimum 10dB)")

        if self.clipping_ratio > 0.1:
            issues.append(f"Too much clipping ({self.clipping_ratio*100:.1f}%)")

        if self.silence_ratio > 0.8:
            issues.append(f"Too much silence ({self.silence_ratio*100:.1f}%)")

        if self.prosodic.hnr < 5:
            issues.append("Poor voice quality (low HNR)")

        return len(issues) == 0, issues


@dataclass
class FeatureWindow:
    """A windowed segment of features for analysis."""
    start_time: float
    end_time: float
    mfcc_mean: List[float]
    mfcc_std: List[float]
    pitch_mean: float
    pitch_std: float
    intensity_mean: float
    spectral_centroid_mean: float
    zcr_mean: float


class VoiceFeatureExtractor:
    """Extracts voice features from audio files.

    Note: This is a framework implementation. In production,
    integrate with librosa, python-speech-features, or similar.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        frame_length_ms: float = 25.0,
        hop_length_ms: float = 10.0,
        num_mfcc: int = 13,
        include_deltas: bool = True
    ):
        self.sample_rate = sample_rate
        self.frame_length_ms = frame_length_ms
        self.hop_length_ms = hop_length_ms
        self.num_mfcc = num_mfcc
        self.include_deltas = include_deltas

    def extract_features(
        self,
        audio_path: str,
        audio_id: Optional[str] = None
    ) -> AudioFeatures:
        """Extract all features from an audio file.

        In production, this would use librosa or similar library.
        This implementation provides the framework structure.
        """
        import datetime

        # Generate audio ID if not provided
        if not audio_id:
            audio_id = hashlib.md5(audio_path.encode()).hexdigest()[:12]

        # Calculate file hash
        file_hash = self._calculate_file_hash(audio_path)

        # In production, load audio and extract features
        # Here we create placeholder structure

        # MFCC features (placeholder)
        mfcc = MFCCFeatures(
            coefficients=self._extract_mfcc_placeholder(),
            num_coefficients=self.num_mfcc,
            frame_length_ms=self.frame_length_ms,
            hop_length_ms=self.hop_length_ms,
            sample_rate=self.sample_rate,
            delta_coefficients=self._extract_mfcc_placeholder() if self.include_deltas else None,
            delta_delta_coefficients=self._extract_mfcc_placeholder() if self.include_deltas else None
        )

        # Spectral features (placeholder)
        spectral = SpectralFeatures(
            spectral_centroid=[2000.0] * 100,
            spectral_bandwidth=[1500.0] * 100,
            spectral_rolloff=[4000.0] * 100,
            spectral_flatness=[0.1] * 100,
            spectral_contrast=[[0.5] * 7 for _ in range(100)],
            zero_crossing_rate=[0.05] * 100,
            chroma_features=[[0.1] * 12 for _ in range(100)]
        )

        # Prosodic features (placeholder)
        prosodic = ProsodicFeatures(
            pitch_values=[150.0] * 100,
            pitch_mean=150.0,
            pitch_std=20.0,
            pitch_min=100.0,
            pitch_max=200.0,
            pitch_range=100.0,
            intensity_values=[0.5] * 100,
            intensity_mean=0.5,
            intensity_std=0.1,
            intensity_range=0.4,
            speech_rate=4.5,
            articulation_rate=5.0,
            pause_ratio=0.1,
            mean_pause_duration=0.3,
            jitter=0.01,
            shimmer=0.03,
            hnr=15.0
        )

        return AudioFeatures(
            audio_id=audio_id,
            duration_seconds=10.0,  # Placeholder
            sample_rate=self.sample_rate,
            num_channels=1,
            format=AudioFormat.WAV,
            mfcc=mfcc,
            spectral=spectral,
            prosodic=prosodic,
            snr_db=25.0,
            clipping_ratio=0.001,
            silence_ratio=0.15,
            extraction_timestamp=datetime.datetime.now().isoformat(),
            extraction_duration_ms=500.0,
            file_hash=file_hash
        )

    def _extract_mfcc_placeholder(self) -> List[List[float]]:
        """Placeholder MFCC extraction."""
        return [[0.0] * self.num_mfcc for _ in range(100)]

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of audio file."""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return hashlib.sha256(file_path.encode()).hexdigest()

    def extract_windowed_features(
        self,
        audio_path: str,
        window_size_seconds: float = 1.0,
        hop_size_seconds: float = 0.5
    ) -> List[FeatureWindow]:
        """Extract features in sliding windows for timeline analysis."""
        # Full feature extraction
        features = self.extract_features(audio_path)

        windows = []
        current_time = 0.0

        while current_time + window_size_seconds <= features.duration_seconds:
            window = FeatureWindow(
                start_time=current_time,
                end_time=current_time + window_size_seconds,
                mfcc_mean=features.mfcc.get_mean(),
                mfcc_std=features.mfcc.get_std(),
                pitch_mean=features.prosodic.pitch_mean,
                pitch_std=features.prosodic.pitch_std,
                intensity_mean=features.prosodic.intensity_mean,
                spectral_centroid_mean=sum(features.spectral.spectral_centroid) / len(features.spectral.spectral_centroid),
                zcr_mean=sum(features.spectral.zero_crossing_rate) / len(features.spectral.zero_crossing_rate)
            )
            windows.append(window)
            current_time += hop_size_seconds

        return windows

    def compare_features(
        self,
        features1: AudioFeatures,
        features2: AudioFeatures
    ) -> Dict[str, float]:
        """Compare two feature sets and return similarity scores."""
        similarities = {}

        # MFCC similarity (cosine similarity of means)
        mean1 = features1.mfcc.get_mean()
        mean2 = features2.mfcc.get_mean()
        similarities["mfcc"] = self._cosine_similarity(mean1, mean2)

        # Pitch similarity
        pitch_diff = abs(features1.prosodic.pitch_mean - features2.prosodic.pitch_mean)
        max_pitch = max(features1.prosodic.pitch_mean, features2.prosodic.pitch_mean)
        similarities["pitch"] = 1.0 - min(pitch_diff / max_pitch, 1.0) if max_pitch > 0 else 0.0

        # Spectral similarity
        spec_stats1 = features1.spectral.get_spectral_statistics()
        spec_stats2 = features2.spectral.get_spectral_statistics()
        spectral_sims = []
        for key in spec_stats1:
            if key in spec_stats2:
                diff = abs(spec_stats1[key]["mean"] - spec_stats2[key]["mean"])
                max_val = max(spec_stats1[key]["mean"], spec_stats2[key]["mean"])
                spectral_sims.append(1.0 - min(diff / max_val, 1.0) if max_val > 0 else 0.0)
        similarities["spectral"] = sum(spectral_sims) / len(spectral_sims) if spectral_sims else 0.0

        # Voice quality similarity
        vq_features1 = [features1.prosodic.jitter, features1.prosodic.shimmer, features1.prosodic.hnr / 30.0]
        vq_features2 = [features2.prosodic.jitter, features2.prosodic.shimmer, features2.prosodic.hnr / 30.0]
        similarities["voice_quality"] = self._cosine_similarity(vq_features1, vq_features2)

        # Overall similarity (weighted average)
        weights = {"mfcc": 0.4, "pitch": 0.2, "spectral": 0.2, "voice_quality": 0.2}
        similarities["overall"] = sum(similarities[k] * weights[k] for k in weights)

        return similarities

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2) or len(vec1) == 0:
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def get_voice_signature(self, features: AudioFeatures) -> Dict[str, Any]:
        """Generate a compact voice signature for identification."""
        return {
            "mfcc_mean": features.mfcc.get_mean(),
            "mfcc_std": features.mfcc.get_std(),
            "pitch_mean": features.prosodic.pitch_mean,
            "pitch_std": features.prosodic.pitch_std,
            "pitch_range": features.prosodic.pitch_range,
            "jitter": features.prosodic.jitter,
            "shimmer": features.prosodic.shimmer,
            "hnr": features.prosodic.hnr,
            "spectral_centroid_mean": sum(features.spectral.spectral_centroid) / len(features.spectral.spectral_centroid),
            "zcr_mean": sum(features.spectral.zero_crossing_rate) / len(features.spectral.zero_crossing_rate),
            "speech_rate": features.prosodic.speech_rate,
            "file_hash": features.file_hash
        }
