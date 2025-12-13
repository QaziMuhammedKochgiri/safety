"""
Exhibit Manager
Numbered exhibits with chain of custody tracking.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
from datetime import datetime
import hashlib


class ExhibitFormat(str, Enum):
    """Exhibit numbering formats."""
    NUMERIC = "numeric"  # 1, 2, 3...
    ALPHA = "alpha"  # A, B, C...
    ALPHA_NUMERIC = "alpha_numeric"  # A1, A2, B1...
    GERMAN = "german"  # Anlage 1, 2...
    TURKISH = "turkish"  # Ek 1, 2...


class CustodyEventType(str, Enum):
    """Types of chain of custody events."""
    CREATED = "created"
    COLLECTED = "collected"
    RECEIVED = "received"
    STORED = "stored"
    ACCESSED = "accessed"
    COPIED = "copied"
    VERIFIED = "verified"
    TRANSFERRED = "transferred"
    AUTHENTICATED = "authenticated"
    SUBMITTED = "submitted"


@dataclass
class CustodyEvent:
    """A single event in chain of custody."""
    event_id: str
    event_type: CustodyEventType
    timestamp: datetime
    actor: str  # Who performed the action
    actor_role: str  # e.g., "Attorney", "Forensic Analyst"
    location: str
    description: str
    previous_hash: Optional[str] = None  # Hash of previous event
    event_hash: Optional[str] = None  # Hash of this event
    digital_signature: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChainOfCustody:
    """Complete chain of custody for an exhibit."""
    exhibit_id: str
    events: List[CustodyEvent]
    current_custodian: str
    current_location: str
    integrity_verified: bool = False
    last_verified: Optional[datetime] = None
    chain_hash: Optional[str] = None  # Hash of entire chain


@dataclass
class Exhibit:
    """A court exhibit with full metadata."""
    exhibit_id: str
    exhibit_number: str  # Formatted number (e.g., "Anlage 1")
    item_id: str  # Reference to original evidence item
    title: str
    description: str
    evidence_type: str
    source: str
    date_created: datetime
    date_collected: datetime
    content_hash: str
    file_path: Optional[str] = None
    file_size_bytes: int = 0
    page_count: int = 1
    chain_of_custody: Optional[ChainOfCustody] = None
    is_authenticated: bool = False
    authentication_method: Optional[str] = None
    authentication_date: Optional[datetime] = None
    certified_by: Optional[str] = None
    translation_required: bool = False
    translation_language: Optional[str] = None
    translation_certified: bool = False
    redactions_applied: bool = False
    redaction_notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExhibitIndex:
    """Index of all exhibits in a package."""
    index_id: str
    case_id: str
    exhibits: List[Exhibit]
    total_exhibits: int
    total_pages: int
    format: ExhibitFormat
    created_at: datetime
    updated_at: datetime
    version: int = 1


class ExhibitManager:
    """Manages exhibits and chain of custody."""

    def __init__(self, exhibit_format: ExhibitFormat = ExhibitFormat.NUMERIC):
        self.exhibits: Dict[str, Exhibit] = {}
        self.custody_chains: Dict[str, ChainOfCustody] = {}
        self.exhibit_counter = 0
        self.format = exhibit_format

    def create_exhibit(
        self,
        item_id: str,
        title: str,
        description: str,
        evidence_type: str,
        source: str,
        date_created: datetime,
        content: Optional[str] = None,
        file_path: Optional[str] = None,
        file_size_bytes: int = 0,
        page_count: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Exhibit:
        """Create a new exhibit from evidence item."""
        self.exhibit_counter += 1

        exhibit_number = self._format_exhibit_number(self.exhibit_counter)
        exhibit_id = f"exhibit_{item_id}_{self.exhibit_counter}"

        # Generate content hash
        content_hash = ""
        if content:
            content_hash = hashlib.sha256(content.encode()).hexdigest()
        elif file_path:
            content_hash = f"file_{hashlib.md5(file_path.encode()).hexdigest()}"

        exhibit = Exhibit(
            exhibit_id=exhibit_id,
            exhibit_number=exhibit_number,
            item_id=item_id,
            title=title,
            description=description,
            evidence_type=evidence_type,
            source=source,
            date_created=date_created,
            date_collected=datetime.utcnow(),
            content_hash=content_hash,
            file_path=file_path,
            file_size_bytes=file_size_bytes,
            page_count=page_count,
            metadata=metadata or {}
        )

        self.exhibits[exhibit_id] = exhibit

        # Initialize chain of custody
        self._initialize_custody_chain(exhibit)

        return exhibit

    def _format_exhibit_number(self, number: int) -> str:
        """Format exhibit number based on format setting."""
        if self.format == ExhibitFormat.NUMERIC:
            return str(number)
        elif self.format == ExhibitFormat.ALPHA:
            return self._number_to_alpha(number)
        elif self.format == ExhibitFormat.ALPHA_NUMERIC:
            letter = chr(65 + ((number - 1) // 10))
            digit = ((number - 1) % 10) + 1
            return f"{letter}{digit}"
        elif self.format == ExhibitFormat.GERMAN:
            return f"Anlage {number}"
        elif self.format == ExhibitFormat.TURKISH:
            return f"Ek {number}"
        else:
            return str(number)

    def _number_to_alpha(self, number: int) -> str:
        """Convert number to letter sequence (A, B, ..., Z, AA, AB, ...)."""
        result = []
        while number > 0:
            number -= 1
            result.append(chr(65 + (number % 26)))
            number //= 26
        return ''.join(reversed(result))

    def _initialize_custody_chain(self, exhibit: Exhibit):
        """Initialize chain of custody for exhibit."""
        initial_event = CustodyEvent(
            event_id=f"event_{exhibit.exhibit_id}_001",
            event_type=CustodyEventType.CREATED,
            timestamp=datetime.utcnow(),
            actor="System",
            actor_role="Evidence Management System",
            location="Digital Repository",
            description=f"Exhibit {exhibit.exhibit_number} created from item {exhibit.item_id}"
        )

        # Calculate event hash
        initial_event.event_hash = self._calculate_event_hash(initial_event)

        chain = ChainOfCustody(
            exhibit_id=exhibit.exhibit_id,
            events=[initial_event],
            current_custodian="System",
            current_location="Digital Repository"
        )

        # Calculate chain hash
        chain.chain_hash = self._calculate_chain_hash(chain)

        self.custody_chains[exhibit.exhibit_id] = chain
        exhibit.chain_of_custody = chain

    def add_custody_event(
        self,
        exhibit_id: str,
        event_type: CustodyEventType,
        actor: str,
        actor_role: str,
        location: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[CustodyEvent]:
        """Add event to chain of custody."""
        chain = self.custody_chains.get(exhibit_id)
        if not chain:
            return None

        # Get previous event hash
        previous_hash = chain.events[-1].event_hash if chain.events else None

        event_num = len(chain.events) + 1
        event = CustodyEvent(
            event_id=f"event_{exhibit_id}_{event_num:03d}",
            event_type=event_type,
            timestamp=datetime.utcnow(),
            actor=actor,
            actor_role=actor_role,
            location=location,
            description=description,
            previous_hash=previous_hash,
            metadata=metadata or {}
        )

        # Calculate event hash
        event.event_hash = self._calculate_event_hash(event)

        chain.events.append(event)
        chain.current_custodian = actor
        chain.current_location = location

        # Update chain hash
        chain.chain_hash = self._calculate_chain_hash(chain)

        return event

    def _calculate_event_hash(self, event: CustodyEvent) -> str:
        """Calculate hash for custody event."""
        data = f"{event.event_type.value}|{event.timestamp.isoformat()}|{event.actor}|{event.location}|{event.previous_hash or ''}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def _calculate_chain_hash(self, chain: ChainOfCustody) -> str:
        """Calculate hash for entire chain."""
        event_hashes = [e.event_hash for e in chain.events if e.event_hash]
        data = "|".join(event_hashes)
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_chain_integrity(self, exhibit_id: str) -> Tuple[bool, List[str]]:
        """Verify integrity of chain of custody."""
        chain = self.custody_chains.get(exhibit_id)
        if not chain:
            return False, ["Chain not found"]

        issues = []
        is_valid = True

        for i, event in enumerate(chain.events):
            # Verify event hash
            calculated_hash = self._calculate_event_hash(event)
            if event.event_hash != calculated_hash:
                is_valid = False
                issues.append(f"Event {i+1} hash mismatch")

            # Verify chain linkage
            if i > 0:
                if event.previous_hash != chain.events[i-1].event_hash:
                    is_valid = False
                    issues.append(f"Event {i+1} previous hash mismatch")

        # Verify overall chain hash
        calculated_chain_hash = self._calculate_chain_hash(chain)
        if chain.chain_hash != calculated_chain_hash:
            is_valid = False
            issues.append("Chain hash mismatch")

        chain.integrity_verified = is_valid
        chain.last_verified = datetime.utcnow()

        return is_valid, issues

    def authenticate_exhibit(
        self,
        exhibit_id: str,
        method: str,
        certifier: str,
        notes: Optional[str] = None
    ) -> bool:
        """Mark exhibit as authenticated."""
        exhibit = self.exhibits.get(exhibit_id)
        if not exhibit:
            return False

        exhibit.is_authenticated = True
        exhibit.authentication_method = method
        exhibit.authentication_date = datetime.utcnow()
        exhibit.certified_by = certifier

        # Add custody event
        self.add_custody_event(
            exhibit_id=exhibit_id,
            event_type=CustodyEventType.AUTHENTICATED,
            actor=certifier,
            actor_role="Certifier",
            location="Authentication Office",
            description=f"Exhibit authenticated via {method}",
            metadata={"method": method, "notes": notes}
        )

        return True

    def mark_translation_required(
        self,
        exhibit_id: str,
        target_language: str
    ) -> bool:
        """Mark exhibit as requiring translation."""
        exhibit = self.exhibits.get(exhibit_id)
        if not exhibit:
            return False

        exhibit.translation_required = True
        exhibit.translation_language = target_language
        return True

    def certify_translation(
        self,
        exhibit_id: str,
        translator: str,
        certification_number: Optional[str] = None
    ) -> bool:
        """Mark translation as certified."""
        exhibit = self.exhibits.get(exhibit_id)
        if not exhibit:
            return False

        exhibit.translation_certified = True
        exhibit.metadata["translator"] = translator
        exhibit.metadata["translation_certification"] = certification_number

        # Add custody event
        self.add_custody_event(
            exhibit_id=exhibit_id,
            event_type=CustodyEventType.VERIFIED,
            actor=translator,
            actor_role="Certified Translator",
            location="Translation Office",
            description=f"Translation certified",
            metadata={
                "language": exhibit.translation_language,
                "certification": certification_number
            }
        )

        return True

    def apply_redactions(
        self,
        exhibit_id: str,
        redaction_notes: str,
        redactor: str
    ) -> bool:
        """Record that redactions have been applied."""
        exhibit = self.exhibits.get(exhibit_id)
        if not exhibit:
            return False

        exhibit.redactions_applied = True
        exhibit.redaction_notes = redaction_notes

        # Add custody event
        self.add_custody_event(
            exhibit_id=exhibit_id,
            event_type=CustodyEventType.ACCESSED,
            actor=redactor,
            actor_role="Legal Professional",
            location="Legal Office",
            description=f"Redactions applied: {redaction_notes}"
        )

        return True

    def generate_exhibit_index(
        self,
        case_id: str,
        language: str = "en"
    ) -> ExhibitIndex:
        """Generate index of all exhibits."""
        exhibits_list = list(self.exhibits.values())
        exhibits_list.sort(key=lambda x: x.exhibit_number)

        total_pages = sum(e.page_count for e in exhibits_list)

        index = ExhibitIndex(
            index_id=f"index_{case_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            case_id=case_id,
            exhibits=exhibits_list,
            total_exhibits=len(exhibits_list),
            total_pages=total_pages,
            format=self.format,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        return index

    def generate_custody_report(
        self,
        exhibit_id: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """Generate chain of custody report for exhibit."""
        exhibit = self.exhibits.get(exhibit_id)
        chain = self.custody_chains.get(exhibit_id)

        if not exhibit or not chain:
            return {"error": "Exhibit or chain not found"}

        templates = {
            "en": {
                "title": "Chain of Custody Certificate",
                "exhibit": "Exhibit",
                "created": "Created",
                "collected": "Collected",
                "current_custodian": "Current Custodian",
                "current_location": "Current Location",
                "events": "Custody Events",
                "integrity": "Integrity Status",
                "verified": "Verified",
                "not_verified": "Not Verified"
            },
            "de": {
                "title": "Verwahrungskette-Zertifikat",
                "exhibit": "Anlage",
                "created": "Erstellt",
                "collected": "Gesammelt",
                "current_custodian": "Aktueller Verwahrer",
                "current_location": "Aktueller Standort",
                "events": "Verwahrungsereignisse",
                "integrity": "Integritätsstatus",
                "verified": "Verifiziert",
                "not_verified": "Nicht verifiziert"
            },
            "tr": {
                "title": "Gözetim Zinciri Sertifikası",
                "exhibit": "Ek",
                "created": "Oluşturulma",
                "collected": "Toplanma",
                "current_custodian": "Mevcut Sorumlu",
                "current_location": "Mevcut Konum",
                "events": "Gözetim Olayları",
                "integrity": "Bütünlük Durumu",
                "verified": "Doğrulandı",
                "not_verified": "Doğrulanmadı"
            }
        }

        t = templates.get(language, templates["en"])

        # Verify chain
        is_valid, issues = self.verify_chain_integrity(exhibit_id)

        report = {
            "title": t["title"],
            "exhibit_info": {
                t["exhibit"]: exhibit.exhibit_number,
                "Title": exhibit.title,
                t["created"]: exhibit.date_created.isoformat(),
                t["collected"]: exhibit.date_collected.isoformat(),
                "Content Hash": exhibit.content_hash
            },
            "custody_info": {
                t["current_custodian"]: chain.current_custodian,
                t["current_location"]: chain.current_location,
                t["integrity"]: t["verified"] if is_valid else t["not_verified"]
            },
            "events": [
                {
                    "type": event.event_type.value,
                    "timestamp": event.timestamp.isoformat(),
                    "actor": event.actor,
                    "role": event.actor_role,
                    "location": event.location,
                    "description": event.description,
                    "hash": event.event_hash
                }
                for event in chain.events
            ],
            "verification": {
                "is_valid": is_valid,
                "issues": issues,
                "chain_hash": chain.chain_hash,
                "verified_at": chain.last_verified.isoformat() if chain.last_verified else None
            },
            "generated_at": datetime.utcnow().isoformat()
        }

        return report

    def transfer_custody(
        self,
        exhibit_id: str,
        from_custodian: str,
        to_custodian: str,
        to_role: str,
        to_location: str,
        reason: str
    ) -> bool:
        """Transfer custody of exhibit."""
        chain = self.custody_chains.get(exhibit_id)
        if not chain:
            return False

        if chain.current_custodian != from_custodian:
            return False  # Only current custodian can transfer

        event = self.add_custody_event(
            exhibit_id=exhibit_id,
            event_type=CustodyEventType.TRANSFERRED,
            actor=to_custodian,
            actor_role=to_role,
            location=to_location,
            description=f"Transferred from {from_custodian}: {reason}"
        )

        return event is not None

    def get_exhibit(self, exhibit_id: str) -> Optional[Exhibit]:
        """Get exhibit by ID."""
        return self.exhibits.get(exhibit_id)

    def get_exhibit_by_number(self, exhibit_number: str) -> Optional[Exhibit]:
        """Get exhibit by formatted number."""
        for exhibit in self.exhibits.values():
            if exhibit.exhibit_number == exhibit_number:
                return exhibit
        return None

    def get_all_exhibits(self) -> List[Exhibit]:
        """Get all exhibits sorted by number."""
        exhibits = list(self.exhibits.values())
        return sorted(exhibits, key=lambda x: x.exhibit_number)

    def get_statistics(self) -> Dict[str, Any]:
        """Get exhibit statistics."""
        exhibits = list(self.exhibits.values())

        authenticated_count = sum(1 for e in exhibits if e.is_authenticated)
        translation_count = sum(1 for e in exhibits if e.translation_required)
        translation_certified = sum(1 for e in exhibits if e.translation_certified)
        redacted_count = sum(1 for e in exhibits if e.redactions_applied)

        by_type = {}
        for exhibit in exhibits:
            etype = exhibit.evidence_type
            by_type[etype] = by_type.get(etype, 0) + 1

        total_pages = sum(e.page_count for e in exhibits)
        total_size = sum(e.file_size_bytes for e in exhibits)

        return {
            "total_exhibits": len(exhibits),
            "total_pages": total_pages,
            "total_size_bytes": total_size,
            "authenticated": authenticated_count,
            "requiring_translation": translation_count,
            "translations_certified": translation_certified,
            "with_redactions": redacted_count,
            "by_evidence_type": by_type,
            "format": self.format.value
        }

    def export_index_to_text(
        self,
        case_id: str,
        language: str = "en"
    ) -> str:
        """Export exhibit index to text format."""
        index = self.generate_exhibit_index(case_id, language)

        templates = {
            "en": {
                "title": "EXHIBIT INDEX",
                "case": "Case",
                "total": "Total Exhibits",
                "pages": "Total Pages",
                "number": "No.",
                "exhibit_title": "Title",
                "type": "Type",
                "date": "Date",
                "page_count": "Pages"
            },
            "de": {
                "title": "ANLAGENVERZEICHNIS",
                "case": "Aktenzeichen",
                "total": "Gesamtanlagen",
                "pages": "Gesamtseiten",
                "number": "Nr.",
                "exhibit_title": "Titel",
                "type": "Art",
                "date": "Datum",
                "page_count": "Seiten"
            },
            "tr": {
                "title": "EK LİSTESİ",
                "case": "Dosya",
                "total": "Toplam Ek",
                "pages": "Toplam Sayfa",
                "number": "No.",
                "exhibit_title": "Başlık",
                "type": "Tür",
                "date": "Tarih",
                "page_count": "Sayfa"
            }
        }

        t = templates.get(language, templates["en"])

        lines = [
            t["title"],
            "=" * 80,
            f"{t['case']}: {case_id}",
            f"{t['total']}: {index.total_exhibits}",
            f"{t['pages']}: {index.total_pages}",
            "",
            f"{t['number']:8} | {t['exhibit_title']:30} | {t['type']:15} | {t['date']:12} | {t['page_count']}",
            "-" * 80
        ]

        for exhibit in index.exhibits:
            date_str = exhibit.date_created.strftime("%Y-%m-%d")
            title_short = exhibit.title[:28] + ".." if len(exhibit.title) > 30 else exhibit.title
            type_short = exhibit.evidence_type[:13] + ".." if len(exhibit.evidence_type) > 15 else exhibit.evidence_type

            lines.append(
                f"{exhibit.exhibit_number:8} | {title_short:30} | {type_short:15} | {date_str:12} | {exhibit.page_count}"
            )

        return "\n".join(lines)
