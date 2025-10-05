### 07. 部署与运维

本节提供以 Docker 为主的部署方案，并给出环境变量、健康检查与日志建议。

### 目标

- 提供 Dockerfile 与 docker-compose.yml
- 环境变量 `.env.example`：端口、LLM 配置
- 健康检查与日志输出标准化（JSON 日志可选）

### 提示词（实现）

```
编写：
- Dockerfile：多阶段构建（基础镜像→安装依赖→复制代码→运行 uvicorn）
- docker-compose.yml：后端服务 + 静态前端（nginx 或任意静态容器）
- .env.example：LLM_PROVIDER、LLM_API_KEY、LLM_BASE_URL、PORT
给出启动命令与排障建议。
```

### 测试方法

- `docker compose up -d` 后访问 `/health`
- 查看容器日志，模拟错误环境变量并验证报错清晰

### 验收标准

- 容器可稳定运行；配置热切换（重启生效）；日志可检索。


