### AI 日程系统 - 实施文档索引与使用说明

本目录包含以“提示词驱动开发”的实施步骤、测试方法与验收标准。所有文档均为中文，并在每个阶段给出可直接复制使用的提示词与测试方案。

### 阅读顺序

1. `00_overview_and_prompts.md`：总览、通用提示词模板与任务拆解
2. `01_backend_api.md`：Python 后端（FastAPI）API 设计与实现提示词（含测试）✅ 已完成
3. `02_llm_service_and_prompt_engineering.md`：LLM 调用封装与提示词工程（含测试）✅ 已完成
4. `03_scheduling_and_conflicts.md`：解析、冲突检测与调度算法（含测试）✅ 已完成
5. `04_frontend_web.md`：Web 前端实现与对接（含测试）✅ 已完成
6. `05_preferences_priority_status.md`：用户偏好、优先级策略与动态状态/休息模式 ✅ 已完成
7. `06_ics_integration.md`：ICS 导入/导出与日历兼容（含测试）⏳ 待实现
8. `07_deploy_and_ops.md`：部署与运维（Docker/Compose/环境变量/监控）⏳ 待实现
9. `08_testing_and_ci.md`：测试策略、覆盖率与 CI 流水线 ✅ 已有基础测试

### 如何使用这些提示词与步骤

- 每个文档的步骤都包含“提示词”与“测试方法”。请按照顺序逐步执行。
- 将提示词粘贴到你的 LLM（如 Cursor/ChatGPT/Claude）中，让其生成/修改代码；完成后立刻按“测试方法”验证。
- 若测试失败：保留失败日志，使用文档中的“调试提示词”进行增量修复。
- 每次通过一个里程碑测试后进行提交（建议使用 Git 分支与 PR 流程）。

### 测试总览

- 单元测试：以 `pytest` 为主，后端用 `fastapi.TestClient/httpx` 进行 API 测试；算法模块提供纯函数单测。
- 集成测试：覆盖“自然语言解析 → 任务建模 → 冲突检测 → 调度 → 可视化”主链路。
- 端到端测试（可选）：前端使用 Playwright/Cypress；在 CI 中最少保留 1 条核心用例。

### 目录约定

- 后端：`backend/`，前端：`frontend/`，公共协议与示例：`contracts/`，测试：各模块内建 `tests/` 目录。
- 环境配置：根目录 `.env.example`；CI 配置：`.github/workflows/`。

更多细节请进入每个子文档查看。


