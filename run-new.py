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

# Agent configurations
AGENTS = {
    "murder": {
        "app_module": "app",
        "app_name": "app",
        "port": 5001,
        "title": "Murder Agent API",
        "description": "AI-powered murder investigation analysis system",
    },
    "cybercrime": {
        "app_module": "cybercrime",
        "app_name": "app",
        "port": 5002,
        "title": "Cybercrime Agent API",
        "description": "AI-powered cybercrime investigation analysis system",
    }
    # Add more agents here in the future
}

class AgentManager:
    def __init__(self):
        self.agents = {}
        self.app = FastAPI(
            title="AI Justice Grid API Gateway",
            description="Gateway for multiple AI investigation agents",
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
        
        # Add health check endpoint
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "agents": list(AGENTS.keys()),
                "message": "AI Justice Grid is running"
            }

    def create_agent_app(self, agent_name):
        """Dynamically import and return the FastAPI app for an agent"""
        try:
            agent_config = AGENTS[agent_name]
            module = __import__(agent_config["app_module"])
            return getattr(module, agent_config["app_name"])
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to load agent {agent_name}: {str(e)}")
            return None

    async def start_agent(self, agent_name, port):
        """Start a single agent server"""
        app = self.create_agent_app(agent_name)
        if not app:
            logger.error(f"Failed to start agent: {agent_name}")
            return False

        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            reload=True
        )
        server = uvicorn.Server(config)
        
        logger.info(f"🚀 Starting {agent_name} agent on port {port}")
        await server.serve()
        return True

    async def start_all_agents(self):
        """Start all configured agents"""
        import asyncio
        tasks = []
        
        for agent_name, config in AGENTS.items():
            task = asyncio.create_task(
                self.start_agent(agent_name, config["port"])
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)

async def main():
    print("\n" + "=" * 60)
    print("🔍 AI Justice Grid - Multi-Agent Investigation System")
    print("=" * 60)
    
    manager = AgentManager()
    
    print("\n🔌 Available Agents:")
    for agent_name, config in AGENTS.items():
        print(f"   • {agent_name.capitalize()}: http://localhost:{config['port']}")
    
    print("\n🌐 API Gateway: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("\n🛑 Press Ctrl+C to stop all servers")
    print("=" * 60)
    
    try:
        # Start the main API gateway
        gateway_config = uvicorn.Config(
            app=manager.app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        gateway_server = uvicorn.Server(gateway_config)
        
        # Start all agents in the background
        import asyncio
        asyncio.create_task(manager.start_all_agents())
        
        # Start the gateway
        await gateway_server.serve()
        
    except KeyboardInterrupt:
        print("\n✓ All servers stopped by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    if not success:
        sys.exit(1)