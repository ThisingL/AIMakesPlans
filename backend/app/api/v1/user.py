"""
User API endpoints.
Handles user preferences and status management.
"""
from fastapi import APIRouter, HTTPException, status

from backend.app.models.schemas import (
    UserPreference,
    UserStatus,
    UserStatusType
)

router = APIRouter(prefix="/user")

# In-memory storage for MVP (single user)
_user_preference: UserPreference = UserPreference()
_user_status: UserStatus = UserStatus()


@router.get("/preferences", response_model=UserPreference)
async def get_preferences() -> UserPreference:
    """
    Get user preferences.
    
    Returns current user preferences including:
    - Working hours
    - No-disturb time slots
    - Focus duration limits
    - Buffer times
    - Priority policy
    
    For MVP, this returns a single global preference.
    In production, this would be user-specific.
    """
    return _user_preference


@router.put("/preferences", response_model=UserPreference)
async def update_preferences(preference: UserPreference) -> UserPreference:
    """
    Update user preferences.
    
    Allows users to customize their scheduling preferences:
    - Working hours (e.g., 9:00-18:00)
    - No-disturb slots (e.g., lunch 12:00-13:00)
    - Maximum focus duration (in minutes)
    - Minimum block unit (in minutes)
    - Buffer time between events (in minutes)
    
    All subsequent scheduling operations will use these preferences.
    
    Example request:
    ```json
    {
        "workingHours": [
            {"start": "09:00", "end": "12:00"},
            {"start": "14:00", "end": "18:00"}
        ],
        "noDisturbSlots": [
            {"start": "12:00", "end": "13:00"}
        ],
        "maxFocusDuration": 90,
        "minBlockUnit": 30,
        "bufferBetweenEvents": 15
    }
    ```
    """
    global _user_preference
    _user_preference = preference
    return _user_preference


@router.get("/status", response_model=UserStatus)
async def get_status() -> UserStatus:
    """
    Get user current status.
    
    Returns:
    - Current state (busy/idle)
    - Rest mode status
    - Current activity description
    
    This information affects scheduling behavior:
    - busy: Delays new task scheduling
    - restMode: Prevents automatic scheduling
    """
    return _user_status


@router.put("/status", response_model=UserStatus)
async def update_status(user_status: UserStatus) -> UserStatus:
    """
    Update user status.
    
    Allows users to set their current state:
    - status: "busy" or "idle"
    - restMode: true/false (休息模式)
    - currentActivity: description of what you're doing
    
    When restMode is enabled:
    - No automatic task scheduling
    - Only manual scheduling allowed
    - Existing tasks remain unchanged
    
    Example request:
    ```json
    {
        "status": "busy",
        "restMode": false,
        "currentActivity": "In a meeting"
    }
    ```
    """
    global _user_status
    _user_status = user_status
    return _user_status


@router.post("/status/toggle-rest", response_model=UserStatus)
async def toggle_rest_mode() -> UserStatus:
    """
    Toggle rest mode on/off.
    
    Convenience endpoint to quickly enable/disable rest mode
    without changing other status fields.
    
    Returns the updated status.
    """
    global _user_status
    _user_status.restMode = not _user_status.restMode
    return _user_status

