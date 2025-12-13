"""
Dashboard Analytics Service for SafeChild
KPI calculations, case metrics, risk distribution, and real-time activity tracking.
"""

import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class CaseStatus(Enum):
    """Case status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    URGENT = "urgent"


class RiskLevel(Enum):
    """Risk level classifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActivityType(Enum):
    """Types of activities tracked."""
    CASE_CREATED = "case_created"
    CASE_UPDATED = "case_updated"
    CASE_COMPLETED = "case_completed"
    EVIDENCE_UPLOADED = "evidence_uploaded"
    ANALYSIS_COMPLETED = "analysis_completed"
    REPORT_GENERATED = "report_generated"
    ALERT_TRIGGERED = "alert_triggered"
    CLIENT_REGISTERED = "client_registered"
    DOCUMENT_ADDED = "document_added"
    MESSAGE_RECEIVED = "message_received"


@dataclass
class KPICard:
    """KPI card data structure."""
    title: str
    value: Any
    change: float  # Percentage change from previous period
    change_direction: str  # up, down, neutral
    icon: str
    color: str  # green, red, yellow, blue
    subtitle: Optional[str] = None
    link: Optional[str] = None


@dataclass
class ActivityItem:
    """Activity feed item."""
    activity_id: str
    activity_type: ActivityType
    title: str
    description: str
    timestamp: datetime
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    case_id: Optional[str] = None
    case_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CaseKanbanItem:
    """Case item for Kanban board."""
    case_id: str
    title: str
    client_name: str
    status: CaseStatus
    risk_level: RiskLevel
    assigned_to: Optional[str]
    due_date: Optional[datetime]
    priority: int  # 1-5, 1 being highest
    created_at: datetime
    last_activity: datetime
    tags: List[str] = field(default_factory=list)


@dataclass
class DueDateAlert:
    """Due date alert."""
    alert_id: str
    case_id: str
    case_title: str
    due_date: datetime
    days_remaining: int
    severity: str  # warning, urgent, overdue
    assigned_to: Optional[str] = None


@dataclass
class TeamMember:
    """Team member for collaboration."""
    user_id: str
    name: str
    email: str
    role: str
    avatar_url: Optional[str]
    active_cases: int
    completed_cases: int
    is_online: bool = False
    last_seen: Optional[datetime] = None


class DashboardAnalytics:
    """Main analytics engine for dashboard."""

    def __init__(self, db):
        self.db = db

    async def get_kpi_cards(self, user_id: Optional[str] = None) -> List[KPICard]:
        """Get KPI cards for dashboard."""
        now = datetime.utcnow()
        last_week = now - timedelta(days=7)
        last_month = now - timedelta(days=30)

        # Query case counts
        total_cases = await self._count_cases({})
        active_cases = await self._count_cases({"status": {"$nin": ["completed", "archived"]}})
        pending_cases = await self._count_cases({"status": "pending"})
        completed_this_month = await self._count_cases({
            "status": "completed",
            "completed_at": {"$gte": last_month}
        })

        # Query alerts
        active_alerts = await self._count_alerts({"resolved": False})
        critical_alerts = await self._count_alerts({"resolved": False, "severity": "critical"})

        # Query clients
        total_clients = await self._count_clients({})
        new_clients_this_week = await self._count_clients({
            "created_at": {"$gte": last_week}
        })

        # Calculate changes
        prev_month = now - timedelta(days=60)
        completed_prev_month = await self._count_cases({
            "status": "completed",
            "completed_at": {"$gte": prev_month, "$lt": last_month}
        })
        completion_change = self._calc_change(completed_this_month, completed_prev_month)

        prev_week_clients = await self._count_clients({
            "created_at": {"$gte": now - timedelta(days=14), "$lt": last_week}
        })
        client_change = self._calc_change(new_clients_this_week, prev_week_clients)

        return [
            KPICard(
                title="Active Cases",
                value=active_cases,
                change=0,  # Would need historical data
                change_direction="neutral",
                icon="briefcase",
                color="blue",
                subtitle=f"{pending_cases} pending review",
                link="/admin/cases"
            ),
            KPICard(
                title="Critical Alerts",
                value=critical_alerts,
                change=0,
                change_direction="neutral" if critical_alerts == 0 else "up",
                icon="alert-triangle",
                color="red" if critical_alerts > 0 else "green",
                subtitle=f"{active_alerts} total alerts",
                link="/admin/alerts"
            ),
            KPICard(
                title="Cases Completed",
                value=completed_this_month,
                change=completion_change,
                change_direction="up" if completion_change > 0 else "down" if completion_change < 0 else "neutral",
                icon="check-circle",
                color="green",
                subtitle="This month",
                link="/admin/cases?status=completed"
            ),
            KPICard(
                title="New Clients",
                value=new_clients_this_week,
                change=client_change,
                change_direction="up" if client_change > 0 else "down" if client_change < 0 else "neutral",
                icon="users",
                color="purple",
                subtitle="This week",
                link="/admin/clients"
            ),
            KPICard(
                title="Total Cases",
                value=total_cases,
                change=0,
                change_direction="neutral",
                icon="folder",
                color="gray",
                subtitle=f"{total_clients} total clients",
                link="/admin/cases"
            ),
            KPICard(
                title="Pending Review",
                value=pending_cases,
                change=0,
                change_direction="neutral",
                icon="clock",
                color="yellow" if pending_cases > 5 else "blue",
                subtitle="Awaiting action",
                link="/admin/cases?status=pending"
            )
        ]

    async def get_activity_feed(
        self,
        limit: int = 20,
        offset: int = 0,
        user_id: Optional[str] = None
    ) -> List[ActivityItem]:
        """Get recent activity feed."""
        query = {}
        if user_id:
            query["user_id"] = user_id

        # Get activities from database
        activities = []

        # Recent case activities
        cases_cursor = self.db.cases.find(
            query if not query else {},
            limit=limit
        ).sort("updated_at", -1)

        async for case in cases_cursor:
            activities.append(ActivityItem(
                activity_id=hashlib.md5(f"case:{case['_id']}:{case.get('updated_at', '')}".encode()).hexdigest()[:12],
                activity_type=ActivityType.CASE_UPDATED,
                title=f"Case Updated: {case.get('title', 'Untitled')}",
                description=f"Status: {case.get('status', 'unknown')}",
                timestamp=case.get("updated_at", datetime.utcnow()),
                case_id=str(case["_id"]),
                case_name=case.get("title", "Untitled")
            ))

        # Recent evidence uploads
        evidence_cursor = self.db.forensic_analyses.find(
            {},
            limit=limit
        ).sort("created_at", -1)

        async for evidence in evidence_cursor:
            activities.append(ActivityItem(
                activity_id=hashlib.md5(f"evidence:{evidence['_id']}".encode()).hexdigest()[:12],
                activity_type=ActivityType.EVIDENCE_UPLOADED,
                title="Evidence Uploaded",
                description=f"Analysis for case {evidence.get('case_id', 'Unknown')}",
                timestamp=evidence.get("created_at", datetime.utcnow()),
                case_id=str(evidence.get("case_id", ""))
            ))

        # Sort all activities by timestamp
        activities.sort(key=lambda x: x.timestamp, reverse=True)

        return activities[offset:offset + limit]

    async def get_case_kanban(self) -> Dict[str, List[CaseKanbanItem]]:
        """Get cases organized by status for Kanban board."""
        kanban = {
            "pending": [],
            "in_progress": [],
            "under_review": [],
            "completed": []
        }

        cursor = self.db.cases.find({
            "status": {"$ne": "archived"}
        }).sort("priority", 1).limit(100)

        async for case in cursor:
            status = case.get("status", "pending")
            if status not in kanban:
                status = "pending"

            item = CaseKanbanItem(
                case_id=str(case["_id"]),
                title=case.get("title", "Untitled Case"),
                client_name=case.get("client_name", "Unknown"),
                status=CaseStatus(status) if status in [s.value for s in CaseStatus] else CaseStatus.PENDING,
                risk_level=RiskLevel(case.get("risk_level", "medium")),
                assigned_to=case.get("assigned_to"),
                due_date=case.get("due_date"),
                priority=case.get("priority", 3),
                created_at=case.get("created_at", datetime.utcnow()),
                last_activity=case.get("updated_at", datetime.utcnow()),
                tags=case.get("tags", [])
            )
            kanban[status].append(item)

        return kanban

    async def get_due_date_alerts(self, days_ahead: int = 7) -> List[DueDateAlert]:
        """Get cases with upcoming or overdue due dates."""
        alerts = []
        now = datetime.utcnow()
        future_date = now + timedelta(days=days_ahead)

        cursor = self.db.cases.find({
            "status": {"$nin": ["completed", "archived"]},
            "due_date": {"$exists": True, "$lte": future_date}
        }).sort("due_date", 1)

        async for case in cursor:
            due_date = case.get("due_date")
            if not due_date:
                continue

            days_remaining = (due_date - now).days

            if days_remaining < 0:
                severity = "overdue"
            elif days_remaining <= 2:
                severity = "urgent"
            else:
                severity = "warning"

            alerts.append(DueDateAlert(
                alert_id=hashlib.md5(f"due:{case['_id']}".encode()).hexdigest()[:12],
                case_id=str(case["_id"]),
                case_title=case.get("title", "Untitled"),
                due_date=due_date,
                days_remaining=days_remaining,
                severity=severity,
                assigned_to=case.get("assigned_to")
            ))

        return alerts

    async def get_team_overview(self) -> List[TeamMember]:
        """Get team members with their case counts."""
        team = []

        cursor = self.db.users.find({"role": {"$in": ["admin", "analyst", "reviewer"]}})

        async for user in cursor:
            user_id = str(user["_id"])

            # Count cases
            active = await self.db.cases.count_documents({
                "assigned_to": user_id,
                "status": {"$nin": ["completed", "archived"]}
            })

            completed = await self.db.cases.count_documents({
                "assigned_to": user_id,
                "status": "completed"
            })

            team.append(TeamMember(
                user_id=user_id,
                name=user.get("name", user.get("email", "Unknown")),
                email=user.get("email", ""),
                role=user.get("role", "analyst"),
                avatar_url=user.get("avatar_url"),
                active_cases=active,
                completed_cases=completed,
                is_online=user.get("is_online", False),
                last_seen=user.get("last_seen")
            ))

        return team

    async def get_risk_distribution(self) -> Dict[str, Any]:
        """Get risk level distribution across cases."""
        pipeline = [
            {"$match": {"status": {"$nin": ["archived"]}}},
            {"$group": {
                "_id": "$risk_level",
                "count": {"$sum": 1}
            }}
        ]

        distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        total = 0

        async for result in self.db.cases.aggregate(pipeline):
            level = result["_id"]
            count = result["count"]
            if level in distribution:
                distribution[level] = count
                total += count

        # Calculate percentages
        percentages = {}
        for level, count in distribution.items():
            percentages[level] = round((count / total * 100) if total > 0 else 0, 1)

        return {
            "counts": distribution,
            "percentages": percentages,
            "total": total
        }

    async def get_case_completion_metrics(self, period_days: int = 30) -> Dict[str, Any]:
        """Get case completion metrics over time."""
        now = datetime.utcnow()
        start_date = now - timedelta(days=period_days)

        # Daily completions
        pipeline = [
            {"$match": {
                "status": "completed",
                "completed_at": {"$gte": start_date}
            }},
            {"$group": {
                "_id": {
                    "year": {"$year": "$completed_at"},
                    "month": {"$month": "$completed_at"},
                    "day": {"$dayOfMonth": "$completed_at"}
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]

        daily_completions = []
        async for result in self.db.cases.aggregate(pipeline):
            date_parts = result["_id"]
            date_str = f"{date_parts['year']}-{date_parts['month']:02d}-{date_parts['day']:02d}"
            daily_completions.append({
                "date": date_str,
                "count": result["count"]
            })

        # Average completion time
        pipeline = [
            {"$match": {
                "status": "completed",
                "completed_at": {"$exists": True},
                "created_at": {"$exists": True}
            }},
            {"$project": {
                "duration": {
                    "$divide": [
                        {"$subtract": ["$completed_at", "$created_at"]},
                        1000 * 60 * 60 * 24  # Convert to days
                    ]
                }
            }},
            {"$group": {
                "_id": None,
                "avg_duration": {"$avg": "$duration"},
                "min_duration": {"$min": "$duration"},
                "max_duration": {"$max": "$duration"}
            }}
        ]

        duration_stats = {"avg": 0, "min": 0, "max": 0}
        async for result in self.db.cases.aggregate(pipeline):
            duration_stats = {
                "avg": round(result.get("avg_duration", 0), 1),
                "min": round(result.get("min_duration", 0), 1),
                "max": round(result.get("max_duration", 0), 1)
            }

        return {
            "daily_completions": daily_completions,
            "duration_stats": duration_stats,
            "period_days": period_days
        }

    async def get_client_satisfaction(self) -> Dict[str, Any]:
        """Get client satisfaction metrics."""
        pipeline = [
            {"$match": {"satisfaction_rating": {"$exists": True}}},
            {"$group": {
                "_id": "$satisfaction_rating",
                "count": {"$sum": 1}
            }}
        ]

        ratings = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total = 0
        sum_ratings = 0

        async for result in self.db.cases.aggregate(pipeline):
            rating = result["_id"]
            count = result["count"]
            if rating in ratings:
                ratings[rating] = count
                total += count
                sum_ratings += rating * count

        avg_rating = round(sum_ratings / total, 2) if total > 0 else 0

        return {
            "distribution": ratings,
            "total_responses": total,
            "average_rating": avg_rating,
            "positive_percentage": round(
                (ratings[4] + ratings[5]) / total * 100 if total > 0 else 0, 1
            )
        }

    async def get_quick_actions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get quick action buttons based on user role and pending items."""
        actions = []

        # Check for pending items
        pending_cases = await self._count_cases({"status": "pending"})
        if pending_cases > 0:
            actions.append({
                "id": "review_pending",
                "label": f"Review Pending ({pending_cases})",
                "icon": "clipboard-list",
                "color": "yellow",
                "link": "/admin/cases?status=pending",
                "priority": 1
            })

        # Check for unread alerts
        unread_alerts = await self._count_alerts({"resolved": False, "read": False})
        if unread_alerts > 0:
            actions.append({
                "id": "check_alerts",
                "label": f"Check Alerts ({unread_alerts})",
                "icon": "bell",
                "color": "red",
                "link": "/admin/alerts",
                "priority": 2
            })

        # Standard actions
        actions.extend([
            {
                "id": "new_case",
                "label": "New Case",
                "icon": "plus-circle",
                "color": "blue",
                "link": "/admin/cases/new",
                "priority": 3
            },
            {
                "id": "generate_report",
                "label": "Generate Report",
                "icon": "file-text",
                "color": "green",
                "link": "/admin/reports/generate",
                "priority": 4
            },
            {
                "id": "upload_evidence",
                "label": "Upload Evidence",
                "icon": "upload",
                "color": "purple",
                "link": "/admin/evidence/upload",
                "priority": 5
            }
        ])

        # Sort by priority
        actions.sort(key=lambda x: x["priority"])

        return actions

    async def get_notifications(
        self,
        user_id: str,
        limit: int = 10,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get user notifications."""
        query = {"user_id": user_id}
        if unread_only:
            query["read"] = False

        notifications = []
        cursor = self.db.notifications.find(query).sort("created_at", -1).limit(limit)

        async for notif in cursor:
            notifications.append({
                "id": str(notif["_id"]),
                "type": notif.get("type", "info"),
                "title": notif.get("title", ""),
                "message": notif.get("message", ""),
                "read": notif.get("read", False),
                "created_at": notif.get("created_at", datetime.utcnow()).isoformat(),
                "link": notif.get("link"),
                "metadata": notif.get("metadata", {})
            })

        return notifications

    async def get_notification_count(self, user_id: str) -> int:
        """Get unread notification count."""
        return await self.db.notifications.count_documents({
            "user_id": user_id,
            "read": False
        })

    # Helper methods
    async def _count_cases(self, query: Dict) -> int:
        """Count cases matching query."""
        try:
            return await self.db.cases.count_documents(query)
        except Exception:
            return 0

    async def _count_alerts(self, query: Dict) -> int:
        """Count alerts matching query."""
        try:
            return await self.db.alerts.count_documents(query)
        except Exception:
            return 0

    async def _count_clients(self, query: Dict) -> int:
        """Count clients matching query."""
        try:
            return await self.db.clients.count_documents(query)
        except Exception:
            return 0

    def _calc_change(self, current: int, previous: int) -> float:
        """Calculate percentage change."""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 1)
