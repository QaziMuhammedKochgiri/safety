"""
Mobile Evidence Capture
Captures evidence using mobile device capabilities with forensic integrity.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import datetime
import hashlib


class CaptureType(str, Enum):
    """Types of evidence capture."""
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    SCREENSHOT = "screenshot"
    LOCATION = "location"
    DOCUMENT_SCAN = "document_scan"
    SCREEN_RECORDING = "screen_recording"


class CaptureQuality(str, Enum):
    """Quality settings for capture."""
    LOW = "low"  # Smaller file, faster upload
    MEDIUM = "medium"  # Balanced
    HIGH = "high"  # Best quality
    ORIGINAL = "original"  # No compression


class CaptureSource(str, Enum):
    """Source of the captured media."""
    FRONT_CAMERA = "front_camera"
    REAR_CAMERA = "rear_camera"
    SCREEN = "screen"
    MICROPHONE = "microphone"
    FILE_PICKER = "file_picker"
    SCANNER = "scanner"


@dataclass
class LocationCapture:
    """Location data captured with evidence."""
    latitude: float
    longitude: float
    accuracy_meters: float
    altitude_meters: Optional[float]
    altitude_accuracy: Optional[float]
    heading: Optional[float]
    speed: Optional[float]
    timestamp: str
    source: str  # gps, network, ip, manual
    address: Optional[str]
    place_name: Optional[str]


@dataclass
class MediaCapture:
    """Base class for media captures."""
    capture_id: str
    capture_type: CaptureType
    case_id: Optional[str]
    user_id: str
    device_id: str

    # File info
    file_name: str
    file_size_bytes: int
    mime_type: str
    duration_seconds: Optional[float]

    # Quality and source
    quality: CaptureQuality
    source: CaptureSource

    # Forensic metadata
    captured_at: str
    capture_timestamp_utc: str
    timezone: str
    content_hash: str  # SHA-256
    is_original: bool  # No editing applied

    # Location
    location: Optional[LocationCapture]

    # Device info at capture
    device_orientation: str
    device_battery_level: Optional[int]
    network_type: Optional[str]

    # Chain of custody
    chain_of_custody: List[Dict[str, Any]]

    # Processing
    is_processed: bool
    processing_notes: Optional[str]

    # Storage
    local_path: Optional[str]
    cloud_path: Optional[str]
    is_synced: bool


@dataclass
class PhotoCapture(MediaCapture):
    """A photo capture."""
    width: int
    height: int
    has_exif: bool
    exif_data: Optional[Dict[str, Any]]
    flash_used: bool
    focal_length: Optional[float]
    iso: Optional[int]
    exposure_time: Optional[str]
    aperture: Optional[float]


@dataclass
class VoiceRecording(MediaCapture):
    """A voice/audio recording."""
    sample_rate: int
    channels: int
    bit_depth: int
    codec: str
    has_transcript: bool
    transcript: Optional[str]
    speakers_detected: int
    noise_level: Optional[str]  # low, medium, high


@dataclass
class VideoCapture(MediaCapture):
    """A video capture."""
    width: int
    height: int
    frame_rate: float
    video_codec: str
    audio_codec: Optional[str]
    has_audio: bool
    thumbnail_path: Optional[str]


@dataclass
class DocumentScan(MediaCapture):
    """A document scan."""
    page_count: int
    pages: List[str]  # Paths to individual page images
    has_ocr: bool
    ocr_text: Optional[str]
    document_type: Optional[str]  # id, letter, form, receipt, etc.
    language_detected: Optional[str]
    confidence_score: Optional[float]


@dataclass
class CaptureSession:
    """A capture session containing multiple captures."""
    session_id: str
    case_id: Optional[str]
    user_id: str
    device_id: str
    started_at: str
    ended_at: Optional[str]
    captures: List[str]  # capture_ids
    description: Optional[str]
    tags: List[str]
    is_complete: bool


class MobileEvidenceCapture:
    """Manages mobile evidence capture with forensic integrity."""

    # Supported formats
    SUPPORTED_PHOTO_FORMATS = ["image/jpeg", "image/png", "image/heic", "image/webp"]
    SUPPORTED_VIDEO_FORMATS = ["video/mp4", "video/webm", "video/quicktime"]
    SUPPORTED_AUDIO_FORMATS = ["audio/mp3", "audio/wav", "audio/ogg", "audio/m4a", "audio/aac"]

    # Max file sizes (bytes)
    MAX_PHOTO_SIZE = 50 * 1024 * 1024  # 50 MB
    MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500 MB
    MAX_AUDIO_SIZE = 100 * 1024 * 1024  # 100 MB

    # Quality presets
    QUALITY_PRESETS = {
        CaptureQuality.LOW: {"photo_max_dim": 1280, "video_bitrate": 1000000},
        CaptureQuality.MEDIUM: {"photo_max_dim": 1920, "video_bitrate": 2500000},
        CaptureQuality.HIGH: {"photo_max_dim": 3840, "video_bitrate": 5000000},
        CaptureQuality.ORIGINAL: {"photo_max_dim": None, "video_bitrate": None}
    }

    def __init__(self):
        self.captures: Dict[str, MediaCapture] = {}
        self.sessions: Dict[str, CaptureSession] = {}
        self.active_sessions: Dict[str, str] = {}  # device_id -> session_id

    def start_capture_session(
        self,
        user_id: str,
        device_id: str,
        case_id: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> CaptureSession:
        """Start a new capture session."""
        session_id = hashlib.md5(
            f"{user_id}-{device_id}-{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        session = CaptureSession(
            session_id=session_id,
            case_id=case_id,
            user_id=user_id,
            device_id=device_id,
            started_at=datetime.datetime.now().isoformat(),
            ended_at=None,
            captures=[],
            description=description,
            tags=tags or [],
            is_complete=False
        )

        self.sessions[session_id] = session
        self.active_sessions[device_id] = session_id

        return session

    def end_capture_session(self, session_id: str) -> bool:
        """End a capture session."""
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]
        session.ended_at = datetime.datetime.now().isoformat()
        session.is_complete = True

        # Remove from active sessions
        for device_id, sid in list(self.active_sessions.items()):
            if sid == session_id:
                del self.active_sessions[device_id]

        return True

    def capture_photo(
        self,
        user_id: str,
        device_id: str,
        file_data: bytes,
        mime_type: str,
        width: int,
        height: int,
        source: CaptureSource,
        quality: CaptureQuality = CaptureQuality.HIGH,
        case_id: Optional[str] = None,
        location: Optional[LocationCapture] = None,
        exif_data: Optional[Dict[str, Any]] = None,
        device_orientation: str = "portrait",
        device_battery_level: Optional[int] = None,
        network_type: Optional[str] = None
    ) -> PhotoCapture:
        """Capture a photo with forensic metadata."""
        # Validate
        if mime_type not in self.SUPPORTED_PHOTO_FORMATS:
            raise ValueError(f"Unsupported photo format: {mime_type}")
        if len(file_data) > self.MAX_PHOTO_SIZE:
            raise ValueError(f"Photo too large: {len(file_data)} bytes")

        capture_id = self._generate_capture_id("photo", user_id)
        now = datetime.datetime.now()
        content_hash = hashlib.sha256(file_data).hexdigest()

        photo = PhotoCapture(
            capture_id=capture_id,
            capture_type=CaptureType.PHOTO,
            case_id=case_id,
            user_id=user_id,
            device_id=device_id,
            file_name=f"{capture_id}.{self._get_extension(mime_type)}",
            file_size_bytes=len(file_data),
            mime_type=mime_type,
            duration_seconds=None,
            quality=quality,
            source=source,
            captured_at=now.isoformat(),
            capture_timestamp_utc=now.utcnow().isoformat(),
            timezone=str(datetime.datetime.now().astimezone().tzinfo),
            content_hash=content_hash,
            is_original=True,
            location=location,
            device_orientation=device_orientation,
            device_battery_level=device_battery_level,
            network_type=network_type,
            chain_of_custody=[{
                "action": "captured",
                "timestamp": now.isoformat(),
                "device_id": device_id,
                "hash": content_hash
            }],
            is_processed=False,
            processing_notes=None,
            local_path=None,
            cloud_path=None,
            is_synced=False,
            width=width,
            height=height,
            has_exif=exif_data is not None,
            exif_data=exif_data,
            flash_used=exif_data.get("flash", False) if exif_data else False,
            focal_length=exif_data.get("focal_length") if exif_data else None,
            iso=exif_data.get("iso") if exif_data else None,
            exposure_time=exif_data.get("exposure_time") if exif_data else None,
            aperture=exif_data.get("aperture") if exif_data else None
        )

        self.captures[capture_id] = photo
        self._add_to_active_session(device_id, capture_id)

        return photo

    def capture_voice_recording(
        self,
        user_id: str,
        device_id: str,
        file_data: bytes,
        mime_type: str,
        duration_seconds: float,
        sample_rate: int,
        channels: int,
        quality: CaptureQuality = CaptureQuality.HIGH,
        case_id: Optional[str] = None,
        location: Optional[LocationCapture] = None,
        device_orientation: str = "portrait",
        device_battery_level: Optional[int] = None,
        network_type: Optional[str] = None
    ) -> VoiceRecording:
        """Capture a voice recording with forensic metadata."""
        # Validate
        if mime_type not in self.SUPPORTED_AUDIO_FORMATS:
            raise ValueError(f"Unsupported audio format: {mime_type}")
        if len(file_data) > self.MAX_AUDIO_SIZE:
            raise ValueError(f"Audio too large: {len(file_data)} bytes")

        capture_id = self._generate_capture_id("audio", user_id)
        now = datetime.datetime.now()
        content_hash = hashlib.sha256(file_data).hexdigest()

        recording = VoiceRecording(
            capture_id=capture_id,
            capture_type=CaptureType.AUDIO,
            case_id=case_id,
            user_id=user_id,
            device_id=device_id,
            file_name=f"{capture_id}.{self._get_extension(mime_type)}",
            file_size_bytes=len(file_data),
            mime_type=mime_type,
            duration_seconds=duration_seconds,
            quality=quality,
            source=CaptureSource.MICROPHONE,
            captured_at=now.isoformat(),
            capture_timestamp_utc=now.utcnow().isoformat(),
            timezone=str(datetime.datetime.now().astimezone().tzinfo),
            content_hash=content_hash,
            is_original=True,
            location=location,
            device_orientation=device_orientation,
            device_battery_level=device_battery_level,
            network_type=network_type,
            chain_of_custody=[{
                "action": "captured",
                "timestamp": now.isoformat(),
                "device_id": device_id,
                "hash": content_hash
            }],
            is_processed=False,
            processing_notes=None,
            local_path=None,
            cloud_path=None,
            is_synced=False,
            sample_rate=sample_rate,
            channels=channels,
            bit_depth=16,  # Standard
            codec=self._get_codec_from_mime(mime_type),
            has_transcript=False,
            transcript=None,
            speakers_detected=0,
            noise_level=None
        )

        self.captures[capture_id] = recording
        self._add_to_active_session(device_id, capture_id)

        return recording

    def capture_video(
        self,
        user_id: str,
        device_id: str,
        file_data: bytes,
        mime_type: str,
        width: int,
        height: int,
        duration_seconds: float,
        frame_rate: float,
        source: CaptureSource,
        quality: CaptureQuality = CaptureQuality.HIGH,
        has_audio: bool = True,
        case_id: Optional[str] = None,
        location: Optional[LocationCapture] = None,
        device_orientation: str = "portrait",
        device_battery_level: Optional[int] = None,
        network_type: Optional[str] = None
    ) -> VideoCapture:
        """Capture a video with forensic metadata."""
        # Validate
        if mime_type not in self.SUPPORTED_VIDEO_FORMATS:
            raise ValueError(f"Unsupported video format: {mime_type}")
        if len(file_data) > self.MAX_VIDEO_SIZE:
            raise ValueError(f"Video too large: {len(file_data)} bytes")

        capture_id = self._generate_capture_id("video", user_id)
        now = datetime.datetime.now()
        content_hash = hashlib.sha256(file_data).hexdigest()

        video = VideoCapture(
            capture_id=capture_id,
            capture_type=CaptureType.VIDEO,
            case_id=case_id,
            user_id=user_id,
            device_id=device_id,
            file_name=f"{capture_id}.{self._get_extension(mime_type)}",
            file_size_bytes=len(file_data),
            mime_type=mime_type,
            duration_seconds=duration_seconds,
            quality=quality,
            source=source,
            captured_at=now.isoformat(),
            capture_timestamp_utc=now.utcnow().isoformat(),
            timezone=str(datetime.datetime.now().astimezone().tzinfo),
            content_hash=content_hash,
            is_original=True,
            location=location,
            device_orientation=device_orientation,
            device_battery_level=device_battery_level,
            network_type=network_type,
            chain_of_custody=[{
                "action": "captured",
                "timestamp": now.isoformat(),
                "device_id": device_id,
                "hash": content_hash
            }],
            is_processed=False,
            processing_notes=None,
            local_path=None,
            cloud_path=None,
            is_synced=False,
            width=width,
            height=height,
            frame_rate=frame_rate,
            video_codec=self._get_video_codec_from_mime(mime_type),
            audio_codec="aac" if has_audio else None,
            has_audio=has_audio,
            thumbnail_path=None
        )

        self.captures[capture_id] = video
        self._add_to_active_session(device_id, capture_id)

        return video

    def scan_document(
        self,
        user_id: str,
        device_id: str,
        pages: List[bytes],
        quality: CaptureQuality = CaptureQuality.HIGH,
        case_id: Optional[str] = None,
        location: Optional[LocationCapture] = None,
        document_type: Optional[str] = None,
        device_orientation: str = "portrait",
        device_battery_level: Optional[int] = None,
        network_type: Optional[str] = None
    ) -> DocumentScan:
        """Scan a document with multiple pages."""
        capture_id = self._generate_capture_id("scan", user_id)
        now = datetime.datetime.now()

        # Calculate combined hash
        combined = b"".join(pages)
        content_hash = hashlib.sha256(combined).hexdigest()

        scan = DocumentScan(
            capture_id=capture_id,
            capture_type=CaptureType.DOCUMENT_SCAN,
            case_id=case_id,
            user_id=user_id,
            device_id=device_id,
            file_name=f"{capture_id}.pdf",
            file_size_bytes=len(combined),
            mime_type="application/pdf",
            duration_seconds=None,
            quality=quality,
            source=CaptureSource.SCANNER,
            captured_at=now.isoformat(),
            capture_timestamp_utc=now.utcnow().isoformat(),
            timezone=str(datetime.datetime.now().astimezone().tzinfo),
            content_hash=content_hash,
            is_original=True,
            location=location,
            device_orientation=device_orientation,
            device_battery_level=device_battery_level,
            network_type=network_type,
            chain_of_custody=[{
                "action": "captured",
                "timestamp": now.isoformat(),
                "device_id": device_id,
                "hash": content_hash,
                "page_count": len(pages)
            }],
            is_processed=False,
            processing_notes=None,
            local_path=None,
            cloud_path=None,
            is_synced=False,
            page_count=len(pages),
            pages=[],  # Would store paths after saving
            has_ocr=False,
            ocr_text=None,
            document_type=document_type,
            language_detected=None,
            confidence_score=None
        )

        self.captures[capture_id] = scan
        self._add_to_active_session(device_id, capture_id)

        return scan

    def capture_location(
        self,
        user_id: str,
        device_id: str,
        latitude: float,
        longitude: float,
        accuracy_meters: float,
        source: str = "gps",
        altitude_meters: Optional[float] = None,
        altitude_accuracy: Optional[float] = None,
        heading: Optional[float] = None,
        speed: Optional[float] = None,
        address: Optional[str] = None,
        place_name: Optional[str] = None
    ) -> LocationCapture:
        """Capture a standalone location."""
        location = LocationCapture(
            latitude=latitude,
            longitude=longitude,
            accuracy_meters=accuracy_meters,
            altitude_meters=altitude_meters,
            altitude_accuracy=altitude_accuracy,
            heading=heading,
            speed=speed,
            timestamp=datetime.datetime.now().isoformat(),
            source=source,
            address=address,
            place_name=place_name
        )

        return location

    def add_to_chain_of_custody(
        self,
        capture_id: str,
        action: str,
        performed_by: str,
        notes: Optional[str] = None
    ) -> bool:
        """Add an entry to the chain of custody."""
        if capture_id not in self.captures:
            return False

        capture = self.captures[capture_id]
        capture.chain_of_custody.append({
            "action": action,
            "timestamp": datetime.datetime.now().isoformat(),
            "performed_by": performed_by,
            "notes": notes,
            "hash": capture.content_hash  # Verify integrity
        })

        return True

    def verify_integrity(self, capture_id: str, file_data: bytes) -> Dict[str, Any]:
        """Verify the integrity of captured evidence."""
        if capture_id not in self.captures:
            return {"valid": False, "error": "Capture not found"}

        capture = self.captures[capture_id]
        current_hash = hashlib.sha256(file_data).hexdigest()

        return {
            "valid": current_hash == capture.content_hash,
            "original_hash": capture.content_hash,
            "current_hash": current_hash,
            "is_original": capture.is_original,
            "chain_of_custody_count": len(capture.chain_of_custody)
        }

    def mark_synced(
        self,
        capture_id: str,
        cloud_path: str
    ) -> bool:
        """Mark a capture as synced to cloud."""
        if capture_id not in self.captures:
            return False

        capture = self.captures[capture_id]
        capture.is_synced = True
        capture.cloud_path = cloud_path

        self.add_to_chain_of_custody(
            capture_id,
            "synced_to_cloud",
            "system",
            f"Uploaded to {cloud_path}"
        )

        return True

    def get_case_captures(
        self,
        case_id: str,
        capture_type: Optional[CaptureType] = None
    ) -> List[MediaCapture]:
        """Get all captures for a case."""
        captures = [
            c for c in self.captures.values()
            if c.case_id == case_id
        ]

        if capture_type:
            captures = [c for c in captures if c.capture_type == capture_type]

        return sorted(captures, key=lambda c: c.captured_at, reverse=True)

    def get_capture_statistics(
        self,
        user_id: Optional[str] = None,
        case_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get capture statistics."""
        captures = list(self.captures.values())

        if user_id:
            captures = [c for c in captures if c.user_id == user_id]
        if case_id:
            captures = [c for c in captures if c.case_id == case_id]

        by_type = {}
        total_size = 0
        synced_count = 0

        for capture in captures:
            ctype = capture.capture_type.value
            by_type[ctype] = by_type.get(ctype, 0) + 1
            total_size += capture.file_size_bytes
            if capture.is_synced:
                synced_count += 1

        return {
            "total_captures": len(captures),
            "by_type": by_type,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "synced_count": synced_count,
            "pending_sync": len(captures) - synced_count,
            "active_sessions": len(self.active_sessions)
        }

    def _generate_capture_id(self, prefix: str, user_id: str) -> str:
        """Generate a unique capture ID."""
        return hashlib.md5(
            f"{prefix}-{user_id}-{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

    def _add_to_active_session(self, device_id: str, capture_id: str):
        """Add capture to active session if exists."""
        if device_id in self.active_sessions:
            session_id = self.active_sessions[device_id]
            if session_id in self.sessions:
                self.sessions[session_id].captures.append(capture_id)

    def _get_extension(self, mime_type: str) -> str:
        """Get file extension from MIME type."""
        extensions = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/heic": "heic",
            "image/webp": "webp",
            "video/mp4": "mp4",
            "video/webm": "webm",
            "video/quicktime": "mov",
            "audio/mp3": "mp3",
            "audio/wav": "wav",
            "audio/ogg": "ogg",
            "audio/m4a": "m4a",
            "audio/aac": "aac"
        }
        return extensions.get(mime_type, "bin")

    def _get_codec_from_mime(self, mime_type: str) -> str:
        """Get audio codec from MIME type."""
        codecs = {
            "audio/mp3": "mp3",
            "audio/wav": "pcm",
            "audio/ogg": "vorbis",
            "audio/m4a": "aac",
            "audio/aac": "aac"
        }
        return codecs.get(mime_type, "unknown")

    def _get_video_codec_from_mime(self, mime_type: str) -> str:
        """Get video codec from MIME type."""
        codecs = {
            "video/mp4": "h264",
            "video/webm": "vp9",
            "video/quicktime": "h264"
        }
        return codecs.get(mime_type, "unknown")
