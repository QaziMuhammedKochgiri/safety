"""
Idiom Translator
Idiom and expression translation with cultural context.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class IdiomCategory(str, Enum):
    """Categories of idioms."""
    THREAT = "threat"
    ENDEARMENT = "endearment"
    DISCIPLINE = "discipline"
    FRUSTRATION = "frustration"
    ANGER = "anger"
    PROMISE = "promise"
    WARNING = "warning"
    AFFECTION = "affection"
    CURSE = "curse"
    BLESSING = "blessing"
    EXAGGERATION = "exaggeration"


@dataclass
class Idiom:
    """An idiom or cultural expression."""
    idiom_id: str
    original: str
    language: str
    literal_translation: str
    actual_meaning: str
    category: IdiomCategory
    severity_if_literal: float  # 0.0-1.0, how concerning if taken literally
    severity_cultural: float  # 0.0-1.0, actual severity in cultural context
    usage_context: str
    legal_note: str
    examples: List[str]
    regions: List[str]


@dataclass
class TranslationResult:
    """Result of idiom translation."""
    original_text: str
    detected_idioms: List[Idiom]
    literal_interpretation: str
    cultural_interpretation: str
    legal_considerations: List[str]
    severity_adjustment: float  # How much severity changes with cultural context
    confidence: float
    warnings: List[str]


# Comprehensive idiom database
IDIOM_DATABASE: List[Dict[str, Any]] = [
    # Turkish Idioms
    {
        "idiom_id": "tr_001",
        "original": "seni öldürürüm",
        "language": "tr",
        "literal_translation": "I will kill you",
        "actual_meaning": "I'm very angry with you (common expression of frustration)",
        "category": IdiomCategory.FRUSTRATION,
        "severity_if_literal": 1.0,
        "severity_cultural": 0.2,
        "usage_context": "Common expression when frustrated, especially with children or family",
        "legal_note": "This is an extremely common Turkish expression that does not indicate actual threat",
        "examples": ["Seni öldürürüm, neden söylemedın?", "Onu öldüreceğim, yine yapmış!"],
        "regions": ["turkey", "turkish_diaspora"]
    },
    {
        "idiom_id": "tr_002",
        "original": "kafanı kırarım",
        "language": "tr",
        "literal_translation": "I'll break your head",
        "actual_meaning": "Strong warning/frustration expression",
        "category": IdiomCategory.WARNING,
        "severity_if_literal": 0.9,
        "severity_cultural": 0.2,
        "usage_context": "Used when someone is being stubborn or not listening",
        "legal_note": "Common expression, does not indicate actual violence intent",
        "examples": ["Dinlemezsen kafanı kırarım!"],
        "regions": ["turkey"]
    },
    {
        "idiom_id": "tr_003",
        "original": "canım ciğerim",
        "language": "tr",
        "literal_translation": "My soul, my liver",
        "actual_meaning": "Term of deep affection/love",
        "category": IdiomCategory.ENDEARMENT,
        "severity_if_literal": 0.0,
        "severity_cultural": 0.0,
        "usage_context": "Used for children, loved ones",
        "legal_note": "Positive expression showing strong affection",
        "examples": ["Canım ciğerim benim, gel buraya"],
        "regions": ["turkey"]
    },
    {
        "idiom_id": "tr_004",
        "original": "gözümün nuru",
        "language": "tr",
        "literal_translation": "Light of my eyes",
        "actual_meaning": "Most precious person (usually child)",
        "category": IdiomCategory.ENDEARMENT,
        "severity_if_literal": 0.0,
        "severity_cultural": 0.0,
        "usage_context": "Deep affection expression",
        "legal_note": "Shows strong parental love",
        "examples": ["Gözümün nuru, iyi misin?"],
        "regions": ["turkey"]
    },
    {
        "idiom_id": "tr_005",
        "original": "dayak yiyeceksin",
        "language": "tr",
        "literal_translation": "You will eat beating",
        "actual_meaning": "You will be punished (not necessarily physical)",
        "category": IdiomCategory.DISCIPLINE,
        "severity_if_literal": 0.8,
        "severity_cultural": 0.3,
        "usage_context": "Warning to child about consequences",
        "legal_note": "Traditional expression, may or may not indicate physical discipline",
        "examples": ["Yapmazsan dayak yiyeceksin"],
        "regions": ["turkey"]
    },
    {
        "idiom_id": "tr_006",
        "original": "allah kahretsin",
        "language": "tr",
        "literal_translation": "May God damn it",
        "actual_meaning": "Expression of extreme frustration",
        "category": IdiomCategory.FRUSTRATION,
        "severity_if_literal": 0.5,
        "severity_cultural": 0.1,
        "usage_context": "General frustration, not directed at person",
        "legal_note": "Common exclamation, not a curse on someone",
        "examples": ["Allah kahretsin, yine bozulmuş!"],
        "regions": ["turkey"]
    },

    # Arabic Idioms
    {
        "idiom_id": "ar_001",
        "original": "سأقتلك",
        "language": "ar",
        "literal_translation": "I will kill you",
        "actual_meaning": "I'm very angry with you (common expression)",
        "category": IdiomCategory.FRUSTRATION,
        "severity_if_literal": 1.0,
        "severity_cultural": 0.2,
        "usage_context": "Common expression of anger/frustration",
        "legal_note": "Very common expression, not literal threat",
        "examples": [],
        "regions": ["middle_east", "north_africa"]
    },
    {
        "idiom_id": "ar_002",
        "original": "يا قرة عيني",
        "language": "ar",
        "literal_translation": "O coolness of my eyes",
        "actual_meaning": "My beloved (usually for children)",
        "category": IdiomCategory.ENDEARMENT,
        "severity_if_literal": 0.0,
        "severity_cultural": 0.0,
        "usage_context": "Deep affection for children/loved ones",
        "legal_note": "Positive expression of parental love",
        "examples": [],
        "regions": ["middle_east"]
    },
    {
        "idiom_id": "ar_003",
        "original": "روحي فداك",
        "language": "ar",
        "literal_translation": "My soul as ransom for you",
        "actual_meaning": "I love you deeply/I'd do anything for you",
        "category": IdiomCategory.AFFECTION,
        "severity_if_literal": 0.0,
        "severity_cultural": 0.0,
        "usage_context": "Expression of deep love and devotion",
        "legal_note": "Very positive expression",
        "examples": [],
        "regions": ["middle_east"]
    },

    # German Idioms
    {
        "idiom_id": "de_001",
        "original": "Ich bring dich um",
        "language": "de",
        "literal_translation": "I'll kill you",
        "actual_meaning": "I'm very angry (less common than Turkish/Arabic equivalent)",
        "category": IdiomCategory.ANGER,
        "severity_if_literal": 1.0,
        "severity_cultural": 0.5,
        "usage_context": "Expression of extreme anger (taken more seriously in German culture)",
        "legal_note": "More serious than in Middle Eastern cultures, but still may be expression",
        "examples": ["Wenn du das nochmal machst, bring ich dich um!"],
        "regions": ["germany", "austria", "switzerland"]
    },
    {
        "idiom_id": "de_002",
        "original": "Mein Schatz",
        "language": "de",
        "literal_translation": "My treasure",
        "actual_meaning": "Term of endearment",
        "category": IdiomCategory.ENDEARMENT,
        "severity_if_literal": 0.0,
        "severity_cultural": 0.0,
        "usage_context": "Common term for loved ones",
        "legal_note": "Positive expression",
        "examples": ["Mein Schatz, komm her"],
        "regions": ["germany", "austria", "switzerland"]
    },

    # Kurdish Idioms
    {
        "idiom_id": "kmr_001",
        "original": "ez te bikujim",
        "language": "kmr",
        "literal_translation": "I will kill you",
        "actual_meaning": "I'm very angry with you",
        "category": IdiomCategory.FRUSTRATION,
        "severity_if_literal": 1.0,
        "severity_cultural": 0.2,
        "usage_context": "Common Kurdish expression of frustration",
        "legal_note": "Similar to Turkish usage, not literal threat",
        "examples": [],
        "regions": ["kurdistan", "turkey", "iraq", "syria"]
    },
    {
        "idiom_id": "kmr_002",
        "original": "canê min",
        "language": "kmr",
        "literal_translation": "My soul",
        "actual_meaning": "My dear/darling",
        "category": IdiomCategory.ENDEARMENT,
        "severity_if_literal": 0.0,
        "severity_cultural": 0.0,
        "usage_context": "Term of endearment",
        "legal_note": "Positive expression of affection",
        "examples": ["Canê min, were vira"],
        "regions": ["kurdistan"]
    }
]


class IdiomTranslator:
    """Translates idioms with cultural context."""

    def __init__(self):
        self.idioms: Dict[str, Idiom] = {}
        self._load_idioms()

    def _load_idioms(self):
        """Load idiom database."""
        for data in IDIOM_DATABASE:
            idiom = Idiom(
                idiom_id=data["idiom_id"],
                original=data["original"],
                language=data["language"],
                literal_translation=data["literal_translation"],
                actual_meaning=data["actual_meaning"],
                category=data["category"],
                severity_if_literal=data["severity_if_literal"],
                severity_cultural=data["severity_cultural"],
                usage_context=data["usage_context"],
                legal_note=data["legal_note"],
                examples=data["examples"],
                regions=data["regions"]
            )
            self.idioms[idiom.idiom_id] = idiom

    def translate(
        self,
        text: str,
        source_language: str
    ) -> TranslationResult:
        """Translate text with idiom recognition."""
        text_lower = text.lower()
        detected_idioms: List[Idiom] = []
        literal_parts = []
        cultural_parts = []
        legal_considerations = []
        warnings = []

        # Search for idioms
        for idiom in self.idioms.values():
            if idiom.language != source_language:
                continue

            if idiom.original.lower() in text_lower:
                detected_idioms.append(idiom)
                literal_parts.append(idiom.literal_translation)
                cultural_parts.append(idiom.actual_meaning)
                legal_considerations.append(idiom.legal_note)

                # Add warning if severity differs significantly
                if idiom.severity_if_literal - idiom.severity_cultural > 0.4:
                    warnings.append(
                        f"'{idiom.original}' appears threatening literally but is "
                        f"a common expression meaning: {idiom.actual_meaning}"
                    )

        # Calculate severity adjustment
        if detected_idioms:
            avg_literal = sum(i.severity_if_literal for i in detected_idioms) / len(detected_idioms)
            avg_cultural = sum(i.severity_cultural for i in detected_idioms) / len(detected_idioms)
            severity_adjustment = avg_literal - avg_cultural
        else:
            severity_adjustment = 0.0

        # Build interpretations
        literal_interpretation = "; ".join(literal_parts) if literal_parts else text
        cultural_interpretation = "; ".join(cultural_parts) if cultural_parts else text

        return TranslationResult(
            original_text=text,
            detected_idioms=detected_idioms,
            literal_interpretation=literal_interpretation,
            cultural_interpretation=cultural_interpretation,
            legal_considerations=list(set(legal_considerations)),
            severity_adjustment=severity_adjustment,
            confidence=0.9 if detected_idioms else 0.5,
            warnings=warnings
        )

    def get_idioms_by_category(
        self,
        category: IdiomCategory,
        language: Optional[str] = None
    ) -> List[Idiom]:
        """Get idioms by category."""
        idioms = [i for i in self.idioms.values() if i.category == category]
        if language:
            idioms = [i for i in idioms if i.language == language]
        return idioms

    def get_idioms_by_language(self, language: str) -> List[Idiom]:
        """Get all idioms for a language."""
        return [i for i in self.idioms.values() if i.language == language]

    def get_threat_idioms(self, language: str) -> List[Idiom]:
        """Get expressions that sound threatening but aren't."""
        categories = [IdiomCategory.THREAT, IdiomCategory.FRUSTRATION, IdiomCategory.ANGER]
        return [
            i for i in self.idioms.values()
            if i.language == language and i.category in categories
            and i.severity_if_literal > 0.5 and i.severity_cultural < 0.4
        ]

    def generate_idiom_guide(
        self,
        language: str,
        output_language: str = "en"
    ) -> str:
        """Generate a guide to idioms in a language."""
        idioms = self.get_idioms_by_language(language)

        if not idioms:
            return f"No idioms found for language: {language}"

        lines = [
            f"IDIOM GUIDE: {language.upper()}",
            "=" * 50,
            "",
            "EXPRESSIONS THAT MAY APPEAR THREATENING:",
            "-" * 40
        ]

        threat_idioms = [i for i in idioms if i.severity_if_literal > 0.5]
        for idiom in threat_idioms:
            lines.extend([
                f"",
                f"Expression: {idiom.original}",
                f"Literal: {idiom.literal_translation}",
                f"Actual meaning: {idiom.actual_meaning}",
                f"Context: {idiom.usage_context}",
                f"Legal note: {idiom.legal_note}",
                ""
            ])

        lines.extend([
            "",
            "TERMS OF ENDEARMENT:",
            "-" * 40
        ])

        endearment_idioms = [i for i in idioms if i.category == IdiomCategory.ENDEARMENT]
        for idiom in endearment_idioms:
            lines.extend([
                f"",
                f"Expression: {idiom.original}",
                f"Literal: {idiom.literal_translation}",
                f"Meaning: {idiom.actual_meaning}",
                ""
            ])

        return "\n".join(lines)

    def batch_translate(
        self,
        texts: List[str],
        source_language: str
    ) -> List[TranslationResult]:
        """Translate multiple texts."""
        return [self.translate(text, source_language) for text in texts]
