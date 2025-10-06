"""
Tests for user preferences and status API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import time

from backend.app.main import app
from backend.app.models.schemas import UserPreference, UserStatus, UserStatusType, TimeSlot

client = TestClient(app)


class TestUserPreferencesAPI:
    """Tests for /v1/user/preferences endpoints"""
    
    def test_get_default_preferences(self):
        """Test getting default user preferences"""
        response = client.get("/v1/user/preferences")
        assert response.status_code == 200
        
        data = response.json()
        assert "workingHours" in data
        assert "maxFocusDuration" in data
        assert data["maxFocusDuration"] == 120
        assert data["minBlockUnit"] == 30
        assert data["bufferBetweenEvents"] == 15
    
    def test_update_preferences(self):
        """Test updating user preferences"""
        new_preferences = {
            "workingHours": [
                {"start": "08:00", "end": "12:00"},
                {"start": "14:00", "end": "18:00"}
            ],
            "noDisturbSlots": [
                {"start": "12:00", "end": "13:00"}
            ],
            "maxFocusDuration": 90,
            "minBlockUnit": 15,
            "bufferBetweenEvents": 10
        }
        
        response = client.put("/v1/user/preferences", json=new_preferences)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["workingHours"]) == 2
        assert data["maxFocusDuration"] == 90
        assert data["minBlockUnit"] == 15
    
    def test_get_updated_preferences(self):
        """Test that preferences persist after update"""
        # Update first
        new_preferences = {
            "workingHours": [{"start": "10:00", "end": "16:00"}],
            "maxFocusDuration": 60,
            "minBlockUnit": 20,
            "bufferBetweenEvents": 5
        }
        client.put("/v1/user/preferences", json=new_preferences)
        
        # Get and verify
        response = client.get("/v1/user/preferences")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["workingHours"]) == 1
        assert data["workingHours"][0]["start"] == "10:00:00"
        assert data["maxFocusDuration"] == 60


class TestUserStatusAPI:
    """Tests for /v1/user/status endpoints"""
    
    def test_get_default_status(self):
        """Test getting default user status"""
        response = client.get("/v1/user/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "restMode" in data
        assert data["status"] == "idle"
        assert data["restMode"] is False
    
    def test_update_status(self):
        """Test updating user status"""
        new_status = {
            "status": "busy",
            "restMode": True,
            "currentActivity": "In a meeting"
        }
        
        response = client.put("/v1/user/status", json=new_status)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "busy"
        assert data["restMode"] is True
        assert data["currentActivity"] == "In a meeting"
    
    def test_toggle_rest_mode(self):
        """Test toggling rest mode"""
        # Set initial state
        client.put("/v1/user/status", json={
            "status": "idle",
            "restMode": False
        })
        
        # Toggle on
        response = client.post("/v1/user/status/toggle-rest")
        assert response.status_code == 200
        assert response.json()["restMode"] is True
        
        # Toggle off
        response = client.post("/v1/user/status/toggle-rest")
        assert response.status_code == 200
        assert response.json()["restMode"] is False
    
    def test_status_persists(self):
        """Test that status persists across requests"""
        # Update
        new_status = {
            "status": "busy",
            "restMode": True,
            "currentActivity": "Working"
        }
        client.put("/v1/user/status", json=new_status)
        
        # Get and verify
        response = client.get("/v1/user/status")
        data = response.json()
        assert data["status"] == "busy"
        assert data["restMode"] is True
        assert data["currentActivity"] == "Working"


class TestPreferencesValidation:
    """Tests for preferences validation"""
    
    def test_invalid_max_focus_duration(self):
        """Test validation of maxFocusDuration"""
        invalid_pref = {
            "workingHours": [{"start": "09:00", "end": "18:00"}],
            "maxFocusDuration": 500,  # > 480, should fail
            "minBlockUnit": 30,
            "bufferBetweenEvents": 15
        }
        
        response = client.put("/v1/user/preferences", json=invalid_pref)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_time_slot(self):
        """Test validation of time slots"""
        invalid_pref = {
            "workingHours": [
                {"start": "18:00", "end": "09:00"}  # End before start
            ],
            "maxFocusDuration": 120,
            "minBlockUnit": 30,
            "bufferBetweenEvents": 15
        }
        
        response = client.put("/v1/user/preferences", json=invalid_pref)
        assert response.status_code == 422

