"""
Collection Scheduler
Schedules and manages automated evidence collection tasks.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from enum import Enum
from datetime import datetime, timedelta, time
import asyncio


class ScheduleFrequency(str, Enum):
    """Frequency of scheduled collections."""
    HOURLY = "hourly"
    EVERY_6_HOURS = "every_6_hours"
    EVERY_12_HOURS = "every_12_hours"
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


@dataclass
class ScheduleConfig:
    """Configuration for a scheduled collection."""
    config_id: str
    case_id: str
    frequency: ScheduleFrequency
    data_sources: List[str]  # DataSource values
    enabled: bool = True
    start_time: Optional[time] = None  # Preferred start time
    wifi_only: bool = True
    battery_threshold: int = 30  # Minimum battery %
    stealth_mode: bool = False
    max_daily_collections: int = 4
    timezone: str = "UTC"
    custom_cron: Optional[str] = None  # For CUSTOM frequency


@dataclass
class ScheduledTask:
    """A scheduled collection task."""
    task_id: str
    schedule_id: str
    case_id: str
    scheduled_for: datetime
    created_at: datetime
    status: str = "pending"  # pending, running, completed, failed, skipped
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_id: Optional[str] = None  # ID of CollectionResult
    skip_reason: Optional[str] = None


class CollectionScheduler:
    """Manages scheduled evidence collection."""

    def __init__(self):
        self.schedules: Dict[str, ScheduleConfig] = {}
        self.tasks: Dict[str, ScheduledTask] = {}
        self.task_queue: List[str] = []  # task_ids ordered by scheduled time
        self._running = False
        self._executor: Optional[Callable] = None

    def create_schedule(
        self,
        case_id: str,
        frequency: ScheduleFrequency,
        data_sources: List[str],
        start_time: Optional[time] = None,
        wifi_only: bool = True,
        battery_threshold: int = 30,
        stealth_mode: bool = False
    ) -> ScheduleConfig:
        """Create a new collection schedule."""
        config_id = f"sched_{case_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        config = ScheduleConfig(
            config_id=config_id,
            case_id=case_id,
            frequency=frequency,
            data_sources=data_sources,
            start_time=start_time,
            wifi_only=wifi_only,
            battery_threshold=battery_threshold,
            stealth_mode=stealth_mode
        )

        self.schedules[config_id] = config

        # Generate initial tasks
        self._generate_tasks(config)

        return config

    def _generate_tasks(
        self,
        config: ScheduleConfig,
        days_ahead: int = 7
    ):
        """Generate scheduled tasks for a schedule config."""
        now = datetime.utcnow()
        end_date = now + timedelta(days=days_ahead)

        current = now
        tasks_generated = 0

        while current < end_date:
            # Calculate next run time based on frequency
            next_run = self._calculate_next_run(config, current)

            if next_run and next_run < end_date:
                task_id = f"task_{config.config_id}_{next_run.strftime('%Y%m%d%H%M%S')}"

                task = ScheduledTask(
                    task_id=task_id,
                    schedule_id=config.config_id,
                    case_id=config.case_id,
                    scheduled_for=next_run,
                    created_at=now
                )

                self.tasks[task_id] = task
                self.task_queue.append(task_id)
                tasks_generated += 1

                current = next_run + timedelta(minutes=1)
            else:
                break

        # Sort queue by scheduled time
        self.task_queue.sort(
            key=lambda tid: self.tasks[tid].scheduled_for
        )

    def _calculate_next_run(
        self,
        config: ScheduleConfig,
        after: datetime
    ) -> Optional[datetime]:
        """Calculate next run time based on frequency."""
        if config.start_time:
            base = after.replace(
                hour=config.start_time.hour,
                minute=config.start_time.minute,
                second=0,
                microsecond=0
            )
            if base <= after:
                base += timedelta(days=1)
        else:
            base = after

        intervals = {
            ScheduleFrequency.HOURLY: timedelta(hours=1),
            ScheduleFrequency.EVERY_6_HOURS: timedelta(hours=6),
            ScheduleFrequency.EVERY_12_HOURS: timedelta(hours=12),
            ScheduleFrequency.DAILY: timedelta(days=1),
            ScheduleFrequency.WEEKLY: timedelta(weeks=1)
        }

        interval = intervals.get(config.frequency)
        if interval:
            # Find next run after 'after' time
            next_run = base
            while next_run <= after:
                next_run += interval
            return next_run

        return None

    def set_executor(self, executor: Callable):
        """Set the task executor function."""
        self._executor = executor

    async def run_scheduler(self):
        """Run the scheduler loop."""
        self._running = True

        while self._running:
            await self._process_due_tasks()
            await asyncio.sleep(60)  # Check every minute

    async def _process_due_tasks(self):
        """Process tasks that are due."""
        now = datetime.utcnow()

        due_tasks = [
            tid for tid in self.task_queue
            if tid in self.tasks and
            self.tasks[tid].status == "pending" and
            self.tasks[tid].scheduled_for <= now
        ]

        for task_id in due_tasks:
            task = self.tasks[task_id]
            config = self.schedules.get(task.schedule_id)

            if not config or not config.enabled:
                task.status = "skipped"
                task.skip_reason = "Schedule disabled"
                continue

            # Check conditions
            skip_reason = self._check_conditions(config)
            if skip_reason:
                task.status = "skipped"
                task.skip_reason = skip_reason
                continue

            # Execute task
            if self._executor:
                try:
                    task.status = "running"
                    task.started_at = datetime.utcnow()

                    result = await self._executor(
                        case_id=task.case_id,
                        data_sources=config.data_sources,
                        stealth_mode=config.stealth_mode
                    )

                    task.status = "completed"
                    task.completed_at = datetime.utcnow()
                    task.result_id = result.get("result_id") if result else None

                except Exception as e:
                    task.status = "failed"
                    task.completed_at = datetime.utcnow()
                    task.skip_reason = str(e)
            else:
                task.status = "skipped"
                task.skip_reason = "No executor configured"

            # Remove from queue
            if task_id in self.task_queue:
                self.task_queue.remove(task_id)

    def _check_conditions(self, config: ScheduleConfig) -> Optional[str]:
        """Check if collection conditions are met."""
        # These would be implemented with actual system checks

        # Check max daily collections
        today_tasks = [
            t for t in self.tasks.values()
            if t.schedule_id == config.config_id and
            t.status == "completed" and
            t.completed_at and
            t.completed_at.date() == datetime.utcnow().date()
        ]

        if len(today_tasks) >= config.max_daily_collections:
            return f"Max daily collections reached ({config.max_daily_collections})"

        # In production: check WiFi, battery, etc.
        # if config.wifi_only and not is_wifi_connected():
        #     return "WiFi not connected"
        # if get_battery_level() < config.battery_threshold:
        #     return f"Battery below {config.battery_threshold}%"

        return None

    def stop_scheduler(self):
        """Stop the scheduler loop."""
        self._running = False

    def get_schedule(self, config_id: str) -> Optional[ScheduleConfig]:
        """Get a schedule configuration."""
        return self.schedules.get(config_id)

    def update_schedule(
        self,
        config_id: str,
        enabled: Optional[bool] = None,
        frequency: Optional[ScheduleFrequency] = None,
        data_sources: Optional[List[str]] = None
    ) -> bool:
        """Update a schedule configuration."""
        config = self.schedules.get(config_id)
        if not config:
            return False

        if enabled is not None:
            config.enabled = enabled

        if frequency is not None:
            config.frequency = frequency
            # Regenerate tasks
            self._clear_pending_tasks(config_id)
            self._generate_tasks(config)

        if data_sources is not None:
            config.data_sources = data_sources

        return True

    def _clear_pending_tasks(self, config_id: str):
        """Clear pending tasks for a schedule."""
        pending_ids = [
            tid for tid, task in self.tasks.items()
            if task.schedule_id == config_id and task.status == "pending"
        ]

        for tid in pending_ids:
            del self.tasks[tid]
            if tid in self.task_queue:
                self.task_queue.remove(tid)

    def delete_schedule(self, config_id: str) -> bool:
        """Delete a schedule and its pending tasks."""
        if config_id not in self.schedules:
            return False

        self._clear_pending_tasks(config_id)
        del self.schedules[config_id]
        return True

    def get_upcoming_tasks(
        self,
        case_id: Optional[str] = None,
        limit: int = 10
    ) -> List[ScheduledTask]:
        """Get upcoming scheduled tasks."""
        upcoming = [
            self.tasks[tid] for tid in self.task_queue
            if tid in self.tasks and self.tasks[tid].status == "pending"
        ]

        if case_id:
            upcoming = [t for t in upcoming if t.case_id == case_id]

        return upcoming[:limit]

    def get_task_history(
        self,
        case_id: str,
        limit: int = 50
    ) -> List[ScheduledTask]:
        """Get task history for a case."""
        history = [
            t for t in self.tasks.values()
            if t.case_id == case_id and t.status in ["completed", "failed", "skipped"]
        ]

        return sorted(
            history,
            key=lambda t: t.completed_at or t.created_at,
            reverse=True
        )[:limit]

    def get_case_schedules(self, case_id: str) -> List[ScheduleConfig]:
        """Get all schedules for a case."""
        return [
            s for s in self.schedules.values()
            if s.case_id == case_id
        ]

    def get_statistics(
        self,
        case_id: Optional[str] = None,
        period_days: int = 7
    ) -> Dict[str, Any]:
        """Get scheduler statistics."""
        cutoff = datetime.utcnow() - timedelta(days=period_days)

        tasks = list(self.tasks.values())
        if case_id:
            tasks = [t for t in tasks if t.case_id == case_id]

        tasks = [t for t in tasks if t.created_at >= cutoff]

        by_status = {}
        for task in tasks:
            by_status[task.status] = by_status.get(task.status, 0) + 1

        completed = [t for t in tasks if t.status == "completed"]
        avg_duration = 0
        if completed:
            durations = [
                (t.completed_at - t.started_at).total_seconds()
                for t in completed
                if t.completed_at and t.started_at
            ]
            if durations:
                avg_duration = sum(durations) / len(durations)

        return {
            "total_tasks": len(tasks),
            "by_status": by_status,
            "success_rate": len(completed) / len(tasks) if tasks else 0,
            "avg_duration_seconds": avg_duration,
            "active_schedules": len([s for s in self.schedules.values() if s.enabled]),
            "pending_tasks": len([t for t in self.task_queue if t in self.tasks])
        }
