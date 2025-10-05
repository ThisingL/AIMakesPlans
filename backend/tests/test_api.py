"""
Integration tests for API endpoints.
Tests basic functionality of all API routes.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from backend.app.main import app
from backend.app.models.schemas import (
    Task,
    TaskType,
    Priority,
    TaskStatus,
    UserPreference,
    Event
)

client = TestClient(app)


class TestHealthEndpoint:
    """Tests for /health endpoint."""
    
    def test_health_check(self):
        """Test that health check returns 200 and correct structure."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
        assert data["version"] == "0.1.0"
    
    def test_health_check_status_field(self):
        """Test that status field is 'ok'."""
        response = client.get("/health")
        assert response.json()["status"] == "ok"


class TestRootEndpoint:
    """Tests for root endpoint."""
    
    def test_root(self):
        """Test root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["version"] == "0.1.0"


class TestTasksEndpoint:
    """Tests for /v1/tasks endpoint."""
    
    def test_create_task(self):
        """Test creating a new task."""
        task_data = {
            "task": {
                "title": "Test Task",
                "description": "This is a test task",
                "type": "flexible",
                "estimatedDuration": 60,
                "priority": "P2",
                "status": "pending"
            }
        }
        
        response = client.post("/v1/tasks", json=task_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert data["task"]["title"] == "Test Task"
        assert data["message"] == "Task created successfully"
    
    def test_create_fixed_task(self):
        """Test creating a fixed task with start and end times."""
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        task_data = {
            "task": {
                "title": "Fixed Meeting",
                "type": "fixed",
                "startTime": start_time.isoformat(),
                "endTime": end_time.isoformat(),
                "priority": "P1"
            }
        }
        
        response = client.post("/v1/tasks", json=task_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["task"]["type"] == "fixed"
        assert "startTime" in data["task"]
        assert "endTime" in data["task"]
    
    def test_list_tasks(self):
        """Test listing all tasks."""
        response = client.get("/v1/tasks")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_task(self):
        """Test getting a specific task."""
        # First create a task
        task_data = {
            "task": {
                "title": "Get Test Task",
                "type": "flexible",
                "estimatedDuration": 30,
                "priority": "P3"
            }
        }
        create_response = client.post("/v1/tasks", json=task_data)
        task_id = create_response.json()["id"]
        
        # Now get it
        response = client.get(f"/v1/tasks/{task_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == "Get Test Task"
    
    def test_get_nonexistent_task(self):
        """Test getting a task that doesn't exist."""
        response = client.get("/v1/tasks/nonexistent-id")
        assert response.status_code == 404
    
    def test_delete_task(self):
        """Test deleting a task."""
        # First create a task
        task_data = {
            "task": {
                "title": "Delete Test Task",
                "type": "flexible",
                "estimatedDuration": 45,
                "priority": "P2"
            }
        }
        create_response = client.post("/v1/tasks", json=task_data)
        task_id = create_response.json()["id"]
        
        # Delete it
        delete_response = client.delete(f"/v1/tasks/{task_id}")
        assert delete_response.status_code == 204
        
        # Verify it's gone
        get_response = client.get(f"/v1/tasks/{task_id}")
        assert get_response.status_code == 404


class TestParseEndpoint:
    """Tests for /v1/parse endpoint."""
    
    def test_parse_simple_text(self):
        """Test parsing simple text."""
        parse_data = {
            "text": "明天下午做2小时报告"
        }
        
        response = client.post("/v1/parse", json=parse_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "task" in data
        assert "confidence" in data
        assert data["task"]["title"] is not None
        assert data["task"]["type"] == "flexible"
    
    def test_parse_with_preference(self):
        """Test parsing with user preference."""
        parse_data = {
            "text": "写周报",
            "preference": {
                "maxFocusDuration": 90,
                "minBlockUnit": 30
            }
        }
        
        response = client.post("/v1/parse", json=parse_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "task" in data
    
    def test_parse_empty_text(self):
        """Test parsing empty text returns error."""
        parse_data = {
            "text": ""
        }
        
        response = client.post("/v1/parse", json=parse_data)
        # Pydantic validation returns 422 (Unprocessable Entity) for validation errors
        assert response.status_code == 422


class TestScheduleEndpoint:
    """Tests for /v1/schedule/plan endpoint."""
    
    def test_plan_schedule_empty(self):
        """Test planning with no tasks."""
        plan_data = {
            "tasks": [],
            "existingEvents": []
        }
        
        response = client.post("/v1/schedule/plan", json=plan_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "scheduledTasks" in data
        assert "conflicts" in data
        assert "explanation" in data
    
    def test_plan_schedule_with_tasks(self):
        """Test planning with tasks."""
        plan_data = {
            "tasks": [
                {
                    "title": "Task 1",
                    "type": "flexible",
                    "estimatedDuration": 60,
                    "priority": "P1"
                },
                {
                    "title": "Task 2",
                    "type": "flexible",
                    "estimatedDuration": 120,
                    "priority": "P2"
                }
            ],
            "existingEvents": []
        }
        
        response = client.post("/v1/schedule/plan", json=plan_data)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data["scheduledTasks"], list)
        assert isinstance(data["conflicts"], list)
        assert isinstance(data["unscheduledTasks"], list)
    
    def test_plan_schedule_with_events(self):
        """Test planning with existing events."""
        start_time = datetime.now() + timedelta(hours=2)
        end_time = start_time + timedelta(hours=1)
        
        plan_data = {
            "tasks": [
                {
                    "title": "Task 1",
                    "type": "flexible",
                    "estimatedDuration": 60,
                    "priority": "P1"
                }
            ],
            "existingEvents": [
                {
                    "title": "Meeting",
                    "startTime": start_time.isoformat(),
                    "endTime": end_time.isoformat()
                }
            ],
            "preference": {
                "maxFocusDuration": 120,
                "bufferBetweenEvents": 15
            }
        }
        
        response = client.post("/v1/schedule/plan", json=plan_data)
        assert response.status_code == 200

