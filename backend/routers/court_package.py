"""
Court Package Generator API Router
Provides endpoints for generating court-ready evidence packages.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import io
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..ai.court_package.evidence_selector import EvidenceSelector, EvidenceItem
from ..ai.court_package.relevance_scorer import RelevanceScorer
from ..ai.court_package.redundancy_remover import RedundancyRemover
from ..ai.court_package.exhibit_manager import ExhibitManager
from ..ai.court_package.document_compiler import DocumentCompiler
from ..ai.court_package.court_formats import CourtFormatGenerator, CourtFormat
from .. import db

router = APIRouter(
    prefix="/court",
    tags=["court-package"],
    responses={404: {"description": "Not found"}},
)


# =============================================================================
# Pydantic Models
# =============================================================================

class EvidenceInput(BaseModel):
    """Input model for evidence item."""
    id: str
    type: str  # message, document, image, audio, video
    content: str
    source: str  # whatsapp, sms, email, etc
    timestamp: datetime
    participants: List[str] = []
    metadata: Optional[Dict[str, Any]] = {}


class PackageRequest(BaseModel):
    """Request model for court package generation."""
    case_id: str
    evidence_items: List[EvidenceInput]
    format: str = "german"  # german, turkish, eu_e001
    language: str = "de"  # de, tr, en
    max_pages: Optional[int] = None
    include_summary: bool = True
    include_timeline: bool = True
    include_chain_of_custody: bool = True


class EvidenceSelection(BaseModel):
    """Model for evidence selection result."""
    id: str
    selected: bool
    relevance_score: float
    category: str
    reason: str


class PackagePreview(BaseModel):
    """Preview of generated package."""
    case_id: str
    total_evidence: int
    selected_evidence: int
    estimated_pages: int
    sections: List[str]
    format: str


class PackageResponse(BaseModel):
    """Response model for package generation."""
    case_id: str
    package_id: str
    format: str
    total_pages: int
    exhibits_count: int
    download_url: str
    preview_url: str
    generated_at: datetime


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/generate", response_model=PackageResponse)
async def generate_package(request: PackageRequest):
    """
    Generate court-ready evidence package.

    Creates a comprehensive court package with selected evidence,
    proper formatting, Bates numbering, and chain of custody
    documentation.
    """
    try:
        # Initialize components
        evidence_selector = EvidenceSelector()
        relevance_scorer = RelevanceScorer()
        redundancy_remover = RedundancyRemover()
        exhibit_manager = ExhibitManager()
        document_compiler = DocumentCompiler()

        # Convert input to EvidenceItem objects
        evidence_items = [
            EvidenceItem(
                id=e.id,
                type=e.type,
                content=e.content,
                source=e.source,
                timestamp=e.timestamp,
                participants=e.participants,
                metadata=e.metadata
            )
            for e in request.evidence_items
        ]

        # Score and select evidence
        scored_evidence = relevance_scorer.score_all(evidence_items)

        # Remove redundant items
        unique_evidence = redundancy_remover.remove_duplicates(scored_evidence)

        # Select based on relevance
        selected_evidence = evidence_selector.select(
            unique_evidence,
            max_items=request.max_pages * 2 if request.max_pages else None
        )

        # Assign exhibit numbers
        exhibits = exhibit_manager.create_exhibits(selected_evidence)

        # Generate document
        format_enum = _get_court_format(request.format)
        document = document_compiler.compile(
            exhibits=exhibits,
            format=format_enum,
            language=request.language,
            include_summary=request.include_summary,
            include_timeline=request.include_timeline,
            include_chain_of_custody=request.include_chain_of_custody
        )

        # Generate unique package ID
        package_id = f"PKG-{request.case_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Store package info in database
        package_doc = {
            "package_id": package_id,
            "case_id": request.case_id,
            "format": request.format,
            "language": request.language,
            "total_evidence": len(request.evidence_items),
            "selected_evidence": len(selected_evidence),
            "exhibits_count": len(exhibits),
            "total_pages": document.page_count,
            "sections": document.sections,
            "document_content": document.content,
            "generated_at": datetime.utcnow()
        }
        await db.db.court_packages.insert_one(package_doc)

        return PackageResponse(
            case_id=request.case_id,
            package_id=package_id,
            format=request.format,
            total_pages=document.page_count,
            exhibits_count=len(exhibits),
            download_url=f"/api/court/download/{package_id}",
            preview_url=f"/api/court/preview/{package_id}",
            generated_at=datetime.utcnow()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Package generation failed: {str(e)}")


@router.get("/formats")
async def get_formats():
    """
    Get available court formats.

    Returns list of supported court document formats
    with their descriptions and requirements.
    """
    return {
        "formats": [
            {
                "id": "german",
                "name": "German Court Format",
                "description": "Standard format for German family courts",
                "language": "de",
                "features": ["Aktenzeichen numbering", "Anlage references", "Eidesstattliche Erklarung"]
            },
            {
                "id": "turkish",
                "name": "Turkish Court Format",
                "description": "Format for Turkish family courts",
                "language": "tr",
                "features": ["Dosya No numbering", "Ek references", "Noter tasdik"]
            },
            {
                "id": "eu_e001",
                "name": "EU E001 Standard",
                "description": "European electronic evidence standard",
                "language": "en",
                "features": ["XML structure", "Digital signatures", "Metadata preservation"]
            }
        ]
    }


@router.post("/select-evidence")
async def select_evidence(
    case_id: str,
    evidence_items: List[EvidenceInput],
    strategy: str = Query("relevance", description="Selection strategy: relevance, chronological, comprehensive")
):
    """
    AI-powered evidence selection.

    Analyzes evidence items and recommends optimal selection
    for maximum impact while avoiding redundancy.
    """
    try:
        evidence_selector = EvidenceSelector()
        relevance_scorer = RelevanceScorer()

        # Convert and score
        items = [
            EvidenceItem(
                id=e.id,
                type=e.type,
                content=e.content,
                source=e.source,
                timestamp=e.timestamp,
                participants=e.participants,
                metadata=e.metadata
            )
            for e in evidence_items
        ]

        scored = relevance_scorer.score_all(items)

        # Select based on strategy
        if strategy == "chronological":
            selected = evidence_selector.select_chronological(scored)
        elif strategy == "comprehensive":
            selected = evidence_selector.select_comprehensive(scored)
        else:
            selected = evidence_selector.select(scored)

        # Build response
        selections = []
        for item in items:
            is_selected = any(s.id == item.id for s in selected)
            score = next((s.relevance_score for s in scored if s.id == item.id), 0)
            selections.append({
                "id": item.id,
                "selected": is_selected,
                "relevance_score": score,
                "category": _categorize_evidence(item),
                "reason": _get_selection_reason(item, is_selected, score)
            })

        return {
            "case_id": case_id,
            "total_items": len(items),
            "selected_count": len(selected),
            "strategy": strategy,
            "selections": selections,
            "ai_recommendation": f"Selected {len(selected)} of {len(items)} items for maximum impact"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evidence selection failed: {str(e)}")


@router.get("/preview/{package_id}")
async def preview_package(package_id: str):
    """
    Get preview of generated package.

    Returns HTML preview of the court package without downloading.
    """
    try:
        package = await db.db.court_packages.find_one({"package_id": package_id})

        if not package:
            raise HTTPException(status_code=404, detail="Package not found")

        return {
            "package_id": package_id,
            "case_id": package.get("case_id"),
            "format": package.get("format"),
            "language": package.get("language"),
            "total_pages": package.get("total_pages"),
            "exhibits_count": package.get("exhibits_count"),
            "sections": package.get("sections"),
            "preview_html": _generate_preview_html(package),
            "generated_at": package.get("generated_at")
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")


@router.get("/download/{package_id}")
async def download_package(
    package_id: str,
    format: str = Query("pdf", description="Download format: pdf, docx, html")
):
    """
    Download generated court package.

    Returns the complete court package in the requested format.
    """
    try:
        package = await db.db.court_packages.find_one({"package_id": package_id})

        if not package:
            raise HTTPException(status_code=404, detail="Package not found")

        document_compiler = DocumentCompiler()

        if format == "pdf":
            content = document_compiler.to_pdf(package.get("document_content", ""))
            media_type = "application/pdf"
            filename = f"{package_id}.pdf"
        elif format == "docx":
            content = document_compiler.to_docx(package.get("document_content", ""))
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"{package_id}.docx"
        else:
            content = package.get("document_content", "").encode()
            media_type = "text/html"
            filename = f"{package_id}.html"

        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.post("/export/{format}")
async def export_package(
    package_id: str,
    format: str
):
    """
    Export package to specific court format.

    Converts existing package to a different court format.
    """
    try:
        package = await db.db.court_packages.find_one({"package_id": package_id})

        if not package:
            raise HTTPException(status_code=404, detail="Package not found")

        court_format_gen = CourtFormatGenerator()
        target_format = _get_court_format(format)

        exported = court_format_gen.convert(
            content=package.get("document_content", ""),
            source_format=_get_court_format(package.get("format", "german")),
            target_format=target_format
        )

        # Create new package for export
        export_id = f"{package_id}-{format}"

        await db.db.court_packages.insert_one({
            "package_id": export_id,
            "case_id": package.get("case_id"),
            "format": format,
            "document_content": exported.content,
            "exported_from": package_id,
            "generated_at": datetime.utcnow()
        })

        return {
            "original_package": package_id,
            "export_package": export_id,
            "format": format,
            "download_url": f"/api/court/download/{export_id}",
            "generated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/chain-of-custody/{case_id}")
async def get_chain_of_custody(case_id: str):
    """
    Get chain of custody for case evidence.

    Returns complete chain of custody documentation
    for all evidence in the case.
    """
    try:
        # Get all evidence records for case
        evidence_records = await db.db.forensic_analyses.find({
            "case_id": case_id
        }).to_list(length=100)

        if not evidence_records:
            raise HTTPException(status_code=404, detail="No evidence found for case")

        chain_entries = []
        for record in evidence_records:
            chain_entries.append({
                "evidence_id": record.get("_id"),
                "collected_at": record.get("created_at", record.get("analyzed_at")),
                "collected_by": record.get("collected_by", "system"),
                "source": record.get("source", "unknown"),
                "hash": record.get("content_hash", ""),
                "verified": record.get("verified", False)
            })

        return {
            "case_id": case_id,
            "total_entries": len(chain_entries),
            "entries": chain_entries,
            "certificate_url": f"/api/court/coc-certificate/{case_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chain of custody: {str(e)}")


# =============================================================================
# Helper Functions
# =============================================================================

def _get_court_format(format_str: str) -> CourtFormat:
    """Convert string to CourtFormat enum."""
    format_map = {
        "german": CourtFormat.GERMAN,
        "turkish": CourtFormat.TURKISH,
        "eu_e001": CourtFormat.EU_E001,
        "eu": CourtFormat.EU_E001
    }
    return format_map.get(format_str.lower(), CourtFormat.GERMAN)


def _categorize_evidence(item: EvidenceItem) -> str:
    """Categorize evidence item."""
    if item.type in ["message", "chat"]:
        return "communication"
    elif item.type in ["image", "photo"]:
        return "visual"
    elif item.type in ["audio", "voice"]:
        return "audio"
    elif item.type in ["document", "file"]:
        return "document"
    return "other"


def _get_selection_reason(item: EvidenceItem, selected: bool, score: float) -> str:
    """Generate reason for selection/rejection."""
    if selected:
        if score > 0.8:
            return "Highly relevant to case allegations"
        elif score > 0.5:
            return "Supports key claims"
        else:
            return "Provides context"
    else:
        if score < 0.3:
            return "Low relevance score"
        else:
            return "Similar content already included"


def _generate_preview_html(package: Dict) -> str:
    """Generate HTML preview of package."""
    content = package.get("document_content", "")
    if not content:
        return "<p>No preview available</p>"

    # Return first 5000 chars as preview
    preview = content[:5000]
    if len(content) > 5000:
        preview += "\n\n... [Preview truncated] ..."

    return f"<div class='court-package-preview'>{preview}</div>"
