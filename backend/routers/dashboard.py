"""
Dashboard API Router for SafeChild
KPI cards, activity feed, case management, and analytics endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from ..services.dashboard_analytics import DashboardAnalytics
from .. import db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"]
)


# ============ Pydantic Models ============

class KPIResponse(BaseModel):
    success: bool
    kpis: List[Dict[str, Any]]


class ActivityFeedResponse(BaseModel):
    success: bool
    activities: List[Dict[str, Any]]
    total: int


class KanbanResponse(BaseModel):
    success: bool
    columns: Dict[str, List[Dict[str, Any]]]


class UpdateCaseStatusRequest(BaseModel):
    case_id: str
    new_status: str
    notes: Optional[str] = None


class AssignCaseRequest(BaseModel):
    case_id: str
    assigned_to: str


class CreateNotificationRequest(BaseModel):
    user_id: str
    type: str = "info"  # info, warning, success, error
    title: str
    message: str
    link: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ============ Dependency ============

def get_analytics():
    """Get dashboard analytics service."""
    return DashboardAnalytics(db.db)


# ============ KPI Endpoints ============

@router.get("/kpis")
async def get_kpis(
    user_id: Optional[str] = Query(None),
    analytics: DashboardAnalytics = Depends(get_analytics)
):
    """Get KPI cards for dashboard."""
    try:
        kpis = await analytics.get_kpi_cards(user_id)
        return {
            "success": True,
            "kpis": [
                {
                    "title": kpi.title,
                    "value": kpi.value,
                    "change": kpi.change,
                    "change_direction": kpi.change_direction,
                    "icon": kpi.icon,
                    "color": kpi.color,
                    "subtitle": kpi.subtitle,
                    "link": kpi.link
                }
                for kpi in kpis
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get KPIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Activity Feed Endpoints ============

@router.get("/activity")
async def get_activity_feed(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: Optional[str] = Query(None),
    analytics: DashboardAnalytics = Depends(get_analytics)
):
    """Get recent activity feed."""
    try:
        activities = await analytics.get_activity_feed(limit, offset, user_id)
        return {
            "success": True,
            "activities": [
                {
                    "activity_id": a.activity_id,
                    "type": a.activity_type.value,
                    "title": a.title,
                    "description": a.description,
                    "timestamp": a.timestamp.isoformat(),
                    "user_id": a.user_id,
                    "user_name": a.user_name,
                    "case_id": a.case_id,
                    "case_name": a.case_name,
                    "metadata": a.metadata
                }
                for a in activities
            ],
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Failed to get activity feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Case Management (Kanban) Endpoints ============

@router.get("/kanban")
async def get_kanban_board(
    analytics: DashboardAnalytics = Depends(get_analytics)
):
    """Get cases organized for Kanban board."""
    try:
        kanban = await analytics.get_case_kanban()
        return {
            "success": True,
            "columns": {
                status: [
                    {
                        "case_id": item.case_id,
                        "title": item.title,
                        "client_name": item.client_name,
                        "status": item.status.value,
                        "risk_level": item.risk_level.value,
                        "assigned_to": item.assigned_to,
                        "due_date": item.due_date.isoformat() if item.due_date else None,
                        "priority": item.priority,
                        "created_at": item.created_at.isoformat(),
                        "last_activity": item.last_activity.isoformat(),
                        "tags": item.tags
                    }
                    for item in items
                ]
                for status, items in kanban.items()
            }
        }
    except Exception as e:
        logger.error(f"Failed to get Kanban board: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kanban/update-status")
async def update_case_status(request: UpdateCaseStatusRequest):
    """Update case status (move card on Kanban)."""
    try:
        result = await db.db.cases.update_one(
            {"_id": request.case_id},
            {
                "$set": {
                    "status": request.new_status,
                    "updated_at": datetime.utcnow()
                },
                "$push": {
                    "status_history": {
                        "status": request.new_status,
                        "notes": request.notes,
                        "changed_at": datetime.utcnow()
                    }
                }
            }
        )

        if result.modified_count == 0:
            # Try with ObjectId
            from bson import ObjectId
            result = await db.db.cases.update_one(
                {"_id": ObjectId(request.case_id)},
                {
                    "$set": {
                        "status": request.new_status,
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {
                        "status_history": {
                            "status": request.new_status,
                            "notes": request.notes,
                            "changed_at": datetime.utcnow()
                        }
                    }
                }
            )

        return {
            "success": True,
            "case_id": request.case_id,
            "new_status": request.new_status
        }
    except Exception as e:
        logger.error(f"Failed to update case status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kanban/assign")
async def assign_case(request: AssignCaseRequest):
    """Assign case to team member."""
    try:
        from bson import ObjectId

        result = await db.db.cases.update_one(
            {"_id": ObjectId(request.case_id)},
            {
                "$set": {
                    "assigned_to": request.assigned_to,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return {
            "success": True,
            "case_id": request.case_id,
            "assigned_to": request.assigned_to
        }
    except Exception as e:
        logger.error(f"Failed to assign case: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Due Date Alerts Endpoints ============

@router.get("/alerts/due-dates")
async def get_due_date_alerts(
    days_ahead: int = Query(7, ge=1, le=30),
    analytics: DashboardAnalytics = Depends(get_analytics)
):
    """Get upcoming and overdue due date alerts."""
    try:
        alerts = await analytics.get_due_date_alerts(days_ahead)
        return {
            "success": True,
            "alerts": [
                {
                    "alert_id": alert.alert_id,
                    "case_id": alert.case_id,
                    "case_title": alert.case_title,
                    "due_date": alert.due_date.isoformat(),
                    "days_remaining": alert.days_remaining,
                    "severity": alert.severity,
                    "assigned_to": alert.assigned_to
                }
                for alert in alerts
            ],
            "total": len(alerts)
        }
    except Exception as e:
        logger.error(f"Failed to get due date alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Team Collaboration Endpoints ============

@router.get("/team")
async def get_team_overview(
    analytics: DashboardAnalytics = Depends(get_analytics)
):
    """Get team members overview."""
    try:
        team = await analytics.get_team_overview()
        return {
            "success": True,
            "team": [
                {
                    "user_id": member.user_id,
                    "name": member.name,
                    "email": member.email,
                    "role": member.role,
                    "avatar_url": member.avatar_url,
                    "active_cases": member.active_cases,
                    "completed_cases": member.completed_cases,
                    "is_online": member.is_online,
                    "last_seen": member.last_seen.isoformat() if member.last_seen else None
                }
                for member in team
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get team overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Analytics Endpoints ============

@router.get("/analytics/risk-distribution")
async def get_risk_distribution(
    analytics: DashboardAnalytics = Depends(get_analytics)
):
    """Get risk level distribution."""
    try:
        distribution = await analytics.get_risk_distribution()
        return {
            "success": True,
            "distribution": distribution
        }
    except Exception as e:
        logger.error(f"Failed to get risk distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/case-completion")
async def get_case_completion_metrics(
    period_days: int = Query(30, ge=7, le=365),
    analytics: DashboardAnalytics = Depends(get_analytics)
):
    """Get case completion metrics over time."""
    try:
        metrics = await analytics.get_case_completion_metrics(period_days)
        return {
            "success": True,
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Failed to get case completion metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/client-satisfaction")
async def get_client_satisfaction(
    analytics: DashboardAnalytics = Depends(get_analytics)
):
    """Get client satisfaction metrics."""
    try:
        satisfaction = await analytics.get_client_satisfaction()
        return {
            "success": True,
            "satisfaction": satisfaction
        }
    except Exception as e:
        logger.error(f"Failed to get client satisfaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Quick Actions Endpoints ============

@router.get("/quick-actions")
async def get_quick_actions(
    user_id: str = Query(...),
    analytics: DashboardAnalytics = Depends(get_analytics)
):
    """Get quick action buttons for user."""
    try:
        actions = await analytics.get_quick_actions(user_id)
        return {
            "success": True,
            "actions": actions
        }
    except Exception as e:
        logger.error(f"Failed to get quick actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Notification Endpoints ============

@router.get("/notifications")
async def get_notifications(
    user_id: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
    unread_only: bool = Query(False),
    analytics: DashboardAnalytics = Depends(get_analytics)
):
    """Get user notifications."""
    try:
        notifications = await analytics.get_notifications(user_id, limit, unread_only)
        count = await analytics.get_notification_count(user_id)
        return {
            "success": True,
            "notifications": notifications,
            "unread_count": count
        }
    except Exception as e:
        logger.error(f"Failed to get notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications")
async def create_notification(request: CreateNotificationRequest):
    """Create a new notification."""
    try:
        notification = {
            "user_id": request.user_id,
            "type": request.type,
            "title": request.title,
            "message": request.message,
            "link": request.link,
            "metadata": request.metadata or {},
            "read": False,
            "created_at": datetime.utcnow()
        }

        result = await db.db.notifications.insert_one(notification)

        return {
            "success": True,
            "notification_id": str(result.inserted_id)
        }
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    """Mark notification as read."""
    try:
        from bson import ObjectId

        result = await db.db.notifications.update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": {"read": True, "read_at": datetime.utcnow()}}
        )

        return {
            "success": True,
            "notification_id": notification_id
        }
    except Exception as e:
        logger.error(f"Failed to mark notification read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/mark-all-read")
async def mark_all_notifications_read(user_id: str = Query(...)):
    """Mark all notifications as read for user."""
    try:
        result = await db.db.notifications.update_many(
            {"user_id": user_id, "read": False},
            {"$set": {"read": True, "read_at": datetime.utcnow()}}
        )

        return {
            "success": True,
            "marked_count": result.modified_count
        }
    except Exception as e:
        logger.error(f"Failed to mark all notifications read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Summary Endpoint ============

@router.get("/summary")
async def get_dashboard_summary(
    user_id: str = Query(...),
    analytics: DashboardAnalytics = Depends(get_analytics)
):
    """Get complete dashboard summary in single request."""
    try:
        # Fetch all data in parallel would be more efficient
        kpis = await analytics.get_kpi_cards(user_id)
        activities = await analytics.get_activity_feed(limit=10, user_id=user_id)
        alerts = await analytics.get_due_date_alerts(days_ahead=7)
        quick_actions = await analytics.get_quick_actions(user_id)
        notification_count = await analytics.get_notification_count(user_id)
        risk_distribution = await analytics.get_risk_distribution()

        return {
            "success": True,
            "summary": {
                "kpis": [
                    {
                        "title": kpi.title,
                        "value": kpi.value,
                        "change": kpi.change,
                        "change_direction": kpi.change_direction,
                        "icon": kpi.icon,
                        "color": kpi.color,
                        "subtitle": kpi.subtitle,
                        "link": kpi.link
                    }
                    for kpi in kpis
                ],
                "recent_activities": [
                    {
                        "activity_id": a.activity_id,
                        "type": a.activity_type.value,
                        "title": a.title,
                        "description": a.description,
                        "timestamp": a.timestamp.isoformat()
                    }
                    for a in activities
                ],
                "due_date_alerts": [
                    {
                        "alert_id": alert.alert_id,
                        "case_title": alert.case_title,
                        "days_remaining": alert.days_remaining,
                        "severity": alert.severity
                    }
                    for alert in alerts[:5]  # Top 5 most urgent
                ],
                "quick_actions": quick_actions[:5],  # Top 5 actions
                "unread_notifications": notification_count,
                "risk_distribution": risk_distribution
            }
        }
    except Exception as e:
        logger.error(f"Failed to get dashboard summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check for dashboard service."""
    return {
        "status": "healthy",
        "service": "dashboard",
        "timestamp": datetime.utcnow().isoformat()
    }
