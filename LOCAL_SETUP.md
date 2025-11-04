# 本地运行指南

## 前置要求

- Python 3.12+
- Node.js 22+
- Poetry (Python 包管理器)
- pnpm (Node 包管理器)

## 安装依赖工具

### 安装 Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 安装 pnpm

```bash
npm install -g pnpm
```

## 克隆仓库

```bash
git clone https://github.com/Innoways-Ltd/hk-immigration-assistant.git
cd hk-immigration-assistant
```

## 配置 Agent

### 1. 进入 agent 目录

```bash
cd agent
```

### 2. 安装依赖

```bash
poetry install
```

### 3. 创建 .env 文件

```bash
cat > .env << 'EOF'
AZURE_OPENAI_API_KEY=d897ab04012a4ea7824c10a48d323fcc
AZURE_OPENAI_ENDPOINT=https://innogpteastus.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview
GOOGLE_MAPS_API_KEY=AIzaSyAQ1jd5AN5FmZGhkkbYpRWEMzTGkz6278g
EOF
```

### 4. 运行 Agent

```bash
poetry run demo
```

Agent 将在 `http://localhost:8000` 启动

## 配置 UI

### 1. 打开新终端，进入 ui 目录

```bash
cd ui
```

### 2. 安装依赖

```bash
pnpm install
```

### 3. 创建 .env 文件

```bash
cat > .env << 'EOF'
AZURE_OPENAI_API_KEY=d897ab04012a4ea7824c10a48d323fcc
AZURE_OPENAI_ENDPOINT=https://innogpteastus.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview
REMOTE_ACTION_URL=http://localhost:8000/copilotkit
EOF
```

### 4. 运行 UI

```bash
pnpm run dev
```

UI 将在 `http://localhost:3000` 启动

## 访问应用

打开浏览器访问：`http://localhost:3000`

## 使用示例

在聊天框中输入：

```
Hi! My name is David Chen. I'm arriving in Hong Kong on May 4th, 2025. 
My office is at 3 Lockhart Road, Wan Chai. I need a 2-bedroom apartment 
with a budget of HKD 65,000 per month, preferably in Wan Chai or Sheung 
Wan area, within walking distance to my office. I'm moving alone, no 
children. I'll need 30 days of temporary accommodation. Please create 
my settlement plan.
```

AI 将自动生成 30 天安顿计划。

## 故障排除

### Agent 无法启动

- 检查 Python 版本：`python --version` (需要 3.12+)
- 检查 Poetry 是否安装：`poetry --version`
- 确认所有环境变量已设置

### UI 无法连接 Agent

- 确认 Agent 正在运行（访问 http://localhost:8000）
- 检查 UI 的 `.env` 文件中 `REMOTE_ACTION_URL` 是否正确
- 确认没有防火墙阻止端口 8000

### 地图无法加载

- 检查网络连接
- 确认浏览器控制台没有错误
- 尝试刷新页面

## 项目结构

```
hk-immigration-assistant/
├── agent/                  # Python Agent
│   ├── immigration/        # Agent 逻辑
│   └── .env               # Agent 环境变量
├── ui/                    # Next.js UI
│   ├── app/               # 页面
│   ├── components/        # 组件
│   └── .env               # UI 环境变量
└── README.md
```

## 下一步

- 查看 `README.md` 了解详细文档
- 查看 `FINAL_SUMMARY.md` 了解项目总结
- 查看 `OPTIMIZATION_SUMMARY.md` 了解优化细节
