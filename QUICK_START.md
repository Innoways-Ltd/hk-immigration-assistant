# 🚀 快速开始 - HK Immigration Assistant

## 5分钟快速部署

### 步骤1：克隆仓库
```bash
git clone https://github.com/Innoways-Ltd/hk-immigration-assistant.git
cd hk-immigration-assistant
```

### 步骤2：配置API密钥
```bash
cp .env.example .env
nano .env  # 填入你的API密钥
```

**必需配置：**
```bash
AZURE_OPENAI_API_KEY=你的Azure_OpenAI密钥
AZURE_OPENAI_ENDPOINT=https://你的资源名.openai.azure.com
GOOGLE_MAPS_API_KEY=你的Google_Maps密钥
```

### 步骤3：一键部署
```bash
./deploy.sh
```

### 步骤4：访问应用
- **前端**: http://localhost:3000
- **后端API**: http://localhost:8000/docs

---

## 停止服务
```bash
./stop.sh
```

---

## 需要帮助？

查看完整文档：
- **部署指南**: [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- **测试指南**: [TESTING_GUIDE.md](./TESTING_GUIDE.md)
- **实现文档**: [CORE_EXTENDED_TASKS_IMPLEMENTATION.md](./CORE_EXTENDED_TASKS_IMPLEMENTATION.md)

---

## 系统要求

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM
- 20GB 磁盘空间

---

## 功能特性

✅ **核心任务**（⭐）- 必需完成的任务  
✅ **扩展任务**（💡）- AI智能推荐的便利活动  
✅ **地图可视化** - 交互式地图显示位置  
✅ **路线优化** - 智能规划每日行程  
✅ **个性化推荐** - 基于用户画像定制建议  

---

祝使用愉快！🎉
