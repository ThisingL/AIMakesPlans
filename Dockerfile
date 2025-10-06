# ==================== 多阶段构建 ====================
# 阶段1: Python后端
# 使用官方镜像（配合Docker镜像加速器使用）
FROM python:3.11-slim as backend-builder

WORKDIR /app

# 使用国内pip镜像加速
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend ./backend
COPY .env.example ./.env

# ==================== 阶段2: 最终镜像 ====================
# 使用官方镜像（配合Docker镜像加速器使用）
FROM python:3.11-slim

WORKDIR /app

# 使用国内pip镜像（防止后续需要安装包）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 从builder复制已安装的包
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY backend ./backend
COPY frontend ./frontend

# 创建非root用户
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 启动后端
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

