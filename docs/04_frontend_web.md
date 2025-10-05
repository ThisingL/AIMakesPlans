### 04. 前端 Web 最小实现与对接

本节将用最小原生 Web（或任意微型框架）对接后端 API，支持自然语言解析与结果展示。

### 目标

- 输入自然语言 → 调用 `/v1/parse` → 展示结构化结果
- 展示规划方案与冲突提示（调用 `/v1/schedule/plan`）
- 提供最小周视图（可先用简单表格表示时间块）

### 文件建议

```
frontend/web/index.html
frontend/web/app.js
frontend/web/styles.css
```

### 提示词（实现）

```
实现最小前端：
- index.html：输入框、按钮、结果区域
- app.js：fetch('/health')、POST /v1/parse、POST /v1/schedule/plan；处理 JSON 显示
- styles.css：基础布局
请给出：本地运行方式（任意静态服务器），以及失败时的错误提示策略。
```

### 测试方法

- 启动后端，打开 `index.html`
- 输入“明天下午做2小时报告” → 能展示解析后的字段
- 模拟错误：网络断开/后端 4xx，前端显示清晰的错误文案

### 验收标准

- 正常/异常路径均有可视反馈；可与后端核心接口打通。


