# AIMakesPlans
AI驱动的时间管理革命：让 LLM 成为你的智能日程助理，负责“理解需求 → 智能排期 → 冲突规避 → 动态跟进”，帮助你专注于真正重要的事。

### 功能概览（MVP）

- **自然语言创建任务**：支持口语化输入（如“明天下午做2小时报告”）→ 解析为结构化数据（标题、时长、时间偏好、优先级等）。
- **冲突检测与灵活调度**：自动识别重叠时间，基于用户偏好与优先级，把灵活任务安排到合适空闲时段。
- **用户偏好与状态**：工作/休息/不可用时段、最大专注时长、缓冲时间、忙碌/空闲、休息模式。
- **优先级策略**：支持“紧急-重要矩阵（Eisenhower）”与“先来后到（FIFO）”切换。
- **进度跟进**：任务结束前后提醒；未完成的灵活任务自动重新排期。
- **可视化（基础）**：Web 页面展示健康检查、解析结果、规划方案（可从简单表格或周视图开始）。
- **ICS（可选）**：导入/导出 iCalendar，兼容主流日历。

### 系统架构（建议）

- **后端（Python / FastAPI）**：
  - 路由：`/health`、`/v1/parse`、`/v1/tasks`、`/v1/schedule/plan`、`/v1/ics/*`、`/v1/user/*`
  - 服务层：LLM 封装、解析、冲突检测、调度、ICS 工具
  - 持久化：MVP 可内存/文件；推荐 SQLite + SQLAlchemy + Alembic（后续可切换 Postgres）

- **前端（Web）**：
  - 最小静态站：`index.html + app.js + styles.css`
  - 与后端接口打通，展示解析结果与排期方案

### 目录规划（建议）

```
backend/
  app/
    main.py
    core/config.py
    api/v1/
      parse.py
      tasks.py
      schedule.py
      ics.py
      user.py
    models/schemas.py
    services/
      llm_service.py
      parsing.py
      conflicts.py
      scheduling.py
      ics_tools.py
    persistence/
      repo.py
  tests/
    test_api.py
    test_parsing.py
    test_conflicts.py
    test_scheduling.py
frontend/
  web/
    index.html
    app.js
    styles.css
```

### 快速开始（待代码就绪后执行）

1) 创建虚拟环境并安装依赖（示例）：

```bash
python -m venv .venv && .\.venv\Scripts\activate
pip install fastapi "uvicorn[standard]" pydantic python-dotenv httpx pytest
```

2) 启动后端：

```bash
uvicorn backend.app.main:app --reload
```

3) 打开前端 `frontend/web/index.html`，在页面中调用 `/health` 和 `/v1/parse` 验证联通。

### 环境变量（示例）

```
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.openai.com/v1
PORT=8000
PRIORITY_POLICY=eisenhower   # eisenhower|fifo
```

### API 概览（草案）

- `GET  /health`：健康检查 → `{status:"ok"}`
- `POST /v1/parse`：自然语言 → 结构化任务（依赖 LLM）
- `POST /v1/tasks`：创建/保存任务（MVP 可内存/文件）
- `POST /v1/schedule/plan`：输入现有事件/偏好/待排任务 → 规划方案
- `POST /v1/ics/import`、`GET /v1/ics/export`：导入/导出 ICS（可选）
- `GET/PUT /v1/user/preferences`：读取/更新用户偏好
- `GET/PUT /v1/user/status`：读取/更新用户状态（busy/idle、restMode）

### 提示词驱动的实施步骤

将每一步的“提示词”复制到你的 LLM（如 Cursor/ChatGPT/Claude），让其产出代码改动。每步完成后立刻进行“测试方式”。

1) 项目初始化（后端 & 前端）

提示词：
```
请创建 FastAPI 后端骨架：
- backend/app/main.py：提供 GET /health 返回 {"status":"ok"}
- backend/app/core/config.py：读取 .env（PORT、LLM_PROVIDER、LLM_API_KEY）
- backend/tests/test_api.py：对 /health 进行集成测试（TestClient）
并创建最小前端：frontend/web/{index.html, app.js, styles.css}，调用 /health 并展示结果。
给出安装依赖、启动命令与 pytest 命令。
```

测试方式：
- `uvicorn backend.app.main:app --reload`；浏览器 `GET /health` 返回 `{"status":"ok"}`
- `pytest -q backend/tests/test_api.py` 通过

2) 数据模型与基础 API

提示词：
```
在 backend/app/models/schemas.py 定义：
- Priority（P0..P3）
- Task/Event/UserPreference/UserStatus/PriorityPolicy/Conflict/SchedulePlan
实现占位路由：POST /v1/parse、/v1/tasks、/v1/schedule/plan，并在 main.py 中挂载。
提供：示例请求/响应、pydantic 校验单测。
```

测试方式：
- `pytest -q backend/tests/test_schemas.py`；用 httpx/TestClient 断言 200 与 schema。

3) LLM 封装与提示词工程

提示词：
```
实现 services/llm_service.py：
- 兼容 OpenAI /v1/chat/completions；读取 LLM_PROVIDER、LLM_API_KEY、LLM_BASE_URL
- 提供 invoke_chat()、parse_text_to_task(text, preference)
- 使用 monkeypatch/mock 替代真实网络，编写单测
```

测试方式：
- 对 invoke_chat 做 monkeypatch，返回固定 JSON；断言 parse_text_to_task 结构正确。

4) 自然语言解析 API

提示词：
```
实现 services/parsing.py 与 api/v1/parse.py：
- POST /v1/parse 接收 {text, preference}，调用 llm_service，返回 Task
- 错误输入返回 4xx，包含错误信息
```

测试方式：
- `pytest -q backend/tests/test_parsing.py`；httpx 测试成功与失败用例。

5) 冲突检测与调度

提示词：
```
实现 conflicts.overlap(a,b) 与 scheduling.plan(tasks, events, preferences, status)
- 冲突规则：start_new < end_exist && end_new > start_exist
- 约束：不可用时段、最小块、缓冲、maxFocusDuration、restMode/busy、优先级与截止时间排序
```

测试方式：
- `pytest -q backend/tests/test_conflicts.py backend/tests/test_scheduling.py`

6) ICS 集成（可选）

提示词：
```
添加 /v1/ics/import 与 /v1/ics/export；使用内存文件进行单测。
```

7) 前端对接

提示词：
```
在前端提供输入框：
- 调用 /v1/parse 展示结构化结果
- 调用 /v1/schedule/plan 展示候选方案与冲突提示
```

### 测试方法与标准

- 单元测试：优先覆盖模型校验、冲突检测、调度算法；LLM 使用 mock。
- 集成测试：API 主链路（解析 → 调度）。
- 前端手测：表单输入 → 解析结果 → 规划结果。
- 通过标准：核心用例全绿；错误路径有清晰提示。

### 数据持久化（可选但推荐）

- MVP：内存或 JSON 文件
- 推荐：SQLite + SQLAlchemy + Alembic，后续无缝切换 Postgres
- 测试：仓储层 CRUD 单测、API 集成测（创建/查询任务）

### 路线图

- v0：MVP（解析、调度、偏好与状态、基础前端）
- v1：ICS、持久化、更多可视化
- v2：第三方日历双向同步、偏好自动学习、团队协同

### 贡献

欢迎通过 Issue/PR 提交改进建议或实现功能。
