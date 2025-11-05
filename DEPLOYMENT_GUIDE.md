# HK Immigration Assistant - 生产环境部署指南

本指南提供完整的生产环境部署步骤，包括Docker部署、云服务器部署和Vercel部署。

---

## 📋 目录

1. [部署概述](#部署概述)
2. [前置要求](#前置要求)
3. [快速部署（Docker）](#快速部署docker)
4. [云服务器部署](#云服务器部署)
5. [Vercel部署（前端）](#vercel部署前端)
6. [环境变量配置](#环境变量配置)
7. [监控和维护](#监控和维护)
8. [故障排除](#故障排除)

---

## 部署概述

HK Immigration Assistant 由两个主要组件组成：

1. **后端Agent（Python）** - LangGraph + FastAPI，端口8000
2. **前端UI（Next.js）** - React应用，端口3000

### 架构图

```
┌─────────────┐      ┌─────────────┐      ┌──────────────┐
│   用户      │ ───> │  前端 UI    │ ───> │  后端 Agent  │
│  (浏览器)   │      │  (Next.js)  │      │  (FastAPI)   │
└─────────────┘      └─────────────┘      └──────────────┘
                            │                     │
                            ├─────────────────────┤
                            │                     │
                     ┌──────▼──────┐      ┌──────▼──────┐
                     │ Azure OpenAI│      │ Google Maps │
                     │     API     │      │     API     │
                     └─────────────┘      └─────────────┘
```

---

## 前置要求

### 必需软件
- **Docker** 20.10+ 和 **Docker Compose** 2.0+
- **Git** 2.30+
- **curl** 或 **wget**

### 必需API密钥
1. **Azure OpenAI API**
   - 获取地址：https://portal.azure.com
   - 需要：API Key, Endpoint, Deployment Name
   
2. **Google Maps API**
   - 获取地址：https://console.cloud.google.com
   - 需要启用：Maps JavaScript API, Places API, Geocoding API

### 服务器要求（生产环境）
- **CPU**: 2核心以上
- **内存**: 4GB以上
- **存储**: 20GB以上
- **操作系统**: Ubuntu 22.04 LTS（推荐）或其他Linux发行版
- **网络**: 公网IP和域名（可选）

---

## 快速部署（Docker）

### 步骤1：克隆仓库

```bash
git clone https://github.com/Innoways-Ltd/hk-immigration-assistant.git
cd hk-immigration-assistant
```

### 步骤2：配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入你的API密钥
nano .env  # 或使用 vim, vi 等编辑器
```

**必需配置：**
```bash
AZURE_OPENAI_API_KEY=your_actual_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview
GOOGLE_MAPS_API_KEY=your_actual_google_maps_key_here
```

### 步骤3：运行部署脚本

```bash
# 赋予执行权限（如果需要）
chmod +x deploy.sh

# 运行部署
./deploy.sh
```

部署脚本会自动：
1. ✅ 检查前置条件
2. ✅ 验证环境变量
3. ✅ 构建Docker镜像
4. ✅ 启动服务
5. ✅ 健康检查
6. ✅ 显示状态

### 步骤4：验证部署

部署成功后，访问：
- **后端API文档**: http://localhost:8000/docs
- **前端应用**: http://localhost:3000

### 步骤5：停止服务

```bash
./stop.sh
```

---

## 云服务器部署

### 选项1：AWS EC2

#### 1. 创建EC2实例

```bash
# 推荐配置
- AMI: Ubuntu Server 22.04 LTS
- Instance Type: t3.medium (2 vCPU, 4GB RAM)
- Storage: 20GB gp3
- Security Group: 开放端口 22 (SSH), 80 (HTTP), 443 (HTTPS), 8000, 3000
```

#### 2. 连接到EC2实例

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

#### 3. 安装Docker

```bash
# 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 添加用户到docker组
sudo usermod -aG docker $USER
newgrp docker
```

#### 4. 部署应用

```bash
# 克隆仓库
git clone https://github.com/Innoways-Ltd/hk-immigration-assistant.git
cd hk-immigration-assistant

# 配置环境变量
cp .env.example .env
nano .env  # 填入API密钥

# 部署
./deploy.sh
```

#### 5. 配置Nginx反向代理（可选）

```bash
# 安装Nginx
sudo apt-get install nginx -y

# 创建Nginx配置
sudo nano /etc/nginx/sites-available/hk-immigration
```

**Nginx配置内容：**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # 后端API
    location /copilotkit {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /docs {
        proxy_pass http://localhost:8000;
    }
}
```

```bash
# 启用配置
sudo ln -s /etc/nginx/sites-available/hk-immigration /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. 配置SSL（推荐）

```bash
# 安装Certbot
sudo apt-get install certbot python3-certbot-nginx -y

# 获取SSL证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 选项2：Azure VM

类似AWS EC2的步骤，使用Azure Portal创建虚拟机。

### 选项3：Google Cloud Platform

类似AWS EC2的步骤，使用GCP Console创建Compute Engine实例。

---

## Vercel部署（前端）

Vercel是部署Next.js应用的最佳选择，提供免费的托管服务。

### 步骤1：准备后端

首先确保后端已部署到云服务器并可公网访问。

### 步骤2：推送代码到GitHub

```bash
git add .
git commit -m "Ready for Vercel deployment"
git push origin master
```

### 步骤3：在Vercel上部署

1. 访问 https://vercel.com 并登录
2. 点击 "New Project"
3. 导入你的GitHub仓库
4. 配置项目：
   - **Framework Preset**: Next.js
   - **Root Directory**: `ui`
   - **Build Command**: `pnpm run build`
   - **Output Directory**: `.next`

### 步骤4：配置环境变量

在Vercel项目设置中添加：

```
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview
REMOTE_ACTION_URL=https://your-backend-domain.com/copilotkit
NEXT_PUBLIC_AGENT_URL=https://your-backend-domain.com
```

### 步骤5：部署

点击 "Deploy" 按钮，Vercel会自动构建和部署。

### 步骤6：配置自定义域名（可选）

在Vercel项目设置中添加自定义域名。

---

## 环境变量配置

### 完整环境变量列表

| 变量名 | 必需 | 说明 | 示例 |
|--------|------|------|------|
| `AZURE_OPENAI_API_KEY` | ✅ | Azure OpenAI API密钥 | `abc123...` |
| `AZURE_OPENAI_ENDPOINT` | ✅ | Azure OpenAI端点 | `https://xxx.openai.azure.com` |
| `AZURE_OPENAI_DEPLOYMENT` | ✅ | 部署名称 | `gpt-4o` |
| `AZURE_OPENAI_API_VERSION` | ✅ | API版本 | `2025-01-01-preview` |
| `GOOGLE_MAPS_API_KEY` | ✅ | Google Maps API密钥 | `AIza...` |
| `REMOTE_ACTION_URL` | ✅ | 后端API地址（前端用） | `http://localhost:8000/copilotkit` |
| `NEXT_PUBLIC_AGENT_URL` | ⚠️ | 公开的后端地址 | `https://api.example.com` |

### 安全建议

1. **不要提交.env文件到Git**
   - 已在.gitignore中排除
   - 使用.env.example作为模板

2. **使用环境变量管理工具**
   - AWS: Secrets Manager
   - Azure: Key Vault
   - GCP: Secret Manager

3. **定期轮换API密钥**

4. **限制API密钥权限**
   - Google Maps: 限制HTTP referrer
   - Azure OpenAI: 使用Azure AD认证

---

## 监控和维护

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看后端日志
docker logs -f hk-immigration-agent

# 查看前端日志
docker logs -f hk-immigration-ui
```

### 健康检查

```bash
# 检查后端健康
curl http://localhost:8000/docs

# 检查前端健康
curl http://localhost:3000
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启单个服务
docker-compose restart agent
docker-compose restart ui
```

### 更新应用

```bash
# 拉取最新代码
git pull origin master

# 重新构建和部署
./deploy.sh
```

### 备份数据

```bash
# 备份环境变量
cp .env .env.backup

# 备份Docker卷（如果有）
docker run --rm -v hk-immigration-assistant_agent-data:/data -v $(pwd):/backup ubuntu tar czf /backup/agent-data-backup.tar.gz /data
```

---

## 故障排除

### 问题1：后端无法启动

**症状：** `docker logs hk-immigration-agent` 显示错误

**可能原因：**
1. 环境变量未设置或错误
2. Azure OpenAI API密钥无效
3. 端口8000被占用

**解决方案：**
```bash
# 检查环境变量
docker exec hk-immigration-agent env | grep AZURE

# 检查端口占用
sudo lsof -i :8000

# 重新部署
./stop.sh
./deploy.sh
```

### 问题2：前端无法连接后端

**症状：** 前端显示连接错误

**可能原因：**
1. `REMOTE_ACTION_URL` 配置错误
2. 后端未启动
3. 网络问题

**解决方案：**
```bash
# 检查后端是否运行
curl http://localhost:8000/docs

# 检查前端环境变量
docker exec hk-immigration-ui env | grep REMOTE_ACTION_URL

# 重启前端
docker-compose restart ui
```

### 问题3：Docker镜像构建失败

**症状：** `./deploy.sh` 在构建阶段失败

**可能原因：**
1. 依赖下载失败
2. 磁盘空间不足
3. 网络问题

**解决方案：**
```bash
# 清理Docker缓存
docker system prune -a

# 检查磁盘空间
df -h

# 手动构建
cd agent
docker build -t hk-immigration-agent .

cd ../ui
docker build -t hk-immigration-ui .
```

### 问题4：扩展任务未生成

**症状：** 只有核心任务，没有扩展任务

**可能原因：**
1. Overpass API访问失败
2. 地理位置信息缺失
3. 相关性评分低于阈值

**解决方案：**
```bash
# 查看后端日志
docker logs hk-immigration-agent | grep -i "extended"

# 检查网络连接
docker exec hk-immigration-agent curl -I https://overpass-api.de/api/interpreter

# 降低评分阈值（开发环境）
# 编辑 agent/immigration/nearby_services.py
# 将 if score >= 0.6 改为 if score >= 0.4
```

### 问题5：性能问题

**症状：** 任务生成速度慢

**可能原因：**
1. API响应慢
2. 资源不足
3. 网络延迟

**解决方案：**
```bash
# 检查容器资源使用
docker stats

# 增加Docker资源限制
# 编辑 docker-compose.yml，添加：
# resources:
#   limits:
#     cpus: '2'
#     memory: 4G

# 启用缓存（未来功能）
```

---

## 生产环境最佳实践

### 1. 安全性

- ✅ 使用HTTPS（SSL/TLS）
- ✅ 配置防火墙规则
- ✅ 定期更新依赖
- ✅ 使用非root用户运行容器
- ✅ 限制API密钥权限

### 2. 可靠性

- ✅ 配置健康检查
- ✅ 使用自动重启策略
- ✅ 设置日志轮转
- ✅ 配置监控告警
- ✅ 定期备份

### 3. 性能

- ✅ 使用CDN加速静态资源
- ✅ 启用Gzip压缩
- ✅ 配置缓存策略
- ✅ 优化Docker镜像大小
- ✅ 使用生产级数据库（未来）

### 4. 可维护性

- ✅ 使用版本标签
- ✅ 编写详细的文档
- ✅ 配置CI/CD流程
- ✅ 定期代码审查
- ✅ 监控和日志分析

---

## 附录

### A. 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
./stop.sh

# 启动服务
./deploy.sh

# 进入容器
docker exec -it hk-immigration-agent bash
docker exec -it hk-immigration-ui sh

# 清理资源
docker-compose down -v
docker system prune -a
```

### B. 目录结构

```
hk-immigration-assistant/
├── agent/                          # 后端代码
│   ├── immigration/                # 核心逻辑
│   │   ├── agent.py
│   │   ├── settlement.py
│   │   ├── task_generator.py
│   │   ├── extended_task_generator.py
│   │   ├── nearby_services.py
│   │   ├── overpass_service.py
│   │   └── ...
│   ├── Dockerfile                  # 后端Docker配置
│   ├── .dockerignore
│   └── pyproject.toml
├── ui/                             # 前端代码
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── Dockerfile                  # 前端Docker配置
│   ├── .dockerignore
│   └── package.json
├── docker-compose.yml              # Docker Compose配置
├── .env.example                    # 环境变量模板
├── deploy.sh                       # 部署脚本
├── stop.sh                         # 停止脚本
├── DEPLOYMENT_GUIDE.md             # 本文档
├── CORE_EXTENDED_TASKS_IMPLEMENTATION.md
├── TESTING_GUIDE.md
└── TEST_REPORT.md
```

### C. 支持和帮助

- **GitHub Issues**: https://github.com/Innoways-Ltd/hk-immigration-assistant/issues
- **文档**: 查看项目README.md和其他文档
- **社区**: 欢迎提交PR和反馈

---

## 总结

本指南涵盖了HK Immigration Assistant的完整部署流程。按照步骤操作，您应该能够成功部署到生产环境。

**快速开始：**
1. 克隆仓库
2. 配置.env文件
3. 运行 `./deploy.sh`
4. 访问 http://localhost:3000

**生产部署：**
1. 部署后端到云服务器
2. 配置Nginx和SSL
3. 部署前端到Vercel
4. 配置监控和备份

祝部署顺利！🚀
