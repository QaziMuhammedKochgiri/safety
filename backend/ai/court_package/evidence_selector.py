"""
Evidence Selector
Smart evidence selection wizard for court package preparation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set, Callable
from enum import Enum
from datetime import datetime, timedelta
import hashlib


class EvidenceCategory(str, Enum):
    """Categories of evidence for family court."""
    COMMUNICATION = "communication"  # Messages, emails, chats
    AUDIO_VIDEO = "audio_video"  # Recordings, videos
    DOCUMENT = "document"  # Contracts, letters, official docs
    PHOTOGRAPH = "photograph"  # Photos of injuries, property, etc.
    FINANCIAL = "financial"  # Bank statements, receipts
    MEDICAL = "medical"  # Medical records, psych evaluations
    EDUCATIONAL = "educational"  # School records, grades
    WITNESS = "witness"  # Witness statements, affidavits
    EXPERT = "expert"  # Expert reports, evaluations
    LOCATION = "location"  # GPS data, check-ins
    SOCIAL_MEDIA = "social_media"  # Social media posts
    OFFICIAL = "official"  # Court orders, police reports


class EvidenceType(str, Enum):
    """Specific types of evidence."""
    # Communication
    TEXT_MESSAGE = "text_message"
    WHATSAPP_MESSAGE = "whatsapp_message"
    EMAIL = "email"
    VOICE_MESSAGE = "voice_message"

    # Audio/Video
    AUDIO_RECORDING = "audio_recording"
    VIDEO_RECORDING = "video_recording"
    SCREENSHOT = "screenshot"

    # Documents
    CUSTODY_AGREEMENT = "custody_agreement"
    COURT_ORDER = "court_order"
    POLICE_REPORT = "police_report"
    RESTRAINING_ORDER = "restraining_order"

    # Expert
    PSYCHOLOGICAL_EVALUATION = "psychological_evaluation"
    GUARDIAN_AD_LITEM_REPORT = "guardian_ad_litem_report"
    SOCIAL_WORKER_REPORT = "social_worker_report"

    # Financial
    BANK_STATEMENT = "bank_statement"
    TAX_RETURN = "tax_return"
    PAY_STUB = "pay_stub"

    # Medical
    MEDICAL_RECORD = "medical_record"
    THERAPY_NOTES = "therapy_notes"
    PRESCRIPTION = "prescription"


class LegalIssue(str, Enum):
    """Legal issues in family court cases."""
    CUSTODY = "custody"
    VISITATION = "visitation"
    PARENTAL_ALIENATION = "parental_alienation"
    DOMESTIC_VIOLENCE = "domestic_violence"
    CHILD_ABUSE = "child_abuse"
    CHILD_NEGLECT = "child_neglect"
    SUBSTANCE_ABUSE = "substance_abuse"
    MENTAL_HEALTH = "mental_health"
    RELOCATION = "relocation"
    CHILD_SUPPORT = "child_support"
    PARENTAL_FITNESS = "parental_fitness"
    INTERFERENCE = "interference"


@dataclass
class EvidenceItem:
    """A single piece of evidence."""
    item_id: str
    title: str
    description: str
    category: EvidenceCategory
    evidence_type: EvidenceType
    source: str  # WhatsApp, Email, etc.
    date_created: datetime
    date_collected: datetime
    content: Optional[str] = None
    file_path: Optional[str] = None
    file_size_bytes: int = 0
    content_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    participants: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    legal_issues: List[LegalIssue] = field(default_factory=list)
    is_authenticated: bool = False
    authentication_method: Optional[str] = None
    chain_of_custody: List[Dict[str, Any]] = field(default_factory=list)
    estimated_pages: int = 1
    language: str = "en"
    requires_translation: bool = False


@dataclass
class SelectionCriteria:
    """Criteria for evidence selection."""
    case_id: str
    target_legal_issues: List[LegalIssue]
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    required_categories: List[EvidenceCategory] = field(default_factory=list)
    excluded_categories: List[EvidenceCategory] = field(default_factory=list)
    required_participants: List[str] = field(default_factory=list)
    max_items: int = 100
    max_pages: int = 500
    prioritize_recent: bool = True
    prioritize_authenticated: bool = True
    include_expert_reports: bool = True
    include_witness_statements: bool = True
    relevance_threshold: float = 0.3
    court_format: str = "german"  # german, turkish, eu_e001


@dataclass
class SelectionResult:
    """Result of evidence selection."""
    case_id: str
    selected_items: List[EvidenceItem]
    excluded_items: List[EvidenceItem]
    total_pages: int
    total_size_bytes: int
    by_category: Dict[EvidenceCategory, List[str]]
    by_legal_issue: Dict[LegalIssue, List[str]]
    selection_reasons: Dict[str, str]
    exclusion_reasons: Dict[str, str]
    warnings: List[str]
    recommendations: List[str]
    created_at: datetime


# Evidence relevance by legal issue
LEGAL_ISSUE_EVIDENCE_MAP: Dict[LegalIssue, Dict[str, Any]] = {
    LegalIssue.PARENTAL_ALIENATION: {
        "high_relevance": [
            EvidenceCategory.COMMUNICATION,
            EvidenceCategory.EXPERT,
            EvidenceCategory.WITNESS
        ],
        "keywords": [
            "alienation", "badmouth", "poison", "against", "hate",
            "don't see", "won't allow", "refuse", "block"
        ],
        "evidence_types": [
            EvidenceType.TEXT_MESSAGE,
            EvidenceType.WHATSAPP_MESSAGE,
            EvidenceType.EMAIL,
            EvidenceType.PSYCHOLOGICAL_EVALUATION
        ]
    },
    LegalIssue.DOMESTIC_VIOLENCE: {
        "high_relevance": [
            EvidenceCategory.MEDICAL,
            EvidenceCategory.PHOTOGRAPH,
            EvidenceCategory.OFFICIAL
        ],
        "keywords": [
            "hit", "hurt", "abuse", "threat", "scared", "violence",
            "bruise", "injury", "attack", "hospital"
        ],
        "evidence_types": [
            EvidenceType.MEDICAL_RECORD,
            EvidenceType.POLICE_REPORT,
            EvidenceType.RESTRAINING_ORDER,
            EvidenceType.PHOTOGRAPH
        ]
    },
    LegalIssue.CHILD_ABUSE: {
        "high_relevance": [
            EvidenceCategory.MEDICAL,
            EvidenceCategory.EXPERT,
            EvidenceCategory.OFFICIAL
        ],
        "keywords": [
            "abuse", "molest", "inappropriate", "hurt child",
            "harm", "discipline", "punishment"
        ],
        "evidence_types": [
            EvidenceType.MEDICAL_RECORD,
            EvidenceType.SOCIAL_WORKER_REPORT,
            EvidenceType.PSYCHOLOGICAL_EVALUATION,
            EvidenceType.POLICE_REPORT
        ]
    },
    LegalIssue.CUSTODY: {
        "high_relevance": [
            EvidenceCategory.DOCUMENT,
            EvidenceCategory.EXPERT,
            EvidenceCategory.EDUCATIONAL
        ],
        "keywords": [
            "custody", "care", "primary", "joint", "sole",
            "parenting", "schedule", "time"
        ],
        "evidence_types": [
            EvidenceType.CUSTODY_AGREEMENT,
            EvidenceType.COURT_ORDER,
            EvidenceType.GUARDIAN_AD_LITEM_REPORT
        ]
    },
    LegalIssue.VISITATION: {
        "high_relevance": [
            EvidenceCategory.COMMUNICATION,
            EvidenceCategory.DOCUMENT,
            EvidenceCategory.LOCATION
        ],
        "keywords": [
            "visit", "pickup", "drop off", "weekend",
            "holiday", "schedule", "missed", "denied"
        ],
        "evidence_types": [
            EvidenceType.TEXT_MESSAGE,
            EvidenceType.EMAIL,
            EvidenceType.CUSTODY_AGREEMENT
        ]
    },
    LegalIssue.SUBSTANCE_ABUSE: {
        "high_relevance": [
            EvidenceCategory.MEDICAL,
            EvidenceCategory.PHOTOGRAPH,
            EvidenceCategory.WITNESS
        ],
        "keywords": [
            "drunk", "high", "drugs", "alcohol", "addict",
            "rehab", "intoxicated", "substance"
        ],
        "evidence_types": [
            EvidenceType.MEDICAL_RECORD,
            EvidenceType.PHOTOGRAPH,
            EvidenceType.POLICE_REPORT
        ]
    },
    LegalIssue.CHILD_NEGLECT: {
        "high_relevance": [
            EvidenceCategory.PHOTOGRAPH,
            EvidenceCategory.MEDICAL,
            EvidenceCategory.EDUCATIONAL
        ],
        "keywords": [
            "neglect", "hungry", "dirty", "unsafe", "supervision",
            "alone", "abandoned", "unsupervised"
        ],
        "evidence_types": [
            EvidenceType.PHOTOGRAPH,
            EvidenceType.MEDICAL_RECORD,
            EvidenceType.SOCIAL_WORKER_REPORT
        ]
    },
    LegalIssue.INTERFERENCE: {
        "high_relevance": [
            EvidenceCategory.COMMUNICATION,
            EvidenceCategory.DOCUMENT,
            EvidenceCategory.LOCATION
        ],
        "keywords": [
            "interfere", "block", "prevent", "stop", "won't let",
            "denied", "refused", "withheld"
        ],
        "evidence_types": [
            EvidenceType.TEXT_MESSAGE,
            EvidenceType.EMAIL,
            EvidenceType.WHATSAPP_MESSAGE
        ]
    }
}


class EvidenceSelector:
    """Smart evidence selection for court packages."""

    def __init__(self):
        self.evidence_pool: Dict[str, EvidenceItem] = {}
        self.selection_history: List[SelectionResult] = []

    def add_evidence(self, item: EvidenceItem) -> str:
        """Add evidence to the pool."""
        # Generate hash if not provided
        if not item.content_hash and item.content:
            item.content_hash = hashlib.sha256(
                item.content.encode()
            ).hexdigest()

        self.evidence_pool[item.item_id] = item
        return item.item_id

    def add_evidence_batch(self, items: List[EvidenceItem]) -> int:
        """Add multiple evidence items."""
        count = 0
        for item in items:
            self.add_evidence(item)
            count += 1
        return count

    def select_evidence(
        self,
        criteria: SelectionCriteria
    ) -> SelectionResult:
        """Select evidence based on criteria."""
        selected: List[EvidenceItem] = []
        excluded: List[EvidenceItem] = []
        selection_reasons: Dict[str, str] = {}
        exclusion_reasons: Dict[str, str] = {}
        warnings: List[str] = []
        recommendations: List[str] = []

        # Score all evidence
        scored_items: List[tuple] = []

        for item_id, item in self.evidence_pool.items():
            # Check exclusion criteria first
            exclusion = self._check_exclusion(item, criteria)
            if exclusion:
                excluded.append(item)
                exclusion_reasons[item_id] = exclusion
                continue

            # Calculate relevance score
            score, reason = self._calculate_relevance_score(item, criteria)

            if score >= criteria.relevance_threshold:
                scored_items.append((item, score, reason))
            else:
                excluded.append(item)
                exclusion_reasons[item_id] = f"Below relevance threshold ({score:.2f} < {criteria.relevance_threshold})"

        # Sort by score (descending)
        scored_items.sort(key=lambda x: x[1], reverse=True)

        # Select items within limits
        total_pages = 0
        for item, score, reason in scored_items:
            if len(selected) >= criteria.max_items:
                excluded.append(item)
                exclusion_reasons[item.item_id] = f"Max items limit reached ({criteria.max_items})"
                continue

            if total_pages + item.estimated_pages > criteria.max_pages:
                excluded.append(item)
                exclusion_reasons[item.item_id] = f"Page limit would be exceeded ({total_pages + item.estimated_pages} > {criteria.max_pages})"
                continue

            selected.append(item)
            selection_reasons[item.item_id] = reason
            total_pages += item.estimated_pages

        # Generate warnings and recommendations
        warnings, recommendations = self._generate_insights(
            selected, excluded, criteria
        )

        # Build result
        result = SelectionResult(
            case_id=criteria.case_id,
            selected_items=selected,
            excluded_items=excluded,
            total_pages=total_pages,
            total_size_bytes=sum(i.file_size_bytes for i in selected),
            by_category=self._group_by_category(selected),
            by_legal_issue=self._group_by_legal_issue(selected),
            selection_reasons=selection_reasons,
            exclusion_reasons=exclusion_reasons,
            warnings=warnings,
            recommendations=recommendations,
            created_at=datetime.utcnow()
        )

        self.selection_history.append(result)
        return result

    def _check_exclusion(
        self,
        item: EvidenceItem,
        criteria: SelectionCriteria
    ) -> Optional[str]:
        """Check if item should be excluded."""
        # Category exclusion
        if item.category in criteria.excluded_categories:
            return f"Category '{item.category.value}' is excluded"

        # Date range check
        if criteria.date_range_start and item.date_created < criteria.date_range_start:
            return f"Before date range ({item.date_created.date()} < {criteria.date_range_start.date()})"

        if criteria.date_range_end and item.date_created > criteria.date_range_end:
            return f"After date range ({item.date_created.date()} > {criteria.date_range_end.date()})"

        return None

    def _calculate_relevance_score(
        self,
        item: EvidenceItem,
        criteria: SelectionCriteria
    ) -> tuple:
        """Calculate relevance score for an evidence item."""
        score = 0.0
        reasons = []

        # Base score for matching legal issues
        matching_issues = set(item.legal_issues) & set(criteria.target_legal_issues)
        if matching_issues:
            issue_score = len(matching_issues) * 0.2
            score += min(issue_score, 0.4)
            reasons.append(f"Matches issues: {', '.join(i.value for i in matching_issues)}")

        # Category relevance
        for issue in criteria.target_legal_issues:
            issue_config = LEGAL_ISSUE_EVIDENCE_MAP.get(issue, {})
            high_relevance_cats = issue_config.get("high_relevance", [])

            if item.category in high_relevance_cats:
                score += 0.15
                reasons.append(f"High-relevance category for {issue.value}")
                break

        # Evidence type bonus
        for issue in criteria.target_legal_issues:
            issue_config = LEGAL_ISSUE_EVIDENCE_MAP.get(issue, {})
            relevant_types = issue_config.get("evidence_types", [])

            if item.evidence_type in relevant_types:
                score += 0.1
                reasons.append(f"Relevant evidence type: {item.evidence_type.value}")
                break

        # Keyword matching
        if item.content:
            content_lower = item.content.lower()
            for issue in criteria.target_legal_issues:
                issue_config = LEGAL_ISSUE_EVIDENCE_MAP.get(issue, {})
                keywords = issue_config.get("keywords", [])

                matched_keywords = [kw for kw in keywords if kw.lower() in content_lower]
                if matched_keywords:
                    keyword_score = min(len(matched_keywords) * 0.05, 0.2)
                    score += keyword_score
                    reasons.append(f"Keywords: {', '.join(matched_keywords[:3])}")

        # Required participant bonus
        if criteria.required_participants:
            matching_participants = set(item.participants) & set(criteria.required_participants)
            if matching_participants:
                score += 0.1
                reasons.append(f"Involves: {', '.join(matching_participants)}")

        # Required category bonus
        if item.category in criteria.required_categories:
            score += 0.15
            reasons.append(f"Required category: {item.category.value}")

        # Authentication bonus
        if item.is_authenticated and criteria.prioritize_authenticated:
            score += 0.1
            reasons.append("Authenticated evidence")

        # Recency bonus
        if criteria.prioritize_recent:
            days_old = (datetime.utcnow() - item.date_created).days
            if days_old <= 30:
                score += 0.1
                reasons.append("Recent evidence (< 30 days)")
            elif days_old <= 90:
                score += 0.05
                reasons.append("Fairly recent (< 90 days)")

        # Expert report bonus
        if item.category == EvidenceCategory.EXPERT and criteria.include_expert_reports:
            score += 0.15
            reasons.append("Expert report")

        # Witness statement bonus
        if item.category == EvidenceCategory.WITNESS and criteria.include_witness_statements:
            score += 0.1
            reasons.append("Witness statement")

        # Cap score at 1.0
        score = min(score, 1.0)

        reason_text = "; ".join(reasons) if reasons else "Base relevance"
        return score, reason_text

    def _generate_insights(
        self,
        selected: List[EvidenceItem],
        excluded: List[EvidenceItem],
        criteria: SelectionCriteria
    ) -> tuple:
        """Generate warnings and recommendations."""
        warnings = []
        recommendations = []

        # Check for category gaps
        selected_categories = {item.category for item in selected}

        if EvidenceCategory.EXPERT not in selected_categories:
            if any(issue in criteria.target_legal_issues for issue in [
                LegalIssue.PARENTAL_ALIENATION,
                LegalIssue.CHILD_ABUSE,
                LegalIssue.MENTAL_HEALTH
            ]):
                warnings.append(
                    "No expert reports selected. Consider obtaining psychological evaluation."
                )

        if EvidenceCategory.OFFICIAL not in selected_categories:
            if LegalIssue.DOMESTIC_VIOLENCE in criteria.target_legal_issues:
                warnings.append(
                    "No official documents (police reports) selected for domestic violence claim."
                )

        # Check for authentication issues
        unauthenticated = [
            item for item in selected
            if not item.is_authenticated
        ]
        if len(unauthenticated) > len(selected) * 0.5:
            warnings.append(
                f"{len(unauthenticated)} of {len(selected)} items lack authentication. "
                "Consider authenticating key evidence."
            )

        # Check for translation needs
        translation_needed = [
            item for item in selected
            if item.requires_translation
        ]
        if translation_needed:
            warnings.append(
                f"{len(translation_needed)} items require certified translation."
            )

        # Check time gaps
        if selected:
            dates = sorted([item.date_created for item in selected])
            for i in range(1, len(dates)):
                gap = (dates[i] - dates[i-1]).days
                if gap > 90:
                    warnings.append(
                        f"Gap of {gap} days in evidence timeline "
                        f"({dates[i-1].date()} to {dates[i].date()})"
                    )
                    break

        # Recommendations
        if len(selected) < 10:
            recommendations.append(
                "Consider collecting more evidence to strengthen the case."
            )

        if not any(item.evidence_type == EvidenceType.TEXT_MESSAGE for item in selected):
            if LegalIssue.PARENTAL_ALIENATION in criteria.target_legal_issues:
                recommendations.append(
                    "Text message evidence is crucial for parental alienation claims."
                )

        # Check legal issue coverage
        covered_issues = set()
        for item in selected:
            covered_issues.update(item.legal_issues)

        uncovered = set(criteria.target_legal_issues) - covered_issues
        if uncovered:
            recommendations.append(
                f"No direct evidence for: {', '.join(i.value for i in uncovered)}. "
                "Consider gathering supporting evidence."
            )

        return warnings, recommendations

    def _group_by_category(
        self,
        items: List[EvidenceItem]
    ) -> Dict[EvidenceCategory, List[str]]:
        """Group evidence IDs by category."""
        result: Dict[EvidenceCategory, List[str]] = {}
        for item in items:
            if item.category not in result:
                result[item.category] = []
            result[item.category].append(item.item_id)
        return result

    def _group_by_legal_issue(
        self,
        items: List[EvidenceItem]
    ) -> Dict[LegalIssue, List[str]]:
        """Group evidence IDs by legal issue."""
        result: Dict[LegalIssue, List[str]] = {}
        for item in items:
            for issue in item.legal_issues:
                if issue not in result:
                    result[issue] = []
                result[issue].append(item.item_id)
        return result

    def get_selection_wizard_steps(
        self,
        criteria: SelectionCriteria
    ) -> List[Dict[str, Any]]:
        """Generate wizard steps for evidence selection UI."""
        steps = [
            {
                "step": 1,
                "title": {
                    "en": "Select Legal Issues",
                    "de": "Rechtliche Fragen auswählen",
                    "tr": "Hukuki Konuları Seçin"
                },
                "description": {
                    "en": "What legal issues are you addressing?",
                    "de": "Welche rechtlichen Fragen behandeln Sie?",
                    "tr": "Hangi hukuki konuları ele alıyorsunuz?"
                },
                "options": [
                    {"value": issue.value, "label": self._get_issue_label(issue)}
                    for issue in LegalIssue
                ],
                "multi_select": True,
                "current_selection": [i.value for i in criteria.target_legal_issues]
            },
            {
                "step": 2,
                "title": {
                    "en": "Set Date Range",
                    "de": "Datumsbereich festlegen",
                    "tr": "Tarih Aralığı Belirleyin"
                },
                "description": {
                    "en": "What time period should evidence cover?",
                    "de": "Welchen Zeitraum sollen die Beweise abdecken?",
                    "tr": "Deliller hangi zaman dilimini kapsamalı?"
                },
                "type": "date_range",
                "current_start": criteria.date_range_start.isoformat() if criteria.date_range_start else None,
                "current_end": criteria.date_range_end.isoformat() if criteria.date_range_end else None
            },
            {
                "step": 3,
                "title": {
                    "en": "Evidence Categories",
                    "de": "Beweiskategorien",
                    "tr": "Delil Kategorileri"
                },
                "description": {
                    "en": "Which types of evidence to include?",
                    "de": "Welche Beweisarten sollen einbezogen werden?",
                    "tr": "Hangi delil türleri dahil edilmeli?"
                },
                "options": [
                    {"value": cat.value, "label": self._get_category_label(cat)}
                    for cat in EvidenceCategory
                ],
                "multi_select": True,
                "current_selection": [c.value for c in criteria.required_categories]
            },
            {
                "step": 4,
                "title": {
                    "en": "Page Limits",
                    "de": "Seitenbegrenzungen",
                    "tr": "Sayfa Limitleri"
                },
                "description": {
                    "en": "Maximum pages for court submission",
                    "de": "Maximale Seitenzahl für die Gerichtsakte",
                    "tr": "Mahkeme sunumu için maksimum sayfa"
                },
                "type": "number",
                "min": 50,
                "max": 2000,
                "default": 500,
                "current_value": criteria.max_pages
            },
            {
                "step": 5,
                "title": {
                    "en": "Court Format",
                    "de": "Gerichtsformat",
                    "tr": "Mahkeme Formatı"
                },
                "description": {
                    "en": "Which court format to use?",
                    "de": "Welches Gerichtsformat soll verwendet werden?",
                    "tr": "Hangi mahkeme formatı kullanılmalı?"
                },
                "options": [
                    {"value": "german", "label": {"en": "German Family Court", "de": "Deutsches Familiengericht", "tr": "Alman Aile Mahkemesi"}},
                    {"value": "turkish", "label": {"en": "Turkish Family Court", "de": "Türkisches Familiengericht", "tr": "Türk Aile Mahkemesi"}},
                    {"value": "eu_e001", "label": {"en": "EU E001 Format", "de": "EU E001 Format", "tr": "AB E001 Formatı"}}
                ],
                "current_selection": criteria.court_format
            }
        ]

        return steps

    def _get_issue_label(self, issue: LegalIssue) -> Dict[str, str]:
        """Get multilingual label for legal issue."""
        labels = {
            LegalIssue.CUSTODY: {"en": "Child Custody", "de": "Sorgerecht", "tr": "Velayet"},
            LegalIssue.VISITATION: {"en": "Visitation Rights", "de": "Umgangsrecht", "tr": "Ziyaret Hakkı"},
            LegalIssue.PARENTAL_ALIENATION: {"en": "Parental Alienation", "de": "Eltern-Kind-Entfremdung", "tr": "Ebeveyn Yabancılaştırması"},
            LegalIssue.DOMESTIC_VIOLENCE: {"en": "Domestic Violence", "de": "Häusliche Gewalt", "tr": "Aile İçi Şiddet"},
            LegalIssue.CHILD_ABUSE: {"en": "Child Abuse", "de": "Kindesmisshandlung", "tr": "Çocuk İstismarı"},
            LegalIssue.CHILD_NEGLECT: {"en": "Child Neglect", "de": "Kindesvernachlässigung", "tr": "Çocuk İhmali"},
            LegalIssue.SUBSTANCE_ABUSE: {"en": "Substance Abuse", "de": "Substanzmissbrauch", "tr": "Madde Bağımlılığı"},
            LegalIssue.MENTAL_HEALTH: {"en": "Mental Health Concerns", "de": "Psychische Gesundheit", "tr": "Ruh Sağlığı"},
            LegalIssue.RELOCATION: {"en": "Relocation", "de": "Umzug", "tr": "Taşınma"},
            LegalIssue.CHILD_SUPPORT: {"en": "Child Support", "de": "Kindesunterhalt", "tr": "Nafaka"},
            LegalIssue.PARENTAL_FITNESS: {"en": "Parental Fitness", "de": "Elterliche Eignung", "tr": "Ebeveynlik Yeterliliği"},
            LegalIssue.INTERFERENCE: {"en": "Custody Interference", "de": "Umgangsvereitelung", "tr": "Velayet Engelleme"}
        }
        return labels.get(issue, {"en": issue.value, "de": issue.value, "tr": issue.value})

    def _get_category_label(self, category: EvidenceCategory) -> Dict[str, str]:
        """Get multilingual label for evidence category."""
        labels = {
            EvidenceCategory.COMMUNICATION: {"en": "Communications", "de": "Kommunikation", "tr": "İletişim"},
            EvidenceCategory.AUDIO_VIDEO: {"en": "Audio/Video", "de": "Audio/Video", "tr": "Ses/Video"},
            EvidenceCategory.DOCUMENT: {"en": "Documents", "de": "Dokumente", "tr": "Belgeler"},
            EvidenceCategory.PHOTOGRAPH: {"en": "Photographs", "de": "Fotos", "tr": "Fotoğraflar"},
            EvidenceCategory.FINANCIAL: {"en": "Financial Records", "de": "Finanzunterlagen", "tr": "Mali Kayıtlar"},
            EvidenceCategory.MEDICAL: {"en": "Medical Records", "de": "Medizinische Unterlagen", "tr": "Tıbbi Kayıtlar"},
            EvidenceCategory.EDUCATIONAL: {"en": "Educational Records", "de": "Schulunterlagen", "tr": "Eğitim Kayıtları"},
            EvidenceCategory.WITNESS: {"en": "Witness Statements", "de": "Zeugenaussagen", "tr": "Tanık İfadeleri"},
            EvidenceCategory.EXPERT: {"en": "Expert Reports", "de": "Gutachten", "tr": "Uzman Raporları"},
            EvidenceCategory.LOCATION: {"en": "Location Data", "de": "Standortdaten", "tr": "Konum Verileri"},
            EvidenceCategory.SOCIAL_MEDIA: {"en": "Social Media", "de": "Soziale Medien", "tr": "Sosyal Medya"},
            EvidenceCategory.OFFICIAL: {"en": "Official Documents", "de": "Amtliche Dokumente", "tr": "Resmi Belgeler"}
        }
        return labels.get(category, {"en": category.value, "de": category.value, "tr": category.value})

    def get_statistics(
        self,
        case_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get evidence pool statistics."""
        items = list(self.evidence_pool.values())
        if case_id:
            # Filter by case if items have case_id in metadata
            items = [i for i in items if i.metadata.get("case_id") == case_id]

        by_category = {}
        by_type = {}
        by_issue = {}

        for item in items:
            # By category
            cat = item.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

            # By type
            etype = item.evidence_type.value
            by_type[etype] = by_type.get(etype, 0) + 1

            # By legal issue
            for issue in item.legal_issues:
                issue_val = issue.value
                by_issue[issue_val] = by_issue.get(issue_val, 0) + 1

        return {
            "total_items": len(items),
            "total_pages": sum(i.estimated_pages for i in items),
            "total_size_bytes": sum(i.file_size_bytes for i in items),
            "authenticated_count": sum(1 for i in items if i.is_authenticated),
            "translation_needed": sum(1 for i in items if i.requires_translation),
            "by_category": by_category,
            "by_type": by_type,
            "by_legal_issue": by_issue,
            "date_range": {
                "earliest": min(i.date_created for i in items).isoformat() if items else None,
                "latest": max(i.date_created for i in items).isoformat() if items else None
            }
        }
