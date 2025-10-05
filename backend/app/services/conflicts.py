"""
Conflict Detection Service - 冲突检测服务
提供时间重叠检测和冲突发现功能
"""
from typing import List, Tuple, Optional
from datetime import datetime

from backend.app.models.schemas import Task, Event, Conflict


def overlap(
    start_a: datetime,
    end_a: datetime,
    start_b: datetime,
    end_b: datetime
) -> bool:
    """
    检测两个时间段是否重叠
    
    重叠条件：start_new < end_exist && end_new > start_exist
    
    Args:
        start_a: 时间段A的开始时间
        end_a: 时间段A的结束时间
        start_b: 时间段B的开始时间
        end_b: 时间段B的结束时间
        
    Returns:
        True if 重叠, False if 不重叠
        
    Examples:
        >>> overlap(
        ...     datetime(2025, 10, 5, 10, 0),
        ...     datetime(2025, 10, 5, 11, 0),
        ...     datetime(2025, 10, 5, 10, 30),
        ...     datetime(2025, 10, 5, 11, 30)
        ... )
        True
        
        >>> # 边界相接不算重叠
        >>> overlap(
        ...     datetime(2025, 10, 5, 10, 0),
        ...     datetime(2025, 10, 5, 11, 0),
        ...     datetime(2025, 10, 5, 11, 0),
        ...     datetime(2025, 10, 5, 12, 0)
        ... )
        False
    """
    # 标准的区间重叠检测算法
    return start_a < end_b and end_a > start_b


def check_task_overlap(task: Task, event: Event) -> bool:
    """
    检查任务和事件是否时间重叠
    
    Args:
        task: 任务对象（必须是固定任务，有startTime和endTime）
        event: 事件对象
        
    Returns:
        True if 重叠
    """
    if task.type.value != "fixed":
        return False
    
    if not task.startTime or not task.endTime:
        return False
    
    return overlap(task.startTime, task.endTime, event.startTime, event.endTime)


def find_conflicts(
    task: Task,
    existing_events: List[Event],
    existing_tasks: Optional[List[Task]] = None
) -> List[Conflict]:
    """
    查找给定任务与现有事件/任务的所有冲突
    
    Args:
        task: 要检查的任务（必须是固定任务）
        existing_events: 现有的事件列表
        existing_tasks: 现有的任务列表（可选）
        
    Returns:
        冲突列表
    """
    conflicts = []
    
    # 只检查固定任务
    if task.type.value != "fixed" or not task.startTime or not task.endTime:
        return conflicts
    
    # 检查与事件的冲突
    for event in existing_events:
        if overlap(task.startTime, task.endTime, event.startTime, event.endTime):
            conflict = Conflict(
                taskId=task.id or "new_task",
                conflictWith=event.id or f"event_{event.title}",
                reason=f"时间与事件 '{event.title}' 重叠",
                startTime=max(task.startTime, event.startTime),
                endTime=min(task.endTime, event.endTime)
            )
            conflicts.append(conflict)
    
    # 检查与其他任务的冲突
    if existing_tasks:
        for other_task in existing_tasks:
            # 跳过自己
            if task.id and other_task.id and task.id == other_task.id:
                continue
            
            # 只检查固定任务
            if other_task.type.value != "fixed":
                continue
            
            if not other_task.startTime or not other_task.endTime:
                continue
            
            if overlap(task.startTime, task.endTime, 
                      other_task.startTime, other_task.endTime):
                conflict = Conflict(
                    taskId=task.id or "new_task",
                    conflictWith=other_task.id or f"task_{other_task.title}",
                    reason=f"时间与任务 '{other_task.title}' 重叠",
                    startTime=max(task.startTime, other_task.startTime),
                    endTime=min(task.endTime, other_task.endTime)
                )
                conflicts.append(conflict)
    
    return conflicts


def find_all_conflicts(
    tasks: List[Task],
    events: List[Event]
) -> List[Conflict]:
    """
    查找所有任务之间以及任务与事件之间的冲突
    
    Args:
        tasks: 任务列表
        events: 事件列表
        
    Returns:
        所有冲突的列表
    """
    all_conflicts = []
    
    for i, task in enumerate(tasks):
        # 检查与事件的冲突
        conflicts_with_events = find_conflicts(task, events, None)
        all_conflicts.extend(conflicts_with_events)
        
        # 检查与其他任务的冲突
        other_tasks = tasks[i+1:]  # 只检查后面的任务，避免重复
        conflicts_with_tasks = find_conflicts(task, [], other_tasks)
        all_conflicts.extend(conflicts_with_tasks)
    
    return all_conflicts


def has_conflict(
    start: datetime,
    end: datetime,
    events: List[Event],
    tasks: Optional[List[Task]] = None
) -> bool:
    """
    检查给定时间段是否与现有事件/任务冲突
    
    Args:
        start: 开始时间
        end: 结束时间
        events: 现有事件列表
        tasks: 现有任务列表（可选）
        
    Returns:
        True if 有冲突
    """
    # 检查与事件的冲突
    for event in events:
        if overlap(start, end, event.startTime, event.endTime):
            return True
    
    # 检查与任务的冲突
    if tasks:
        for task in tasks:
            if task.type.value != "fixed":
                continue
            if not task.startTime or not task.endTime:
                continue
            if overlap(start, end, task.startTime, task.endTime):
                return True
    
    return False

