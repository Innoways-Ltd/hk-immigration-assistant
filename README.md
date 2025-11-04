# HK Immigration Assistant

An AI-powered Hong Kong immigration settlement assistant that helps new immigrants create personalized 30-day settlement plans through natural conversation.

## Features

- **One-Time Information Submission**: Users can provide all information in a single message
- **Intelligent Plan Generation**: AI automatically creates a 30-day settlement plan with 13 essential tasks
- **Map Visualization**: Interactive map showing service locations and route paths
- **Task Management**: Clear display of tasks grouped by phases with priorities and details
- **Real Data Integration**: Google Maps API for authentic Hong Kong locations

## Tech Stack

### Agent (Python)
- **Framework**: LangGraph + LangChain
- **LLM**: Azure OpenAI (gpt-4o)
- **APIs**: Google Maps API

### UI (Next.js)
- **Framework**: Next.js 14.2.5
- **UI Library**: CopilotKit React components
- **Map**: React-Leaflet + OpenStreetMap
- **Styling**: Tailwind CSS

## Project Structure

```
hk-immigration-assistant/
├── agent/                  # Python agent (LangGraph)
│   ├── immigration/        # Agent logic
│   │   ├── agent.py       # Workflow definition
│   │   ├── chat.py        # Chat node
│   │   ├── settlement.py  # Settlement plan generation
│   │   ├── search.py      # Location search
│   │   └── state.py       # State management
│   ├── pyproject.toml     # Python dependencies
│   └── .env               # Agent environment variables
├── ui/                    # Next.js UI
│   ├── app/               # Next.js app directory
│   ├── components/        # React components
│   ├── lib/               # Utilities and hooks
│   ├── package.json       # Node dependencies
│   └── .env               # UI environment variables
└── README.md
```

## Prerequisites

- Python 3.12+
- Node.js 22+
- Poetry (Python package manager)
- pnpm (Node package manager)
- Azure OpenAI API access
- Google Maps API key

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Innoways-Ltd/hk-immigration-assistant.git
cd hk-immigration-assistant
```

### 2. Setup Agent

```bash
cd agent

# Install dependencies
poetry install

# Create .env file
cat > .env << EOF
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
EOF

# Run agent
poetry run demo
```

The agent will start on `http://localhost:8000`

### 3. Setup UI

```bash
cd ui

# Install dependencies
pnpm install

# Create .env file
cat > .env << EOF
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview
REMOTE_ACTION_URL=http://localhost:8000/copilotkit
EOF

# Run UI
pnpm run dev
```

The UI will start on `http://localhost:3000`

## Deployment

### Deploy Agent

The agent needs to be deployed to a cloud server (AWS EC2, Azure VM, Google Cloud, etc.) to be accessible from the public internet.

#### Option 1: Docker Deployment

```bash
cd agent

# Build Docker image
docker build -t hk-immigration-agent .

# Run container
docker run -p 8000:8000 \
  -e AZURE_OPENAI_API_KEY=your_key \
  -e AZURE_OPENAI_ENDPOINT=your_endpoint \
  -e AZURE_OPENAI_DEPLOYMENT=gpt-4o \
  -e AZURE_OPENAI_API_VERSION=2025-01-01-preview \
  -e GOOGLE_MAPS_API_KEY=your_key \
  hk-immigration-agent
```

#### Option 2: Direct Deployment

1. SSH into your server
2. Install Python 3.12 and Poetry
3. Clone the repository
4. Follow the agent setup steps above
5. Use a process manager like `systemd` or `supervisor` to keep the agent running

### Deploy UI to Vercel

1. Push code to GitHub
2. Go to [Vercel](https://vercel.com)
3. Import your GitHub repository
4. Configure environment variables:
   - `AZURE_OPENAI_API_KEY`
   - `AZURE_OPENAI_ENDPOINT`
   - `AZURE_OPENAI_DEPLOYMENT`
   - `AZURE_OPENAI_API_VERSION`
   - `REMOTE_ACTION_URL` (your agent's public URL)
5. Deploy

## Environment Variables

### Agent (.env)

```bash
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

### UI (.env)

```bash
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview
REMOTE_ACTION_URL=http://localhost:8000/copilotkit
# For production, use your agent's public URL:
# REMOTE_ACTION_URL=https://your-agent-server.com/copilotkit
```

## Usage

1. Open the application in your browser
2. Provide all your information in one message:
   ```
   Hi! My name is David Chen. I'm arriving in Hong Kong on May 4th, 2025. 
   My office is at 3 Lockhart Road, Wan Chai. I need a 2-bedroom apartment 
   with a budget of HKD 65,000 per month, preferably in Wan Chai or Sheung 
   Wan area, within walking distance to my office. I'm moving alone, no 
   children. I'll need 30 days of temporary accommodation. Please create 
   my settlement plan.
   ```
3. AI will extract all information and generate a 30-day settlement plan
4. View tasks on the left card and locations on the map
5. Follow the blue route path to complete your settlement journey

## Settlement Plan Structure

The default plan includes 13 tasks across 4 phases:

### Phase 1: Arrival & Temporary Settlement (Day 1-3)
- Airport Pickup
- Check-in to Temporary Accommodation
- Purchase Octopus Card
- Get Mobile SIM Card

### Phase 2: Housing (Day 3-7)
- Property Viewing
- Sign Lease Agreement
- Setup Utilities

### Phase 3: Banking & Identity (Day 7-14)
- Open Bank Account
- Apply for Hong Kong Identity Card
- Register for Tax

### Phase 4: Work & Daily Life (Day 14-30)
- Visit Office Location
- Explore Neighborhood
- Register with Family Doctor

## Development

### Agent Development

```bash
cd agent
poetry shell
poetry run demo
```

### UI Development

```bash
cd ui
pnpm run dev
```

## Troubleshooting

### Agent won't start
- Check Python version (3.12+ required)
- Verify all environment variables are set
- Check Azure OpenAI API key is valid

### UI can't connect to agent
- Verify agent is running on port 8000
- Check `REMOTE_ACTION_URL` in UI .env file
- Ensure no firewall blocking port 8000

### Map not loading
- Check internet connection
- Verify OpenStreetMap tiles are accessible
- Check browser console for errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.

## Acknowledgments

- Built with [CopilotKit](https://github.com/CopilotKit/CopilotKit)
- Powered by Azure OpenAI
- Maps by OpenStreetMap
- Location data by Google Maps API
