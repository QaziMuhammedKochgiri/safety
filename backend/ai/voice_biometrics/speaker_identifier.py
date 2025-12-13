"""
Speaker Identifier
Speaker identification and verification for voice evidence authentication.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import datetime
import hashlib
import math

from .voice_features import VoiceFeatureExtractor, AudioFeatures


class GenderEstimate(str, Enum):
    """Estimated gender from voice."""
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class AgeRange(str, Enum):
    """Estimated age range from voice."""
    CHILD = "child"  # < 12
    ADOLESCENT = "adolescent"  # 12-17
    YOUNG_ADULT = "young_adult"  # 18-35
    MIDDLE_AGED = "middle_aged"  # 36-55
    SENIOR = "senior"  # 55+
    UNKNOWN = "unknown"


@dataclass
class SpeakerProfile:
    """A registered speaker profile for identification."""
    profile_id: str
    display_name: str
    role: str  # mother, father, child, witness, etc.

    # Voice signature
    voice_signature: Dict[str, Any]
    enrollment_samples: List[str]  # Audio file IDs used for enrollment
    enrollment_date: str

    # Estimated demographics
    gender_estimate: GenderEstimate
    age_range_estimate: AgeRange

    # Statistics
    total_identifications: int = 0
    average_confidence: float = 0.0
    last_identified: Optional[str] = None

    # Metadata
    notes: str = ""
    case_id: Optional[str] = None


@dataclass
class SpeakerSegment:
    """A segment of audio attributed to a specific speaker."""
    segment_id: str
    start_time: float
    end_time: float
    speaker_id: Optional[str]  # None if unknown
    confidence: float
    is_speech: bool  # True if speech, False if silence/noise
    transcript: Optional[str] = None


@dataclass
class IdentificationResult:
    """Result of speaker identification (1:N matching)."""
    audio_id: str
    identified_speaker: Optional[str]  # Profile ID or None
    confidence: float
    all_candidates: List[Dict[str, float]]  # List of {profile_id, score}
    is_known_speaker: bool
    quality_score: float
    warnings: List[str]
    processing_time_ms: float


@dataclass
class VerificationResult:
    """Result of speaker verification (1:1 matching)."""
    audio_id: str
    claimed_speaker_id: str
    is_verified: bool
    confidence: float
    similarity_score: float
    threshold_used: float
    quality_score: float
    warnings: List[str]
    processing_time_ms: float


@dataclass
class DiarizationResult:
    """Result of speaker diarization (who spoke when)."""
    audio_id: str
    duration_seconds: float
    num_speakers: int
    segments: List[SpeakerSegment]
    speaker_durations: Dict[str, float]  # Speaker ID -> total seconds
    speaker_turn_counts: Dict[str, int]  # Speaker ID -> number of turns
    overlapping_speech_ratio: float  # Proportion of overlapping speech
    processing_time_ms: float


class SpeakerIdentifier:
    """Speaker identification and verification system."""

    def __init__(
        self,
        verification_threshold: float = 0.7,
        identification_threshold: float = 0.6,
        min_enrollment_samples: int = 3
    ):
        self.verification_threshold = verification_threshold
        self.identification_threshold = identification_threshold
        self.min_enrollment_samples = min_enrollment_samples
        self.feature_extractor = VoiceFeatureExtractor()
        self.profiles: Dict[str, SpeakerProfile] = {}

    def enroll_speaker(
        self,
        profile_id: str,
        display_name: str,
        role: str,
        audio_paths: List[str],
        case_id: Optional[str] = None,
        notes: str = ""
    ) -> Tuple[SpeakerProfile, List[str]]:
        """Enroll a new speaker with voice samples.

        Returns:
            Tuple of (profile, warnings)
        """
        warnings = []

        if len(audio_paths) < self.min_enrollment_samples:
            warnings.append(
                f"Only {len(audio_paths)} samples provided. "
                f"Minimum {self.min_enrollment_samples} recommended."
            )

        # Extract features from all samples
        all_features: List[AudioFeatures] = []
        sample_ids = []

        for path in audio_paths:
            try:
                features = self.feature_extractor.extract_features(path)
                suitable, issues = features.is_suitable_for_identification()

                if suitable:
                    all_features.append(features)
                    sample_ids.append(features.audio_id)
                else:
                    warnings.extend(issues)
            except Exception as e:
                warnings.append(f"Failed to process {path}: {str(e)}")

        if not all_features:
            raise ValueError("No suitable audio samples for enrollment")

        # Create combined voice signature
        voice_signature = self._create_combined_signature(all_features)

        # Estimate demographics
        gender = self._estimate_gender(all_features)
        age_range = self._estimate_age_range(all_features)

        # Create profile
        profile = SpeakerProfile(
            profile_id=profile_id,
            display_name=display_name,
            role=role,
            voice_signature=voice_signature,
            enrollment_samples=sample_ids,
            enrollment_date=datetime.datetime.now().isoformat(),
            gender_estimate=gender,
            age_range_estimate=age_range,
            notes=notes,
            case_id=case_id
        )

        self.profiles[profile_id] = profile
        return profile, warnings

    def _create_combined_signature(
        self,
        features_list: List[AudioFeatures]
    ) -> Dict[str, Any]:
        """Create a combined voice signature from multiple samples."""
        # Average the signatures
        signatures = [
            self.feature_extractor.get_voice_signature(f)
            for f in features_list
        ]

        combined = {}

        # Average numeric values
        for key in signatures[0]:
            values = [s[key] for s in signatures if key in s]
            if not values:
                continue

            if isinstance(values[0], list):
                # Average list elements
                combined[key] = [
                    sum(v[i] for v in values) / len(values)
                    for i in range(len(values[0]))
                ]
            elif isinstance(values[0], (int, float)):
                combined[key] = sum(values) / len(values)
            else:
                combined[key] = values[0]

        combined["num_samples"] = len(features_list)
        return combined

    def _estimate_gender(self, features_list: List[AudioFeatures]) -> GenderEstimate:
        """Estimate speaker gender from voice features."""
        # Average pitch is primary indicator
        avg_pitch = sum(f.prosodic.pitch_mean for f in features_list) / len(features_list)

        if avg_pitch < 120:
            return GenderEstimate.MALE
        elif avg_pitch > 180:
            return GenderEstimate.FEMALE
        else:
            return GenderEstimate.UNKNOWN

    def _estimate_age_range(self, features_list: List[AudioFeatures]) -> AgeRange:
        """Estimate speaker age range from voice features."""
        avg_pitch = sum(f.prosodic.pitch_mean for f in features_list) / len(features_list)
        avg_jitter = sum(f.prosodic.jitter for f in features_list) / len(features_list)
        avg_shimmer = sum(f.prosodic.shimmer for f in features_list) / len(features_list)

        # High pitch + low jitter/shimmer = younger
        # High jitter/shimmer = older
        # Very high pitch = child

        if avg_pitch > 250:
            return AgeRange.CHILD
        elif avg_pitch > 200 and avg_jitter < 0.02:
            return AgeRange.ADOLESCENT
        elif avg_jitter < 0.015 and avg_shimmer < 0.04:
            return AgeRange.YOUNG_ADULT
        elif avg_jitter > 0.025 or avg_shimmer > 0.06:
            return AgeRange.SENIOR
        else:
            return AgeRange.MIDDLE_AGED

    def identify_speaker(
        self,
        audio_path: str
    ) -> IdentificationResult:
        """Identify a speaker from audio (1:N matching)."""
        import time
        start_time = time.time()

        warnings = []

        # Extract features
        features = self.feature_extractor.extract_features(audio_path)
        suitable, issues = features.is_suitable_for_identification()
        warnings.extend(issues)

        quality_score = features.get_quality_score()

        if not self.profiles:
            return IdentificationResult(
                audio_id=features.audio_id,
                identified_speaker=None,
                confidence=0.0,
                all_candidates=[],
                is_known_speaker=False,
                quality_score=quality_score,
                warnings=["No enrolled speakers"],
                processing_time_ms=(time.time() - start_time) * 1000
            )

        # Compare against all profiles
        query_signature = self.feature_extractor.get_voice_signature(features)
        candidates = []

        for profile_id, profile in self.profiles.items():
            score = self._compare_signatures(
                query_signature,
                profile.voice_signature
            )
            candidates.append({"profile_id": profile_id, "score": score})

        # Sort by score (highest first)
        candidates.sort(key=lambda x: x["score"], reverse=True)

        # Check if best match exceeds threshold
        best_match = candidates[0] if candidates else None
        is_known = best_match and best_match["score"] >= self.identification_threshold

        # Update profile statistics if identified
        if is_known:
            profile = self.profiles[best_match["profile_id"]]
            profile.total_identifications += 1
            profile.average_confidence = (
                (profile.average_confidence * (profile.total_identifications - 1) +
                 best_match["score"]) / profile.total_identifications
            )
            profile.last_identified = datetime.datetime.now().isoformat()

        return IdentificationResult(
            audio_id=features.audio_id,
            identified_speaker=best_match["profile_id"] if is_known else None,
            confidence=best_match["score"] if best_match else 0.0,
            all_candidates=candidates[:5],  # Top 5 candidates
            is_known_speaker=is_known,
            quality_score=quality_score,
            warnings=warnings,
            processing_time_ms=(time.time() - start_time) * 1000
        )

    def verify_speaker(
        self,
        audio_path: str,
        claimed_speaker_id: str
    ) -> VerificationResult:
        """Verify if audio matches a claimed speaker (1:1 matching)."""
        import time
        start_time = time.time()

        warnings = []

        if claimed_speaker_id not in self.profiles:
            return VerificationResult(
                audio_id="",
                claimed_speaker_id=claimed_speaker_id,
                is_verified=False,
                confidence=0.0,
                similarity_score=0.0,
                threshold_used=self.verification_threshold,
                quality_score=0.0,
                warnings=["Speaker profile not found"],
                processing_time_ms=(time.time() - start_time) * 1000
            )

        # Extract features
        features = self.feature_extractor.extract_features(audio_path)
        suitable, issues = features.is_suitable_for_identification()
        warnings.extend(issues)

        quality_score = features.get_quality_score()

        # Compare with claimed speaker
        query_signature = self.feature_extractor.get_voice_signature(features)
        profile = self.profiles[claimed_speaker_id]
        similarity = self._compare_signatures(
            query_signature,
            profile.voice_signature
        )

        is_verified = similarity >= self.verification_threshold

        return VerificationResult(
            audio_id=features.audio_id,
            claimed_speaker_id=claimed_speaker_id,
            is_verified=is_verified,
            confidence=similarity if is_verified else 1.0 - similarity,
            similarity_score=similarity,
            threshold_used=self.verification_threshold,
            quality_score=quality_score,
            warnings=warnings,
            processing_time_ms=(time.time() - start_time) * 1000
        )

    def _compare_signatures(
        self,
        sig1: Dict[str, Any],
        sig2: Dict[str, Any]
    ) -> float:
        """Compare two voice signatures and return similarity score."""
        similarities = []

        # MFCC mean comparison (most important)
        if "mfcc_mean" in sig1 and "mfcc_mean" in sig2:
            mfcc_sim = self._cosine_similarity(sig1["mfcc_mean"], sig2["mfcc_mean"])
            similarities.append(("mfcc", mfcc_sim, 0.4))

        # Pitch comparison
        if "pitch_mean" in sig1 and "pitch_mean" in sig2:
            pitch_diff = abs(sig1["pitch_mean"] - sig2["pitch_mean"])
            max_pitch = max(sig1["pitch_mean"], sig2["pitch_mean"])
            pitch_sim = 1.0 - min(pitch_diff / max_pitch, 1.0) if max_pitch > 0 else 0.0
            similarities.append(("pitch", pitch_sim, 0.15))

        # Pitch variability
        if "pitch_std" in sig1 and "pitch_std" in sig2:
            std_diff = abs(sig1["pitch_std"] - sig2["pitch_std"])
            max_std = max(sig1["pitch_std"], sig2["pitch_std"])
            std_sim = 1.0 - min(std_diff / max_std, 1.0) if max_std > 0 else 0.0
            similarities.append(("pitch_var", std_sim, 0.1))

        # Voice quality (jitter, shimmer, HNR)
        vq_features = ["jitter", "shimmer", "hnr"]
        for vq in vq_features:
            if vq in sig1 and vq in sig2:
                diff = abs(sig1[vq] - sig2[vq])
                max_val = max(sig1[vq], sig2[vq])
                if max_val > 0:
                    sim = 1.0 - min(diff / max_val, 1.0)
                    similarities.append((vq, sim, 0.05))

        # Speech rate
        if "speech_rate" in sig1 and "speech_rate" in sig2:
            rate_diff = abs(sig1["speech_rate"] - sig2["speech_rate"])
            max_rate = max(sig1["speech_rate"], sig2["speech_rate"])
            rate_sim = 1.0 - min(rate_diff / max_rate, 1.0) if max_rate > 0 else 0.0
            similarities.append(("speech_rate", rate_sim, 0.1))

        # Weighted average
        if not similarities:
            return 0.0

        total_weight = sum(w for _, _, w in similarities)
        weighted_sum = sum(s * w for _, s, w in similarities)
        return weighted_sum / total_weight if total_weight > 0 else 0.0

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

    def diarize_audio(
        self,
        audio_path: str,
        known_speakers: Optional[List[str]] = None
    ) -> DiarizationResult:
        """Perform speaker diarization on audio file.

        Segments audio by speaker (who spoke when).
        """
        import time
        start_time = time.time()

        # Extract windowed features
        windows = self.feature_extractor.extract_windowed_features(audio_path)

        # Simple diarization based on feature clustering
        # In production, use more sophisticated methods
        segments: List[SpeakerSegment] = []
        current_speaker = None
        segment_start = 0.0

        for i, window in enumerate(windows):
            # Detect if this is speech or silence
            is_speech = window.intensity_mean > 0.1

            if not is_speech:
                # Silence segment
                if current_speaker is not None:
                    segments.append(SpeakerSegment(
                        segment_id=f"seg_{len(segments)}",
                        start_time=segment_start,
                        end_time=window.start_time,
                        speaker_id=current_speaker,
                        confidence=0.8,
                        is_speech=True
                    ))
                    current_speaker = None
                    segment_start = window.end_time
            else:
                # Speech segment
                if known_speakers:
                    # Try to identify speaker
                    result = self._identify_window(window, known_speakers)
                    speaker = result["speaker_id"]
                else:
                    # Unknown speakers - assign generic IDs
                    speaker = f"speaker_{hash(tuple(window.mfcc_mean[:5])) % 4}"

                if speaker != current_speaker:
                    if current_speaker is not None:
                        segments.append(SpeakerSegment(
                            segment_id=f"seg_{len(segments)}",
                            start_time=segment_start,
                            end_time=window.start_time,
                            speaker_id=current_speaker,
                            confidence=0.7,
                            is_speech=True
                        ))
                    current_speaker = speaker
                    segment_start = window.start_time

        # Add final segment
        if current_speaker is not None and windows:
            segments.append(SpeakerSegment(
                segment_id=f"seg_{len(segments)}",
                start_time=segment_start,
                end_time=windows[-1].end_time,
                speaker_id=current_speaker,
                confidence=0.7,
                is_speech=True
            ))

        # Calculate speaker statistics
        speaker_durations: Dict[str, float] = {}
        speaker_turns: Dict[str, int] = {}

        for seg in segments:
            if seg.speaker_id and seg.is_speech:
                duration = seg.end_time - seg.start_time
                speaker_durations[seg.speaker_id] = speaker_durations.get(seg.speaker_id, 0) + duration
                speaker_turns[seg.speaker_id] = speaker_turns.get(seg.speaker_id, 0) + 1

        total_duration = windows[-1].end_time if windows else 0.0

        return DiarizationResult(
            audio_id=hashlib.md5(audio_path.encode()).hexdigest()[:12],
            duration_seconds=total_duration,
            num_speakers=len(speaker_durations),
            segments=segments,
            speaker_durations=speaker_durations,
            speaker_turn_counts=speaker_turns,
            overlapping_speech_ratio=0.0,  # Simplified - would need proper overlap detection
            processing_time_ms=(time.time() - start_time) * 1000
        )

    def _identify_window(
        self,
        window,
        known_speakers: List[str]
    ) -> Dict[str, Any]:
        """Identify speaker for a single window."""
        best_speaker = None
        best_score = 0.0

        window_sig = {
            "mfcc_mean": window.mfcc_mean,
            "pitch_mean": window.pitch_mean,
            "pitch_std": window.pitch_std
        }

        for speaker_id in known_speakers:
            if speaker_id in self.profiles:
                score = self._compare_signatures(
                    window_sig,
                    self.profiles[speaker_id].voice_signature
                )
                if score > best_score:
                    best_score = score
                    best_speaker = speaker_id

        return {"speaker_id": best_speaker, "score": best_score}

    def get_profile(self, profile_id: str) -> Optional[SpeakerProfile]:
        """Get a speaker profile by ID."""
        return self.profiles.get(profile_id)

    def list_profiles(self, case_id: Optional[str] = None) -> List[SpeakerProfile]:
        """List all speaker profiles, optionally filtered by case."""
        profiles = list(self.profiles.values())
        if case_id:
            profiles = [p for p in profiles if p.case_id == case_id]
        return profiles

    def delete_profile(self, profile_id: str) -> bool:
        """Delete a speaker profile."""
        if profile_id in self.profiles:
            del self.profiles[profile_id]
            return True
        return False

    def export_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Export a profile for backup or transfer."""
        profile = self.profiles.get(profile_id)
        if not profile:
            return None

        return {
            "profile_id": profile.profile_id,
            "display_name": profile.display_name,
            "role": profile.role,
            "voice_signature": profile.voice_signature,
            "enrollment_samples": profile.enrollment_samples,
            "enrollment_date": profile.enrollment_date,
            "gender_estimate": profile.gender_estimate.value,
            "age_range_estimate": profile.age_range_estimate.value,
            "case_id": profile.case_id,
            "notes": profile.notes
        }

    def import_profile(self, data: Dict[str, Any]) -> SpeakerProfile:
        """Import a profile from exported data."""
        profile = SpeakerProfile(
            profile_id=data["profile_id"],
            display_name=data["display_name"],
            role=data["role"],
            voice_signature=data["voice_signature"],
            enrollment_samples=data["enrollment_samples"],
            enrollment_date=data["enrollment_date"],
            gender_estimate=GenderEstimate(data["gender_estimate"]),
            age_range_estimate=AgeRange(data["age_range_estimate"]),
            case_id=data.get("case_id"),
            notes=data.get("notes", "")
        )
        self.profiles[profile.profile_id] = profile
        return profile
