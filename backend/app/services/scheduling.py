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
        
        # 检查是否需要拆分任务
        # 如果任务时长超过最大专注时长，拆分成多个子任务
        should_split = task.estimatedDuration > preference.maxFocusDuration
        
        # 先计算时间段限制（这个逻辑需要提前，供拆分任务使用）
        task_deadline = task.deadline if task.deadline else end_search
        
        search_start = start_search
        time_slot_start = None
        time_slot_end = None
        
        if task.deadline:
            deadline_hour = task_deadline.hour
            deadline_minute = task_deadline.minute
            
            # 判断是否是特定时间段的限制
            if deadline_hour == 18 and deadline_minute == 0:
                time_slot_start = task_deadline.replace(hour=12, minute=0, second=0, microsecond=0)
                time_slot_end = task_deadline
            elif deadline_hour == 12 and deadline_minute == 0:
                time_slot_start = task_deadline.replace(hour=9, minute=0, second=0, microsecond=0)
                time_slot_end = task_deadline
            elif deadline_hour == 23 and deadline_minute == 0:
                time_slot_start = task_deadline.replace(hour=18, minute=0, second=0, microsecond=0)
                time_slot_end = task_deadline
            elif deadline_hour == 23 and deadline_minute == 59:
                time_slot_start = task_deadline.replace(hour=9, minute=0, second=0, microsecond=0)
                time_slot_end = task_deadline.replace(hour=18, minute=0, second=0, microsecond=0)
            
            if time_slot_start and time_slot_start < datetime.now():
                time_slot_start = datetime.now()
        
        if should_split:
            # 拆分任务
            remaining_duration = task.estimatedDuration
            part_number = 1
            total_parts = (task.estimatedDuration + preference.maxFocusDuration - 1) // preference.maxFocusDuration
            
            split_success = True
            temp_scheduled = []  # 临时存储拆分任务，如果失败则丢弃
            
            while remaining_duration > 0:
                # 每个子任务的时长
                part_duration = min(remaining_duration, preference.maxFocusDuration)
                
                # 创建子任务
                part_task = Task(
                    id=f"{task.id}_part{part_number}" if task.id else None,
                    title=f"{task.title}（第{part_number}部分，共{total_parts}部分）",
                    description=task.description,
                    type=task.type,
                    estimatedDuration=part_duration,
                    deadline=task.deadline,
                    priority=task.priority,
                    status=task.status,
                    location=task.location,
                    tags=task.tags + [f"拆分任务{part_number}/{total_parts}"]
                )
                
                # 为子任务分配时间（继承原任务的时间段限制）
                assigned = _assign_single_task(
                    part_task,
                    free_slots,
                    task_deadline,
                    preference,
                    policy,
                    temp_scheduled,  # 使用临时列表
                    search_start,
                    time_slot_start,  # 传递时间段限制！
                    time_slot_end     # 传递时间段限制！
                )
                
                if not assigned:
                    # 如果某个子任务无法分配，整个拆分失败
                    split_success = False
                    break
                
                remaining_duration -= part_duration
                part_number += 1
            
            if split_success:
                # 拆分成功，将所有子任务添加到结果
                scheduled_tasks.extend(temp_scheduled)
            else:
                # 拆分失败，标记为未调度
                unscheduled_tasks.append(task)
            
            continue  # 跳过下面的单任务处理逻辑
        
        # 为单个任务分配时间（时间段限制已在上面计算过了）
        assigned = _assign_single_task(
            task,
            free_slots,
            task_deadline,
            preference,
            policy,
            scheduled_tasks,
            search_start,
            time_slot_start,
            time_slot_end
        )
        
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


def _assign_single_task(
    task: Task,
    free_slots: List[FreeSlot],
    task_deadline: datetime,
    preference: UserPreference,
    policy: str,
    scheduled_tasks: List[ScheduledTask],
    search_start: datetime,
    time_slot_start: Optional[datetime] = None,
    time_slot_end: Optional[datetime] = None
) -> bool:
    """
    为单个任务分配时间
    
    Returns:
        True if 分配成功
    """
    # 寻找合适的空闲槽
    for slot in free_slots:
        # 检查是否在截止时间前
        if slot.end > task_deadline:
            continue
        
        # 如果有时间段限制（如"下午"），检查是否在指定时间段内
        if time_slot_start and time_slot_end:
            # slot必须在指定时间段内
            if slot.start < time_slot_start or slot.end > time_slot_end:
                continue
        else:
            # 没有特定时间段限制，只要不在过去即可
            if slot.start < search_start:
                continue
        
        # 检查时长是否足够
        if slot.duration_minutes >= task.estimatedDuration:
            # 分配这个槽
            scheduled_start = slot.start
            scheduled_end = scheduled_start + timedelta(minutes=task.estimatedDuration)
            
            # 最后检查：确保结束时间不超过deadline
            if scheduled_end <= task_deadline:
                scheduled_tasks.append(ScheduledTask(
                    task=task,
                    scheduledStart=scheduled_start,
                    scheduledEnd=scheduled_end,
                    reason=f"根据{policy}策略分配到空闲时段，在截止时间前完成"
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
                
                return True
    
    return False

