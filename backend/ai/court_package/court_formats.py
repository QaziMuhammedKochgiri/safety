"""
Court Formats
German, Turkish, and EU E001 court format templates.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime
from abc import ABC, abstractmethod


class CourtFormat(str, Enum):
    """Available court formats."""
    GERMAN_FAMILY = "german_family"
    TURKISH_FAMILY = "turkish_family"
    EU_E001 = "eu_e001"
    US_FAMILY = "us_family"
    INTERNATIONAL = "international"


class DocumentLanguage(str, Enum):
    """Document languages."""
    ENGLISH = "en"
    GERMAN = "de"
    TURKISH = "tr"
    FRENCH = "fr"
    SPANISH = "es"


@dataclass
class CoverPage:
    """Cover page content."""
    court_name: str
    case_number: str
    case_title: str
    petitioner: str
    respondent: str
    document_title: str
    filing_date: datetime
    attorney_name: Optional[str] = None
    attorney_address: Optional[str] = None
    attorney_phone: Optional[str] = None
    attorney_email: Optional[str] = None
    attorney_bar_number: Optional[str] = None
    judge_name: Optional[str] = None
    hearing_date: Optional[datetime] = None
    logo_path: Optional[str] = None
    additional_info: Dict[str, str] = field(default_factory=dict)


@dataclass
class TableOfContents:
    """Table of contents structure."""
    entries: List[Dict[str, Any]]  # [{title, page_start, page_end, level}]
    show_page_numbers: bool = True
    show_exhibit_numbers: bool = True
    multilevel: bool = True
    language: str = "en"


class CourtFormatBase(ABC):
    """Base class for court format generators."""

    def __init__(self, language: str = "en"):
        self.language = language
        self.date_format = "%Y-%m-%d"
        self.page_size = "A4"
        self.margins = {"top": 25, "bottom": 25, "left": 30, "right": 20}
        self.font_family = "Times New Roman"
        self.font_size = 12
        self.line_spacing = 1.5

    @abstractmethod
    def generate_cover_page(self, cover: CoverPage) -> str:
        """Generate cover page content."""
        pass

    @abstractmethod
    def generate_table_of_contents(self, toc: TableOfContents) -> str:
        """Generate table of contents."""
        pass

    @abstractmethod
    def format_exhibit_label(self, number: int) -> str:
        """Format exhibit label."""
        pass

    @abstractmethod
    def get_section_headers(self) -> Dict[str, str]:
        """Get section header translations."""
        pass


class GermanFamilyCourt(CourtFormatBase):
    """German Family Court (Familiengericht) format."""

    def __init__(self, language: str = "de"):
        super().__init__(language)
        self.date_format = "%d.%m.%Y"
        self.page_size = "A4"
        self.margins = {"top": 25, "bottom": 25, "left": 30, "right": 20}

    def generate_cover_page(self, cover: CoverPage) -> str:
        """Generate German family court cover page."""
        templates = {
            "de": {
                "in_matter": "In der Familiensache",
                "petitioner": "Antragsteller/in",
                "respondent": "Antragsgegner/in",
                "case_number": "Aktenzeichen",
                "before": "Vor dem",
                "submitted_by": "Eingereicht von",
                "date": "Datum",
                "address": "Anschrift",
                "phone": "Telefon",
                "email": "E-Mail",
                "bar_number": "Zulassungsnummer"
            },
            "en": {
                "in_matter": "In the Matter of",
                "petitioner": "Petitioner",
                "respondent": "Respondent",
                "case_number": "Case Number",
                "before": "Before the",
                "submitted_by": "Submitted by",
                "date": "Date",
                "address": "Address",
                "phone": "Phone",
                "email": "Email",
                "bar_number": "Bar Number"
            }
        }

        t = templates.get(self.language, templates["de"])

        lines = [
            "",
            "",
            f"                    {t['before']}",
            f"                    {cover.court_name}",
            "",
            f"                    {t['case_number']}: {cover.case_number}",
            "",
            "",
            f"                    {t['in_matter']}:",
            "",
            f"                    {cover.case_title}",
            "",
            "",
            f"{t['petitioner']}:",
            f"    {cover.petitioner}",
            "",
            f"{t['respondent']}:",
            f"    {cover.respondent}",
            "",
            "",
            "",
            f"                    {cover.document_title}",
            "",
            "",
            "",
        ]

        if cover.attorney_name:
            lines.extend([
                f"{t['submitted_by']}:",
                f"    {cover.attorney_name}",
            ])
            if cover.attorney_address:
                lines.append(f"    {t['address']}: {cover.attorney_address}")
            if cover.attorney_phone:
                lines.append(f"    {t['phone']}: {cover.attorney_phone}")
            if cover.attorney_email:
                lines.append(f"    {t['email']}: {cover.attorney_email}")
            if cover.attorney_bar_number:
                lines.append(f"    {t['bar_number']}: {cover.attorney_bar_number}")

        lines.extend([
            "",
            "",
            f"{t['date']}: {cover.filing_date.strftime(self.date_format)}"
        ])

        return "\n".join(lines)

    def generate_table_of_contents(self, toc: TableOfContents) -> str:
        """Generate German table of contents."""
        headers = {
            "de": "INHALTSVERZEICHNIS",
            "en": "TABLE OF CONTENTS"
        }

        header = headers.get(self.language, headers["de"])
        lines = [header, "=" * 60, ""]

        for entry in toc.entries:
            indent = "    " * (entry.get("level", 0))
            title = entry["title"]
            page = entry.get("page_start", "")

            if toc.show_page_numbers and page:
                dots = "." * (50 - len(indent) - len(title))
                lines.append(f"{indent}{title}{dots}{page}")
            else:
                lines.append(f"{indent}{title}")

        return "\n".join(lines)

    def format_exhibit_label(self, number: int) -> str:
        """Format German exhibit label."""
        return f"Anlage {number}"

    def get_section_headers(self) -> Dict[str, str]:
        """Get German section headers."""
        if self.language == "de":
            return {
                "cover": "Deckblatt",
                "toc": "Inhaltsverzeichnis",
                "summary": "Zusammenfassung",
                "facts": "Sachverhalt",
                "arguments": "Rechtliche Würdigung",
                "evidence": "Beweismittel",
                "exhibits": "Anlagen",
                "conclusion": "Antrag",
                "certification": "Zustellungsbescheinigung"
            }
        else:
            return {
                "cover": "Cover Page",
                "toc": "Table of Contents",
                "summary": "Executive Summary",
                "facts": "Statement of Facts",
                "arguments": "Legal Arguments",
                "evidence": "Evidence Summary",
                "exhibits": "Exhibits",
                "conclusion": "Conclusion",
                "certification": "Certificate of Service"
            }

    def generate_antrag(self, requests: List[str]) -> str:
        """Generate German court petition (Antrag)."""
        templates = {
            "de": {
                "header": "ANTRAG",
                "intro": "Namens und im Auftrag des/der Antragsteller/in wird beantragt:",
                "item_prefix": ""
            },
            "en": {
                "header": "PETITION",
                "intro": "On behalf of the Petitioner, it is requested that:",
                "item_prefix": ""
            }
        }

        t = templates.get(self.language, templates["de"])

        lines = [
            t["header"],
            "",
            t["intro"],
            ""
        ]

        for i, request in enumerate(requests, 1):
            lines.append(f"    {i}. {request}")
            lines.append("")

        return "\n".join(lines)


class TurkishFamilyCourt(CourtFormatBase):
    """Turkish Family Court (Aile Mahkemesi) format."""

    def __init__(self, language: str = "tr"):
        super().__init__(language)
        self.date_format = "%d/%m/%Y"
        self.page_size = "A4"
        self.margins = {"top": 20, "bottom": 20, "left": 25, "right": 20}

    def generate_cover_page(self, cover: CoverPage) -> str:
        """Generate Turkish family court cover page."""
        templates = {
            "tr": {
                "court": "Sayın",
                "hakimlik": "HAKİMLİĞİ'NE",
                "case_number": "Dosya No",
                "plaintiff": "DAVACI",
                "defendant": "DAVALI",
                "subject": "KONU",
                "date": "Tarih",
                "attorney": "Vekili",
                "address": "Adres",
                "phone": "Tel",
                "email": "E-posta"
            },
            "en": {
                "court": "To the Honorable",
                "hakimlik": "COURT",
                "case_number": "File No",
                "plaintiff": "PLAINTIFF",
                "defendant": "DEFENDANT",
                "subject": "SUBJECT",
                "date": "Date",
                "attorney": "Attorney",
                "address": "Address",
                "phone": "Phone",
                "email": "Email"
            }
        }

        t = templates.get(self.language, templates["tr"])

        lines = [
            "",
            f"                    {t['court']}",
            f"                    {cover.court_name}",
            f"                    {t['hakimlik']}",
            "",
            f"                    {t['case_number']}: {cover.case_number}",
            "",
            "",
            f"{t['plaintiff']}    : {cover.petitioner}",
        ]

        if cover.attorney_name:
            lines.append(f"{t['attorney']}     : {cover.attorney_name}")

        lines.extend([
            "",
            f"{t['defendant']}     : {cover.respondent}",
            "",
            f"{t['subject']}       : {cover.document_title}",
            "",
            "",
        ])

        if cover.attorney_address:
            lines.append(f"{t['address']}        : {cover.attorney_address}")
        if cover.attorney_phone:
            lines.append(f"{t['phone']}           : {cover.attorney_phone}")
        if cover.attorney_email:
            lines.append(f"{t['email']}        : {cover.attorney_email}")

        lines.extend([
            "",
            "",
            f"{t['date']}: {cover.filing_date.strftime(self.date_format)}"
        ])

        return "\n".join(lines)

    def generate_table_of_contents(self, toc: TableOfContents) -> str:
        """Generate Turkish table of contents."""
        headers = {
            "tr": "İÇİNDEKİLER",
            "en": "TABLE OF CONTENTS"
        }

        header = headers.get(self.language, headers["tr"])
        lines = [header, "=" * 60, ""]

        for entry in toc.entries:
            indent = "    " * (entry.get("level", 0))
            title = entry["title"]
            page = entry.get("page_start", "")

            if toc.show_page_numbers and page:
                dots = "." * (50 - len(indent) - len(title))
                lines.append(f"{indent}{title}{dots}{page}")
            else:
                lines.append(f"{indent}{title}")

        return "\n".join(lines)

    def format_exhibit_label(self, number: int) -> str:
        """Format Turkish exhibit label."""
        return f"Ek {number}"

    def get_section_headers(self) -> Dict[str, str]:
        """Get Turkish section headers."""
        if self.language == "tr":
            return {
                "cover": "Kapak",
                "toc": "İçindekiler",
                "summary": "Özet",
                "facts": "Olaylar",
                "arguments": "Hukuki Değerlendirme",
                "evidence": "Deliller",
                "exhibits": "Ekler",
                "conclusion": "Sonuç ve Talep",
                "certification": "Tebliğ Belgesi"
            }
        else:
            return {
                "cover": "Cover Page",
                "toc": "Table of Contents",
                "summary": "Summary",
                "facts": "Facts",
                "arguments": "Legal Evaluation",
                "evidence": "Evidence",
                "exhibits": "Appendices",
                "conclusion": "Conclusion and Request",
                "certification": "Service Certificate"
            }

    def generate_talep(self, requests: List[str]) -> str:
        """Generate Turkish petition section (Sonuç ve Talep)."""
        templates = {
            "tr": {
                "header": "SONUÇ VE TALEP",
                "intro": "Yukarıda arz ve izah edilen nedenlerle;",
                "respectfully": "saygılarımızla arz ve talep ederiz."
            },
            "en": {
                "header": "CONCLUSION AND REQUEST",
                "intro": "For the reasons explained above;",
                "respectfully": "we respectfully request."
            }
        }

        t = templates.get(self.language, templates["tr"])

        lines = [
            t["header"],
            "",
            t["intro"],
            ""
        ]

        for i, request in enumerate(requests, 1):
            lines.append(f"    {i}- {request}")
            lines.append("")

        lines.extend([
            "",
            t["respectfully"]
        ])

        return "\n".join(lines)


class EUE001Format(CourtFormatBase):
    """EU E001 European Enforcement Order format."""

    def __init__(self, language: str = "en"):
        super().__init__(language)
        self.date_format = "%Y-%m-%d"
        self.page_size = "A4"
        self.margins = {"top": 25, "bottom": 25, "left": 25, "right": 25}
        self.font_size = 11
        self.line_spacing = 1.15

    def generate_cover_page(self, cover: CoverPage) -> str:
        """Generate EU E001 format cover page."""
        templates = {
            "en": {
                "form_title": "EUROPEAN ENFORCEMENT ORDER",
                "form_number": "Form E001",
                "regulation": "(Regulation (EC) No 805/2004)",
                "court_origin": "Court of Origin",
                "case_ref": "Case Reference",
                "claimant": "Claimant (Creditor)",
                "defendant": "Defendant (Debtor)",
                "date_judgment": "Date of Judgment",
                "date_certificate": "Date of Certificate"
            },
            "de": {
                "form_title": "EUROPÄISCHER VOLLSTRECKUNGSTITEL",
                "form_number": "Formblatt E001",
                "regulation": "(Verordnung (EG) Nr. 805/2004)",
                "court_origin": "Ursprungsgericht",
                "case_ref": "Aktenzeichen",
                "claimant": "Gläubiger",
                "defendant": "Schuldner",
                "date_judgment": "Datum des Urteils",
                "date_certificate": "Datum der Bescheinigung"
            },
            "fr": {
                "form_title": "TITRE EXÉCUTOIRE EUROPÉEN",
                "form_number": "Formulaire E001",
                "regulation": "(Règlement (CE) n° 805/2004)",
                "court_origin": "Juridiction d'origine",
                "case_ref": "Référence du dossier",
                "claimant": "Créancier",
                "defendant": "Débiteur",
                "date_judgment": "Date du jugement",
                "date_certificate": "Date du certificat"
            }
        }

        t = templates.get(self.language, templates["en"])

        lines = [
            "",
            f"                    {t['form_title']}",
            f"                    {t['form_number']}",
            f"                    {t['regulation']}",
            "",
            "=" * 70,
            "",
            f"1. {t['court_origin']}:",
            f"   {cover.court_name}",
            "",
            f"2. {t['case_ref']}:",
            f"   {cover.case_number}",
            "",
            f"3. {t['claimant']}:",
            f"   {cover.petitioner}",
            "",
            f"4. {t['defendant']}:",
            f"   {cover.respondent}",
            "",
            f"5. {t['date_judgment']}:",
            f"   {cover.filing_date.strftime(self.date_format)}",
            "",
            f"6. {t['date_certificate']}:",
            f"   {datetime.utcnow().strftime(self.date_format)}",
            "",
            "=" * 70
        ]

        return "\n".join(lines)

    def generate_table_of_contents(self, toc: TableOfContents) -> str:
        """Generate EU format table of contents."""
        headers = {
            "en": "CONTENTS",
            "de": "INHALT",
            "fr": "SOMMAIRE"
        }

        header = headers.get(self.language, headers["en"])
        lines = [header, "-" * 60, ""]

        for entry in toc.entries:
            level = entry.get("level", 0)
            if level == 0:
                prefix = ""
            elif level == 1:
                prefix = "    "
            else:
                prefix = "        "

            title = entry["title"]
            page = entry.get("page_start", "")

            if toc.show_page_numbers and page:
                space = " " * (50 - len(prefix) - len(title))
                lines.append(f"{prefix}{title}{space}{page}")
            else:
                lines.append(f"{prefix}{title}")

        return "\n".join(lines)

    def format_exhibit_label(self, number: int) -> str:
        """Format EU exhibit label."""
        return f"Exhibit {number}"

    def get_section_headers(self) -> Dict[str, str]:
        """Get EU E001 section headers."""
        if self.language == "de":
            return {
                "cover": "Deckblatt",
                "toc": "Inhalt",
                "summary": "Zusammenfassung",
                "facts": "Sachverhalt",
                "arguments": "Rechtliche Begründung",
                "evidence": "Beweismittel",
                "exhibits": "Anlagen",
                "conclusion": "Schlussfolgerung",
                "certification": "Bescheinigung"
            }
        elif self.language == "fr":
            return {
                "cover": "Page de garde",
                "toc": "Sommaire",
                "summary": "Résumé",
                "facts": "Exposé des faits",
                "arguments": "Arguments juridiques",
                "evidence": "Preuves",
                "exhibits": "Pièces jointes",
                "conclusion": "Conclusion",
                "certification": "Certification"
            }
        else:
            return {
                "cover": "Cover Page",
                "toc": "Contents",
                "summary": "Summary",
                "facts": "Statement of Facts",
                "arguments": "Legal Arguments",
                "evidence": "Evidence",
                "exhibits": "Exhibits",
                "conclusion": "Conclusion",
                "certification": "Certification"
            }

    def generate_bates_stamp(self, case_id: str, page_number: int) -> str:
        """Generate Bates stamp for EU format."""
        return f"{case_id[:8].upper()}-{page_number:06d}"


class CourtFormatGenerator:
    """Factory for court format generators."""

    FORMATS = {
        CourtFormat.GERMAN_FAMILY: GermanFamilyCourt,
        CourtFormat.TURKISH_FAMILY: TurkishFamilyCourt,
        CourtFormat.EU_E001: EUE001Format
    }

    @classmethod
    def get_format(
        cls,
        format_type: CourtFormat,
        language: str = "en"
    ) -> CourtFormatBase:
        """Get court format generator."""
        format_class = cls.FORMATS.get(format_type)
        if not format_class:
            raise ValueError(f"Unknown format: {format_type}")

        return format_class(language=language)

    @classmethod
    def get_available_formats(cls) -> List[Dict[str, Any]]:
        """Get list of available formats."""
        return [
            {
                "format": CourtFormat.GERMAN_FAMILY.value,
                "name": {
                    "en": "German Family Court",
                    "de": "Deutsches Familiengericht",
                    "tr": "Alman Aile Mahkemesi"
                },
                "languages": ["de", "en"],
                "page_size": "A4",
                "exhibit_format": "Anlage {n}"
            },
            {
                "format": CourtFormat.TURKISH_FAMILY.value,
                "name": {
                    "en": "Turkish Family Court",
                    "de": "Türkisches Familiengericht",
                    "tr": "Türk Aile Mahkemesi"
                },
                "languages": ["tr", "en"],
                "page_size": "A4",
                "exhibit_format": "Ek {n}"
            },
            {
                "format": CourtFormat.EU_E001.value,
                "name": {
                    "en": "EU E001 Format",
                    "de": "EU E001 Format",
                    "tr": "AB E001 Formatı"
                },
                "languages": ["en", "de", "fr"],
                "page_size": "A4",
                "exhibit_format": "Exhibit {n}"
            }
        ]

    @classmethod
    def generate_complete_package(
        cls,
        format_type: CourtFormat,
        cover_info: CoverPage,
        toc_entries: List[Dict[str, Any]],
        content_sections: Dict[str, str],
        language: str = "en"
    ) -> Dict[str, str]:
        """Generate complete court package with all sections."""
        formatter = cls.get_format(format_type, language)

        # Generate cover page
        cover_page = formatter.generate_cover_page(cover_info)

        # Generate table of contents
        toc = TableOfContents(
            entries=toc_entries,
            show_page_numbers=True,
            language=language
        )
        table_of_contents = formatter.generate_table_of_contents(toc)

        # Get section headers
        headers = formatter.get_section_headers()

        # Build complete document
        document = {
            "cover_page": cover_page,
            "table_of_contents": table_of_contents,
            "section_headers": headers,
            "format_info": {
                "format": format_type.value,
                "language": language,
                "date_format": formatter.date_format,
                "page_size": formatter.page_size
            }
        }

        # Add content sections
        for section_key, content in content_sections.items():
            header = headers.get(section_key, section_key.upper())
            document[section_key] = f"\n{header}\n{'=' * len(header)}\n\n{content}"

        return document
