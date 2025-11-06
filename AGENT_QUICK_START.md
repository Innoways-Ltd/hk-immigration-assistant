# Agent Server Quick Start Guide

## ✅ Issue Fixed!

The agent server import error has been fixed. You can now start the server successfully!

## Prerequisites

- Python 3.12+
- Poetry (Python package manager)

## Installation

### 1. Install Poetry (if not already installed)

```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="/home/user/.local/bin:$PATH"
```

### 2. Install Dependencies

```bash
cd agent
poetry install
```

This will install all required packages including:
- langgraph
- langchain-openai
- copilotkit
- fastapi
- uvicorn
- and more...

## Configuration

### Create Environment File

```bash
cd agent
cp ../.env.example .env
```

### Edit .env File

Open `.env` and configure the following:

```bash
# Required: Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_actual_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview

# Optional: Google Maps API
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# Server Configuration
PORT=8000
ENVIRONMENT=development
```

## Running the Server

### Development Mode (with auto-reload)

```bash
cd agent
poetry run demo
```

The server will start on `http://localhost:8000`

### Production Mode

```bash
cd agent
export ENVIRONMENT=production
poetry run demo
```

## Verify Server is Running

### Check Server Logs

You should see:
```
INFO:     Uvicorn running on http://localhost:8000 (Press CTRL+C to quit)
INFO:     Started server process [XXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Test CopilotKit Endpoint

```bash
curl http://localhost:8000/copilotkit
```

### Access in Browser

Open: http://localhost:8000/docs (FastAPI auto-generated documentation)

## Troubleshooting

### ImportError: cannot import name 'LangGraphAGUIAgent'

✅ **FIXED!** This issue has been resolved in the latest code.

If you still see this error, make sure you have pulled the latest changes:
```bash
git pull origin fix/agent-import-error
```

### Poetry not found

```bash
export PATH="/home/user/.local/bin:$PATH"
# Or add to your shell profile (.bashrc, .zshrc, etc.)
```

### Dependencies installation fails

```bash
# Clear poetry cache
poetry cache clear pypi --all
# Reinstall
poetry install
```

### Server won't start

1. Check Python version: `python3 --version` (must be 3.12+)
2. Verify `.env` file exists in `agent/` directory
3. Check if port 8000 is already in use: `lsof -i :8000`
4. Review error messages in console output

## API Endpoints

### CopilotKit Agent Endpoint
- **URL:** `http://localhost:8000/copilotkit`
- **Method:** POST
- **Description:** Main endpoint for CopilotKit integration

### Health Check (if implemented)
- **URL:** `http://localhost:8000/health`
- **Method:** GET

## Next Steps

1. ✅ Server is running successfully
2. Configure UI to connect to agent server
3. Test full application flow
4. Deploy to production (see DEPLOYMENT_GUIDE.md)

## Development Tips

### Running in Background

```bash
# Start server in background
cd agent
nohup poetry run demo > agent.log 2>&1 &

# Check logs
tail -f agent.log

# Stop server
pkill -f "poetry run demo"
```

### Using with Docker

```bash
cd agent
docker build -t hk-immigration-agent .
docker run -p 8000:8000 --env-file .env hk-immigration-agent
```

### Hot Reload

The development server automatically reloads when you change Python files in the `immigration/` directory.

## Project Structure

```
agent/
├── immigration/           # Main package
│   ├── agent.py          # Agent workflow definition
│   ├── demo.py           # Server entry point (FIXED!)
│   ├── chat.py           # Chat node
│   ├── settlement.py     # Settlement plan generation
│   ├── search.py         # Location search
│   └── state.py          # State management
├── pyproject.toml        # Dependencies
├── poetry.lock           # Lock file
└── .env                  # Configuration (create this!)
```

## Related Documentation

- **Main README:** ../README.md
- **Deployment Guide:** ../DEPLOYMENT_GUIDE.md
- **Fix Report:** ../AGENT_SERVER_FIX_REPORT.md
- **Testing Guide:** ../TESTING_GUIDE.md

## Support

If you encounter any issues:
1. Check the error logs
2. Review the AGENT_SERVER_FIX_REPORT.md
3. Open an issue on GitHub
4. Contact the development team

---

**Status:** ✅ Ready for development  
**Last Updated:** 2025-11-06  
**Fix PR:** https://github.com/Innoways-Ltd/hk-immigration-assistant/pull/1
