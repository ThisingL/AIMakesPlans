"""
Data models and schemas using Pydantic.
Defines Task, Event, UserPreference, and related structures.
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Literal
from datetime import datetime, time
from enum import Enum


class Priority(str, Enum):
    """Task priority levels (P0=highest, P3=lowest)."""
    P0 = "P0"  # Critical/Urgent
    P1 = "P1"  # High
    P2 = "P2"  # Medium
    P3 = "P3"  # Low


class TaskType(str, Enum):
    """Task type: fixed (specific time) or flexible (can be scheduled)."""
    FIXED = "fixed"
    FLEXIBLE = "flexible"


class TaskStatus(str, Enum):
    """Task completion status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PriorityPolicy(str, Enum):
    """Priority sorting policy."""
    EISENHOWER = "eisenhower"  # Urgent-Important Matrix
    FIFO = "fifo"  # First In First Out


class UserStatusType(str, Enum):
    """User current status."""
    BUSY = "busy"
    IDLE = "idle"


class Task(BaseModel):
    """
    Task model: represents a work item.
    - fixed: has specific startTime and endTime
    - flexible: has estimatedDuration and optional deadline
    """
    id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=2000, description="Detailed description")
    type: TaskType = Field(TaskType.FLEXIBLE, description="Task type: fixed or flexible")
    
    # Time-related fields
    estimatedDuration: Optional[int] = Field(None, gt=0, description="Estimated duration in minutes (for flexible tasks)")
    startTime: Optional[datetime] = Field(None, description="Start time (for fixed tasks)")
    endTime: Optional[datetime] = Field(None, description="End time (for fixed tasks)")
    deadline: Optional[datetime] = Field(None, description="Deadline (for flexible tasks)")
    
    # Additional fields
    priority: Priority = Field(Priority.P2, description="Task priority")
    status: TaskStatus = Field(TaskStatus.PENDING, description="Task status")
    location: Optional[str] = Field(None, max_length=200, description="Location")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    
    @field_validator('endTime')
    @classmethod
    def validate_end_time(cls, v, info):
        """Validate that endTime is after startTime."""
        if v is not None and info.data.get('startTime') is not None:
            if v <= info.data['startTime']:
                raise ValueError('endTime must be after startTime')
        return v
    
    @model_validator(mode='after')
    def validate_task_type_fields(self):
        """Validate that task has required fields based on type."""
        if self.type == TaskType.FIXED:
            if self.startTime is None or self.endTime is None:
                raise ValueError('Fixed tasks must have startTime and endTime')
        elif self.type == TaskType.FLEXIBLE:
            if self.estimatedDuration is None:
                raise ValueError('Flexible tasks must have estimatedDuration')
        return self


class Event(BaseModel):
    """
    Event model: represents a calendar event (similar to Task but simpler).
    Always has specific start and end times.
    """
    id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    startTime: datetime
    endTime: datetime
    location: Optional[str] = Field(None, max_length=200)
    
    @field_validator('endTime')
    @classmethod
    def validate_end_time(cls, v, info):
        """Validate that endTime is after startTime."""
        if v <= info.data['startTime']:
            raise ValueError('endTime must be after startTime')
        return v


class TimeSlot(BaseModel):
    """Represents a time slot (used for working hours, no-disturb slots)."""
    start: time = Field(..., description="Start time (HH:MM)")
    end: time = Field(..., description="End time (HH:MM)")
    
    @field_validator('end')
    @classmethod
    def validate_end_time(cls, v, info):
        """Validate that end is after start."""
        if v <= info.data['start']:
            raise ValueError('end time must be after start time')
        return v


class UserPreference(BaseModel):
    """
    User preferences for scheduling.
    Defines working hours, focus duration, buffer times, etc.
    """
    workingHours: List[TimeSlot] = Field(
        default_factory=lambda: [TimeSlot(start=time(9, 0), end=time(18, 0))],
        description="Working hours per day"
    )
    noDisturbSlots: List[TimeSlot] = Field(
        default_factory=list,
        description="Time slots to avoid scheduling (lunch, break, etc.)"
    )
    maxFocusDuration: int = Field(
        120,
        gt=0,
        le=480,
        description="Maximum continuous focus time in minutes"
    )
    minBlockUnit: int = Field(
        30,
        gt=0,
        le=120,
        description="Minimum scheduling block unit in minutes"
    )
    bufferBetweenEvents: int = Field(
        15,
        ge=0,
        le=60,
        description="Buffer time between events in minutes"
    )


class UserStatus(BaseModel):
    """User's current status."""
    status: UserStatusType = Field(UserStatusType.IDLE, description="Current status: busy or idle")
    restMode: bool = Field(False, description="Whether in rest mode (avoid scheduling new tasks)")
    currentActivity: Optional[str] = Field(None, description="Current activity description")


class Conflict(BaseModel):
    """Represents a scheduling conflict."""
    taskId: str
    conflictWith: str  # ID of conflicting event/task
    reason: str
    startTime: datetime
    endTime: datetime


class ScheduledTask(BaseModel):
    """A task with assigned time slot."""
    task: Task
    scheduledStart: datetime
    scheduledEnd: datetime
    reason: Optional[str] = Field(None, description="Reason for this scheduling decision")


class SchedulePlan(BaseModel):
    """
    Output of scheduling algorithm.
    Contains scheduled tasks, conflicts, and explanations.
    """
    scheduledTasks: List[ScheduledTask] = Field(default_factory=list)
    conflicts: List[Conflict] = Field(default_factory=list)
    unscheduledTasks: List[Task] = Field(default_factory=list, description="Tasks that couldn't be scheduled")
    explanation: Optional[str] = Field(None, description="Overall explanation of the plan")


# API Request/Response Models

class ParseRequest(BaseModel):
    """Request model for /v1/parse endpoint."""
    text: str = Field(..., min_length=1, max_length=1000, description="Natural language text to parse")
    preference: Optional[UserPreference] = Field(None, description="User preferences (optional)")


class ParseResponse(BaseModel):
    """Response model for /v1/parse endpoint."""
    task: Task
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Parsing confidence score")


class CreateTaskRequest(BaseModel):
    """Request model for creating a task."""
    task: Task


class CreateTaskResponse(BaseModel):
    """Response model for creating a task."""
    id: str
    task: Task
    message: str = "Task created successfully"


class SchedulePlanRequest(BaseModel):
    """Request model for /v1/schedule/plan endpoint."""
    tasks: List[Task] = Field(..., description="Tasks to schedule")
    existingEvents: List[Event] = Field(default_factory=list, description="Existing calendar events")
    preference: Optional[UserPreference] = Field(None, description="User preferences")
    userStatus: Optional[UserStatus] = Field(None, description="User status")


class HealthResponse(BaseModel):
    """Response model for /health endpoint."""
    status: str = "ok"
    timestamp: Optional[datetime] = None
    version: str = "0.1.0"
