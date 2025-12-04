"""
Real Analytics Dashboard Router
Comprehensive analytics and business intelligence for SafeChild Law Firm
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from bson import ObjectId
import asyncio

from ..auth import get_current_admin_user
from .. import db

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# =============================================================================
# Overview Analytics
# =============================================================================

@router.get("/overview")
async def get_analytics_overview(
    period: str = Query("30d", description="Time period: 7d, 30d, 90d, 1y, all"),
    current_user: dict = Depends(get_current_admin_user)
):
    """Get comprehensive analytics overview."""

    # Calculate date range
    now = datetime.utcnow()
    if period == "7d":
        start_date = now - timedelta(days=7)
    elif period == "30d":
        start_date = now - timedelta(days=30)
    elif period == "90d":
        start_date = now - timedelta(days=90)
    elif period == "1y":
        start_date = now - timedelta(days=365)
    else:
        start_date = datetime(2020, 1, 1)  # All time

    # Previous period for comparison
    period_length = (now - start_date).days
    prev_start = start_date - timedelta(days=period_length)
    prev_end = start_date

    # Parallel data fetching
    results = await asyncio.gather(
        get_client_stats(start_date, now, prev_start, prev_end),
        get_case_stats(start_date, now, prev_start, prev_end),
        get_document_stats(start_date, now, prev_start, prev_end),
        get_meeting_stats(start_date, now, prev_start, prev_end),
        get_evidence_stats(start_date, now, prev_start, prev_end),
        get_forensic_stats(start_date, now, prev_start, prev_end),
        return_exceptions=True
    )

    client_stats, case_stats, doc_stats, meeting_stats, evidence_stats, forensic_stats = results

    return {
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": now.isoformat(),
        "clients": client_stats if not isinstance(client_stats, Exception) else {},
        "cases": case_stats if not isinstance(case_stats, Exception) else {},
        "documents": doc_stats if not isinstance(doc_stats, Exception) else {},
        "meetings": meeting_stats if not isinstance(meeting_stats, Exception) else {},
        "evidence": evidence_stats if not isinstance(evidence_stats, Exception) else {},
        "forensics": forensic_stats if not isinstance(forensic_stats, Exception) else {}
    }


async def get_client_stats(start_date: datetime, end_date: datetime,
                           prev_start: datetime, prev_end: datetime) -> Dict:
    """Get client statistics."""
    # Current period
    current_count = await db.db.clients.count_documents({
        "createdAt": {"$gte": start_date, "$lte": end_date}
    })

    # Previous period
    prev_count = await db.db.clients.count_documents({
        "createdAt": {"$gte": prev_start, "$lte": prev_end}
    })

    # Total clients
    total = await db.db.clients.count_documents({})

    # Active clients (have activity in last 30 days)
    active = await db.db.clients.count_documents({
        "lastActivity": {"$gte": datetime.utcnow() - timedelta(days=30)}
    })

    # Status breakdown
    status_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_breakdown = await db.db.clients.aggregate(status_pipeline).to_list(100)

    # Calculate change percentage
    change = 0
    if prev_count > 0:
        change = round(((current_count - prev_count) / prev_count) * 100, 1)
    elif current_count > 0:
        change = 100

    return {
        "total": total,
        "new_in_period": current_count,
        "active": active,
        "change_percent": change,
        "by_status": {s["_id"]: s["count"] for s in status_breakdown if s["_id"]}
    }


async def get_case_stats(start_date: datetime, end_date: datetime,
                         prev_start: datetime, prev_end: datetime) -> Dict:
    """Get case statistics."""
    # Current period cases
    current = await db.db.cases.count_documents({
        "created_at": {"$gte": start_date, "$lte": end_date}
    })

    # Previous period
    prev = await db.db.cases.count_documents({
        "created_at": {"$gte": prev_start, "$lte": prev_end}
    })

    # Total cases
    total = await db.db.cases.count_documents({})

    # By status
    status_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_breakdown = await db.db.cases.aggregate(status_pipeline).to_list(100)

    # By type
    type_pipeline = [
        {"$group": {"_id": "$case_type", "count": {"$sum": 1}}}
    ]
    type_breakdown = await db.db.cases.aggregate(type_pipeline).to_list(100)

    # Calculate change
    change = 0
    if prev > 0:
        change = round(((current - prev) / prev) * 100, 1)
    elif current > 0:
        change = 100

    # Active vs closed
    active = await db.db.cases.count_documents({"status": {"$in": ["active", "in_progress", "pending"]}})
    closed = await db.db.cases.count_documents({"status": {"$in": ["closed", "completed", "resolved"]}})

    return {
        "total": total,
        "new_in_period": current,
        "active": active,
        "closed": closed,
        "change_percent": change,
        "by_status": {s["_id"]: s["count"] for s in status_breakdown if s["_id"]},
        "by_type": {t["_id"]: t["count"] for t in type_breakdown if t["_id"]}
    }


async def get_document_stats(start_date: datetime, end_date: datetime,
                             prev_start: datetime, prev_end: datetime) -> Dict:
    """Get document statistics."""
    current = await db.db.documents.count_documents({
        "uploadedAt": {"$gte": start_date, "$lte": end_date}
    })

    prev = await db.db.documents.count_documents({
        "uploadedAt": {"$gte": prev_start, "$lte": prev_end}
    })

    total = await db.db.documents.count_documents({})

    # By type
    type_pipeline = [
        {"$group": {"_id": "$type", "count": {"$sum": 1}}}
    ]
    type_breakdown = await db.db.documents.aggregate(type_pipeline).to_list(100)

    # Total size (if tracked)
    size_pipeline = [
        {"$group": {"_id": None, "total_size": {"$sum": "$size"}}}
    ]
    size_result = await db.db.documents.aggregate(size_pipeline).to_list(1)
    total_size = size_result[0]["total_size"] if size_result else 0

    change = 0
    if prev > 0:
        change = round(((current - prev) / prev) * 100, 1)
    elif current > 0:
        change = 100

    return {
        "total": total,
        "new_in_period": current,
        "total_size_mb": round(total_size / (1024 * 1024), 2) if total_size else 0,
        "change_percent": change,
        "by_type": {t["_id"]: t["count"] for t in type_breakdown if t["_id"]}
    }


async def get_meeting_stats(start_date: datetime, end_date: datetime,
                            prev_start: datetime, prev_end: datetime) -> Dict:
    """Get meeting statistics."""
    current = await db.db.meetings.count_documents({
        "createdAt": {"$gte": start_date, "$lte": end_date}
    })

    prev = await db.db.meetings.count_documents({
        "createdAt": {"$gte": prev_start, "$lte": prev_end}
    })

    total = await db.db.meetings.count_documents({})

    # Upcoming meetings
    upcoming = await db.db.meetings.count_documents({
        "scheduledTime": {"$gte": datetime.utcnow()},
        "status": {"$ne": "cancelled"}
    })

    # Completed meetings
    completed = await db.db.meetings.count_documents({
        "status": "completed"
    })

    # By type
    type_pipeline = [
        {"$group": {"_id": "$type", "count": {"$sum": 1}}}
    ]
    type_breakdown = await db.db.meetings.aggregate(type_pipeline).to_list(100)

    change = 0
    if prev > 0:
        change = round(((current - prev) / prev) * 100, 1)
    elif current > 0:
        change = 100

    return {
        "total": total,
        "new_in_period": current,
        "upcoming": upcoming,
        "completed": completed,
        "change_percent": change,
        "by_type": {t["_id"]: t["count"] for t in type_breakdown if t["_id"]}
    }


async def get_evidence_stats(start_date: datetime, end_date: datetime,
                             prev_start: datetime, prev_end: datetime) -> Dict:
    """Get evidence collection statistics."""
    # Evidence items
    current = await db.db.evidence_items.count_documents({
        "collected_at": {"$gte": start_date, "$lte": end_date}
    })

    prev = await db.db.evidence_items.count_documents({
        "collected_at": {"$gte": prev_start, "$lte": prev_end}
    })

    total = await db.db.evidence_items.count_documents({})

    # Sessions
    total_sessions = await db.db.evidence_sessions.count_documents({})
    active_sessions = await db.db.evidence_sessions.count_documents({"status": "active"})

    # By platform
    platform_pipeline = [
        {"$group": {"_id": "$platform", "count": {"$sum": 1}}}
    ]
    platform_breakdown = await db.db.evidence_items.aggregate(platform_pipeline).to_list(100)

    change = 0
    if prev > 0:
        change = round(((current - prev) / prev) * 100, 1)
    elif current > 0:
        change = 100

    return {
        "total_items": total,
        "new_in_period": current,
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "change_percent": change,
        "by_platform": {p["_id"]: p["count"] for p in platform_breakdown if p["_id"]}
    }


async def get_forensic_stats(start_date: datetime, end_date: datetime,
                             prev_start: datetime, prev_end: datetime) -> Dict:
    """Get forensic analysis statistics."""
    current = await db.db.forensic_analyses.count_documents({
        "created_at": {"$gte": start_date, "$lte": end_date}
    })

    prev = await db.db.forensic_analyses.count_documents({
        "created_at": {"$gte": prev_start, "$lte": prev_end}
    })

    total = await db.db.forensic_analyses.count_documents({})

    # By status
    status_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_breakdown = await db.db.forensic_analyses.aggregate(status_pipeline).to_list(100)

    # Average risk score
    risk_pipeline = [
        {"$match": {"risk_score": {"$exists": True}}},
        {"$group": {"_id": None, "avg_risk": {"$avg": "$risk_score"}}}
    ]
    risk_result = await db.db.forensic_analyses.aggregate(risk_pipeline).to_list(1)
    avg_risk = risk_result[0]["avg_risk"] if risk_result else 0

    # High risk cases
    high_risk = await db.db.forensic_analyses.count_documents({
        "risk_level": {"$in": ["high", "critical"]}
    })

    change = 0
    if prev > 0:
        change = round(((current - prev) / prev) * 100, 1)
    elif current > 0:
        change = 100

    return {
        "total": total,
        "new_in_period": current,
        "high_risk_cases": high_risk,
        "avg_risk_score": round(avg_risk, 1) if avg_risk else 0,
        "change_percent": change,
        "by_status": {s["_id"]: s["count"] for s in status_breakdown if s["_id"]}
    }


# =============================================================================
# Time Series Data
# =============================================================================

@router.get("/trends")
async def get_trends(
    metric: str = Query(..., description="Metric: clients, cases, documents, meetings, evidence"),
    period: str = Query("30d", description="Time period: 7d, 30d, 90d, 1y"),
    granularity: str = Query("day", description="Granularity: hour, day, week, month"),
    current_user: dict = Depends(get_current_admin_user)
):
    """Get time series trends for a specific metric."""

    now = datetime.utcnow()
    if period == "7d":
        start_date = now - timedelta(days=7)
    elif period == "30d":
        start_date = now - timedelta(days=30)
    elif period == "90d":
        start_date = now - timedelta(days=90)
    else:
        start_date = now - timedelta(days=365)

    # Collection mapping
    collection_map = {
        "clients": ("clients", "createdAt"),
        "cases": ("cases", "created_at"),
        "documents": ("documents", "uploadedAt"),
        "meetings": ("meetings", "createdAt"),
        "evidence": ("evidence_items", "collected_at")
    }

    if metric not in collection_map:
        raise HTTPException(status_code=400, detail="Invalid metric")

    collection_name, date_field = collection_map[metric]
    collection = db.db[collection_name]

    # Date format for grouping
    if granularity == "hour":
        date_format = "%Y-%m-%d %H:00"
    elif granularity == "day":
        date_format = "%Y-%m-%d"
    elif granularity == "week":
        date_format = "%Y-W%U"
    else:
        date_format = "%Y-%m"

    # Aggregation pipeline
    pipeline = [
        {"$match": {date_field: {"$gte": start_date, "$lte": now}}},
        {"$group": {
            "_id": {"$dateToString": {"format": date_format, "date": f"${date_field}"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]

    results = await collection.aggregate(pipeline).to_list(1000)

    return {
        "metric": metric,
        "period": period,
        "granularity": granularity,
        "data": [{"date": r["_id"], "count": r["count"]} for r in results]
    }


# =============================================================================
# Performance Metrics
# =============================================================================

@router.get("/performance")
async def get_performance_metrics(
    current_user: dict = Depends(get_current_admin_user)
):
    """Get performance and efficiency metrics."""

    now = datetime.utcnow()
    last_30_days = now - timedelta(days=30)

    # Average case resolution time
    case_pipeline = [
        {"$match": {
            "status": {"$in": ["closed", "completed", "resolved"]},
            "created_at": {"$exists": True},
            "closed_at": {"$exists": True}
        }},
        {"$project": {
            "resolution_days": {
                "$divide": [
                    {"$subtract": ["$closed_at", "$created_at"]},
                    1000 * 60 * 60 * 24  # Convert to days
                ]
            }
        }},
        {"$group": {
            "_id": None,
            "avg_days": {"$avg": "$resolution_days"},
            "min_days": {"$min": "$resolution_days"},
            "max_days": {"$max": "$resolution_days"}
        }}
    ]
    case_resolution = await db.db.cases.aggregate(case_pipeline).to_list(1)

    # Client response time (time from registration to first meeting)
    response_pipeline = [
        {"$match": {"createdAt": {"$gte": last_30_days}}},
        {"$lookup": {
            "from": "meetings",
            "localField": "clientNumber",
            "foreignField": "clientNumber",
            "as": "meetings"
        }},
        {"$match": {"meetings.0": {"$exists": True}}},
        {"$project": {
            "response_hours": {
                "$divide": [
                    {"$subtract": [
                        {"$arrayElemAt": ["$meetings.createdAt", 0]},
                        "$createdAt"
                    ]},
                    1000 * 60 * 60  # Convert to hours
                ]
            }
        }},
        {"$group": {
            "_id": None,
            "avg_hours": {"$avg": "$response_hours"}
        }}
    ]
    response_time = await db.db.clients.aggregate(response_pipeline).to_list(1)

    # Document upload rate
    doc_count = await db.db.documents.count_documents({
        "uploadedAt": {"$gte": last_30_days}
    })

    # Evidence collection efficiency
    evidence_pipeline = [
        {"$match": {"created_at": {"$gte": last_30_days}}},
        {"$group": {
            "_id": "$session_id",
            "items_collected": {"$sum": 1}
        }},
        {"$group": {
            "_id": None,
            "avg_items_per_session": {"$avg": "$items_collected"}
        }}
    ]
    evidence_efficiency = await db.db.evidence_items.aggregate(evidence_pipeline).to_list(1)

    # Task completion rate
    task_total = await db.db.timeline_tasks.count_documents({
        "created_at": {"$gte": last_30_days}
    })
    task_completed = await db.db.timeline_tasks.count_documents({
        "created_at": {"$gte": last_30_days},
        "status": "completed"
    })

    return {
        "case_resolution": {
            "avg_days": round(case_resolution[0]["avg_days"], 1) if case_resolution else None,
            "min_days": round(case_resolution[0]["min_days"], 1) if case_resolution else None,
            "max_days": round(case_resolution[0]["max_days"], 1) if case_resolution else None
        },
        "client_response": {
            "avg_hours": round(response_time[0]["avg_hours"], 1) if response_time else None
        },
        "documents": {
            "uploads_last_30_days": doc_count,
            "avg_per_day": round(doc_count / 30, 1)
        },
        "evidence_collection": {
            "avg_items_per_session": round(evidence_efficiency[0]["avg_items_per_session"], 1) if evidence_efficiency else None
        },
        "tasks": {
            "total": task_total,
            "completed": task_completed,
            "completion_rate": round((task_completed / task_total) * 100, 1) if task_total > 0 else 0
        }
    }


# =============================================================================
# Geographic Analytics
# =============================================================================

@router.get("/geographic")
async def get_geographic_analytics(
    current_user: dict = Depends(get_current_admin_user)
):
    """Get geographic distribution of clients and cases."""

    # Clients by country
    country_pipeline = [
        {"$match": {"country": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$country", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    by_country = await db.db.clients.aggregate(country_pipeline).to_list(20)

    # Clients by city
    city_pipeline = [
        {"$match": {"city": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$city", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    by_city = await db.db.clients.aggregate(city_pipeline).to_list(20)

    # International cases
    international = await db.db.cases.count_documents({
        "case_type": {"$in": ["international_custody", "hague_convention"]}
    })

    # Cases by jurisdiction
    jurisdiction_pipeline = [
        {"$match": {"jurisdiction": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$jurisdiction", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    by_jurisdiction = await db.db.cases.aggregate(jurisdiction_pipeline).to_list(10)

    return {
        "clients_by_country": [{"country": c["_id"], "count": c["count"]} for c in by_country],
        "clients_by_city": [{"city": c["_id"], "count": c["count"]} for c in by_city],
        "international_cases": international,
        "cases_by_jurisdiction": [{"jurisdiction": j["_id"], "count": j["count"]} for j in by_jurisdiction]
    }


# =============================================================================
# Risk Analytics
# =============================================================================

@router.get("/risk-distribution")
async def get_risk_distribution(
    current_user: dict = Depends(get_current_admin_user)
):
    """Get risk level distribution across cases and forensic analyses."""

    # Forensic risk distribution
    forensic_pipeline = [
        {"$match": {"risk_level": {"$exists": True}}},
        {"$group": {"_id": "$risk_level", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    forensic_risk = await db.db.forensic_analyses.aggregate(forensic_pipeline).to_list(10)

    # Risk scores histogram
    score_pipeline = [
        {"$match": {"risk_score": {"$exists": True}}},
        {"$bucket": {
            "groupBy": "$risk_score",
            "boundaries": [0, 20, 40, 60, 80, 100],
            "default": "100+",
            "output": {"count": {"$sum": 1}}
        }}
    ]
    score_distribution = await db.db.forensic_analyses.aggregate(score_pipeline).to_list(10)

    # High risk indicators
    indicator_pipeline = [
        {"$match": {"risk_indicators": {"$exists": True, "$ne": []}}},
        {"$unwind": "$risk_indicators"},
        {"$group": {"_id": "$risk_indicators", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_indicators = await db.db.forensic_analyses.aggregate(indicator_pipeline).to_list(10)

    # Cases requiring immediate attention
    urgent_cases = await db.db.forensic_analyses.count_documents({
        "risk_level": {"$in": ["critical", "high"]},
        "status": {"$ne": "resolved"}
    })

    return {
        "by_level": {r["_id"]: r["count"] for r in forensic_risk},
        "score_distribution": [
            {"range": f"{s['_id']}-{s['_id']+19}", "count": s["count"]}
            for s in score_distribution if isinstance(s["_id"], (int, float))
        ],
        "top_risk_indicators": [{"indicator": i["_id"], "count": i["count"]} for i in top_indicators],
        "urgent_cases": urgent_cases
    }


# =============================================================================
# Activity Feed
# =============================================================================

@router.get("/activity-feed")
async def get_activity_feed(
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_admin_user)
):
    """Get recent activity feed across all modules."""

    activities = []
    now = datetime.utcnow()

    # Recent clients
    clients = await db.db.clients.find(
        {"createdAt": {"$exists": True}},
        {"clientNumber": 1, "name": 1, "email": 1, "createdAt": 1}
    ).sort("createdAt", -1).limit(10).to_list(10)

    for c in clients:
        activities.append({
            "type": "client_registered",
            "timestamp": c.get("createdAt"),
            "title": "Yeni müvekkil kaydı",
            "description": f"{c.get('name', 'İsimsiz')} sisteme kaydoldu",
            "reference": c.get("clientNumber")
        })

    # Recent cases
    cases = await db.db.cases.find(
        {"created_at": {"$exists": True}},
        {"case_id": 1, "case_type": 1, "client_name": 1, "created_at": 1}
    ).sort("created_at", -1).limit(10).to_list(10)

    for c in cases:
        activities.append({
            "type": "case_created",
            "timestamp": c.get("created_at"),
            "title": "Yeni dava oluşturuldu",
            "description": f"{c.get('case_type', 'Dava')} - {c.get('client_name', '')}",
            "reference": c.get("case_id")
        })

    # Recent documents
    docs = await db.db.documents.find(
        {"uploadedAt": {"$exists": True}},
        {"documentNumber": 1, "title": 1, "type": 1, "uploadedAt": 1}
    ).sort("uploadedAt", -1).limit(10).to_list(10)

    for d in docs:
        activities.append({
            "type": "document_uploaded",
            "timestamp": d.get("uploadedAt"),
            "title": "Belge yüklendi",
            "description": d.get("title", "Yeni belge"),
            "reference": d.get("documentNumber")
        })

    # Recent meetings
    meetings = await db.db.meetings.find(
        {"createdAt": {"$exists": True}},
        {"meetingId": 1, "type": 1, "clientName": 1, "createdAt": 1}
    ).sort("createdAt", -1).limit(10).to_list(10)

    for m in meetings:
        activities.append({
            "type": "meeting_scheduled",
            "timestamp": m.get("createdAt"),
            "title": "Toplantı planlandı",
            "description": f"{m.get('type', 'Toplantı')} - {m.get('clientName', '')}",
            "reference": m.get("meetingId")
        })

    # Recent forensic analyses
    forensics = await db.db.forensic_analyses.find(
        {"created_at": {"$exists": True}},
        {"case_id": 1, "risk_level": 1, "created_at": 1}
    ).sort("created_at", -1).limit(10).to_list(10)

    for f in forensics:
        activities.append({
            "type": "forensic_analysis",
            "timestamp": f.get("created_at"),
            "title": "Adli analiz tamamlandı",
            "description": f"Risk seviyesi: {f.get('risk_level', 'Bilinmiyor')}",
            "reference": f.get("case_id")
        })

    # Sort by timestamp and limit
    activities.sort(key=lambda x: x.get("timestamp") or datetime.min, reverse=True)
    activities = activities[:limit]

    return {
        "activities": activities,
        "total": len(activities)
    }


# =============================================================================
# Export Analytics
# =============================================================================

@router.get("/export")
async def export_analytics(
    format: str = Query("json", description="Export format: json, csv"),
    period: str = Query("30d", description="Time period"),
    current_user: dict = Depends(get_current_admin_user)
):
    """Export analytics data for reporting."""

    # Get overview data
    overview = await get_analytics_overview(period, current_user)

    if format == "csv":
        # Create CSV-friendly data
        csv_data = []

        # Clients
        csv_data.append({
            "category": "Müvekkiller",
            "total": overview["clients"].get("total", 0),
            "new": overview["clients"].get("new_in_period", 0),
            "active": overview["clients"].get("active", 0),
            "change": overview["clients"].get("change_percent", 0)
        })

        # Cases
        csv_data.append({
            "category": "Davalar",
            "total": overview["cases"].get("total", 0),
            "new": overview["cases"].get("new_in_period", 0),
            "active": overview["cases"].get("active", 0),
            "change": overview["cases"].get("change_percent", 0)
        })

        # Documents
        csv_data.append({
            "category": "Belgeler",
            "total": overview["documents"].get("total", 0),
            "new": overview["documents"].get("new_in_period", 0),
            "active": 0,
            "change": overview["documents"].get("change_percent", 0)
        })

        # Meetings
        csv_data.append({
            "category": "Toplantılar",
            "total": overview["meetings"].get("total", 0),
            "new": overview["meetings"].get("new_in_period", 0),
            "active": overview["meetings"].get("upcoming", 0),
            "change": overview["meetings"].get("change_percent", 0)
        })

        return {
            "format": "csv",
            "data": csv_data,
            "headers": ["category", "total", "new", "active", "change"]
        }

    return {
        "format": "json",
        "data": overview
    }
