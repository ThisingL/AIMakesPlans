### 03. 解析、冲突检测与调度算法（含测试）

本节实现冲突检测与灵活任务调度的核心逻辑，并提供丰富的单元测试建议。

### 目标

- 提供时间重叠判断：`start_new < end_exist && end_new > start_exist`
- 在偏好约束下寻找空闲时间块：不可用时段、最小块、缓冲时间
- 根据优先级与截止时间进行排序与分配，必要时给出备选方案

### 文件建议

```
backend/app/services/conflicts.py
backend/app/services/scheduling.py
backend/tests/test_conflicts.py
backend/tests/test_scheduling.py
```

### 提示词（实现）

```
实现 conflicts.py：
- overlap(a, b) -> bool
- find_conflicts(item, events) -> list[Conflict]

实现 scheduling.py：
- find_free_slots(events, preferences, range) -> list[Slot]
- plan(tasks, events, preferences, status) -> PlanResult（包含成功分配、冲突、无法安排说明）
- 策略：固定事件优先，灵活任务按 priority、deadline 排序；尊重缓冲与最小块
 - 状态约束：`status.restMode=true` 时仅返回“备选方案”不落地；`status.state=busy` 时可延后执行
```

### 测试设计

- 冲突检测：
  - 完全重叠、边界相接（不算重叠）、包含关系、跨日情况
- 空闲块查找：
  - 考虑不可用时段与缓冲时间；有/无可用块
- 调度：
  - 高优先级先排入；截止时间近者优先；无可用时给出备选

示例断言：

```
def test_overlap_basic():
    a = ("2025-10-05T10:00", "2025-10-05T11:00")
    b = ("2025-10-05T10:30", "2025-10-05T11:30")
    assert overlap(a, b) is True
```


