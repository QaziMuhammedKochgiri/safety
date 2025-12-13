"""
Cultural Context Database
Cultural norms and family structure information by region.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set
from enum import Enum
from datetime import datetime


class CulturalRegion(str, Enum):
    """Cultural regions with distinct family norms."""
    WESTERN_EUROPE = "western_europe"
    EASTERN_EUROPE = "eastern_europe"
    NORTHERN_EUROPE = "northern_europe"
    SOUTHERN_EUROPE = "southern_europe"
    MIDDLE_EAST = "middle_east"
    TURKEY = "turkey"
    NORTH_AFRICA = "north_africa"
    SUB_SAHARAN_AFRICA = "sub_saharan_africa"
    SOUTH_ASIA = "south_asia"
    EAST_ASIA = "east_asia"
    SOUTHEAST_ASIA = "southeast_asia"
    NORTH_AMERICA = "north_america"
    LATIN_AMERICA = "latin_america"
    OCEANIA = "oceania"


class FamilyStructure(str, Enum):
    """Types of family structures."""
    NUCLEAR = "nuclear"  # Parents + children
    EXTENDED = "extended"  # Multiple generations
    PATRIARCHAL = "patriarchal"  # Father-centered
    MATRIARCHAL = "matriarchal"  # Mother-centered
    EGALITARIAN = "egalitarian"  # Equal partnership
    COLLECTIVIST = "collectivist"  # Family decisions together
    INDIVIDUALIST = "individualist"  # Individual autonomy


class CommunicationStyle(str, Enum):
    """Cultural communication styles."""
    DIRECT = "direct"  # Explicit, clear communication
    INDIRECT = "indirect"  # Implicit, contextual
    HIGH_CONTEXT = "high_context"  # Meaning from context
    LOW_CONTEXT = "low_context"  # Explicit meaning
    FORMAL = "formal"  # Hierarchical, respectful
    INFORMAL = "informal"  # Casual, egalitarian


class GenderRole(str, Enum):
    """Cultural gender role expectations."""
    TRADITIONAL = "traditional"
    MODERN = "modern"
    TRANSITIONAL = "transitional"
    EGALITARIAN = "egalitarian"


@dataclass
class CulturalNorm:
    """A specific cultural norm."""
    norm_id: str
    category: str  # family, communication, discipline, etc.
    description: Dict[str, str]  # language -> description
    regions: List[CulturalRegion]
    importance: float  # 0.0 - 1.0
    legal_relevance: str  # How it affects legal interpretation
    examples: List[str]
    court_consideration: str  # How courts should consider this


@dataclass
class CultureProfile:
    """Complete cultural profile for a region."""
    region: CulturalRegion
    primary_languages: List[str]
    family_structure: FamilyStructure
    communication_style: CommunicationStyle
    gender_roles: GenderRole
    discipline_norms: Dict[str, Any]
    respect_hierarchy: List[str]  # Who deserves respect (elders, etc.)
    family_involvement: float  # 0.0-1.0, extended family involvement
    honor_concept: bool  # Honor/shame culture
    collectivism_score: float  # 0.0 (individualist) - 1.0 (collectivist)
    power_distance: float  # 0.0 (low) - 1.0 (high)
    uncertainty_avoidance: float
    long_term_orientation: float
    norms: List[CulturalNorm]
    legal_system: str  # civil, common, religious, mixed
    child_custody_tendency: str  # Description of typical custody arrangements
    key_considerations: Dict[str, str]


# Cultural profiles database
CULTURE_PROFILES: Dict[CulturalRegion, Dict[str, Any]] = {
    CulturalRegion.TURKEY: {
        "primary_languages": ["tr"],
        "family_structure": FamilyStructure.EXTENDED,
        "communication_style": CommunicationStyle.INDIRECT,
        "gender_roles": GenderRole.TRANSITIONAL,
        "discipline_norms": {
            "physical": "Declining but historically accepted",
            "verbal": "Commonly used, especially by mothers",
            "emotional": "Through family pressure and honor concepts"
        },
        "respect_hierarchy": ["elders", "parents", "teachers", "religious_figures"],
        "family_involvement": 0.85,
        "honor_concept": True,
        "collectivism_score": 0.63,
        "power_distance": 0.66,
        "uncertainty_avoidance": 0.85,
        "long_term_orientation": 0.46,
        "legal_system": "civil",
        "child_custody_tendency": "Mother custody under 7, then either parent based on best interest",
        "key_considerations": {
            "namus": "Honor (namus) plays significant role in family disputes",
            "aile": "Extended family involvement is normal, not interference",
            "cocuk": "Children are community responsibility, not just parents'",
            "saygı": "Respect for elders may explain communication patterns"
        }
    },
    CulturalRegion.WESTERN_EUROPE: {
        "primary_languages": ["de", "fr", "nl", "en"],
        "family_structure": FamilyStructure.NUCLEAR,
        "communication_style": CommunicationStyle.DIRECT,
        "gender_roles": GenderRole.EGALITARIAN,
        "discipline_norms": {
            "physical": "Generally prohibited, legally banned in many countries",
            "verbal": "Discouraged, seen as emotionally harmful",
            "emotional": "Focus on natural consequences"
        },
        "respect_hierarchy": ["parents", "teachers"],
        "family_involvement": 0.4,
        "honor_concept": False,
        "collectivism_score": 0.35,
        "power_distance": 0.35,
        "uncertainty_avoidance": 0.65,
        "long_term_orientation": 0.55,
        "legal_system": "civil",
        "child_custody_tendency": "Joint custody preferred, based on child's best interest",
        "key_considerations": {
            "autonomy": "Individual autonomy highly valued, even for children",
            "equality": "Gender equality expected in parenting",
            "privacy": "Family matters considered private",
            "state_role": "Strong state intervention in child protection"
        }
    },
    CulturalRegion.MIDDLE_EAST: {
        "primary_languages": ["ar", "fa", "he"],
        "family_structure": FamilyStructure.PATRIARCHAL,
        "communication_style": CommunicationStyle.HIGH_CONTEXT,
        "gender_roles": GenderRole.TRADITIONAL,
        "discipline_norms": {
            "physical": "Traditionally accepted, varies by country",
            "verbal": "Common, expected from father",
            "emotional": "Through family honor and shame"
        },
        "respect_hierarchy": ["father", "elders", "religious_figures", "mother"],
        "family_involvement": 0.95,
        "honor_concept": True,
        "collectivism_score": 0.8,
        "power_distance": 0.8,
        "uncertainty_avoidance": 0.68,
        "long_term_orientation": 0.23,
        "legal_system": "mixed",
        "child_custody_tendency": "Mother until specific age (varies), then often father",
        "key_considerations": {
            "honor": "Family honor central to disputes",
            "religion": "Religious law may influence custody decisions",
            "gender": "Different expectations for sons and daughters",
            "extended_family": "Grandparents often involved in child-rearing"
        }
    },
    CulturalRegion.SOUTH_ASIA: {
        "primary_languages": ["hi", "ur", "bn", "ta"],
        "family_structure": FamilyStructure.EXTENDED,
        "communication_style": CommunicationStyle.INDIRECT,
        "gender_roles": GenderRole.TRADITIONAL,
        "discipline_norms": {
            "physical": "Widely accepted, seen as parental duty",
            "verbal": "Common, comparison with others",
            "emotional": "Through family expectations and guilt"
        },
        "respect_hierarchy": ["elders", "parents", "teachers", "in_laws"],
        "family_involvement": 0.9,
        "honor_concept": True,
        "collectivism_score": 0.77,
        "power_distance": 0.77,
        "uncertainty_avoidance": 0.4,
        "long_term_orientation": 0.51,
        "legal_system": "common",
        "child_custody_tendency": "Mother for young children, father financial responsibility",
        "key_considerations": {
            "izzat": "Family honor (izzat) crucial in decisions",
            "joint_family": "Joint family living is normative",
            "arranged_marriage": "Family involvement in life decisions",
            "caste": "Caste/community considerations may apply"
        }
    },
    CulturalRegion.EAST_ASIA: {
        "primary_languages": ["zh", "ja", "ko"],
        "family_structure": FamilyStructure.COLLECTIVIST,
        "communication_style": CommunicationStyle.HIGH_CONTEXT,
        "gender_roles": GenderRole.TRANSITIONAL,
        "discipline_norms": {
            "physical": "Declining, was traditionally accepted",
            "verbal": "Common, academic pressure",
            "emotional": "Through shame and family duty"
        },
        "respect_hierarchy": ["ancestors", "parents", "elders", "teachers"],
        "family_involvement": 0.75,
        "honor_concept": True,
        "collectivism_score": 0.46,
        "power_distance": 0.60,
        "uncertainty_avoidance": 0.85,
        "long_term_orientation": 0.87,
        "legal_system": "civil",
        "child_custody_tendency": "Varies by country, increasing joint custody",
        "key_considerations": {
            "face": "Maintaining face (面子/체면) is crucial",
            "education": "Educational achievement extremely important",
            "filial_piety": "Duty to parents and ancestors",
            "harmony": "Social harmony valued over individual expression"
        }
    },
    CulturalRegion.LATIN_AMERICA: {
        "primary_languages": ["es", "pt"],
        "family_structure": FamilyStructure.EXTENDED,
        "communication_style": CommunicationStyle.INDIRECT,
        "gender_roles": GenderRole.TRANSITIONAL,
        "discipline_norms": {
            "physical": "Traditionally accepted, changing",
            "verbal": "Common, expressive",
            "emotional": "Through family bonds and guilt"
        },
        "respect_hierarchy": ["parents", "elders", "godparents", "teachers"],
        "family_involvement": 0.85,
        "honor_concept": True,
        "collectivism_score": 0.76,
        "power_distance": 0.68,
        "uncertainty_avoidance": 0.8,
        "long_term_orientation": 0.33,
        "legal_system": "civil",
        "child_custody_tendency": "Traditionally mother, moving to shared",
        "key_considerations": {
            "familismo": "Strong family loyalty (familismo)",
            "machismo": "Traditional gender roles still influential",
            "compadrazgo": "Godparent relationships important",
            "expressiveness": "Emotional expression is normal"
        }
    }
}


# Cultural norms database
CULTURAL_NORMS: List[Dict[str, Any]] = [
    {
        "norm_id": "norm_discipline_001",
        "category": "discipline",
        "description": {
            "en": "Physical discipline is considered normal parenting in many cultures",
            "de": "Körperliche Züchtigung gilt in vielen Kulturen als normale Erziehung",
            "tr": "Fiziksel disiplin birçok kültürde normal ebeveynlik olarak kabul edilir"
        },
        "regions": [CulturalRegion.TURKEY, CulturalRegion.MIDDLE_EAST, CulturalRegion.SOUTH_ASIA],
        "importance": 0.8,
        "legal_relevance": "May be misinterpreted as abuse in Western courts",
        "examples": [
            "Light slapping for misbehavior",
            "Use of belt or stick for serious infractions"
        ],
        "court_consideration": "Courts should distinguish between cultural discipline practices and actual abuse"
    },
    {
        "norm_id": "norm_extended_family_001",
        "category": "family_involvement",
        "description": {
            "en": "Grandparents and extended family regularly involved in child-rearing",
            "de": "Großeltern und erweiterte Familie regelmäßig an der Kindererziehung beteiligt",
            "tr": "Büyükanne-babalar ve geniş aile düzenli olarak çocuk yetiştirmeye dahil"
        },
        "regions": [CulturalRegion.TURKEY, CulturalRegion.MIDDLE_EAST, CulturalRegion.SOUTH_ASIA, CulturalRegion.LATIN_AMERICA],
        "importance": 0.9,
        "legal_relevance": "Not third-party interference but normal family functioning",
        "examples": [
            "Grandparents providing daily care",
            "Aunts/uncles having authority over children",
            "Family councils making decisions"
        ],
        "court_consideration": "Extended family involvement should not be seen as alienation or interference"
    },
    {
        "norm_id": "norm_honor_001",
        "category": "honor",
        "description": {
            "en": "Family honor (namus/izzat) central to family functioning",
            "de": "Familienehre (namus/izzat) zentral für das Familienleben",
            "tr": "Aile namusu aile işleyişi için merkezi öneme sahip"
        },
        "regions": [CulturalRegion.TURKEY, CulturalRegion.MIDDLE_EAST, CulturalRegion.SOUTH_ASIA],
        "importance": 0.95,
        "legal_relevance": "May explain behavior that seems controlling to Western eyes",
        "examples": [
            "Concern about children's behavior reflecting on family",
            "Pressure to maintain appearances",
            "Strict rules about social interactions"
        ],
        "court_consideration": "Honor concerns should be understood but not justify harmful behavior"
    },
    {
        "norm_id": "norm_gender_roles_001",
        "category": "gender",
        "description": {
            "en": "Traditional gender roles assign different responsibilities to mothers and fathers",
            "de": "Traditionelle Geschlechterrollen weisen Müttern und Vätern unterschiedliche Verantwortlichkeiten zu",
            "tr": "Geleneksel cinsiyet rolleri annelere ve babalara farklı sorumluluklar verir"
        },
        "regions": [CulturalRegion.TURKEY, CulturalRegion.MIDDLE_EAST, CulturalRegion.SOUTH_ASIA, CulturalRegion.LATIN_AMERICA],
        "importance": 0.7,
        "legal_relevance": "Father's financial focus doesn't mean disengagement from children",
        "examples": [
            "Father as breadwinner, mother as caregiver",
            "Father as disciplinarian",
            "Different interactions with sons vs daughters"
        ],
        "court_consideration": "Traditional roles don't indicate lack of parental love or capability"
    },
    {
        "norm_id": "norm_communication_001",
        "category": "communication",
        "description": {
            "en": "High-context communication relies on implicit meaning rather than explicit words",
            "de": "High-Context-Kommunikation basiert auf impliziter Bedeutung statt expliziter Worte",
            "tr": "Yüksek bağlamlı iletişim açık kelimeler yerine örtük anlama dayanır"
        },
        "regions": [CulturalRegion.TURKEY, CulturalRegion.MIDDLE_EAST, CulturalRegion.EAST_ASIA, CulturalRegion.SOUTH_ASIA],
        "importance": 0.8,
        "legal_relevance": "Messages may not mean what they literally say",
        "examples": [
            "Saying 'no problem' when there is a problem",
            "Using hints rather than direct requests",
            "Silence meaning disagreement"
        ],
        "court_consideration": "Text message analysis needs cultural context interpretation"
    },
    {
        "norm_id": "norm_respect_001",
        "category": "respect",
        "description": {
            "en": "Deference to elders and authority figures is expected and normal",
            "de": "Respekt vor Älteren und Autoritätspersonen wird erwartet und ist normal",
            "tr": "Büyüklere ve otorite figürlerine saygı beklenir ve normaldir"
        },
        "regions": [CulturalRegion.TURKEY, CulturalRegion.EAST_ASIA, CulturalRegion.SOUTH_ASIA, CulturalRegion.MIDDLE_EAST],
        "importance": 0.85,
        "legal_relevance": "Child's deference to parent may be cultural, not fear",
        "examples": [
            "Not contradicting parents in public",
            "Speaking formally to elders",
            "Following elder's decisions without question"
        ],
        "court_consideration": "Quiet compliance may be respect, not indication of abuse"
    }
]


class CulturalContext:
    """Database and analyzer for cultural context."""

    def __init__(self):
        self.profiles: Dict[CulturalRegion, CultureProfile] = {}
        self.norms: Dict[str, CulturalNorm] = {}
        self._load_profiles()
        self._load_norms()

    def _load_profiles(self):
        """Load cultural profiles."""
        for region, data in CULTURE_PROFILES.items():
            norms = [n for n in CULTURAL_NORMS if region in n.get("regions", [])]
            norm_objects = [
                CulturalNorm(
                    norm_id=n["norm_id"],
                    category=n["category"],
                    description=n["description"],
                    regions=n["regions"],
                    importance=n["importance"],
                    legal_relevance=n["legal_relevance"],
                    examples=n["examples"],
                    court_consideration=n["court_consideration"]
                )
                for n in norms
            ]

            profile = CultureProfile(
                region=region,
                primary_languages=data["primary_languages"],
                family_structure=data["family_structure"],
                communication_style=data["communication_style"],
                gender_roles=data["gender_roles"],
                discipline_norms=data["discipline_norms"],
                respect_hierarchy=data["respect_hierarchy"],
                family_involvement=data["family_involvement"],
                honor_concept=data["honor_concept"],
                collectivism_score=data["collectivism_score"],
                power_distance=data["power_distance"],
                uncertainty_avoidance=data["uncertainty_avoidance"],
                long_term_orientation=data["long_term_orientation"],
                norms=norm_objects,
                legal_system=data["legal_system"],
                child_custody_tendency=data["child_custody_tendency"],
                key_considerations=data["key_considerations"]
            )

            self.profiles[region] = profile

    def _load_norms(self):
        """Load cultural norms."""
        for norm_data in CULTURAL_NORMS:
            norm = CulturalNorm(
                norm_id=norm_data["norm_id"],
                category=norm_data["category"],
                description=norm_data["description"],
                regions=norm_data["regions"],
                importance=norm_data["importance"],
                legal_relevance=norm_data["legal_relevance"],
                examples=norm_data["examples"],
                court_consideration=norm_data["court_consideration"]
            )
            self.norms[norm.norm_id] = norm

    def get_profile(self, region: CulturalRegion) -> Optional[CultureProfile]:
        """Get cultural profile for a region."""
        return self.profiles.get(region)

    def get_profile_by_language(self, language_code: str) -> Optional[CultureProfile]:
        """Get cultural profile by primary language."""
        for profile in self.profiles.values():
            if language_code in profile.primary_languages:
                return profile
        return None

    def get_relevant_norms(
        self,
        region: CulturalRegion,
        categories: Optional[List[str]] = None
    ) -> List[CulturalNorm]:
        """Get relevant cultural norms for a region."""
        norms = [
            n for n in self.norms.values()
            if region in n.regions
        ]

        if categories:
            norms = [n for n in norms if n.category in categories]

        return sorted(norms, key=lambda n: n.importance, reverse=True)

    def get_court_considerations(
        self,
        region: CulturalRegion,
        language: str = "en"
    ) -> List[Dict[str, str]]:
        """Get court considerations for a cultural context."""
        profile = self.get_profile(region)
        if not profile:
            return []

        considerations = []

        # Add profile-level considerations
        for key, value in profile.key_considerations.items():
            considerations.append({
                "category": key,
                "consideration": value,
                "importance": "high"
            })

        # Add norm-specific considerations
        for norm in profile.norms:
            desc = norm.description.get(language, norm.description.get("en", ""))
            considerations.append({
                "category": norm.category,
                "consideration": norm.court_consideration,
                "description": desc,
                "importance": "high" if norm.importance > 0.7 else "medium"
            })

        return considerations

    def compare_cultures(
        self,
        region1: CulturalRegion,
        region2: CulturalRegion
    ) -> Dict[str, Any]:
        """Compare two cultural profiles."""
        p1 = self.get_profile(region1)
        p2 = self.get_profile(region2)

        if not p1 or not p2:
            return {"error": "Profile not found"}

        differences = []
        similarities = []

        # Compare dimensions
        dimensions = [
            ("family_involvement", "Family Involvement"),
            ("collectivism_score", "Collectivism"),
            ("power_distance", "Power Distance"),
            ("uncertainty_avoidance", "Uncertainty Avoidance")
        ]

        for dim, name in dimensions:
            v1 = getattr(p1, dim)
            v2 = getattr(p2, dim)
            diff = abs(v1 - v2)

            if diff < 0.2:
                similarities.append({
                    "dimension": name,
                    "value1": v1,
                    "value2": v2,
                    "note": "Similar across cultures"
                })
            else:
                differences.append({
                    "dimension": name,
                    "value1": v1,
                    "value2": v2,
                    "diff": diff,
                    "note": f"{region1.value} is {'higher' if v1 > v2 else 'lower'}"
                })

        # Compare structures
        if p1.family_structure != p2.family_structure:
            differences.append({
                "dimension": "Family Structure",
                "value1": p1.family_structure.value,
                "value2": p2.family_structure.value,
                "note": "Different family organization"
            })

        if p1.communication_style != p2.communication_style:
            differences.append({
                "dimension": "Communication Style",
                "value1": p1.communication_style.value,
                "value2": p2.communication_style.value,
                "note": "Different communication expectations"
            })

        return {
            "region1": region1.value,
            "region2": region2.value,
            "differences": sorted(differences, key=lambda x: x.get("diff", 0), reverse=True),
            "similarities": similarities,
            "cross_cultural_notes": self._get_cross_cultural_notes(p1, p2)
        }

    def _get_cross_cultural_notes(
        self,
        p1: CultureProfile,
        p2: CultureProfile
    ) -> List[str]:
        """Generate notes for cross-cultural situations."""
        notes = []

        # Honor culture clash
        if p1.honor_concept and not p2.honor_concept:
            notes.append(
                "Honor-based behavior from one culture may be misunderstood "
                "as controlling or abusive by the other culture's standards"
            )

        # Extended vs nuclear family
        if p1.family_involvement > 0.7 and p2.family_involvement < 0.5:
            notes.append(
                "Extended family involvement normal in one culture may be "
                "seen as interference by the other"
            )

        # Communication style
        if p1.communication_style != p2.communication_style:
            notes.append(
                "Different communication styles may lead to misunderstandings "
                "in message interpretation"
            )

        # Gender roles
        if p1.gender_roles != p2.gender_roles:
            notes.append(
                "Different gender role expectations may affect parenting "
                "style assessments"
            )

        return notes

    def get_interpretation_guide(
        self,
        region: CulturalRegion,
        context: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """Get interpretation guide for specific context."""
        profile = self.get_profile(region)
        if not profile:
            return {"error": "Profile not found"}

        guides = {
            "discipline": {
                "en": {
                    "introduction": f"In {region.value} culture, discipline is understood as:",
                    "norms": profile.discipline_norms,
                    "consideration": "Physical discipline may be cultural, not abusive",
                    "warning": "However, severity must still be assessed"
                }
            },
            "communication": {
                "en": {
                    "introduction": f"Communication in {region.value} is typically {profile.communication_style.value}",
                    "implications": [
                        "Messages may not mean what they literally say",
                        "Context is crucial for interpretation",
                        "Silence may have meaning"
                    ],
                    "analysis_tip": "Look for contextual clues, not just words"
                }
            },
            "family_involvement": {
                "en": {
                    "introduction": f"Family involvement score: {profile.family_involvement:.0%}",
                    "implications": [
                        "Extended family involvement is normal" if profile.family_involvement > 0.6 else "Nuclear family focus",
                        "Not necessarily third-party interference",
                        "May explain presence of grandparents in communications"
                    ]
                }
            }
        }

        return guides.get(context, {"error": f"Unknown context: {context}"}).get(language, guides.get(context, {}).get("en", {}))
