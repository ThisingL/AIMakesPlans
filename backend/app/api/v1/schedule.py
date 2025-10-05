"""
Schedule API endpoints.
Handles scheduling and planning of tasks.
"""
from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timedelta

from backend.app.models.schemas import (
    SchedulePlanRequest,
    SchedulePlan,
    ScheduledTask,
    Conflict,
    UserPreference,
    UserStatus
)

router = APIRouter(prefix="/schedule")


@router.post("/plan", response_model=SchedulePlan)
async def plan_schedule(request: SchedulePlanRequest) -> SchedulePlan:
    """
    Create a schedule plan for given tasks.
    
    Takes into account:
    - Existing events
    - User preferences (working hours, buffer times, etc.)
    - User status (busy/idle, rest mode)
    - Task priorities and deadlines
    
    For MVP, this is a placeholder that returns a mock plan.
    Will be replaced with actual scheduling algorithm.
    """
    tasks = request.tasks
    existing_events = request.existingEvents
    preference = request.preference or UserPreference()
    user_status = request.userStatus or UserStatus()
    
    # Placeholder scheduling logic
    # For now, just return an empty plan with explanation
    
    scheduled_tasks = []
    conflicts = []
    unscheduled_tasks = list(tasks)
    
    # Simple placeholder: try to schedule first task
    if tasks:
        first_task = tasks[0]
        if first_task.type.value == "flexible" and first_task.estimatedDuration:
            # Schedule for next available slot (tomorrow 9 AM for demo)
            scheduled_start = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
            scheduled_end = scheduled_start + timedelta(minutes=first_task.estimatedDuration)
            
            scheduled_tasks.append(ScheduledTask(
                task=first_task,
                scheduledStart=scheduled_start,
                scheduledEnd=scheduled_end,
                reason="Scheduled to first available slot in working hours"
            ))
            unscheduled_tasks = tasks[1:]
    
    explanation = (
        f"Scheduled {len(scheduled_tasks)} tasks, "
        f"found {len(conflicts)} conflicts, "
        f"{len(unscheduled_tasks)} tasks remain unscheduled. "
        "This is a placeholder response - actual scheduling algorithm will be implemented."
    )
    
    return SchedulePlan(
        scheduledTasks=scheduled_tasks,
        conflicts=conflicts,
        unscheduledTasks=unscheduled_tasks,
        explanation=explanation
    )

