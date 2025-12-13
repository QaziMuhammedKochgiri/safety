"""
Cultural Analyzer
Culture-aware text analysis for evidence interpretation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
from datetime import datetime
import re

from .cultural_context import CulturalContext, CulturalRegion, CultureProfile
from .language_detector import LanguageDetector, LanguageCode


class CulturalIndicator(str, Enum):
    """Types of cultural indicators in text."""
    HONORIFIC = "honorific"
    FAMILY_TERM = "family_term"
    RELIGIOUS_REFERENCE = "religious_reference"
    HONOR_CONCEPT = "honor_concept"
    FORMALITY_MARKER = "formality_marker"
    INDIRECT_COMMUNICATION = "indirect_communication"
    COLLECTIVE_REFERENCE = "collective_reference"
    GENDER_ROLE = "gender_role"
    DISCIPLINE_REFERENCE = "discipline_reference"
    RESPECT_MARKER = "respect_marker"


@dataclass
class ContextualMeaning:
    """Cultural context for a phrase or word."""
    phrase: str
    literal_meaning: str
    cultural_meaning: str
    region: CulturalRegion
    indicator_type: CulturalIndicator
    legal_relevance: str
    confidence: float
    examples: List[str]


@dataclass
class CulturalAnalysis:
    """Complete cultural analysis of text."""
    text: str
    detected_language: LanguageCode
    inferred_culture: CulturalRegion
    culture_confidence: float
    indicators_found: List[CulturalIndicator]
    contextual_meanings: List[ContextualMeaning]
    court_considerations: List[str]
    potential_misinterpretations: List[Dict[str, str]]
    cultural_context_notes: List[str]
    analysis_timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


# Cultural indicator patterns
CULTURAL_PATTERNS: Dict[CulturalRegion, Dict[CulturalIndicator, List[Dict[str, Any]]]] = {
    CulturalRegion.TURKEY: {
        CulturalIndicator.FAMILY_TERM: [
            {"pattern": r"\b(anne|baba|dede|nine|amca|dayı|teyze|hala|abla|abi)\b",
             "meaning": "Family terms indicating extended family involvement"},
            {"pattern": r"\b(koca|karı|eş|gelin|damat)\b",
             "meaning": "Spouse/in-law terms showing family structure"}
        ],
        CulturalIndicator.HONOR_CONCEPT: [
            {"pattern": r"\b(namus|şeref|onur|ayıp|ar|günah)\b",
             "meaning": "Honor/shame concepts central to behavior"},
            {"pattern": r"\b(rezil|mahcup|utanç|yüz kızartıcı)\b",
             "meaning": "Shame-related terms"}
        ],
        CulturalIndicator.RESPECT_MARKER: [
            {"pattern": r"\b(saygı|hürmet|edep|terbiye)\b",
             "meaning": "Respect concepts"},
            {"pattern": r"\b(büyükler|yaşlılar|efendi|hanım)\b",
             "meaning": "Respect for elders/authority"}
        ],
        CulturalIndicator.DISCIPLINE_REFERENCE: [
            {"pattern": r"\b(dayak|tokat|dövmek|cezalandır)\b",
             "meaning": "Physical discipline terms"},
            {"pattern": r"\b(uslan|adam ol|yaramazlık)\b",
             "meaning": "Behavioral correction terms"}
        ],
        CulturalIndicator.RELIGIOUS_REFERENCE: [
            {"pattern": r"\b(allah|inşallah|maşallah|bismillah|helal|haram)\b",
             "meaning": "Religious references common in speech"},
            {"pattern": r"\b(dua|namaz|oruç|bayram)\b",
             "meaning": "Religious practice references"}
        ],
        CulturalIndicator.INDIRECT_COMMUNICATION: [
            {"pattern": r"\b(yani|şey|anlarsın|bilirsin|malum)\b",
             "meaning": "Indirect communication markers"},
            {"pattern": r"\b(demek istediğim|anladın mı|ne demek istediğimi)\b",
             "meaning": "Implicit meaning indicators"}
        ]
    },
    CulturalRegion.MIDDLE_EAST: {
        CulturalIndicator.HONOR_CONCEPT: [
            {"pattern": r"\b(شرف|عرض|نامس|عار)\b",
             "meaning": "Honor concepts"},
            {"pattern": r"\b(عيب|حرام|حلال)\b",
             "meaning": "Shame and religious propriety"}
        ],
        CulturalIndicator.FAMILY_TERM: [
            {"pattern": r"\b(أب|أم|جد|جدة|عم|خال|خالة|عمة)\b",
             "meaning": "Extended family terms"},
            {"pattern": r"\b(زوج|زوجة|حماة|حمو)\b",
             "meaning": "Spouse and in-law terms"}
        ],
        CulturalIndicator.RELIGIOUS_REFERENCE: [
            {"pattern": r"\b(الله|إن شاء الله|ما شاء الله|بسم الله)\b",
             "meaning": "Religious expressions"},
            {"pattern": r"\b(صلاة|صوم|حج|زكاة)\b",
             "meaning": "Religious practice"}
        ]
    },
    CulturalRegion.WESTERN_EUROPE: {
        CulturalIndicator.FORMALITY_MARKER: [
            {"pattern": r"\b(Sie|Ihnen|Sehr geehrte)\b",
             "meaning": "Formal address in German"},
            {"pattern": r"\b(vous|madame|monsieur)\b",
             "meaning": "Formal address in French"}
        ],
        CulturalIndicator.FAMILY_TERM: [
            {"pattern": r"\b(Mutter|Vater|Eltern|Großeltern)\b",
             "meaning": "German family terms"},
            {"pattern": r"\b(mère|père|parents|grands-parents)\b",
             "meaning": "French family terms"}
        ]
    }
}

# Cultural misinterpretation database
CULTURAL_MISINTERPRETATIONS: List[Dict[str, Any]] = [
    {
        "surface_meaning": "Parent threatens to 'hit' child",
        "cultural_context": "In many cultures, verbal threats of physical discipline are common expressions of frustration, not actual intent",
        "regions": [CulturalRegion.TURKEY, CulturalRegion.MIDDLE_EAST, CulturalRegion.SOUTH_ASIA],
        "legal_note": "May not indicate actual abuse risk - context and history matter",
        "keywords": ["hit", "beat", "slap", "döv", "vur", "ضرب"]
    },
    {
        "surface_meaning": "Grandparent making parenting decisions",
        "cultural_context": "Extended family involvement in child-rearing is normal, not interference",
        "regions": [CulturalRegion.TURKEY, CulturalRegion.MIDDLE_EAST, CulturalRegion.SOUTH_ASIA, CulturalRegion.LATIN_AMERICA],
        "legal_note": "Not third-party interference - normal family functioning",
        "keywords": ["grandparent", "grandmother", "grandfather", "dede", "nine", "جد", "جدة"]
    },
    {
        "surface_meaning": "Parent mentions family honor",
        "cultural_context": "Honor concepts are cultural values, not necessarily controlling behavior",
        "regions": [CulturalRegion.TURKEY, CulturalRegion.MIDDLE_EAST, CulturalRegion.SOUTH_ASIA],
        "legal_note": "Concern for honor is cultural, but extreme measures for honor must be assessed",
        "keywords": ["honor", "namus", "şeref", "شرف", "عرض", "izzat"]
    },
    {
        "surface_meaning": "Parent uses religious language",
        "cultural_context": "Religious expressions are common in daily speech, not necessarily fundamentalist",
        "regions": [CulturalRegion.TURKEY, CulturalRegion.MIDDLE_EAST],
        "legal_note": "Religious references don't indicate extremism - assess actual behavior",
        "keywords": ["inshallah", "mashallah", "allah", "إن شاء الله", "ما شاء الله"]
    },
    {
        "surface_meaning": "Child shows deference/obedience",
        "cultural_context": "Respect for parents/elders is deeply ingrained, silence may be respect not fear",
        "regions": [CulturalRegion.TURKEY, CulturalRegion.MIDDLE_EAST, CulturalRegion.EAST_ASIA, CulturalRegion.SOUTH_ASIA],
        "legal_note": "Quiet compliance may be cultural respect, not indication of abuse",
        "keywords": ["obey", "respect", "saygı", "hürmet", "احترام"]
    }
]


class CulturalAnalyzer:
    """Analyzes text for cultural context."""

    def __init__(self):
        self.cultural_context = CulturalContext()
        self.language_detector = LanguageDetector()

    def analyze(
        self,
        text: str,
        known_culture: Optional[CulturalRegion] = None
    ) -> CulturalAnalysis:
        """Perform cultural analysis on text."""
        # Detect language
        lang_result = self.language_detector.detect(text)
        detected_language = lang_result.primary_language

        # Infer culture from language if not provided
        if known_culture:
            inferred_culture = known_culture
            culture_confidence = 1.0
        else:
            inferred_culture, culture_confidence = self._infer_culture(
                detected_language, text
            )

        # Find cultural indicators
        indicators_found, contextual_meanings = self._find_indicators(
            text, inferred_culture
        )

        # Get court considerations
        court_considerations = self._get_court_considerations(
            inferred_culture, indicators_found
        )

        # Find potential misinterpretations
        misinterpretations = self._find_misinterpretations(
            text, inferred_culture
        )

        # Generate cultural context notes
        context_notes = self._generate_context_notes(
            inferred_culture, indicators_found
        )

        return CulturalAnalysis(
            text=text,
            detected_language=detected_language,
            inferred_culture=inferred_culture,
            culture_confidence=culture_confidence,
            indicators_found=list(set(indicators_found)),
            contextual_meanings=contextual_meanings,
            court_considerations=court_considerations,
            potential_misinterpretations=misinterpretations,
            cultural_context_notes=context_notes,
            analysis_timestamp=datetime.utcnow()
        )

    def _infer_culture(
        self,
        language: LanguageCode,
        text: str
    ) -> Tuple[CulturalRegion, float]:
        """Infer cultural region from language and content."""
        language_to_culture = {
            LanguageCode.TURKISH: (CulturalRegion.TURKEY, 0.9),
            LanguageCode.ARABIC: (CulturalRegion.MIDDLE_EAST, 0.7),
            LanguageCode.PERSIAN: (CulturalRegion.MIDDLE_EAST, 0.8),
            LanguageCode.GERMAN: (CulturalRegion.WESTERN_EUROPE, 0.8),
            LanguageCode.FRENCH: (CulturalRegion.WESTERN_EUROPE, 0.7),
            LanguageCode.SPANISH: (CulturalRegion.LATIN_AMERICA, 0.6),
            LanguageCode.ENGLISH: (CulturalRegion.WESTERN_EUROPE, 0.5),
            LanguageCode.RUSSIAN: (CulturalRegion.EASTERN_EUROPE, 0.8),
            LanguageCode.HINDI: (CulturalRegion.SOUTH_ASIA, 0.9),
            LanguageCode.KURDISH_KURMANJI: (CulturalRegion.TURKEY, 0.8),
            LanguageCode.KURDISH_SORANI: (CulturalRegion.MIDDLE_EAST, 0.8)
        }

        return language_to_culture.get(
            language,
            (CulturalRegion.WESTERN_EUROPE, 0.3)
        )

    def _find_indicators(
        self,
        text: str,
        culture: CulturalRegion
    ) -> Tuple[List[CulturalIndicator], List[ContextualMeaning]]:
        """Find cultural indicators in text."""
        indicators = []
        meanings = []
        text_lower = text.lower()

        patterns = CULTURAL_PATTERNS.get(culture, {})

        for indicator_type, pattern_list in patterns.items():
            for pattern_info in pattern_list:
                pattern = pattern_info["pattern"]
                matches = re.findall(pattern, text, re.IGNORECASE)

                if matches:
                    indicators.append(indicator_type)

                    for match in matches[:3]:  # Limit to 3 examples
                        meaning = ContextualMeaning(
                            phrase=match,
                            literal_meaning=match,
                            cultural_meaning=pattern_info["meaning"],
                            region=culture,
                            indicator_type=indicator_type,
                            legal_relevance=self._get_legal_relevance(indicator_type),
                            confidence=0.8,
                            examples=[]
                        )
                        meanings.append(meaning)

        return indicators, meanings

    def _get_legal_relevance(self, indicator: CulturalIndicator) -> str:
        """Get legal relevance for indicator type."""
        relevance = {
            CulturalIndicator.HONOR_CONCEPT: (
                "Honor-based language may be cultural expression, not necessarily "
                "indicating controlling or abusive behavior"
            ),
            CulturalIndicator.FAMILY_TERM: (
                "Extended family involvement is normative in this culture and "
                "should not be interpreted as third-party interference"
            ),
            CulturalIndicator.DISCIPLINE_REFERENCE: (
                "References to discipline should be assessed in cultural context - "
                "verbal expressions may not indicate actual behavior"
            ),
            CulturalIndicator.RELIGIOUS_REFERENCE: (
                "Religious language is common in daily speech and does not "
                "necessarily indicate fundamentalism or extremism"
            ),
            CulturalIndicator.RESPECT_MARKER: (
                "Emphasis on respect and hierarchy is cultural and should not be "
                "confused with authoritarian control"
            ),
            CulturalIndicator.INDIRECT_COMMUNICATION: (
                "Indirect communication style may affect message interpretation - "
                "literal reading may miss intended meaning"
            )
        }

        return relevance.get(indicator, "Cultural context should be considered")

    def _get_court_considerations(
        self,
        culture: CulturalRegion,
        indicators: List[CulturalIndicator]
    ) -> List[str]:
        """Get court considerations based on analysis."""
        considerations = []

        profile = self.cultural_context.get_profile(culture)
        if profile:
            for key, value in profile.key_considerations.items():
                considerations.append(f"{key.title()}: {value}")

        # Add indicator-specific considerations
        if CulturalIndicator.HONOR_CONCEPT in indicators:
            considerations.append(
                "Honor-based language detected - assess whether this represents "
                "cultural values or harmful behavior"
            )

        if CulturalIndicator.FAMILY_TERM in indicators:
            considerations.append(
                "Extended family references detected - this culture typically "
                "involves family in child-rearing decisions"
            )

        if CulturalIndicator.DISCIPLINE_REFERENCE in indicators:
            considerations.append(
                "Discipline language detected - cultural norms around discipline "
                "differ; assess actual behavior, not just words"
            )

        return considerations

    def _find_misinterpretations(
        self,
        text: str,
        culture: CulturalRegion
    ) -> List[Dict[str, str]]:
        """Find potential misinterpretations."""
        misinterpretations = []
        text_lower = text.lower()

        for misint in CULTURAL_MISINTERPRETATIONS:
            if culture not in misint["regions"]:
                continue

            for keyword in misint["keywords"]:
                if keyword.lower() in text_lower:
                    misinterpretations.append({
                        "surface_meaning": misint["surface_meaning"],
                        "cultural_context": misint["cultural_context"],
                        "legal_note": misint["legal_note"],
                        "trigger": keyword
                    })
                    break

        return misinterpretations

    def _generate_context_notes(
        self,
        culture: CulturalRegion,
        indicators: List[CulturalIndicator]
    ) -> List[str]:
        """Generate contextual notes for the analysis."""
        notes = []

        profile = self.cultural_context.get_profile(culture)
        if not profile:
            return notes

        notes.append(
            f"Culture: {culture.value} - Family involvement level: "
            f"{profile.family_involvement:.0%}"
        )

        if profile.honor_concept:
            notes.append(
                "This is an honor-based culture - honor/shame concepts affect "
                "behavior and should be understood in context"
            )

        if profile.collectivism_score > 0.6:
            notes.append(
                f"Collectivist culture ({profile.collectivism_score:.0%}) - "
                "family/community decisions are normal"
            )

        if profile.power_distance > 0.6:
            notes.append(
                f"High power distance ({profile.power_distance:.0%}) - "
                "hierarchical relationships are normative"
            )

        return notes

    def compare_interpretations(
        self,
        text: str,
        culture1: CulturalRegion,
        culture2: CulturalRegion
    ) -> Dict[str, Any]:
        """Compare how text might be interpreted in different cultures."""
        analysis1 = self.analyze(text, culture1)
        analysis2 = self.analyze(text, culture2)

        return {
            "text": text,
            "culture1": {
                "region": culture1.value,
                "indicators": [i.value for i in analysis1.indicators_found],
                "considerations": analysis1.court_considerations,
                "misinterpretations": analysis1.potential_misinterpretations
            },
            "culture2": {
                "region": culture2.value,
                "indicators": [i.value for i in analysis2.indicators_found],
                "considerations": analysis2.court_considerations,
                "misinterpretations": analysis2.potential_misinterpretations
            },
            "cross_cultural_notes": self.cultural_context.compare_cultures(
                culture1, culture2
            ).get("cross_cultural_notes", [])
        }

    def get_cultural_disclaimer(
        self,
        culture: CulturalRegion,
        language: str = "en"
    ) -> str:
        """Generate cultural context disclaimer for reports."""
        templates = {
            "en": (
                "CULTURAL CONTEXT DISCLAIMER\n\n"
                "This analysis involves parties from {culture} cultural background. "
                "The following cultural factors should be considered:\n\n"
                "{factors}\n\n"
                "Communications and behaviors should be interpreted with awareness "
                "of these cultural norms. What may appear concerning from one "
                "cultural perspective may be normative in another."
            ),
            "de": (
                "KULTURELLER KONTEXTHINWEIS\n\n"
                "Diese Analyse betrifft Parteien mit {culture} kulturellem Hintergrund. "
                "Die folgenden kulturellen Faktoren sollten berücksichtigt werden:\n\n"
                "{factors}\n\n"
                "Kommunikation und Verhaltensweisen sollten unter Berücksichtigung "
                "dieser kulturellen Normen interpretiert werden."
            ),
            "tr": (
                "KÜLTÜREL BAĞLAM UYARISI\n\n"
                "Bu analiz {culture} kültürel geçmişe sahip tarafları içermektedir. "
                "Aşağıdaki kültürel faktörler dikkate alınmalıdır:\n\n"
                "{factors}\n\n"
                "İletişim ve davranışlar bu kültürel normlar göz önünde bulundurularak "
                "yorumlanmalıdır."
            )
        }

        profile = self.cultural_context.get_profile(culture)
        factors = []

        if profile:
            if profile.family_involvement > 0.6:
                factors.append("- Extended family involvement is normative")
            if profile.honor_concept:
                factors.append("- Honor/shame concepts influence behavior")
            if profile.collectivism_score > 0.6:
                factors.append("- Collective family decision-making is expected")
            if profile.power_distance > 0.6:
                factors.append("- Hierarchical relationships are cultural norm")

        template = templates.get(language, templates["en"])
        return template.format(
            culture=culture.value.replace("_", " ").title(),
            factors="\n".join(factors) if factors else "- Cultural context should be considered"
        )
