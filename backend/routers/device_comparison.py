"""
Device Comparison API Router for SafeChild
Multi-device pairing, discrepancy detection, and visualization endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import logging

from ..forensics.comparison import (
    DeviceComparisonEngine,
    DevicePairing,
    TimelineSync,
    ContactMatcher,
    MessageThreadMatcher,
    DeviceInfo,
    DeviceRole,
    DeviceType,
    DiscrepancyDetector,
    ComparisonVisualizer,
    VisualizationFormat
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/comparison",
    tags=["device-comparison"]
)


# ============ Pydantic Models ============

class DeviceRoleEnum(str, Enum):
    PARENT = "parent"
    CHILD = "child"
    UNKNOWN = "unknown"


class DeviceTypeEnum(str, Enum):
    ANDROID = "android"
    IOS = "ios"
    UNKNOWN = "unknown"


class DeviceInfoModel(BaseModel):
    device_id: str
    device_name: str
    device_type: DeviceTypeEnum = DeviceTypeEnum.UNKNOWN
    device_role: DeviceRoleEnum = DeviceRoleEnum.UNKNOWN
    owner_name: str
    phone_number: Optional[str] = None
    imei: Optional[str] = None
    serial_number: Optional[str] = None
    os_version: Optional[str] = None
    extraction_date: Optional[datetime] = None


class MessageModel(BaseModel):
    id: Optional[str] = None
    sender: str
    recipient: str
    body: str
    timestamp: datetime
    source: Optional[str] = "unknown"
    is_incoming: bool = True
    has_media: bool = False


class ContactModel(BaseModel):
    id: Optional[str] = None
    name: str
    phone_numbers: List[str] = []
    email: Optional[str] = None


class CallModel(BaseModel):
    id: Optional[str] = None
    phone_number: str
    direction: str  # incoming, outgoing, missed
    timestamp: datetime
    duration: int = 0


class CompareDevicesRequest(BaseModel):
    device_a: DeviceInfoModel
    device_b: DeviceInfoModel
    messages_a: List[MessageModel] = []
    messages_b: List[MessageModel] = []
    contacts_a: List[ContactModel] = []
    contacts_b: List[ContactModel] = []
    calls_a: List[CallModel] = []
    calls_b: List[CallModel] = []


class PairDevicesRequest(BaseModel):
    device_a: DeviceInfoModel
    device_b: DeviceInfoModel
    contacts_a: List[ContactModel] = []
    contacts_b: List[ContactModel] = []
    messages_a: List[MessageModel] = []
    messages_b: List[MessageModel] = []


class DetectDiscrepanciesRequest(BaseModel):
    device_a_id: str
    device_b_id: str
    messages_a: List[MessageModel] = []
    messages_b: List[MessageModel] = []
    screenshot_paths: List[str] = []


class TimelineSyncRequest(BaseModel):
    events_a: List[Dict[str, Any]] = []
    events_b: List[Dict[str, Any]] = []
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class MatchContactsRequest(BaseModel):
    contacts_a: List[ContactModel] = []
    contacts_b: List[ContactModel] = []


class MatchThreadsRequest(BaseModel):
    messages_a: List[MessageModel] = []
    messages_b: List[MessageModel] = []


class VisualizationRequest(BaseModel):
    comparison_result: Dict[str, Any]
    device_a_name: str
    device_b_name: str
    messages_a: List[MessageModel] = []
    messages_b: List[MessageModel] = []
    format: str = "html"


# ============ Helper Functions ============

def model_to_device_info(model: DeviceInfoModel) -> DeviceInfo:
    """Convert Pydantic model to DeviceInfo dataclass."""
    return DeviceInfo(
        device_id=model.device_id,
        device_name=model.device_name,
        device_type=DeviceType(model.device_type.value),
        device_role=DeviceRole(model.device_role.value),
        owner_name=model.owner_name,
        phone_number=model.phone_number,
        imei=model.imei,
        serial_number=model.serial_number,
        os_version=model.os_version,
        extraction_date=model.extraction_date
    )


def models_to_messages(models: List[MessageModel]) -> List[Dict[str, Any]]:
    """Convert message models to dicts."""
    return [
        {
            "id": m.id,
            "sender": m.sender,
            "recipient": m.recipient,
            "body": m.body,
            "timestamp": m.timestamp,
            "source": m.source,
            "is_incoming": m.is_incoming,
            "has_media": m.has_media
        }
        for m in models
    ]


def models_to_contacts(models: List[ContactModel]) -> List[Dict[str, Any]]:
    """Convert contact models to dicts."""
    return [
        {
            "id": c.id,
            "name": c.name,
            "phone_numbers": c.phone_numbers,
            "email": c.email
        }
        for c in models
    ]


def models_to_calls(models: List[CallModel]) -> List[Dict[str, Any]]:
    """Convert call models to dicts."""
    return [
        {
            "id": c.id,
            "phone_number": c.phone_number,
            "direction": c.direction,
            "timestamp": c.timestamp,
            "duration": c.duration,
            "type": "call"
        }
        for c in models
    ]


# ============ Endpoints ============

@router.post("/compare")
async def compare_devices(request: CompareDevicesRequest):
    """
    Perform comprehensive comparison between two devices.

    This endpoint:
    - Pairs the two devices
    - Matches contacts and message threads
    - Synchronizes timelines
    - Returns complete comparison report
    """
    try:
        engine = DeviceComparisonEngine()

        # Convert models
        device_a = model_to_device_info(request.device_a)
        device_b = model_to_device_info(request.device_b)
        messages_a = models_to_messages(request.messages_a)
        messages_b = models_to_messages(request.messages_b)
        contacts_a = models_to_contacts(request.contacts_a)
        contacts_b = models_to_contacts(request.contacts_b)
        calls_a = models_to_calls(request.calls_a)
        calls_b = models_to_calls(request.calls_b)

        # Perform comparison
        result = engine.compare_devices(
            device_a=device_a,
            device_b=device_b,
            contacts_a=contacts_a,
            contacts_b=contacts_b,
            messages_a=messages_a,
            messages_b=messages_b,
            calls_a=calls_a,
            calls_b=calls_b
        )

        return {
            "success": True,
            "comparison": result
        }

    except Exception as e:
        logger.error(f"Device comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pair")
async def pair_devices(request: PairDevicesRequest):
    """
    Pair two devices based on common data patterns.

    Returns pairing confidence and common data statistics.
    """
    try:
        pairing = DevicePairing()

        # Convert models
        device_a = model_to_device_info(request.device_a)
        device_b = model_to_device_info(request.device_b)
        contacts_a = models_to_contacts(request.contacts_a)
        contacts_b = models_to_contacts(request.contacts_b)
        messages_a = models_to_messages(request.messages_a)
        messages_b = models_to_messages(request.messages_b)

        # Pair devices
        result = pairing.pair_devices(
            device_a=device_a,
            device_b=device_b,
            contacts_a=contacts_a,
            contacts_b=contacts_b,
            messages_a=messages_a,
            messages_b=messages_b
        )

        return {
            "success": True,
            "pairing": {
                "pairing_id": result.pairing_id,
                "relationship": result.relationship,
                "common_contacts": result.common_contacts,
                "common_threads": result.common_threads,
                "confidence": result.pairing_confidence,
                "overlap_period": {
                    "start": result.overlap_period[0].isoformat() if result.overlap_period[0] != datetime.min else None,
                    "end": result.overlap_period[1].isoformat() if result.overlap_period[1] != datetime.max else None
                }
            }
        }

    except Exception as e:
        logger.error(f"Device pairing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/discrepancies")
async def detect_discrepancies(request: DetectDiscrepanciesRequest):
    """
    Detect all types of discrepancies between two devices.

    Includes:
    - Deleted messages
    - Edited messages
    - Time gaps
    - Screenshot verification
    """
    try:
        detector = DiscrepancyDetector()

        messages_a = models_to_messages(request.messages_a)
        messages_b = models_to_messages(request.messages_b)

        result = detector.detect_all_discrepancies(
            messages_a=messages_a,
            messages_b=messages_b,
            device_a_id=request.device_a_id,
            device_b_id=request.device_b_id,
            screenshots=request.screenshot_paths if request.screenshot_paths else None
        )

        return {
            "success": True,
            "discrepancies": result
        }

    except Exception as e:
        logger.error(f"Discrepancy detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/timeline/sync")
async def sync_timelines(request: TimelineSyncRequest):
    """
    Synchronize timelines between two devices.

    Returns merged timeline with matched events and gaps.
    """
    try:
        sync = TimelineSync()

        result = sync.sync_timelines(
            events_a=request.events_a,
            events_b=request.events_b,
            start_time=request.start_time,
            end_time=request.end_time
        )

        return {
            "success": True,
            "timeline": {
                "timeline_id": result.timeline_id,
                "start_time": result.start_time.isoformat(),
                "end_time": result.end_time.isoformat(),
                "total_events": len(result.events),
                "sync_quality": result.sync_quality,
                "gaps": [
                    {"start": g[0].isoformat(), "end": g[1].isoformat()}
                    for g in result.gaps
                ]
            }
        }

    except Exception as e:
        logger.error(f"Timeline sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contacts/match")
async def match_contacts(request: MatchContactsRequest):
    """
    Match contacts between two devices.

    Returns matched contacts and those unique to each device.
    """
    try:
        matcher = ContactMatcher()

        contacts_a = models_to_contacts(request.contacts_a)
        contacts_b = models_to_contacts(request.contacts_b)

        matched, only_a, only_b = matcher.match_contacts(contacts_a, contacts_b)

        return {
            "success": True,
            "contacts": {
                "matched": len(matched),
                "only_on_a": len(only_a),
                "only_on_b": len(only_b),
                "matched_details": [
                    {
                        "contact_id": c.contact_id,
                        "name_a": c.name_device_a,
                        "name_b": c.name_device_b,
                        "phones": c.phone_numbers,
                        "name_mismatch": c.name_mismatch
                    } for c in matched
                ],
                "only_a_contacts": only_a[:20],  # Limit for response size
                "only_b_contacts": only_b[:20]
            }
        }

    except Exception as e:
        logger.error(f"Contact matching failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/threads/match")
async def match_threads(request: MatchThreadsRequest):
    """
    Match message threads between two devices.

    Returns thread comparison with missing message counts.
    """
    try:
        matcher = MessageThreadMatcher()

        messages_a = models_to_messages(request.messages_a)
        messages_b = models_to_messages(request.messages_b)

        matches = matcher.match_threads(messages_a, messages_b)

        return {
            "success": True,
            "threads": {
                "total": len(matches),
                "with_discrepancies": sum(1 for t in matches if t.missing_on_a > 0 or t.missing_on_b > 0),
                "details": [
                    {
                        "thread_id": t.thread_id,
                        "participants": t.participants,
                        "device_a_count": t.device_a_message_count,
                        "device_b_count": t.device_b_message_count,
                        "common": t.common_messages,
                        "missing_on_a": t.missing_on_a,
                        "missing_on_b": t.missing_on_b,
                        "confidence": t.match_confidence
                    } for t in matches
                ]
            }
        }

    except Exception as e:
        logger.error(f"Thread matching failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visualize")
async def create_visualization(request: VisualizationRequest):
    """
    Create visualization for comparison results.

    Returns timeline view, diff views, and conflict report.
    """
    try:
        visualizer = ComparisonVisualizer()

        # Determine format
        format_map = {
            "html": VisualizationFormat.HTML,
            "json": VisualizationFormat.JSON,
            "text": VisualizationFormat.TEXT
        }
        vis_format = format_map.get(request.format.lower(), VisualizationFormat.HTML)

        messages_a = models_to_messages(request.messages_a)
        messages_b = models_to_messages(request.messages_b)

        result = visualizer.create_full_visualization(
            comparison_result=request.comparison_result,
            device_a_name=request.device_a_name,
            device_b_name=request.device_b_name,
            messages_a=messages_a,
            messages_b=messages_b,
            format=vis_format
        )

        return {
            "success": True,
            "visualization": result
        }

    except Exception as e:
        logger.error(f"Visualization creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_comparison_stats():
    """
    Get general statistics about comparison capabilities.
    """
    return {
        "success": True,
        "capabilities": {
            "device_types": ["android", "ios"],
            "device_roles": ["parent", "child"],
            "supported_sources": ["sms", "whatsapp", "telegram", "signal", "calls"],
            "discrepancy_types": [
                "deleted_message",
                "edited_message",
                "time_gap",
                "missing_contact",
                "screenshot_mismatch"
            ],
            "visualization_formats": ["html", "json", "text"],
            "features": {
                "device_pairing": True,
                "timeline_sync": True,
                "contact_matching": True,
                "thread_matching": True,
                "deleted_message_detection": True,
                "edit_history_comparison": True,
                "time_gap_analysis": True,
                "screenshot_verification": True,
                "side_by_side_timeline": True,
                "diff_view": True,
                "conflict_reporting": True
            }
        },
        "version": "1.0.0"
    }


@router.get("/health")
async def health_check():
    """Health check for comparison service."""
    return {
        "status": "healthy",
        "service": "device-comparison",
        "timestamp": datetime.utcnow().isoformat()
    }
