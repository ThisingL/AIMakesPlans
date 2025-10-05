### 08. 用户偏好、优先级策略与动态状态（休息模式）

本节定义偏好与状态的模型、接口与调度规则，并提供提示词与测试方法。

### 目标

- 模型：`UserPreference`、`UserStatus`、`PriorityPolicy`
- API：读取/更新用户偏好与状态；在调度中应用
- 调度规则：忙碌/空闲、休息模式、缓冲时间、最大专注时长、最小块；优先级排序

### 数据模型（建议）

- `UserPreference`
  - `workingHours`: 每日工作时间段（如 09:00-18:00，周末可不同）
  - `noDisturbSlots`: 不可用时段（午休 12:00-13:00、晚餐 18:00-19:00 等）
  - `maxFocusDuration`: 单次连续专注上限（分钟）
  - `minBlockUnit`: 最小时间块（分钟）
  - `bufferBetweenEvents`: 事件间缓冲（分钟）
  - `priorityPolicy`: "eisenhower" | "fifo"

- `UserStatus`
  - `state`: "busy" | "idle"
  - `restMode`: boolean（开启时暂停新安排与提醒）
  - `lastUpdated`: ISO 时间戳

### API（建议）

```
GET  /v1/user/preferences
PUT  /v1/user/preferences
GET  /v1/user/status
PUT  /v1/user/status
```

### 调度与状态规则

- 状态影响：
  - `state=busy`：仅允许查询，不触发新排期（或只生成草案，不落库）
  - `restMode=true`：不生成新安排与提醒；仅允许查看、标记完成

- 优先级排序：
  - `eisenhower`：按紧急（deadline 近）×重要（priority 值）综合评分排序
  - `fifo`：按创建时间先来后到

- 时间约束：
  - 排入空闲块时需满足 `minBlockUnit` 与 `bufferBetweenEvents`
  - 若 `estimatedDuration > maxFocusDuration`：允许拆分为多块，并在块之间加入缓冲

### 提示词（实现）

```
实现以下内容：
- models/schemas.py：新增 UserPreference, UserStatus, PriorityPolicy；补充示例
- api/v1/user.py：实现上述 4 个端点（内存/文件存储占位实现）
- services/scheduling.py：读取 preferences 与 status，应用 restMode/priorityPolicy/maxFocusDuration 等规则
提供：单元测试与集成测试。
```

### 测试方法

- 单测：
  - 偏好合并与默认值填充；`maxFocusDuration`/`minBlockUnit` 的边界
  - `restMode=true` 时，`plan()` 不返回可落地的新安排（只给备选）

- 集成：
  - 设置偏好与状态后，调用 `/v1/schedule/plan`，断言排序与时间块符合预期

### 验收标准

- 支持读取/更新偏好与状态
- 调度结果严格遵守偏好与状态约束；优先级策略可切换


