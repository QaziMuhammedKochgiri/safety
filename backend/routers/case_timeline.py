"""
Case Timeline & Task Management Router for SafeChild

Provides comprehensive case timeline tracking and task management for legal cases.
Features:
- Visual timeline of all case events
- Task creation, assignment, and tracking
- Deadline management with notifications
- Case milestones and phases
- Activity logging
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta
from enum import Enum
import uuid

from .. import get_db
from ..auth import get_current_admin, get_current_user
from ..logging_config import get_logger

router = APIRouter(prefix="/timeline", tags=["Case Timeline & Tasks"])
logger = get_logger("safechild.timeline")


# =============================================================================
# Enums and Models
# =============================================================================

class EventType(str, Enum):
    CASE_CREATED = "case_created"
    CASE_UPDATED = "case_updated"
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_SIGNED = "document_signed"
    EVIDENCE_COLLECTED = "evidence_collected"
    MEETING_SCHEDULED = "meeting_scheduled"
    MEETING_COMPLETED = "meeting_completed"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    MILESTONE_REACHED = "milestone_reached"
    COURT_DATE_SET = "court_date_set"
    MESSAGE_SENT = "message_sent"
    FORENSIC_ANALYSIS = "forensic_analysis"
    CLIENT_CONTACT = "client_contact"
    PAYMENT_RECEIVED = "payment_received"
    NOTE_ADDED = "note_added"
    STATUS_CHANGE = "status_change"
    DEADLINE_SET = "deadline_set"
    CUSTOM = "custom"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class MilestoneStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


# Request Models
class CreateEventRequest(BaseModel):
    case_id: str
    event_type: str
    title: str
    description: Optional[str] = ""
    metadata: Optional[dict] = None
    related_entity_id: Optional[str] = None
    related_entity_type: Optional[str] = None


class CreateTaskRequest(BaseModel):
    case_id: str
    title: str
    description: Optional[str] = ""
    priority: str = "medium"
    due_date: Optional[str] = None
    assigned_to: Optional[str] = None
    category: Optional[str] = None
    checklist: Optional[List[dict]] = None


class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[str] = None
    assigned_to: Optional[str] = None
    checklist: Optional[List[dict]] = None


class CreateMilestoneRequest(BaseModel):
    case_id: str
    title: str
    description: Optional[str] = ""
    target_date: Optional[str] = None
    phase: Optional[str] = None
    order: Optional[int] = 0


# =============================================================================
# Timeline Event Endpoints
# =============================================================================

@router.post("/events")
async def create_timeline_event(
    request: CreateEventRequest,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create a new timeline event"""

    event_id = f"EVT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"

    event = {
        "event_id": event_id,
        "case_id": request.case_id,
        "event_type": request.event_type,
        "title": request.title,
        "description": request.description,
        "metadata": request.metadata or {},
        "related_entity_id": request.related_entity_id,
        "related_entity_type": request.related_entity_type,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": current_user.get("email", "admin"),
        "is_automated": False
    }

    await db.timeline_events.insert_one(event)

    logger.info(f"Timeline event created: {event_id} for case {request.case_id}")
    return event


@router.get("/events/{case_id}")
async def get_case_timeline(
    case_id: str,
    event_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get timeline events for a case"""

    query = {"case_id": case_id}

    if event_type:
        query["event_type"] = event_type

    if start_date:
        query["created_at"] = {"$gte": start_date}

    if end_date:
        if "created_at" in query:
            query["created_at"]["$lte"] = end_date
        else:
            query["created_at"] = {"$lte": end_date}

    cursor = db.timeline_events.find(query).sort("created_at", -1).limit(limit)
    events = await cursor.to_list(length=limit)

    # Convert ObjectId to string
    for event in events:
        event["_id"] = str(event.get("_id", ""))

    return {"events": events, "count": len(events)}


@router.get("/events/recent")
async def get_recent_events(
    limit: int = 20,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get recent timeline events across all cases"""

    cursor = db.timeline_events.find().sort("created_at", -1).limit(limit)
    events = await cursor.to_list(length=limit)

    for event in events:
        event["_id"] = str(event.get("_id", ""))

    return {"events": events}


# =============================================================================
# Task Management Endpoints
# =============================================================================

@router.post("/tasks")
async def create_task(
    request: CreateTaskRequest,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create a new task"""

    task_id = f"TASK-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"

    task = {
        "task_id": task_id,
        "case_id": request.case_id,
        "title": request.title,
        "description": request.description,
        "priority": request.priority,
        "status": TaskStatus.PENDING.value,
        "due_date": request.due_date,
        "assigned_to": request.assigned_to,
        "category": request.category,
        "checklist": request.checklist or [],
        "created_at": datetime.utcnow().isoformat(),
        "created_by": current_user.get("email", "admin"),
        "updated_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "comments": []
    }

    await db.tasks.insert_one(task)

    # Create timeline event for task creation
    await db.timeline_events.insert_one({
        "event_id": f"EVT-{str(uuid.uuid4())[:12]}",
        "case_id": request.case_id,
        "event_type": EventType.TASK_CREATED.value,
        "title": f"Task created: {request.title}",
        "description": request.description,
        "metadata": {"task_id": task_id, "priority": request.priority},
        "related_entity_id": task_id,
        "related_entity_type": "task",
        "created_at": datetime.utcnow().isoformat(),
        "created_by": current_user.get("email", "admin"),
        "is_automated": True
    })

    logger.info(f"Task created: {task_id}")
    return task


@router.get("/tasks")
async def list_tasks(
    case_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[str] = None,
    overdue_only: bool = False,
    limit: int = 100,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List tasks with optional filters"""

    query = {}

    if case_id:
        query["case_id"] = case_id
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    if assigned_to:
        query["assigned_to"] = assigned_to
    if overdue_only:
        query["due_date"] = {"$lt": datetime.utcnow().isoformat()}
        query["status"] = {"$nin": [TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value]}

    cursor = db.tasks.find(query).sort([("priority", -1), ("due_date", 1)]).limit(limit)
    tasks = await cursor.to_list(length=limit)

    for task in tasks:
        task["_id"] = str(task.get("_id", ""))

    return {"tasks": tasks, "count": len(tasks)}


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get a specific task"""

    task = await db.tasks.find_one({"task_id": task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task["_id"] = str(task.get("_id", ""))
    return task


@router.put("/tasks/{task_id}")
async def update_task(
    task_id: str,
    request: UpdateTaskRequest,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update a task"""

    task = await db.tasks.find_one({"task_id": task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = {"updated_at": datetime.utcnow().isoformat()}

    if request.title is not None:
        update_data["title"] = request.title
    if request.description is not None:
        update_data["description"] = request.description
    if request.priority is not None:
        update_data["priority"] = request.priority
    if request.status is not None:
        update_data["status"] = request.status
        if request.status == TaskStatus.COMPLETED.value:
            update_data["completed_at"] = datetime.utcnow().isoformat()
    if request.due_date is not None:
        update_data["due_date"] = request.due_date
    if request.assigned_to is not None:
        update_data["assigned_to"] = request.assigned_to
    if request.checklist is not None:
        update_data["checklist"] = request.checklist

    await db.tasks.update_one({"task_id": task_id}, {"$set": update_data})

    # Create timeline event if status changed to completed
    if request.status == TaskStatus.COMPLETED.value:
        await db.timeline_events.insert_one({
            "event_id": f"EVT-{str(uuid.uuid4())[:12]}",
            "case_id": task["case_id"],
            "event_type": EventType.TASK_COMPLETED.value,
            "title": f"Task completed: {task['title']}",
            "description": "",
            "metadata": {"task_id": task_id},
            "related_entity_id": task_id,
            "related_entity_type": "task",
            "created_at": datetime.utcnow().isoformat(),
            "created_by": current_user.get("email", "admin"),
            "is_automated": True
        })

    updated_task = await db.tasks.find_one({"task_id": task_id})
    updated_task["_id"] = str(updated_task.get("_id", ""))

    return updated_task


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete a task"""

    result = await db.tasks.delete_one({"task_id": task_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"success": True, "task_id": task_id}


@router.post("/tasks/{task_id}/comments")
async def add_task_comment(
    task_id: str,
    content: str = Body(..., embed=True),
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Add a comment to a task"""

    comment = {
        "comment_id": str(uuid.uuid4())[:12],
        "content": content,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": current_user.get("email", "admin")
    }

    result = await db.tasks.update_one(
        {"task_id": task_id},
        {"$push": {"comments": comment}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    return comment


# =============================================================================
# Milestone Endpoints
# =============================================================================

@router.post("/milestones")
async def create_milestone(
    request: CreateMilestoneRequest,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create a case milestone"""

    milestone_id = f"MS-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"

    milestone = {
        "milestone_id": milestone_id,
        "case_id": request.case_id,
        "title": request.title,
        "description": request.description,
        "target_date": request.target_date,
        "phase": request.phase,
        "order": request.order,
        "status": MilestoneStatus.PENDING.value,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": current_user.get("email", "admin"),
        "completed_at": None
    }

    await db.milestones.insert_one(milestone)

    logger.info(f"Milestone created: {milestone_id}")
    return milestone


@router.get("/milestones/{case_id}")
async def get_case_milestones(
    case_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get milestones for a case"""

    cursor = db.milestones.find({"case_id": case_id}).sort("order", 1)
    milestones = await cursor.to_list(length=100)

    for milestone in milestones:
        milestone["_id"] = str(milestone.get("_id", ""))

    return {"milestones": milestones}


@router.put("/milestones/{milestone_id}")
async def update_milestone(
    milestone_id: str,
    status: str = Body(..., embed=True),
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update milestone status"""

    update_data = {"status": status}
    if status == MilestoneStatus.COMPLETED.value:
        update_data["completed_at"] = datetime.utcnow().isoformat()

    result = await db.milestones.update_one(
        {"milestone_id": milestone_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Milestone not found")

    # Create timeline event
    milestone = await db.milestones.find_one({"milestone_id": milestone_id})
    if milestone and status == MilestoneStatus.COMPLETED.value:
        await db.timeline_events.insert_one({
            "event_id": f"EVT-{str(uuid.uuid4())[:12]}",
            "case_id": milestone["case_id"],
            "event_type": EventType.MILESTONE_REACHED.value,
            "title": f"Milestone reached: {milestone['title']}",
            "description": milestone.get("description", ""),
            "metadata": {"milestone_id": milestone_id},
            "related_entity_id": milestone_id,
            "related_entity_type": "milestone",
            "created_at": datetime.utcnow().isoformat(),
            "created_by": current_user.get("email", "admin"),
            "is_automated": True
        })

    return {"success": True, "status": status}


# =============================================================================
# Dashboard & Statistics
# =============================================================================

@router.get("/dashboard")
async def get_timeline_dashboard(
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get dashboard statistics for timeline and tasks"""

    now = datetime.utcnow().isoformat()
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()

    # Task statistics
    total_tasks = await db.tasks.count_documents({})
    pending_tasks = await db.tasks.count_documents({"status": TaskStatus.PENDING.value})
    in_progress_tasks = await db.tasks.count_documents({"status": TaskStatus.IN_PROGRESS.value})
    completed_tasks = await db.tasks.count_documents({"status": TaskStatus.COMPLETED.value})
    overdue_tasks = await db.tasks.count_documents({
        "due_date": {"$lt": now},
        "status": {"$nin": [TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value]}
    })

    # Urgent/high priority tasks
    urgent_tasks = await db.tasks.count_documents({
        "priority": {"$in": [TaskPriority.URGENT.value, TaskPriority.HIGH.value]},
        "status": {"$nin": [TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value]}
    })

    # Recent events count
    recent_events = await db.timeline_events.count_documents({
        "created_at": {"$gte": week_ago}
    })

    # Events by type (last 7 days)
    event_pipeline = [
        {"$match": {"created_at": {"$gte": week_ago}}},
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}}
    ]
    event_types = await db.timeline_events.aggregate(event_pipeline).to_list(length=50)

    # Tasks by priority
    priority_pipeline = [
        {"$match": {"status": {"$nin": [TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value]}}},
        {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
    ]
    tasks_by_priority = await db.tasks.aggregate(priority_pipeline).to_list(length=10)

    # Upcoming deadlines (next 7 days)
    next_week = (datetime.utcnow() + timedelta(days=7)).isoformat()
    upcoming_cursor = db.tasks.find({
        "due_date": {"$gte": now, "$lte": next_week},
        "status": {"$nin": [TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value]}
    }).sort("due_date", 1).limit(10)
    upcoming_deadlines = await upcoming_cursor.to_list(length=10)

    for task in upcoming_deadlines:
        task["_id"] = str(task.get("_id", ""))

    return {
        "task_stats": {
            "total": total_tasks,
            "pending": pending_tasks,
            "in_progress": in_progress_tasks,
            "completed": completed_tasks,
            "overdue": overdue_tasks,
            "urgent": urgent_tasks
        },
        "recent_events_count": recent_events,
        "events_by_type": {e["_id"]: e["count"] for e in event_types},
        "tasks_by_priority": {p["_id"]: p["count"] for p in tasks_by_priority},
        "upcoming_deadlines": upcoming_deadlines
    }


@router.get("/case/{case_id}/summary")
async def get_case_summary(
    case_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get a comprehensive summary for a case"""

    # Get client info
    client = await db.clients.find_one({"clientNumber": case_id})

    # Get timeline events
    events_cursor = db.timeline_events.find({"case_id": case_id}).sort("created_at", -1).limit(20)
    events = await events_cursor.to_list(length=20)

    # Get tasks
    tasks_cursor = db.tasks.find({"case_id": case_id}).sort("due_date", 1)
    tasks = await tasks_cursor.to_list(length=50)

    # Get milestones
    milestones_cursor = db.milestones.find({"case_id": case_id}).sort("order", 1)
    milestones = await milestones_cursor.to_list(length=20)

    # Calculate statistics
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.get("status") == TaskStatus.COMPLETED.value)
    overdue_tasks = sum(1 for t in tasks if t.get("due_date") and t["due_date"] < datetime.utcnow().isoformat() and t.get("status") not in [TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value])

    total_milestones = len(milestones)
    completed_milestones = sum(1 for m in milestones if m.get("status") == MilestoneStatus.COMPLETED.value)

    # Convert ObjectIds
    for event in events:
        event["_id"] = str(event.get("_id", ""))
    for task in tasks:
        task["_id"] = str(task.get("_id", ""))
    for milestone in milestones:
        milestone["_id"] = str(milestone.get("_id", ""))

    return {
        "case_id": case_id,
        "client": {
            "name": client.get("fullName") if client else "Unknown",
            "status": client.get("status") if client else "unknown"
        } if client else None,
        "statistics": {
            "total_events": len(events),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "overdue_tasks": overdue_tasks,
            "task_completion_rate": round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1),
            "total_milestones": total_milestones,
            "completed_milestones": completed_milestones,
            "milestone_progress": round((completed_milestones / total_milestones * 100) if total_milestones > 0 else 0, 1)
        },
        "recent_events": events[:10],
        "pending_tasks": [t for t in tasks if t.get("status") != TaskStatus.COMPLETED.value][:10],
        "milestones": milestones
    }


# =============================================================================
# Predefined Milestone Templates
# =============================================================================

@router.get("/templates/milestones")
async def get_milestone_templates():
    """Get predefined milestone templates for common case types"""

    templates = {
        "child_custody": {
            "name": "Child Custody Case",
            "name_de": "Sorgerechtsfall",
            "milestones": [
                {"title": "Initial Consultation", "title_de": "Erstberatung", "phase": "intake", "order": 1},
                {"title": "Document Collection", "title_de": "Dokumentensammlung", "phase": "preparation", "order": 2},
                {"title": "Evidence Analysis", "title_de": "Beweisanalyse", "phase": "preparation", "order": 3},
                {"title": "Forensic Assessment", "title_de": "Forensische Bewertung", "phase": "investigation", "order": 4},
                {"title": "Mediation Attempt", "title_de": "Mediationsversuch", "phase": "negotiation", "order": 5},
                {"title": "Court Filing", "title_de": "Gerichtseinreichung", "phase": "litigation", "order": 6},
                {"title": "Court Hearing", "title_de": "Gerichtsverhandlung", "phase": "litigation", "order": 7},
                {"title": "Final Order", "title_de": "Endgultige Anordnung", "phase": "conclusion", "order": 8}
            ]
        },
        "international_custody": {
            "name": "International Custody Case",
            "name_de": "Internationaler Sorgerechtsfall",
            "milestones": [
                {"title": "Initial Consultation", "title_de": "Erstberatung", "phase": "intake", "order": 1},
                {"title": "Jurisdiction Analysis", "title_de": "Zustandigkeitsanalyse", "phase": "preparation", "order": 2},
                {"title": "International Document Collection", "title_de": "Internationale Dokumentensammlung", "phase": "preparation", "order": 3},
                {"title": "Hague Convention Assessment", "title_de": "Haager Abkommen Bewertung", "phase": "investigation", "order": 4},
                {"title": "Foreign Court Coordination", "title_de": "Auslandische Gerichtskoordination", "phase": "coordination", "order": 5},
                {"title": "Central Authority Contact", "title_de": "Kontakt mit Zentralbehorde", "phase": "coordination", "order": 6},
                {"title": "Court Filing", "title_de": "Gerichtseinreichung", "phase": "litigation", "order": 7},
                {"title": "Cross-Border Hearing", "title_de": "Grenzuberschreitende Verhandlung", "phase": "litigation", "order": 8},
                {"title": "Enforcement Order", "title_de": "Vollstreckungsanordnung", "phase": "conclusion", "order": 9}
            ]
        },
        "forensic_investigation": {
            "name": "Forensic Investigation Case",
            "name_de": "Forensischer Ermittlungsfall",
            "milestones": [
                {"title": "Case Intake", "title_de": "Fallaufnahme", "phase": "intake", "order": 1},
                {"title": "Device Collection", "title_de": "Geratesammlung", "phase": "collection", "order": 2},
                {"title": "Social Media Analysis", "title_de": "Social-Media-Analyse", "phase": "analysis", "order": 3},
                {"title": "Message Extraction", "title_de": "Nachrichtenextraktion", "phase": "analysis", "order": 4},
                {"title": "AI Risk Assessment", "title_de": "KI-Risikobewertung", "phase": "analysis", "order": 5},
                {"title": "Expert Report", "title_de": "Expertenbericht", "phase": "reporting", "order": 6},
                {"title": "Court Submission", "title_de": "Gerichtseinreichung", "phase": "conclusion", "order": 7}
            ]
        }
    }

    return {"templates": templates}


@router.post("/templates/milestones/apply")
async def apply_milestone_template(
    case_id: str = Body(..., embed=True),
    template_id: str = Body(..., embed=True),
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Apply a milestone template to a case"""

    templates = (await get_milestone_templates())["templates"]

    if template_id not in templates:
        raise HTTPException(status_code=400, detail="Invalid template ID")

    template = templates[template_id]
    created_milestones = []

    for ms in template["milestones"]:
        milestone_id = f"MS-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"

        milestone = {
            "milestone_id": milestone_id,
            "case_id": case_id,
            "title": ms["title"],
            "title_de": ms.get("title_de"),
            "description": "",
            "target_date": None,
            "phase": ms["phase"],
            "order": ms["order"],
            "status": MilestoneStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": current_user.get("email", "admin"),
            "completed_at": None,
            "from_template": template_id
        }

        await db.milestones.insert_one(milestone)
        created_milestones.append(milestone)

    # Create timeline event
    await db.timeline_events.insert_one({
        "event_id": f"EVT-{str(uuid.uuid4())[:12]}",
        "case_id": case_id,
        "event_type": EventType.CUSTOM.value,
        "title": f"Applied milestone template: {template['name']}",
        "description": f"Created {len(created_milestones)} milestones from template",
        "metadata": {"template_id": template_id, "milestone_count": len(created_milestones)},
        "related_entity_id": None,
        "related_entity_type": None,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": current_user.get("email", "admin"),
        "is_automated": True
    })

    logger.info(f"Applied template {template_id} to case {case_id}")
    return {"success": True, "milestones_created": len(created_milestones)}
