### 06. 测试策略与 CI 流水线

本节定义测试金字塔与 GitHub Actions 配置，确保每步实现都有可靠的验证手段。

### 测试分层

- 单元测试（pytest）：模型校验、算法纯函数（冲突、调度）、LLM 封装（mock）
- 集成测试：API 级测试（TestClient/httpx），覆盖解析与调度主链路
- 端到端（可选）：前端 UI 测试（Playwright/Cypress）

### 覆盖率

- 使用 `coverage.py` 或 `pytest-cov`，目标 ≥ 70%（逐步提升）

### 提示词（CI 配置）

```
在 .github/workflows/ci.yml 中：
- 触发：push, pull_request
- 步骤：checkout → setup-python → 安装依赖 → 运行 pytest → （可选）上传覆盖率
- 缓存 pip 依赖以加速
```

### 本地与 CI 的一致性

- `requirements.txt/poetry.lock` 固定版本
- 测试使用 mock，避免网络依赖

### 验收标准

- 本地与 CI 均可一键通过测试；PR 必须绿。


