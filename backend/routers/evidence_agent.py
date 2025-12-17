"""
Evidence Collection Agent API Router
Provides endpoints for automated evidence collection scheduling and monitoring.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..ai.evidence_agent.collection_engine import EvidenceCollector
from ..ai.evidence_agent.scheduler import CollectionScheduler
from ..ai.evidence_agent.change_detector import ChangeDetector
from ..ai.evidence_agent.alert_system import AlertManager
from ..ai.evidence_agent.digest_generator import DigestGenerator
from .. import db

router = APIRouter(
    prefix="/evidence-agent",
    tags=["evidence-agent"],
    responses={404: {"description": "Not found"}},
)


# =============================================================================
# Enums
# =============================================================================

class CollectionSource(str, Enum):
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    SMS = "sms"
    EMAIL = "email"
    SOCIAL = "social"
    CLOUD = "cloud"


class ScheduleFrequency(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class AlertPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# Pydantic Models
# =============================================================================

class ScheduleCreate(BaseModel):
    """Model for creating collection schedule."""
    case_id: str
    name: str
    sources: List[str]  # List of CollectionSource values
    frequency: str = "daily"  # ScheduleFrequency
    cron_expression: Optional[str] = None  # For custom frequency
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    active: bool = True
    options: Optional[Dict[str, Any]] = {}


class ScheduleUpdate(BaseModel):
    """Model for updating schedule."""
    name: Optional[str] = None
    sources: Optional[List[str]] = None
    frequency: Optional[str] = None
    cron_expression: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    active: Optional[bool] = None
    options: Optional[Dict[str, Any]] = None


class ScheduleResponse(BaseModel):
    """Schedule response model."""
    id: str
    case_id: str
    name: str
    sources: List[str]
    frequency: str
    cron_expression: Optional[str]
    next_run: Optional[datetime]
    last_run: Optional[datetime]
    active: bool
    total_runs: int
    successful_runs: int


class ChangeEvent(BaseModel):
    """Change detection event."""
    id: str
    case_id: str
    source: str
    change_type: str  # new, modified, deleted
    content_preview: str
    detected_at: datetime
    severity: str
    acknowledged: bool


class AlertCreate(BaseModel):
    """Model for creating alert rule."""
    case_id: str
    name: str
    conditions: Dict[str, Any]  # e.g., {"keyword": "...", "source": "...", "severity": "..."}
    priority: str = "medium"
    notify_email: Optional[str] = None
    notify_sms: Optional[str] = None
    active: bool = True


class AlertResponse(BaseModel):
    """Alert response model."""
    id: str
    case_id: str
    name: str
    conditions: Dict[str, Any]
    priority: str
    active: bool
    triggered_count: int
    last_triggered: Optional[datetime]


class DigestRequest(BaseModel):
    """Request for generating digest."""
    case_id: str
    period: str = "weekly"  # daily, weekly, monthly
    include_stats: bool = True
    include_changes: bool = True
    include_alerts: bool = True


class DigestResponse(BaseModel):
    """Digest response model."""
    case_id: str
    period: str
    start_date: datetime
    end_date: datetime
    total_collections: int
    new_items: int
    changes_detected: int
    alerts_triggered: int
    summary: str
    key_findings: List[str]


# =============================================================================
# Schedule Endpoints
# =============================================================================

@router.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(schedule: ScheduleCreate):
    """
    Create a new evidence collection schedule.

    Sets up automated collection from specified sources
    at the given frequency.
    """
    try:
        schedule_manager = CollectionScheduler()

        schedule_id = f"SCH-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Calculate next run based on frequency
        next_run = schedule_manager.calculate_next_run(
            frequency=schedule.frequency,
            cron_expression=schedule.cron_expression,
            start_time=schedule.start_time
        )

        schedule_doc = {
            "id": schedule_id,
            "case_id": schedule.case_id,
            "name": schedule.name,
            "sources": schedule.sources,
            "frequency": schedule.frequency,
            "cron_expression": schedule.cron_expression,
            "start_time": schedule.start_time,
            "end_time": schedule.end_time,
            "next_run": next_run,
            "last_run": None,
            "active": schedule.active,
            "options": schedule.options,
            "total_runs": 0,
            "successful_runs": 0,
            "created_at": datetime.utcnow()
        }

        await db.db.collection_schedules.insert_one(schedule_doc)

        return ScheduleResponse(
            id=schedule_id,
            case_id=schedule.case_id,
            name=schedule.name,
            sources=schedule.sources,
            frequency=schedule.frequency,
            cron_expression=schedule.cron_expression,
            next_run=next_run,
            last_run=None,
            active=schedule.active,
            total_runs=0,
            successful_runs=0
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create schedule: {str(e)}")


@router.get("/schedules", response_model=List[ScheduleResponse])
async def list_schedules(
    case_id: Optional[str] = Query(None),
    active_only: bool = Query(False)
):
    """List all collection schedules."""
    try:
        query = {}
        if case_id:
            query["case_id"] = case_id
        if active_only:
            query["active"] = True

        schedules = await db.db.collection_schedules.find(query).to_list(length=100)

        return [
            ScheduleResponse(
                id=s.get("id"),
                case_id=s.get("case_id"),
                name=s.get("name"),
                sources=s.get("sources", []),
                frequency=s.get("frequency"),
                cron_expression=s.get("cron_expression"),
                next_run=s.get("next_run"),
                last_run=s.get("last_run"),
                active=s.get("active", False),
                total_runs=s.get("total_runs", 0),
                successful_runs=s.get("successful_runs", 0)
            )
            for s in schedules
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list schedules: {str(e)}")


@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: str):
    """Get schedule details."""
    try:
        schedule = await db.db.collection_schedules.find_one({"id": schedule_id})

        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        return ScheduleResponse(
            id=schedule.get("id"),
            case_id=schedule.get("case_id"),
            name=schedule.get("name"),
            sources=schedule.get("sources", []),
            frequency=schedule.get("frequency"),
            cron_expression=schedule.get("cron_expression"),
            next_run=schedule.get("next_run"),
            last_run=schedule.get("last_run"),
            active=schedule.get("active", False),
            total_runs=schedule.get("total_runs", 0),
            successful_runs=schedule.get("successful_runs", 0)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get schedule: {str(e)}")


@router.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(schedule_id: str, update: ScheduleUpdate):
    """Update collection schedule."""
    try:
        schedule = await db.db.collection_schedules.find_one({"id": schedule_id})

        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        update_doc = {k: v for k, v in update.dict().items() if v is not None}
        update_doc["updated_at"] = datetime.utcnow()

        # Recalculate next run if frequency changed
        if "frequency" in update_doc or "cron_expression" in update_doc:
            schedule_manager = CollectionScheduler()
            update_doc["next_run"] = schedule_manager.calculate_next_run(
                frequency=update_doc.get("frequency", schedule.get("frequency")),
                cron_expression=update_doc.get("cron_expression", schedule.get("cron_expression"))
            )

        await db.db.collection_schedules.update_one(
            {"id": schedule_id},
            {"$set": update_doc}
        )

        updated = await db.db.collection_schedules.find_one({"id": schedule_id})

        return ScheduleResponse(
            id=updated.get("id"),
            case_id=updated.get("case_id"),
            name=updated.get("name"),
            sources=updated.get("sources", []),
            frequency=updated.get("frequency"),
            cron_expression=updated.get("cron_expression"),
            next_run=updated.get("next_run"),
            last_run=updated.get("last_run"),
            active=updated.get("active", False),
            total_runs=updated.get("total_runs", 0),
            successful_runs=updated.get("successful_runs", 0)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update schedule: {str(e)}")


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str):
    """Delete collection schedule."""
    try:
        result = await db.db.collection_schedules.delete_one({"id": schedule_id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Schedule not found")

        return {"message": "Schedule deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete schedule: {str(e)}")


@router.post("/schedules/{schedule_id}/run")
async def run_schedule_now(schedule_id: str):
    """Manually trigger a collection schedule."""
    try:
        schedule = await db.db.collection_schedules.find_one({"id": schedule_id})

        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        collection_engine = EvidenceCollector()

        # Run collection
        result = await collection_engine.collect(
            case_id=schedule.get("case_id"),
            sources=schedule.get("sources", []),
            options=schedule.get("options", {})
        )

        # Update schedule stats
        await db.db.collection_schedules.update_one(
            {"id": schedule_id},
            {
                "$set": {"last_run": datetime.utcnow()},
                "$inc": {
                    "total_runs": 1,
                    "successful_runs": 1 if result.success else 0
                }
            }
        )

        return {
            "schedule_id": schedule_id,
            "success": result.success,
            "items_collected": result.items_count,
            "duration_seconds": result.duration,
            "errors": result.errors
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run schedule: {str(e)}")


# =============================================================================
# Change Detection Endpoints
# =============================================================================

@router.get("/changes", response_model=List[ChangeEvent])
async def get_changes(
    case_id: str,
    source: Optional[str] = Query(None),
    change_type: Optional[str] = Query(None, description="new, modified, deleted"),
    since: Optional[datetime] = Query(None),
    unacknowledged_only: bool = Query(False)
):
    """
    Get detected changes for a case.

    Returns list of content changes detected since last collection.
    """
    try:
        query = {"case_id": case_id}

        if source:
            query["source"] = source
        if change_type:
            query["change_type"] = change_type
        if since:
            query["detected_at"] = {"$gte": since}
        if unacknowledged_only:
            query["acknowledged"] = False

        changes = await db.db.evidence_changes.find(query).sort("detected_at", -1).to_list(length=100)

        return [
            ChangeEvent(
                id=c.get("id"),
                case_id=c.get("case_id"),
                source=c.get("source"),
                change_type=c.get("change_type"),
                content_preview=c.get("content_preview", "")[:200],
                detected_at=c.get("detected_at"),
                severity=c.get("severity", "medium"),
                acknowledged=c.get("acknowledged", False)
            )
            for c in changes
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get changes: {str(e)}")


@router.post("/changes/{change_id}/acknowledge")
async def acknowledge_change(change_id: str):
    """Acknowledge a detected change."""
    try:
        result = await db.db.evidence_changes.update_one(
            {"id": change_id},
            {"$set": {"acknowledged": True, "acknowledged_at": datetime.utcnow()}}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Change not found")

        return {"message": "Change acknowledged"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge change: {str(e)}")


# =============================================================================
# Alert Endpoints
# =============================================================================

@router.post("/alerts", response_model=AlertResponse)
async def create_alert(alert: AlertCreate):
    """
    Create an alert rule.

    Sets up monitoring for specific conditions and triggers
    notifications when met.
    """
    try:
        alert_id = f"ALT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        alert_doc = {
            "id": alert_id,
            "case_id": alert.case_id,
            "name": alert.name,
            "conditions": alert.conditions,
            "priority": alert.priority,
            "notify_email": alert.notify_email,
            "notify_sms": alert.notify_sms,
            "active": alert.active,
            "triggered_count": 0,
            "last_triggered": None,
            "created_at": datetime.utcnow()
        }

        await db.db.alert_rules.insert_one(alert_doc)

        return AlertResponse(
            id=alert_id,
            case_id=alert.case_id,
            name=alert.name,
            conditions=alert.conditions,
            priority=alert.priority,
            active=alert.active,
            triggered_count=0,
            last_triggered=None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create alert: {str(e)}")


@router.get("/alerts", response_model=List[AlertResponse])
async def list_alerts(
    case_id: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    active_only: bool = Query(False)
):
    """List alert rules."""
    try:
        query = {}
        if case_id:
            query["case_id"] = case_id
        if priority:
            query["priority"] = priority
        if active_only:
            query["active"] = True

        alerts = await db.db.alert_rules.find(query).to_list(length=100)

        return [
            AlertResponse(
                id=a.get("id"),
                case_id=a.get("case_id"),
                name=a.get("name"),
                conditions=a.get("conditions", {}),
                priority=a.get("priority"),
                active=a.get("active", False),
                triggered_count=a.get("triggered_count", 0),
                last_triggered=a.get("last_triggered")
            )
            for a in alerts
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list alerts: {str(e)}")


@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str):
    """Delete alert rule."""
    try:
        result = await db.db.alert_rules.delete_one({"id": alert_id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Alert not found")

        return {"message": "Alert deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete alert: {str(e)}")


@router.get("/alerts/triggered")
async def get_triggered_alerts(
    case_id: Optional[str] = Query(None),
    since: Optional[datetime] = Query(None)
):
    """Get triggered alert instances."""
    try:
        query = {}
        if case_id:
            query["case_id"] = case_id
        if since:
            query["triggered_at"] = {"$gte": since}

        triggered = await db.db.triggered_alerts.find(query).sort("triggered_at", -1).to_list(length=100)

        return {
            "total": len(triggered),
            "alerts": [
                {
                    "id": t.get("id"),
                    "alert_id": t.get("alert_id"),
                    "alert_name": t.get("alert_name"),
                    "case_id": t.get("case_id"),
                    "triggered_at": t.get("triggered_at"),
                    "priority": t.get("priority"),
                    "details": t.get("details")
                }
                for t in triggered
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get triggered alerts: {str(e)}")


# =============================================================================
# Digest Endpoints
# =============================================================================

@router.post("/digest", response_model=DigestResponse)
async def generate_digest(request: DigestRequest):
    """
    Generate evidence collection digest.

    Creates a summary report of collection activities
    for the specified period.
    """
    try:
        digest_generator = DigestGenerator()

        # Calculate date range
        end_date = datetime.utcnow()
        if request.period == "daily":
            start_date = end_date - timedelta(days=1)
        elif request.period == "weekly":
            start_date = end_date - timedelta(weeks=1)
        else:  # monthly
            start_date = end_date - timedelta(days=30)

        # Get collections
        collections = await db.db.forensic_analyses.find({
            "case_id": request.case_id,
            "created_at": {"$gte": start_date, "$lte": end_date}
        }).to_list(length=1000)

        # Get changes
        changes = await db.db.evidence_changes.find({
            "case_id": request.case_id,
            "detected_at": {"$gte": start_date, "$lte": end_date}
        }).to_list(length=1000)

        # Get alerts
        alerts = await db.db.triggered_alerts.find({
            "case_id": request.case_id,
            "triggered_at": {"$gte": start_date, "$lte": end_date}
        }).to_list(length=100)

        # Generate digest
        digest = digest_generator.generate(
            collections=collections,
            changes=changes,
            alerts=alerts,
            period=request.period
        )

        # Store digest
        digest_doc = {
            "case_id": request.case_id,
            "period": request.period,
            "start_date": start_date,
            "end_date": end_date,
            "total_collections": len(collections),
            "new_items": sum(c.get("items_count", 0) for c in collections),
            "changes_detected": len(changes),
            "alerts_triggered": len(alerts),
            "summary": digest.summary,
            "key_findings": digest.key_findings,
            "generated_at": datetime.utcnow()
        }
        await db.db.digests.insert_one(digest_doc)

        return DigestResponse(
            case_id=request.case_id,
            period=request.period,
            start_date=start_date,
            end_date=end_date,
            total_collections=len(collections),
            new_items=sum(c.get("items_count", 0) for c in collections),
            changes_detected=len(changes),
            alerts_triggered=len(alerts),
            summary=digest.summary,
            key_findings=digest.key_findings
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate digest: {str(e)}")


@router.get("/digest/history")
async def get_digest_history(
    case_id: str,
    limit: int = Query(10, ge=1, le=50)
):
    """Get historical digests for a case."""
    try:
        digests = await db.db.digests.find({
            "case_id": case_id
        }).sort("generated_at", -1).to_list(length=limit)

        return {
            "case_id": case_id,
            "total": len(digests),
            "digests": [
                {
                    "period": d.get("period"),
                    "start_date": d.get("start_date"),
                    "end_date": d.get("end_date"),
                    "total_collections": d.get("total_collections"),
                    "changes_detected": d.get("changes_detected"),
                    "alerts_triggered": d.get("alerts_triggered"),
                    "generated_at": d.get("generated_at")
                }
                for d in digests
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get digest history: {str(e)}")
