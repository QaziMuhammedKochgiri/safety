"""
Language Detector
Automatic language detection for evidence text.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import re
from collections import Counter


class LanguageCode(str, Enum):
    """Supported language codes."""
    ENGLISH = "en"
    GERMAN = "de"
    TURKISH = "tr"
    ARABIC = "ar"
    PERSIAN = "fa"
    KURDISH_KURMANJI = "kmr"
    KURDISH_SORANI = "ckb"
    FRENCH = "fr"
    SPANISH = "es"
    ITALIAN = "it"
    DUTCH = "nl"
    RUSSIAN = "ru"
    HINDI = "hi"
    URDU = "ur"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    PORTUGUESE = "pt"
    UNKNOWN = "unknown"


class ScriptType(str, Enum):
    """Writing script types."""
    LATIN = "latin"
    ARABIC = "arabic"
    CYRILLIC = "cyrillic"
    DEVANAGARI = "devanagari"
    CJK = "cjk"  # Chinese, Japanese, Korean
    KOREAN = "korean"  # Hangul specifically
    MIXED = "mixed"
    UNKNOWN = "unknown"


@dataclass
class DetectionResult:
    """Result of language detection."""
    primary_language: LanguageCode
    confidence: float
    script_type: ScriptType
    secondary_languages: List[Tuple[LanguageCode, float]]
    is_multilingual: bool
    code_switching_detected: bool
    word_count: int
    character_count: int
    detected_patterns: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


# Language-specific character patterns
SCRIPT_RANGES = {
    ScriptType.ARABIC: r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]',
    ScriptType.CYRILLIC: r'[\u0400-\u04FF\u0500-\u052F]',
    ScriptType.DEVANAGARI: r'[\u0900-\u097F]',
    ScriptType.CJK: r'[\u4E00-\u9FFF\u3400-\u4DBF]',
    ScriptType.KOREAN: r'[\uAC00-\uD7AF\u1100-\u11FF]',
    ScriptType.LATIN: r'[A-Za-z\u00C0-\u024F]'
}

# Language-specific stopwords and common words
LANGUAGE_MARKERS: Dict[LanguageCode, Dict[str, Any]] = {
    LanguageCode.ENGLISH: {
        "stopwords": ["the", "is", "are", "was", "were", "be", "been", "being",
                      "have", "has", "had", "do", "does", "did", "will", "would",
                      "could", "should", "may", "might", "must", "shall", "can",
                      "a", "an", "and", "or", "but", "if", "then", "because",
                      "as", "of", "at", "by", "for", "with", "about", "to", "from"],
        "patterns": [r"\b(the|this|that|these|those)\b", r"\b(don't|won't|can't|isn't)\b"],
        "script": ScriptType.LATIN
    },
    LanguageCode.GERMAN: {
        "stopwords": ["der", "die", "das", "ein", "eine", "und", "oder", "aber",
                      "ist", "sind", "war", "waren", "haben", "hat", "hatte",
                      "werden", "wird", "wurde", "können", "kann", "konnte",
                      "nicht", "auch", "nur", "noch", "schon", "immer", "sehr",
                      "ich", "du", "er", "sie", "es", "wir", "ihr", "Sie"],
        "patterns": [r"\b(sch|ch|ck|tz|ei|ie|au|eu|äu)\w*\b", r"\b\w+ung\b", r"\b\w+heit\b"],
        "script": ScriptType.LATIN
    },
    LanguageCode.TURKISH: {
        "stopwords": ["bir", "bu", "ve", "de", "da", "ile", "için", "gibi",
                      "olan", "olarak", "daha", "en", "çok", "kadar", "sonra",
                      "önce", "ancak", "ama", "fakat", "yani", "şey", "var",
                      "yok", "ne", "nasıl", "neden", "nerede", "kim", "ben",
                      "sen", "o", "biz", "siz", "onlar", "bana", "sana", "ona"],
        "patterns": [r"\b\w+[ıiuü]yor\w*\b", r"\b\w+[ae]cak\b", r"\b\w+[dt][ıiuü]k?\b", r"[şçğüöıİ]"],
        "script": ScriptType.LATIN
    },
    LanguageCode.ARABIC: {
        "stopwords": ["في", "من", "على", "إلى", "عن", "مع", "هذا", "هذه",
                      "ذلك", "تلك", "الذي", "التي", "كان", "كانت", "يكون",
                      "أن", "لأن", "إذا", "ثم", "لكن", "أو", "و", "هو", "هي"],
        "patterns": [r"ال\w+", r"\w+ة\b"],
        "script": ScriptType.ARABIC
    },
    LanguageCode.PERSIAN: {
        "stopwords": ["در", "به", "از", "که", "را", "با", "این", "آن",
                      "برای", "تا", "است", "بود", "شد", "می", "هم",
                      "و", "یا", "اما", "چون", "اگر", "پس"],
        "patterns": [r"می\s*\w+", r"\w+ها\b"],
        "script": ScriptType.ARABIC
    },
    LanguageCode.KURDISH_KURMANJI: {
        "stopwords": ["di", "de", "ji", "bi", "li", "ku", "ev", "ew",
                      "em", "hûn", "ew", "min", "te", "wî", "wê",
                      "û", "an", "lê", "belê", "na", "ne", "her"],
        "patterns": [r"\bx[we]\w*\b", r"\b\w+kirin\b"],
        "script": ScriptType.LATIN
    },
    LanguageCode.KURDISH_SORANI: {
        "stopwords": ["له", "بۆ", "له‌گه‌ڵ", "ئه‌م", "ئه‌و", "که", "چونکه",
                      "ئه‌گه‌ر", "بۆیه", "هه‌روه‌ها", "یان", "به‌ڵام"],
        "patterns": [r"ئ\w+", r"\w+ەوە\b"],
        "script": ScriptType.ARABIC
    },
    LanguageCode.FRENCH: {
        "stopwords": ["le", "la", "les", "un", "une", "des", "et", "ou",
                      "mais", "donc", "car", "ni", "que", "qui", "quoi",
                      "est", "sont", "était", "étaient", "avoir", "être",
                      "je", "tu", "il", "elle", "nous", "vous", "ils", "elles"],
        "patterns": [r"\b(qu'|l'|d'|n'|c'|j'|m'|t'|s')\w+", r"\b\w+tion\b", r"[éèêëàâäùûüôöïî]"],
        "script": ScriptType.LATIN
    },
    LanguageCode.SPANISH: {
        "stopwords": ["el", "la", "los", "las", "un", "una", "unos", "unas",
                      "y", "o", "pero", "porque", "como", "si", "cuando",
                      "es", "son", "era", "eran", "ser", "estar", "tener",
                      "yo", "tú", "él", "ella", "nosotros", "vosotros", "ellos"],
        "patterns": [r"\b\w+ción\b", r"\b\w+mente\b", r"[ñáéíóú¿¡]"],
        "script": ScriptType.LATIN
    },
    LanguageCode.RUSSIAN: {
        "stopwords": ["и", "в", "не", "на", "я", "что", "он", "с", "как",
                      "это", "а", "она", "по", "но", "они", "мы", "к",
                      "у", "же", "его", "её", "для", "от", "до"],
        "patterns": [r"[а-яА-ЯёЁ]+"],
        "script": ScriptType.CYRILLIC
    }
}


class LanguageDetector:
    """Automatic language detection for text."""

    def __init__(self):
        self.min_confidence = 0.3
        self.min_words = 3

    def detect(self, text: str) -> DetectionResult:
        """Detect language of text."""
        if not text or len(text.strip()) < 3:
            return DetectionResult(
                primary_language=LanguageCode.UNKNOWN,
                confidence=0.0,
                script_type=ScriptType.UNKNOWN,
                secondary_languages=[],
                is_multilingual=False,
                code_switching_detected=False,
                word_count=0,
                character_count=0,
                detected_patterns=[]
            )

        # Detect script first
        script_type = self._detect_script(text)

        # Get candidate languages based on script
        candidates = self._get_script_languages(script_type)

        # Score each candidate language
        scores: Dict[LanguageCode, float] = {}
        patterns_found: Dict[LanguageCode, List[str]] = {}

        for lang in candidates:
            score, patterns = self._score_language(text, lang)
            scores[lang] = score
            patterns_found[lang] = patterns

        # Sort by score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        if not sorted_scores or sorted_scores[0][1] < self.min_confidence:
            primary = LanguageCode.UNKNOWN
            confidence = 0.0
        else:
            primary = sorted_scores[0][0]
            confidence = sorted_scores[0][1]

        # Check for multilingual/code-switching
        secondary = [(lang, score) for lang, score in sorted_scores[1:] if score > 0.2]
        is_multilingual = len(secondary) > 0 and secondary[0][1] > 0.3
        code_switching = self._detect_code_switching(text, primary, secondary)

        # Count words and characters
        words = text.split()
        word_count = len(words)
        char_count = len(text)

        return DetectionResult(
            primary_language=primary,
            confidence=confidence,
            script_type=script_type,
            secondary_languages=secondary,
            is_multilingual=is_multilingual,
            code_switching_detected=code_switching,
            word_count=word_count,
            character_count=char_count,
            detected_patterns=patterns_found.get(primary, [])
        )

    def _detect_script(self, text: str) -> ScriptType:
        """Detect the primary script of text."""
        script_counts = {}

        for script, pattern in SCRIPT_RANGES.items():
            count = len(re.findall(pattern, text))
            if count > 0:
                script_counts[script] = count

        if not script_counts:
            return ScriptType.UNKNOWN

        # Check for mixed scripts
        total_chars = sum(script_counts.values())
        dominant = max(script_counts, key=script_counts.get)
        dominant_ratio = script_counts[dominant] / total_chars

        if dominant_ratio < 0.7 and len(script_counts) > 1:
            return ScriptType.MIXED

        return dominant

    def _get_script_languages(self, script: ScriptType) -> List[LanguageCode]:
        """Get candidate languages for a script type."""
        script_to_langs = {
            ScriptType.LATIN: [
                LanguageCode.ENGLISH, LanguageCode.GERMAN, LanguageCode.TURKISH,
                LanguageCode.FRENCH, LanguageCode.SPANISH, LanguageCode.ITALIAN,
                LanguageCode.DUTCH, LanguageCode.PORTUGUESE, LanguageCode.KURDISH_KURMANJI
            ],
            ScriptType.ARABIC: [
                LanguageCode.ARABIC, LanguageCode.PERSIAN, LanguageCode.URDU,
                LanguageCode.KURDISH_SORANI
            ],
            ScriptType.CYRILLIC: [LanguageCode.RUSSIAN],
            ScriptType.DEVANAGARI: [LanguageCode.HINDI],
            ScriptType.CJK: [LanguageCode.CHINESE, LanguageCode.JAPANESE],
            ScriptType.KOREAN: [LanguageCode.KOREAN],
            ScriptType.MIXED: list(LanguageCode),
            ScriptType.UNKNOWN: list(LanguageCode)
        }

        return script_to_langs.get(script, list(LanguageCode))

    def _score_language(
        self,
        text: str,
        language: LanguageCode
    ) -> Tuple[float, List[str]]:
        """Score text for a specific language."""
        markers = LANGUAGE_MARKERS.get(language)
        if not markers:
            return 0.0, []

        score = 0.0
        patterns_found = []
        text_lower = text.lower()
        words = text_lower.split()

        # Stopword matching
        stopwords = set(markers.get("stopwords", []))
        word_set = set(words)
        stopword_matches = len(word_set & stopwords)

        if len(words) > 0:
            stopword_ratio = stopword_matches / min(len(words), 50)
            score += stopword_ratio * 0.5

        # Pattern matching
        patterns = markers.get("patterns", [])
        for pattern in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                score += min(len(matches) * 0.1, 0.3)
                patterns_found.append(pattern)

        # Script matching
        expected_script = markers.get("script")
        detected_script = self._detect_script(text)
        if expected_script == detected_script:
            score += 0.2
        elif detected_script == ScriptType.MIXED:
            score += 0.1

        return min(score, 1.0), patterns_found

    def _detect_code_switching(
        self,
        text: str,
        primary: LanguageCode,
        secondary: List[Tuple[LanguageCode, float]]
    ) -> bool:
        """Detect code-switching between languages."""
        if not secondary:
            return False

        # Split into sentences or phrases
        segments = re.split(r'[.!?;,]', text)
        segment_languages = []

        for segment in segments:
            segment = segment.strip()
            if len(segment) < 5:
                continue

            result = self.detect(segment)
            if result.confidence > 0.4:
                segment_languages.append(result.primary_language)

        # Check if different languages appear in different segments
        unique_languages = set(segment_languages)
        return len(unique_languages) > 1

    def detect_batch(self, texts: List[str]) -> List[DetectionResult]:
        """Detect language for multiple texts."""
        return [self.detect(text) for text in texts]

    def get_language_name(
        self,
        code: LanguageCode,
        display_language: str = "en"
    ) -> str:
        """Get human-readable language name."""
        names = {
            LanguageCode.ENGLISH: {"en": "English", "de": "Englisch", "tr": "İngilizce"},
            LanguageCode.GERMAN: {"en": "German", "de": "Deutsch", "tr": "Almanca"},
            LanguageCode.TURKISH: {"en": "Turkish", "de": "Türkisch", "tr": "Türkçe"},
            LanguageCode.ARABIC: {"en": "Arabic", "de": "Arabisch", "tr": "Arapça"},
            LanguageCode.PERSIAN: {"en": "Persian", "de": "Persisch", "tr": "Farsça"},
            LanguageCode.KURDISH_KURMANJI: {"en": "Kurdish (Kurmanji)", "de": "Kurdisch (Kurmandschi)", "tr": "Kürtçe (Kurmancî)"},
            LanguageCode.KURDISH_SORANI: {"en": "Kurdish (Sorani)", "de": "Kurdisch (Sorani)", "tr": "Kürtçe (Soranî)"},
            LanguageCode.FRENCH: {"en": "French", "de": "Französisch", "tr": "Fransızca"},
            LanguageCode.SPANISH: {"en": "Spanish", "de": "Spanisch", "tr": "İspanyolca"},
            LanguageCode.RUSSIAN: {"en": "Russian", "de": "Russisch", "tr": "Rusça"},
            LanguageCode.UNKNOWN: {"en": "Unknown", "de": "Unbekannt", "tr": "Bilinmiyor"}
        }

        lang_names = names.get(code, {"en": code.value})
        return lang_names.get(display_language, lang_names.get("en", code.value))

    def get_statistics(self, results: List[DetectionResult]) -> Dict[str, Any]:
        """Get statistics from detection results."""
        if not results:
            return {"total": 0}

        language_counts = Counter(r.primary_language for r in results)
        script_counts = Counter(r.script_type for r in results)
        multilingual_count = sum(1 for r in results if r.is_multilingual)
        code_switch_count = sum(1 for r in results if r.code_switching_detected)
        avg_confidence = sum(r.confidence for r in results) / len(results)

        return {
            "total": len(results),
            "by_language": dict(language_counts),
            "by_script": dict(script_counts),
            "multilingual_count": multilingual_count,
            "code_switching_count": code_switch_count,
            "average_confidence": avg_confidence,
            "high_confidence_count": sum(1 for r in results if r.confidence > 0.7),
            "low_confidence_count": sum(1 for r in results if r.confidence < 0.4)
        }
