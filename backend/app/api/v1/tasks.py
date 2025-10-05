"""
Tasks API endpoints.
Handles task creation, retrieval, update, and deletion.
"""
from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime
import uuid

from backend.app.models.schemas import (
    Task,
    CreateTaskRequest,
    CreateTaskResponse,
    TaskType,
    Priority,
    TaskStatus
)

router = APIRouter(prefix="/tasks")

# In-memory storage for MVP (will be replaced with database)
tasks_db: dict[str, Task] = {}


@router.post("", response_model=CreateTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(request: CreateTaskRequest) -> CreateTaskResponse:
    """
    Create a new task.
    
    For MVP, this is a placeholder that stores tasks in memory.
    """
    task = request.task
    
    # Generate ID if not provided
    if task.id is None:
        task.id = str(uuid.uuid4())
    
    # Check if task with this ID already exists
    if task.id in tasks_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Task with ID {task.id} already exists"
        )
    
    # Store task
    tasks_db[task.id] = task
    
    return CreateTaskResponse(
        id=task.id,
        task=task,
        message="Task created successfully"
    )


@router.get("", response_model=List[Task])
async def list_tasks() -> List[Task]:
    """
    List all tasks.
    
    Returns all tasks from in-memory storage.
    """
    return list(tasks_db.values())


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str) -> Task:
    """
    Get a specific task by ID.
    """
    if task_id not in tasks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    return tasks_db[task_id]


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str):
    """
    Delete a task by ID.
    """
    if task_id not in tasks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    del tasks_db[task_id]
    return None

