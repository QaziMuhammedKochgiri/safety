"""
Image Analysis API Router

Provides endpoints for face detection, image categorization, and safety checks.
"""

import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from pydantic import BaseModel, Field

from ..auth import get_current_admin
from ..database import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..forensics.ai import (
    ImageAnalysisEngine,
    ImageAnalysisResult,
    ImageCategory,
    SafetyLevel
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/images", tags=["image-analysis"])

# Global engine instance (lazy loaded)
_engine: Optional[ImageAnalysisEngine] = None


def get_engine() -> ImageAnalysisEngine:
    """Get or create image analysis engine"""
    global _engine
    if _engine is None:
        _engine = ImageAnalysisEngine()
    return _engine


# Pydantic models

class FaceLocationResponse(BaseModel):
    top: int
    right: int
    bottom: int
    left: int
    width: int
    height: int


class DetectedFaceResponse(BaseModel):
    id: str
    location: FaceLocationResponse
    confidence: float
    estimatedAge: Optional[str] = None
    clusterId: Optional[str] = None


class ImageAnalysisResponse(BaseModel):
    id: str
    caseId: str
    fileName: str
    fileHash: str
    width: int
    height: int
    format: str
    faces: List[DetectedFaceResponse]
    faceCount: int
    category: str
    tags: List[str]
    confidence: float
    extractedText: str
    textLanguage: str
    safetyLevel: str
    safetyFlags: List[str]
    isBlurred: bool
    phash: str
    createdAt: str
    processingTime: float


class ImageStatsResponse(BaseModel):
    totalImages: int
    totalFaces: int
    categoryBreakdown: dict
    safetyBreakdown: dict
    uniquePeople: int
    duplicateGroups: int


class FaceClusterResponse(BaseModel):
    clusterId: str
    imageCount: int
    faces: List[dict]


@router.post("/{case_id}/analyze")
async def analyze_image(
    case_id: str,
    file: UploadFile = File(...),
    detect_faces: bool = Query(True),
    extract_text: bool = Query(True),
    check_safety: bool = Query(True),
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> ImageAnalysisResponse:
    """
    Analyze a single image.

    Performs face detection, categorization, OCR, and safety checks.
    """
    try:
        # Validate case exists
        case = await db.cases.find_one({"_id": case_id})
        if not case:
            case = await db.cases.find_one({"case_id": case_id})
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # Read file
        image_data = await file.read()

        if len(image_data) == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        # Analyze image
        engine = get_engine()
        result = engine.analyze(
            image_data=image_data,
            file_name=file.filename or "image",
            case_id=case_id,
            detect_faces=detect_faces,
            extract_text=extract_text,
            check_safety=check_safety
        )

        # Store in database
        analysis_doc = {
            "_id": result.id,
            "case_id": case_id,
            "file_name": result.file_name,
            "file_hash": result.file_hash,
            "width": result.width,
            "height": result.height,
            "format": result.format,
            "faces": [
                {
                    "id": f.id,
                    "location": f.location.to_dict(),
                    "encoding": f.encoding,
                    "confidence": f.confidence,
                    "estimated_age": f.estimated_age,
                    "cluster_id": f.cluster_id
                }
                for f in result.faces
            ],
            "face_count": result.face_count,
            "category": result.category.value,
            "tags": result.tags,
            "confidence": result.confidence,
            "extracted_text": result.extracted_text,
            "text_language": result.text_language,
            "safety_level": result.safety_level.value,
            "safety_flags": result.safety_flags,
            "is_blurred": result.is_blurred,
            "phash": result.phash,
            "processing_time": result.processing_time,
            "created_at": datetime.now(),
            "created_by": current_user.get("id")
        }

        await db.image_analyses.insert_one(analysis_doc)

        # Log activity
        await db.audit_logs.insert_one({
            "action": "image_analysis",
            "case_id": case_id,
            "user_id": current_user.get("id"),
            "timestamp": datetime.now(),
            "details": {
                "file_name": result.file_name,
                "face_count": result.face_count,
                "category": result.category.value,
                "safety_level": result.safety_level.value
            }
        })

        return _result_to_response(result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{case_id}/batch-analyze")
async def batch_analyze(
    case_id: str,
    files: List[UploadFile] = File(...),
    detect_faces: bool = Query(True),
    extract_text: bool = Query(True),
    check_safety: bool = Query(True),
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Analyze multiple images."""
    try:
        # Validate case
        case = await db.cases.find_one({"_id": case_id})
        if not case:
            case = await db.cases.find_one({"case_id": case_id})
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        engine = get_engine()
        results = []
        errors = []

        for file in files:
            try:
                image_data = await file.read()
                if len(image_data) == 0:
                    errors.append({"fileName": file.filename, "error": "Empty file"})
                    continue

                result = engine.analyze(
                    image_data=image_data,
                    file_name=file.filename or "image",
                    case_id=case_id,
                    detect_faces=detect_faces,
                    extract_text=extract_text,
                    check_safety=check_safety
                )

                # Store in database
                analysis_doc = {
                    "_id": result.id,
                    "case_id": case_id,
                    "file_name": result.file_name,
                    "file_hash": result.file_hash,
                    "width": result.width,
                    "height": result.height,
                    "format": result.format,
                    "faces": [
                        {
                            "id": f.id,
                            "location": f.location.to_dict(),
                            "encoding": f.encoding,
                            "confidence": f.confidence,
                            "estimated_age": f.estimated_age,
                            "cluster_id": f.cluster_id
                        }
                        for f in result.faces
                    ],
                    "face_count": result.face_count,
                    "category": result.category.value,
                    "tags": result.tags,
                    "confidence": result.confidence,
                    "extracted_text": result.extracted_text,
                    "text_language": result.text_language,
                    "safety_level": result.safety_level.value,
                    "safety_flags": result.safety_flags,
                    "is_blurred": result.is_blurred,
                    "phash": result.phash,
                    "processing_time": result.processing_time,
                    "created_at": datetime.now(),
                    "created_by": current_user.get("id")
                }

                await db.image_analyses.insert_one(analysis_doc)
                results.append(result.to_dict())

            except Exception as e:
                errors.append({"fileName": file.filename, "error": str(e)})

        # Log activity
        await db.audit_logs.insert_one({
            "action": "batch_image_analysis",
            "case_id": case_id,
            "user_id": current_user.get("id"),
            "timestamp": datetime.now(),
            "details": {
                "total_files": len(files),
                "successful": len(results),
                "failed": len(errors)
            }
        })

        return {
            "success": True,
            "totalFiles": len(files),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch image analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{case_id}")
async def get_image_analyses(
    case_id: str,
    category: Optional[str] = None,
    safety_level: Optional[str] = None,
    has_faces: Optional[bool] = None,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> List[ImageAnalysisResponse]:
    """Get all image analyses for a case with optional filtering."""
    query = {"case_id": case_id}

    if category:
        query["category"] = category
    if safety_level:
        query["safety_level"] = safety_level
    if has_faces is not None:
        if has_faces:
            query["face_count"] = {"$gt": 0}
        else:
            query["face_count"] = 0

    analyses = await db.image_analyses.find(query).sort("created_at", -1).to_list(length=None)

    return [_doc_to_response(a) for a in analyses]


@router.get("/{case_id}/image/{image_id}")
async def get_image_analysis(
    case_id: str,
    image_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> ImageAnalysisResponse:
    """Get detailed analysis for a specific image."""
    analysis = await db.image_analyses.find_one({
        "_id": image_id,
        "case_id": case_id
    })

    if not analysis:
        raise HTTPException(status_code=404, detail="Image analysis not found")

    return _doc_to_response(analysis)


@router.get("/{case_id}/stats")
async def get_image_stats(
    case_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> ImageStatsResponse:
    """Get image analysis statistics for a case."""
    analyses = await db.image_analyses.find(
        {"case_id": case_id}
    ).to_list(length=None)

    if not analyses:
        return ImageStatsResponse(
            totalImages=0,
            totalFaces=0,
            categoryBreakdown={},
            safetyBreakdown={},
            uniquePeople=0,
            duplicateGroups=0
        )

    total_faces = sum(a.get("face_count", 0) for a in analyses)

    # Category breakdown
    category_breakdown = {}
    for a in analyses:
        cat = a.get("category", "unknown")
        category_breakdown[cat] = category_breakdown.get(cat, 0) + 1

    # Safety breakdown
    safety_breakdown = {}
    for a in analyses:
        safety = a.get("safety_level", "safe")
        safety_breakdown[safety] = safety_breakdown.get(safety, 0) + 1

    # Count unique people (cluster IDs)
    cluster_ids = set()
    for a in analyses:
        for face in a.get("faces", []):
            if face.get("cluster_id"):
                cluster_ids.add(face["cluster_id"])

    # Find duplicate groups (same phash)
    phashes = [a.get("phash") for a in analyses if a.get("phash")]
    duplicate_groups = len(phashes) - len(set(phashes))

    return ImageStatsResponse(
        totalImages=len(analyses),
        totalFaces=total_faces,
        categoryBreakdown=category_breakdown,
        safetyBreakdown=safety_breakdown,
        uniquePeople=len(cluster_ids),
        duplicateGroups=duplicate_groups
    )


@router.get("/{case_id}/faces")
async def get_face_clusters(
    case_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> List[FaceClusterResponse]:
    """Get face clusters (grouped by person) for a case."""
    analyses = await db.image_analyses.find(
        {"case_id": case_id, "face_count": {"$gt": 0}}
    ).to_list(length=None)

    # Group faces by cluster
    clusters = {}
    for a in analyses:
        for face in a.get("faces", []):
            cluster_id = face.get("cluster_id", "unknown")
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append({
                "imageId": a["_id"],
                "fileName": a["file_name"],
                "faceId": face["id"],
                "location": face["location"],
                "estimatedAge": face.get("estimated_age")
            })

    return [
        FaceClusterResponse(
            clusterId=cluster_id,
            imageCount=len(set(f["imageId"] for f in faces)),
            faces=faces
        )
        for cluster_id, faces in clusters.items()
    ]


@router.get("/{case_id}/duplicates")
async def find_duplicates(
    case_id: str,
    threshold: float = Query(0.9, ge=0.5, le=1.0),
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Find duplicate/similar images based on perceptual hash."""
    analyses = await db.image_analyses.find(
        {"case_id": case_id, "phash": {"$ne": ""}}
    ).to_list(length=None)

    if len(analyses) < 2:
        return {"duplicates": []}

    # Get phashes
    images = [(a["_id"], a["phash"]) for a in analyses]

    # Find duplicates using engine
    engine = get_engine()
    duplicate_map = engine.safety.find_duplicates(images, threshold)

    # Build response
    duplicates = []
    seen = set()
    for img_id, similar_ids in duplicate_map.items():
        group_key = tuple(sorted([img_id] + similar_ids))
        if group_key not in seen:
            seen.add(group_key)
            group_analyses = [a for a in analyses if a["_id"] in group_key]
            duplicates.append({
                "imageIds": list(group_key),
                "images": [
                    {
                        "id": a["_id"],
                        "fileName": a["file_name"],
                        "phash": a["phash"]
                    }
                    for a in group_analyses
                ]
            })

    return {"duplicates": duplicates}


@router.delete("/{case_id}/image/{image_id}")
async def delete_image_analysis(
    case_id: str,
    image_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete an image analysis."""
    result = await db.image_analyses.delete_one({
        "_id": image_id,
        "case_id": case_id
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Image analysis not found")

    # Log deletion
    await db.audit_logs.insert_one({
        "action": "image_analysis_delete",
        "case_id": case_id,
        "user_id": current_user.get("id"),
        "timestamp": datetime.now(),
        "details": {"image_id": image_id}
    })

    return {"success": True, "message": "Image analysis deleted"}


def _result_to_response(result: ImageAnalysisResult) -> ImageAnalysisResponse:
    """Convert ImageAnalysisResult to response model."""
    return ImageAnalysisResponse(
        id=result.id,
        caseId=result.case_id,
        fileName=result.file_name,
        fileHash=result.file_hash,
        width=result.width,
        height=result.height,
        format=result.format,
        faces=[
            DetectedFaceResponse(
                id=f.id,
                location=FaceLocationResponse(**f.location.to_dict()),
                confidence=f.confidence,
                estimatedAge=f.estimated_age,
                clusterId=f.cluster_id
            )
            for f in result.faces
        ],
        faceCount=result.face_count,
        category=result.category.value,
        tags=result.tags,
        confidence=result.confidence,
        extractedText=result.extracted_text,
        textLanguage=result.text_language,
        safetyLevel=result.safety_level.value,
        safetyFlags=result.safety_flags,
        isBlurred=result.is_blurred,
        phash=result.phash,
        createdAt=result.created_at.isoformat(),
        processingTime=result.processing_time
    )


def _doc_to_response(doc: dict) -> ImageAnalysisResponse:
    """Convert MongoDB document to response model."""
    return ImageAnalysisResponse(
        id=doc["_id"],
        caseId=doc["case_id"],
        fileName=doc["file_name"],
        fileHash=doc["file_hash"],
        width=doc["width"],
        height=doc["height"],
        format=doc["format"],
        faces=[
            DetectedFaceResponse(
                id=f["id"],
                location=FaceLocationResponse(**f["location"]),
                confidence=f.get("confidence", 0),
                estimatedAge=f.get("estimated_age"),
                clusterId=f.get("cluster_id")
            )
            for f in doc.get("faces", [])
        ],
        faceCount=doc["face_count"],
        category=doc["category"],
        tags=doc.get("tags", []),
        confidence=doc.get("confidence", 0),
        extractedText=doc.get("extracted_text", ""),
        textLanguage=doc.get("text_language", ""),
        safetyLevel=doc["safety_level"],
        safetyFlags=doc.get("safety_flags", []),
        isBlurred=doc.get("is_blurred", False),
        phash=doc.get("phash", ""),
        createdAt=doc["created_at"].isoformat() if doc.get("created_at") else "",
        processingTime=doc.get("processing_time", 0)
    )
