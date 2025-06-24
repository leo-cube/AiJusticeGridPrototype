import sys
import uvicorn
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware import Middleware
from contextlib import asynccontextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Unified server configuration
UNIFIED_PORT = 9000

# Agent configurations - now all run on unified server
AGENTS = {
    "murder": {
        "app_module": "app",
        "app_name": "app",
        "title": "Murder Agent API",
        "description": "AI-powered murder investigation analysis system",
        "prefix": "/api/murder"
    },
    "cybercrime": {
        "app_module": "cybercrime",
        "app_name": "app",
        "title": "Cybercrime Agent API",
        "description": "AI-powered cybercrime investigation analysis system",
        "prefix": "/api/cyber"
    }
    # Add more agents here in the future
}

class UnifiedAgentServer:
    def __init__(self):
        self.app = FastAPI(
            title="AI Justice Grid - Unified Multi-Agent System",
            description="Unified server for multiple AI investigation agents",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.setup_unified_routes()

    def setup_unified_routes(self):
        """Setup unified routes for all agents"""
        import importlib

        @self.app.get("/")
        async def root():
            return {
                "message": "AI Justice Grid - Unified Multi-Agent Investigation System",
                "agents": list(AGENTS.keys()),
                "endpoints": {
                    agent: config["prefix"] for agent, config in AGENTS.items()
                }
            }

        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "agents": list(AGENTS.keys()),
                "message": "All agents operational on unified server",
                "endpoints": [
                    "/",
                    "/health",
                    "/api/murder",
                    "/api/murder/download-pdf",
                    "/api/cyber",
                    "/api/cyber/download-pdf",
                    "/docs",
                    "/redoc"
                ]
            }

        # Import and include agent routes
        self.include_agent_routes()

    def include_agent_routes(self):
        """Include routes from all agent modules"""
        try:
            # Import murder agent routes
            from app import app as murder_app
            from app import murder_agent_endpoint, download_murder_pdf

            # Import cyber agent routes
            from cybercrime import app as cyber_app
            from cybercrime import cyber_agent_endpoint, download_cybercrime_pdf

            # Add murder agent routes
            self.app.post("/api/murder")(murder_agent_endpoint)
            self.app.post("/api/murder/download-pdf")(download_murder_pdf)

            # Add cyber agent routes
            self.app.post("/api/cyber")(cyber_agent_endpoint)
            self.app.post("/api/cyber/download-pdf")(download_cybercrime_pdf)

            logger.info("✓ Successfully included all agent routes")

        except Exception as e:
            logger.error(f"✗ Failed to include agent routes: {e}")
            raise

async def main():
    print("\n" + "=" * 60)
    print("🔍 AI Justice Grid - Unified Multi-Agent Investigation System")
    print("=" * 60)

    server = UnifiedAgentServer()

    print("\n🔌 Available Agents (Unified Server):")
    for agent_name, config in AGENTS.items():
        print(f"   • {agent_name.capitalize()}: http://localhost:{UNIFIED_PORT}{config['prefix']}")

    print(f"\n🌐 Unified Server: http://localhost:{UNIFIED_PORT}")
    print(f"📚 API Documentation: http://localhost:{UNIFIED_PORT}/docs")
    print("\n🛑 Press Ctrl+C to stop the server")
    print("=" * 60)

    try:
        # Start the unified server
        config = uvicorn.Config(
            app=server.app,
            host="0.0.0.0",
            port=UNIFIED_PORT,
            log_level="info",
            reload=True
        )
        unified_server = uvicorn.Server(config)

        logger.info(f"🚀 Starting unified server on port {UNIFIED_PORT}")
        await unified_server.serve()

    except KeyboardInterrupt:
        print("\n✓ Unified server stopped by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

    return True

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    if not success:
        sys.exit(1)
