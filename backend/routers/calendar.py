"""
Calendar Integration Router
Unified calendar with Google/Outlook sync, reminders, and scheduling
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from bson import ObjectId
import uuid
from enum import Enum

from ..auth import get_current_admin_user, get_current_user
from .. import db

router = APIRouter(prefix="/calendar", tags=["Calendar"])


class EventType(str, Enum):
    MEETING = "meeting"
    COURT_DATE = "court_date"
    DEADLINE = "deadline"
    TASK = "task"
    REMINDER = "reminder"
    CONSULTATION = "consultation"
    DEPOSITION = "deposition"
    FILING = "filing"
    HEARING = "hearing"
    OTHER = "other"


class EventStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    RESCHEDULED = "rescheduled"


# =============================================================================
# Calendar Events CRUD
# =============================================================================

@router.get("/events")
async def get_calendar_events(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    event_type: Optional[str] = None,
    case_id: Optional[str] = None,
    client_number: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get calendar events with filters."""

    query = {"is_deleted": {"$ne": True}}

    # Date range filter
    if start_date:
        try:
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query["start_time"] = {"$gte": start}
        except:
            pass

    if end_date:
        try:
            end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            if "start_time" in query:
                query["start_time"]["$lte"] = end
            else:
                query["start_time"] = {"$lte": end}
        except:
            pass

    if event_type:
        query["event_type"] = event_type
    if case_id:
        query["case_id"] = case_id
    if client_number:
        query["client_number"] = client_number
    if status:
        query["status"] = status

    events = await db.db.calendar_events.find(query).sort("start_time", 1).to_list(500)

    return {
        "events": [
            {
                "event_id": e["event_id"],
                "title": e["title"],
                "description": e.get("description"),
                "event_type": e["event_type"],
                "start_time": e["start_time"],
                "end_time": e.get("end_time"),
                "all_day": e.get("all_day", False),
                "location": e.get("location"),
                "case_id": e.get("case_id"),
                "client_number": e.get("client_number"),
                "client_name": e.get("client_name"),
                "status": e.get("status", "scheduled"),
                "color": e.get("color"),
                "reminders": e.get("reminders", []),
                "attendees": e.get("attendees", []),
                "recurrence": e.get("recurrence"),
                "external_id": e.get("external_id"),
                "external_source": e.get("external_source"),
                "created_by": e.get("created_by")
            }
            for e in events
        ],
        "total": len(events)
    }


@router.post("/events")
async def create_calendar_event(
    data: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Create a new calendar event."""

    if not data.get("title"):
        raise HTTPException(status_code=400, detail="Başlık zorunludur")
    if not data.get("start_time"):
        raise HTTPException(status_code=400, detail="Başlangıç zamanı zorunludur")

    # Parse start time
    try:
        start_time = datetime.fromisoformat(data["start_time"].replace("Z", "+00:00"))
    except:
        raise HTTPException(status_code=400, detail="Geçersiz başlangıç zamanı formatı")

    # Parse end time if provided
    end_time = None
    if data.get("end_time"):
        try:
            end_time = datetime.fromisoformat(data["end_time"].replace("Z", "+00:00"))
        except:
            pass

    # Default color based on event type
    default_colors = {
        "meeting": "#4F46E5",
        "court_date": "#DC2626",
        "deadline": "#F59E0B",
        "task": "#10B981",
        "reminder": "#8B5CF6",
        "consultation": "#3B82F6",
        "deposition": "#EC4899",
        "filing": "#6366F1",
        "hearing": "#EF4444",
        "other": "#6B7280"
    }

    event = {
        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
        "title": data["title"],
        "description": data.get("description"),
        "event_type": data.get("event_type", "other"),
        "start_time": start_time,
        "end_time": end_time,
        "all_day": data.get("all_day", False),
        "location": data.get("location"),
        "case_id": data.get("case_id"),
        "client_number": data.get("client_number"),
        "client_name": data.get("client_name"),
        "status": data.get("status", "scheduled"),
        "color": data.get("color") or default_colors.get(data.get("event_type", "other"), "#6B7280"),
        "reminders": data.get("reminders", []),
        "attendees": data.get("attendees", []),
        "recurrence": data.get("recurrence"),
        "notes": data.get("notes"),
        "created_at": datetime.utcnow(),
        "created_by": current_user.get("email"),
        "updated_at": datetime.utcnow(),
        "is_deleted": False
    }

    await db.db.calendar_events.insert_one(event)

    return {
        "success": True,
        "event_id": event["event_id"],
        "message": "Etkinlik oluşturuldu"
    }


@router.get("/events/{event_id}")
async def get_event_detail(
    event_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific event by ID."""

    event = await db.db.calendar_events.find_one({
        "event_id": event_id,
        "is_deleted": {"$ne": True}
    })

    if not event:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadı")

    return {
        "event_id": event["event_id"],
        "title": event["title"],
        "description": event.get("description"),
        "event_type": event["event_type"],
        "start_time": event["start_time"],
        "end_time": event.get("end_time"),
        "all_day": event.get("all_day", False),
        "location": event.get("location"),
        "case_id": event.get("case_id"),
        "client_number": event.get("client_number"),
        "client_name": event.get("client_name"),
        "status": event.get("status", "scheduled"),
        "color": event.get("color"),
        "reminders": event.get("reminders", []),
        "attendees": event.get("attendees", []),
        "recurrence": event.get("recurrence"),
        "notes": event.get("notes"),
        "created_at": event.get("created_at"),
        "created_by": event.get("created_by")
    }


@router.put("/events/{event_id}")
async def update_event(
    event_id: str,
    data: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Update a calendar event."""

    update_data = {"updated_at": datetime.utcnow()}

    # Parse dates if provided
    if "start_time" in data:
        try:
            update_data["start_time"] = datetime.fromisoformat(data["start_time"].replace("Z", "+00:00"))
        except:
            pass

    if "end_time" in data:
        try:
            update_data["end_time"] = datetime.fromisoformat(data["end_time"].replace("Z", "+00:00"))
        except:
            pass

    for field in ["title", "description", "event_type", "all_day", "location",
                  "case_id", "client_number", "client_name", "status", "color",
                  "reminders", "attendees", "recurrence", "notes"]:
        if field in data:
            update_data[field] = data[field]

    result = await db.db.calendar_events.update_one(
        {"event_id": event_id, "is_deleted": {"$ne": True}},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadı")

    return {"success": True, "message": "Etkinlik güncellendi"}


@router.delete("/events/{event_id}")
async def delete_event(
    event_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a calendar event (soft delete)."""

    result = await db.db.calendar_events.update_one(
        {"event_id": event_id},
        {"$set": {"is_deleted": True, "deleted_at": datetime.utcnow()}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadı")

    return {"success": True, "message": "Etkinlik silindi"}


# =============================================================================
# Quick Views
# =============================================================================

@router.get("/today")
async def get_today_events(
    current_user: dict = Depends(get_current_user)
):
    """Get today's events."""

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    events = await db.db.calendar_events.find({
        "start_time": {"$gte": today, "$lt": tomorrow},
        "is_deleted": {"$ne": True}
    }).sort("start_time", 1).to_list(100)

    return {
        "date": today.isoformat(),
        "events": [
            {
                "event_id": e["event_id"],
                "title": e["title"],
                "event_type": e["event_type"],
                "start_time": e["start_time"],
                "end_time": e.get("end_time"),
                "location": e.get("location"),
                "client_name": e.get("client_name"),
                "status": e.get("status"),
                "color": e.get("color")
            }
            for e in events
        ],
        "count": len(events)
    }


@router.get("/upcoming")
async def get_upcoming_events(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get upcoming events for the next N days."""

    now = datetime.utcnow()
    end_date = now + timedelta(days=days)

    events = await db.db.calendar_events.find({
        "start_time": {"$gte": now, "$lte": end_date},
        "is_deleted": {"$ne": True},
        "status": {"$nin": ["cancelled", "completed"]}
    }).sort("start_time", 1).limit(limit).to_list(limit)

    return {
        "period_days": days,
        "events": [
            {
                "event_id": e["event_id"],
                "title": e["title"],
                "event_type": e["event_type"],
                "start_time": e["start_time"],
                "end_time": e.get("end_time"),
                "location": e.get("location"),
                "client_name": e.get("client_name"),
                "case_id": e.get("case_id"),
                "status": e.get("status"),
                "color": e.get("color")
            }
            for e in events
        ],
        "count": len(events)
    }


@router.get("/deadlines")
async def get_upcoming_deadlines(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get upcoming deadlines and court dates."""

    now = datetime.utcnow()
    end_date = now + timedelta(days=days)

    events = await db.db.calendar_events.find({
        "start_time": {"$gte": now, "$lte": end_date},
        "event_type": {"$in": ["deadline", "court_date", "filing", "hearing"]},
        "is_deleted": {"$ne": True},
        "status": {"$nin": ["cancelled", "completed"]}
    }).sort("start_time", 1).to_list(100)

    # Group by urgency
    urgent = []  # Within 3 days
    upcoming = []  # Within 7 days
    later = []  # Beyond 7 days

    for e in events:
        days_until = (e["start_time"].replace(tzinfo=None) - now.replace(tzinfo=None)).days
        event_data = {
            "event_id": e["event_id"],
            "title": e["title"],
            "event_type": e["event_type"],
            "start_time": e["start_time"],
            "case_id": e.get("case_id"),
            "client_name": e.get("client_name"),
            "days_until": days_until
        }

        if days_until <= 3:
            urgent.append(event_data)
        elif days_until <= 7:
            upcoming.append(event_data)
        else:
            later.append(event_data)

    return {
        "urgent": urgent,
        "upcoming": upcoming,
        "later": later,
        "total": len(events)
    }


# =============================================================================
# Calendar Sync
# =============================================================================

@router.get("/sync/status")
async def get_sync_status(
    current_user: dict = Depends(get_current_user)
):
    """Get calendar sync status for current user."""

    # Check user's sync settings
    user_settings = await db.db.user_settings.find_one({
        "user_email": current_user.get("email")
    })

    google_connected = False
    outlook_connected = False
    last_sync = None

    if user_settings:
        google_connected = bool(user_settings.get("google_calendar_token"))
        outlook_connected = bool(user_settings.get("outlook_calendar_token"))
        last_sync = user_settings.get("last_calendar_sync")

    return {
        "google_calendar": {
            "connected": google_connected,
            "last_sync": last_sync
        },
        "outlook_calendar": {
            "connected": outlook_connected,
            "last_sync": last_sync
        }
    }


@router.post("/sync/google")
async def sync_google_calendar(
    data: dict = Body(...),
    current_user: dict = Depends(get_current_admin_user)
):
    """Initiate Google Calendar sync (placeholder for OAuth flow)."""

    # This would normally handle OAuth token exchange
    # For now, return instructions

    return {
        "status": "pending",
        "message": "Google Takvim entegrasyonu için OAuth yapılandırması gerekli",
        "instructions": [
            "1. Google Cloud Console'da OAuth 2.0 istemci kimlik bilgileri oluşturun",
            "2. Yetkilendirme URL'sine yönlendirin",
            "3. Geri dönüş kodunu kullanarak token alın",
            "4. Token'ı güvenli şekilde saklayın"
        ]
    }


@router.post("/sync/outlook")
async def sync_outlook_calendar(
    data: dict = Body(...),
    current_user: dict = Depends(get_current_admin_user)
):
    """Initiate Outlook Calendar sync (placeholder for OAuth flow)."""

    return {
        "status": "pending",
        "message": "Outlook Takvim entegrasyonu için Azure AD yapılandırması gerekli",
        "instructions": [
            "1. Azure AD'de uygulama kaydı oluşturun",
            "2. Microsoft Graph API izinlerini yapılandırın",
            "3. OAuth akışını tamamlayın",
            "4. Token'ı güvenli şekilde saklayın"
        ]
    }


# =============================================================================
# ICS Export
# =============================================================================

@router.get("/export/ics")
async def export_calendar_ics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    event_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Export calendar events as ICS format."""

    query = {"is_deleted": {"$ne": True}}

    if start_date:
        try:
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query["start_time"] = {"$gte": start}
        except:
            pass

    if end_date:
        try:
            end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            if "start_time" in query:
                query["start_time"]["$lte"] = end
            else:
                query["start_time"] = {"$lte": end}
        except:
            pass

    if event_type:
        query["event_type"] = event_type

    events = await db.db.calendar_events.find(query).to_list(500)

    # Generate ICS content
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//SafeChild Law Firm//Calendar//TR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:SafeChild Takvim"
    ]

    for event in events:
        start_dt = event["start_time"]
        end_dt = event.get("end_time") or (start_dt + timedelta(hours=1))

        ics_lines.extend([
            "BEGIN:VEVENT",
            f"UID:{event['event_id']}@safechild.com",
            f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART:{start_dt.strftime('%Y%m%dT%H%M%SZ')}",
            f"DTEND:{end_dt.strftime('%Y%m%dT%H%M%SZ')}",
            f"SUMMARY:{event['title']}",
        ])

        if event.get("description"):
            ics_lines.append(f"DESCRIPTION:{event['description']}")
        if event.get("location"):
            ics_lines.append(f"LOCATION:{event['location']}")

        ics_lines.append("END:VEVENT")

    ics_lines.append("END:VCALENDAR")

    ics_content = "\r\n".join(ics_lines)

    return {
        "content": ics_content,
        "filename": f"safechild_calendar_{datetime.now().strftime('%Y%m%d')}.ics",
        "content_type": "text/calendar"
    }


# =============================================================================
# Availability
# =============================================================================

@router.get("/availability")
async def get_availability(
    date: str,
    duration_minutes: int = Query(60, ge=15, le=480),
    current_user: dict = Depends(get_current_user)
):
    """Get available time slots for a specific date."""

    try:
        target_date = datetime.fromisoformat(date)
    except:
        raise HTTPException(status_code=400, detail="Geçersiz tarih formatı")

    # Get working hours (9 AM to 6 PM)
    day_start = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
    day_end = target_date.replace(hour=18, minute=0, second=0, microsecond=0)

    # Get existing events for the day
    events = await db.db.calendar_events.find({
        "start_time": {"$gte": day_start, "$lt": day_end},
        "is_deleted": {"$ne": True},
        "status": {"$nin": ["cancelled"]}
    }).sort("start_time", 1).to_list(100)

    # Find available slots
    available_slots = []
    current_time = day_start

    for event in events:
        event_start = event["start_time"]
        event_end = event.get("end_time") or (event_start + timedelta(hours=1))

        # Check if there's a gap before this event
        if current_time + timedelta(minutes=duration_minutes) <= event_start:
            available_slots.append({
                "start": current_time.isoformat(),
                "end": event_start.isoformat()
            })

        current_time = max(current_time, event_end)

    # Check for slot after last event
    if current_time + timedelta(minutes=duration_minutes) <= day_end:
        available_slots.append({
            "start": current_time.isoformat(),
            "end": day_end.isoformat()
        })

    return {
        "date": date,
        "duration_minutes": duration_minutes,
        "working_hours": {
            "start": "09:00",
            "end": "18:00"
        },
        "available_slots": available_slots,
        "existing_events": len(events)
    }


# =============================================================================
# Reminders
# =============================================================================

@router.get("/reminders/pending")
async def get_pending_reminders(
    current_user: dict = Depends(get_current_user)
):
    """Get pending reminders that need to be sent."""

    now = datetime.utcnow()
    upcoming = now + timedelta(hours=24)  # Next 24 hours

    events = await db.db.calendar_events.find({
        "start_time": {"$gte": now, "$lte": upcoming},
        "is_deleted": {"$ne": True},
        "status": {"$nin": ["cancelled", "completed"]},
        "reminders": {"$exists": True, "$ne": []}
    }).to_list(100)

    reminders = []
    for event in events:
        for reminder in event.get("reminders", []):
            reminder_time = event["start_time"] - timedelta(minutes=reminder.get("minutes_before", 30))
            if now <= reminder_time <= upcoming:
                reminders.append({
                    "event_id": event["event_id"],
                    "event_title": event["title"],
                    "event_time": event["start_time"],
                    "reminder_time": reminder_time,
                    "reminder_type": reminder.get("type", "notification"),
                    "client_name": event.get("client_name")
                })

    return {
        "reminders": sorted(reminders, key=lambda x: x["reminder_time"]),
        "count": len(reminders)
    }
