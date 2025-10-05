"""
Parse API endpoints.
Handles natural language text parsing into structured tasks.
"""
from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timedelta

from backend.app.models.schemas import (
    ParseRequest,
    ParseResponse,
    Task,
    TaskType,
    Priority,
    TaskStatus
)

router = APIRouter(prefix="/parse")


@router.post("", response_model=ParseResponse)
async def parse_text(request: ParseRequest) -> ParseResponse:
    """
    Parse natural language text into a structured task.
    
    For MVP, this is a placeholder that returns a mock task.
    Will be replaced with actual LLM integration.
    
    Example input: "明天下午做2小时报告"
    """
    text = request.text.strip()
    
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text cannot be empty"
        )
    
    # Placeholder parsing logic (will be replaced with LLM service)
    # For now, create a flexible task with some default values
    task = Task(
        title=text[:50] if len(text) > 50 else text,  # Use first 50 chars as title
        description=f"Parsed from: {text}",
        type=TaskType.FLEXIBLE,
        estimatedDuration=120,  # Default 2 hours
        deadline=datetime.now() + timedelta(days=1),  # Tomorrow
        priority=Priority.P2,
        status=TaskStatus.PENDING
    )
    
    return ParseResponse(
        task=task,
        confidence=0.8  # Placeholder confidence
    )

