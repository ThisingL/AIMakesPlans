### 01. 后端架构与 API 设计（Python + FastAPI）

本节指导以提示词驱动的方式实现可运行的后端。包含：目录结构、依赖、关键接口、测试方案与提示词。

### 目标

- 使用 FastAPI 搭建后端，提供基础健康检查与版本信息
- 定义 v1 API：解析、任务创建、调度规划的占位路由
- 配置化读取环境变量（端口、LLM 提供商、API Keys）
- 提供完整测试方法（pytest + TestClient）

### 建议依赖

```
fastapi
uvicorn[standard]
pydantic
python-dotenv
httpx
pytest
```

### 目录结构（后端）

```
backend/
  app/
    main.py
    core/config.py
    api/v1/__init__.py
    api/v1/tasks.py
    api/v1/parse.py
    api/v1/schedule.py
    models/schemas.py
  tests/
    test_api.py
```

### 步骤与提示词

1) 初始化骨架与健康检查

提示词：

```
创建 FastAPI 应用：
- backend/app/main.py：创建 app；添加 GET /health 返回 {"status":"ok"}
- backend/app/core/config.py：读取 .env（PORT、LLM_PROVIDER、LLM_API_KEY）
- backend/tests/test_api.py：对 /health 做基础测试（200 与 JSON 字段）
输出：关键代码、依赖、运行/测试命令。
```

测试：
- 运行：`uvicorn backend.app.main:app --reload`
- 浏览器/`curl http://127.0.0.1:8000/health`
- `pytest -q backend/tests/test_api.py`

2) 定义数据模型（Pydantic）

提示词：

```
在 backend/app/models/schemas.py 定义：
- Priority（枚举 P0..P3）
- Task（title, description, type: fixed/flexible, estimatedDuration, startTime, endTime, deadline, priority）
- Event（startTime, endTime, title, description, location）
- UserPreference（workingHours, noDisturbSlots, maxFocusDuration, minBlockUnit, bufferBetweenEvents）
请给出：字段校验与示例。
```

测试：
- `pytest` 中新增 `test_schemas.py`，对字段必填、非法值进行断言。

3) v1 路由占位

提示词：

```
实现以下路由占位（返回 200 与固定示例）：
- POST /v1/tasks（创建任务）
- POST /v1/parse（文本→结构化 Task）
- POST /v1/schedule/plan（规划）
并在 main.py 中挂载路由。
```

测试：
- `httpx`/`TestClient` 对 3 个路由做 200 响应与 schema 基本断言。

### 验收标准

- 健康检查可用，v1 路由存在且可返回示例
- 模型校验单元测试通过

### 附：最小单测样例（可复制到 LLM 生成代码时参考）

```
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"
```


