# AI Scheduling System - Backend API

## 项目概述

基于FastAPI的AI驱动智能日程管理系统后端。支持自然语言任务解析、冲突检测和智能调度。

## 目录结构

```
backend/
├── app/
│   ├── main.py                 # FastAPI应用入口
│   ├── core/
│   │   └── config.py          # 配置管理
│   ├── models/
│   │   └── schemas.py         # 数据模型定义
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py    # v1路由汇总
│   │       ├── tasks.py       # 任务管理API
│   │       ├── parse.py       # 自然语言解析API
│   │       └── schedule.py    # 调度规划API
│   └── services/              # 服务层（待实现）
│       ├── llm_service.py     # LLM封装
│       ├── parsing.py         # 解析逻辑
│       ├── scheduling.py      # 调度算法
│       └── conflicts.py       # 冲突检测
└── tests/
    ├── test_api.py            # API集成测试
    └── test_schemas.py        # 数据模型单元测试
```

## 快速开始

### 1. 激活conda环境

```bash
conda activate project_ai_makes_plans
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量（可选）

复制`.env.example`到`.env`并配置：

```bash
cp .env.example .env
```

编辑`.env`文件：

```
LLM_PROVIDER=openai
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-3.5-turbo
PORT=8000
PRIORITY_POLICY=eisenhower
```

### 4. 启动服务器

```bash
# 开发模式（热重载）
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

# 或使用Python模块方式
python -m uvicorn backend.app.main:app --reload
```

### 5. 访问API文档

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- 健康检查: http://127.0.0.1:8000/health

## API 端点

### 健康检查

- `GET /health` - 服务健康状态
- `GET /` - API基本信息

### v1 API

#### 任务管理

- `POST /v1/tasks` - 创建任务
- `GET /v1/tasks` - 获取所有任务
- `GET /v1/tasks/{task_id}` - 获取指定任务
- `DELETE /v1/tasks/{task_id}` - 删除任务

#### 自然语言解析

- `POST /v1/parse` - 将自然语言文本解析为结构化任务

#### 调度规划

- `POST /v1/schedule/plan` - 生成任务调度方案

## 数据模型

### Task（任务）

```python
{
    "id": "uuid",
    "title": "任务标题",
    "description": "任务描述",
    "type": "flexible",  # 或 "fixed"
    "estimatedDuration": 120,  # 分钟（灵活任务）
    "startTime": "2025-10-06T14:00:00",  # 固定任务
    "endTime": "2025-10-06T16:00:00",    # 固定任务
    "deadline": "2025-10-08T18:00:00",   # 截止时间
    "priority": "P2",  # P0-P3
    "status": "pending",  # pending/in_progress/completed/cancelled
    "location": "会议室",
    "tags": ["工作", "重要"]
}
```

### Event（事件）

```python
{
    "id": "uuid",
    "title": "会议",
    "description": "团队会议",
    "startTime": "2025-10-06T10:00:00",
    "endTime": "2025-10-06T11:00:00",
    "location": "101会议室"
}
```

### UserPreference（用户偏好）

```python
{
    "workingHours": [
        {"start": "09:00", "end": "18:00"}
    ],
    "noDisturbSlots": [
        {"start": "12:00", "end": "13:00"}
    ],
    "maxFocusDuration": 120,  # 最大专注时长（分钟）
    "minBlockUnit": 30,       # 最小时间块（分钟）
    "bufferBetweenEvents": 15 # 事件间缓冲（分钟）
}
```

## 测试

### 运行所有测试

```bash
pytest backend/tests/ -v
```

### 运行特定测试

```bash
# 只运行API测试
pytest backend/tests/test_api.py -v

# 只运行模型测试
pytest backend/tests/test_schemas.py -v
```

### 测试覆盖率

```bash
pytest backend/tests/ --cov=backend/app --cov-report=html
```

## 使用示例

### 创建灵活任务

```bash
curl -X POST http://127.0.0.1:8000/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task": {
      "title": "写周报",
      "type": "flexible",
      "estimatedDuration": 60,
      "priority": "P2"
    }
  }'
```

### 创建固定任务

```bash
curl -X POST http://127.0.0.1:8000/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task": {
      "title": "团队会议",
      "type": "fixed",
      "startTime": "2025-10-06T14:00:00",
      "endTime": "2025-10-06T15:00:00",
      "priority": "P1"
    }
  }'
```

### 解析自然语言

```bash
curl -X POST http://127.0.0.1:8000/v1/parse \
  -H "Content-Type: application/json" \
  -d '{
    "text": "明天下午做2小时报告"
  }'
```

### 生成调度方案

```bash
curl -X POST http://127.0.0.1:8000/v1/schedule/plan \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {
        "title": "写代码",
        "type": "flexible",
        "estimatedDuration": 120,
        "priority": "P1"
      }
    ],
    "existingEvents": [],
    "preference": {
      "maxFocusDuration": 120
    }
  }'
```

## 当前状态

✅ **已完成（v0.1.0）**

- FastAPI应用骨架
- 健康检查和基础路由
- 完整的数据模型定义（Pydantic）
- 任务管理API（CRUD操作）
- 解析和调度API占位符
- 全面的单元测试和集成测试（38个测试全部通过）
- CORS支持
- API文档（Swagger/ReDoc）

⏳ **待实现**

- LLM服务集成（OpenAI/Claude/DeepSeek）
- 实际的自然语言解析逻辑
- 冲突检测算法
- 智能调度算法
- 数据持久化（SQLite/PostgreSQL）
- ICS导入/导出
- 用户偏好和状态管理API

## 开发指南

### 添加新的API端点

1. 在`backend/app/api/v1/`下创建新的路由文件
2. 在`backend/app/api/v1/__init__.py`中注册路由
3. 在`backend/tests/`中添加相应的测试

### 添加新的数据模型

1. 在`backend/app/models/schemas.py`中定义Pydantic模型
2. 在`backend/tests/test_schemas.py`中添加验证测试

### 代码规范

- 遵循PEP 8规范
- 使用类型提示
- 编写文档字符串
- 保持测试覆盖率

## 下一步

按照`docs/02_llm_service_and_prompt_engineering.md`文档继续开发LLM服务层。

## 许可证

MIT License

