"""
Unit tests for conflict detection service.
Tests various scenarios of time overlap and conflict detection.
"""
import pytest
from datetime import datetime, timedelta

from backend.app.services.conflicts import (
    overlap,
    check_task_overlap,
    find_conflicts,
    find_all_conflicts,
    has_conflict
)
from backend.app.models.schemas import Task, Event, TaskType, Priority


class TestOverlapFunction:
    """Tests for the overlap() function"""
    
    def test_overlap_basic(self):
        """Test basic overlap scenario"""
        # 10:00-11:00 和 10:30-11:30 重叠
        a_start = datetime(2025, 10, 5, 10, 0)
        a_end = datetime(2025, 10, 5, 11, 0)
        b_start = datetime(2025, 10, 5, 10, 30)
        b_end = datetime(2025, 10, 5, 11, 30)
        
        assert overlap(a_start, a_end, b_start, b_end) is True
    
    def test_overlap_complete(self):
        """Test complete overlap (one contains the other)"""
        # 10:00-12:00 完全包含 10:30-11:00
        a_start = datetime(2025, 10, 5, 10, 0)
        a_end = datetime(2025, 10, 5, 12, 0)
        b_start = datetime(2025, 10, 5, 10, 30)
        b_end = datetime(2025, 10, 5, 11, 0)
        
        assert overlap(a_start, a_end, b_start, b_end) is True
    
    def test_no_overlap_separate(self):
        """Test no overlap - completely separate"""
        # 10:00-11:00 和 12:00-13:00 不重叠
        a_start = datetime(2025, 10, 5, 10, 0)
        a_end = datetime(2025, 10, 5, 11, 0)
        b_start = datetime(2025, 10, 5, 12, 0)
        b_end = datetime(2025, 10, 5, 13, 0)
        
        assert overlap(a_start, a_end, b_start, b_end) is False
    
    def test_no_overlap_adjacent(self):
        """Test no overlap - adjacent times (touching boundaries)"""
        # 10:00-11:00 和 11:00-12:00 边界相接，不算重叠
        a_start = datetime(2025, 10, 5, 10, 0)
        a_end = datetime(2025, 10, 5, 11, 0)
        b_start = datetime(2025, 10, 5, 11, 0)
        b_end = datetime(2025, 10, 5, 12, 0)
        
        assert overlap(a_start, a_end, b_start, b_end) is False
    
    def test_overlap_cross_day(self):
        """Test overlap across days"""
        # 23:00-01:00 和 00:00-02:00 重叠
        a_start = datetime(2025, 10, 5, 23, 0)
        a_end = datetime(2025, 10, 6, 1, 0)
        b_start = datetime(2025, 10, 6, 0, 0)
        b_end = datetime(2025, 10, 6, 2, 0)
        
        assert overlap(a_start, a_end, b_start, b_end) is True
    
    def test_overlap_same_start(self):
        """Test overlap with same start time"""
        # 10:00-11:00 和 10:00-11:30 重叠
        a_start = datetime(2025, 10, 5, 10, 0)
        a_end = datetime(2025, 10, 5, 11, 0)
        b_start = datetime(2025, 10, 5, 10, 0)
        b_end = datetime(2025, 10, 5, 11, 30)
        
        assert overlap(a_start, a_end, b_start, b_end) is True
    
    def test_overlap_same_end(self):
        """Test overlap with same end time"""
        # 10:00-12:00 和 11:00-12:00 重叠
        a_start = datetime(2025, 10, 5, 10, 0)
        a_end = datetime(2025, 10, 5, 12, 0)
        b_start = datetime(2025, 10, 5, 11, 0)
        b_end = datetime(2025, 10, 5, 12, 0)
        
        assert overlap(a_start, a_end, b_start, b_end) is True


class TestCheckTaskOverlap:
    """Tests for check_task_overlap() function"""
    
    def test_fixed_task_overlaps_event(self):
        """Test fixed task overlapping with event"""
        task = Task(
            title="Meeting",
            type=TaskType.FIXED,
            startTime=datetime(2025, 10, 5, 10, 0),
            endTime=datetime(2025, 10, 5, 11, 0),
            priority=Priority.P1
        )
        
        event = Event(
            title="Conference",
            startTime=datetime(2025, 10, 5, 10, 30),
            endTime=datetime(2025, 10, 5, 11, 30)
        )
        
        assert check_task_overlap(task, event) is True
    
    def test_fixed_task_no_overlap_event(self):
        """Test fixed task not overlapping with event"""
        task = Task(
            title="Meeting",
            type=TaskType.FIXED,
            startTime=datetime(2025, 10, 5, 10, 0),
            endTime=datetime(2025, 10, 5, 11, 0),
            priority=Priority.P1
        )
        
        event = Event(
            title="Conference",
            startTime=datetime(2025, 10, 5, 12, 0),
            endTime=datetime(2025, 10, 5, 13, 0)
        )
        
        assert check_task_overlap(task, event) is False
    
    def test_flexible_task_no_overlap(self):
        """Test flexible task doesn't check for overlap"""
        task = Task(
            title="Work",
            type=TaskType.FLEXIBLE,
            estimatedDuration=60,
            priority=Priority.P2
        )
        
        event = Event(
            title="Meeting",
            startTime=datetime(2025, 10, 5, 10, 0),
            endTime=datetime(2025, 10, 5, 11, 0)
        )
        
        # Flexible tasks don't have fixed time, so no overlap check
        assert check_task_overlap(task, event) is False


class TestFindConflicts:
    """Tests for find_conflicts() function"""
    
    def test_find_conflicts_with_events(self):
        """Test finding conflicts between task and events"""
        task = Task(
            id="task1",
            title="Meeting A",
            type=TaskType.FIXED,
            startTime=datetime(2025, 10, 5, 10, 0),
            endTime=datetime(2025, 10, 5, 11, 0),
            priority=Priority.P1
        )
        
        events = [
            Event(
                id="event1",
                title="Meeting B",
                startTime=datetime(2025, 10, 5, 10, 30),
                endTime=datetime(2025, 10, 5, 11, 30)
            ),
            Event(
                id="event2",
                title="Meeting C",
                startTime=datetime(2025, 10, 5, 12, 0),
                endTime=datetime(2025, 10, 5, 13, 0)
            )
        ]
        
        conflicts = find_conflicts(task, events)
        
        assert len(conflicts) == 1
        assert conflicts[0].taskId == "task1"
        assert conflicts[0].conflictWith == "event1"
    
    def test_find_conflicts_with_tasks(self):
        """Test finding conflicts between tasks"""
        task1 = Task(
            id="task1",
            title="Meeting A",
            type=TaskType.FIXED,
            startTime=datetime(2025, 10, 5, 10, 0),
            endTime=datetime(2025, 10, 5, 11, 0),
            priority=Priority.P1
        )
        
        task2 = Task(
            id="task2",
            title="Meeting B",
            type=TaskType.FIXED,
            startTime=datetime(2025, 10, 5, 10, 30),
            endTime=datetime(2025, 10, 5, 11, 30),
            priority=Priority.P1
        )
        
        conflicts = find_conflicts(task1, [], [task2])
        
        assert len(conflicts) == 1
        assert conflicts[0].conflictWith == "task2"
    
    def test_no_conflicts(self):
        """Test no conflicts found"""
        task = Task(
            id="task1",
            title="Meeting",
            type=TaskType.FIXED,
            startTime=datetime(2025, 10, 5, 10, 0),
            endTime=datetime(2025, 10, 5, 11, 0),
            priority=Priority.P1
        )
        
        events = [
            Event(
                id="event1",
                title="Other Meeting",
                startTime=datetime(2025, 10, 5, 12, 0),
                endTime=datetime(2025, 10, 5, 13, 0)
            )
        ]
        
        conflicts = find_conflicts(task, events)
        
        assert len(conflicts) == 0
    
    def test_flexible_task_no_conflicts(self):
        """Test flexible task returns no conflicts"""
        task = Task(
            id="task1",
            title="Work",
            type=TaskType.FLEXIBLE,
            estimatedDuration=60,
            priority=Priority.P2
        )
        
        events = [
            Event(
                id="event1",
                title="Meeting",
                startTime=datetime(2025, 10, 5, 10, 0),
                endTime=datetime(2025, 10, 5, 11, 0)
            )
        ]
        
        conflicts = find_conflicts(task, events)
        
        # Flexible tasks don't have conflicts until scheduled
        assert len(conflicts) == 0


class TestHasConflict:
    """Tests for has_conflict() function"""
    
    def test_has_conflict_with_event(self):
        """Test detecting conflict with events"""
        events = [
            Event(
                title="Meeting",
                startTime=datetime(2025, 10, 5, 10, 0),
                endTime=datetime(2025, 10, 5, 11, 0)
            )
        ]
        
        # Check time that overlaps
        result = has_conflict(
            datetime(2025, 10, 5, 10, 30),
            datetime(2025, 10, 5, 11, 30),
            events
        )
        
        assert result is True
    
    def test_no_conflict_with_event(self):
        """Test no conflict with events"""
        events = [
            Event(
                title="Meeting",
                startTime=datetime(2025, 10, 5, 10, 0),
                endTime=datetime(2025, 10, 5, 11, 0)
            )
        ]
        
        # Check time that doesn't overlap
        result = has_conflict(
            datetime(2025, 10, 5, 12, 0),
            datetime(2025, 10, 5, 13, 0),
            events
        )
        
        assert result is False
    
    def test_has_conflict_with_task(self):
        """Test detecting conflict with tasks"""
        tasks = [
            Task(
                title="Work",
                type=TaskType.FIXED,
                startTime=datetime(2025, 10, 5, 14, 0),
                endTime=datetime(2025, 10, 5, 15, 0),
                priority=Priority.P2
            )
        ]
        
        result = has_conflict(
            datetime(2025, 10, 5, 14, 30),
            datetime(2025, 10, 5, 15, 30),
            [],
            tasks
        )
        
        assert result is True

