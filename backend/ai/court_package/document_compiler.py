"""
Document Compiler
Page limit compliance and court document formatting.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
from datetime import datetime
import hashlib


class DocumentSection(str, Enum):
    """Sections of a court document."""
    COVER_PAGE = "cover_page"
    TABLE_OF_CONTENTS = "table_of_contents"
    EXECUTIVE_SUMMARY = "executive_summary"
    INTRODUCTION = "introduction"
    STATEMENT_OF_FACTS = "statement_of_facts"
    LEGAL_ARGUMENTS = "legal_arguments"
    EVIDENCE_SUMMARY = "evidence_summary"
    WITNESS_LIST = "witness_list"
    EXHIBITS = "exhibits"
    CONCLUSION = "conclusion"
    APPENDICES = "appendices"
    CERTIFICATION = "certification"


class PageSize(str, Enum):
    """Page size standards."""
    A4 = "A4"  # 210 x 297 mm (European standard)
    LETTER = "letter"  # 8.5 x 11 inches (US standard)
    LEGAL = "legal"  # 8.5 x 14 inches (US legal)


@dataclass
class PageLimitConfig:
    """Configuration for page limits."""
    court_format: str
    max_total_pages: int = 500
    max_main_body_pages: int = 100
    max_exhibits_pages: int = 400
    max_appendices_pages: int = 100
    page_size: PageSize = PageSize.A4
    font_size: int = 12
    line_spacing: float = 1.5
    margins_mm: Dict[str, int] = field(default_factory=lambda: {
        "top": 25, "bottom": 25, "left": 30, "right": 20
    })
    chars_per_page: int = 2500  # Estimated characters per page
    require_page_numbers: bool = True
    require_bates_stamps: bool = False


@dataclass
class DocumentPage:
    """A single page in the compiled document."""
    page_number: int
    section: DocumentSection
    content: str
    bates_number: Optional[str] = None
    exhibit_id: Optional[str] = None
    is_continuation: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CourtDocument:
    """A complete court document package."""
    document_id: str
    case_id: str
    title: str
    court_name: str
    case_number: str
    filing_date: datetime
    pages: List[DocumentPage]
    sections: Dict[DocumentSection, Tuple[int, int]]  # section -> (start_page, end_page)
    total_pages: int
    total_exhibits: int
    table_of_contents: List[Dict[str, Any]]
    document_hash: str
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompilationResult:
    """Result of document compilation."""
    success: bool
    document: Optional[CourtDocument]
    warnings: List[str]
    errors: List[str]
    page_breakdown: Dict[DocumentSection, int]
    items_included: List[str]
    items_excluded: List[str]
    exclusion_reasons: Dict[str, str]
    processing_time_seconds: float


# Court-specific page limits and requirements
COURT_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "german_family": {
        "name": {
            "en": "German Family Court",
            "de": "Deutsches Familiengericht",
            "tr": "Alman Aile Mahkemesi"
        },
        "max_pages": 500,
        "max_main_body": 100,
        "max_exhibits": 400,
        "page_size": PageSize.A4,
        "font_size": 12,
        "line_spacing": 1.5,
        "margins_mm": {"top": 25, "bottom": 25, "left": 30, "right": 20},
        "require_translation": True,
        "require_certification": True,
        "bates_stamps": False,
        "exhibit_format": "Anlage {number}",
        "date_format": "%d.%m.%Y"
    },
    "turkish_family": {
        "name": {
            "en": "Turkish Family Court",
            "de": "Türkisches Familiengericht",
            "tr": "Türk Aile Mahkemesi"
        },
        "max_pages": 300,
        "max_main_body": 50,
        "max_exhibits": 250,
        "page_size": PageSize.A4,
        "font_size": 12,
        "line_spacing": 1.5,
        "margins_mm": {"top": 20, "bottom": 20, "left": 25, "right": 20},
        "require_translation": True,
        "require_certification": True,
        "bates_stamps": False,
        "exhibit_format": "Ek {number}",
        "date_format": "%d/%m/%Y"
    },
    "eu_e001": {
        "name": {
            "en": "EU E001 Format",
            "de": "EU E001 Format",
            "tr": "AB E001 Formatı"
        },
        "max_pages": 200,
        "max_main_body": 50,
        "max_exhibits": 150,
        "page_size": PageSize.A4,
        "font_size": 11,
        "line_spacing": 1.15,
        "margins_mm": {"top": 25, "bottom": 25, "left": 25, "right": 25},
        "require_translation": True,
        "require_certification": True,
        "bates_stamps": True,
        "exhibit_format": "Exhibit {number}",
        "date_format": "%Y-%m-%d"
    },
    "us_family": {
        "name": {
            "en": "US Family Court",
            "de": "US-Familiengericht",
            "tr": "ABD Aile Mahkemesi"
        },
        "max_pages": 500,
        "max_main_body": 100,
        "max_exhibits": 400,
        "page_size": PageSize.LETTER,
        "font_size": 12,
        "line_spacing": 2.0,
        "margins_mm": {"top": 25, "bottom": 25, "left": 25, "right": 25},
        "require_translation": False,
        "require_certification": True,
        "bates_stamps": True,
        "exhibit_format": "Exhibit {letter}",
        "date_format": "%m/%d/%Y"
    }
}


class DocumentCompiler:
    """Compiles evidence into court-ready document packages."""

    def __init__(self):
        self.current_page = 0
        self.bates_counter = 0
        self.exhibit_counter = 0

    def compile_document(
        self,
        case_id: str,
        case_info: Dict[str, Any],
        selected_evidence: List[Dict[str, Any]],
        court_format: str = "german_family",
        language: str = "en"
    ) -> CompilationResult:
        """Compile evidence into a court document package."""
        start_time = datetime.utcnow()

        court_config = COURT_REQUIREMENTS.get(court_format, COURT_REQUIREMENTS["german_family"])
        warnings: List[str] = []
        errors: List[str] = []
        items_included: List[str] = []
        items_excluded: List[str] = []
        exclusion_reasons: Dict[str, str] = {}

        # Reset counters
        self.current_page = 0
        self.bates_counter = 0
        self.exhibit_counter = 0

        # Create page limit config
        page_config = PageLimitConfig(
            court_format=court_format,
            max_total_pages=court_config["max_pages"],
            max_main_body_pages=court_config["max_main_body"],
            max_exhibits_pages=court_config["max_exhibits"],
            page_size=court_config["page_size"],
            font_size=court_config["font_size"],
            line_spacing=court_config["line_spacing"],
            margins_mm=court_config["margins_mm"],
            require_bates_stamps=court_config["bates_stamps"]
        )

        pages: List[DocumentPage] = []
        sections: Dict[DocumentSection, Tuple[int, int]] = {}
        page_breakdown: Dict[DocumentSection, int] = {}

        try:
            # 1. Cover page
            cover_pages = self._generate_cover_page(case_info, court_config, language)
            start_page = self.current_page + 1
            pages.extend(cover_pages)
            self.current_page += len(cover_pages)
            sections[DocumentSection.COVER_PAGE] = (start_page, self.current_page)
            page_breakdown[DocumentSection.COVER_PAGE] = len(cover_pages)

            # 2. Table of contents (placeholder, updated at end)
            toc_pages = self._generate_toc_placeholder()
            start_page = self.current_page + 1
            pages.extend(toc_pages)
            self.current_page += len(toc_pages)
            sections[DocumentSection.TABLE_OF_CONTENTS] = (start_page, self.current_page)
            page_breakdown[DocumentSection.TABLE_OF_CONTENTS] = len(toc_pages)

            # 3. Executive summary
            summary_pages = self._generate_executive_summary(
                case_info, selected_evidence, court_config, language
            )
            start_page = self.current_page + 1
            pages.extend(summary_pages)
            self.current_page += len(summary_pages)
            sections[DocumentSection.EXECUTIVE_SUMMARY] = (start_page, self.current_page)
            page_breakdown[DocumentSection.EXECUTIVE_SUMMARY] = len(summary_pages)

            # 4. Evidence summary
            evidence_summary_pages = self._generate_evidence_summary(
                selected_evidence, court_config, language
            )
            start_page = self.current_page + 1
            pages.extend(evidence_summary_pages)
            self.current_page += len(evidence_summary_pages)
            sections[DocumentSection.EVIDENCE_SUMMARY] = (start_page, self.current_page)
            page_breakdown[DocumentSection.EVIDENCE_SUMMARY] = len(evidence_summary_pages)

            # Check main body page limit
            main_body_pages = self.current_page
            if main_body_pages > page_config.max_main_body_pages:
                warnings.append(
                    f"Main body exceeds limit: {main_body_pages} > {page_config.max_main_body_pages} pages"
                )

            # 5. Exhibits
            exhibit_start = self.current_page + 1
            available_exhibit_pages = page_config.max_exhibits_pages
            exhibit_pages, included, excluded, reasons = self._compile_exhibits(
                selected_evidence,
                available_exhibit_pages,
                court_config,
                language
            )
            pages.extend(exhibit_pages)
            self.current_page += len(exhibit_pages)
            sections[DocumentSection.EXHIBITS] = (exhibit_start, self.current_page)
            page_breakdown[DocumentSection.EXHIBITS] = len(exhibit_pages)

            items_included.extend(included)
            items_excluded.extend(excluded)
            exclusion_reasons.update(reasons)

            # 6. Certification page
            cert_pages = self._generate_certification(case_info, court_config, language)
            start_page = self.current_page + 1
            pages.extend(cert_pages)
            self.current_page += len(cert_pages)
            sections[DocumentSection.CERTIFICATION] = (start_page, self.current_page)
            page_breakdown[DocumentSection.CERTIFICATION] = len(cert_pages)

            # Update page numbers
            for i, page in enumerate(pages):
                page.page_number = i + 1
                if page_config.require_bates_stamps and not page.bates_number:
                    page.bates_number = f"{case_id[:8].upper()}-{i+1:04d}"

            # Generate table of contents
            toc_entries = self._generate_toc_entries(sections, court_config, language)

            # Check total page limit
            if self.current_page > page_config.max_total_pages:
                warnings.append(
                    f"Total pages exceed limit: {self.current_page} > {page_config.max_total_pages}"
                )

            # Calculate document hash
            content_for_hash = "".join(p.content for p in pages)
            doc_hash = hashlib.sha256(content_for_hash.encode()).hexdigest()

            # Create document
            document = CourtDocument(
                document_id=f"doc_{case_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                case_id=case_id,
                title=case_info.get("title", "Court Filing"),
                court_name=case_info.get("court_name", court_config["name"].get(language, court_config["name"]["en"])),
                case_number=case_info.get("case_number", ""),
                filing_date=datetime.utcnow(),
                pages=pages,
                sections=sections,
                total_pages=self.current_page,
                total_exhibits=len(items_included),
                table_of_contents=toc_entries,
                document_hash=doc_hash,
                created_at=datetime.utcnow(),
                metadata={
                    "court_format": court_format,
                    "language": language,
                    "page_config": {
                        "page_size": page_config.page_size.value,
                        "font_size": page_config.font_size,
                        "line_spacing": page_config.line_spacing
                    }
                }
            )

            end_time = datetime.utcnow()

            return CompilationResult(
                success=True,
                document=document,
                warnings=warnings,
                errors=errors,
                page_breakdown=page_breakdown,
                items_included=items_included,
                items_excluded=items_excluded,
                exclusion_reasons=exclusion_reasons,
                processing_time_seconds=(end_time - start_time).total_seconds()
            )

        except Exception as e:
            errors.append(f"Compilation error: {str(e)}")
            end_time = datetime.utcnow()

            return CompilationResult(
                success=False,
                document=None,
                warnings=warnings,
                errors=errors,
                page_breakdown=page_breakdown,
                items_included=items_included,
                items_excluded=items_excluded,
                exclusion_reasons=exclusion_reasons,
                processing_time_seconds=(end_time - start_time).total_seconds()
            )

    def _generate_cover_page(
        self,
        case_info: Dict[str, Any],
        court_config: Dict[str, Any],
        language: str
    ) -> List[DocumentPage]:
        """Generate cover page."""
        templates = {
            "en": {
                "court": "In the {court_name}",
                "case_number": "Case No. {case_number}",
                "matter": "In the Matter of:",
                "petitioner": "Petitioner: {petitioner}",
                "respondent": "Respondent: {respondent}",
                "filing": "Court Filing",
                "date": "Date: {date}",
                "attorney": "Submitted by: {attorney}"
            },
            "de": {
                "court": "Vor dem {court_name}",
                "case_number": "Aktenzeichen: {case_number}",
                "matter": "In der Sache:",
                "petitioner": "Antragsteller/in: {petitioner}",
                "respondent": "Antragsgegner/in: {respondent}",
                "filing": "Gerichtsakte",
                "date": "Datum: {date}",
                "attorney": "Eingereicht von: {attorney}"
            },
            "tr": {
                "court": "{court_name}",
                "case_number": "Dosya No: {case_number}",
                "matter": "Dava Konusu:",
                "petitioner": "Davacı: {petitioner}",
                "respondent": "Davalı: {respondent}",
                "filing": "Mahkeme Dosyası",
                "date": "Tarih: {date}",
                "attorney": "Sunan: {attorney}"
            }
        }

        t = templates.get(language, templates["en"])
        date_format = court_config.get("date_format", "%Y-%m-%d")

        content = "\n\n".join([
            t["court"].format(court_name=case_info.get("court_name", "Family Court")),
            t["case_number"].format(case_number=case_info.get("case_number", "TBD")),
            "",
            t["matter"],
            case_info.get("case_title", ""),
            "",
            t["petitioner"].format(petitioner=case_info.get("petitioner", "")),
            t["respondent"].format(respondent=case_info.get("respondent", "")),
            "",
            t["filing"],
            "",
            t["date"].format(date=datetime.now().strftime(date_format)),
            t["attorney"].format(attorney=case_info.get("attorney", ""))
        ])

        return [DocumentPage(
            page_number=1,
            section=DocumentSection.COVER_PAGE,
            content=content
        )]

    def _generate_toc_placeholder(self) -> List[DocumentPage]:
        """Generate placeholder for table of contents."""
        return [DocumentPage(
            page_number=0,
            section=DocumentSection.TABLE_OF_CONTENTS,
            content="[TABLE OF CONTENTS - TO BE GENERATED]"
        )]

    def _generate_executive_summary(
        self,
        case_info: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        court_config: Dict[str, Any],
        language: str
    ) -> List[DocumentPage]:
        """Generate executive summary."""
        templates = {
            "en": {
                "title": "EXECUTIVE SUMMARY",
                "intro": "This filing presents {count} pieces of evidence in support of the following claims:",
                "evidence_overview": "Evidence Overview:",
                "key_findings": "Key Findings:"
            },
            "de": {
                "title": "ZUSAMMENFASSUNG",
                "intro": "Diese Akte enthält {count} Beweismittel zur Unterstützung der folgenden Ansprüche:",
                "evidence_overview": "Beweisübersicht:",
                "key_findings": "Wichtigste Erkenntnisse:"
            },
            "tr": {
                "title": "YÖNETİCİ ÖZETİ",
                "intro": "Bu dosya, aşağıdaki iddiaları desteklemek için {count} delil sunmaktadır:",
                "evidence_overview": "Delil Özeti:",
                "key_findings": "Temel Bulgular:"
            }
        }

        t = templates.get(language, templates["en"])

        # Count evidence by category
        by_category = {}
        for item in evidence:
            cat = item.get("category", "other")
            by_category[cat] = by_category.get(cat, 0) + 1

        content_parts = [
            t["title"],
            "",
            t["intro"].format(count=len(evidence)),
            "",
            t["evidence_overview"]
        ]

        for cat, count in by_category.items():
            content_parts.append(f"  - {cat}: {count}")

        content_parts.extend(["", t["key_findings"]])

        # Add key claims from case info
        claims = case_info.get("claims", [])
        for claim in claims[:5]:
            content_parts.append(f"  - {claim}")

        content = "\n".join(content_parts)

        # Split into pages if needed (rough estimate)
        pages = []
        chars_per_page = court_config.get("chars_per_page", 2500)

        for i in range(0, len(content), chars_per_page):
            chunk = content[i:i+chars_per_page]
            pages.append(DocumentPage(
                page_number=0,
                section=DocumentSection.EXECUTIVE_SUMMARY,
                content=chunk,
                is_continuation=(i > 0)
            ))

        return pages if pages else [DocumentPage(
            page_number=0,
            section=DocumentSection.EXECUTIVE_SUMMARY,
            content=content
        )]

    def _generate_evidence_summary(
        self,
        evidence: List[Dict[str, Any]],
        court_config: Dict[str, Any],
        language: str
    ) -> List[DocumentPage]:
        """Generate evidence summary section."""
        templates = {
            "en": {
                "title": "EVIDENCE SUMMARY",
                "exhibit": "Exhibit",
                "date": "Date",
                "type": "Type",
                "description": "Description"
            },
            "de": {
                "title": "BEWEISÜBERSICHT",
                "exhibit": "Anlage",
                "date": "Datum",
                "type": "Art",
                "description": "Beschreibung"
            },
            "tr": {
                "title": "DELİL ÖZETİ",
                "exhibit": "Ek",
                "date": "Tarih",
                "type": "Tür",
                "description": "Açıklama"
            }
        }

        t = templates.get(language, templates["en"])
        exhibit_format = court_config.get("exhibit_format", "Exhibit {number}")
        date_format = court_config.get("date_format", "%Y-%m-%d")

        content_parts = [
            t["title"],
            "",
            f"{t['exhibit']} | {t['date']} | {t['type']} | {t['description']}",
            "-" * 80
        ]

        for i, item in enumerate(evidence, 1):
            exhibit_num = exhibit_format.format(number=i, letter=chr(64+i))
            date = item.get("date_created", "")
            if isinstance(date, datetime):
                date = date.strftime(date_format)
            elif isinstance(date, str) and len(date) > 10:
                date = date[:10]

            evidence_type = item.get("evidence_type", "unknown")
            description = item.get("description", item.get("title", ""))[:50]

            content_parts.append(
                f"{exhibit_num} | {date} | {evidence_type} | {description}"
            )

        content = "\n".join(content_parts)

        # Split into pages
        chars_per_page = court_config.get("chars_per_page", 2500)
        pages = []

        for i in range(0, len(content), chars_per_page):
            chunk = content[i:i+chars_per_page]
            pages.append(DocumentPage(
                page_number=0,
                section=DocumentSection.EVIDENCE_SUMMARY,
                content=chunk,
                is_continuation=(i > 0)
            ))

        return pages if pages else [DocumentPage(
            page_number=0,
            section=DocumentSection.EVIDENCE_SUMMARY,
            content=content
        )]

    def _compile_exhibits(
        self,
        evidence: List[Dict[str, Any]],
        max_pages: int,
        court_config: Dict[str, Any],
        language: str
    ) -> Tuple[List[DocumentPage], List[str], List[str], Dict[str, str]]:
        """Compile exhibits within page limits."""
        pages: List[DocumentPage] = []
        included: List[str] = []
        excluded: List[str] = []
        exclusion_reasons: Dict[str, str] = {}

        exhibit_format = court_config.get("exhibit_format", "Exhibit {number}")
        chars_per_page = court_config.get("chars_per_page", 2500)

        total_pages = 0
        exhibit_num = 0

        # Sort evidence by relevance/priority
        sorted_evidence = sorted(
            evidence,
            key=lambda x: x.get("relevance_score", 0),
            reverse=True
        )

        for item in sorted_evidence:
            item_id = item.get("item_id", "")
            estimated_pages = item.get("estimated_pages", 1)

            # Check if adding this item would exceed limit
            if total_pages + estimated_pages > max_pages:
                excluded.append(item_id)
                exclusion_reasons[item_id] = f"Page limit exceeded ({total_pages + estimated_pages} > {max_pages})"
                continue

            exhibit_num += 1
            exhibit_label = exhibit_format.format(number=exhibit_num, letter=chr(64+exhibit_num))

            # Generate exhibit cover page
            cover_content = self._generate_exhibit_cover(
                item, exhibit_label, court_config, language
            )

            pages.append(DocumentPage(
                page_number=0,
                section=DocumentSection.EXHIBITS,
                content=cover_content,
                exhibit_id=item_id,
                metadata={"exhibit_label": exhibit_label}
            ))
            total_pages += 1

            # Add exhibit content pages
            content = item.get("content", "")
            if content:
                for i in range(0, len(content), chars_per_page):
                    chunk = content[i:i+chars_per_page]
                    pages.append(DocumentPage(
                        page_number=0,
                        section=DocumentSection.EXHIBITS,
                        content=chunk,
                        exhibit_id=item_id,
                        is_continuation=(i > 0),
                        metadata={"exhibit_label": exhibit_label}
                    ))
                    total_pages += 1

                    if total_pages >= max_pages:
                        break

            included.append(item_id)

            if total_pages >= max_pages:
                # Mark remaining as excluded
                remaining = sorted_evidence[sorted_evidence.index(item)+1:]
                for remaining_item in remaining:
                    rid = remaining_item.get("item_id", "")
                    if rid not in excluded:
                        excluded.append(rid)
                        exclusion_reasons[rid] = "Page limit reached"
                break

        return pages, included, excluded, exclusion_reasons

    def _generate_exhibit_cover(
        self,
        item: Dict[str, Any],
        exhibit_label: str,
        court_config: Dict[str, Any],
        language: str
    ) -> str:
        """Generate cover page for an exhibit."""
        templates = {
            "en": {
                "exhibit": "EXHIBIT",
                "title": "Title:",
                "type": "Type:",
                "date": "Date:",
                "source": "Source:",
                "participants": "Participants:",
                "description": "Description:",
                "authentication": "Authentication:",
                "authenticated": "Authenticated",
                "not_authenticated": "Not authenticated"
            },
            "de": {
                "exhibit": "ANLAGE",
                "title": "Titel:",
                "type": "Art:",
                "date": "Datum:",
                "source": "Quelle:",
                "participants": "Beteiligte:",
                "description": "Beschreibung:",
                "authentication": "Authentifizierung:",
                "authenticated": "Authentifiziert",
                "not_authenticated": "Nicht authentifiziert"
            },
            "tr": {
                "exhibit": "EK",
                "title": "Başlık:",
                "type": "Tür:",
                "date": "Tarih:",
                "source": "Kaynak:",
                "participants": "Katılımcılar:",
                "description": "Açıklama:",
                "authentication": "Doğrulama:",
                "authenticated": "Doğrulandı",
                "not_authenticated": "Doğrulanmadı"
            }
        }

        t = templates.get(language, templates["en"])
        date_format = court_config.get("date_format", "%Y-%m-%d")

        date = item.get("date_created", "")
        if isinstance(date, datetime):
            date = date.strftime(date_format)

        is_auth = item.get("is_authenticated", False)
        auth_status = t["authenticated"] if is_auth else t["not_authenticated"]

        participants = item.get("participants", [])
        participants_str = ", ".join(participants) if participants else "N/A"

        lines = [
            f"{t['exhibit']} {exhibit_label}",
            "=" * 40,
            "",
            f"{t['title']} {item.get('title', 'Untitled')}",
            f"{t['type']} {item.get('evidence_type', 'Unknown')}",
            f"{t['date']} {date}",
            f"{t['source']} {item.get('source', 'Unknown')}",
            f"{t['participants']} {participants_str}",
            "",
            f"{t['description']}",
            item.get('description', 'No description provided.'),
            "",
            f"{t['authentication']} {auth_status}"
        ]

        return "\n".join(lines)

    def _generate_certification(
        self,
        case_info: Dict[str, Any],
        court_config: Dict[str, Any],
        language: str
    ) -> List[DocumentPage]:
        """Generate certification page."""
        templates = {
            "en": {
                "title": "CERTIFICATE OF SERVICE",
                "body": (
                    "I hereby certify that a true and correct copy of the foregoing "
                    "has been served upon all parties of record.\n\n"
                    "Total Pages: {total_pages}\n"
                    "Total Exhibits: {total_exhibits}\n\n"
                    "Date: {date}\n\n"
                    "Signature: ____________________\n"
                    "Name: {name}\n"
                    "Address: {address}"
                )
            },
            "de": {
                "title": "ZUSTELLUNGSBESCHEINIGUNG",
                "body": (
                    "Hiermit wird bescheinigt, dass eine wahrheitsgetreue Kopie "
                    "des Vorstehenden allen Parteien zugestellt wurde.\n\n"
                    "Gesamtseiten: {total_pages}\n"
                    "Gesamtanlagen: {total_exhibits}\n\n"
                    "Datum: {date}\n\n"
                    "Unterschrift: ____________________\n"
                    "Name: {name}\n"
                    "Adresse: {address}"
                )
            },
            "tr": {
                "title": "TEBLİĞ BELGESİ",
                "body": (
                    "İşbu belge, yukarıdaki belgelerin doğru ve eksiksiz bir kopyasının "
                    "tüm taraflara tebliğ edildiğini onaylar.\n\n"
                    "Toplam Sayfa: {total_pages}\n"
                    "Toplam Ek: {total_exhibits}\n\n"
                    "Tarih: {date}\n\n"
                    "İmza: ____________________\n"
                    "İsim: {name}\n"
                    "Adres: {address}"
                )
            }
        }

        t = templates.get(language, templates["en"])
        date_format = court_config.get("date_format", "%Y-%m-%d")

        content = t["title"] + "\n\n" + t["body"].format(
            total_pages=self.current_page,
            total_exhibits=self.exhibit_counter,
            date=datetime.now().strftime(date_format),
            name=case_info.get("attorney", ""),
            address=case_info.get("attorney_address", "")
        )

        return [DocumentPage(
            page_number=0,
            section=DocumentSection.CERTIFICATION,
            content=content
        )]

    def _generate_toc_entries(
        self,
        sections: Dict[DocumentSection, Tuple[int, int]],
        court_config: Dict[str, Any],
        language: str
    ) -> List[Dict[str, Any]]:
        """Generate table of contents entries."""
        section_names = {
            "en": {
                DocumentSection.COVER_PAGE: "Cover Page",
                DocumentSection.TABLE_OF_CONTENTS: "Table of Contents",
                DocumentSection.EXECUTIVE_SUMMARY: "Executive Summary",
                DocumentSection.EVIDENCE_SUMMARY: "Evidence Summary",
                DocumentSection.EXHIBITS: "Exhibits",
                DocumentSection.CERTIFICATION: "Certificate of Service"
            },
            "de": {
                DocumentSection.COVER_PAGE: "Deckblatt",
                DocumentSection.TABLE_OF_CONTENTS: "Inhaltsverzeichnis",
                DocumentSection.EXECUTIVE_SUMMARY: "Zusammenfassung",
                DocumentSection.EVIDENCE_SUMMARY: "Beweisübersicht",
                DocumentSection.EXHIBITS: "Anlagen",
                DocumentSection.CERTIFICATION: "Zustellungsbescheinigung"
            },
            "tr": {
                DocumentSection.COVER_PAGE: "Kapak Sayfası",
                DocumentSection.TABLE_OF_CONTENTS: "İçindekiler",
                DocumentSection.EXECUTIVE_SUMMARY: "Yönetici Özeti",
                DocumentSection.EVIDENCE_SUMMARY: "Delil Özeti",
                DocumentSection.EXHIBITS: "Ekler",
                DocumentSection.CERTIFICATION: "Tebliğ Belgesi"
            }
        }

        names = section_names.get(language, section_names["en"])
        entries = []

        for section, (start, end) in sections.items():
            entries.append({
                "section": section.value,
                "name": names.get(section, section.value),
                "start_page": start,
                "end_page": end
            })

        return sorted(entries, key=lambda x: x["start_page"])

    def estimate_pages(
        self,
        evidence: List[Dict[str, Any]],
        court_format: str = "german_family"
    ) -> Dict[str, Any]:
        """Estimate total pages for a set of evidence."""
        court_config = COURT_REQUIREMENTS.get(court_format, COURT_REQUIREMENTS["german_family"])

        # Fixed sections
        cover_pages = 1
        toc_pages = 1
        summary_pages = 2
        evidence_list_pages = max(1, len(evidence) // 30)
        certification_pages = 1

        main_body_estimate = cover_pages + toc_pages + summary_pages + evidence_list_pages + certification_pages

        # Exhibit pages
        exhibit_pages = sum(item.get("estimated_pages", 1) for item in evidence)

        total_estimate = main_body_estimate + exhibit_pages

        return {
            "main_body_pages": main_body_estimate,
            "exhibit_pages": exhibit_pages,
            "total_pages": total_estimate,
            "max_allowed": court_config["max_pages"],
            "within_limit": total_estimate <= court_config["max_pages"],
            "overflow_pages": max(0, total_estimate - court_config["max_pages"])
        }
