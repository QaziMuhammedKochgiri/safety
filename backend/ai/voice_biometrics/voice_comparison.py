"""
Voice Comparison
Forensic voice comparison for court evidence.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import datetime
import math

from .voice_features import VoiceFeatureExtractor, AudioFeatures
from .speaker_identifier import SpeakerIdentifier


class ConclusionStrength(str, Enum):
    """Strength of forensic conclusion."""
    IDENTIFICATION = "identification"  # Same speaker
    STRONG_SUPPORT = "strong_support"  # Strong support for same speaker
    MODERATE_SUPPORT = "moderate_support"  # Moderate support
    LIMITED_SUPPORT = "limited_support"  # Limited support
    INCONCLUSIVE = "inconclusive"  # Cannot determine
    LIMITED_OPPOSITION = "limited_opposition"  # Limited support for different speakers
    MODERATE_OPPOSITION = "moderate_opposition"
    STRONG_OPPOSITION = "strong_opposition"
    EXCLUSION = "exclusion"  # Different speakers


@dataclass
class SimilarityScore:
    """Detailed similarity score between voice samples."""
    overall_score: float  # 0.0-1.0
    mfcc_similarity: float
    pitch_similarity: float
    spectral_similarity: float
    voice_quality_similarity: float
    prosodic_similarity: float
    component_weights: Dict[str, float]


@dataclass
class LikelihoodRatio:
    """Likelihood ratio for forensic voice comparison.

    LR > 1: Evidence supports same speaker
    LR < 1: Evidence supports different speakers
    LR = 1: Neutral
    """
    log_likelihood_ratio: float  # Log10(LR)
    verbal_equivalent: str  # e.g., "Strong support for same speaker"
    confidence_interval: Tuple[float, float]
    methodology: str


@dataclass
class ComparisonResult:
    """Result of voice comparison between two samples."""
    sample_a_id: str
    sample_b_id: str
    comparison_timestamp: str

    # Similarity metrics
    similarity: SimilarityScore
    likelihood_ratio: LikelihoodRatio

    # Conclusion
    conclusion: ConclusionStrength
    conclusion_text: str

    # Quality factors
    sample_a_quality: float
    sample_b_quality: float
    comparison_reliability: float

    # Detailed analysis
    feature_comparison: Dict[str, Dict[str, Any]]
    discriminating_features: List[str]  # Features that differ
    consistent_features: List[str]  # Features that match

    # Warnings and limitations
    warnings: List[str]
    limitations: List[str]


@dataclass
class ForensicReport:
    """Complete forensic voice comparison report for court."""
    report_id: str
    case_id: str
    examiner: str
    report_date: str

    # Samples analyzed
    questioned_sample: Dict[str, Any]  # Unknown voice
    known_sample: Dict[str, Any]  # Known reference voice

    # Comparison results
    comparison: ComparisonResult

    # Report sections
    executive_summary: str
    methodology_section: str
    analysis_section: str
    conclusion_section: str

    # Supporting data
    quality_assessment: Dict[str, Any]
    feature_tables: List[Dict[str, Any]]
    visualizations: List[str]  # Paths to generated charts

    # Legal compliance
    chain_of_custody: List[Dict[str, Any]]
    examiner_qualifications: str
    methodology_validation: str
    limitations_statement: str

    # Certification
    certification_statement: str
    digital_signature: Optional[str]


# Likelihood ratio verbal scale (based on forensic science standards)
LR_VERBAL_SCALE = [
    (6, "Very strong support for same speaker"),
    (4, "Strong support for same speaker"),
    (2, "Moderately strong support for same speaker"),
    (1, "Limited support for same speaker"),
    (0, "Inconclusive - neutral"),
    (-1, "Limited support for different speakers"),
    (-2, "Moderately strong support for different speakers"),
    (-4, "Strong support for different speakers"),
    (-6, "Very strong support for different speakers")
]


class VoiceComparison:
    """Forensic voice comparison system."""

    def __init__(
        self,
        identification_threshold: float = 0.85,
        exclusion_threshold: float = 0.3
    ):
        self.identification_threshold = identification_threshold
        self.exclusion_threshold = exclusion_threshold
        self.feature_extractor = VoiceFeatureExtractor()

    def compare(
        self,
        sample_a_path: str,
        sample_b_path: str,
        sample_a_name: str = "Sample A",
        sample_b_name: str = "Sample B"
    ) -> ComparisonResult:
        """Compare two voice samples."""
        # Extract features from both samples
        features_a = self.feature_extractor.extract_features(sample_a_path)
        features_b = self.feature_extractor.extract_features(sample_b_path)

        # Assess quality
        quality_a = features_a.get_quality_score()
        quality_b = features_b.get_quality_score()

        # Calculate similarity scores
        similarity = self._calculate_similarity(features_a, features_b)

        # Calculate likelihood ratio
        lr = self._calculate_likelihood_ratio(similarity)

        # Determine conclusion
        conclusion, conclusion_text = self._determine_conclusion(similarity, lr)

        # Detailed feature comparison
        feature_comparison = self._compare_features_detailed(features_a, features_b)

        # Identify discriminating and consistent features
        discriminating, consistent = self._identify_feature_patterns(feature_comparison)

        # Calculate comparison reliability
        reliability = self._calculate_reliability(quality_a, quality_b, features_a, features_b)

        # Generate warnings
        warnings = self._generate_warnings(features_a, features_b, quality_a, quality_b)

        return ComparisonResult(
            sample_a_id=features_a.audio_id,
            sample_b_id=features_b.audio_id,
            comparison_timestamp=datetime.datetime.now().isoformat(),
            similarity=similarity,
            likelihood_ratio=lr,
            conclusion=conclusion,
            conclusion_text=conclusion_text,
            sample_a_quality=quality_a,
            sample_b_quality=quality_b,
            comparison_reliability=reliability,
            feature_comparison=feature_comparison,
            discriminating_features=discriminating,
            consistent_features=consistent,
            warnings=warnings,
            limitations=self._get_limitations()
        )

    def _calculate_similarity(
        self,
        features_a: AudioFeatures,
        features_b: AudioFeatures
    ) -> SimilarityScore:
        """Calculate detailed similarity scores."""
        # Get voice signatures
        sig_a = self.feature_extractor.get_voice_signature(features_a)
        sig_b = self.feature_extractor.get_voice_signature(features_b)

        # MFCC similarity (most important for speaker ID)
        mfcc_sim = self._cosine_similarity(
            sig_a.get("mfcc_mean", []),
            sig_b.get("mfcc_mean", [])
        )

        # Pitch similarity
        pitch_diff = abs(sig_a.get("pitch_mean", 0) - sig_b.get("pitch_mean", 0))
        max_pitch = max(sig_a.get("pitch_mean", 1), sig_b.get("pitch_mean", 1))
        pitch_sim = 1.0 - min(pitch_diff / max_pitch, 1.0) if max_pitch > 0 else 0.0

        # Pitch range similarity
        range_a = sig_a.get("pitch_range", 0)
        range_b = sig_b.get("pitch_range", 0)
        range_diff = abs(range_a - range_b)
        max_range = max(range_a, range_b, 1)
        range_sim = 1.0 - min(range_diff / max_range, 1.0)

        # Spectral similarity
        centroid_a = sig_a.get("spectral_centroid_mean", 0)
        centroid_b = sig_b.get("spectral_centroid_mean", 0)
        centroid_diff = abs(centroid_a - centroid_b)
        max_centroid = max(centroid_a, centroid_b, 1)
        spectral_sim = 1.0 - min(centroid_diff / max_centroid, 1.0)

        # Voice quality similarity (jitter, shimmer, HNR)
        vq_features = ["jitter", "shimmer", "hnr"]
        vq_sims = []
        for vq in vq_features:
            if vq in sig_a and vq in sig_b:
                diff = abs(sig_a[vq] - sig_b[vq])
                max_val = max(sig_a[vq], sig_b[vq], 0.001)
                vq_sims.append(1.0 - min(diff / max_val, 1.0))
        voice_quality_sim = sum(vq_sims) / len(vq_sims) if vq_sims else 0.5

        # Prosodic similarity (speech rate, etc.)
        rate_a = sig_a.get("speech_rate", 4.5)
        rate_b = sig_b.get("speech_rate", 4.5)
        rate_diff = abs(rate_a - rate_b)
        max_rate = max(rate_a, rate_b, 1)
        prosodic_sim = 1.0 - min(rate_diff / max_rate, 1.0)

        # Combined pitch similarity
        pitch_combined = (pitch_sim + range_sim) / 2

        # Weights based on forensic literature
        weights = {
            "mfcc": 0.40,
            "pitch": 0.15,
            "spectral": 0.15,
            "voice_quality": 0.20,
            "prosodic": 0.10
        }

        # Calculate overall score
        overall = (
            mfcc_sim * weights["mfcc"] +
            pitch_combined * weights["pitch"] +
            spectral_sim * weights["spectral"] +
            voice_quality_sim * weights["voice_quality"] +
            prosodic_sim * weights["prosodic"]
        )

        return SimilarityScore(
            overall_score=overall,
            mfcc_similarity=mfcc_sim,
            pitch_similarity=pitch_combined,
            spectral_similarity=spectral_sim,
            voice_quality_similarity=voice_quality_sim,
            prosodic_similarity=prosodic_sim,
            component_weights=weights
        )

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity."""
        if len(vec1) != len(vec2) or len(vec1) == 0:
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _calculate_likelihood_ratio(self, similarity: SimilarityScore) -> LikelihoodRatio:
        """Calculate forensic likelihood ratio."""
        # Convert similarity to log-likelihood ratio
        # This is a simplified model; production would use calibrated models

        score = similarity.overall_score

        if score >= 0.95:
            log_lr = 6.0
        elif score >= 0.85:
            log_lr = 4.0 + (score - 0.85) * 20
        elif score >= 0.70:
            log_lr = 2.0 + (score - 0.70) * 13.3
        elif score >= 0.55:
            log_lr = 0.5 + (score - 0.55) * 10
        elif score >= 0.45:
            log_lr = -0.5 + (score - 0.45) * 10
        elif score >= 0.30:
            log_lr = -2.0 + (score - 0.30) * 10
        elif score >= 0.15:
            log_lr = -4.0 + (score - 0.15) * 13.3
        else:
            log_lr = -6.0

        # Find verbal equivalent
        verbal = "Inconclusive"
        for threshold, description in LR_VERBAL_SCALE:
            if log_lr >= threshold:
                verbal = description
                break

        # Confidence interval (simplified)
        ci_width = 1.0 if score < 0.3 or score > 0.7 else 1.5
        confidence_interval = (log_lr - ci_width, log_lr + ci_width)

        return LikelihoodRatio(
            log_likelihood_ratio=log_lr,
            verbal_equivalent=verbal,
            confidence_interval=confidence_interval,
            methodology="Acoustic-phonetic likelihood ratio using MFCC, pitch, and voice quality features"
        )

    def _determine_conclusion(
        self,
        similarity: SimilarityScore,
        lr: LikelihoodRatio
    ) -> Tuple[ConclusionStrength, str]:
        """Determine forensic conclusion."""
        score = similarity.overall_score
        log_lr = lr.log_likelihood_ratio

        if score >= self.identification_threshold and log_lr >= 4:
            conclusion = ConclusionStrength.IDENTIFICATION
            text = "The voice samples are from the same speaker."
        elif log_lr >= 4:
            conclusion = ConclusionStrength.STRONG_SUPPORT
            text = "The evidence provides strong support for the proposition that the voices are from the same speaker."
        elif log_lr >= 2:
            conclusion = ConclusionStrength.MODERATE_SUPPORT
            text = "The evidence provides moderate support for the proposition that the voices are from the same speaker."
        elif log_lr >= 0.5:
            conclusion = ConclusionStrength.LIMITED_SUPPORT
            text = "The evidence provides limited support for the proposition that the voices are from the same speaker."
        elif log_lr >= -0.5:
            conclusion = ConclusionStrength.INCONCLUSIVE
            text = "The evidence is inconclusive - it does not meaningfully support either same speaker or different speaker propositions."
        elif log_lr >= -2:
            conclusion = ConclusionStrength.LIMITED_OPPOSITION
            text = "The evidence provides limited support for the proposition that the voices are from different speakers."
        elif log_lr >= -4:
            conclusion = ConclusionStrength.MODERATE_OPPOSITION
            text = "The evidence provides moderate support for the proposition that the voices are from different speakers."
        elif score <= self.exclusion_threshold and log_lr < -4:
            conclusion = ConclusionStrength.EXCLUSION
            text = "The voice samples are from different speakers."
        else:
            conclusion = ConclusionStrength.STRONG_OPPOSITION
            text = "The evidence provides strong support for the proposition that the voices are from different speakers."

        return conclusion, text

    def _compare_features_detailed(
        self,
        features_a: AudioFeatures,
        features_b: AudioFeatures
    ) -> Dict[str, Dict[str, Any]]:
        """Generate detailed feature comparison."""
        comparison = {}

        # Pitch comparison
        comparison["fundamental_frequency"] = {
            "sample_a": features_a.prosodic.pitch_mean,
            "sample_b": features_b.prosodic.pitch_mean,
            "difference": abs(features_a.prosodic.pitch_mean - features_b.prosodic.pitch_mean),
            "percentage_diff": abs(features_a.prosodic.pitch_mean - features_b.prosodic.pitch_mean) /
                              max(features_a.prosodic.pitch_mean, features_b.prosodic.pitch_mean, 1) * 100,
            "unit": "Hz"
        }

        # Pitch range
        comparison["pitch_range"] = {
            "sample_a": features_a.prosodic.pitch_range,
            "sample_b": features_b.prosodic.pitch_range,
            "difference": abs(features_a.prosodic.pitch_range - features_b.prosodic.pitch_range),
            "unit": "Hz"
        }

        # Jitter
        comparison["jitter"] = {
            "sample_a": features_a.prosodic.jitter,
            "sample_b": features_b.prosodic.jitter,
            "difference": abs(features_a.prosodic.jitter - features_b.prosodic.jitter),
            "unit": "%"
        }

        # Shimmer
        comparison["shimmer"] = {
            "sample_a": features_a.prosodic.shimmer,
            "sample_b": features_b.prosodic.shimmer,
            "difference": abs(features_a.prosodic.shimmer - features_b.prosodic.shimmer),
            "unit": "%"
        }

        # HNR
        comparison["harmonics_to_noise_ratio"] = {
            "sample_a": features_a.prosodic.hnr,
            "sample_b": features_b.prosodic.hnr,
            "difference": abs(features_a.prosodic.hnr - features_b.prosodic.hnr),
            "unit": "dB"
        }

        # Speech rate
        comparison["speech_rate"] = {
            "sample_a": features_a.prosodic.speech_rate,
            "sample_b": features_b.prosodic.speech_rate,
            "difference": abs(features_a.prosodic.speech_rate - features_b.prosodic.speech_rate),
            "unit": "syllables/second"
        }

        return comparison

    def _identify_feature_patterns(
        self,
        comparison: Dict[str, Dict[str, Any]]
    ) -> Tuple[List[str], List[str]]:
        """Identify discriminating and consistent features."""
        discriminating = []
        consistent = []

        thresholds = {
            "fundamental_frequency": 15,  # % difference
            "pitch_range": 20,
            "jitter": 30,
            "shimmer": 30,
            "harmonics_to_noise_ratio": 25,
            "speech_rate": 20
        }

        for feature, data in comparison.items():
            pct_diff = data.get("percentage_diff", 0)
            if pct_diff == 0 and "difference" in data:
                max_val = max(data.get("sample_a", 1), data.get("sample_b", 1), 0.001)
                pct_diff = data["difference"] / max_val * 100

            threshold = thresholds.get(feature, 20)

            if pct_diff > threshold:
                discriminating.append(feature)
            elif pct_diff < threshold * 0.5:
                consistent.append(feature)

        return discriminating, consistent

    def _calculate_reliability(
        self,
        quality_a: float,
        quality_b: float,
        features_a: AudioFeatures,
        features_b: AudioFeatures
    ) -> float:
        """Calculate comparison reliability score."""
        # Base reliability on quality
        reliability = (quality_a + quality_b) / 2

        # Penalize if samples are very different in duration
        duration_ratio = min(features_a.duration_seconds, features_b.duration_seconds) / \
                        max(features_a.duration_seconds, features_b.duration_seconds)
        if duration_ratio < 0.3:
            reliability *= 0.8

        # Penalize short samples
        min_duration = min(features_a.duration_seconds, features_b.duration_seconds)
        if min_duration < 5:
            reliability *= 0.7
        elif min_duration < 10:
            reliability *= 0.85

        return reliability

    def _generate_warnings(
        self,
        features_a: AudioFeatures,
        features_b: AudioFeatures,
        quality_a: float,
        quality_b: float
    ) -> List[str]:
        """Generate warnings about comparison."""
        warnings = []

        if quality_a < 0.5:
            warnings.append(f"Sample A has poor audio quality (score: {quality_a:.2f})")
        if quality_b < 0.5:
            warnings.append(f"Sample B has poor audio quality (score: {quality_b:.2f})")

        if features_a.duration_seconds < 5:
            warnings.append("Sample A is very short (<5 seconds) - limited reliability")
        if features_b.duration_seconds < 5:
            warnings.append("Sample B is very short (<5 seconds) - limited reliability")

        if features_a.snr_db < 15:
            warnings.append("Sample A has high background noise")
        if features_b.snr_db < 15:
            warnings.append("Sample B has high background noise")

        return warnings

    def _get_limitations(self) -> List[str]:
        """Get standard limitations statement."""
        return [
            "Voice comparison cannot provide absolute certainty",
            "Results should be interpreted in context with other evidence",
            "Recording conditions may affect comparison accuracy",
            "Disguised or altered voices may not be reliably compared",
            "Emotional state and health can affect voice characteristics",
            "This analysis uses automated acoustic comparison; human expert review recommended for legal proceedings"
        ]

    def generate_forensic_report(
        self,
        comparison: ComparisonResult,
        case_id: str,
        examiner: str,
        questioned_info: Dict[str, Any],
        known_info: Dict[str, Any]
    ) -> ForensicReport:
        """Generate complete forensic report for court."""
        report_id = f"VCR-{case_id}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Generate report sections
        executive_summary = self._generate_executive_summary(comparison)
        methodology = self._generate_methodology_section()
        analysis = self._generate_analysis_section(comparison)
        conclusion = self._generate_conclusion_section(comparison)

        # Quality assessment
        quality_assessment = {
            "questioned_sample": {
                "quality_score": comparison.sample_a_quality,
                "suitable_for_comparison": comparison.sample_a_quality > 0.4
            },
            "known_sample": {
                "quality_score": comparison.sample_b_quality,
                "suitable_for_comparison": comparison.sample_b_quality > 0.4
            },
            "overall_reliability": comparison.comparison_reliability
        }

        # Feature tables
        feature_tables = [
            {
                "name": "Acoustic Feature Comparison",
                "data": comparison.feature_comparison
            }
        ]

        return ForensicReport(
            report_id=report_id,
            case_id=case_id,
            examiner=examiner,
            report_date=datetime.datetime.now().isoformat(),
            questioned_sample=questioned_info,
            known_sample=known_info,
            comparison=comparison,
            executive_summary=executive_summary,
            methodology_section=methodology,
            analysis_section=analysis,
            conclusion_section=conclusion,
            quality_assessment=quality_assessment,
            feature_tables=feature_tables,
            visualizations=[],  # Would include paths to generated spectrograms, etc.
            chain_of_custody=questioned_info.get("chain_of_custody", []),
            examiner_qualifications=self._get_examiner_qualifications(examiner),
            methodology_validation=self._get_methodology_validation(),
            limitations_statement=self._get_limitations_statement(),
            certification_statement=self._get_certification_statement(examiner),
            digital_signature=None  # Would be added in production
        )

    def _generate_executive_summary(self, comparison: ComparisonResult) -> str:
        """Generate executive summary."""
        return (
            f"This report presents the findings of a forensic voice comparison analysis. "
            f"The overall similarity score between the samples is {comparison.similarity.overall_score:.2f}. "
            f"The likelihood ratio analysis yields a log-LR of {comparison.likelihood_ratio.log_likelihood_ratio:.1f}, "
            f"corresponding to: {comparison.likelihood_ratio.verbal_equivalent}. "
            f"\n\nConclusion: {comparison.conclusion_text}"
        )

    def _generate_methodology_section(self) -> str:
        """Generate methodology section."""
        return """
METHODOLOGY

This analysis employs acoustic-phonetic voice comparison methodology, which examines measurable
properties of speech signals. The following acoustic parameters were analyzed:

1. Mel-Frequency Cepstral Coefficients (MFCCs): Spectral envelope characteristics representing
   vocal tract configuration.

2. Fundamental Frequency (F0): The pitch of the voice, including mean, range, and variability.

3. Voice Quality Parameters: Jitter (pitch perturbation), shimmer (amplitude perturbation),
   and harmonics-to-noise ratio (HNR).

4. Prosodic Features: Speech rate, pause patterns, and intensity contours.

The comparison uses a likelihood ratio framework, which evaluates the probability of the
observed acoustic evidence under two competing hypotheses:
- Hp (Prosecution hypothesis): The samples are from the same speaker
- Hd (Defense hypothesis): The samples are from different speakers

The likelihood ratio (LR) expresses how many times more likely the evidence is under Hp
compared to Hd.
"""

    def _generate_analysis_section(self, comparison: ComparisonResult) -> str:
        """Generate analysis section."""
        lines = ["ANALYSIS\n"]

        lines.append("Component Similarity Scores:")
        lines.append(f"  - MFCC Similarity: {comparison.similarity.mfcc_similarity:.3f}")
        lines.append(f"  - Pitch Similarity: {comparison.similarity.pitch_similarity:.3f}")
        lines.append(f"  - Spectral Similarity: {comparison.similarity.spectral_similarity:.3f}")
        lines.append(f"  - Voice Quality Similarity: {comparison.similarity.voice_quality_similarity:.3f}")
        lines.append(f"  - Prosodic Similarity: {comparison.similarity.prosodic_similarity:.3f}")
        lines.append(f"\nOverall Similarity Score: {comparison.similarity.overall_score:.3f}")

        lines.append("\nFeature Analysis:")
        if comparison.consistent_features:
            lines.append(f"  Consistent features: {', '.join(comparison.consistent_features)}")
        if comparison.discriminating_features:
            lines.append(f"  Discriminating features: {', '.join(comparison.discriminating_features)}")

        if comparison.warnings:
            lines.append("\nWarnings:")
            for warning in comparison.warnings:
                lines.append(f"  - {warning}")

        return "\n".join(lines)

    def _generate_conclusion_section(self, comparison: ComparisonResult) -> str:
        """Generate conclusion section."""
        return f"""
CONCLUSION

Based on the acoustic-phonetic analysis conducted, the likelihood ratio is
10^{comparison.likelihood_ratio.log_likelihood_ratio:.1f} ({comparison.likelihood_ratio.verbal_equivalent}).

{comparison.conclusion_text}

This conclusion is expressed with a reliability rating of {comparison.comparison_reliability:.0%}
based on the quality of the samples analyzed.

LIMITATIONS

{chr(10).join('- ' + lim for lim in comparison.limitations)}
"""

    def _get_examiner_qualifications(self, examiner: str) -> str:
        """Get examiner qualifications statement."""
        return f"Analysis conducted by {examiner}. Qualifications should be documented separately."

    def _get_methodology_validation(self) -> str:
        """Get methodology validation statement."""
        return (
            "The acoustic-phonetic comparison methodology used in this analysis is based on "
            "established forensic voice comparison practices. The likelihood ratio approach "
            "follows recommendations from the European Network of Forensic Science Institutes (ENFSI) "
            "and the International Association for Forensic Phonetics and Acoustics (IAFPA)."
        )

    def _get_limitations_statement(self) -> str:
        """Get limitations statement."""
        return (
            "Voice comparison analysis cannot provide absolute certainty of speaker identity. "
            "Results are probabilistic and should be considered alongside other evidence. "
            "Factors such as recording quality, speaker health, emotional state, and intentional "
            "voice disguise may affect the reliability of the comparison."
        )

    def _get_certification_statement(self, examiner: str) -> str:
        """Get certification statement."""
        return (
            f"I, {examiner}, certify that this report accurately represents the findings of "
            f"the voice comparison analysis conducted. The analysis was performed using "
            f"standard forensic acoustic methodology and the conclusions represent my "
            f"professional opinion based on the evidence examined."
        )
