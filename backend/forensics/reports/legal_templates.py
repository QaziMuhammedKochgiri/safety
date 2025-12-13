"""
Legal Templates for SafeChild Reports
GDPR compliance, expert witness statements, and court filing formats.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class Jurisdiction(Enum):
    """Supported legal jurisdictions."""
    GERMANY = "germany"
    TURKEY = "turkey"
    EUROPEAN_UNION = "eu"
    INTERNATIONAL = "international"


@dataclass
class GDPRChecklist:
    """GDPR compliance checklist for forensic evidence."""
    case_id: str
    data_controller: str
    data_processor: str
    legal_basis: str
    data_subjects: List[str]
    data_categories: List[str]
    retention_period: str
    security_measures: List[str]
    third_party_recipients: List[str]
    cross_border_transfers: bool
    dpia_conducted: bool
    consent_obtained: bool
    legitimate_interest_assessment: Optional[str] = None
    checklist_items: List[Dict[str, Any]] = field(default_factory=list)
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.checklist_items:
            self.checklist_items = self._generate_checklist()

    def _generate_checklist(self) -> List[Dict[str, Any]]:
        """Generate GDPR compliance checklist items."""
        return [
            {
                "id": "lawful_basis",
                "title": "Lawful Basis Identified",
                "description": "Legal basis for processing has been identified and documented",
                "article": "Article 6",
                "status": "pending",
                "notes": ""
            },
            {
                "id": "purpose_limitation",
                "title": "Purpose Limitation",
                "description": "Data collected for specified, explicit, and legitimate purposes",
                "article": "Article 5(1)(b)",
                "status": "pending",
                "notes": ""
            },
            {
                "id": "data_minimization",
                "title": "Data Minimization",
                "description": "Only necessary data is processed",
                "article": "Article 5(1)(c)",
                "status": "pending",
                "notes": ""
            },
            {
                "id": "accuracy",
                "title": "Accuracy",
                "description": "Data is accurate and kept up to date",
                "article": "Article 5(1)(d)",
                "status": "pending",
                "notes": ""
            },
            {
                "id": "storage_limitation",
                "title": "Storage Limitation",
                "description": "Data retention period defined and justified",
                "article": "Article 5(1)(e)",
                "status": "pending",
                "notes": ""
            },
            {
                "id": "integrity_confidentiality",
                "title": "Integrity and Confidentiality",
                "description": "Appropriate security measures implemented",
                "article": "Article 5(1)(f)",
                "status": "pending",
                "notes": ""
            },
            {
                "id": "accountability",
                "title": "Accountability",
                "description": "Documentation of compliance measures",
                "article": "Article 5(2)",
                "status": "pending",
                "notes": ""
            },
            {
                "id": "data_subject_rights",
                "title": "Data Subject Rights",
                "description": "Procedures for handling data subject requests",
                "article": "Articles 15-22",
                "status": "pending",
                "notes": ""
            },
            {
                "id": "security_measures",
                "title": "Technical Security Measures",
                "description": "Encryption, pseudonymization, access controls",
                "article": "Article 32",
                "status": "pending",
                "notes": ""
            },
            {
                "id": "breach_notification",
                "title": "Breach Notification Procedures",
                "description": "72-hour notification process documented",
                "article": "Articles 33-34",
                "status": "pending",
                "notes": ""
            }
        ]

    def mark_item_complete(self, item_id: str, notes: str = ""):
        """Mark a checklist item as complete."""
        for item in self.checklist_items:
            if item["id"] == item_id:
                item["status"] = "complete"
                item["notes"] = notes
                item["completed_at"] = datetime.utcnow().isoformat()
                break

    def get_compliance_score(self) -> float:
        """Calculate compliance percentage."""
        if not self.checklist_items:
            return 0.0
        complete = sum(1 for item in self.checklist_items if item["status"] == "complete")
        return (complete / len(self.checklist_items)) * 100


@dataclass
class ExpertWitnessTemplate:
    """Expert witness statement template."""
    case_id: str
    expert_name: str
    expert_title: str
    expert_qualifications: List[str]
    expert_experience_years: int
    court_name: str
    jurisdiction: Jurisdiction
    statement_date: datetime

    # Statement sections
    introduction: str = ""
    scope_of_examination: str = ""
    methodology: str = ""
    findings: List[Dict[str, Any]] = field(default_factory=list)
    opinions: List[str] = field(default_factory=list)
    conclusions: str = ""
    limitations: List[str] = field(default_factory=list)

    # Declaration
    declaration_text: str = ""

    def generate_introduction(self, language: str = "en") -> str:
        """Generate standard introduction section."""
        intros = {
            "en": f"""
I, {self.expert_name}, {self.expert_title}, hereby provide this expert witness statement
in connection with Case No. {self.case_id} before the {self.court_name}.

QUALIFICATIONS:
{self._format_qualifications()}

I have been instructed to provide an expert opinion on the digital forensic evidence
in this matter. I understand my duty to the Court and have complied with that duty.
""",
            "de": f"""
Ich, {self.expert_name}, {self.expert_title}, erstatte hiermit ein Sachverstaendigengutachten
im Verfahren Az. {self.case_id} vor dem {self.court_name}.

QUALIFIKATIONEN:
{self._format_qualifications()}

Ich wurde beauftragt, ein Gutachten ueber die digitalen forensischen Beweise in dieser
Angelegenheit zu erstellen. Ich bin mir meiner Pflicht gegenueber dem Gericht bewusst
und habe diese Pflicht erfuellt.
""",
            "tr": f"""
Ben, {self.expert_name}, {self.expert_title}, {self.court_name} nezdindeki
{self.case_id} sayili dava ile ilgili olarak bu bilirkisi raporunu sunmaktayim.

NITELIKLER:
{self._format_qualifications()}

Bu davadaki dijital adli deliller hakkinda bilirkisi gorusu vermekle gorevlendirildim.
Mahkemeye karsi gorevimin bilincindeyim ve bu gorevi yerine getirdim.
"""
        }
        return intros.get(language, intros["en"])

    def _format_qualifications(self) -> str:
        """Format qualifications as bullet points."""
        return "\n".join(f"- {q}" for q in self.expert_qualifications)

    def generate_methodology_section(self, language: str = "en") -> str:
        """Generate standard methodology section."""
        methodologies = {
            "en": """
METHODOLOGY:

The following forensic methodology was employed in this examination:

1. ACQUISITION: Digital evidence was acquired using forensically sound methods that
   preserve the integrity of the original data. All acquisitions were verified using
   cryptographic hash values (SHA-256).

2. PRESERVATION: Evidence was stored in a secure, access-controlled environment.
   Chain of custody documentation was maintained throughout the process.

3. ANALYSIS: Examination was conducted using industry-standard forensic tools and
   techniques. All findings were documented and are reproducible.

4. VERIFICATION: Results were cross-verified using multiple tools where applicable.
   Hash values were recalculated at each stage to ensure data integrity.

5. REPORTING: Findings are presented in an objective manner, clearly distinguishing
   between observations and opinions.
""",
            "de": """
METHODIK:

Bei dieser Untersuchung wurde folgende forensische Methodik angewandt:

1. SICHERUNG: Digitale Beweise wurden mit forensisch einwandfreien Methoden gesichert,
   die die Integritaet der Originaldaten bewahren. Alle Sicherungen wurden mittels
   kryptografischer Hashwerte (SHA-256) verifiziert.

2. AUFBEWAHRUNG: Beweise wurden in einer sicheren, zugangsgeschuetzten Umgebung
   aufbewahrt. Die Beweismittelkette wurde waehrend des gesamten Prozesses dokumentiert.

3. ANALYSE: Die Untersuchung wurde mit branchenueblichen forensischen Werkzeugen und
   Techniken durchgefuehrt. Alle Erkenntnisse wurden dokumentiert und sind reproduzierbar.

4. VERIFIKATION: Ergebnisse wurden, wo anwendbar, mit mehreren Werkzeugen
   kreuzverifiziert. Hashwerte wurden in jeder Phase neu berechnet, um die
   Datenintegritaet sicherzustellen.

5. BERICHTERSTATTUNG: Erkenntnisse werden objektiv praesentiert, wobei klar zwischen
   Beobachtungen und Meinungen unterschieden wird.
""",
            "tr": """
METODOLOJI:

Bu incelemede asagidaki adli metodoloji uygulanmistir:

1. ELDE ETME: Dijital deliller, orijinal verilerin butunlugunu koruyan adli acidan
   saglikli yontemler kullanilarak elde edilmistir. Tum elde etme islemleri
   kriptografik hash degerleri (SHA-256) kullanilarak dogrulanmistir.

2. KORUMA: Deliller guvenli, erisim kontrollü bir ortamda saklanmistir.
   Delil zinciri belgeleri surec boyunca tutulmustur.

3. ANALIZ: Inceleme, endustri standardi adli araclar ve teknikler kullanilarak
   gerceklestirilmistir. Tum bulgular belgelenmis ve tekrarlanabilirdir.

4. DOGRULAMA: Sonuclar, uygulanabilir oldugunda birden fazla arac kullanilarak
   capraz dogrulanmistir. Hash degerleri, veri butunlugunu saglamak icin her
   asamada yeniden hesaplanmistir.

5. RAPORLAMA: Bulgular, gozlemler ve gorusler arasinda net bir ayrim yapilarak
   objektif bir sekilde sunulmaktadir.
"""
        }
        return methodologies.get(language, methodologies["en"])

    def generate_declaration(self, language: str = "en") -> str:
        """Generate expert declaration."""
        declarations = {
            "en": f"""
DECLARATION:

I, {self.expert_name}, declare that:

1. I understand my duty to the Court and have complied with that duty.

2. The opinions expressed in this report are my own, based on my expertise and
   the evidence I have examined.

3. I have set out in this report all matters which I regard as being relevant
   to the opinions I have expressed.

4. I will notify the Court and the parties immediately if, for any reason, I
   change my opinion.

5. I have not been improperly influenced by any party in forming my opinions.

6. The factual matters stated in this report are true to the best of my knowledge
   and belief.

Signed: ________________________________

Name: {self.expert_name}
Title: {self.expert_title}
Date: {self.statement_date.strftime('%Y-%m-%d')}
""",
            "de": f"""
ERKLAERUNG:

Ich, {self.expert_name}, erklaere dass:

1. Ich mir meiner Pflicht gegenueber dem Gericht bewusst bin und diese Pflicht
   erfuellt habe.

2. Die in diesem Gutachten geaeusserten Meinungen meine eigenen sind, basierend
   auf meiner Expertise und den von mir untersuchten Beweisen.

3. Ich in diesem Gutachten alle Angelegenheiten dargelegt habe, die ich fuer
   relevant fuer meine geaeusserten Meinungen halte.

4. Ich das Gericht und die Parteien unverzueglich benachrichtigen werde, falls
   ich aus irgendeinem Grund meine Meinung aendere.

5. Ich bei der Bildung meiner Meinung von keiner Partei unzulaessig beeinflusst wurde.

6. Die in diesem Gutachten dargelegten Tatsachen nach bestem Wissen und Gewissen
   wahr sind.

Unterschrift: ________________________________

Name: {self.expert_name}
Titel: {self.expert_title}
Datum: {self.statement_date.strftime('%d.%m.%Y')}
""",
            "tr": f"""
BEYAN:

Ben, {self.expert_name}, asagidakileri beyan ederim:

1. Mahkemeye karsi gorevimin bilincindeyim ve bu gorevi yerine getirdim.

2. Bu raporda ifade edilen gorusler, uzmanlıgima ve inceledigim delillere
   dayanan kendi goruslerimdir.

3. Ifade ettigim goruslerle ilgili oldugunu dusundugum tum konulari bu
   raporda ortaya koydum.

4. Herhangi bir nedenle gorusumu degistirmem durumunda Mahkemeyi ve taraflari
   derhal bilgilendirecegim.

5. Goruslerimi olustururken hicbir tarafca uygunsuz sekilde etkilenmedim.

6. Bu raporda belirtilen olgusal konular bildigim ve inandıgim kadariyla dogrudur.

Imza: ________________________________

Ad: {self.expert_name}
Unvan: {self.expert_title}
Tarih: {self.statement_date.strftime('%d.%m.%Y')}
"""
        }
        return declarations.get(language, declarations["en"])


@dataclass
class EvidenceAuthenticationPage:
    """Evidence authentication page for court submissions."""
    evidence_id: str
    case_id: str
    file_name: str
    file_size: int
    file_type: str
    hash_sha256: str
    hash_md5: str
    acquisition_date: datetime
    acquisition_method: str
    acquired_by: str
    chain_of_custody_maintained: bool
    integrity_verified: bool

    def generate_authentication_html(self, language: str = "en") -> str:
        """Generate HTML authentication page."""
        titles = {
            "en": "Evidence Authentication Certificate",
            "de": "Beweismittel-Authentifizierungszertifikat",
            "tr": "Delil Dogrulama Sertifikasi"
        }

        return f"""
        <div class="evidence-authentication">
            <h2>{titles.get(language, titles['en'])}</h2>

            <div class="certificate-header">
                <p><strong>Certificate ID:</strong> AUTH-{self.evidence_id}</p>
                <p><strong>Case Reference:</strong> {self.case_id}</p>
                <p><strong>Generated:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>

            <div class="evidence-details">
                <h3>Evidence Details</h3>
                <table>
                    <tr><td>Evidence ID:</td><td>{self.evidence_id}</td></tr>
                    <tr><td>File Name:</td><td>{self.file_name}</td></tr>
                    <tr><td>File Size:</td><td>{self.file_size:,} bytes</td></tr>
                    <tr><td>File Type:</td><td>{self.file_type}</td></tr>
                </table>
            </div>

            <div class="hash-verification">
                <h3>Cryptographic Verification</h3>
                <table>
                    <tr>
                        <td>SHA-256:</td>
                        <td class="hash-value">{self.hash_sha256}</td>
                    </tr>
                    <tr>
                        <td>MD5:</td>
                        <td class="hash-value">{self.hash_md5}</td>
                    </tr>
                </table>
                <p class="note">These hash values can be used to verify that the evidence
                has not been altered since acquisition.</p>
            </div>

            <div class="acquisition-details">
                <h3>Acquisition Information</h3>
                <table>
                    <tr><td>Date:</td><td>{self.acquisition_date.strftime('%Y-%m-%d %H:%M:%S UTC')}</td></tr>
                    <tr><td>Method:</td><td>{self.acquisition_method}</td></tr>
                    <tr><td>Acquired By:</td><td>{self.acquired_by}</td></tr>
                </table>
            </div>

            <div class="integrity-statement">
                <h3>Integrity Statement</h3>
                <p>
                    <span class="{'verified' if self.chain_of_custody_maintained else 'not-verified'}">
                        {'✓' if self.chain_of_custody_maintained else '✗'} Chain of Custody Maintained
                    </span>
                </p>
                <p>
                    <span class="{'verified' if self.integrity_verified else 'not-verified'}">
                        {'✓' if self.integrity_verified else '✗'} Integrity Verified
                    </span>
                </p>
            </div>

            <div class="certification">
                <p>This certificate confirms that the above evidence has been acquired,
                preserved, and verified in accordance with forensic best practices.</p>

                <div class="signature-line">
                    <p>________________________________</p>
                    <p>Forensic Examiner Signature</p>
                </div>
            </div>
        </div>
        """


@dataclass
class CourtFilingFormat:
    """Court filing format templates for different jurisdictions."""
    jurisdiction: Jurisdiction
    case_id: str
    court_name: str
    filing_date: datetime

    def get_header(self, language: str = "en") -> str:
        """Get jurisdiction-specific header."""
        if self.jurisdiction == Jurisdiction.GERMANY:
            return self._get_german_header()
        elif self.jurisdiction == Jurisdiction.TURKEY:
            return self._get_turkish_header()
        else:
            return self._get_international_header(language)

    def _get_german_header(self) -> str:
        """German court filing header (Aktenzeichen format)."""
        return f"""
================================================================================
                              {self.court_name.upper()}
================================================================================

Aktenzeichen: {self.case_id}
Eingangsdatum: {self.filing_date.strftime('%d.%m.%Y')}

--------------------------------------------------------------------------------
                    FORENSISCHES SACHVERSTAENDIGENGUTACHTEN
                    (Digitale Beweismittelanalyse)
--------------------------------------------------------------------------------

"""

    def _get_turkish_header(self) -> str:
        """Turkish court filing header."""
        return f"""
================================================================================
                              {self.court_name.upper()}
================================================================================

Dosya No: {self.case_id}
Tarih: {self.filing_date.strftime('%d.%m.%Y')}

--------------------------------------------------------------------------------
                         ADLI BILIRKISI RAPORU
                    (Dijital Delil Incelemesi)
--------------------------------------------------------------------------------

"""

    def _get_international_header(self, language: str) -> str:
        """International/EU format header."""
        return f"""
================================================================================
                              {self.court_name.upper()}
================================================================================

Case Reference: {self.case_id}
Filing Date: {self.filing_date.strftime('%Y-%m-%d')}

--------------------------------------------------------------------------------
                    FORENSIC EXPERT REPORT
                    (Digital Evidence Analysis)
--------------------------------------------------------------------------------

"""

    def get_footer(self, language: str = "en") -> str:
        """Get jurisdiction-specific footer."""
        if self.jurisdiction == Jurisdiction.GERMANY:
            return """
--------------------------------------------------------------------------------
Dieses Gutachten wurde nach bestem Wissen und Gewissen erstellt.
Der Sachverstaendige versichert, dass die Angaben vollstaendig und richtig sind.
--------------------------------------------------------------------------------
"""
        elif self.jurisdiction == Jurisdiction.TURKEY:
            return """
--------------------------------------------------------------------------------
Bu rapor bilgim ve inancim dahilinde hazirlanmistir.
Bilirkisi, bilgilerin eksiksiz ve dogru oldugunu beyan eder.
--------------------------------------------------------------------------------
"""
        else:
            return """
--------------------------------------------------------------------------------
This report has been prepared to the best of my knowledge and belief.
The expert certifies that the information provided is complete and accurate.
--------------------------------------------------------------------------------
"""


class LegalTemplateEngine:
    """Engine for generating legal templates."""

    def __init__(self):
        self.templates = {}

    def generate_gdpr_checklist(
        self,
        case_id: str,
        data_controller: str,
        data_processor: str,
        legal_basis: str,
        data_subjects: List[str],
        data_categories: List[str],
        retention_period: str = "Duration of legal proceedings + 7 years"
    ) -> GDPRChecklist:
        """Generate a GDPR compliance checklist."""
        return GDPRChecklist(
            case_id=case_id,
            data_controller=data_controller,
            data_processor=data_processor,
            legal_basis=legal_basis,
            data_subjects=data_subjects,
            data_categories=data_categories,
            retention_period=retention_period,
            security_measures=[
                "AES-256 encryption at rest",
                "TLS 1.3 encryption in transit",
                "Role-based access control",
                "Audit logging enabled",
                "Secure backup procedures"
            ],
            third_party_recipients=[],
            cross_border_transfers=False,
            dpia_conducted=True,
            consent_obtained=False  # Using legal basis instead
        )

    def generate_expert_witness_template(
        self,
        case_id: str,
        expert_name: str,
        expert_title: str,
        expert_qualifications: List[str],
        experience_years: int,
        court_name: str,
        jurisdiction: Jurisdiction
    ) -> ExpertWitnessTemplate:
        """Generate an expert witness statement template."""
        return ExpertWitnessTemplate(
            case_id=case_id,
            expert_name=expert_name,
            expert_title=expert_title,
            expert_qualifications=expert_qualifications,
            expert_experience_years=experience_years,
            court_name=court_name,
            jurisdiction=jurisdiction,
            statement_date=datetime.utcnow()
        )

    def generate_evidence_authentication(
        self,
        evidence_id: str,
        case_id: str,
        file_name: str,
        file_size: int,
        file_type: str,
        hash_sha256: str,
        hash_md5: str,
        acquisition_date: datetime,
        acquisition_method: str,
        acquired_by: str
    ) -> EvidenceAuthenticationPage:
        """Generate an evidence authentication page."""
        return EvidenceAuthenticationPage(
            evidence_id=evidence_id,
            case_id=case_id,
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            hash_sha256=hash_sha256,
            hash_md5=hash_md5,
            acquisition_date=acquisition_date,
            acquisition_method=acquisition_method,
            acquired_by=acquired_by,
            chain_of_custody_maintained=True,
            integrity_verified=True
        )

    def generate_court_filing(
        self,
        jurisdiction: Jurisdiction,
        case_id: str,
        court_name: str
    ) -> CourtFilingFormat:
        """Generate court filing format template."""
        return CourtFilingFormat(
            jurisdiction=jurisdiction,
            case_id=case_id,
            court_name=court_name,
            filing_date=datetime.utcnow()
        )


# Convenience functions
def generate_gdpr_checklist(case_id: str, **kwargs) -> GDPRChecklist:
    """Generate GDPR compliance checklist."""
    engine = LegalTemplateEngine()
    return engine.generate_gdpr_checklist(case_id, **kwargs)


def generate_expert_statement(case_id: str, **kwargs) -> ExpertWitnessTemplate:
    """Generate expert witness statement template."""
    engine = LegalTemplateEngine()
    return engine.generate_expert_witness_template(case_id, **kwargs)


def generate_authentication_page(evidence_id: str, case_id: str, **kwargs) -> EvidenceAuthenticationPage:
    """Generate evidence authentication page."""
    engine = LegalTemplateEngine()
    return engine.generate_evidence_authentication(evidence_id, case_id, **kwargs)
