// ==================== 配置 ====================
const API_BASE_URL = 'http://127.0.0.1:8000';

// ==================== 全局状态 ====================
let currentTask = null;
let allTasks = [];
let selectedDate = new Date();
let currentMonth = new Date();

// ==================== 工具函数 ====================

/**
 * 显示Toast通知
 */
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.className = 'toast';
    }, 3000);
}

/**
 * 显示/隐藏加载动画
 */
function setLoading(isLoading) {
    const overlay = document.getElementById('loading-overlay');
    overlay.style.display = isLoading ? 'flex' : 'none';
}

/**
 * 格式化日期时间
 */
function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * 格式化日期（仅日期部分）
 */
function formatDate(date) {
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}

/**
 * 格式化时间（仅时间部分）
 */
function formatTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * 格式化时长（分钟转小时）
 */
function formatDuration(minutes) {
    if (!minutes) return '-';
    if (minutes < 60) return `${minutes}分钟`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}小时${mins}分钟` : `${hours}小时`;
}

/**
 * 判断是否是同一天
 */
function isSameDay(date1, date2) {
    return date1.getFullYear() === date2.getFullYear() &&
           date1.getMonth() === date2.getMonth() &&
           date1.getDate() === date2.getDate();
}

/**
 * 获取日期的任务数量
 */
function getTaskCountForDate(date) {
    return allTasks.filter(task => {
        if (task.type === 'fixed' && task.startTime) {
            return isSameDay(new Date(task.startTime), date);
        }
        if (task.type === 'flexible' && task.deadline) {
            return isSameDay(new Date(task.deadline), date);
        }
        return false;
    }).length;
}

// ==================== API 调用 ====================

/**
 * 检查API健康状态
 */
async function checkAPIHealth() {
    const statusEl = document.getElementById('api-status');
    
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'ok') {
            statusEl.textContent = '✓ API连接正常';
            statusEl.className = 'status-indicator online';
            return true;
        }
    } catch (error) {
        statusEl.textContent = '✗ API连接失败';
        statusEl.className = 'status-indicator offline';
        console.error('API健康检查失败:', error);
        return false;
    }
}

/**
 * 解析自然语言任务
 */
async function parseTask(text) {
    try {
        setLoading(true);
        
        const response = await fetch(`${API_BASE_URL}/v1/parse`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '解析失败');
        }
        
        const data = await response.json();
        return data;
        
    } catch (error) {
        console.error('解析任务失败:', error);
        throw error;
    } finally {
        setLoading(false);
    }
}

/**
 * 保存任务到后端
 */
async function saveTask(task) {
    try {
        const response = await fetch(`${API_BASE_URL}/v1/tasks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ task })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '保存失败');
        }
        
        const data = await response.json();
        return data;
        
    } catch (error) {
        console.error('保存任务失败:', error);
        throw error;
    }
}

/**
 * 获取所有任务
 */
async function fetchAllTasks() {
    try {
        const response = await fetch(`${API_BASE_URL}/v1/tasks`);
        
        if (!response.ok) {
            throw new Error('获取任务失败');
        }
        
        const tasks = await response.json();
        return tasks;
        
    } catch (error) {
        console.error('获取任务失败:', error);
        return [];
    }
}

/**
 * 删除任务
 */
async function deleteTask(taskId) {
    try {
        const response = await fetch(`${API_BASE_URL}/v1/tasks/${taskId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('删除失败');
        }
        
        return true;
        
    } catch (error) {
        console.error('删除任务失败:', error);
        throw error;
    }
}

// ==================== UI 渲染 ====================

/**
 * 渲染日历
 */
function renderCalendar() {
    const calendar = document.getElementById('calendar');
    calendar.innerHTML = '';
    
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    
    // 日历头部
    const header = document.createElement('div');
    header.className = 'calendar-header';
    header.innerHTML = `
        <div class="calendar-nav">
            <button id="prev-month">◀</button>
            <span class="calendar-month">${year}年${month + 1}月</span>
            <button id="next-month">▶</button>
        </div>
    `;
    calendar.appendChild(header);
    
    // 星期标签
    const weekDays = ['日', '一', '二', '三', '四', '五', '六'];
    weekDays.forEach(day => {
        const dayEl = document.createElement('div');
        dayEl.className = 'calendar-day-header';
        dayEl.textContent = day;
        dayEl.style.textAlign = 'center';
        dayEl.style.fontWeight = '600';
        dayEl.style.fontSize = '0.9rem';
        dayEl.style.color = 'var(--text-secondary)';
        dayEl.style.padding = '8px';
        calendar.appendChild(dayEl);
    });
    
    // 获取本月第一天和最后一天
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const firstDayOfWeek = firstDay.getDay();
    const daysInMonth = lastDay.getDate();
    
    // 填充空白日期（月初）
    for (let i = 0; i < firstDayOfWeek; i++) {
        const emptyDay = document.createElement('div');
        emptyDay.className = 'calendar-day empty';
        calendar.appendChild(emptyDay);
    }
    
    // 填充日期
    const today = new Date();
    for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(year, month, day);
        const dayEl = document.createElement('div');
        dayEl.className = 'calendar-day';
        
        // 标记今天
        if (isSameDay(date, today)) {
            dayEl.classList.add('today');
        }
        
        // 标记选中日期
        if (isSameDay(date, selectedDate)) {
            dayEl.classList.add('selected');
        }
        
        // 检查是否有任务
        if (getTaskCountForDate(date) > 0) {
            dayEl.classList.add('has-tasks');
        }
        
        dayEl.innerHTML = `
            <span class="day-number">${day}</span>
        `;
        
        // 点击事件
        dayEl.addEventListener('click', () => {
            selectedDate = date;
            renderCalendar();
            renderDailySchedule(date);
        });
        
        calendar.appendChild(dayEl);
    }
    
    // 绑定月份导航事件
    document.getElementById('prev-month').addEventListener('click', () => {
        currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1);
        renderCalendar();
    });
    
    document.getElementById('next-month').addEventListener('click', () => {
        currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1);
        renderCalendar();
    });
}

/**
 * 渲染每日日程
 */
function renderDailySchedule(date) {
    const container = document.getElementById('daily-schedule');
    const title = document.getElementById('selected-date-title');
    
    // 更新标题
    const dateStr = formatDate(date);
    const isToday = isSameDay(date, new Date());
    title.textContent = `📅 ${isToday ? '今天' : dateStr}的日程`;
    
    // 获取当天的任务
    const tasksForDay = allTasks.filter(task => {
        if (task.type === 'fixed' && task.startTime) {
            return isSameDay(new Date(task.startTime), date);
        }
        if (task.type === 'flexible' && task.deadline) {
            return isSameDay(new Date(task.deadline), date);
        }
        return false;
    });
    
    // 按开始时间或截止时间排序
    tasksForDay.sort((a, b) => {
        const timeA = a.startTime || a.deadline;
        const timeB = b.startTime || b.deadline;
        return new Date(timeA) - new Date(timeB);
    });
    
    if (tasksForDay.length === 0) {
        container.innerHTML = '<p class="empty-state">这一天没有安排任务</p>';
        return;
    }
    
    // 渲染任务列表
    let html = '';
    tasksForDay.forEach(task => {
        const typeClass = task.type === 'fixed' ? 'fixed' : 'flexible';
        const statusClass = task.status === 'completed' ? 'completed' : '';
        
        html += `
            <div class="schedule-item ${typeClass} ${statusClass}" data-task-id="${task.id}">
                <div class="schedule-item-header">
                    <span class="schedule-item-title">${task.title}</span>
                    <span class="priority-badge priority-${task.priority}">${task.priority}</span>
                </div>
        `;
        
        // 时间信息
        if (task.type === 'fixed' && task.startTime && task.endTime) {
            // 固定任务：显示具体的开始和结束时间
            html += `
                <div class="schedule-item-time">
                    🕐 ${formatTime(task.startTime)} - ${formatTime(task.endTime)}
                    ${task.location ? ' | 📍 ' + task.location : ''}
                </div>
            `;
        } else if (task.type === 'flexible') {
            // 灵活任务：显示预估时长和截止时间
            html += `
                <div class="schedule-item-time">
                    ⏱️ 预估${formatDuration(task.estimatedDuration)}
                    ${task.deadline ? ' | ⏰ 截止：' + formatTime(task.deadline) : ''}
                </div>
            `;
        } else {
            // 兜底：显示可用信息
            html += `
                <div class="schedule-item-time">
                    ℹ️ ${task.type === 'fixed' ? '固定时间' : '灵活安排'}
                </div>
            `;
        }
        
        // 元数据
        html += '<div class="schedule-item-meta">';
        // 只有灵活任务才在这里显示地点（固定任务已在时间行显示）
        if (task.type === 'flexible' && task.location) {
            html += `<span>📍 ${task.location}</span>`;
        }
        if (task.description) {
            html += `<span>📝 ${task.description}</span>`;
        }
        if (task.tags && task.tags.length > 0) {
            task.tags.forEach(tag => {
                html += `<span class="tag">${tag}</span>`;
            });
        }
        html += '</div>';
        
        // 操作按钮
        if (task.status !== 'completed') {
            html += `
                <div class="schedule-item-actions">
                    <button class="btn-complete" onclick="markTaskComplete('${task.id}')">
                        ✓ 完成
                    </button>
                    <button class="btn-delete" onclick="deleteTaskById('${task.id}')">
                        ✗ 删除
                    </button>
                </div>
            `;
        }
        
        html += '</div>';
    });
    
    container.innerHTML = html;
}

/**
 * 渲染解析结果
 */
function renderParseResult(result) {
    const container = document.getElementById('parse-result');
    const { task, confidence } = result;
    
    let html = '<div class="result-items">';
    
    // 标题
    html += `
        <div class="result-item">
            <span class="result-label">任务标题：</span>
            <span class="result-value"><strong>${task.title}</strong></span>
        </div>
    `;
    
    // 描述
    if (task.description) {
        html += `
            <div class="result-item">
                <span class="result-label">描述：</span>
                <span class="result-value">${task.description}</span>
            </div>
        `;
    }
    
    // 任务类型
    const typeText = task.type === 'fixed' ? '固定任务' : '灵活任务';
    html += `
        <div class="result-item">
            <span class="result-label">类型：</span>
            <span class="result-value">${typeText}</span>
        </div>
    `;
    
    // 时间信息
    if (task.type === 'fixed') {
        html += `
            <div class="result-item">
                <span class="result-label">开始时间：</span>
                <span class="result-value">${formatDateTime(task.startTime)}</span>
            </div>
            <div class="result-item">
                <span class="result-label">结束时间：</span>
                <span class="result-value">${formatDateTime(task.endTime)}</span>
            </div>
        `;
    } else {
        html += `
            <div class="result-item">
                <span class="result-label">预估时长：</span>
                <span class="result-value">${formatDuration(task.estimatedDuration)}</span>
            </div>
        `;
        if (task.deadline) {
            html += `
                <div class="result-item">
                    <span class="result-label">截止时间：</span>
                    <span class="result-value">${formatDateTime(task.deadline)}</span>
                </div>
            `;
        }
    }
    
    // 优先级
    html += `
        <div class="result-item">
            <span class="result-label">优先级：</span>
            <span class="result-value">
                <span class="priority-badge priority-${task.priority}">${task.priority}</span>
            </span>
        </div>
    `;
    
    // 地点
    if (task.location) {
        html += `
            <div class="result-item">
                <span class="result-label">地点：</span>
                <span class="result-value">${task.location}</span>
            </div>
        `;
    }
    
    // 标签
    if (task.tags && task.tags.length > 0) {
        html += `
            <div class="result-item">
                <span class="result-label">标签：</span>
                <span class="result-value">
                    ${task.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                </span>
            </div>
        `;
    }
    
    // 置信度
    html += `
        <div class="result-item">
            <span class="result-label">置信度：</span>
            <span class="result-value">
                <span class="confidence">${(confidence * 100).toFixed(0)}%</span>
            </span>
        </div>
    `;
    
    html += '</div>';
    
    container.innerHTML = html;
    
    // 显示结果区域
    document.getElementById('parse-result-section').style.display = 'block';
    
    // 滚动到结果区域
    document.getElementById('parse-result-section').scrollIntoView({ 
        behavior: 'smooth', 
        block: 'nearest' 
    });
}

/**
 * 更新统计信息
 */
function updateStats() {
    const total = allTasks.length;
    const completed = allTasks.filter(t => t.status === 'completed').length;
    const inProgress = allTasks.filter(t => t.status === 'in_progress').length;
    
    document.getElementById('total-tasks').textContent = total;
    document.getElementById('completed-tasks').textContent = completed;
    document.getElementById('inprogress-tasks').textContent = inProgress;
}

/**
 * 刷新所有数据
 */
async function refreshData() {
    allTasks = await fetchAllTasks();
    updateStats();
    renderCalendar();
    renderDailySchedule(selectedDate);
}

// ==================== 事件处理 ====================

/**
 * 处理解析按钮点击
 */
async function handleParseClick() {
    const input = document.getElementById('task-input');
    const text = input.value.trim();
    
    if (!text) {
        showToast('请输入任务描述', 'error');
        return;
    }
    
    try {
        const result = await parseTask(text);
        currentTask = result.task;
        renderParseResult(result);
        showToast('解析成功！', 'success');
    } catch (error) {
        showToast(`解析失败：${error.message}`, 'error');
    }
}

/**
 * 处理保存任务按钮点击
 */
async function handleSaveTask() {
    if (!currentTask) {
        showToast('没有待保存的任务', 'error');
        return;
    }
    
    try {
        setLoading(true);
        const result = await saveTask(currentTask);
        showToast('任务已保存！', 'success');
        
        // 清空输入
        document.getElementById('task-input').value = '';
        document.getElementById('parse-result-section').style.display = 'none';
        currentTask = null;
        
        // 刷新数据
        await refreshData();
        
    } catch (error) {
        showToast(`保存失败：${error.message}`, 'error');
    } finally {
        setLoading(false);
    }
}

/**
 * 生成调度方案
 */
async function generateSchedulePlan(tasks, existingEvents = []) {
    try {
        setLoading(true);
        
        // 获取工作时间配置（使用默认值）
        const preference = {
            workingHours: [{start: "09:00", end: "18:00"}],
            bufferBetweenEvents: 15,
            maxFocusDuration: 120,
            minBlockUnit: 30
        };
        
        const response = await fetch(`${API_BASE_URL}/v1/schedule/plan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tasks: tasks,
                existingEvents: existingEvents,
                preference: preference
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '调度失败');
        }
        
        return await response.json();
        
    } catch (error) {
        console.error('生成调度方案失败:', error);
        throw error;
    } finally {
        setLoading(false);
    }
}

// 全局变量存储当前调度方案
let currentSchedulePlan = null;

/**
 * 显示调度结果模态框
 */
function showScheduleModal(plan) {
    currentSchedulePlan = plan;
    const modal = document.getElementById('schedule-modal');
    const body = document.getElementById('schedule-modal-body');
    
    let html = '';
    
    // 已调度的任务
    if (plan.scheduledTasks && plan.scheduledTasks.length > 0) {
        html += '<h3 style="color: var(--success-color); margin-bottom: 12px;">✅ 已调度的任务</h3>';
        plan.scheduledTasks.forEach(item => {
            const start = formatDateTime(item.scheduledStart);
            const end = formatDateTime(item.scheduledEnd);
            html += `
                <div class="schedule-plan-item">
                    <div class="plan-item-title">${item.task.title}</div>
                    <div class="plan-item-time">🕐 ${start} - ${end}</div>
                    ${item.reason ? `<div class="plan-item-time">💡 ${item.reason}</div>` : ''}
                </div>
            `;
        });
    }
    
    // 冲突
    if (plan.conflicts && plan.conflicts.length > 0) {
        html += '<h3 style="color: var(--error-color); margin-top: 20px; margin-bottom: 12px;">⚠️ 发现冲突</h3>';
        plan.conflicts.forEach(conflict => {
            html += `
                <div class="schedule-plan-item conflict">
                    <div class="plan-item-title">任务 ${conflict.taskId}</div>
                    <div class="plan-item-time">⚠️ ${conflict.reason}</div>
                </div>
            `;
        });
    }
    
    // 未调度的任务
    if (plan.unscheduledTasks && plan.unscheduledTasks.length > 0) {
        html += '<h3 style="color: var(--warning-color); margin-top: 20px; margin-bottom: 12px;">⏸️ 未能调度的任务</h3>';
        plan.unscheduledTasks.forEach(task => {
            html += `
                <div class="schedule-plan-item unscheduled">
                    <div class="plan-item-title">${task.title}</div>
                    <div class="plan-item-time">⏸️ 未找到合适的时间槽</div>
                </div>
            `;
        });
    }
    
    // 说明
    if (plan.explanation) {
        html += `
            <div class="plan-explanation">
                <strong>📋 调度说明：</strong><br>
                ${plan.explanation}
            </div>
        `;
    }
    
    body.innerHTML = html;
    modal.classList.add('show');
}

/**
 * 关闭调度模态框
 */
function closeScheduleModal() {
    const modal = document.getElementById('schedule-modal');
    modal.classList.remove('show');
    currentSchedulePlan = null;
}

/**
 * 确认应用调度方案
 */
async function confirmSchedule() {
    if (!currentSchedulePlan) {
        closeScheduleModal();
        return;
    }
    
    try {
        setLoading(true);
        closeScheduleModal();
        
        // 应用调度方案：将调度后的时间更新到任务
        for (const scheduledItem of currentSchedulePlan.scheduledTasks) {
            const task = scheduledItem.task;
            
            // 如果是灵活任务被调度了，转换为固定任务
            if (task.type === 'flexible' && scheduledItem.scheduledStart && scheduledItem.scheduledEnd) {
                // 删除旧任务
                if (task.id) {
                    await deleteTask(task.id);
                }
                
                // 创建新的固定任务
                const updatedTask = {
                    ...task,
                    type: 'fixed',
                    startTime: scheduledItem.scheduledStart,
                    endTime: scheduledItem.scheduledEnd,
                    estimatedDuration: null  // 固定任务不需要这个字段
                };
                
                await saveTask(updatedTask);
            }
        }
        
        // 刷新数据
        await refreshData();
        showToast('调度方案已应用！', 'success');
        
    } catch (error) {
        showToast(`应用失败：${error.message}`, 'error');
    } finally {
        setLoading(false);
    }
}

/**
 * 处理立即调度按钮点击
 */
async function handleScheduleNow() {
    if (!currentTask) {
        showToast('没有待调度的任务', 'error');
        return;
    }
    
    // 如果是固定任务，直接保存，不需要调度
    if (currentTask.type === 'fixed') {
        try {
            setLoading(true);
            await saveTask(currentTask);
            await refreshData();
            switchTab('schedule');
            showToast('固定任务已保存！', 'success');
            
            currentTask = null;
            document.getElementById('task-input').value = '';
            document.getElementById('parse-result-section').style.display = 'none';
        } catch (error) {
            showToast(`保存失败：${error.message}`, 'error');
        } finally {
            setLoading(false);
        }
        return;
    }
    
    // 灵活任务才需要调度
    try {
        setLoading(true);
        
        // 1. 临时给任务分配ID（用于调度计算）
        const taskForSchedule = {
            ...currentTask,
            id: 'temp_' + Date.now()
        };
        
        // 2. 获取所有现有任务（用于检测冲突）
        const allExistingTasks = await fetchAllTasks();
        
        // 3. 过滤出已经是固定时间的任务，作为已存在的事件
        const existingFixedTasks = allExistingTasks.filter(t => t.type === 'fixed');
        
        // 转换为Event格式
        const existingEvents = existingFixedTasks.map(t => ({
            id: t.id,
            title: t.title,
            startTime: t.startTime,
            endTime: t.endTime,
            location: t.location
        }));
        
        // 4. 只调度当前任务（不保存，只预览）
        const plan = await generateSchedulePlan([taskForSchedule], existingEvents);
        
        // 5. 显示漂亮的调度结果模态框
        showScheduleModal(plan);
        
        // 注意：这里不保存任务，只有用户点击"应用"才保存
        
    } catch (error) {
        showToast(`调度失败：${error.message}`, 'error');
    } finally {
        setLoading(false);
    }
}

/**
 * 确认并应用调度方案（从模态框点击"应用"按钮调用）
 */
async function confirmSchedule() {
    if (!currentSchedulePlan || !currentTask) {
        closeScheduleModal();
        return;
    }
    
    // 先保存到局部变量（因为关闭模态框会清空全局变量）
    const planToApply = currentSchedulePlan;
    const taskToSave = currentTask;
    
    // 关闭模态框
    closeScheduleModal();
    
    try {
        setLoading(true);
        
        // 现在才真正保存任务
        const savedTask = await saveTask(taskToSave);
        const taskWithId = savedTask.task;
        
        // 应用调度方案：将调度后的时间更新到任务
        if (planToApply.scheduledTasks && planToApply.scheduledTasks.length > 0) {
            const scheduledItem = planToApply.scheduledTasks[0];  // 只处理当前任务
            const task = scheduledItem.task;
            
            // 如果是灵活任务被调度了，转换为固定任务
            if (task.type === 'flexible' && scheduledItem.scheduledStart && scheduledItem.scheduledEnd) {
                // 删除刚保存的灵活任务
                if (taskWithId.id) {
                    await deleteTask(taskWithId.id);
                }
                
                // 创建新的固定任务
                const updatedTask = {
                    ...taskWithId,
                    type: 'fixed',
                    startTime: scheduledItem.scheduledStart,
                    endTime: scheduledItem.scheduledEnd,
                    estimatedDuration: null
                };
                
                await saveTask(updatedTask);
            } else if (task.type === 'fixed') {
                // 固定任务直接使用原有时间，已经保存过了，不需要额外操作
                console.log('固定任务已保存，使用原有时间');
            }
        }
        
        // 刷新数据并切换到日程tab
        await refreshData();
        switchTab('schedule');
        
        showToast('调度方案已应用！', 'success');
        
        // 清理状态（已在closeScheduleModal中清理）
        document.getElementById('task-input').value = '';
        document.getElementById('parse-result-section').style.display = 'none';
        
    } catch (error) {
        showToast(`应用失败：${error.message}`, 'error');
    } finally {
        setLoading(false);
    }
}

/**
 * 标记任务完成
 */
async function markTaskComplete(taskId) {
    // 简化实现：从列表中移除
    try {
        await deleteTask(taskId);
        showToast('任务已完成！', 'success');
        await refreshData();
    } catch (error) {
        showToast(`操作失败：${error.message}`, 'error');
    }
}

/**
 * 删除任务
 */
async function deleteTaskById(taskId) {
    if (!confirm('确定要删除这个任务吗？')) {
        return;
    }
    
    try {
        await deleteTask(taskId);
        showToast('任务已删除', 'success');
        await refreshData();
    } catch (error) {
        showToast(`删除失败：${error.message}`, 'error');
    }
}

/**
 * 处理示例按钮点击
 */
function handleExampleClick(event) {
    if (event.target.classList.contains('example-btn')) {
        const text = event.target.dataset.text;
        document.getElementById('task-input').value = text;
        showToast('示例已填入，点击"解析任务"继续', 'info');
    }
}

/**
 * 切换Tab
 */
function switchTab(tabName) {
    // 更新tab按钮
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.tab === tabName) {
            tab.classList.add('active');
        }
    });
    
    // 更新tab内容
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    if (tabName === 'input') {
        document.getElementById('input-tab').classList.add('active');
    } else if (tabName === 'schedule') {
        document.getElementById('schedule-tab').classList.add('active');
    }
}

// ==================== 初始化 ====================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('AIMakesPlans 前端初始化中...');
    
    // 检查API健康状态
    checkAPIHealth();
    setInterval(checkAPIHealth, 30000); // 每30秒检查一次
    
    // 加载任务数据
    await refreshData();
    
    // 渲染今天的日程
    renderDailySchedule(selectedDate);
    
    // 绑定事件
    document.getElementById('parse-btn').addEventListener('click', handleParseClick);
    document.getElementById('save-task-btn').addEventListener('click', handleSaveTask);
    document.getElementById('schedule-now-btn').addEventListener('click', handleScheduleNow);
    document.getElementById('refresh-schedule-btn').addEventListener('click', refreshData);
    document.querySelector('.examples').addEventListener('click', handleExampleClick);
    
    // Tab切换事件
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            switchTab(tab.dataset.tab);
        });
    });
    
    // 支持回车键快速解析
    document.getElementById('task-input').addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            handleParseClick();
        }
    });
    
    console.log('✓ AIMakesPlans 前端已初始化');
});
