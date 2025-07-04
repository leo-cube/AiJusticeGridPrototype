#!/usr/bin/env python3
"""
Simple test server to verify the Interactive Agent works
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Interactive Agent Test Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# NVIDIA API Configuration
NVIDIA_API_KEY = "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"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "nvidia/llama-3.1-nemotron-ultra-253b-v1"

# Try to import OpenAI client
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    
    def get_nvidia_client():
        """Get NVIDIA OpenAI client"""
        try:
            return OpenAI(
                base_url=NVIDIA_BASE_URL,
                api_key=NVIDIA_API_KEY
            )
        except Exception as e:
            logger.error(f"Failed to initialize NVIDIA client: {e}")
            return None
            
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not available")
    
    def get_nvidia_client():
        return None

# Request/Response models
class GenericAgentRequest(BaseModel):
    question: str = Field(default="", description="User's question or input")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation continuity")
    force_new_session: bool = Field(default=False, description="Force creation of new session")
    forceReset: bool = Field(default=False, description="Alternative field for forcing reset")

class GenericAgentData(BaseModel):
    analysis: str = Field(description="AI analysis response")
    is_collecting_info: bool = Field(description="Whether still collecting case information")
    current_step: str = Field(description="Current step in the investigation process")
    collected_data: Dict[str, Any] = Field(default_factory=dict, description="Collected case data")
    error: Optional[str] = Field(default=None, description="Error message if any")

class GenericAgentResponse(BaseModel):
    success: bool = Field(description="Whether the request was successful")
    data: GenericAgentData = Field(description="Response data")
    session_id: str = Field(description="Session ID")
    message: str = Field(description="Status message")

# Conversation states
interactive_conversation_states = {}

class InteractiveAgent:
    """Simple Interactive Agent for testing"""

    def __init__(self):
        self.agent_type = "interactive"
        self.nvidia_api_key = NVIDIA_API_KEY

    def create_new_conversation_state(self, conversation_states: Dict):
        """Create a new conversation state"""
        session_id = str(uuid.uuid4())
        conversation_states[session_id] = {
            "current_step": "greeting",
            "conversation_history": [],
            "last_updated": datetime.now().isoformat()
        }
        return session_id

    def call_nvidia_api(self, prompt: str, conversation_history: List = None) -> str:
        """Call NVIDIA API using OpenAI client for interactive conversation"""
        try:
            client = get_nvidia_client()
            if not client or not OPENAI_AVAILABLE:
                logger.warning("OpenAI client not available, using fallback")
                return self.generate_fallback_response(prompt)

            # Build messages with conversation history
            messages = [
                {"role": "system", "content": """You are an intelligent and helpful AI assistant. You can help with a wide variety of tasks including:
                - Answering questions on various topics
                - Providing explanations and analysis
                - Helping with problem-solving
                - Offering advice and recommendations
                - Assisting with research and information gathering
                - Creative tasks like writing and brainstorming
                
                Be conversational, helpful, and engaging. Provide detailed and informative responses while maintaining a friendly tone."""}
            ]
            
            # Add conversation history
            if conversation_history:
                for entry in conversation_history[-10:]:  # Keep last 10 exchanges
                    if "user" in entry and "assistant" in entry:
                        messages.append({"role": "user", "content": entry["user"]})
                        messages.append({"role": "assistant", "content": entry["assistant"]})
            
            # Add current prompt
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=NVIDIA_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=4000
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error calling NVIDIA API: {str(e)}")
            return self.generate_fallback_response(prompt)

    def generate_fallback_response(self, prompt: str = "") -> str:
        """Generate fallback response when API is unavailable"""
        if "hello" in prompt.lower() or "hi" in prompt.lower():
            return "Hello! I'm your AI assistant. I'm here to help you with any questions or tasks you might have. How can I assist you today?"
        elif "help" in prompt.lower():
            return "I'm here to help! I can assist you with various tasks like answering questions, providing explanations, helping with analysis, and much more. What would you like help with?"
        else:
            return f"I understand you're asking about: '{prompt}'. While I'm currently experiencing some technical difficulties with my AI processing capabilities, I'm still here to help. Could you please rephrase your question or try again in a moment?"

    def process_message(self, message: str, session_id: Optional[str] = None,
                       force_new_session: bool = False, conversation_states: Dict = None):
        """Process user message and return response"""
        try:
            if conversation_states is None:
                conversation_states = {}

            # Handle session management
            if force_new_session or not session_id or session_id not in conversation_states:
                session_id = self.create_new_conversation_state(conversation_states)
                return session_id, "Hello! I'm your AI assistant. I'm here to help you with any questions or tasks you might have. What can I assist you with today?", False, "greeting", None

            # Get conversation history
            conversation_history = conversation_states[session_id].get("conversation_history", [])
            
            # Generate response using NVIDIA API
            response = self.call_nvidia_api(message, conversation_history)
            
            # Update conversation history
            conversation_history.append({
                "user": message,
                "assistant": response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep only last 20 exchanges to manage memory
            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]
            
            conversation_states[session_id]["conversation_history"] = conversation_history
            conversation_states[session_id]["last_updated"] = datetime.now().isoformat()

            return session_id, response, False, "conversation", None

        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}")
            return session_id or str(uuid.uuid4()), f"I apologize, but I encountered an error: {str(e)}", False, "error", str(e)

# Initialize the agent
interactive_agent = InteractiveAgent()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Interactive Agent Test Server is running",
        "timestamp": datetime.now().isoformat(),
        "nvidia_api_available": OPENAI_AVAILABLE
    }

@app.post("/api/interactive", response_model=GenericAgentResponse)
async def interactive_agent_endpoint(request: GenericAgentRequest):
    """Main endpoint for interactive agent conversations"""
    try:
        # Health check
        if request.question == "ping":
            return GenericAgentResponse(
                success=True,
                data=GenericAgentData(
                    analysis="Interactive Agent is running",
                    is_collecting_info=False,
                    current_step="ping",
                    collected_data={},
                    error=None
                ),
                session_id="ping_session",
                message="Health check successful"
            )

        force_new_session = request.force_new_session or request.forceReset

        session_id, response, is_collecting_info, current_step, error_message = interactive_agent.process_message(
            request.question,
            request.session_id,
            force_new_session=force_new_session,
            conversation_states=interactive_conversation_states
        )

        return GenericAgentResponse(
            success=True,
            data=GenericAgentData(
                analysis=response,
                is_collecting_info=is_collecting_info,
                current_step=current_step,
                collected_data={"conversation_history": interactive_conversation_states[session_id].get("conversation_history", [])[-5:]} if session_id in interactive_conversation_states else {},
                error=error_message
            ),
            session_id=session_id,
            message="Message processed successfully"
        )

    except Exception as e:
        logger.error(f"Error in interactive_agent_endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "data": {
                    "analysis": "An error occurred while processing your request."
                }
            }
        )

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Interactive Agent Test Server on port 5001")
    uvicorn.run(
        "simple_server:app",
        host="0.0.0.0",
        port=5001,
        reload=True,
        log_level="info"
    )
