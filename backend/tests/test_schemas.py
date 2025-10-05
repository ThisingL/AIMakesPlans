"""
Unit tests for Pydantic schemas and data models.
Tests validation, constraints, and edge cases.
"""
import pytest
from datetime import datetime, time, timedelta
from pydantic import ValidationError

from backend.app.models.schemas import (
    Task,
    Event,
    TimeSlot,
    UserPreference,
    UserStatus,
    Priority,
    TaskType,
    TaskStatus,
    UserStatusType,
    SchedulePlan,
    Conflict,
    ScheduledTask
)


class TestPriorityEnum:
    """Tests for Priority enum."""
    
    def test_all_priority_levels(self):
        """Test all priority levels exist."""
        assert Priority.P0 == "P0"
        assert Priority.P1 == "P1"
        assert Priority.P2 == "P2"
        assert Priority.P3 == "P3"


class TestTaskModel:
    """Tests for Task model validation."""
    
    def test_create_flexible_task(self):
        """Test creating a valid flexible task."""
        task = Task(
            title="Test Task",
            type=TaskType.FLEXIBLE,
            estimatedDuration=60,
            priority=Priority.P2
        )
        assert task.title == "Test Task"
        assert task.type == TaskType.FLEXIBLE
        assert task.estimatedDuration == 60
    
    def test_create_fixed_task(self):
        """Test creating a valid fixed task."""
        start = datetime.now()
        end = start + timedelta(hours=2)
        
        task = Task(
            title="Meeting",
            type=TaskType.FIXED,
            startTime=start,
            endTime=end,
            priority=Priority.P1
        )
        assert task.type == TaskType.FIXED
        assert task.startTime == start
        assert task.endTime == end
    
    def test_flexible_task_requires_duration(self):
        """Test that flexible tasks require estimatedDuration."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                title="Invalid Task",
                type=TaskType.FLEXIBLE,
                # Missing estimatedDuration
                priority=Priority.P2
            )
        
        assert "Flexible tasks must have estimatedDuration" in str(exc_info.value)
    
    def test_fixed_task_requires_times(self):
        """Test that fixed tasks require start and end times."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                title="Invalid Meeting",
                type=TaskType.FIXED,
                # Missing startTime and endTime
                priority=Priority.P1
            )
        
        assert "Fixed tasks must have startTime and endTime" in str(exc_info.value)
    
    def test_end_time_must_be_after_start(self):
        """Test that endTime must be after startTime."""
        start = datetime.now()
        end = start - timedelta(hours=1)  # Invalid: end before start
        
        with pytest.raises(ValidationError) as exc_info:
            Task(
                title="Invalid Task",
                type=TaskType.FIXED,
                startTime=start,
                endTime=end
            )
        
        assert "endTime must be after startTime" in str(exc_info.value)
    
    def test_title_required(self):
        """Test that title is required."""
        with pytest.raises(ValidationError):
            Task(
                type=TaskType.FLEXIBLE,
                estimatedDuration=60
            )
    
    def test_title_length_constraints(self):
        """Test title length constraints."""
        # Empty title
        with pytest.raises(ValidationError):
            Task(
                title="",
                type=TaskType.FLEXIBLE,
                estimatedDuration=60
            )
        
        # Too long title (> 200 chars)
        with pytest.raises(ValidationError):
            Task(
                title="x" * 201,
                type=TaskType.FLEXIBLE,
                estimatedDuration=60
            )
    
    def test_default_values(self):
        """Test default values for optional fields."""
        task = Task(
            title="Test",
            type=TaskType.FLEXIBLE,
            estimatedDuration=60
        )
        assert task.priority == Priority.P2
        assert task.status == TaskStatus.PENDING
        assert task.tags == []
        assert task.description is None


class TestEventModel:
    """Tests for Event model validation."""
    
    def test_create_valid_event(self):
        """Test creating a valid event."""
        start = datetime.now()
        end = start + timedelta(hours=1)
        
        event = Event(
            title="Team Meeting",
            startTime=start,
            endTime=end,
            location="Room 101"
        )
        assert event.title == "Team Meeting"
        assert event.startTime == start
        assert event.endTime == end
        assert event.location == "Room 101"
    
    def test_event_end_after_start(self):
        """Test that event endTime must be after startTime."""
        start = datetime.now()
        end = start - timedelta(hours=1)
        
        with pytest.raises(ValidationError) as exc_info:
            Event(
                title="Invalid Event",
                startTime=start,
                endTime=end
            )
        
        assert "endTime must be after startTime" in str(exc_info.value)


class TestTimeSlotModel:
    """Tests for TimeSlot model validation."""
    
    def test_create_valid_timeslot(self):
        """Test creating a valid time slot."""
        slot = TimeSlot(start=time(9, 0), end=time(17, 0))
        assert slot.start == time(9, 0)
        assert slot.end == time(17, 0)
    
    def test_end_must_be_after_start(self):
        """Test that end time must be after start time."""
        with pytest.raises(ValidationError) as exc_info:
            TimeSlot(start=time(17, 0), end=time(9, 0))
        
        assert "end time must be after start time" in str(exc_info.value)
    
    def test_same_start_and_end_invalid(self):
        """Test that start and end cannot be the same."""
        with pytest.raises(ValidationError):
            TimeSlot(start=time(9, 0), end=time(9, 0))


class TestUserPreferenceModel:
    """Tests for UserPreference model validation."""
    
    def test_default_preferences(self):
        """Test default user preferences."""
        pref = UserPreference()
        assert len(pref.workingHours) == 1
        assert pref.workingHours[0].start == time(9, 0)
        assert pref.workingHours[0].end == time(18, 0)
        assert pref.maxFocusDuration == 120
        assert pref.minBlockUnit == 30
        assert pref.bufferBetweenEvents == 15
    
    def test_custom_preferences(self):
        """Test creating custom preferences."""
        pref = UserPreference(
            workingHours=[
                TimeSlot(start=time(8, 0), end=time(12, 0)),
                TimeSlot(start=time(13, 0), end=time(17, 0))
            ],
            noDisturbSlots=[
                TimeSlot(start=time(12, 0), end=time(13, 0))
            ],
            maxFocusDuration=90,
            minBlockUnit=15,
            bufferBetweenEvents=10
        )
        assert len(pref.workingHours) == 2
        assert len(pref.noDisturbSlots) == 1
        assert pref.maxFocusDuration == 90
    
    def test_max_focus_duration_constraints(self):
        """Test maxFocusDuration constraints."""
        # Must be positive
        with pytest.raises(ValidationError):
            UserPreference(maxFocusDuration=0)
        
        # Must be <= 480 (8 hours)
        with pytest.raises(ValidationError):
            UserPreference(maxFocusDuration=500)
    
    def test_min_block_unit_constraints(self):
        """Test minBlockUnit constraints."""
        # Must be positive
        with pytest.raises(ValidationError):
            UserPreference(minBlockUnit=0)
        
        # Must be <= 120
        with pytest.raises(ValidationError):
            UserPreference(minBlockUnit=130)


class TestUserStatusModel:
    """Tests for UserStatus model validation."""
    
    def test_default_status(self):
        """Test default user status."""
        status = UserStatus()
        assert status.status == UserStatusType.IDLE
        assert status.restMode is False
        assert status.currentActivity is None
    
    def test_busy_status(self):
        """Test busy status with activity."""
        status = UserStatus(
            status=UserStatusType.BUSY,
            restMode=False,
            currentActivity="In a meeting"
        )
        assert status.status == UserStatusType.BUSY
        assert status.currentActivity == "In a meeting"
    
    def test_rest_mode(self):
        """Test rest mode."""
        status = UserStatus(
            status=UserStatusType.IDLE,
            restMode=True
        )
        assert status.restMode is True


class TestSchedulePlanModel:
    """Tests for SchedulePlan model validation."""
    
    def test_empty_schedule_plan(self):
        """Test creating an empty schedule plan."""
        plan = SchedulePlan()
        assert plan.scheduledTasks == []
        assert plan.conflicts == []
        assert plan.unscheduledTasks == []
        assert plan.explanation is None
    
    def test_schedule_plan_with_data(self):
        """Test creating a schedule plan with data."""
        task = Task(
            title="Task 1",
            type=TaskType.FLEXIBLE,
            estimatedDuration=60
        )
        
        scheduled_start = datetime.now()
        scheduled_end = scheduled_start + timedelta(hours=1)
        
        scheduled_task = ScheduledTask(
            task=task,
            scheduledStart=scheduled_start,
            scheduledEnd=scheduled_end,
            reason="First available slot"
        )
        
        plan = SchedulePlan(
            scheduledTasks=[scheduled_task],
            conflicts=[],
            unscheduledTasks=[],
            explanation="Successfully scheduled all tasks"
        )
        
        assert len(plan.scheduledTasks) == 1
        assert plan.scheduledTasks[0].task.title == "Task 1"
        assert plan.explanation == "Successfully scheduled all tasks"

