"""
Location Mapping API Router

Provides endpoints for GPS location extraction and map visualization
using Leaflet.js + OpenStreetMap.
"""

import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field

from ..auth import get_current_admin
from ..database import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..forensics.visualization import (
    LocationMapper,
    GeoLocation,
    LocationCluster,
    LocationSource,
    extract_gps_from_images
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/locations", tags=["location-map"])


# Pydantic models

class LocationResponse(BaseModel):
    id: str
    latitude: float
    longitude: float
    timestamp: Optional[str]
    source: str
    address: Optional[str]
    fileName: Optional[str]


class ClusterResponse(BaseModel):
    id: str
    centerLat: float
    centerLng: float
    visitCount: int
    firstVisit: Optional[str]
    lastVisit: Optional[str]
    type: str


class StatsResponse(BaseModel):
    totalLocations: int
    sources: dict
    dateRange: Optional[dict]
    clusters: int


@router.get("/{case_id}")
async def get_location_map(
    case_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get location map data for a case.

    Returns Leaflet.js compatible JSON for visualization.
    """
    try:
        # Get case data
        case = await db.cases.find_one({"_id": case_id})
        if not case:
            case = await db.cases.find_one({"case_id": case_id})

        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # Create location mapper
        mapper = LocationMapper(case_id)

        # Get photos with GPS from collected_data
        collected_data = await db.collected_data.find(
            {"case_id": case_id}
        ).to_list(length=None)

        for data in collected_data:
            # Process photos with EXIF
            if data.get("data_type") in ["photos", "media"]:
                photos = data.get("data", {}).get("photos", [])
                for photo in photos:
                    # Check for GPS data
                    gps = photo.get("gps") or photo.get("location")
                    if gps:
                        mapper.add_location(
                            latitude=gps.get("latitude"),
                            longitude=gps.get("longitude"),
                            timestamp=photo.get("timestamp"),
                            source=LocationSource.EXIF,
                            place_name=gps.get("place"),
                            metadata={"fileName": photo.get("filename")}
                        )

            # Process WhatsApp shared locations
            elif data.get("data_type") == "whatsapp":
                messages = data.get("data", {}).get("messages", [])
                for msg in messages:
                    if msg.get("type") == "location":
                        loc = msg.get("location", {})
                        mapper.add_location(
                            latitude=loc.get("latitude"),
                            longitude=loc.get("longitude"),
                            timestamp=msg.get("timestamp"),
                            source=LocationSource.WHATSAPP_LOCATION,
                            place_name=loc.get("name")
                        )

        # Get forensic_results with GPS data
        forensic_results = await db.forensic_results.find(
            {"case_id": case_id}
        ).to_list(length=None)

        for result in forensic_results:
            # Process location history
            location_history = result.get("location_history", [])
            for loc in location_history:
                if loc.get("latitude") and loc.get("longitude"):
                    mapper.add_location(
                        latitude=loc["latitude"],
                        longitude=loc["longitude"],
                        timestamp=loc.get("timestamp"),
                        source=LocationSource.GOOGLE_HISTORY if "google" in str(result.get("source", "")).lower()
                               else LocationSource.IOS_SIGNIFICANT,
                        address=loc.get("address")
                    )

            # Process photo GPS from analysis
            photo_analysis = result.get("photo_analysis", {})
            for photo in photo_analysis.get("photos", []):
                gps = photo.get("exif", {}).get("gps")
                if gps:
                    mapper.add_location(
                        latitude=gps.get("latitude"),
                        longitude=gps.get("longitude"),
                        timestamp=photo.get("timestamp"),
                        source=LocationSource.EXIF,
                        metadata={"fileName": photo.get("filename")}
                    )

        # Detect clusters
        mapper.detect_clusters(radius_km=0.5, min_visits=2)

        # Log access
        await db.audit_logs.insert_one({
            "action": "location_map_view",
            "case_id": case_id,
            "user_id": current_user.get("id"),
            "timestamp": datetime.now(),
            "details": {
                "locations": len(mapper.locations),
                "clusters": len(mapper.clusters)
            }
        })

        return mapper.to_leaflet_json()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building location map: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{case_id}/stats")
async def get_location_stats(
    case_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> StatsResponse:
    """Get location statistics for a case"""
    result = await get_location_map(case_id, current_user, db)
    stats = result.get("statistics", {})

    return StatsResponse(
        totalLocations=stats.get("totalLocations", 0),
        sources=stats.get("sources", {}),
        dateRange=stats.get("dateRange"),
        clusters=stats.get("clusters", 0)
    )


@router.get("/{case_id}/clusters")
async def get_location_clusters(
    case_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> List[ClusterResponse]:
    """Get frequent location clusters"""
    result = await get_location_map(case_id, current_user, db)
    clusters = result.get("clusters", [])

    return [
        ClusterResponse(
            id=c.get("id"),
            centerLat=c.get("position", [0, 0])[0],
            centerLng=c.get("position", [0, 0])[1],
            visitCount=c.get("popup", {}).get("visitCount", 0),
            firstVisit=c.get("popup", {}).get("firstVisit"),
            lastVisit=c.get("popup", {}).get("lastVisit"),
            type=c.get("popup", {}).get("type", "frequent")
        )
        for c in clusters
    ]


@router.get("/{case_id}/timeline")
async def get_location_timeline(
    case_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get location timeline for animation"""
    result = await get_location_map(case_id, current_user, db)
    return {
        "timeline": result.get("timeline", []),
        "bounds": result.get("bounds")
    }


@router.get("/{case_id}/heatmap")
async def get_location_heatmap(
    case_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get heatmap data for location density"""
    result = await get_location_map(case_id, current_user, db)
    return {
        "heatmap": result.get("heatmap", []),
        "bounds": result.get("bounds")
    }


@router.post("/{case_id}/extract-from-images")
async def extract_gps_from_uploaded_images(
    case_id: str,
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Extract GPS from uploaded images.

    Supports JPEG and TIFF formats with EXIF GPS data.
    """
    try:
        mapper = LocationMapper(case_id)
        extracted_count = 0

        for file in files:
            if not file.content_type or not file.content_type.startswith("image/"):
                continue

            image_data = await file.read()
            location = mapper.extract_exif_gps(image_data, file.filename)

            if location:
                extracted_count += 1

        # Detect clusters
        mapper.detect_clusters()

        # Log extraction
        await db.audit_logs.insert_one({
            "action": "gps_extraction",
            "case_id": case_id,
            "user_id": current_user.get("id"),
            "timestamp": datetime.now(),
            "details": {
                "uploaded_files": len(files),
                "extracted_locations": extracted_count
            }
        })

        return {
            "success": True,
            "uploadedFiles": len(files),
            "extractedLocations": extracted_count,
            "data": mapper.to_leaflet_json()
        }

    except Exception as e:
        logger.error(f"Error extracting GPS from images: {e}")
        raise HTTPException(status_code=500, detail=str(e))
