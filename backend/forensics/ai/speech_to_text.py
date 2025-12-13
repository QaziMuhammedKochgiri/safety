"""
Speech-to-Text Module for SafeChild

Provides audio transcription using OpenAI Whisper (self-hosted).
Supports WhatsApp voice notes, Telegram audio, and video audio extraction.
"""

import os
import io
import logging
import tempfile
import subprocess
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class AudioFormat(Enum):
    """Supported audio formats"""
    OPUS = "opus"       # WhatsApp voice notes
    OGG = "ogg"         # Telegram audio
    M4A = "m4a"         # iPhone recordings
    MP3 = "mp3"         # Standard audio
    WAV = "wav"         # Uncompressed
    AAC = "aac"         # Common mobile format
    WEBM = "webm"       # Video audio
    MP4 = "mp4"         # Video with audio
    MOV = "mov"         # iPhone video


class TranscriptionSource(Enum):
    """Source of audio file"""
    WHATSAPP_VOICE = "whatsapp_voice"
    TELEGRAM_VOICE = "telegram_voice"
    PHONE_RECORDING = "phone_recording"
    VIDEO_AUDIO = "video_audio"
    UNKNOWN = "unknown"


@dataclass
class TranscriptSegment:
    """Individual segment of transcription with timestamp"""
    start: float           # Start time in seconds
    end: float             # End time in seconds
    text: str              # Transcribed text
    confidence: float = 0.0  # Confidence score (0-1)
    speaker: Optional[str] = None  # Speaker ID if diarization enabled

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start,
            "end": self.end,
            "text": self.text,
            "confidence": self.confidence,
            "speaker": self.speaker,
            "startFormatted": self._format_time(self.start),
            "endFormatted": self._format_time(self.end)
        }

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds as MM:SS.ms"""
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins:02d}:{secs:05.2f}"


@dataclass
class TranscriptionResult:
    """Full transcription result"""
    id: str
    case_id: str
    file_name: str
    source: TranscriptionSource
    language: str
    duration: float           # Duration in seconds
    full_text: str           # Complete transcription
    segments: List[TranscriptSegment] = field(default_factory=list)
    word_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    processing_time: float = 0.0
    model_used: str = "whisper-base"

    # Analysis results
    keywords: List[str] = field(default_factory=list)
    sentiment_score: float = 0.0  # -1 to 1
    risk_indicators: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "caseId": self.case_id,
            "fileName": self.file_name,
            "source": self.source.value,
            "language": self.language,
            "duration": self.duration,
            "durationFormatted": self._format_duration(self.duration),
            "fullText": self.full_text,
            "segments": [s.to_dict() for s in self.segments],
            "wordCount": self.word_count,
            "createdAt": self.created_at.isoformat(),
            "processingTime": self.processing_time,
            "modelUsed": self.model_used,
            "keywords": self.keywords,
            "sentimentScore": self.sentiment_score,
            "riskIndicators": self.risk_indicators
        }

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration as HH:MM:SS"""
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"


class AudioProcessor:
    """Handles audio extraction and format conversion"""

    # Supported input formats
    SUPPORTED_FORMATS = {'.opus', '.ogg', '.m4a', '.mp3', '.wav', '.aac',
                         '.webm', '.mp4', '.mov', '.3gp', '.amr'}

    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()

    def _find_ffmpeg(self) -> str:
        """Find ffmpeg binary"""
        # Check common locations
        paths = [
            "ffmpeg",
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            "/opt/homebrew/bin/ffmpeg"
        ]

        for path in paths:
            try:
                result = subprocess.run(
                    [path, "-version"],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return path
            except:
                continue

        logger.warning("ffmpeg not found, audio conversion may fail")
        return "ffmpeg"

    def extract_audio_from_video(
        self,
        video_data: bytes,
        output_format: str = "wav"
    ) -> Tuple[bytes, float]:
        """
        Extract audio track from video file.

        Returns:
            Tuple of (audio_data, duration_seconds)
        """
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as video_file:
            video_file.write(video_data)
            video_path = video_file.name

        with tempfile.NamedTemporaryFile(suffix=f".{output_format}", delete=False) as audio_file:
            audio_path = audio_file.name

        try:
            # Extract audio using ffmpeg
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-vn",  # No video
                "-acodec", "pcm_s16le" if output_format == "wav" else "libmp3lame",
                "-ar", "16000",  # 16kHz for Whisper
                "-ac", "1",  # Mono
                "-y",  # Overwrite
                audio_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=300  # 5 minutes max
            )

            if result.returncode != 0:
                logger.error(f"ffmpeg error: {result.stderr.decode()}")
                raise Exception("Audio extraction failed")

            # Get duration
            duration = self._get_audio_duration(audio_path)

            # Read output
            with open(audio_path, "rb") as f:
                audio_data = f.read()

            return audio_data, duration

        finally:
            # Cleanup temp files
            try:
                os.unlink(video_path)
                os.unlink(audio_path)
            except:
                pass

    def convert_to_wav(
        self,
        audio_data: bytes,
        input_format: str
    ) -> Tuple[bytes, float]:
        """
        Convert audio to WAV format (16kHz mono) for Whisper.

        Returns:
            Tuple of (wav_data, duration_seconds)
        """
        with tempfile.NamedTemporaryFile(suffix=f".{input_format}", delete=False) as input_file:
            input_file.write(audio_data)
            input_path = input_file.name

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as output_file:
            output_path = output_file.name

        try:
            cmd = [
                self.ffmpeg_path,
                "-i", input_path,
                "-acodec", "pcm_s16le",
                "-ar", "16000",  # 16kHz for Whisper
                "-ac", "1",  # Mono
                "-y",
                output_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=60
            )

            if result.returncode != 0:
                logger.error(f"ffmpeg conversion error: {result.stderr.decode()}")
                raise Exception(f"Audio conversion failed: {input_format} to WAV")

            duration = self._get_audio_duration(output_path)

            with open(output_path, "rb") as f:
                wav_data = f.read()

            return wav_data, duration

        finally:
            try:
                os.unlink(input_path)
                os.unlink(output_path)
            except:
                pass

    def _get_audio_duration(self, file_path: str) -> float:
        """Get audio duration using ffprobe"""
        try:
            ffprobe = self.ffmpeg_path.replace("ffmpeg", "ffprobe")
            cmd = [
                ffprobe,
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10
            )

            if result.returncode == 0:
                return float(result.stdout.decode().strip())
        except:
            pass

        return 0.0

    def detect_source(self, file_name: str, metadata: Optional[Dict] = None) -> TranscriptionSource:
        """Detect audio source from filename and metadata"""
        name_lower = file_name.lower()

        # WhatsApp patterns
        if "ptt" in name_lower or "aud-" in name_lower:
            return TranscriptionSource.WHATSAPP_VOICE
        if name_lower.endswith(".opus") and "whatsapp" in name_lower:
            return TranscriptionSource.WHATSAPP_VOICE

        # Telegram patterns
        if "telegram" in name_lower or name_lower.startswith("audio_"):
            return TranscriptionSource.TELEGRAM_VOICE

        # Video extraction
        ext = Path(file_name).suffix.lower()
        if ext in {'.mp4', '.mov', '.webm', '.3gp'}:
            return TranscriptionSource.VIDEO_AUDIO

        # Phone recording
        if "recording" in name_lower or "voice" in name_lower:
            return TranscriptionSource.PHONE_RECORDING

        return TranscriptionSource.UNKNOWN


class WhisperTranscriber:
    """
    OpenAI Whisper transcription engine (self-hosted).

    Supports:
    - Multiple model sizes (tiny, base, small, medium, large)
    - Multi-language transcription
    - Automatic language detection
    - Timestamp-aligned segments
    """

    # Model sizes and their characteristics
    MODELS = {
        "tiny": {"size": "39M", "vram": "1GB", "speed": "~32x"},
        "base": {"size": "74M", "vram": "1GB", "speed": "~16x"},
        "small": {"size": "244M", "vram": "2GB", "speed": "~6x"},
        "medium": {"size": "769M", "vram": "5GB", "speed": "~2x"},
        "large": {"size": "1550M", "vram": "10GB", "speed": "~1x"}
    }

    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load Whisper model"""
        try:
            import whisper
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            logger.info(f"Whisper model loaded successfully")
        except ImportError:
            logger.warning("Whisper not installed. Install with: pip install openai-whisper")
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.model = None

    def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        task: str = "transcribe"  # or "translate" for English translation
    ) -> Dict[str, Any]:
        """
        Transcribe audio using Whisper.

        Args:
            audio_data: WAV audio bytes
            language: ISO language code (e.g., "tr", "en") or None for auto-detect
            task: "transcribe" or "translate" (to English)

        Returns:
            Dict with transcription result
        """
        if self.model is None:
            # Fallback: return empty result if Whisper not available
            return self._fallback_transcribe(audio_data)

        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            audio_path = f.name

        try:
            import time
            start_time = time.time()

            # Transcribe
            result = self.model.transcribe(
                audio_path,
                language=language,
                task=task,
                verbose=False
            )

            processing_time = time.time() - start_time

            # Build segments
            segments = []
            for seg in result.get("segments", []):
                segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"].strip(),
                    "confidence": seg.get("avg_logprob", 0)
                })

            return {
                "text": result["text"].strip(),
                "language": result.get("language", language or "unknown"),
                "segments": segments,
                "processing_time": processing_time
            }

        finally:
            try:
                os.unlink(audio_path)
            except:
                pass

    def _fallback_transcribe(self, audio_data: bytes) -> Dict[str, Any]:
        """Fallback when Whisper is not available"""
        logger.warning("Whisper not available, returning placeholder")
        return {
            "text": "[Transcription not available - Whisper model not loaded]",
            "language": "unknown",
            "segments": [],
            "processing_time": 0
        }

    def detect_language(self, audio_data: bytes) -> str:
        """Detect audio language"""
        if self.model is None:
            return "unknown"

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            audio_path = f.name

        try:
            import whisper

            # Load audio and pad/trim
            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio)

            # Make log-Mel spectrogram
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)

            # Detect language
            _, probs = self.model.detect_language(mel)
            detected = max(probs, key=probs.get)

            return detected

        finally:
            try:
                os.unlink(audio_path)
            except:
                pass


class TranscriptAnalyzer:
    """Analyze transcriptions for keywords, sentiment, and risk indicators"""

    # Risk keywords by category (Turkish & English)
    RISK_KEYWORDS = {
        "threats": [
            "öldüreceğim", "döveceğim", "kill", "hurt", "harm",
            "vuracağım", "seni mahvedeceğim", "pişman olacaksın"
        ],
        "manipulation": [
            "annen seni sevmiyor", "baban kötü", "daddy doesn't love",
            "mommy is bad", "beni seçmelisin", "onlarla görüşme"
        ],
        "alienation": [
            "onlara gitme", "onları aramayacaksın", "ben yokken",
            "seninle olmak istemiyorlar", "senden nefret ediyorlar"
        ],
        "emotional_abuse": [
            "aptal", "salak", "işe yaramaz", "stupid", "worthless",
            "useless", "seni istemiyorum", "keşke olmasaydın"
        ],
        "coercion": [
            "söylemezsen", "if you tell", "cezalandırırım",
            "kimseye söyleme", "aramızda kalsın", "secret"
        ]
    }

    def analyze(self, transcript: str, language: str = "tr") -> Dict[str, Any]:
        """
        Analyze transcript for keywords, sentiment, and risk.

        Returns:
            Dict with analysis results
        """
        text_lower = transcript.lower()

        # Find risk keywords
        found_risks = []
        risk_categories = []

        for category, keywords in self.RISK_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    found_risks.append(keyword)
                    if category not in risk_categories:
                        risk_categories.append(category)

        # Simple sentiment analysis (placeholder for actual model)
        sentiment = self._simple_sentiment(text_lower, language)

        # Extract keywords
        keywords = self._extract_keywords(transcript, language)

        return {
            "riskIndicators": found_risks,
            "riskCategories": risk_categories,
            "riskLevel": self._calculate_risk_level(found_risks, risk_categories),
            "sentiment": sentiment,
            "keywords": keywords
        }

    def _simple_sentiment(self, text: str, language: str) -> float:
        """Simple rule-based sentiment (placeholder for actual model)"""
        positive_words = {"iyi", "güzel", "seviyorum", "mutlu", "good", "love", "happy", "nice"}
        negative_words = {"kötü", "nefret", "kızgın", "üzgün", "bad", "hate", "angry", "sad"}

        words = set(text.split())
        pos_count = len(words & positive_words)
        neg_count = len(words & negative_words)

        if pos_count + neg_count == 0:
            return 0.0

        return (pos_count - neg_count) / (pos_count + neg_count)

    def _extract_keywords(self, text: str, language: str, max_keywords: int = 10) -> List[str]:
        """Extract important keywords from text"""
        # Simple word frequency approach
        import re

        # Turkish stopwords
        stopwords = {
            "ve", "bir", "bu", "da", "de", "için", "ile", "ne", "var", "yok",
            "ben", "sen", "o", "biz", "siz", "onlar", "mi", "mı", "mu", "mü",
            "the", "a", "an", "is", "are", "was", "were", "to", "of", "and", "in"
        }

        # Clean and tokenize
        words = re.findall(r'\b\w+\b', text.lower())
        words = [w for w in words if len(w) > 2 and w not in stopwords]

        # Count frequencies
        freq = {}
        for word in words:
            freq[word] = freq.get(word, 0) + 1

        # Sort by frequency
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)

        return [w for w, _ in sorted_words[:max_keywords]]

    def _calculate_risk_level(self, risks: List[str], categories: List[str]) -> str:
        """Calculate overall risk level"""
        if len(risks) >= 5 or len(categories) >= 3:
            return "high"
        elif len(risks) >= 2 or len(categories) >= 2:
            return "medium"
        elif len(risks) >= 1:
            return "low"
        return "none"


class SpeechToTextEngine:
    """
    Main Speech-to-Text engine combining all components.
    """

    def __init__(self, whisper_model: str = "base"):
        self.audio_processor = AudioProcessor()
        self.transcriber = WhisperTranscriber(whisper_model)
        self.analyzer = TranscriptAnalyzer()

    def process_audio(
        self,
        audio_data: bytes,
        file_name: str,
        case_id: str,
        metadata: Optional[Dict] = None,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Process audio file and return full transcription result.

        Args:
            audio_data: Raw audio file bytes
            file_name: Original filename
            case_id: Associated case ID
            metadata: Optional metadata
            language: Language code or None for auto-detect

        Returns:
            TranscriptionResult with transcription and analysis
        """
        import time
        start_time = time.time()

        # Generate ID
        file_hash = hashlib.md5(audio_data[:1024]).hexdigest()[:8]
        result_id = f"tr_{case_id}_{file_hash}"

        # Detect source
        source = self.audio_processor.detect_source(file_name, metadata)

        # Get file extension
        ext = Path(file_name).suffix.lower().lstrip('.')

        # Convert to WAV if needed
        if ext in {'mp4', 'mov', 'webm', '3gp'}:
            # Extract audio from video
            wav_data, duration = self.audio_processor.extract_audio_from_video(audio_data)
        elif ext != 'wav':
            # Convert audio format
            wav_data, duration = self.audio_processor.convert_to_wav(audio_data, ext)
        else:
            wav_data = audio_data
            duration = self.audio_processor._get_audio_duration_from_bytes(audio_data)

        # Detect language if not specified
        if language is None:
            language = self.transcriber.detect_language(wav_data)

        # Transcribe
        whisper_result = self.transcriber.transcribe(wav_data, language)

        # Build segments
        segments = [
            TranscriptSegment(
                start=s["start"],
                end=s["end"],
                text=s["text"],
                confidence=s.get("confidence", 0)
            )
            for s in whisper_result.get("segments", [])
        ]

        # Analyze
        analysis = self.analyzer.analyze(
            whisper_result["text"],
            whisper_result.get("language", language or "unknown")
        )

        # Calculate word count
        word_count = len(whisper_result["text"].split())

        processing_time = time.time() - start_time

        return TranscriptionResult(
            id=result_id,
            case_id=case_id,
            file_name=file_name,
            source=source,
            language=whisper_result.get("language", language or "unknown"),
            duration=duration,
            full_text=whisper_result["text"],
            segments=segments,
            word_count=word_count,
            processing_time=processing_time,
            model_used=f"whisper-{self.transcriber.model_name}",
            keywords=analysis["keywords"],
            sentiment_score=analysis["sentiment"],
            risk_indicators=analysis["riskIndicators"]
        )

    def batch_process(
        self,
        files: List[Tuple[bytes, str]],  # List of (data, filename)
        case_id: str,
        language: Optional[str] = None
    ) -> List[TranscriptionResult]:
        """Process multiple audio files"""
        results = []

        for audio_data, file_name in files:
            try:
                result = self.process_audio(
                    audio_data=audio_data,
                    file_name=file_name,
                    case_id=case_id,
                    language=language
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {file_name}: {e}")
                continue

        return results

    def search_transcripts(
        self,
        transcripts: List[TranscriptionResult],
        query: str,
        case_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search through transcripts for a query.

        Returns list of matches with context.
        """
        results = []

        if not case_sensitive:
            query = query.lower()

        for transcript in transcripts:
            text = transcript.full_text if case_sensitive else transcript.full_text.lower()

            if query in text:
                # Find matching segments
                matching_segments = []
                for seg in transcript.segments:
                    seg_text = seg.text if case_sensitive else seg.text.lower()
                    if query in seg_text:
                        matching_segments.append(seg.to_dict())

                results.append({
                    "transcriptId": transcript.id,
                    "fileName": transcript.file_name,
                    "source": transcript.source.value,
                    "matchCount": text.count(query),
                    "matchingSegments": matching_segments
                })

        return results


# Utility function for extracting voice notes from WhatsApp export
def extract_whatsapp_voice_notes(export_path: str) -> List[Tuple[bytes, str]]:
    """
    Extract voice note files from WhatsApp export folder.

    Returns list of (file_data, filename) tuples.
    """
    voice_notes = []
    export_dir = Path(export_path)

    # WhatsApp voice note patterns
    patterns = ["*.opus", "*.ogg", "PTT-*.opus", "AUD-*.opus"]

    for pattern in patterns:
        for file_path in export_dir.rglob(pattern):
            try:
                with open(file_path, "rb") as f:
                    data = f.read()
                voice_notes.append((data, file_path.name))
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")

    return voice_notes
