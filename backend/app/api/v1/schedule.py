"""
Schedule API endpoints.
Handles scheduling and planning of tasks.
"""
from fastapi import APIRouter, HTTPException, status

from backend.app.models.schemas import (
    SchedulePlanRequest,
    SchedulePlan,
    UserPreference,
    UserStatus
)
from backend.app.services.scheduling import schedule_tasks

router = APIRouter(prefix="/schedule")


@router.post("/plan", response_model=SchedulePlan)
async def plan_schedule(request: SchedulePlanRequest) -> SchedulePlan:
    """
    Create a schedule plan for given tasks using intelligent scheduling algorithm.
    
    This endpoint analyzes tasks, existing events, and user preferences to create
    an optimal schedule that:
    - Detects and reports conflicts
    - Respects working hours and no-disturb slots
    - Considers task priorities and deadlines
    - Applies buffer times between events
    - Handles user status (busy/rest mode)
    
    Args:
        request: SchedulePlanRequest containing:
            - tasks: List of tasks to schedule
            - existingEvents: Current calendar events
            - preference: User scheduling preferences (optional)
            - userStatus: User current status (optional)
    
    Returns:
        SchedulePlan with:
            - scheduledTasks: Successfully scheduled tasks with assigned time slots
            - conflicts: Detected scheduling conflicts
            - unscheduledTasks: Tasks that couldn't be scheduled
            - explanation: Human-readable explanation of the plan
    
    Examples:
        Request:
        ```json
        {
            "tasks": [
                {
                    "title": "写代码",
                    "type": "flexible",
                    "estimatedDuration": 120,
                    "priority": "P1"
                }
            ],
            "existingEvents": [],
            "preference": {
                "workingHours": [{"start": "09:00", "end": "18:00"}],
                "bufferBetweenEvents": 15
            }
        }
        ```
    """
    try:
        # 获取参数，使用默认值
        tasks = request.tasks
        existing_events = request.existingEvents
        preference = request.preference or UserPreference()
        user_status = request.userStatus or UserStatus()
        
        # 调用调度算法
        plan = schedule_tasks(
            tasks=tasks,
            events=existing_events,
            preference=preference,
            user_status=user_status,
            search_days=7  # 搜索未来7天的空闲时间
        )
        
        return plan
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scheduling error: {str(e)}"
        )
