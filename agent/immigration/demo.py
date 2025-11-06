"""Hong Kong Immigration Settlement Assistant Server"""

import os
import logging
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from fastapi import FastAPI
import uvicorn
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from copilotkit import CopilotKitRemoteEndpoint, LangGraphAgent
from immigration.agent import graph


app = FastAPI()
sdk = CopilotKitRemoteEndpoint(
    agents=[
        LangGraphAgent(
            name="immigration",
            description="Helps new immigrants settle into Hong Kong by creating personalized settlement plans.",
            graph=graph,
        )
    ],
)

add_fastapi_endpoint(app, sdk, "/copilotkit")

def main():
    """Run the uvicorn server."""
    port = int(os.getenv("PORT", "8000"))
    # Check if running in production (no reload)
    is_production = os.getenv("ENVIRONMENT", "development") == "production"

    if is_production:
        # Production mode: bind to 0.0.0.0, no reload
        uvicorn.run(
            "immigration.demo:app",
            host="0.0.0.0",
            port=port,
            reload=False
        )
    else:
        # Development mode
        uvicorn.run(
            "immigration.demo:app",
            host="localhost",
            port=port,
            reload=True,
            reload_dirs=(
                ["."] +
                (["../../../sdk-python/copilotkit"]
                 if os.path.exists("../../../sdk-python/copilotkit")
                 else []
                 )
            )
        )

if __name__ == "__main__":
    main()
