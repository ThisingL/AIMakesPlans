# AIMakesPlans - 部署指南

本文档详细说明如何将AIMakesPlans部署到阿里云服务器的Docker环境中。

---

## 📋 前提条件

### 阿里云服务器要求
- ✅ 操作系统：Ubuntu 20.04+ / CentOS 7+
- ✅ 内存：至少2GB（推荐4GB）
- ✅ 磁盘：至少10GB可用空间
- ✅ 已安装Docker和Docker Compose
- ✅ 已开放端口：8000（后端）、3000或80（前端）

### 本地准备

- ✅ 项目代码
- ✅ SiliconFlow API Key

---

## 🚀 部署步骤

### 方案A：Docker Compose部署（推荐）⭐

#### 步骤1：准备服务器

**1.1 连接到服务器**
```bash
ssh root@your-server-ip
```

**1.2 安装Docker（如果还没安装）**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 启动Docker
sudo systemctl start docker
sudo systemctl enable docker

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

**1.3 配置Docker镜像加速器（重要！中国大陆必须）**

由于访问Docker Hub很慢，需要配置国内镜像：

```bash
# 创建配置文件
sudo mkdir -p /etc/docker
sudo nano /etc/docker/daemon.json
```

添加以下内容（已验证可用的镜像源）：
```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://mirror.baidubce.com",
    "https://dockerproxy.com",
    "https://docker.mirrors.ustc.edu.cn"
  ]
}
```

**如果有阿里云账号（推荐，速度更快）：**
1. 登录 https://cr.console.aliyun.com/
2. 左侧菜单 → 镜像工具 → 镜像加速器
3. 复制你的专属加速地址，例如：
```json
{
  "registry-mirrors": ["https://xxxxx.mirror.aliyuncs.com"]
}
```

**重启Docker使配置生效：**
```bash
sudo systemctl daemon-reload
sudo systemctl restart docker

# 验证配置
docker info | grep -A 5 "Registry Mirrors"
# 应该显示配置的镜像地址
```

#### 步骤2：上传项目代码

**2.1 在服务器创建项目目录**
```bash
mkdir -p /opt/aimakesplans
cd /opt/aimakesplans
```

**2.2 上传代码（从本地）**

**方式A：使用Git（推荐）**
```bash
# 在服务器上
git clone https://github.com/yourusername/AIMakesPlans.git .
```

**方式B：使用scp上传**
```bash
# 在本地（Windows PowerShell）
cd C:\Users\god\Desktop\projects\AIMakesPlans
scp -r * root@your-server-ip:/opt/aimakesplans/
```

**方式C：使用SFTP工具**
- 使用FileZilla、WinSCP等工具
- 上传整个项目文件夹到服务器

#### 步骤3：配置环境变量

**3.1 创建.env文件**
```bash
cd /opt/aimakesplans
nano .env
```

**3.2 填入以下内容**
```env
# LLM Provider Configuration
LLM_PROVIDER=siliconflow
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
LLM_BASE_URL=https://api.siliconflow.cn/v1
MAX_TOKENS=4096

# API Key - 填入你的真实API Key
OPENAI_API_KEY=sk-your-actual-api-key-here

# Embedding Model
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5

# Server Configuration
PORT=8000
HOST=0.0.0.0

# Priority Policy
PRIORITY_POLICY=eisenhower
```

保存并退出（Ctrl+X, Y, Enter）

#### 步骤4：启动服务

**4.1 构建并启动容器**
```bash
cd /opt/aimakesplans
docker-compose up -d --build
```

**4.2 查看启动状态**

```bash
# 查看容器状态
docker-compose ps

# 应该看到：
# NAME                     STATUS
# aimakesplans-backend     Up (healthy)
# aimakesplans-frontend    Up (healthy)

# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

#### 步骤5：验证部署

**5.1 测试后端API**
```bash
curl http://localhost:8000/health
# 应该返回: {"status":"ok",...}
```

**5.2 测试前端**
```bash
curl http://localhost:3000
# 应该返回HTML内容
```

**5.3 在浏览器访问**
```
http://your-server-ip:8000/docs  # API文档
http://your-server-ip:3000       # 前端界面
```

---

### 方案B：使用Nginx反向代理（生产推荐）⭐⭐

如果你想使用域名访问，或者需要HTTPS，建议配置Nginx。

#### 步骤1：修改docker-compose.yml端口

将前端端口改为内部端口：
```yaml
frontend:
  ports:
    - "127.0.0.1:3000:80"  # 只在本地监听
```

后端也改为内部：
```yaml
backend:
  ports:
    - "127.0.0.1:8000:8000"
```

#### 步骤2：安装Nginx（在宿主机）

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx -y

# 启动Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

#### 步骤3：配置Nginx

**3.1 创建配置文件**
```bash
sudo nano /etc/nginx/sites-available/aimakesplans
```

**3.2 填入以下配置**
```nginx
server {
    listen 80;
    server_name your-domain.com;  # 改成你的域名或IP
    
    client_max_body_size 20M;
    
    # 前端静态文件
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 后端API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置（LLM调用可能需要更长时间）
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 直接访问API文档
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_set_header Host $host;
    }
    
    location /redoc {
        proxy_pass http://localhost:8000/redoc;
        proxy_set_header Host $host;
    }
}
```

**3.3 启用配置**
```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/aimakesplans /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

#### 步骤4：配置防火墙

```bash
# Ubuntu UFW
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload

# CentOS Firewalld
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

#### 步骤5：配置HTTPS（可选但推荐）

使用Let's Encrypt免费证书：

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx -y

# 自动配置HTTPS
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## 🔄 前端API地址配置

**重要：** 如果使用Nginx代理，需要修改前端的API地址：

### 选项1：使用相对路径（推荐）

修改 `frontend/web/app.js`：
```javascript
// 开发环境
// const API_BASE_URL = 'http://127.0.0.1:8000';

// 生产环境（通过Nginx代理）
const API_BASE_URL = '/api';  // 使用相对路径
```

### 选项2：使用环境变量

创建 `frontend/web/config.js`：
```javascript
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://127.0.0.1:8000'  // 本地开发
    : '/api';                   // 生产环境
```

---

## 📦 完整部署架构

### 架构图

```
                    Internet
                       ↓
                  Nginx (80/443)
                       ↓
        ┌──────────────┴──────────────┐
        ↓                             ↓
   Frontend容器                  Backend容器
   (nginx:alpine)              (python:3.11)
   端口: 3000                   端口: 8000
        ↓                             ↓
    静态文件                      FastAPI应用
    (HTML/CSS/JS)                    ↓
                                  LLM API
                              (SiliconFlow)
```

### 不配置Nginx的情况（方案A）

```
Internet → 服务器IP:3000（前端）
         → 服务器IP:8000（后端API）

优点：简单直接
缺点：
  - 需要开放多个端口
  - 无HTTPS
  - 无域名支持
  - 前端需要跨域访问后端
```

### 配置Nginx的情况（方案B - 推荐）

```
Internet → 域名（或IP）:80/443
         → Nginx反向代理
            ├─ / → 前端容器:3000
            └─ /api/ → 后端容器:8000

优点：
  ✅ 统一入口（只需开放80/443）
  ✅ 支持HTTPS
  ✅ 支持域名
  ✅ 无跨域问题
  ✅ 可以做负载均衡
  ✅ 可以缓存静态资源
```

---

## 🛠️ 常用操作命令

### Docker Compose命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f frontend

# 重新构建
docker-compose up -d --build

# 查看状态
docker-compose ps

# 进入容器
docker-compose exec backend bash
docker-compose exec frontend sh
```

### 更新部署

```bash
# 1. 拉取最新代码
cd /opt/aimakesplans
git pull

# 2. 重新构建和启动
docker-compose down
docker-compose up -d --build

# 3. 查看日志确认
docker-compose logs -f
```

---

## 🔍 故障排除

### 问题1：容器无法启动

**检查日志：**
```bash
docker-compose logs backend
```

**常见原因：**
- .env文件未配置或API Key错误
- 端口被占用
- 内存不足

**解决：**
```bash
# 检查端口占用
sudo netstat -tlnp | grep 8000
sudo netstat -tlnp | grep 3000

# 释放端口或修改docker-compose.yml中的端口
```

### 问题2：无法访问API

**检查：**
```bash
# 容器内测试
docker-compose exec backend curl http://localhost:8000/health

# 宿主机测试
curl http://localhost:8000/health

# 外部测试
curl http://your-server-ip:8000/health
```

**如果容器内能访问，外部不能：**
- 检查防火墙配置
- 检查阿里云安全组规则（开放8000端口）

### 问题3：前端无法调用后端

**症状：** 前端页面显示"API连接失败"

**原因：** CORS或网络问题

**解决：**
```bash
# 方案1：使用Nginx代理（推荐）
# 按照上面的Nginx配置操作

# 方案2：修改前端API地址
# 将 app.js 中的 localhost 改为服务器IP
const API_BASE_URL = 'http://your-server-ip:8000';
```

### 问题4：Nginx配置错误

**测试配置：**
```bash
sudo nginx -t
```

**查看错误日志：**
```bash
sudo tail -f /var/log/nginx/error.log
```

---

## 🔒 安全建议

### 1. 使用HTTPS

```bash
# 使用Certbot自动配置
sudo certbot --nginx -d your-domain.com
```

### 2. 限制访问

在Nginx配置中添加IP白名单（可选）：
```nginx
location / {
    allow 1.2.3.4;      # 你的IP
    deny all;           # 拒绝其他
    # ... 其他配置
}
```

### 3. API速率限制

```nginx
# 在http块中
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

# 在location块中
location /api/ {
    limit_req zone=api_limit burst=20;
    # ... 其他配置
}
```

### 4. 定期更新

```bash
# 定期拉取更新
cd /opt/aimakesplans
git pull
docker-compose up -d --build
```

---

## 📊 监控和日志

### 查看资源使用

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
docker system df
```

### 日志管理

```bash
# 限制日志大小（在docker-compose.yml中）
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 健康检查

```bash
# 检查容器健康状态
docker-compose ps

# 手动健康检查
curl http://localhost:8000/health
```

---

## 🎯 完整部署清单

### 最简部署（不用Nginx）

```bash
# 1. 上传代码
scp -r AIMakesPlans root@server:/opt/

# 2. 配置.env
nano /opt/AIMakesPlans/.env

# 3. 启动
cd /opt/AIMakesPlans
docker-compose up -d

# 4. 开放端口（阿里云安全组）
开放: 8000, 3000

# 5. 访问
http://server-ip:3000
```

### 完整部署（使用Nginx + HTTPS）

```bash
# 1. 上传代码
git clone ... 或 scp

# 2. 配置.env
nano .env

# 3. 修改docker-compose.yml端口为内部
ports:
  - "127.0.0.1:8000:8000"
  - "127.0.0.1:3000:80"

# 4. 启动容器
docker-compose up -d --build

# 5. 安装配置Nginx
sudo apt install nginx
sudo nano /etc/nginx/sites-available/aimakesplans
# 粘贴上面的Nginx配置

# 6. 启用配置
sudo ln -s /etc/nginx/sites-available/aimakesplans /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 7. 配置HTTPS
sudo certbot --nginx -d your-domain.com

# 8. 开放端口
开放: 80, 443

# 9. 访问
https://your-domain.com
```

---

## ❓ FAQ

### Q: 需要配置Nginx吗？

**答：看情况**

**不需要Nginx的场景：**
- 只是个人使用
- 可以接受IP:端口的访问方式
- 不需要HTTPS

**需要Nginx的场景：**
- 想用域名访问
- 需要HTTPS加密
- 需要统一入口
- 需要负载均衡
- 生产环境部署

### Q: 前端的API地址需要改吗？

**答：需要**

如果使用Nginx代理，修改 `frontend/web/app.js`：
```javascript
const API_BASE_URL = '/api';  // 通过Nginx代理
```

如果不用Nginx：
```javascript
const API_BASE_URL = 'http://your-server-ip:8000';  // 直接访问
```

### Q: 数据会丢失吗？

**答：当前会**

目前使用内存存储，容器重启后数据会丢失。

**解决方案（v0.2计划实现）：**
1. 添加Volume持久化
2. 使用SQLite或PostgreSQL
3. 定期备份

**临时方案：**
```yaml
# 在docker-compose.yml中添加
volumes:
  - ./data:/app/data
```

### Q: 如何查看日志？

```bash
# 实时日志
docker-compose logs -f

# 最近100行
docker-compose logs --tail=100

# 特定服务
docker-compose logs -f backend
```

---

## 🎉 部署成功检查清单

- [ ] Docker容器正常运行（docker-compose ps显示healthy）
- [ ] 后端API可访问（curl /health返回ok）
- [ ] 前端页面可打开
- [ ] API文档可访问（/docs）
- [ ] 前端能调用后端API（检查Console无错误）
- [ ] 任务创建功能正常
- [ ] AI解析功能正常（需要API Key正确）
- [ ] 调度功能正常

**全部✓后，部署成功！** 🚀

---

## 📞 需要帮助？

- 查看日志：`docker-compose logs -f`
- 重启服务：`docker-compose restart`
- 完全重建：`docker-compose down && docker-compose up -d --build`

**遇到问题欢迎提Issue！**

