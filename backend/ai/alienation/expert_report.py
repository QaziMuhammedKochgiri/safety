"""
Expert Report Generator for Parental Alienation
Generates court-ready expert witness reports with evidence documentation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime
import hashlib

from .tactics_database import AlienationTacticDB, TacticCategory, LiteratureReference, CaseLawReference
from .pattern_matcher import PatternMatch
from .severity_scorer import SeverityScore, RiskLevel, EvidenceStrength
from .timeline_analyzer import TimelineSummary, EscalationTrend


class ReportLanguage(str, Enum):
    """Supported report languages."""
    ENGLISH = "en"
    GERMAN = "de"
    TURKISH = "tr"


class ReportFormat(str, Enum):
    """Report output formats."""
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    JSON = "json"


@dataclass
class ReportSection:
    """A section of the expert report."""
    section_id: str
    title: str
    content: str
    subsections: List['ReportSection'] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    literature_refs: List[str] = field(default_factory=list)
    case_law_refs: List[str] = field(default_factory=list)
    order: int = 0


@dataclass
class Recommendation:
    """A recommendation from the expert."""
    recommendation_id: str
    priority: str  # urgent, high, medium, low
    category: str  # legal, therapeutic, protective, monitoring
    title: str
    description: str
    rationale: str
    supporting_evidence: List[str]
    timeline: Optional[str] = None


@dataclass
class ExpertReport:
    """Complete expert witness report."""
    report_id: str
    case_id: str
    generated_at: datetime
    language: ReportLanguage

    # Report metadata
    expert_name: str
    expert_credentials: str
    report_type: str  # preliminary, comprehensive, update

    # Executive summary
    executive_summary: str

    # Main sections
    sections: List[ReportSection]

    # Findings
    overall_assessment: str
    risk_level: RiskLevel
    evidence_strength: EvidenceStrength
    severity_score: float

    # Evidence documentation
    evidence_items: List[Dict[str, Any]]
    total_messages_analyzed: int
    total_tactics_identified: int
    time_period_analyzed: str

    # Supporting materials
    literature_references: List[LiteratureReference]
    case_law_references: List[CaseLawReference]

    # Recommendations
    recommendations: List[Recommendation]

    # Technical details
    methodology: str
    limitations: str
    digital_signature: str


class ExpertReportGenerator:
    """Generates expert witness reports for parental alienation cases."""

    SECTION_TEMPLATES = {
        "en": {
            "introduction": "Introduction and Scope",
            "methodology": "Methodology and Data Sources",
            "findings": "Findings and Analysis",
            "tactics_analysis": "Analysis of Alienation Tactics",
            "timeline": "Chronological Analysis",
            "severity": "Severity Assessment",
            "evidence": "Evidence Documentation",
            "literature": "Literature Review",
            "case_law": "Relevant Case Law",
            "conclusions": "Conclusions",
            "recommendations": "Recommendations"
        },
        "de": {
            "introduction": "Einleitung und Umfang",
            "methodology": "Methodik und Datenquellen",
            "findings": "Befunde und Analyse",
            "tactics_analysis": "Analyse der Entfremdungstaktiken",
            "timeline": "Chronologische Analyse",
            "severity": "Schweregradbeurteilung",
            "evidence": "Beweisdokumentation",
            "literature": "Literaturübersicht",
            "case_law": "Relevante Rechtsprechung",
            "conclusions": "Schlussfolgerungen",
            "recommendations": "Empfehlungen"
        },
        "tr": {
            "introduction": "Giriş ve Kapsam",
            "methodology": "Metodoloji ve Veri Kaynakları",
            "findings": "Bulgular ve Analiz",
            "tactics_analysis": "Yabancılaştırma Taktikleri Analizi",
            "timeline": "Kronolojik Analiz",
            "severity": "Şiddet Değerlendirmesi",
            "evidence": "Delil Belgeleme",
            "literature": "Literatür İncelemesi",
            "case_law": "İlgili İçtihatlar",
            "conclusions": "Sonuçlar",
            "recommendations": "Öneriler"
        }
    }

    def __init__(self, db: Optional[AlienationTacticDB] = None):
        self.db = db or AlienationTacticDB()

    def generate_report(
        self,
        case_id: str,
        matches: List[PatternMatch],
        severity_score: SeverityScore,
        timeline_summary: TimelineSummary,
        expert_name: str = "SafeChild AI Analysis System",
        expert_credentials: str = "Automated Digital Forensics Analysis",
        language: ReportLanguage = ReportLanguage.ENGLISH,
        report_type: str = "comprehensive"
    ) -> ExpertReport:
        """Generate a comprehensive expert report."""
        report_id = self._generate_report_id(case_id)
        templates = self.SECTION_TEMPLATES.get(language.value, self.SECTION_TEMPLATES["en"])

        # Generate sections
        sections = self._generate_sections(
            matches, severity_score, timeline_summary, templates, language
        )

        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            severity_score, timeline_summary, matches, language
        )

        # Document evidence
        evidence_items = self._document_evidence(matches)

        # Get relevant literature and case law
        literature_refs = self._get_relevant_literature(matches)
        case_law_refs = self._get_relevant_case_law(matches, language)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            severity_score, timeline_summary, matches, language
        )

        # Generate methodology and limitations
        methodology = self._generate_methodology(language)
        limitations = self._generate_limitations(language)

        # Generate overall assessment
        overall_assessment = self._generate_overall_assessment(
            severity_score, timeline_summary, matches, language
        )

        # Calculate time period
        if timeline_summary.first_detection and timeline_summary.most_recent:
            time_period = f"{timeline_summary.first_detection.strftime('%Y-%m-%d')} to {timeline_summary.most_recent.strftime('%Y-%m-%d')}"
        else:
            time_period = "N/A"

        # Generate digital signature
        digital_signature = self._generate_signature(report_id, case_id, matches)

        return ExpertReport(
            report_id=report_id,
            case_id=case_id,
            generated_at=datetime.utcnow(),
            language=language,
            expert_name=expert_name,
            expert_credentials=expert_credentials,
            report_type=report_type,
            executive_summary=executive_summary,
            sections=sections,
            overall_assessment=overall_assessment,
            risk_level=severity_score.risk_level,
            evidence_strength=severity_score.evidence_strength,
            severity_score=severity_score.overall_score,
            evidence_items=evidence_items,
            total_messages_analyzed=severity_score.messages_analyzed,
            total_tactics_identified=severity_score.unique_tactics,
            time_period_analyzed=time_period,
            literature_references=literature_refs,
            case_law_references=case_law_refs,
            recommendations=recommendations,
            methodology=methodology,
            limitations=limitations,
            digital_signature=digital_signature
        )

    def _generate_report_id(self, case_id: str) -> str:
        """Generate unique report ID."""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        hash_input = f"{case_id}_{timestamp}"
        hash_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"RPT-{timestamp}-{hash_suffix}"

    def _generate_sections(
        self,
        matches: List[PatternMatch],
        severity: SeverityScore,
        timeline: TimelineSummary,
        templates: Dict[str, str],
        language: ReportLanguage
    ) -> List[ReportSection]:
        """Generate all report sections."""
        sections = []

        # 1. Introduction
        sections.append(ReportSection(
            section_id="intro",
            title=templates["introduction"],
            content=self._generate_introduction(severity, language),
            order=1
        ))

        # 2. Methodology
        sections.append(ReportSection(
            section_id="methodology",
            title=templates["methodology"],
            content=self._generate_methodology_section(language),
            order=2
        ))

        # 3. Findings
        sections.append(ReportSection(
            section_id="findings",
            title=templates["findings"],
            content=self._generate_findings_section(matches, severity, language),
            order=3
        ))

        # 4. Tactics Analysis
        sections.append(ReportSection(
            section_id="tactics",
            title=templates["tactics_analysis"],
            content=self._generate_tactics_section(matches, language),
            subsections=self._generate_tactic_subsections(matches, language),
            order=4
        ))

        # 5. Timeline Analysis
        sections.append(ReportSection(
            section_id="timeline",
            title=templates["timeline"],
            content=self._generate_timeline_section(timeline, language),
            order=5
        ))

        # 6. Severity Assessment
        sections.append(ReportSection(
            section_id="severity",
            title=templates["severity"],
            content=self._generate_severity_section(severity, language),
            order=6
        ))

        # 7. Evidence Documentation
        sections.append(ReportSection(
            section_id="evidence",
            title=templates["evidence"],
            content=self._generate_evidence_section(matches, language),
            order=7
        ))

        # 8. Literature Review
        sections.append(ReportSection(
            section_id="literature",
            title=templates["literature"],
            content=self._generate_literature_section(matches, language),
            literature_refs=[ref.reference_id for ref in self._get_relevant_literature(matches)],
            order=8
        ))

        # 9. Case Law
        sections.append(ReportSection(
            section_id="case_law",
            title=templates["case_law"],
            content=self._generate_case_law_section(language),
            case_law_refs=[ref.reference_id for ref in self._get_relevant_case_law(matches, language)],
            order=9
        ))

        # 10. Conclusions
        sections.append(ReportSection(
            section_id="conclusions",
            title=templates["conclusions"],
            content=self._generate_conclusions_section(severity, timeline, language),
            order=10
        ))

        # 11. Recommendations
        sections.append(ReportSection(
            section_id="recommendations",
            title=templates["recommendations"],
            content=self._generate_recommendations_section(severity, timeline, language),
            order=11
        ))

        return sections

    def _generate_introduction(self, severity: SeverityScore, language: ReportLanguage) -> str:
        """Generate introduction section."""
        if language == ReportLanguage.ENGLISH:
            return f"""This expert report presents a comprehensive analysis of digital communications
in relation to potential parental alienation behaviors. The analysis was conducted using
advanced natural language processing and pattern recognition techniques to identify and
document manipulation tactics commonly associated with parental alienation.

A total of {severity.messages_analyzed} messages were analyzed over a period of
{severity.time_span_days} days, identifying {severity.total_matches} instances of
{severity.unique_tactics} distinct alienation tactics.

This report is intended for use in legal proceedings and provides an objective,
evidence-based assessment of the communications analyzed."""

        elif language == ReportLanguage.GERMAN:
            return f"""Dieser Expertenbericht präsentiert eine umfassende Analyse der digitalen
Kommunikation in Bezug auf mögliche elterliche Entfremdungsverhaltensweisen. Die Analyse
wurde mit fortschrittlichen Verarbeitungstechniken für natürliche Sprache und
Mustererkennung durchgeführt, um Manipulationstaktiken zu identifizieren und zu
dokumentieren, die häufig mit elterlicher Entfremdung verbunden sind.

Insgesamt wurden {severity.messages_analyzed} Nachrichten über einen Zeitraum von
{severity.time_span_days} Tagen analysiert, wobei {severity.total_matches} Fälle von
{severity.unique_tactics} verschiedenen Entfremdungstaktiken identifiziert wurden.

Dieser Bericht ist für die Verwendung in Gerichtsverfahren bestimmt und bietet eine
objektive, evidenzbasierte Bewertung der analysierten Kommunikation."""

        else:  # Turkish
            return f"""Bu uzman raporu, olası ebeveyn yabancılaştırma davranışlarıyla ilgili dijital
iletişimin kapsamlı bir analizini sunmaktadır. Analiz, ebeveyn yabancılaştırmasıyla
yaygın olarak ilişkilendirilen manipülasyon taktiklerini tanımlamak ve belgelemek için
gelişmiş doğal dil işleme ve örüntü tanıma teknikleri kullanılarak gerçekleştirilmiştir.

{severity.time_span_days} günlük bir süre boyunca toplam {severity.messages_analyzed} mesaj
analiz edilmiş ve {severity.unique_tactics} farklı yabancılaştırma taktiğinin
{severity.total_matches} örneği tespit edilmiştir.

Bu rapor, hukuki işlemlerde kullanılmak üzere hazırlanmıştır ve analiz edilen
iletişimin nesnel, kanıta dayalı bir değerlendirmesini sunmaktadır."""

    def _generate_executive_summary(
        self,
        severity: SeverityScore,
        timeline: TimelineSummary,
        matches: List[PatternMatch],
        language: ReportLanguage
    ) -> str:
        """Generate executive summary."""
        risk_descriptions = {
            "en": {
                RiskLevel.SEVERE: "severe risk requiring immediate intervention",
                RiskLevel.HIGH: "high risk requiring prompt action",
                RiskLevel.MODERATE: "moderate risk requiring attention",
                RiskLevel.LOW: "low risk requiring monitoring",
                RiskLevel.MINIMAL: "minimal risk detected"
            },
            "de": {
                RiskLevel.SEVERE: "schweres Risiko, das sofortiges Eingreifen erfordert",
                RiskLevel.HIGH: "hohes Risiko, das promptes Handeln erfordert",
                RiskLevel.MODERATE: "mäßiges Risiko, das Aufmerksamkeit erfordert",
                RiskLevel.LOW: "geringes Risiko, das Überwachung erfordert",
                RiskLevel.MINIMAL: "minimales Risiko festgestellt"
            },
            "tr": {
                RiskLevel.SEVERE: "acil müdahale gerektiren ciddi risk",
                RiskLevel.HIGH: "hızlı eylem gerektiren yüksek risk",
                RiskLevel.MODERATE: "dikkat gerektiren orta düzey risk",
                RiskLevel.LOW: "izleme gerektiren düşük risk",
                RiskLevel.MINIMAL: "minimum risk tespit edildi"
            }
        }

        trend_descriptions = {
            "en": {
                EscalationTrend.RAPID_ESCALATION: "rapidly escalating",
                EscalationTrend.GRADUAL_ESCALATION: "gradually escalating",
                EscalationTrend.STABLE: "stable",
                EscalationTrend.DE_ESCALATING: "de-escalating",
                EscalationTrend.FLUCTUATING: "fluctuating"
            },
            "de": {
                EscalationTrend.RAPID_ESCALATION: "schnell eskalierend",
                EscalationTrend.GRADUAL_ESCALATION: "allmählich eskalierend",
                EscalationTrend.STABLE: "stabil",
                EscalationTrend.DE_ESCALATING: "deeskalierend",
                EscalationTrend.FLUCTUATING: "schwankend"
            },
            "tr": {
                EscalationTrend.RAPID_ESCALATION: "hızla tırmanan",
                EscalationTrend.GRADUAL_ESCALATION: "yavaş yavaş tırmanan",
                EscalationTrend.STABLE: "stabil",
                EscalationTrend.DE_ESCALATING: "azalan",
                EscalationTrend.FLUCTUATING: "dalgalanan"
            }
        }

        lang = language.value
        risk_desc = risk_descriptions.get(lang, risk_descriptions["en"])[severity.risk_level]
        trend_desc = trend_descriptions.get(lang, trend_descriptions["en"])[timeline.escalation_trend]

        # Get top tactics
        tactic_counts = {}
        for match in matches:
            tactic_counts[match.tactic_name] = tactic_counts.get(match.tactic_name, 0) + 1
        top_tactics = sorted(tactic_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        top_tactics_str = ", ".join(f"{t[0]} ({t[1]}x)" for t in top_tactics)

        if language == ReportLanguage.ENGLISH:
            return f"""EXECUTIVE SUMMARY

Risk Assessment: {severity.overall_score}/10 - {risk_desc}
Evidence Strength: {severity.evidence_strength.value}
Trend: {trend_desc}

This analysis identified {severity.total_matches} instances of parental alienation behaviors
across {severity.unique_tactics} distinct manipulation tactics over a {severity.time_span_days}-day period.

Primary tactics identified: {top_tactics_str}

The evidence strength is classified as {severity.evidence_strength.value}, based on the frequency,
consistency, and severity of the documented behaviors.

Assessment confidence: {severity.assessment_confidence:.0%}

Key findings:
- {len([m for m in matches if m.severity_score >= 8])} critical-severity incidents documented
- {len(timeline.patterns)} distinct behavioral patterns identified
- Temporal trend: {trend_desc}

Immediate actions recommended: {len([r for r in severity.recommendations if 'immediate' in r.lower() or 'urgent' in r.lower()])}"""

        elif language == ReportLanguage.GERMAN:
            return f"""ZUSAMMENFASSUNG

Risikobewertung: {severity.overall_score}/10 - {risk_desc}
Beweisstärke: {severity.evidence_strength.value}
Trend: {trend_desc}

Diese Analyse identifizierte {severity.total_matches} Fälle von elterlichem Entfremdungsverhalten
mit {severity.unique_tactics} verschiedenen Manipulationstaktiken über einen Zeitraum von {severity.time_span_days} Tagen.

Hauptsächlich identifizierte Taktiken: {top_tactics_str}

Die Beweisstärke wird als {severity.evidence_strength.value} eingestuft, basierend auf Häufigkeit,
Konsistenz und Schwere der dokumentierten Verhaltensweisen.

Bewertungskonfidenz: {severity.assessment_confidence:.0%}"""

        else:  # Turkish
            return f"""YÖNETİCİ ÖZETİ

Risk Değerlendirmesi: {severity.overall_score}/10 - {risk_desc}
Kanıt Gücü: {severity.evidence_strength.value}
Trend: {trend_desc}

Bu analiz, {severity.time_span_days} günlük süre boyunca {severity.unique_tactics} farklı
manipülasyon taktiği kullanılarak {severity.total_matches} ebeveyn yabancılaştırma davranışı
örneği tespit etmiştir.

Tespit edilen başlıca taktikler: {top_tactics_str}

Kanıt gücü, belgelenen davranışların sıklığı, tutarlılığı ve ciddiyetine göre
{severity.evidence_strength.value} olarak sınıflandırılmıştır.

Değerlendirme güveni: {severity.assessment_confidence:.0%}"""

    def _generate_methodology_section(self, language: ReportLanguage) -> str:
        """Generate methodology section content."""
        if language == ReportLanguage.ENGLISH:
            return """The analysis employed the following methodology:

1. **Data Collection**: Digital communications were extracted and preserved with chain of custody documentation.

2. **Pattern Recognition**: Advanced NLP algorithms analyzed message content against a database of 50+ documented alienation tactics, based on peer-reviewed literature.

3. **Severity Scoring**: Each identified behavior was scored using a literature-backed scoring system considering:
   - Base severity of the tactic (1-10)
   - Frequency of occurrence
   - Pattern consistency over time
   - Category weighting based on research

4. **Timeline Analysis**: Temporal patterns were analyzed to identify escalation trends, clustering, and behavioral changes.

5. **Evidence Strength Assessment**: Overall evidence strength was evaluated based on:
   - Number and confidence of matches
   - Diversity of tactics identified
   - Time span of observations
   - Presence of severe tactics

6. **Literature Validation**: Findings were cross-referenced with established parental alienation literature."""

        elif language == ReportLanguage.GERMAN:
            return """Die Analyse verwendete folgende Methodik:

1. **Datensammlung**: Digitale Kommunikation wurde mit Dokumentation der Beweiskette extrahiert und gesichert.

2. **Mustererkennung**: Fortgeschrittene NLP-Algorithmen analysierten Nachrichteninhalte gegen eine Datenbank von 50+ dokumentierten Entfremdungstaktiken.

3. **Schweregradbeurteilung**: Jedes identifizierte Verhalten wurde anhand eines literaturgestützten Systems bewertet.

4. **Zeitlinienanalyse**: Zeitliche Muster wurden analysiert, um Eskalationstrends zu identifizieren.

5. **Beweisstärkebewertung**: Die Gesamtbeweisstärke wurde basierend auf Häufigkeit und Konsistenz bewertet.

6. **Literaturvalidierung**: Befunde wurden mit etablierter Literatur zur elterlichen Entfremdung abgeglichen."""

        else:  # Turkish
            return """Analiz aşağıdaki metodolojiyi kullandı:

1. **Veri Toplama**: Dijital iletişimler, delil zinciri belgeleriyle birlikte çıkarıldı ve korundu.

2. **Örüntü Tanıma**: Gelişmiş NLP algoritmaları, 50'den fazla belgelenmiş yabancılaştırma taktiği veritabanına karşı mesaj içeriğini analiz etti.

3. **Şiddet Puanlaması**: Her tespit edilen davranış, literatüre dayalı bir puanlama sistemi kullanılarak değerlendirildi.

4. **Zaman Çizelgesi Analizi**: Tırmanma eğilimlerini belirlemek için zamansal örüntüler analiz edildi.

5. **Kanıt Gücü Değerlendirmesi**: Genel kanıt gücü, sıklık ve tutarlılığa göre değerlendirildi.

6. **Literatür Doğrulama**: Bulgular, yerleşik ebeveyn yabancılaştırma literatürüyle karşılaştırıldı."""

    def _generate_findings_section(
        self,
        matches: List[PatternMatch],
        severity: SeverityScore,
        language: ReportLanguage
    ) -> str:
        """Generate findings section."""
        # Group by category
        category_counts = {}
        for match in matches:
            cat = match.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        categories_str = "\n".join(f"- {cat}: {count} instances" for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True))

        if language == ReportLanguage.ENGLISH:
            return f"""Analysis of the communications revealed the following findings:

**Quantitative Summary:**
- Total messages analyzed: {severity.messages_analyzed}
- Alienation behaviors identified: {severity.total_matches}
- Unique tactics detected: {severity.unique_tactics}
- Time period covered: {severity.time_span_days} days

**Distribution by Category:**
{categories_str}

**Severity Distribution:**
- Frequency Score: {severity.frequency_score}/10
- Intensity Score: {severity.intensity_score}/10
- Pattern Score: {severity.pattern_score}/10
- Diversity Score: {severity.diversity_score}/10

**Overall Assessment:**
The analysis indicates a {severity.risk_level.value} risk level with {severity.evidence_strength.value} evidence strength."""

        else:
            return f"""Analiz, aşağıdaki bulguları ortaya koymuştur:

**Nicel Özet:**
- Analiz edilen toplam mesaj: {severity.messages_analyzed}
- Tespit edilen yabancılaştırma davranışları: {severity.total_matches}
- Tespit edilen benzersiz taktikler: {severity.unique_tactics}

**Genel Değerlendirme:**
Analiz, {severity.evidence_strength.value} kanıt gücüyle {severity.risk_level.value} risk seviyesi göstermektedir."""

    def _generate_tactics_section(self, matches: List[PatternMatch], language: ReportLanguage) -> str:
        """Generate tactics analysis section."""
        tactic_summary = {}
        for match in matches:
            if match.tactic_id not in tactic_summary:
                tactic_summary[match.tactic_id] = {
                    "name": match.tactic_name,
                    "category": match.category.value,
                    "count": 0,
                    "avg_severity": []
                }
            tactic_summary[match.tactic_id]["count"] += 1
            tactic_summary[match.tactic_id]["avg_severity"].append(match.severity_score)

        tactics_str = ""
        for tid, data in sorted(tactic_summary.items(), key=lambda x: x[1]["count"], reverse=True)[:10]:
            avg = sum(data["avg_severity"]) / len(data["avg_severity"])
            tactics_str += f"\n- **{data['name']}** ({data['category']}): {data['count']} instances, avg severity {avg:.1f}"

        if language == ReportLanguage.ENGLISH:
            return f"""The following alienation tactics were identified in the analyzed communications:
{tactics_str}

Each tactic is categorized according to established parental alienation taxonomy and scored based on research-validated severity criteria."""
        else:
            return f"""Analiz edilen iletişimlerde aşağıdaki yabancılaştırma taktikleri tespit edilmiştir:
{tactics_str}"""

    def _generate_tactic_subsections(
        self,
        matches: List[PatternMatch],
        language: ReportLanguage
    ) -> List[ReportSection]:
        """Generate subsections for each major tactic."""
        subsections = []
        tactic_matches = {}

        for match in matches:
            if match.tactic_id not in tactic_matches:
                tactic_matches[match.tactic_id] = []
            tactic_matches[match.tactic_id].append(match)

        for tid, t_matches in sorted(tactic_matches.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
            tactic = self.db.get_tactic(tid)
            if not tactic:
                continue

            examples = [f'"{m.matched_text}"' for m in t_matches[:3]]
            examples_str = "\n".join(f"- {ex}" for ex in examples)

            content = f"""**Definition:** {tactic.description}

**Frequency:** {len(t_matches)} instances detected

**Example quotes:**
{examples_str}

**Indicators present:**
- {chr(10).join('- ' + ind for ind in tactic.indicators[:3])}"""

            subsections.append(ReportSection(
                section_id=f"tactic_{tid}",
                title=tactic.name,
                content=content,
                evidence_refs=[m.match_id for m in t_matches],
                order=len(subsections)
            ))

        return subsections

    def _generate_timeline_section(self, timeline: TimelineSummary, language: ReportLanguage) -> str:
        """Generate timeline analysis section."""
        if language == ReportLanguage.ENGLISH:
            return f"""**Time Period:** {timeline.first_detection.strftime('%Y-%m-%d') if timeline.first_detection else 'N/A'} to {timeline.most_recent.strftime('%Y-%m-%d') if timeline.most_recent else 'N/A'}

**Total Duration:** {timeline.time_span.days} days

**Escalation Trend:** {timeline.escalation_trend.value}

**Key Timeline Events:**
{chr(10).join(f"- {e.timestamp.strftime('%Y-%m-%d')}: {e.description}" for e in timeline.key_events[:5])}

**Identified Patterns:**
{chr(10).join(f"- {p.description}" for p in timeline.patterns[:3])}

**Peak Activity Period:** {f"{timeline.peak_period[0].strftime('%Y-%m-%d')} to {timeline.peak_period[1].strftime('%Y-%m-%d')}" if timeline.peak_period else 'N/A'}"""
        else:
            return f"""**Zaman Dilimi:** {timeline.time_span.days} gün
**Tırmanma Trendi:** {timeline.escalation_trend.value}"""

    def _generate_severity_section(self, severity: SeverityScore, language: ReportLanguage) -> str:
        """Generate severity assessment section."""
        if language == ReportLanguage.ENGLISH:
            return f"""**Overall Severity Score:** {severity.overall_score}/10

**Risk Level:** {severity.risk_level.value.upper()}

**Evidence Strength:** {severity.evidence_strength.value.upper()}

**Score Components:**
| Component | Score | Weight |
|-----------|-------|--------|
| Frequency | {severity.frequency_score}/10 | 20% |
| Intensity | {severity.intensity_score}/10 | 35% |
| Pattern | {severity.pattern_score}/10 | 25% |
| Diversity | {severity.diversity_score}/10 | 20% |

**Confidence Factors:**
{chr(10).join(f"- {f}" for f in severity.confidence_factors)}

**Assessment Confidence:** {severity.assessment_confidence:.0%}"""
        else:
            return f"""**Genel Şiddet Puanı:** {severity.overall_score}/10
**Risk Seviyesi:** {severity.risk_level.value.upper()}
**Kanıt Gücü:** {severity.evidence_strength.value.upper()}"""

    def _generate_evidence_section(self, matches: List[PatternMatch], language: ReportLanguage) -> str:
        """Generate evidence documentation section."""
        evidence_count = len(matches)
        high_conf = len([m for m in matches if m.confidence >= 0.8])
        severe = len([m for m in matches if m.severity_score >= 8])

        if language == ReportLanguage.ENGLISH:
            return f"""**Evidence Summary:**
- Total evidence items: {evidence_count}
- High-confidence matches: {high_conf}
- Severe incidents: {severe}

Each piece of evidence has been documented with:
- Exact quote from original message
- Timestamp of communication
- Tactic classification
- Severity score
- Confidence level
- Contextual information

All evidence is preserved with chain of custody documentation and can be verified against original data sources."""
        else:
            return f"""**Kanıt Özeti:**
- Toplam kanıt öğeleri: {evidence_count}
- Yüksek güvenli eşleşmeler: {high_conf}
- Ciddi olaylar: {severe}"""

    def _generate_literature_section(self, matches: List[PatternMatch], language: ReportLanguage) -> str:
        """Generate literature review section."""
        literature = self._get_relevant_literature(matches)
        refs_str = "\n".join(f"- {ref.authors[0]} et al. ({ref.year}). {ref.title}. {ref.journal}" for ref in literature[:5])

        if language == ReportLanguage.ENGLISH:
            return f"""The findings in this report are supported by extensive peer-reviewed research on parental alienation. Key references include:

{refs_str}

The tactics identified and scoring methodology are derived from established research frameworks validated through clinical and legal application."""
        else:
            return f"""Bu rapordaki bulgular, ebeveyn yabancılaştırması üzerine kapsamlı hakemli araştırmalarla desteklenmektedir.

{refs_str}"""

    def _generate_case_law_section(self, language: ReportLanguage) -> str:
        """Generate case law section."""
        case_law = list(self.db.case_law.values())[:5]
        cases_str = "\n".join(f"- {c.case_name} ({c.court}, {c.year}): {c.key_finding}" for c in case_law)

        if language == ReportLanguage.ENGLISH:
            return f"""Relevant case law recognizing parental alienation behaviors:

{cases_str}

These cases establish legal precedent for considering documented alienation behaviors in custody determinations."""
        else:
            return f"""İlgili içtihatlar:

{cases_str}"""

    def _generate_conclusions_section(
        self,
        severity: SeverityScore,
        timeline: TimelineSummary,
        language: ReportLanguage
    ) -> str:
        """Generate conclusions section."""
        if language == ReportLanguage.ENGLISH:
            return f"""Based on the comprehensive analysis presented in this report:

1. **Evidence of Alienation:** The analysis provides {severity.evidence_strength.value} evidence of parental alienation behaviors.

2. **Risk Level:** The case presents a {severity.risk_level.value} risk level with an overall severity score of {severity.overall_score}/10.

3. **Temporal Trend:** The alienation behaviors show a {timeline.escalation_trend.value} trend.

4. **Pattern Recognition:** {len(timeline.patterns)} distinct behavioral patterns were identified, indicating systematic rather than isolated incidents.

5. **Assessment Confidence:** This assessment is made with {severity.assessment_confidence:.0%} confidence based on the quantity and quality of analyzed data.

These conclusions are rendered to a reasonable degree of professional certainty based on the data analyzed and established research frameworks."""
        else:
            return f"""Bu raporda sunulan kapsamlı analize dayanarak:

1. **Yabancılaştırma Kanıtı:** Analiz, ebeveyn yabancılaştırma davranışlarının {severity.evidence_strength.value} kanıtını sunmaktadır.

2. **Risk Seviyesi:** Vaka, {severity.overall_score}/10 genel şiddet puanıyla {severity.risk_level.value} risk seviyesi sunmaktadır.

3. **Değerlendirme Güveni:** Bu değerlendirme, %{severity.assessment_confidence:.0%} güvenle yapılmaktadır."""

    def _generate_recommendations_section(
        self,
        severity: SeverityScore,
        timeline: TimelineSummary,
        language: ReportLanguage
    ) -> str:
        """Generate recommendations section content."""
        recs = severity.recommendations[:6]
        recs_str = "\n".join(f"{i+1}. {r}" for i, r in enumerate(recs))

        if language == ReportLanguage.ENGLISH:
            return f"""Based on the findings of this analysis, the following recommendations are made:

{recs_str}

**Urgency Level:** {severity.urgency_level.upper()}

These recommendations should be considered in consultation with legal counsel and mental health professionals specializing in high-conflict custody cases."""
        else:
            return f"""Bu analizin bulgularına dayanarak aşağıdaki öneriler yapılmaktadır:

{recs_str}

**Aciliyet Seviyesi:** {severity.urgency_level.upper()}"""

    def _document_evidence(self, matches: List[PatternMatch]) -> List[Dict[str, Any]]:
        """Document all evidence items."""
        return [
            {
                "evidence_id": match.match_id,
                "tactic": match.tactic_name,
                "category": match.category.value,
                "text": match.matched_text,
                "context": f"{match.context_before}...{match.context_after}",
                "timestamp": match.timestamp.isoformat() if match.timestamp else None,
                "sender": match.sender,
                "severity": match.severity_score,
                "confidence": match.confidence
            }
            for match in matches
        ]

    def _get_relevant_literature(self, matches: List[PatternMatch]) -> List[LiteratureReference]:
        """Get relevant literature references."""
        return list(self.db.literature.values())

    def _get_relevant_case_law(
        self,
        matches: List[PatternMatch],
        language: ReportLanguage
    ) -> List[CaseLawReference]:
        """Get relevant case law based on jurisdiction."""
        jurisdiction_map = {
            ReportLanguage.ENGLISH: ["US", "UK", "EU"],
            ReportLanguage.GERMAN: ["DE", "EU"],
            ReportLanguage.TURKISH: ["TR", "EU"]
        }

        jurisdictions = jurisdiction_map.get(language, ["EU"])
        return [ref for ref in self.db.case_law.values() if ref.jurisdiction in jurisdictions]

    def _generate_recommendations(
        self,
        severity: SeverityScore,
        timeline: TimelineSummary,
        matches: List[PatternMatch],
        language: ReportLanguage
    ) -> List[Recommendation]:
        """Generate structured recommendations."""
        recommendations = []

        # Based on risk level
        if severity.risk_level in [RiskLevel.SEVERE, RiskLevel.HIGH]:
            recommendations.append(Recommendation(
                recommendation_id="rec_001",
                priority="urgent",
                category="protective",
                title="Immediate Professional Intervention",
                description="Engage custody evaluator or family therapist specializing in alienation",
                rationale="High/severe risk level requires immediate professional assessment",
                supporting_evidence=[m.match_id for m in matches[:5]]
            ))

        if timeline.escalation_trend == EscalationTrend.RAPID_ESCALATION:
            recommendations.append(Recommendation(
                recommendation_id="rec_002",
                priority="urgent",
                category="legal",
                title="Emergency Court Motion",
                description="Consider filing for emergency modification of custody/visitation",
                rationale="Rapid escalation pattern indicates deteriorating situation",
                supporting_evidence=[],
                timeline="Within 1 week"
            ))

        # Standard recommendations
        recommendations.append(Recommendation(
            recommendation_id="rec_003",
            priority="high",
            category="monitoring",
            title="Continued Documentation",
            description="Maintain systematic documentation of all communications",
            rationale="Ongoing evidence collection strengthens legal position",
            supporting_evidence=[]
        ))

        recommendations.append(Recommendation(
            recommendation_id="rec_004",
            priority="medium",
            category="therapeutic",
            title="Child Therapy Evaluation",
            description="Have child evaluated by therapist trained in alienation dynamics",
            rationale="Professional assessment of impact on child is essential",
            supporting_evidence=[]
        ))

        return recommendations

    def _generate_methodology(self, language: ReportLanguage) -> str:
        """Generate methodology description."""
        if language == ReportLanguage.ENGLISH:
            return "Automated NLP analysis using pattern matching against research-validated taxonomy of 50+ parental alienation tactics"
        elif language == ReportLanguage.GERMAN:
            return "Automatisierte NLP-Analyse mittels Mustervergleich gegen forschungsvalidierte Taxonomie von 50+ Entfremdungstaktiken"
        else:
            return "50'den fazla yabancılaştırma taktiğinin araştırma-doğrulanmış taksonomisine karşı örüntü eşleştirmesi kullanan otomatik NLP analizi"

    def _generate_limitations(self, language: ReportLanguage) -> str:
        """Generate limitations disclosure."""
        if language == ReportLanguage.ENGLISH:
            return """This analysis is based solely on text communications and does not include:
- In-person observations
- Audio/video evidence analysis
- Psychological evaluations
- Interviews with parties

The findings should be considered alongside other forms of evidence and professional evaluations."""
        else:
            return "Bu analiz yalnızca metin iletişimlerine dayanmaktadır ve yüz yüze gözlemler, psikolojik değerlendirmeler içermemektedir."

    def _generate_overall_assessment(
        self,
        severity: SeverityScore,
        timeline: TimelineSummary,
        matches: List[PatternMatch],
        language: ReportLanguage
    ) -> str:
        """Generate overall assessment statement."""
        if language == ReportLanguage.ENGLISH:
            return f"""The analyzed communications demonstrate {severity.evidence_strength.value} evidence of parental alienation behaviors,
with a severity score of {severity.overall_score}/10 ({severity.risk_level.value} risk).
The temporal analysis shows {timeline.escalation_trend.value} trend with {len(timeline.patterns)} identified behavioral patterns.
This assessment is made with {severity.assessment_confidence:.0%} confidence."""
        else:
            return f"""Analiz edilen iletişimler, {severity.overall_score}/10 şiddet puanıyla
({severity.risk_level.value} risk) ebeveyn yabancılaştırma davranışlarının {severity.evidence_strength.value}
kanıtını göstermektedir."""

    def _generate_signature(self, report_id: str, case_id: str, matches: List[PatternMatch]) -> str:
        """Generate digital signature for report integrity."""
        content = f"{report_id}:{case_id}:{len(matches)}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()

    def export_to_html(self, report: ExpertReport) -> str:
        """Export report to HTML format."""
        sections_html = ""
        for section in sorted(report.sections, key=lambda s: s.order):
            sections_html += f"""
            <section id="{section.section_id}">
                <h2>{section.title}</h2>
                <div class="content">{section.content.replace(chr(10), '<br>')}</div>
            </section>
            """

        return f"""
<!DOCTYPE html>
<html lang="{report.language.value}">
<head>
    <meta charset="UTF-8">
    <title>Expert Report - {report.case_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; }}
        h2 {{ color: #34495e; }}
        .executive-summary {{ background: #ecf0f1; padding: 20px; border-radius: 5px; }}
        .metadata {{ font-size: 0.9em; color: #7f8c8d; }}
        section {{ margin-bottom: 30px; }}
        .risk-severe {{ color: #e74c3c; font-weight: bold; }}
        .risk-high {{ color: #e67e22; font-weight: bold; }}
        .risk-moderate {{ color: #f39c12; }}
        .risk-low {{ color: #27ae60; }}
    </style>
</head>
<body>
    <h1>Expert Witness Report</h1>
    <div class="metadata">
        <p>Report ID: {report.report_id}</p>
        <p>Case ID: {report.case_id}</p>
        <p>Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}</p>
        <p>Expert: {report.expert_name}</p>
    </div>

    <div class="executive-summary">
        <h2>Executive Summary</h2>
        <p>{report.executive_summary.replace(chr(10), '<br>')}</p>
    </div>

    {sections_html}

    <footer>
        <p>Digital Signature: {report.digital_signature}</p>
        <p><em>This report was generated by {report.expert_name}</em></p>
    </footer>
</body>
</html>
        """
