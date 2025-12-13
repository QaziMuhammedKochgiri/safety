"""
Legal Terminology
Cross-jurisdictional legal term translation with context.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class JurisdictionType(str, Enum):
    """Types of legal jurisdictions."""
    GERMAN = "german"
    TURKISH = "turkish"
    EU = "eu"
    UK = "uk"
    US = "us"
    INTERNATIONAL = "international"


class LegalDomain(str, Enum):
    """Legal domains/areas."""
    FAMILY = "family"
    CUSTODY = "custody"
    CHILD_PROTECTION = "child_protection"
    DOMESTIC_VIOLENCE = "domestic_violence"
    INTERNATIONAL = "international"
    EVIDENCE = "evidence"
    PROCEDURE = "procedure"


@dataclass
class TermEquivalent:
    """A term equivalent in a specific jurisdiction."""
    jurisdiction: JurisdictionType
    term: str
    language_code: str
    definition: str
    legal_basis: str  # Law/regulation reference
    nuances: List[str]  # Important differences
    usage_examples: List[str]


@dataclass
class LegalTerm:
    """A legal term with cross-jurisdictional equivalents."""
    term_id: str
    canonical_term: str  # Standard English term
    domain: LegalDomain
    definition: str
    equivalents: List[TermEquivalent]
    false_friends: List[str]  # Terms that look similar but mean different
    warnings: List[str]  # Important legal warnings
    related_terms: List[str]


@dataclass
class JurisdictionContext:
    """Context for a specific legal jurisdiction."""
    jurisdiction: JurisdictionType
    language_code: str
    legal_system: str  # civil law, common law, etc.
    family_court_name: str
    custody_authority: str
    child_protection_agency: str
    key_legislation: List[str]
    court_levels: List[str]
    appeal_process: str


@dataclass
class TranslationContext:
    """Context for legal term translation."""
    source_jurisdiction: JurisdictionType
    target_jurisdiction: JurisdictionType
    domain: LegalDomain
    formality_level: str  # court, informal, academic
    needs_explanation: bool


@dataclass
class TermTranslation:
    """Result of translating a legal term."""
    original_term: str
    translated_term: str
    source_jurisdiction: JurisdictionType
    target_jurisdiction: JurisdictionType
    confidence: float
    warnings: List[str]
    explanation: str
    legal_basis: str
    false_friends_warning: Optional[str]


# Jurisdiction context database
JURISDICTION_CONTEXTS: Dict[JurisdictionType, Dict[str, Any]] = {
    JurisdictionType.GERMAN: {
        "jurisdiction": JurisdictionType.GERMAN,
        "language_code": "de",
        "legal_system": "civil_law",
        "family_court_name": "Familiengericht",
        "custody_authority": "Jugendamt",
        "child_protection_agency": "Jugendamt",
        "key_legislation": [
            "BGB (Bürgerliches Gesetzbuch) §§ 1626-1698",
            "FamFG (Gesetz über das Verfahren in Familiensachen)",
            "SGB VIII (Kinder- und Jugendhilfegesetz)",
            "GewSchG (Gewaltschutzgesetz)"
        ],
        "court_levels": [
            "Amtsgericht - Familiengericht",
            "Oberlandesgericht",
            "Bundesgerichtshof"
        ],
        "appeal_process": "Beschwerde within 1 month to Oberlandesgericht"
    },
    JurisdictionType.TURKISH: {
        "jurisdiction": JurisdictionType.TURKISH,
        "language_code": "tr",
        "legal_system": "civil_law",
        "family_court_name": "Aile Mahkemesi",
        "custody_authority": "Aile ve Sosyal Hizmetler İl Müdürlüğü",
        "child_protection_agency": "Sosyal Hizmetler ve Çocuk Esirgeme Kurumu",
        "key_legislation": [
            "Türk Medeni Kanunu (TMK) Madde 335-351",
            "Aile Mahkemeleri Kuruluş Kanunu",
            "Çocuk Koruma Kanunu",
            "Ailenin Korunması ve Kadına Karşı Şiddetin Önlenmesine Dair Kanun"
        ],
        "court_levels": [
            "Aile Mahkemesi",
            "Bölge Adliye Mahkemesi",
            "Yargıtay"
        ],
        "appeal_process": "İstinaf within 2 weeks to Bölge Adliye Mahkemesi"
    },
    JurisdictionType.EU: {
        "jurisdiction": JurisdictionType.EU,
        "language_code": "en",
        "legal_system": "supranational",
        "family_court_name": "National Family Court (jurisdiction specific)",
        "custody_authority": "National Authority",
        "child_protection_agency": "National Child Protection Service",
        "key_legislation": [
            "Brussels IIa Regulation (2201/2003)",
            "Brussels IIb Regulation (2019/1111)",
            "Hague Convention on Child Abduction 1980",
            "Hague Convention on Parental Responsibility 1996"
        ],
        "court_levels": [
            "National First Instance Court",
            "National Appeal Court",
            "Court of Justice of the European Union (CJEU)"
        ],
        "appeal_process": "Varies by Member State; CJEU for EU law interpretation"
    },
    JurisdictionType.UK: {
        "jurisdiction": JurisdictionType.UK,
        "language_code": "en",
        "legal_system": "common_law",
        "family_court_name": "Family Court",
        "custody_authority": "Cafcass (Children and Family Court Advisory and Support Service)",
        "child_protection_agency": "Local Authority Children's Services",
        "key_legislation": [
            "Children Act 1989",
            "Children and Families Act 2014",
            "Family Law Act 1996",
            "Domestic Abuse Act 2021"
        ],
        "court_levels": [
            "Family Court (Magistrates/District Judge)",
            "Family Court (Circuit Judge)",
            "High Court (Family Division)",
            "Court of Appeal",
            "Supreme Court"
        ],
        "appeal_process": "Permission to appeal required; to next tier within 21 days"
    },
    JurisdictionType.US: {
        "jurisdiction": JurisdictionType.US,
        "language_code": "en",
        "legal_system": "common_law",
        "family_court_name": "Family Court / Superior Court",
        "custody_authority": "Department of Children and Family Services (varies by state)",
        "child_protection_agency": "Child Protective Services (CPS)",
        "key_legislation": [
            "UCCJEA (Uniform Child Custody Jurisdiction and Enforcement Act)",
            "PKPA (Parental Kidnapping Prevention Act)",
            "ICARA (International Child Abduction Remedies Act)",
            "State Family Code (varies)"
        ],
        "court_levels": [
            "Family Court / Superior Court",
            "State Court of Appeals",
            "State Supreme Court",
            "Federal Courts (for ICARA)"
        ],
        "appeal_process": "Varies by state; typically 30-60 days to file notice of appeal"
    }
}


# Legal terminology database
LEGAL_TERMS: List[Dict[str, Any]] = [
    # Custody terms
    {
        "term_id": "custody_001",
        "canonical_term": "sole custody",
        "domain": LegalDomain.CUSTODY,
        "definition": "One parent has exclusive legal and physical custody of the child",
        "equivalents": [
            {
                "jurisdiction": JurisdictionType.GERMAN,
                "term": "alleiniges Sorgerecht",
                "language_code": "de",
                "definition": "Ein Elternteil hat das alleinige elterliche Sorgerecht",
                "legal_basis": "BGB § 1671",
                "nuances": ["Includes both Personensorge and Vermögenssorge"],
                "usage_examples": ["Der Mutter wurde das alleinige Sorgerecht übertragen."]
            },
            {
                "jurisdiction": JurisdictionType.TURKISH,
                "term": "tek başına velayet",
                "language_code": "tr",
                "definition": "Bir ebeveynin çocuk üzerinde tek başına velayet hakkı",
                "legal_basis": "TMK Madde 336",
                "nuances": ["After divorce, custody typically goes to one parent"],
                "usage_examples": ["Velayet hakkı anneye verildi."]
            },
            {
                "jurisdiction": JurisdictionType.UK,
                "term": "sole residence order / child arrangements order",
                "language_code": "en",
                "definition": "Child lives primarily with one parent",
                "legal_basis": "Children Act 1989 s.8",
                "nuances": ["Residence orders replaced by Child Arrangements Orders in 2014"],
                "usage_examples": ["A child arrangements order was made for the child to live with the mother."]
            }
        ],
        "false_friends": ["Umgangsrecht (visitation, not custody)", "Aufenthaltsbestimmungsrecht (residence determination only)"],
        "warnings": ["German Sorgerecht encompasses more than US custody"],
        "related_terms": ["joint custody", "legal custody", "physical custody"]
    },
    {
        "term_id": "custody_002",
        "canonical_term": "joint custody",
        "domain": LegalDomain.CUSTODY,
        "definition": "Both parents share legal and/or physical custody of the child",
        "equivalents": [
            {
                "jurisdiction": JurisdictionType.GERMAN,
                "term": "gemeinsames Sorgerecht",
                "language_code": "de",
                "definition": "Beide Elternteile haben das elterliche Sorgerecht gemeinsam",
                "legal_basis": "BGB § 1626",
                "nuances": ["Default for married parents; maintained after divorce unless court decides otherwise"],
                "usage_examples": ["Die Eltern behalten das gemeinsame Sorgerecht."]
            },
            {
                "jurisdiction": JurisdictionType.TURKISH,
                "term": "ortak velayet",
                "language_code": "tr",
                "definition": "Her iki ebeveynin de velayet hakkına sahip olması",
                "legal_basis": "TMK Madde 336",
                "nuances": ["Not traditionally recognized; custody goes to one parent after divorce"],
                "usage_examples": ["Ortak velayet Türk hukukunda yaygın değildir."]
            },
            {
                "jurisdiction": JurisdictionType.UK,
                "term": "shared parental responsibility",
                "language_code": "en",
                "definition": "Both parents retain parental responsibility",
                "legal_basis": "Children Act 1989 s.2",
                "nuances": ["Parental responsibility is not lost by divorce"],
                "usage_examples": ["Both parents continue to have parental responsibility."]
            }
        ],
        "false_friends": ["Wechselmodell (alternating residence, not just shared rights)"],
        "warnings": ["Joint custody in Germany is very different from joint physical custody in US"],
        "related_terms": ["sole custody", "shared custody", "parental responsibility"]
    },
    {
        "term_id": "custody_003",
        "canonical_term": "visitation rights",
        "domain": LegalDomain.CUSTODY,
        "definition": "The right of a non-custodial parent to spend time with their child",
        "equivalents": [
            {
                "jurisdiction": JurisdictionType.GERMAN,
                "term": "Umgangsrecht",
                "language_code": "de",
                "definition": "Recht des Kindes und des nicht-betreuenden Elternteils auf Umgang",
                "legal_basis": "BGB § 1684",
                "nuances": ["Framed as child's right, not parent's right; applies to grandparents too"],
                "usage_examples": ["Das Umgangsrecht wurde auf jedes zweite Wochenende festgelegt."]
            },
            {
                "jurisdiction": JurisdictionType.TURKISH,
                "term": "kişisel ilişki kurma hakkı",
                "language_code": "tr",
                "definition": "Velayet hakkı olmayan ebeveynin çocukla görüşme hakkı",
                "legal_basis": "TMK Madde 323",
                "nuances": ["Court determines frequency and conditions"],
                "usage_examples": ["Babaya ayda iki hafta sonu kişisel ilişki hakkı tanındı."]
            },
            {
                "jurisdiction": JurisdictionType.UK,
                "term": "contact order / child arrangements order (contact)",
                "language_code": "en",
                "definition": "Order specifying time child spends with non-resident parent",
                "legal_basis": "Children Act 1989 s.8",
                "nuances": ["Contact orders replaced by Child Arrangements Orders in 2014"],
                "usage_examples": ["The father was granted contact every other weekend."]
            }
        ],
        "false_friends": ["Sorgerecht (custody, includes more than visitation)"],
        "warnings": ["German Umgangsrecht is legally the child's right, not the parent's"],
        "related_terms": ["custody", "parenting time", "access"]
    },
    {
        "term_id": "custody_004",
        "canonical_term": "parental alienation",
        "domain": LegalDomain.CUSTODY,
        "definition": "When one parent manipulates a child to reject the other parent",
        "equivalents": [
            {
                "jurisdiction": JurisdictionType.GERMAN,
                "term": "Eltern-Kind-Entfremdung",
                "language_code": "de",
                "definition": "Beeinflussung eines Kindes durch einen Elternteil gegen den anderen",
                "legal_basis": "Recognized in case law, not codified",
                "nuances": ["Courts increasingly recognize but controversial; not a medical diagnosis"],
                "usage_examples": ["Es liegen Anzeichen für eine Eltern-Kind-Entfremdung vor."]
            },
            {
                "jurisdiction": JurisdictionType.TURKISH,
                "term": "ebeveyn yabancılaştırması",
                "language_code": "tr",
                "definition": "Bir ebeveynin çocuğu diğer ebeveyne karşı olumsuz etkilemesi",
                "legal_basis": "Recognized in expert reports, not codified",
                "nuances": ["Increasingly recognized by Turkish family courts"],
                "usage_examples": ["Bilirkişi raporu ebeveyn yabancılaştırması tespit etmiştir."]
            },
            {
                "jurisdiction": JurisdictionType.UK,
                "term": "parental alienation",
                "language_code": "en",
                "definition": "A child's resistance or hostility towards a parent without legitimate justification",
                "legal_basis": "Recognized in case law; Cafcass guidance",
                "nuances": ["Courts cautious; must distinguish from legitimate estrangement"],
                "usage_examples": ["The expert found evidence of parental alienation."]
            }
        ],
        "false_friends": ["Estrangement (justified rejection vs. manipulated rejection)"],
        "warnings": ["Controversial concept; requires expert evidence; distinguish from abuse response"],
        "related_terms": ["parental interference", "custody interference", "psychological manipulation"]
    },

    # Child protection terms
    {
        "term_id": "protect_001",
        "canonical_term": "child protection order",
        "domain": LegalDomain.CHILD_PROTECTION,
        "definition": "Court order to protect a child from harm or risk of harm",
        "equivalents": [
            {
                "jurisdiction": JurisdictionType.GERMAN,
                "term": "Sorgerechtsentzug / Schutzanordnung",
                "language_code": "de",
                "definition": "Gerichtliche Maßnahmen zum Schutz des Kindeswohls",
                "legal_basis": "BGB § 1666, § 1666a",
                "nuances": ["Ranges from specific instructions to full custody removal"],
                "usage_examples": ["Das Gericht ordnete einen teilweisen Sorgerechtsentzug an."]
            },
            {
                "jurisdiction": JurisdictionType.TURKISH,
                "term": "çocuk koruma tedbiri",
                "language_code": "tr",
                "definition": "Çocuğun korunması için mahkeme tarafından alınan tedbirler",
                "legal_basis": "Çocuk Koruma Kanunu Madde 5",
                "nuances": ["Includes counseling, education, care, health, accommodation measures"],
                "usage_examples": ["Mahkeme çocuk koruma tedbiri kararı verdi."]
            },
            {
                "jurisdiction": JurisdictionType.UK,
                "term": "care order / supervision order",
                "language_code": "en",
                "definition": "Order placing child in local authority care or supervision",
                "legal_basis": "Children Act 1989 s.31",
                "nuances": ["Care order transfers parental responsibility; supervision order does not"],
                "usage_examples": ["The local authority applied for a care order."]
            }
        ],
        "false_friends": ["Emergency protection order (short-term vs. longer-term protection)"],
        "warnings": ["Different thresholds in different jurisdictions"],
        "related_terms": ["emergency protection", "interim care order", "safeguarding"]
    },
    {
        "term_id": "protect_002",
        "canonical_term": "best interests of the child",
        "domain": LegalDomain.CHILD_PROTECTION,
        "definition": "The paramount consideration in all decisions affecting children",
        "equivalents": [
            {
                "jurisdiction": JurisdictionType.GERMAN,
                "term": "Kindeswohl",
                "language_code": "de",
                "definition": "Das körperliche, geistige und seelische Wohl des Kindes",
                "legal_basis": "BGB § 1697a; UN-Kinderrechtskonvention Art. 3",
                "nuances": ["Central concept in all family court decisions; includes stability, attachment, child's will"],
                "usage_examples": ["Das Kindeswohl ist der Maßstab aller Entscheidungen."]
            },
            {
                "jurisdiction": JurisdictionType.TURKISH,
                "term": "çocuğun üstün yararı",
                "language_code": "tr",
                "definition": "Çocukla ilgili tüm kararlarda öncelikli olarak gözetilmesi gereken çocuğun yararı",
                "legal_basis": "TMK Madde 339; UN Çocuk Hakları Sözleşmesi Madde 3",
                "nuances": ["Primary consideration in custody decisions"],
                "usage_examples": ["Karar çocuğun üstün yararı gözetilerek verilmiştir."]
            },
            {
                "jurisdiction": JurisdictionType.UK,
                "term": "welfare of the child / best interests",
                "language_code": "en",
                "definition": "The child's welfare shall be the court's paramount consideration",
                "legal_basis": "Children Act 1989 s.1",
                "nuances": ["Welfare checklist in s.1(3) provides factors to consider"],
                "usage_examples": ["The court applied the welfare checklist."]
            }
        ],
        "false_friends": [],
        "warnings": ["Factors considered vary by jurisdiction; check local welfare checklist"],
        "related_terms": ["welfare checklist", "child's wishes", "harm assessment"]
    },

    # Domestic violence terms
    {
        "term_id": "dv_001",
        "canonical_term": "protection order",
        "domain": LegalDomain.DOMESTIC_VIOLENCE,
        "definition": "Court order prohibiting contact or proximity to protected person",
        "equivalents": [
            {
                "jurisdiction": JurisdictionType.GERMAN,
                "term": "Gewaltschutzanordnung",
                "language_code": "de",
                "definition": "Gerichtliche Anordnung zum Schutz vor Gewalt und Nachstellung",
                "legal_basis": "GewSchG § 1, § 2",
                "nuances": ["Can include residence assignment, contact prohibition, proximity ban"],
                "usage_examples": ["Es wurde eine Gewaltschutzanordnung mit Kontaktverbot erlassen."]
            },
            {
                "jurisdiction": JurisdictionType.TURKISH,
                "term": "koruma kararı / uzaklaştırma kararı",
                "language_code": "tr",
                "definition": "Aile içi şiddetten koruma için verilen tedbir kararı",
                "legal_basis": "6284 sayılı Kanun",
                "nuances": ["Can be issued immediately by police or prosecutor; court confirmation required"],
                "usage_examples": ["Savcılık tarafından koruma kararı verildi."]
            },
            {
                "jurisdiction": JurisdictionType.UK,
                "term": "non-molestation order / occupation order",
                "language_code": "en",
                "definition": "Order prohibiting harassment/violence or regulating home occupation",
                "legal_basis": "Family Law Act 1996 Part IV",
                "nuances": ["Non-molestation for behavior; occupation order for home rights"],
                "usage_examples": ["The court granted a non-molestation order."]
            },
            {
                "jurisdiction": JurisdictionType.US,
                "term": "restraining order / protective order",
                "language_code": "en",
                "definition": "Court order restricting contact and proximity",
                "legal_basis": "Varies by state",
                "nuances": ["Emergency, temporary, and permanent orders available"],
                "usage_examples": ["She obtained a temporary restraining order."]
            }
        ],
        "false_friends": ["Peace bond (Canadian term)", "Apprehended violence order (Australian term)"],
        "warnings": ["Terminology varies significantly between jurisdictions"],
        "related_terms": ["no-contact order", "restraining order", "emergency protection"]
    },

    # International terms
    {
        "term_id": "intl_001",
        "canonical_term": "international child abduction",
        "domain": LegalDomain.INTERNATIONAL,
        "definition": "Wrongful removal or retention of a child across international borders",
        "equivalents": [
            {
                "jurisdiction": JurisdictionType.GERMAN,
                "term": "internationale Kindesentführung",
                "language_code": "de",
                "definition": "Widerrechtliches Verbringen oder Zurückhalten eines Kindes über Staatsgrenzen",
                "legal_basis": "Haager Kindesentführungsübereinkommen (HKÜ); IntFamRVG",
                "nuances": ["Central authority is Bundesamt für Justiz"],
                "usage_examples": ["Es liegt ein Fall internationaler Kindesentführung vor."]
            },
            {
                "jurisdiction": JurisdictionType.TURKISH,
                "term": "uluslararası çocuk kaçırma",
                "language_code": "tr",
                "definition": "Çocuğun uluslararası sınırlar ötesine hukuka aykırı götürülmesi veya alıkonulması",
                "legal_basis": "Lahey Çocuk Kaçırma Sözleşmesi; 5717 sayılı Kanun",
                "nuances": ["Turkey is a contracting state since 2000"],
                "usage_examples": ["Uluslararası çocuk kaçırma davası açıldı."]
            },
            {
                "jurisdiction": JurisdictionType.EU,
                "term": "wrongful removal or retention",
                "language_code": "en",
                "definition": "Removal/retention breaching custody rights under Brussels IIa",
                "legal_basis": "Brussels IIa/IIb Regulation; Hague Convention 1980",
                "nuances": ["Enhanced procedures within EU; Article 11 provisions"],
                "usage_examples": ["The court ordered immediate return under Brussels IIa."]
            }
        ],
        "false_friends": ["Kidnapping (criminal term)", "Custody violation (may be domestic)"],
        "warnings": ["Time-sensitive; 1-year period for automatic return; grave risk exception exists"],
        "related_terms": ["habitual residence", "custody rights", "return order"]
    },
    {
        "term_id": "intl_002",
        "canonical_term": "habitual residence",
        "domain": LegalDomain.INTERNATIONAL,
        "definition": "The country where a child has their established life and connections",
        "equivalents": [
            {
                "jurisdiction": JurisdictionType.GERMAN,
                "term": "gewöhnlicher Aufenthalt",
                "language_code": "de",
                "definition": "Der Ort, an dem sich der Daseinsmittelpunkt des Kindes befindet",
                "legal_basis": "EU-Recht; HKÜ",
                "nuances": ["Factual concept, not domicile; social integration is key"],
                "usage_examples": ["Der gewöhnliche Aufenthalt des Kindes ist in Deutschland."]
            },
            {
                "jurisdiction": JurisdictionType.TURKISH,
                "term": "mutat mesken",
                "language_code": "tr",
                "definition": "Çocuğun yaşam merkezinin bulunduğu yer",
                "legal_basis": "MÖHUK; Lahey Sözleşmeleri",
                "nuances": ["Determined by actual life circumstances, not registration"],
                "usage_examples": ["Çocuğun mutat meskeni Türkiye olarak belirlendi."]
            },
            {
                "jurisdiction": JurisdictionType.EU,
                "term": "habitual residence",
                "language_code": "en",
                "definition": "Place which reflects some degree of integration in a social and family environment",
                "legal_basis": "CJEU case law; Brussels IIa/IIb",
                "nuances": ["CJEU: focus on child's situation, not parents' intentions"],
                "usage_examples": ["The court determined habitual residence based on the child's integration."]
            }
        ],
        "false_friends": ["Domicile (legal concept, not same)", "Nationality (irrelevant for HR)"],
        "warnings": ["Critical for jurisdiction; can change quickly for young children"],
        "related_terms": ["jurisdiction", "international child abduction", "forum"]
    },

    # Evidence terms
    {
        "term_id": "evid_001",
        "canonical_term": "expert witness",
        "domain": LegalDomain.EVIDENCE,
        "definition": "A person with specialized knowledge who provides expert opinion to court",
        "equivalents": [
            {
                "jurisdiction": JurisdictionType.GERMAN,
                "term": "Sachverständiger / Gutachter",
                "language_code": "de",
                "definition": "Person mit besonderer Sachkunde, die dem Gericht Gutachten erstattet",
                "legal_basis": "ZPO § 402ff; FamFG § 30",
                "nuances": ["Court-appointed Gutachter in family cases; private experts less common"],
                "usage_examples": ["Das Gericht bestellte einen psychologischen Sachverständigen."]
            },
            {
                "jurisdiction": JurisdictionType.TURKISH,
                "term": "bilirkişi",
                "language_code": "tr",
                "definition": "Uzmanlık gerektiren konularda mahkemeye görüş bildiren uzman",
                "legal_basis": "HMK Madde 266-287",
                "nuances": ["Court selects from official expert lists"],
                "usage_examples": ["Mahkeme sosyal hizmet uzmanı bilirkişi atadı."]
            },
            {
                "jurisdiction": JurisdictionType.UK,
                "term": "expert witness",
                "language_code": "en",
                "definition": "Person qualified to give expert opinion evidence",
                "legal_basis": "Family Procedure Rules Part 25",
                "nuances": ["Single joint expert preferred in family cases"],
                "usage_examples": ["The court gave permission for a single joint expert."]
            }
        ],
        "false_friends": ["Witness (regular witness vs. expert)", "Consultant (not giving evidence)"],
        "warnings": ["Expert's duty is to the court, not the instructing party"],
        "related_terms": ["expert report", "assessment", "psychological evaluation"]
    },
    {
        "term_id": "evid_002",
        "canonical_term": "digital evidence",
        "domain": LegalDomain.EVIDENCE,
        "definition": "Evidence derived from electronic devices or digital communications",
        "equivalents": [
            {
                "jurisdiction": JurisdictionType.GERMAN,
                "term": "digitale Beweismittel / elektronische Beweise",
                "language_code": "de",
                "definition": "Beweismittel aus elektronischen Geräten oder digitaler Kommunikation",
                "legal_basis": "ZPO § 371 (Augenschein); case law",
                "nuances": ["Authentication and integrity requirements; chain of custody important"],
                "usage_examples": ["Die WhatsApp-Nachrichten wurden als digitale Beweismittel vorgelegt."]
            },
            {
                "jurisdiction": JurisdictionType.TURKISH,
                "term": "dijital delil / elektronik delil",
                "language_code": "tr",
                "definition": "Elektronik cihazlardan veya dijital iletişimden elde edilen deliller",
                "legal_basis": "HMK Madde 199 (belge); CMK elektronik delil hükümleri",
                "nuances": ["Authenticity must be established; expert verification often required"],
                "usage_examples": ["Mesajların dijital delil olarak kabul edilmesi talep edildi."]
            },
            {
                "jurisdiction": JurisdictionType.UK,
                "term": "digital evidence / electronic evidence",
                "language_code": "en",
                "definition": "Information stored or transmitted in digital form",
                "legal_basis": "Civil Evidence Act 1995; case law",
                "nuances": ["Hearsay rules relaxed; authenticity and weight considerations"],
                "usage_examples": ["The court admitted the text messages as digital evidence."]
            }
        ],
        "false_friends": [],
        "warnings": ["Privacy laws may restrict use; obtain legally; preserve metadata"],
        "related_terms": ["chain of custody", "authentication", "forensic analysis"]
    }
]


class LegalTerminology:
    """Cross-jurisdictional legal terminology service."""

    def __init__(self):
        self.terms: Dict[str, LegalTerm] = {}
        self.jurisdictions: Dict[JurisdictionType, JurisdictionContext] = {}
        self._load_data()

    def _load_data(self):
        """Load terminology and jurisdiction data."""
        # Load jurisdiction contexts
        for jtype, data in JURISDICTION_CONTEXTS.items():
            self.jurisdictions[jtype] = JurisdictionContext(
                jurisdiction=data["jurisdiction"],
                language_code=data["language_code"],
                legal_system=data["legal_system"],
                family_court_name=data["family_court_name"],
                custody_authority=data["custody_authority"],
                child_protection_agency=data["child_protection_agency"],
                key_legislation=data["key_legislation"],
                court_levels=data["court_levels"],
                appeal_process=data["appeal_process"]
            )

        # Load legal terms
        for data in LEGAL_TERMS:
            equivalents = []
            for eq_data in data["equivalents"]:
                equiv = TermEquivalent(
                    jurisdiction=eq_data["jurisdiction"],
                    term=eq_data["term"],
                    language_code=eq_data["language_code"],
                    definition=eq_data["definition"],
                    legal_basis=eq_data["legal_basis"],
                    nuances=eq_data["nuances"],
                    usage_examples=eq_data["usage_examples"]
                )
                equivalents.append(equiv)

            term = LegalTerm(
                term_id=data["term_id"],
                canonical_term=data["canonical_term"],
                domain=data["domain"],
                definition=data["definition"],
                equivalents=equivalents,
                false_friends=data["false_friends"],
                warnings=data["warnings"],
                related_terms=data["related_terms"]
            )
            self.terms[term.term_id] = term

    def get_term(self, term_id: str) -> Optional[LegalTerm]:
        """Get a legal term by ID."""
        return self.terms.get(term_id)

    def search_terms(
        self,
        query: str,
        domain: Optional[LegalDomain] = None
    ) -> List[LegalTerm]:
        """Search for legal terms matching a query."""
        query_lower = query.lower()
        results = []

        for term in self.terms.values():
            # Check canonical term
            if query_lower in term.canonical_term.lower():
                if domain is None or term.domain == domain:
                    results.append(term)
                continue

            # Check equivalents
            for equiv in term.equivalents:
                if query_lower in equiv.term.lower():
                    if domain is None or term.domain == domain:
                        results.append(term)
                    break

        return results

    def translate_term(
        self,
        term_text: str,
        source_jurisdiction: JurisdictionType,
        target_jurisdiction: JurisdictionType
    ) -> Optional[TermTranslation]:
        """Translate a legal term between jurisdictions."""
        # Find matching term
        term_lower = term_text.lower()
        matching_term: Optional[LegalTerm] = None
        source_equiv: Optional[TermEquivalent] = None

        for term in self.terms.values():
            # Check if it matches canonical term
            if term_lower == term.canonical_term.lower():
                matching_term = term
                break

            # Check equivalents
            for equiv in term.equivalents:
                if term_lower == equiv.term.lower() and equiv.jurisdiction == source_jurisdiction:
                    matching_term = term
                    source_equiv = equiv
                    break

            if matching_term:
                break

        if not matching_term:
            return None

        # Find target equivalent
        target_equiv: Optional[TermEquivalent] = None
        for equiv in matching_term.equivalents:
            if equiv.jurisdiction == target_jurisdiction:
                target_equiv = equiv
                break

        if not target_equiv:
            return None

        # Build translation
        warnings = list(matching_term.warnings)

        # Add nuance warnings
        if target_equiv.nuances:
            warnings.extend([f"Note: {n}" for n in target_equiv.nuances])

        # Check for false friends
        false_friend_warning = None
        for ff in matching_term.false_friends:
            if any(ff.lower() in term_text.lower() for _ in [True]):
                false_friend_warning = f"Warning: '{ff}' is a false friend - similar term with different meaning"
                break

        return TermTranslation(
            original_term=term_text,
            translated_term=target_equiv.term,
            source_jurisdiction=source_jurisdiction,
            target_jurisdiction=target_jurisdiction,
            confidence=0.9,
            warnings=warnings,
            explanation=target_equiv.definition,
            legal_basis=target_equiv.legal_basis,
            false_friends_warning=false_friend_warning
        )

    def get_jurisdiction_context(
        self,
        jurisdiction: JurisdictionType
    ) -> Optional[JurisdictionContext]:
        """Get context information for a jurisdiction."""
        return self.jurisdictions.get(jurisdiction)

    def get_terms_by_domain(
        self,
        domain: LegalDomain
    ) -> List[LegalTerm]:
        """Get all terms in a specific legal domain."""
        return [t for t in self.terms.values() if t.domain == domain]

    def generate_glossary(
        self,
        source_jurisdiction: JurisdictionType,
        target_jurisdiction: JurisdictionType,
        domain: Optional[LegalDomain] = None
    ) -> str:
        """Generate a bilingual legal glossary."""
        terms = self.terms.values()
        if domain:
            terms = [t for t in terms if t.domain == domain]

        source_ctx = self.jurisdictions.get(source_jurisdiction)
        target_ctx = self.jurisdictions.get(target_jurisdiction)

        if not source_ctx or not target_ctx:
            return "Jurisdiction not found"

        lines = [
            f"LEGAL GLOSSARY",
            f"From: {source_jurisdiction.value.upper()} ({source_ctx.language_code})",
            f"To: {target_jurisdiction.value.upper()} ({target_ctx.language_code})",
            "=" * 60,
            ""
        ]

        for term in terms:
            source_equiv = None
            target_equiv = None

            for equiv in term.equivalents:
                if equiv.jurisdiction == source_jurisdiction:
                    source_equiv = equiv
                if equiv.jurisdiction == target_jurisdiction:
                    target_equiv = equiv

            if source_equiv and target_equiv:
                lines.extend([
                    f"[{term.domain.value.upper()}]",
                    f"  {source_equiv.term}",
                    f"  → {target_equiv.term}",
                    f"  Definition: {target_equiv.definition}",
                    f"  Legal basis: {target_equiv.legal_basis}",
                    ""
                ])

                if term.warnings:
                    lines.append(f"  ⚠️ {'; '.join(term.warnings)}")
                    lines.append("")

        return "\n".join(lines)

    def get_court_info(
        self,
        jurisdiction: JurisdictionType
    ) -> Dict[str, Any]:
        """Get court and authority information for a jurisdiction."""
        ctx = self.jurisdictions.get(jurisdiction)
        if not ctx:
            return {}

        return {
            "family_court": ctx.family_court_name,
            "custody_authority": ctx.custody_authority,
            "child_protection_agency": ctx.child_protection_agency,
            "court_levels": ctx.court_levels,
            "appeal_process": ctx.appeal_process,
            "key_legislation": ctx.key_legislation,
            "legal_system": ctx.legal_system
        }

    def compare_concepts(
        self,
        term_id: str,
        jurisdictions: List[JurisdictionType]
    ) -> Dict[str, Any]:
        """Compare how a legal concept works across jurisdictions."""
        term = self.terms.get(term_id)
        if not term:
            return {}

        comparison = {
            "concept": term.canonical_term,
            "definition": term.definition,
            "jurisdictions": {}
        }

        for jtype in jurisdictions:
            for equiv in term.equivalents:
                if equiv.jurisdiction == jtype:
                    comparison["jurisdictions"][jtype.value] = {
                        "term": equiv.term,
                        "language": equiv.language_code,
                        "definition": equiv.definition,
                        "legal_basis": equiv.legal_basis,
                        "nuances": equiv.nuances,
                        "examples": equiv.usage_examples
                    }
                    break

        comparison["warnings"] = term.warnings
        comparison["false_friends"] = term.false_friends

        return comparison
