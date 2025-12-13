"""
Export Formats for SafeChild Reports
E001 (EU standard) and Cellebrite XML format support.
"""

import hashlib
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import io
import logging

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Supported export formats."""
    E001 = "e001"           # EU forensic evidence format
    CELLEBRITE_XML = "cellebrite_xml"  # Cellebrite interoperability
    UFED_XML = "ufed_xml"   # UFED report format
    AXIOM_JSON = "axiom_json"  # Magnet AXIOM format


@dataclass
class E001Metadata:
    """E001 format metadata structure."""
    case_reference: str
    evidence_number: str
    examiner_name: str
    examiner_organization: str
    acquisition_date: datetime
    export_date: datetime
    tool_name: str = "SafeChild Forensics"
    tool_version: str = "1.0.0"
    jurisdiction: str = "EU"
    classification: str = "RESTRICTED"


@dataclass
class E001EvidenceItem:
    """Single evidence item in E001 format."""
    item_id: str
    item_type: str
    source_path: str
    hash_sha256: str
    hash_md5: str
    file_size: int
    created_date: Optional[datetime]
    modified_date: Optional[datetime]
    accessed_date: Optional[datetime]
    metadata: Dict[str, Any] = field(default_factory=dict)
    content_preview: Optional[str] = None
    tags: List[str] = field(default_factory=list)


class E001Exporter:
    """Export evidence in E001 EU standard format."""

    # E001 namespace
    NAMESPACE = "http://www.edrm.net/schema/2020/E001"

    def __init__(self):
        self.metadata: Optional[E001Metadata] = None
        self.evidence_items: List[E001EvidenceItem] = []

    def set_metadata(self, metadata: E001Metadata):
        """Set export metadata."""
        self.metadata = metadata

    def add_evidence_item(self, item: E001EvidenceItem):
        """Add an evidence item to export."""
        self.evidence_items.append(item)

    def export(self) -> bytes:
        """Export to E001 XML format."""
        if not self.metadata:
            raise ValueError("Metadata must be set before export")

        # Create root element with namespace
        root = ET.Element("E001Export", {
            "xmlns": self.NAMESPACE,
            "version": "1.0",
            "exportDate": datetime.utcnow().isoformat() + "Z"
        })

        # Add metadata section
        metadata_elem = ET.SubElement(root, "Metadata")
        self._add_metadata_elements(metadata_elem)

        # Add evidence items
        evidence_elem = ET.SubElement(root, "EvidenceCollection")
        evidence_elem.set("count", str(len(self.evidence_items)))

        for item in self.evidence_items:
            self._add_evidence_item(evidence_elem, item)

        # Add integrity section
        integrity_elem = ET.SubElement(root, "IntegrityInformation")
        self._add_integrity_info(integrity_elem)

        # Convert to pretty-printed XML
        xml_string = ET.tostring(root, encoding="unicode")
        pretty_xml = minidom.parseString(xml_string).toprettyxml(indent="  ")

        # Remove extra blank lines
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        final_xml = '\n'.join(lines)

        return final_xml.encode("utf-8")

    def _add_metadata_elements(self, parent: ET.Element):
        """Add metadata elements."""
        meta = self.metadata

        ET.SubElement(parent, "CaseReference").text = meta.case_reference
        ET.SubElement(parent, "EvidenceNumber").text = meta.evidence_number

        examiner = ET.SubElement(parent, "Examiner")
        ET.SubElement(examiner, "Name").text = meta.examiner_name
        ET.SubElement(examiner, "Organization").text = meta.examiner_organization

        ET.SubElement(parent, "AcquisitionDate").text = meta.acquisition_date.isoformat() + "Z"
        ET.SubElement(parent, "ExportDate").text = meta.export_date.isoformat() + "Z"

        tool = ET.SubElement(parent, "Tool")
        ET.SubElement(tool, "Name").text = meta.tool_name
        ET.SubElement(tool, "Version").text = meta.tool_version

        ET.SubElement(parent, "Jurisdiction").text = meta.jurisdiction
        ET.SubElement(parent, "Classification").text = meta.classification

    def _add_evidence_item(self, parent: ET.Element, item: E001EvidenceItem):
        """Add single evidence item."""
        item_elem = ET.SubElement(parent, "EvidenceItem", {"id": item.item_id})

        ET.SubElement(item_elem, "Type").text = item.item_type
        ET.SubElement(item_elem, "SourcePath").text = item.source_path
        ET.SubElement(item_elem, "FileSize").text = str(item.file_size)

        # Hash values
        hashes = ET.SubElement(item_elem, "HashValues")
        sha256 = ET.SubElement(hashes, "Hash", {"algorithm": "SHA-256"})
        sha256.text = item.hash_sha256
        md5 = ET.SubElement(hashes, "Hash", {"algorithm": "MD5"})
        md5.text = item.hash_md5

        # Timestamps
        timestamps = ET.SubElement(item_elem, "Timestamps")
        if item.created_date:
            ET.SubElement(timestamps, "Created").text = item.created_date.isoformat() + "Z"
        if item.modified_date:
            ET.SubElement(timestamps, "Modified").text = item.modified_date.isoformat() + "Z"
        if item.accessed_date:
            ET.SubElement(timestamps, "Accessed").text = item.accessed_date.isoformat() + "Z"

        # Metadata
        if item.metadata:
            meta_elem = ET.SubElement(item_elem, "ExtendedMetadata")
            for key, value in item.metadata.items():
                prop = ET.SubElement(meta_elem, "Property", {"name": key})
                prop.text = str(value)

        # Content preview
        if item.content_preview:
            preview = ET.SubElement(item_elem, "ContentPreview")
            preview.text = item.content_preview[:500]  # Limit preview

        # Tags
        if item.tags:
            tags_elem = ET.SubElement(item_elem, "Tags")
            for tag in item.tags:
                ET.SubElement(tags_elem, "Tag").text = tag

    def _add_integrity_info(self, parent: ET.Element):
        """Add integrity verification information."""
        # Calculate overall manifest hash
        manifest_data = json.dumps({
            "case": self.metadata.case_reference,
            "items": [{"id": i.item_id, "hash": i.hash_sha256} for i in self.evidence_items],
            "timestamp": datetime.utcnow().isoformat()
        }, sort_keys=True)

        manifest_hash = hashlib.sha256(manifest_data.encode()).hexdigest()

        ET.SubElement(parent, "ManifestHash", {"algorithm": "SHA-256"}).text = manifest_hash
        ET.SubElement(parent, "TotalItems").text = str(len(self.evidence_items))
        ET.SubElement(parent, "GeneratedAt").text = datetime.utcnow().isoformat() + "Z"


@dataclass
class CellebriteDataItem:
    """Data item structure for Cellebrite export."""
    item_id: str
    category: str      # Contacts, Messages, Calls, Media, etc.
    subcategory: str
    timestamp: Optional[datetime]
    source_application: str
    data: Dict[str, Any]
    deleted: bool = False
    carved: bool = False


class CellebriteExporter:
    """Export evidence in Cellebrite XML format for interoperability."""

    def __init__(self):
        self.case_info: Dict[str, str] = {}
        self.device_info: Dict[str, str] = {}
        self.data_items: List[CellebriteDataItem] = []
        self.extraction_info: Dict[str, Any] = {}

    def set_case_info(
        self,
        case_id: str,
        case_name: str,
        examiner: str,
        organization: str
    ):
        """Set case information."""
        self.case_info = {
            "case_id": case_id,
            "case_name": case_name,
            "examiner": examiner,
            "organization": organization,
            "created_date": datetime.utcnow().isoformat()
        }

    def set_device_info(
        self,
        device_name: str,
        device_model: str,
        serial_number: str,
        imei: Optional[str] = None,
        os_version: Optional[str] = None
    ):
        """Set device information."""
        self.device_info = {
            "device_name": device_name,
            "device_model": device_model,
            "serial_number": serial_number,
            "imei": imei or "",
            "os_version": os_version or ""
        }

    def set_extraction_info(
        self,
        extraction_type: str,
        extraction_date: datetime,
        tool_name: str = "SafeChild Forensics",
        tool_version: str = "1.0.0"
    ):
        """Set extraction information."""
        self.extraction_info = {
            "type": extraction_type,
            "date": extraction_date.isoformat(),
            "tool": tool_name,
            "version": tool_version
        }

    def add_data_item(self, item: CellebriteDataItem):
        """Add a data item to export."""
        self.data_items.append(item)

    def add_contact(
        self,
        item_id: str,
        name: str,
        phone_numbers: List[str],
        emails: List[str] = None,
        source: str = "Unknown"
    ):
        """Add a contact item."""
        self.data_items.append(CellebriteDataItem(
            item_id=item_id,
            category="Contacts",
            subcategory="Contact",
            timestamp=None,
            source_application=source,
            data={
                "name": name,
                "phone_numbers": phone_numbers,
                "emails": emails or []
            }
        ))

    def add_message(
        self,
        item_id: str,
        sender: str,
        recipient: str,
        body: str,
        timestamp: datetime,
        source: str = "SMS",
        read: bool = True
    ):
        """Add a message item."""
        self.data_items.append(CellebriteDataItem(
            item_id=item_id,
            category="Messages",
            subcategory=source,
            timestamp=timestamp,
            source_application=source,
            data={
                "sender": sender,
                "recipient": recipient,
                "body": body,
                "read": read
            }
        ))

    def add_call(
        self,
        item_id: str,
        phone_number: str,
        call_type: str,  # incoming, outgoing, missed
        duration: int,
        timestamp: datetime
    ):
        """Add a call log item."""
        self.data_items.append(CellebriteDataItem(
            item_id=item_id,
            category="Calls",
            subcategory=f"{call_type.capitalize()} Call",
            timestamp=timestamp,
            source_application="Phone",
            data={
                "phone_number": phone_number,
                "call_type": call_type,
                "duration_seconds": duration
            }
        ))

    def add_media(
        self,
        item_id: str,
        file_name: str,
        file_path: str,
        media_type: str,  # image, video, audio
        file_size: int,
        timestamp: Optional[datetime],
        hash_value: str
    ):
        """Add a media item."""
        self.data_items.append(CellebriteDataItem(
            item_id=item_id,
            category="Media",
            subcategory=media_type.capitalize(),
            timestamp=timestamp,
            source_application="Gallery",
            data={
                "file_name": file_name,
                "file_path": file_path,
                "file_size": file_size,
                "hash_sha256": hash_value
            }
        ))

    def export(self) -> bytes:
        """Export to Cellebrite-compatible XML format."""
        root = ET.Element("CellebriteExport", {
            "version": "1.0",
            "generator": "SafeChild Forensics",
            "exportDate": datetime.utcnow().isoformat() + "Z"
        })

        # Add case information
        case_elem = ET.SubElement(root, "CaseInfo")
        for key, value in self.case_info.items():
            ET.SubElement(case_elem, key.replace("_", "")).text = str(value)

        # Add device information
        device_elem = ET.SubElement(root, "DeviceInfo")
        for key, value in self.device_info.items():
            if value:
                ET.SubElement(device_elem, key.replace("_", "")).text = str(value)

        # Add extraction information
        extraction_elem = ET.SubElement(root, "ExtractionInfo")
        for key, value in self.extraction_info.items():
            ET.SubElement(extraction_elem, key.replace("_", "")).text = str(value)

        # Group items by category
        categories: Dict[str, List[CellebriteDataItem]] = {}
        for item in self.data_items:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)

        # Add data categories
        data_elem = ET.SubElement(root, "ExtractedData")
        for category, items in categories.items():
            cat_elem = ET.SubElement(data_elem, "Category", {
                "name": category,
                "count": str(len(items))
            })
            for item in items:
                self._add_data_item(cat_elem, item)

        # Add statistics
        stats_elem = ET.SubElement(root, "Statistics")
        ET.SubElement(stats_elem, "TotalItems").text = str(len(self.data_items))
        ET.SubElement(stats_elem, "Categories").text = str(len(categories))

        deleted_count = sum(1 for i in self.data_items if i.deleted)
        ET.SubElement(stats_elem, "DeletedItems").text = str(deleted_count)

        carved_count = sum(1 for i in self.data_items if i.carved)
        ET.SubElement(stats_elem, "CarvedItems").text = str(carved_count)

        # Convert to pretty-printed XML
        xml_string = ET.tostring(root, encoding="unicode")
        pretty_xml = minidom.parseString(xml_string).toprettyxml(indent="  ")

        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        final_xml = '\n'.join(lines)

        return final_xml.encode("utf-8")

    def _add_data_item(self, parent: ET.Element, item: CellebriteDataItem):
        """Add a single data item to XML."""
        item_elem = ET.SubElement(parent, "Item", {
            "id": item.item_id,
            "subcategory": item.subcategory
        })

        if item.deleted:
            item_elem.set("deleted", "true")
        if item.carved:
            item_elem.set("carved", "true")

        if item.timestamp:
            ET.SubElement(item_elem, "Timestamp").text = item.timestamp.isoformat() + "Z"

        ET.SubElement(item_elem, "Source").text = item.source_application

        # Add data fields
        data_elem = ET.SubElement(item_elem, "Data")
        for key, value in item.data.items():
            if isinstance(value, list):
                list_elem = ET.SubElement(data_elem, key)
                for v in value:
                    ET.SubElement(list_elem, "Value").text = str(v)
            elif isinstance(value, dict):
                dict_elem = ET.SubElement(data_elem, key)
                for k, v in value.items():
                    ET.SubElement(dict_elem, k).text = str(v)
            else:
                ET.SubElement(data_elem, key).text = str(value)


class ExportEngine:
    """Main export engine for various formats."""

    def __init__(self):
        self.e001_exporter = E001Exporter()
        self.cellebrite_exporter = CellebriteExporter()

    def export_to_e001(
        self,
        case_id: str,
        evidence_number: str,
        examiner_name: str,
        examiner_org: str,
        evidence_items: List[Dict[str, Any]]
    ) -> bytes:
        """Export evidence to E001 format."""

        # Set metadata
        self.e001_exporter.set_metadata(E001Metadata(
            case_reference=case_id,
            evidence_number=evidence_number,
            examiner_name=examiner_name,
            examiner_organization=examiner_org,
            acquisition_date=datetime.utcnow(),
            export_date=datetime.utcnow()
        ))

        # Add evidence items
        for item in evidence_items:
            e001_item = E001EvidenceItem(
                item_id=item.get("id", ""),
                item_type=item.get("type", "unknown"),
                source_path=item.get("path", ""),
                hash_sha256=item.get("hash_sha256", ""),
                hash_md5=item.get("hash_md5", ""),
                file_size=item.get("size", 0),
                created_date=item.get("created"),
                modified_date=item.get("modified"),
                accessed_date=item.get("accessed"),
                metadata=item.get("metadata", {}),
                content_preview=item.get("preview"),
                tags=item.get("tags", [])
            )
            self.e001_exporter.add_evidence_item(e001_item)

        return self.e001_exporter.export()

    def export_to_cellebrite(
        self,
        case_id: str,
        case_name: str,
        examiner: str,
        organization: str,
        device_info: Dict[str, str],
        data_items: List[Dict[str, Any]]
    ) -> bytes:
        """Export data to Cellebrite XML format."""

        # Set case info
        self.cellebrite_exporter.set_case_info(
            case_id=case_id,
            case_name=case_name,
            examiner=examiner,
            organization=organization
        )

        # Set device info
        self.cellebrite_exporter.set_device_info(
            device_name=device_info.get("name", "Unknown Device"),
            device_model=device_info.get("model", "Unknown"),
            serial_number=device_info.get("serial", "Unknown"),
            imei=device_info.get("imei"),
            os_version=device_info.get("os_version")
        )

        # Set extraction info
        self.cellebrite_exporter.set_extraction_info(
            extraction_type="Logical",
            extraction_date=datetime.utcnow()
        )

        # Add data items
        for item in data_items:
            cellebrite_item = CellebriteDataItem(
                item_id=item.get("id", ""),
                category=item.get("category", "Other"),
                subcategory=item.get("subcategory", "Unknown"),
                timestamp=item.get("timestamp"),
                source_application=item.get("source", "Unknown"),
                data=item.get("data", {}),
                deleted=item.get("deleted", False),
                carved=item.get("carved", False)
            )
            self.cellebrite_exporter.add_data_item(cellebrite_item)

        return self.cellebrite_exporter.export()

    def export_to_json(self, data: Dict[str, Any]) -> bytes:
        """Export to JSON format (AXIOM-compatible)."""
        export_data = {
            "export_version": "1.0",
            "export_date": datetime.utcnow().isoformat() + "Z",
            "generator": "SafeChild Forensics",
            "data": data
        }
        return json.dumps(export_data, indent=2, ensure_ascii=False, default=str).encode("utf-8")


# Convenience function
def export_to_format(
    format: str,
    case_info: Dict[str, Any],
    evidence_items: List[Dict[str, Any]],
    **kwargs
) -> bytes:
    """Export evidence to specified format."""

    engine = ExportEngine()

    if format.lower() == "e001":
        return engine.export_to_e001(
            case_id=case_info.get("case_id", ""),
            evidence_number=case_info.get("evidence_number", ""),
            examiner_name=case_info.get("examiner_name", ""),
            examiner_org=case_info.get("examiner_org", ""),
            evidence_items=evidence_items
        )

    elif format.lower() in ["cellebrite_xml", "cellebrite"]:
        return engine.export_to_cellebrite(
            case_id=case_info.get("case_id", ""),
            case_name=case_info.get("case_name", ""),
            examiner=case_info.get("examiner_name", ""),
            organization=case_info.get("examiner_org", ""),
            device_info=case_info.get("device_info", {}),
            data_items=evidence_items
        )

    elif format.lower() == "json":
        return engine.export_to_json({
            "case_info": case_info,
            "evidence_items": evidence_items
        })

    else:
        raise ValueError(f"Unsupported export format: {format}")
