"""
Reports Router for SafeChild
Court-ready report generation API endpoints.
"""

from fastapi import APIRouter, HTTPException, status, Query, BackgroundTasks, Depends
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import io
import logging

from ..forensics.reports import (
    ReportEngine,
    ReportType,
    ReportFormat,
    ReportLanguage,
    EvidenceItem,
    ChainOfCustody,
    LegalTemplateEngine,
    Jurisdiction,
    ExportEngine
)
from .. import db
from ..auth import get_current_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


# =============================================================================
# Pydantic Models
# =============================================================================

class ReportTypeEnum(str, Enum):
    full_analysis = "full_analysis"
    executive_summary = "executive_summary"
    evidence_index = "evidence_index"
    chain_of_custody = "chain_of_custody"
    expert_witness = "expert_witness"
    risk_assessment = "risk_assessment"
    alienation_report = "alienation_report"
    timeline = "timeline"


class ReportFormatEnum(str, Enum):
    pdf = "pdf"
    docx = "docx"
    html = "html"
    json = "json"
    e001 = "e001"
    cellebrite_xml = "cellebrite_xml"


class ReportLanguageEnum(str, Enum):
    en = "en"
    de = "de"
    tr = "tr"


class JurisdictionEnum(str, Enum):
    germany = "germany"
    turkey = "turkey"
    eu = "eu"
    international = "international"


class EvidenceItemRequest(BaseModel):
    item_id: str
    item_type: str
    source: str
    timestamp: datetime
    description: str
    hash_value: str
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    risk_indicators: List[str] = Field(default_factory=list)
    relevance_score: float = 0.0


class ChainOfCustodyRequest(BaseModel):
    evidence_id: str
    acquisition_date: datetime
    acquisition_method: str
    acquired_by: str
    device_info: Dict[str, str]
    hash_original: str
    hash_algorithm: str = "SHA-256"


class SignerInfoRequest(BaseModel):
    name: str
    title: str
    organization: str


class GenerateReportRequest(BaseModel):
    report_type: ReportTypeEnum
    format: ReportFormatEnum
    language: ReportLanguageEnum = ReportLanguageEnum.en
    case_info: Dict[str, Any]
    evidence_items: List[EvidenceItemRequest]
    chain_of_custody: Optional[ChainOfCustodyRequest] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    sign_report: bool = False
    signer_info: Optional[SignerInfoRequest] = None


class ExpertWitnessRequest(BaseModel):
    expert_name: str
    expert_title: str
    expert_qualifications: List[str]
    experience_years: int
    court_name: str
    jurisdiction: JurisdictionEnum
    scope_of_examination: str
    methodology: Optional[str] = None
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    opinions: List[str] = Field(default_factory=list)
    conclusions: str
    limitations: List[str] = Field(default_factory=list)


class GDPRChecklistRequest(BaseModel):
    data_controller: str
    data_processor: str
    legal_basis: str
    data_subjects: List[str]
    data_categories: List[str]
    retention_period: str = "Duration of legal proceedings + 7 years"


class ExportRequest(BaseModel):
    format: str  # e001, cellebrite_xml, json
    evidence_number: Optional[str] = None
    device_info: Optional[Dict[str, str]] = None


class ReportResponse(BaseModel):
    report_id: str
    report_type: str
    format: str
    language: str
    title: str
    generated_at: datetime
    content_hash: str
    page_count: int
    signed: bool
    metadata: Dict[str, Any]


# =============================================================================
# Report Generation Endpoints
# =============================================================================

@router.post("/{case_id}/generate", response_model=ReportResponse)
async def generate_report(
    case_id: str,
    request: GenerateReportRequest,
    admin: dict = Depends(get_current_admin)
):
    """Generate a forensic report for a case."""

    try:
        engine = ReportEngine()

        # Convert evidence items
        evidence_objects = []
        for item in request.evidence_items:
            evidence_objects.append(EvidenceItem(
                item_id=item.item_id,
                item_type=item.item_type,
                source=item.source,
                timestamp=item.timestamp,
                description=item.description,
                hash_value=item.hash_value,
                file_path=item.file_path,
                metadata=item.metadata,
                risk_indicators=item.risk_indicators,
                relevance_score=item.relevance_score
            ))

        # Convert chain of custody if provided
        coc = None
        if request.chain_of_custody:
            coc = ChainOfCustody(
                case_id=case_id,
                evidence_id=request.chain_of_custody.evidence_id,
                acquisition_date=request.chain_of_custody.acquisition_date,
                acquisition_method=request.chain_of_custody.acquisition_method,
                acquired_by=request.chain_of_custody.acquired_by,
                device_info=request.chain_of_custody.device_info,
                hash_original=request.chain_of_custody.hash_original,
                hash_algorithm=request.chain_of_custody.hash_algorithm
            )

        # Convert signer info
        signer = None
        if request.signer_info:
            signer = {
                "name": request.signer_info.name,
                "title": request.signer_info.title,
                "organization": request.signer_info.organization
            }

        # Generate report
        report = engine.generate_report(
            case_id=case_id,
            report_type=ReportType(request.report_type.value),
            format=ReportFormat(request.format.value),
            language=ReportLanguage(request.language.value),
            case_info=request.case_info,
            evidence_items=evidence_objects,
            chain_of_custody=coc,
            risk_assessment=request.risk_assessment,
            sign_report=request.sign_report,
            signer_info=signer
        )

        # Store report metadata in database
        report_doc = {
            "report_id": report.report_id,
            "case_id": case_id,
            "report_type": report.report_type.value,
            "format": report.format.value,
            "language": report.language.value,
            "title": report.title,
            "generated_at": report.generated_at,
            "content_hash": report.content_hash,
            "page_count": report.page_count,
            "signed": report.signature is not None,
            "signer_name": report.signature.signer_name if report.signature else None,
            "metadata": report.metadata,
            "generated_by": admin.get("username", "unknown"),
            "content_size": len(report.content)
        }

        await db.db.generated_reports.insert_one(report_doc)

        # Store content in GridFS or as separate document for large reports
        await db.db.report_content.insert_one({
            "report_id": report.report_id,
            "content": report.content,
            "created_at": datetime.utcnow()
        })

        logger.info(f"Generated report {report.report_id} for case {case_id}")

        return ReportResponse(
            report_id=report.report_id,
            report_type=report.report_type.value,
            format=report.format.value,
            language=report.language.value,
            title=report.title,
            generated_at=report.generated_at,
            content_hash=report.content_hash,
            page_count=report.page_count,
            signed=report.signature is not None,
            metadata=report.metadata
        )

    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}"
        )


@router.get("/{case_id}/reports")
async def list_reports(
    case_id: str,
    report_type: Optional[ReportTypeEnum] = None,
    format: Optional[ReportFormatEnum] = None,
    limit: int = Query(50, ge=1, le=200),
    admin: dict = Depends(get_current_admin)
):
    """List all generated reports for a case."""

    query = {"case_id": case_id}

    if report_type:
        query["report_type"] = report_type.value
    if format:
        query["format"] = format.value

    cursor = db.db.generated_reports.find(query).sort("generated_at", -1).limit(limit)
    reports = await cursor.to_list(length=limit)

    # Remove MongoDB _id
    for report in reports:
        report.pop("_id", None)

    return {
        "case_id": case_id,
        "total": len(reports),
        "reports": reports
    }


@router.get("/{case_id}/report/{report_id}/download")
async def download_report(
    case_id: str,
    report_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Download a generated report."""

    # Get report metadata
    report = await db.db.generated_reports.find_one({
        "report_id": report_id,
        "case_id": case_id
    })

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Get report content
    content_doc = await db.db.report_content.find_one({"report_id": report_id})
    if not content_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report content not found"
        )

    content = content_doc["content"]

    # Determine content type and filename
    content_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "html": "text/html",
        "json": "application/json",
        "e001": "application/xml",
        "cellebrite_xml": "application/xml"
    }

    extensions = {
        "pdf": "pdf",
        "docx": "docx",
        "html": "html",
        "json": "json",
        "e001": "xml",
        "cellebrite_xml": "xml"
    }

    format_type = report.get("format", "pdf")
    content_type = content_types.get(format_type, "application/octet-stream")
    extension = extensions.get(format_type, "bin")
    filename = f"{report_id}.{extension}"

    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.delete("/{case_id}/report/{report_id}")
async def delete_report(
    case_id: str,
    report_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Delete a generated report."""

    result = await db.db.generated_reports.delete_one({
        "report_id": report_id,
        "case_id": case_id
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Delete content
    await db.db.report_content.delete_one({"report_id": report_id})

    return {"status": "deleted", "report_id": report_id}


# =============================================================================
# Legal Template Endpoints
# =============================================================================

@router.post("/{case_id}/gdpr-checklist")
async def generate_gdpr_checklist(
    case_id: str,
    request: GDPRChecklistRequest,
    admin: dict = Depends(get_current_admin)
):
    """Generate a GDPR compliance checklist for the case."""

    engine = LegalTemplateEngine()

    checklist = engine.generate_gdpr_checklist(
        case_id=case_id,
        data_controller=request.data_controller,
        data_processor=request.data_processor,
        legal_basis=request.legal_basis,
        data_subjects=request.data_subjects,
        data_categories=request.data_categories,
        retention_period=request.retention_period
    )

    # Store checklist
    checklist_doc = {
        "case_id": case_id,
        "type": "gdpr_checklist",
        "data_controller": checklist.data_controller,
        "data_processor": checklist.data_processor,
        "legal_basis": checklist.legal_basis,
        "data_subjects": checklist.data_subjects,
        "data_categories": checklist.data_categories,
        "retention_period": checklist.retention_period,
        "security_measures": checklist.security_measures,
        "checklist_items": checklist.checklist_items,
        "compliance_score": checklist.get_compliance_score(),
        "created_at": datetime.utcnow(),
        "created_by": admin.get("username", "unknown")
    }

    await db.db.legal_checklists.insert_one(checklist_doc)

    return {
        "case_id": case_id,
        "checklist_items": checklist.checklist_items,
        "compliance_score": checklist.get_compliance_score(),
        "security_measures": checklist.security_measures
    }


@router.post("/{case_id}/expert-witness")
async def generate_expert_witness_template(
    case_id: str,
    request: ExpertWitnessRequest,
    language: ReportLanguageEnum = ReportLanguageEnum.en,
    admin: dict = Depends(get_current_admin)
):
    """Generate an expert witness statement template."""

    engine = LegalTemplateEngine()

    template = engine.generate_expert_witness_template(
        case_id=case_id,
        expert_name=request.expert_name,
        expert_title=request.expert_title,
        expert_qualifications=request.expert_qualifications,
        experience_years=request.experience_years,
        court_name=request.court_name,
        jurisdiction=Jurisdiction(request.jurisdiction.value)
    )

    # Generate sections
    introduction = template.generate_introduction(language.value)
    methodology = request.methodology or template.generate_methodology_section(language.value)
    declaration = template.generate_declaration(language.value)

    # Store template
    template_doc = {
        "case_id": case_id,
        "type": "expert_witness",
        "expert_name": request.expert_name,
        "expert_title": request.expert_title,
        "court_name": request.court_name,
        "jurisdiction": request.jurisdiction.value,
        "language": language.value,
        "introduction": introduction,
        "scope_of_examination": request.scope_of_examination,
        "methodology": methodology,
        "findings": request.findings,
        "opinions": request.opinions,
        "conclusions": request.conclusions,
        "limitations": request.limitations,
        "declaration": declaration,
        "created_at": datetime.utcnow(),
        "created_by": admin.get("username", "unknown")
    }

    await db.db.legal_templates.insert_one(template_doc)

    return {
        "case_id": case_id,
        "introduction": introduction,
        "scope_of_examination": request.scope_of_examination,
        "methodology": methodology,
        "findings": request.findings,
        "opinions": request.opinions,
        "conclusions": request.conclusions,
        "limitations": request.limitations,
        "declaration": declaration
    }


# =============================================================================
# Export Endpoints
# =============================================================================

@router.post("/{case_id}/export")
async def export_evidence(
    case_id: str,
    request: ExportRequest,
    admin: dict = Depends(get_current_admin)
):
    """Export case evidence to E001 or Cellebrite format."""

    # Get case info
    case = await db.db.forensic_analyses.find_one({"case_id": case_id})
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    # Get evidence items
    evidence_cursor = db.db.evidence_items.find({"case_id": case_id})
    evidence_items = await evidence_cursor.to_list(length=1000)

    engine = ExportEngine()

    if request.format.lower() == "e001":
        content = engine.export_to_e001(
            case_id=case_id,
            evidence_number=request.evidence_number or f"EVD-{case_id}",
            examiner_name=admin.get("username", "Unknown"),
            examiner_org="SafeChild Law Firm",
            evidence_items=[{
                "id": e.get("item_id", ""),
                "type": e.get("item_type", "unknown"),
                "path": e.get("file_path", ""),
                "hash_sha256": e.get("hash_sha256", ""),
                "hash_md5": e.get("hash_md5", ""),
                "size": e.get("file_size", 0),
                "created": e.get("created_date"),
                "modified": e.get("modified_date"),
                "metadata": e.get("metadata", {}),
                "preview": e.get("content_preview"),
                "tags": e.get("tags", [])
            } for e in evidence_items]
        )
        content_type = "application/xml"
        filename = f"{case_id}_e001_export.xml"

    elif request.format.lower() in ["cellebrite_xml", "cellebrite"]:
        content = engine.export_to_cellebrite(
            case_id=case_id,
            case_name=case.get("case_name", f"Case {case_id}"),
            examiner=admin.get("username", "Unknown"),
            organization="SafeChild Law Firm",
            device_info=request.device_info or {},
            data_items=[{
                "id": e.get("item_id", ""),
                "category": e.get("category", "Other"),
                "subcategory": e.get("item_type", "Unknown"),
                "timestamp": e.get("timestamp"),
                "source": e.get("source", "Unknown"),
                "data": e.get("content", {}),
                "deleted": e.get("is_deleted", False),
                "carved": e.get("is_carved", False)
            } for e in evidence_items]
        )
        content_type = "application/xml"
        filename = f"{case_id}_cellebrite_export.xml"

    elif request.format.lower() == "json":
        content = engine.export_to_json({
            "case_info": {
                "case_id": case_id,
                "case_name": case.get("case_name"),
                "created_at": case.get("created_at"),
                "examiner": admin.get("username")
            },
            "evidence_items": evidence_items
        })
        content_type = "application/json"
        filename = f"{case_id}_export.json"

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format: {request.format}"
        )

    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


# =============================================================================
# Statistics Endpoint
# =============================================================================

@router.get("/{case_id}/stats")
async def get_report_stats(
    case_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Get report generation statistics for a case."""

    # Count reports by type
    pipeline = [
        {"$match": {"case_id": case_id}},
        {"$group": {
            "_id": "$report_type",
            "count": {"$sum": 1},
            "total_pages": {"$sum": "$page_count"}
        }}
    ]

    type_stats = await db.db.generated_reports.aggregate(pipeline).to_list(length=100)

    # Count reports by format
    format_pipeline = [
        {"$match": {"case_id": case_id}},
        {"$group": {
            "_id": "$format",
            "count": {"$sum": 1}
        }}
    ]

    format_stats = await db.db.generated_reports.aggregate(format_pipeline).to_list(length=100)

    # Total reports
    total = await db.db.generated_reports.count_documents({"case_id": case_id})

    # Latest report
    latest = await db.db.generated_reports.find_one(
        {"case_id": case_id},
        sort=[("generated_at", -1)]
    )

    return {
        "case_id": case_id,
        "total_reports": total,
        "by_type": {s["_id"]: s["count"] for s in type_stats},
        "by_format": {s["_id"]: s["count"] for s in format_stats},
        "total_pages": sum(s.get("total_pages", 0) for s in type_stats),
        "latest_report": {
            "report_id": latest.get("report_id") if latest else None,
            "generated_at": latest.get("generated_at") if latest else None,
            "type": latest.get("report_type") if latest else None
        } if latest else None
    }
