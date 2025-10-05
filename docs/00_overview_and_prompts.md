### 00. 总览与提示词模板（提示词驱动开发）

本节提供“任务拆解 + 通用提示词模板”。按顺序执行，每一步都包含：目标、产出物、提示词、测试方法与验收标准。

### 项目结构（建议）

```
backend/
  app/
    main.py
    api/
      v1/
        schedules.py
        tasks.py
    core/
      config.py
    services/
      llm_service.py
      scheduling.py
      parsing.py
      conflicts.py
    models/
      schemas.py
    persistence/
      repo.py
  tests/
    test_api.py
    test_scheduling.py
frontend/
  web/
    index.html
    app.js
    styles.css
contracts/
  schemas.openapi.json
  examples/
    create_task.json
docs/
  ...（本文档所在位置）
```

### 任务拆解（里程碑）

1) 项目初始化与基础约定
- 目标：创建后端 FastAPI 骨架、前端静态目录、基础配置和依赖。
- 产出：`backend/app/main.py` 启动可用，健康检查接口通过，基础测试通过。

2) 模型与协议定义（Pydantic + OpenAPI）
- 目标：定义任务、事件、用户偏好等数据结构；生成并固定 OpenAPI。
- 产出：`schemas.py` 完成；`/openapi.json` 可导出；示例样本完成。

3) LLM 服务封装与提示词工程
- 目标：使用 Python 封装 LLM（OpenAI/Claude/DeepSeek 等），提供解析与规划提示词模板。
- 产出：`services/llm_service.py`、可配置的 `LLM_PROVIDER`、单元测试。

4) 自然语言解析与结构化建模
- 目标：将“明天下午做2小时报告”等文本解析成结构化任务。
- 产出：`services/parsing.py`，API：`POST /v1/parse`。

5) 冲突检测与灵活任务调度
- 目标：实现时间重叠检测与灵活任务排期算法（单日/同周）。
- 产出：`services/conflicts.py`、`services/scheduling.py`；API：`/v1/schedule/plan`。

6) ICS 导入/导出
- 目标：支持 iCalendar 导入/导出固定事件。
- 产出：`/v1/ics/import`、`/v1/ics/export`。

7) 前端 Web 对接与可视化
- 目标：最小可用 Web（周视图或简化列表），调用后端 API、拖拽/标记完成。
- 产出：`frontend/web` 可运行；与 API 打通。

8) 测试与 CI
- 目标：完善单元、集成测试；GitHub Actions 持续集成。
- 产出：`pytest` 通过；CI 徽章；最少 70% 语句覆盖。

9) 部署与运维
- 目标：Docker 化、环境变量、日志与基本监控。
- 产出：`Dockerfile`、`docker-compose.yml`、运行文档。

---

### 通用提示词模板（给 LLM）

将以下提示词复制到你的 LLM 中，根据“当前阶段”替换花括号内容。

```
你是一名资深软件工程师，使用 Python(FastAPI) + Web 前端实现“AI 日程系统”。
当前阶段：{阶段名称，例如：项目初始化}
目标：{该阶段要达成的目标}
约束：
- 遵循已确定的数据模型与 API 设计
- 生成可运行的代码，包含必要的导入/依赖
- 代码可测（pytest 单测或最少提供 http 调用示例）

请输出：
1) 代码变更列表（文件路径与关键变更点）
2) 完整代码片段（仅新/改文件）
3) 依赖与环境变量说明
4) 测试方法（命令、示例请求、预期响应）
5) 如失败，给出调试步骤
```

---

### 单元测试提示词模板

```
为以下模块补充 pytest 单元测试：{模块/函数}
要求：
- 覆盖典型路径与边界条件
- 无外部网络依赖（对 LLM/HTTP 进行 mock）
- 可独立运行：pytest -q 通过
请给出：测试代码、运行命令与通过标准
```

---

### 里程碑 1：项目初始化（后端 & 前端）

目标：
- 创建 FastAPI 应用、基础路由（`GET /health`），并配置 `uvicorn` 启动
- 初始化前端静态目录与最小页面
- 准备 `requirements.txt` 与 `pytest` 配置

建议对 LLM 的提示词：

```
请在项目中创建后端骨架（FastAPI）：
- backend/app/main.py：包含 /health 路由返回 {"status":"ok"}
- backend/app/core/config.py：读取 .env 的基本配置（PORT、LLM_PROVIDER）
- backend/tests/test_api.py：包含 /health 的集成测试（使用 TestClient）
- requirements.txt：fastapi, uvicorn[standard], pydantic, python-dotenv, pytest, httpx
并创建最小前端：
- frontend/web/index.html, app.js, styles.css（调用 /health 并展示结果）
给出启动命令与测试命令。
```

测试方法：
- 后端：`uvicorn backend.app.main:app --reload` 启动；访问 `GET /health` 返回 `{"status":"ok"}`
- 单测：`pytest -q backend/tests/test_api.py`
- 前端：用任意静态服务器或浏览器直接打开 `index.html`，页面展示健康状态。

验收标准：
- 路由与测试全部通过；前端能正确显示健康状态。

---

### 里程碑 2：数据模型与 API 契约

目标：
- 在 `models/schemas.py` 定义 `Task`, `Event`, `UserPreference` 等
- 在 `api/v1/tasks.py` 提供 `POST /v1/tasks/parse`（文本→结构化）、`POST /v1/tasks`（创建）
- 导出 OpenAPI（`/openapi.json`）并固定示例

提示词：

```
新增/更新以下文件：
- backend/app/models/schemas.py：定义 Task(Event-like)、SchedulePlan、Conflict、UserPreference
- backend/app/api/v1/tasks.py：实现 POST /v1/tasks/parse 与 POST /v1/tasks
- backend/app/app.py 或 main.py：挂载 v1 路由
请给出：数据模型、路由实现、示例请求/响应、OpenAPI 导出方法，以及针对 schemas 的 pydantic 校验单测。
```

测试方法：
- 运行服务后：`curl -X POST /v1/tasks -d '{...}'` 返回 201
- `pytest -q backend/tests/test_schemas.py`

验收标准：
- 模型字段与文档一致；OpenAPI 可导出；单测通过。

---

### 里程碑 3：LLM 服务与提示词工程

目标：
- `services/llm_service.py` 封装多家 LLM 提供商，基于环境变量切换
- 提供解析/调度通用提示词模板，并暴露 `parse_text_to_task()` 接口

提示词：

```
实现 Python LLM 封装：
- 支持 OpenAI/Claude/DeepSeek（任选至少1家，接口可扩展）
- 读取 API Key、base_url 等环境变量
- 提供函数 parse_text_to_task(text, preference)->Task（返回 pydantic 模型或 dict）
请给出：代码、依赖、mock 单测方案（不调用真实网络）。
```

测试方法：
- 单测对 `llm_service` 进行 monkeypatch，返回可控 JSON；断言解析结果结构正确。

验收标准：
- 无真实网络依赖；接口稳定，异常处理到位。

---

### 里程碑 4：自然语言解析 API

目标：
- `services/parsing.py` 调用 `llm_service`，完成文本→结构化任务
- `POST /v1/parse` 对外提供解析能力

提示词：

```
实现 parsing 模块与 API：
- services/parsing.py：封装业务规则（字段兜底、默认优先级、类型推断）
- api/v1/parse.py：POST /v1/parse 接收 {text, preference} 返回 Task
请给出：代码、错误场景示例、API 测试用例（httpx）。
```

测试方法：
- `pytest -q backend/tests/test_parsing_api.py`

验收标准：
- 合法文本解析成功，错误文本返回 4xx 并包含错误信息。

---

### 里程碑 5：冲突检测与调度

目标：
- `conflicts.py` 实现时间重叠判断；`scheduling.py` 实现灵活任务排期（同周单块/可选拆分）
- API：`POST /v1/schedule/plan` 输入当前日程与待排任务，输出候选方案与理由

提示词：

```
实现冲突检测与调度算法：
- conflicts.overlap(a,b)：基于 (start_new < end_exist && end_new > start_exist)
- scheduling.plan(tasks, events, preferences)：返回可行方案、冲突与解释
- api/v1/schedule.py：POST /v1/schedule/plan
请给出：算法代码、边界用例单测、API 集成测。
```

测试方法：
- `pytest -q backend/tests/test_conflicts.py test_scheduling.py`

验收标准：
- 典型冲突可识别；灵活任务按优先级与约束排入合适空闲时段。

---

### 里程碑 6：ICS 导入/导出

目标：
- 支持上传 ICS 导入固定事件；导出当前日程为 ICS

提示词：

```
新增接口：
- POST /v1/ics/import（multipart/form-data 上传 .ics）
- GET /v1/ics/export（下载 .ics）
实现解析/序列化，并编写文件级单元测试（使用内存文件）。
```

测试方法：
- 用示例 ICS 文件进行导入，导出后比对关键字段。

验收标准：
- 与主流日历兼容（基本字段）；错误文件返回 4xx。

---

### 里程碑 7：前端 Web 对接

目标：
- 构建最小页面：输入自然语言 → 调用 /v1/parse → 展示结果；展示计划方案与冲突提示

提示词：

```
实现前端：
- index.html + app.js：提供输入框、结果区域、简单周视图（可选第三方库）
- 与后端 /health、/v1/parse、/v1/schedule/plan 对接
给出：构建/运行方式与手动测试步骤。
```

测试方法：
- 打开页面，输入“明天下午做2小时报告”，前端展示解析后的结构化数据。

验收标准：
- 常见输入可正确显示；错误提示清晰。

---

### 里程碑 8：测试与 CI

提示词：

```
配置 pytest 与 GitHub Actions：
- 添加 pytest.ini（最少警告过滤与失败重试可选）
- .github/workflows/ci.yml：安装依赖、运行 pytest、上传覆盖率到 codecov（可选）
```

测试方法：
- 本地与 CI 均能 `pytest -q` 全绿。

验收标准：
- CI 运行成功；覆盖率 ≥ 70%（可作为后续目标）。

---

### 里程碑 9：部署与运维

提示词：

```
提供部署文件：
- Dockerfile（多阶段构建）
- docker-compose.yml（后端 + 前端静态服务）
- .env.example（API Keys、LLM_PROVIDER、PORT）
给出：构建与启动命令、健康检查说明、日志采集建议。
```

测试方法：
- `docker compose up -d` 后，访问后端健康检查与前端页面。

验收标准：
- 在容器中可稳定运行，日志与环境变量生效。


