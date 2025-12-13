"""
Image Analysis Module for SafeChild

Provides face detection, image categorization, and safety features.
All tools are free and open-source (face_recognition, YOLO, Tesseract, imagehash).
"""

import os
import io
import logging
import hashlib
import tempfile
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class ImageCategory(Enum):
    """Image categories for classification"""
    SCREENSHOT = "screenshot"
    PHOTO = "photo"
    DOCUMENT = "document"
    CHAT = "chat"
    SELFIE = "selfie"
    GROUP_PHOTO = "group_photo"
    LANDSCAPE = "landscape"
    INDOOR = "indoor"
    OUTDOOR = "outdoor"
    UNKNOWN = "unknown"


class SafetyLevel(Enum):
    """Safety level for images"""
    SAFE = "safe"
    QUESTIONABLE = "questionable"
    UNSAFE = "unsafe"
    BLOCKED = "blocked"


@dataclass
class FaceLocation:
    """Face bounding box location"""
    top: int
    right: int
    bottom: int
    left: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    @property
    def area(self) -> int:
        return self.width * self.height

    def to_dict(self) -> Dict[str, int]:
        return {
            "top": self.top,
            "right": self.right,
            "bottom": self.bottom,
            "left": self.left,
            "width": self.width,
            "height": self.height
        }


@dataclass
class DetectedFace:
    """Detected face with encoding and metadata"""
    id: str
    location: FaceLocation
    encoding: Optional[List[float]] = None
    confidence: float = 0.0
    estimated_age: Optional[str] = None  # "child", "teen", "adult", "senior"
    cluster_id: Optional[str] = None  # For grouping same person

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "location": self.location.to_dict(),
            "confidence": self.confidence,
            "estimatedAge": self.estimated_age,
            "clusterId": self.cluster_id
        }


@dataclass
class ImageAnalysisResult:
    """Complete analysis result for an image"""
    id: str
    case_id: str
    file_name: str
    file_hash: str
    width: int
    height: int
    format: str

    # Face detection
    faces: List[DetectedFace] = field(default_factory=list)
    face_count: int = 0

    # Categorization
    category: ImageCategory = ImageCategory.UNKNOWN
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.0

    # OCR
    extracted_text: str = ""
    text_language: str = ""

    # Safety
    safety_level: SafetyLevel = SafetyLevel.SAFE
    safety_flags: List[str] = field(default_factory=list)
    is_blurred: bool = False

    # Perceptual hash (for duplicate detection)
    phash: str = ""

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    processing_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "caseId": self.case_id,
            "fileName": self.file_name,
            "fileHash": self.file_hash,
            "width": self.width,
            "height": self.height,
            "format": self.format,
            "faces": [f.to_dict() for f in self.faces],
            "faceCount": self.face_count,
            "category": self.category.value,
            "tags": self.tags,
            "confidence": self.confidence,
            "extractedText": self.extracted_text,
            "textLanguage": self.text_language,
            "safetyLevel": self.safety_level.value,
            "safetyFlags": self.safety_flags,
            "isBlurred": self.is_blurred,
            "phash": self.phash,
            "createdAt": self.created_at.isoformat(),
            "processingTime": self.processing_time
        }


class FaceDetector:
    """
    Face detection using face_recognition library (dlib-based).
    Free and open-source, runs locally.
    """

    def __init__(self):
        self._fr = None
        self._load_library()

    def _load_library(self):
        """Load face_recognition library"""
        try:
            import face_recognition
            self._fr = face_recognition
            logger.info("face_recognition library loaded")
        except ImportError:
            logger.warning(
                "face_recognition not installed. "
                "Install with: pip install face_recognition"
            )

    def detect_faces(
        self,
        image_data: bytes,
        get_encodings: bool = True
    ) -> List[DetectedFace]:
        """
        Detect faces in image.

        Args:
            image_data: Image bytes
            get_encodings: Whether to extract face encodings (slower but needed for matching)

        Returns:
            List of DetectedFace objects
        """
        if self._fr is None:
            return self._fallback_detect(image_data)

        try:
            import numpy as np
            from PIL import Image

            # Load image
            img = Image.open(io.BytesIO(image_data))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img_array = np.array(img)

            # Detect face locations
            face_locations = self._fr.face_locations(img_array, model="hog")

            # Get encodings if requested
            face_encodings = []
            if get_encodings and face_locations:
                face_encodings = self._fr.face_encodings(img_array, face_locations)

            # Build results
            faces = []
            for i, (top, right, bottom, left) in enumerate(face_locations):
                face_id = f"face_{hashlib.md5(f'{top}{right}{bottom}{left}'.encode()).hexdigest()[:8]}"

                face = DetectedFace(
                    id=face_id,
                    location=FaceLocation(top=top, right=right, bottom=bottom, left=left),
                    encoding=list(face_encodings[i]) if i < len(face_encodings) else None,
                    confidence=0.95  # face_recognition doesn't give confidence
                )

                # Estimate age based on face size ratio
                face.estimated_age = self._estimate_age_category(
                    face.location, img.width, img.height
                )

                faces.append(face)

            return faces

        except Exception as e:
            logger.error(f"Face detection error: {e}")
            return []

    def _estimate_age_category(
        self,
        location: FaceLocation,
        img_width: int,
        img_height: int
    ) -> str:
        """
        Simple heuristic for age estimation based on face proportions.
        NOTE: This is NOT accurate - use proper age estimation model for real use.
        """
        face_ratio = location.area / (img_width * img_height)
        aspect_ratio = location.width / location.height if location.height > 0 else 1

        # Children tend to have rounder faces
        if aspect_ratio > 0.9 and face_ratio > 0.1:
            return "child"
        elif face_ratio > 0.05:
            return "adult"
        else:
            return "unknown"

    def _fallback_detect(self, image_data: bytes) -> List[DetectedFace]:
        """Fallback when face_recognition is not available"""
        logger.warning("Face detection not available (library not installed)")
        return []

    def match_faces(
        self,
        face1_encoding: List[float],
        face2_encoding: List[float],
        tolerance: float = 0.6
    ) -> bool:
        """Check if two face encodings belong to the same person"""
        if self._fr is None or not face1_encoding or not face2_encoding:
            return False

        import numpy as np
        distance = np.linalg.norm(
            np.array(face1_encoding) - np.array(face2_encoding)
        )
        return distance < tolerance

    def cluster_faces(
        self,
        faces: List[DetectedFace],
        tolerance: float = 0.6
    ) -> Dict[str, List[str]]:
        """
        Group faces by person (same-person matching).

        Returns:
            Dict mapping cluster_id to list of face_ids
        """
        if self._fr is None or not faces:
            return {}

        import numpy as np

        # Get faces with encodings
        faces_with_enc = [f for f in faces if f.encoding]
        if not faces_with_enc:
            return {}

        encodings = [np.array(f.encoding) for f in faces_with_enc]

        # Simple clustering: assign each face to first matching cluster
        clusters = defaultdict(list)
        cluster_reps = []  # Representative encoding for each cluster

        for i, face in enumerate(faces_with_enc):
            assigned = False
            for cluster_id, rep_encoding in enumerate(cluster_reps):
                distance = np.linalg.norm(encodings[i] - rep_encoding)
                if distance < tolerance:
                    clusters[f"person_{cluster_id}"].append(face.id)
                    face.cluster_id = f"person_{cluster_id}"
                    assigned = True
                    break

            if not assigned:
                # New cluster
                cluster_id = len(cluster_reps)
                cluster_reps.append(encodings[i])
                clusters[f"person_{cluster_id}"].append(face.id)
                face.cluster_id = f"person_{cluster_id}"

        return dict(clusters)


class ImageCategorizer:
    """
    Image categorization using various techniques.
    Uses heuristics and optional CLIP model.
    """

    # Screenshot detection patterns
    SCREENSHOT_INDICATORS = {
        "aspect_ratios": [(9, 16), (9, 19.5), (9, 20), (3, 4)],  # Mobile ratios
        "status_bar_height_ratio": 0.03,  # Top 3% typically has status bar
    }

    def __init__(self):
        self._clip_model = None
        self._yolo_model = None
        self._load_models()

    def _load_models(self):
        """Load optional ML models"""
        # CLIP for scene classification
        try:
            import clip
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._clip_model, self._clip_preprocess = clip.load("ViT-B/32", device=device)
            self._clip_device = device
            logger.info("CLIP model loaded")
        except ImportError:
            logger.info("CLIP not installed - using heuristic classification")

        # YOLO for object detection
        try:
            from ultralytics import YOLO
            self._yolo_model = YOLO('yolov8n.pt')  # Nano model (smallest, fastest)
            logger.info("YOLO model loaded")
        except ImportError:
            logger.info("YOLO not installed - skipping object detection")

    def categorize(
        self,
        image_data: bytes,
        faces: List[DetectedFace]
    ) -> Tuple[ImageCategory, List[str], float]:
        """
        Categorize image and extract tags.

        Returns:
            Tuple of (category, tags, confidence)
        """
        from PIL import Image

        img = Image.open(io.BytesIO(image_data))
        width, height = img.size

        tags = []
        confidence = 0.5

        # Check if screenshot
        if self._is_screenshot(img):
            return ImageCategory.SCREENSHOT, ["screenshot", "mobile"], 0.9

        # Check face count
        face_count = len(faces)
        if face_count == 1:
            # Check if selfie (face is large and centered)
            face = faces[0]
            if self._is_selfie(face, width, height):
                return ImageCategory.SELFIE, ["selfie", "person", "portrait"], 0.8
            tags.append("portrait")
        elif face_count > 1:
            tags.append("group")
            if face_count > 4:
                return ImageCategory.GROUP_PHOTO, ["group", "multiple_people"], 0.8

        # Use YOLO for object detection
        if self._yolo_model:
            yolo_tags = self._detect_objects(image_data)
            tags.extend(yolo_tags)

            # Classify based on detected objects
            if "person" in yolo_tags or face_count > 0:
                if "outdoor" in " ".join(yolo_tags).lower():
                    tags.append("outdoor")
                    return ImageCategory.OUTDOOR, tags, 0.7
                else:
                    return ImageCategory.INDOOR if face_count > 0 else ImageCategory.PHOTO, tags, 0.6

        # Use CLIP for scene classification
        if self._clip_model:
            category, clip_confidence = self._classify_with_clip(img)
            return category, tags, clip_confidence

        # Default based on faces
        if face_count > 0:
            return ImageCategory.PHOTO, tags, 0.5

        return ImageCategory.UNKNOWN, tags, 0.3

    def _is_screenshot(self, img) -> bool:
        """Detect if image is a screenshot"""
        width, height = img.size

        # Check aspect ratio
        ratio = width / height
        for w, h in self.SCREENSHOT_INDICATORS["aspect_ratios"]:
            expected = w / h
            if abs(ratio - expected) < 0.05:
                return True

        # Check for status bar (uniform color strip at top)
        try:
            import numpy as np
            img_array = np.array(img)

            # Get top 3% of image
            status_bar_height = int(height * 0.03)
            top_strip = img_array[:status_bar_height, :, :]

            # Check if colors are very uniform (status bar characteristic)
            color_std = np.std(top_strip)
            if color_std < 20:  # Low variance = uniform color
                return True
        except:
            pass

        return False

    def _is_selfie(self, face: DetectedFace, img_width: int, img_height: int) -> bool:
        """Check if the image is likely a selfie"""
        loc = face.location

        # Face should be large (>15% of image)
        face_ratio = loc.area / (img_width * img_height)
        if face_ratio < 0.15:
            return False

        # Face should be roughly centered
        face_center_x = (loc.left + loc.right) / 2
        face_center_y = (loc.top + loc.bottom) / 2

        img_center_x = img_width / 2
        img_center_y = img_height / 2

        x_offset = abs(face_center_x - img_center_x) / img_width
        y_offset = abs(face_center_y - img_center_y) / img_height

        return x_offset < 0.25 and y_offset < 0.35

    def _detect_objects(self, image_data: bytes) -> List[str]:
        """Detect objects using YOLO"""
        if not self._yolo_model:
            return []

        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                f.write(image_data)
                temp_path = f.name

            results = self._yolo_model(temp_path, verbose=False)
            os.unlink(temp_path)

            tags = set()
            for result in results:
                for box in result.boxes:
                    class_name = result.names[int(box.cls)]
                    tags.add(class_name.lower())

            return list(tags)
        except Exception as e:
            logger.warning(f"YOLO detection error: {e}")
            return []

    def _classify_with_clip(self, img) -> Tuple[ImageCategory, float]:
        """Classify image using CLIP"""
        if not self._clip_model:
            return ImageCategory.UNKNOWN, 0.3

        try:
            import torch
            import clip

            # Category descriptions
            categories = {
                ImageCategory.SELFIE: "a selfie photo of a person",
                ImageCategory.GROUP_PHOTO: "a group photo with multiple people",
                ImageCategory.LANDSCAPE: "a landscape or nature photo",
                ImageCategory.INDOOR: "an indoor photo",
                ImageCategory.OUTDOOR: "an outdoor photo",
                ImageCategory.DOCUMENT: "a document or text image",
                ImageCategory.CHAT: "a chat or messaging screenshot",
                ImageCategory.SCREENSHOT: "a mobile phone screenshot",
            }

            # Preprocess image
            image = self._clip_preprocess(img).unsqueeze(0).to(self._clip_device)

            # Encode text prompts
            text = clip.tokenize(list(categories.values())).to(self._clip_device)

            with torch.no_grad():
                logits_per_image, _ = self._clip_model(image, text)
                probs = logits_per_image.softmax(dim=-1).cpu().numpy()[0]

            # Get best match
            best_idx = probs.argmax()
            best_category = list(categories.keys())[best_idx]
            confidence = float(probs[best_idx])

            return best_category, confidence

        except Exception as e:
            logger.warning(f"CLIP classification error: {e}")
            return ImageCategory.UNKNOWN, 0.3


class OCRExtractor:
    """
    Text extraction from images using Tesseract OCR.
    Free and open-source.
    """

    def __init__(self):
        self._tesseract_available = False
        self._check_tesseract()

    def _check_tesseract(self):
        """Check if Tesseract is available"""
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            self._tesseract_available = True
            logger.info("Tesseract OCR available")
        except:
            logger.info("Tesseract not installed - OCR disabled")

    def extract_text(
        self,
        image_data: bytes,
        language: str = "tur+eng"  # Turkish + English
    ) -> Tuple[str, str]:
        """
        Extract text from image.

        Args:
            image_data: Image bytes
            language: Tesseract language code

        Returns:
            Tuple of (extracted_text, detected_language)
        """
        if not self._tesseract_available:
            return "", ""

        try:
            import pytesseract
            from PIL import Image

            img = Image.open(io.BytesIO(image_data))

            # Extract text with Turkish and English
            text = pytesseract.image_to_string(img, lang=language)
            text = text.strip()

            # Detect language heuristically
            detected_lang = self._detect_language(text)

            return text, detected_lang

        except Exception as e:
            logger.warning(f"OCR extraction error: {e}")
            return "", ""

    def _detect_language(self, text: str) -> str:
        """Simple language detection based on character sets"""
        if not text:
            return ""

        # Turkish-specific characters
        turkish_chars = set("şŞğĞüÜöÖçÇıİ")

        # Arabic script (for Kurdish Sorani)
        arabic_chars = set("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")

        text_chars = set(text)

        if text_chars & turkish_chars:
            return "tr"
        elif text_chars & arabic_chars:
            return "ar"
        else:
            return "en"


class SafetyChecker:
    """
    Safety checking for images.
    Uses perceptual hashing and optional NSFW detection.
    """

    def __init__(self):
        self._imagehash = None
        self._nsfw_model = None
        self._load_libraries()

        # Known bad hash database (placeholder - in production, use real database)
        self._blocked_hashes: Set[str] = set()

    def _load_libraries(self):
        """Load required libraries"""
        try:
            import imagehash
            self._imagehash = imagehash
            logger.info("imagehash library loaded")
        except ImportError:
            logger.info("imagehash not installed - duplicate detection disabled")

    def compute_phash(self, image_data: bytes) -> str:
        """Compute perceptual hash of image"""
        if not self._imagehash:
            return ""

        try:
            from PIL import Image
            img = Image.open(io.BytesIO(image_data))
            return str(self._imagehash.phash(img))
        except Exception as e:
            logger.warning(f"Hash computation error: {e}")
            return ""

    def check_safety(
        self,
        image_data: bytes,
        phash: str = ""
    ) -> Tuple[SafetyLevel, List[str]]:
        """
        Check image safety.

        Returns:
            Tuple of (safety_level, flags)
        """
        flags = []

        # Check against blocked hashes
        if phash and phash in self._blocked_hashes:
            return SafetyLevel.BLOCKED, ["blocked_hash"]

        # Compute hash if not provided
        if not phash:
            phash = self.compute_phash(image_data)

        # Check hash similarity to blocked content
        if self._imagehash and phash:
            for blocked_hash in self._blocked_hashes:
                similarity = self._hash_similarity(phash, blocked_hash)
                if similarity > 0.9:
                    flags.append("similar_to_blocked")
                    return SafetyLevel.BLOCKED, flags

        # Default to safe
        return SafetyLevel.SAFE, flags

    def _hash_similarity(self, hash1: str, hash2: str) -> float:
        """Compute similarity between two hashes"""
        if not self._imagehash or not hash1 or not hash2:
            return 0.0

        try:
            h1 = self._imagehash.hex_to_hash(hash1)
            h2 = self._imagehash.hex_to_hash(hash2)

            # Hamming distance
            distance = h1 - h2
            max_distance = 64  # 64-bit hash

            return 1 - (distance / max_distance)
        except:
            return 0.0

    def find_duplicates(
        self,
        images: List[Tuple[str, str]],  # List of (image_id, phash)
        threshold: float = 0.9
    ) -> Dict[str, List[str]]:
        """
        Find duplicate/similar images.

        Returns:
            Dict mapping image_id to list of similar image_ids
        """
        if not self._imagehash:
            return {}

        duplicates = defaultdict(list)

        for i, (id1, hash1) in enumerate(images):
            for j, (id2, hash2) in enumerate(images[i + 1:], i + 1):
                similarity = self._hash_similarity(hash1, hash2)
                if similarity >= threshold:
                    duplicates[id1].append(id2)
                    duplicates[id2].append(id1)

        return dict(duplicates)


class ImageAnalysisEngine:
    """
    Main image analysis engine combining all components.
    """

    def __init__(self):
        self.face_detector = FaceDetector()
        self.categorizer = ImageCategorizer()
        self.ocr = OCRExtractor()
        self.safety = SafetyChecker()

    def analyze(
        self,
        image_data: bytes,
        file_name: str,
        case_id: str,
        extract_text: bool = True,
        detect_faces: bool = True,
        check_safety: bool = True
    ) -> ImageAnalysisResult:
        """
        Perform complete image analysis.

        Args:
            image_data: Image bytes
            file_name: Original filename
            case_id: Associated case ID
            extract_text: Whether to run OCR
            detect_faces: Whether to detect faces
            check_safety: Whether to check safety

        Returns:
            ImageAnalysisResult with all analysis data
        """
        import time
        from PIL import Image

        start_time = time.time()

        # Get image info
        img = Image.open(io.BytesIO(image_data))
        width, height = img.size
        img_format = img.format or "UNKNOWN"

        # Compute hashes
        file_hash = hashlib.sha256(image_data).hexdigest()
        result_id = f"img_{case_id}_{file_hash[:8]}"

        # Detect faces
        faces = []
        if detect_faces:
            faces = self.face_detector.detect_faces(image_data)

        # Cluster faces
        if faces:
            self.face_detector.cluster_faces(faces)

        # Categorize
        category, tags, confidence = self.categorizer.categorize(image_data, faces)

        # Extract text
        extracted_text = ""
        text_language = ""
        if extract_text:
            extracted_text, text_language = self.ocr.extract_text(image_data)

        # Safety check
        phash = self.safety.compute_phash(image_data)
        safety_level = SafetyLevel.SAFE
        safety_flags = []
        if check_safety:
            safety_level, safety_flags = self.safety.check_safety(image_data, phash)

        processing_time = time.time() - start_time

        return ImageAnalysisResult(
            id=result_id,
            case_id=case_id,
            file_name=file_name,
            file_hash=file_hash,
            width=width,
            height=height,
            format=img_format,
            faces=faces,
            face_count=len(faces),
            category=category,
            tags=tags,
            confidence=confidence,
            extracted_text=extracted_text,
            text_language=text_language,
            safety_level=safety_level,
            safety_flags=safety_flags,
            is_blurred=False,
            phash=phash,
            processing_time=processing_time
        )

    def batch_analyze(
        self,
        images: List[Tuple[bytes, str]],  # List of (data, filename)
        case_id: str
    ) -> List[ImageAnalysisResult]:
        """Analyze multiple images"""
        results = []

        for image_data, file_name in images:
            try:
                result = self.analyze(
                    image_data=image_data,
                    file_name=file_name,
                    case_id=case_id
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to analyze {file_name}: {e}")

        return results

    def get_face_clusters(
        self,
        results: List[ImageAnalysisResult]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get face clusters across multiple images.

        Returns:
            Dict mapping cluster_id to list of {imageId, faceId, location}
        """
        # Collect all faces
        all_faces = []
        for result in results:
            for face in result.faces:
                all_faces.append((face, result.id, result.file_name))

        # Cluster faces
        if all_faces:
            faces_only = [f[0] for f in all_faces]
            self.face_detector.cluster_faces(faces_only)

        # Build cluster mapping
        clusters = defaultdict(list)
        for face, img_id, file_name in all_faces:
            if face.cluster_id:
                clusters[face.cluster_id].append({
                    "imageId": img_id,
                    "fileName": file_name,
                    "faceId": face.id,
                    "location": face.location.to_dict()
                })

        return dict(clusters)
