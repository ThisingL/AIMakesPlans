### 02. LLM 服务封装与提示词工程

本节聚焦：如何以可替换的方式封装 LLM，制定稳定的解析/规划提示词，并提供完善的测试方法（mock）。

### 目标

- 支持至少一种厂商（如 OpenAI 兼容协议），接口可扩展至 Claude/DeepSeek
- 通过环境变量切换 `LLM_PROVIDER`、`LLM_API_KEY`、`LLM_BASE_URL`
- 提供核心方法：`parse_text_to_task(text, preference)` 与 `plan_schedule(inputs)`
- 对外不暴露厂商差异，返回统一数据结构（与 `schemas.py` 对应）

### 目录与文件

```
backend/app/services/llm_service.py
backend/tests/test_llm_service.py
```

### 实施提示词

1) 服务封装

```
实现 llm_service：
- 基于 httpx 同步/异步客户端调用 OpenAI 兼容接口（/v1/chat/completions）
- 读取 LLM_PROVIDER, LLM_API_KEY, LLM_BASE_URL
- 提供：invoke_chat(messages, temperature=0.2) 基础方法
- 在其上实现 parse_text_to_task(text, preference) 与 plan_schedule(inputs)
- 统一异常：网络错误、超时、无效响应结构
```

2) 提示词工程（解析）

```
为“文本→Task”编写系统提示与用户提示：
- 系统提示：你是资深日程规划助手，请将用户文本解析为结构化 JSON（字段：title, type, estimatedDuration, startTime/endTime/deadline, priority）。
- 用户提示：给出输入文本、用户偏好与示例输出 JSON（严格 JSON，无注释）。
```

3) 提示词工程（调度）

```
为“调度规划”编写提示词：
- 输入：当前事件/任务列表、用户偏好、待排灵活任务
- 输出：候选时间块、冲突说明、排序与理由（可解释）
```

### 测试与 Mock

- 使用 pytest 对 `invoke_chat` 进行 monkeypatch，返回模拟 JSON
- 断言：解析函数能将文本映射为合法 Task；调度函数输出包含候选方案

示例单测片段：

```
import types
from backend.app.services import llm_service

def fake_invoke_chat(messages, temperature=0.2):
    return {
        "choices": [{"message": {"content": '{"title":"报告","type":"flexible","estimatedDuration":120}'}}]
    }

def test_parse_text_to_task_monkeypatch(monkeypatch):
    monkeypatch.setattr(llm_service, "invoke_chat", fake_invoke_chat)
    task = llm_service.parse_text_to_task("明天下午做2小时报告", preference={})
    assert task["title"] == "报告"
    assert task["estimatedDuration"] == 120
```


