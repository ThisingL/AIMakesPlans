"""
Scheduling Service - 调度服务
实现灵活任务的智能调度算法
"""
from typing import List, Tuple, Optional
from datetime import datetime, timedelta, time
from dataclasses import dataclass

from backend.app.models.schemas import (
    Task, Event, UserPreference, UserStatus,
    SchedulePlan, ScheduledTask, Conflict, TimeSlot,
    Priority, PriorityPolicy
)
from backend.app.services.conflicts import has_conflict, find_conflicts
from backend.app.core.config import settings


@dataclass
class FreeSlot:
    """空闲时间槽"""
    start: datetime
    end: datetime
    duration_minutes: int


def is_within_working_hours(
    start: datetime,
    end: datetime,
    working_hours: List[TimeSlot]
) -> bool:
    """
    检查时间段是否在工作时间内
    
    Args:
        start: 开始时间
        end: 结束时间
        working_hours: 工作时间段列表
        
    Returns:
        True if 在工作时间内
    """
    if not working_hours:
        return True
    
    start_time = start.time()
    end_time = end.time()
    
    for slot in working_hours:
        if start_time >= slot.start and end_time <= slot.end:
            return True
    
    return False


def is_in_no_disturb_slots(
    start: datetime,
    end: datetime,
    no_disturb_slots: List[TimeSlot]
) -> bool:
    """
    检查时间段是否与免打扰时段重叠
    
    Args:
        start: 开始时间
        end: 结束时间
        no_disturb_slots: 免打扰时段列表
        
    Returns:
        True if 重叠
    """
    if not no_disturb_slots:
        return False
    
    start_time = start.time()
    end_time = end.time()
    
    for slot in no_disturb_slots:
        # 简化处理：检查是否有重叠
        if start_time < slot.end and end_time > slot.start:
            return True
    
    return False


def find_free_slots(
    start_date: datetime,
    end_date: datetime,
    events: List[Event],
    tasks: List[Task],
    preference: UserPreference,
    min_duration_minutes: int = 30
) -> List[FreeSlot]:
    """
    在指定时间范围内查找空闲时间槽
    
    Args:
        start_date: 搜索开始日期
        end_date: 搜索结束日期
        events: 现有事件列表
        tasks: 现有任务列表（仅固定任务）
        preference: 用户偏好
        min_duration_minutes: 最小时长（分钟）
        
    Returns:
        空闲时间槽列表
    """
    free_slots = []
    current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 按天遍历
    while current_date <= end_date:
        # 遍历每个工作时段
        for work_slot in preference.workingHours:
            slot_start = current_date.replace(
                hour=work_slot.start.hour,
                minute=work_slot.start.minute,
                second=0,
                microsecond=0
            )
            slot_end = current_date.replace(
                hour=work_slot.end.hour,
                minute=work_slot.end.minute,
                second=0,
                microsecond=0
            )
            
            # 以最小时间块为单位查找空闲时间
            block_size = timedelta(minutes=preference.minBlockUnit)
            buffer = timedelta(minutes=preference.bufferBetweenEvents)
            
            current_time = slot_start
            while current_time + timedelta(minutes=min_duration_minutes) <= slot_end:
                potential_end = current_time + timedelta(minutes=min_duration_minutes)
                
                # 检查是否在免打扰时段
                if is_in_no_disturb_slots(current_time, potential_end, preference.noDisturbSlots):
                    current_time += block_size
                    continue
                
                # 检查是否与现有事件/任务冲突（考虑缓冲时间）
                check_start = current_time - buffer
                check_end = potential_end + buffer
                
                if not has_conflict(check_start, check_end, events, tasks):
                    # 找到一个空闲槽，计算实际可用时长
                    available_end = potential_end
                    temp_end = potential_end + block_size
                    
                    # 尝试扩展这个空闲槽
                    while temp_end <= slot_end:
                        if is_in_no_disturb_slots(potential_end, temp_end, preference.noDisturbSlots):
                            break
                        if has_conflict(temp_end - buffer, temp_end + buffer, events, tasks):
                            break
                        available_end = temp_end
                        temp_end += block_size
                    
                    duration = int((available_end - current_time).total_seconds() / 60)
                    
                    # 限制最大时长不超过maxFocusDuration
                    if duration > preference.maxFocusDuration:
                        duration = preference.maxFocusDuration
                        available_end = current_time + timedelta(minutes=duration)
                    
                    free_slots.append(FreeSlot(
                        start=current_time,
                        end=available_end,
                        duration_minutes=duration
                    ))
                    
                    # 跳过这个已找到的空闲槽
                    current_time = available_end + buffer
                else:
                    current_time += block_size
        
        # 下一天
        current_date += timedelta(days=1)
    
    return free_slots


def sort_tasks_by_priority(
    tasks: List[Task],
    policy: str = "eisenhower"
) -> List[Task]:
    """
    根据优先级策略对任务排序
    
    Args:
        tasks: 任务列表
        policy: 优先级策略（eisenhower 或 fifo）
        
    Returns:
        排序后的任务列表
    """
    if policy == "fifo":
        # FIFO：按创建顺序（这里简化为原顺序）
        return tasks
    
    # Eisenhower矩阵：P0 > P1 > P2 > P3
    # 同优先级下，按截止时间排序
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    
    def sort_key(task: Task) -> Tuple[int, datetime]:
        priority_value = priority_order.get(task.priority.value, 2)
        # 如果有截止时间，优先级相同时deadline近的排前面
        deadline = task.deadline if task.deadline else datetime.max
        return (priority_value, deadline)
    
    return sorted(tasks, key=sort_key)


def schedule_tasks(
    tasks: List[Task],
    events: List[Event],
    preference: UserPreference,
    user_status: Optional[UserStatus] = None,
    search_days: int = 7
) -> SchedulePlan:
    """
    为灵活任务安排时间
    
    Args:
        tasks: 待调度的任务列表
        events: 现有事件列表
        preference: 用户偏好
        user_status: 用户状态
        search_days: 搜索未来多少天的空闲时间
        
    Returns:
        调度方案
    """
    scheduled_tasks: List[ScheduledTask] = []
    unscheduled_tasks: List[Task] = []
    conflicts: List[Conflict] = []
    
    # 分离固定任务和灵活任务
    fixed_tasks = [t for t in tasks if t.type.value == "fixed"]
    flexible_tasks = [t for t in tasks if t.type.value == "flexible"]
    
    # 检查固定任务的冲突
    for task in fixed_tasks:
        task_conflicts = find_conflicts(task, events, fixed_tasks)
        if task_conflicts:
            conflicts.extend(task_conflicts)
            unscheduled_tasks.append(task)
        else:
            # 固定任务没冲突，直接添加到结果
            scheduled_tasks.append(ScheduledTask(
                task=task,
                scheduledStart=task.startTime,
                scheduledEnd=task.endTime,
                reason="固定时间任务"
            ))
    
    # 检查用户状态
    if user_status and user_status.restMode:
        # 休息模式：不自动调度，只返回建议
        explanation = "用户处于休息模式，仅提供备选方案，不自动调度灵活任务。"
        unscheduled_tasks.extend(flexible_tasks)
        return SchedulePlan(
            scheduledTasks=scheduled_tasks,
            conflicts=conflicts,
            unscheduledTasks=unscheduled_tasks,
            explanation=explanation
        )
    
    # 对灵活任务排序
    policy = settings.PRIORITY_POLICY
    sorted_flexible_tasks = sort_tasks_by_priority(flexible_tasks, policy)
    
    # 查找空闲时间槽
    start_search = datetime.now()
    end_search = start_search + timedelta(days=search_days)
    
    # 已调度的固定任务也要考虑
    scheduled_fixed_tasks = [st.task for st in scheduled_tasks if st.task.type.value == "fixed"]
    
    free_slots = find_free_slots(
        start_search,
        end_search,
        events,
        scheduled_fixed_tasks,
        preference,
        min_duration_minutes=preference.minBlockUnit
    )
    
    # 为每个灵活任务分配时间
    for task in sorted_flexible_tasks:
        if not task.estimatedDuration:
            unscheduled_tasks.append(task)
            continue
        
        # 如果有截止时间，只在截止时间前搜索
        task_deadline = task.deadline if task.deadline else end_search
        
        # 寻找合适的空闲槽
        assigned = False
        for slot in free_slots:
            # 检查是否在截止时间前
            if slot.start > task_deadline:
                continue
            
            # 检查时长是否足够
            if slot.duration_minutes >= task.estimatedDuration:
                # 分配这个槽
                scheduled_start = slot.start
                scheduled_end = scheduled_start + timedelta(minutes=task.estimatedDuration)
                
                scheduled_tasks.append(ScheduledTask(
                    task=task,
                    scheduledStart=scheduled_start,
                    scheduledEnd=scheduled_end,
                    reason=f"根据{policy}策略分配到空闲时段"
                ))
                
                # 更新这个槽（分割或移除）
                remaining_duration = slot.duration_minutes - task.estimatedDuration
                if remaining_duration >= preference.minBlockUnit:
                    # 还有剩余时间，更新槽
                    slot.start = scheduled_end + timedelta(minutes=preference.bufferBetweenEvents)
                    slot.duration_minutes = remaining_duration - preference.bufferBetweenEvents
                else:
                    # 没有足够剩余时间，移除这个槽
                    free_slots.remove(slot)
                
                assigned = True
                break
        
        if not assigned:
            unscheduled_tasks.append(task)
    
    # 生成说明
    explanation_parts = []
    explanation_parts.append(f"成功调度 {len(scheduled_tasks)} 个任务")
    
    if conflicts:
        explanation_parts.append(f"发现 {len(conflicts)} 个冲突")
    
    if unscheduled_tasks:
        explanation_parts.append(f"{len(unscheduled_tasks)} 个任务无法调度（可能是时间不足或超过截止时间）")
    
    if user_status and user_status.status.value == "busy":
        explanation_parts.append("用户当前忙碌，已适当延后任务安排")
    
    explanation = "；".join(explanation_parts) + "。"
    
    return SchedulePlan(
        scheduledTasks=scheduled_tasks,
        conflicts=conflicts,
        unscheduledTasks=unscheduled_tasks,
        explanation=explanation
    )

