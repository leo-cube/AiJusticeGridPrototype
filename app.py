import logging
import uuid
import os
import requests
from datetime import datetime
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Tuple, Optional, Union
from io import BytesIO

# PDF generation libraries
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Initialize FastAPI app
app = FastAPI(
    title="Murder Agent API",
    description="AI-powered murder investigation analysis system",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for Netlify deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:3000", 
        "https://*.netlify.app",
        "https://*.netlify.com",
        "https://aijusticegrid.netlify.app",  # Replace with your actual Netlify URL
        "*"  # Allow all origins for now - you can restrict this later
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NVIDIA API Configuration
NVIDIA_API_KEY = "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"
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

# Define the case information collection steps
CASE_INFO_STEPS = [
    {
        "id": "greeting",
        "message": "**[LIVE DATA ANALYSIS]**\n\nHello, I'm the Murder Agent, an AI assistant specialized in homicide investigations. I'll help you analyze a murder case by collecting relevant information. Let's start with the basics. What is the Case ID for this investigation?",
        "field": "case_id",
        "next_step": "date_of_crime"
    },
    {
        "id": "date_of_crime",
        "message": "**[LIVE DATA ANALYSIS]**\n\nThank you. When did the crime occur? Please provide the date (YYYY-MM-DD, MM/DD/YYYY, or text format like 'January 15, 2023').",
        "field": "date_of_crime",
        "next_step": "time_of_crime"
    },
    {
        "id": "time_of_crime",
        "message": "**[LIVE DATA ANALYSIS]**\n\nWhat time did the crime occur? (HH:MM format, or approximate time like '2:30 PM', 'noon', or 'evening')",
        "field": "time_of_crime",
        "next_step": "location"
    },
    {
        "id": "location",
        "message": "**[LIVE DATA ANALYSIS]**\n\nWhere did the crime take place? Please provide the location.",
        "field": "location",
        "next_step": "victim_name"
    },
    {
        "id": "victim_name",
        "message": "**[LIVE DATA ANALYSIS]**\n\nWhat is the victim's name?",
        "field": "victim_name",
        "next_step": "victim_age"
    },
    {
        "id": "victim_age",
        "message": "**[LIVE DATA ANALYSIS]**\n\nWhat is the victim's age?",
        "field": "victim_age",
        "next_step": "victim_gender"
    },
    {
        "id": "victim_gender",
        "message": "**[LIVE DATA ANALYSIS]**\n\nWhat is the victim's gender?",
        "field": "victim_gender",
        "next_step": "cause_of_death"
    },
    {
        "id": "cause_of_death",
        "message": "**[LIVE DATA ANALYSIS]**\n\nWhat was the cause of death?",
        "field": "cause_of_death",
        "next_step": "weapon_used"
    },
    {
        "id": "weapon_used",
        "message": "**[LIVE DATA ANALYSIS]**\n\nWas a weapon used? If so, what kind?",
        "field": "weapon_used",
        "next_step": "crime_scene_description"
    },
    {
        "id": "crime_scene_description",
        "message": "**[LIVE DATA ANALYSIS]**\n\nPlease describe the crime scene.",
        "field": "crime_scene_description",
        "next_step": "witnesses"
    },
    {
        "id": "witnesses",
        "message": "**[LIVE DATA ANALYSIS]**\n\nWere there any witnesses? If so, please provide details.",
        "field": "witnesses",
        "next_step": "evidence_found"
    },
    {
        "id": "evidence_found",
        "message": "**[LIVE DATA ANALYSIS]**\n\nWhat evidence was found at the scene?",
        "field": "evidence_found",
        "next_step": "suspects"
    },
    {
        "id": "suspects",
        "message": "**[LIVE DATA ANALYSIS]**\n\nAre there any suspects at this time?",
        "field": "suspects",
        "next_step": "additional_notes"
    },
    {
        "id": "additional_notes",
        "message": "**[LIVE DATA ANALYSIS]**\n\nDo you have any additional notes or information about the case?",
        "field": "additional_notes",
        "next_step": "analysis"
    },
    {
        "id": "analysis",
        "message": "**[LIVE DATA ANALYSIS]**\n\nThank you for providing all the case details. I'll now analyze this information and provide you with a comprehensive report.",
        "field": None,
        "next_step": None
    }
]

# Dictionary to store conversation states
conversation_states = {}

# Pydantic Models for Request/Response validation
class MurderAgentRequest(BaseModel):
    question: str = Field(default="", description="User's question or input")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation continuity")
    force_new_session: bool = Field(default=False, description="Force creation of new session")
    forceReset: bool = Field(default=False, description="Alternative field for forcing reset")

class MurderAgentData(BaseModel):
    analysis: str = Field(description="AI analysis response")
    is_collecting_info: bool = Field(description="Whether still collecting case information")
    current_step: str = Field(description="Current step in the investigation process")
    collected_data: Dict[str, Any] = Field(default_factory=dict, description="Collected case data")
    error: Optional[str] = Field(default=None, description="Error message if any")

class MurderAgentResponse(BaseModel):
    success: bool = Field(description="Whether the request was successful")
    data: MurderAgentData = Field(description="Response data")
    session_id: str = Field(description="Session ID")
    message: str = Field(description="Status message")

class PDFDownloadRequest(BaseModel):
    session_id: str = Field(description="Session ID for PDF generation")

class HealthResponse(BaseModel):
    status: str = Field(description="Health status")
    message: str = Field(description="Status message")
    endpoints: list[str] = Field(description="Available endpoints")

class ErrorResponse(BaseModel):
    success: bool = Field(default=False)
    error: str = Field(description="Error message")
    data: Optional[Dict[str, Any]] = Field(default=None)

class MurderAgent:
    def __init__(self):
        self.nvidia_api_key = NVIDIA_API_KEY
        self.nvidia_api_url = NVIDIA_API_URL

    def get_step_by_id(self, step_id):
        """Get step configuration by ID"""
        for step in CASE_INFO_STEPS:
            if step["id"] == step_id:
                return step
        return None

    def create_new_conversation_state(self):
        """Create a new conversation state"""
        session_id = str(uuid.uuid4())
        conversation_states[session_id] = {
            "current_step": "greeting",
            "collected_data": {},
            "last_updated": datetime.now().isoformat()
        }
        return session_id

    def store_user_input(self, session_id: str, step_id: str, user_input: str) -> Tuple[bool, Optional[str]]:
        """Store user input in the conversation state"""
        if session_id not in conversation_states:
            return False, "Session not found"

        current_step = self.get_step_by_id(step_id)
        if not current_step:
            return False, "Invalid step"

        if current_step["field"]:
            conversation_states[session_id]["collected_data"][current_step["field"]] = user_input

        return True, None

    def advance_to_next_step(self, session_id, current_step_id):
        """Advance to the next step in the conversation"""
        if session_id not in conversation_states:
            return False

        current_step = self.get_step_by_id(current_step_id)
        if not current_step:
            return False

        if current_step["next_step"]:
            next_step_id = current_step["next_step"]
            conversation_states[session_id]["current_step"] = next_step_id
            return True

        return False

    def call_nvidia_api(self, prompt: str) -> str:
        """Call NVIDIA API for case analysis"""
        try:
            headers = {
                "Authorization": f"Bearer {self.nvidia_api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "nvidia/llama-3.1-nemotron-70b-instruct",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a specialized AI assistant for homicide investigations. Provide detailed, professional analysis of murder cases with comprehensive insights on motives, suspects, evidence, and investigative approaches."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }

            response = requests.post(self.nvidia_api_url, headers=headers, json=payload)
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"Error calling NVIDIA API: {str(e)}")
            return self.generate_fallback_analysis()

    def generate_fallback_analysis(self) -> str:
        """Generate fallback analysis if NVIDIA API fails"""
        return """**[LIVE DATA ANALYSIS]**

**Case Analysis Report**

I apologize, but I'm currently unable to connect to the advanced analysis system. However, I can provide a basic framework for your investigation:

**1. Comprehensive Analysis of the Case**
- Review all collected evidence systematically
- Establish timeline of events
- Analyze victim profile and potential connections

**2. Potential Motives and Suspects to Consider**
- Personal relationships and conflicts
- Financial motives
- Random crime vs. targeted attack

**3. Recommended Investigative Approaches**
- Interview all witnesses thoroughly
- Examine physical evidence
- Check alibis of potential suspects

**4. Key Evidence to Focus On and Analysis**
- Crime scene forensics
- Witness testimonies
- Physical evidence analysis

**5. Possible Solutions or Conclusions**
- Continue investigation with systematic approach
- Focus on most promising leads
- Consider consulting with forensic experts

Please ensure all evidence is properly documented and chain of custody is maintained."""

    def generate_analysis_prompt(self, case_details: Dict[str, Any]) -> str:
        """Generate prompt for NVIDIA API analysis"""
        prompt = f"""
Analyze the following murder case and provide a comprehensive investigation report:

**Case Details:**
Case ID: {case_details.get('case_id', 'N/A')}
Date of Crime: {case_details.get('date_of_crime', 'N/A')}
Time of Crime: {case_details.get('time_of_crime', 'N/A')}
Location: {case_details.get('location', 'N/A')}
Victim Name: {case_details.get('victim_name', 'N/A')}
Victim Age: {case_details.get('victim_age', 'N/A')}
Victim Gender: {case_details.get('victim_gender', 'N/A')}
Cause of Death: {case_details.get('cause_of_death', 'N/A')}
Weapon Used: {case_details.get('weapon_used', 'N/A')}
Crime Scene Description: {case_details.get('crime_scene_description', 'N/A')}
Witnesses: {case_details.get('witnesses', 'N/A')}
Evidence Found: {case_details.get('evidence_found', 'N/A')}
Suspects: {case_details.get('suspects', 'N/A')}
Additional Notes: {case_details.get('additional_notes', 'N/A')}

Please provide a detailed analysis following this structure:

**1. Comprehensive Analysis of the Case**
- Analyze the victim profile, crime scene, and circumstances
- Identify patterns and significant details
- Assess the nature of the crime (planned vs. spontaneous, personal vs. random)

**2. Potential Motives and Suspects to Consider**
- Analyze possible motives based on the evidence
- Evaluate potential suspects and their likelihood
- Consider relationship dynamics and external factors

**3. Recommended Investigative Approaches**
- Suggest specific investigative steps
- Prioritize evidence collection and analysis
- Recommend interview strategies

**4. Key Evidence to Focus On and Analysis**
- Highlight the most critical evidence
- Suggest forensic analysis priorities
- Identify gaps in evidence collection

**5. Possible Solutions or Conclusions**
- Provide investigative conclusions based on available evidence
- Suggest next steps for case resolution
- Identify areas requiring further investigation

Format your response with clear headers and detailed analysis for each section.
"""
        return prompt

    def analyze_case(self, case_details: Dict[str, Any]) -> str:
        """Analyze the case using NVIDIA API"""
        prompt = self.generate_analysis_prompt(case_details)
        analysis = self.call_nvidia_api(prompt)

        # Format the analysis with the proper header
        formatted_analysis = f"**[LIVE DATA ANALYSIS]**\n\n**Case Analysis: Case ID {case_details.get('case_id', 'Unknown')}**\n\n{analysis}"

        return formatted_analysis

    def process_message(self, message: str, session_id: Optional[str] = None, force_new_session: bool = False) -> Tuple[str, str, bool, str, Optional[str]]:
        """Process user message and return appropriate response"""
        logger.info(f"Processing message: {message} with session_id: {session_id}")

        # Handle reset or new session requests
        if message and message.lower() in ["reset", "restart", "start over"] or force_new_session:
            if session_id and session_id in conversation_states:
                del conversation_states[session_id]
            session_id = self.create_new_conversation_state()
            current_step = self.get_step_by_id("greeting")
            return session_id, current_step["message"], True, "greeting", None

        # Create new session if none exists
        if not session_id or session_id not in conversation_states:
            session_id = self.create_new_conversation_state()
            if not message:
                current_step = self.get_step_by_id("greeting")
                return session_id, current_step["message"], True, "greeting", None

        conv_state = conversation_states[session_id]
        current_step_id = conv_state["current_step"]

        # Handle greeting step without message
        if current_step_id == "greeting" and not message:
            return session_id, self.get_step_by_id("greeting")["message"], True, "greeting", None

        # Process user input
        if message:
            success, error_message = self.store_user_input(session_id, current_step_id, message)

            if not success:
                current_step = self.get_step_by_id(current_step_id)
                error_response = f"I couldn't process your input: {error_message}\n\nPlease try again. {current_step['message']}"
                return session_id, error_response, True, current_step_id, error_message

            # Advance to next step
            self.advance_to_next_step(session_id, current_step_id)
            current_step_id = conv_state["current_step"]
            current_step = self.get_step_by_id(current_step_id)

            # Check if we've reached the analysis step
            if current_step_id == "analysis":
                analysis = self.analyze_case(conv_state["collected_data"])
                conversation_states[session_id]["analysis_result"] = analysis
                conversation_states[session_id]["analysis_completed"] = True
                conversation_states[session_id]["current_step"] = "completed"
                return session_id, analysis, False, "completed", None

            # Return next question
            if current_step and current_step["message"]:
                return session_id, current_step["message"], True, current_step_id, None

        # Default response
        current_step = self.get_step_by_id(current_step_id)
        return session_id, current_step["message"] if current_step else "What would you like to know?", True, current_step_id, None


# Initialize the Murder Agent
murder_agent = MurderAgent()

# FastAPI Routes
@app.get("/", response_model=Dict[str, str])
async def home():
    """Home endpoint"""
    logger.info("Received GET request for home endpoint")
    return {"message": "Murder Agent API is running"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    logger.info("Received GET request for health endpoint")
    return HealthResponse(
        status="healthy",
        message="Murder Agent API is running",
        endpoints=[
            "/",
            "/health",
            "/api/murder",
            "/api/murder/download-pdf",
            "/docs",
            "/redoc"
        ]
    )

@app.post("/api/murder", response_model=MurderAgentResponse)
async def murder_agent_endpoint(request: MurderAgentRequest):
    """Main endpoint for murder agent interactions"""
    try:
        # Health check
        if request.question == "ping":
            return MurderAgentResponse(
                success=True,
                data=MurderAgentData(
                    analysis="Murder Agent is running",
                    is_collecting_info=False,
                    current_step="ping",
                    collected_data={},
                    error=None
                ),
                session_id="ping_session",
                message="Health check successful"
            )

        force_new_session = request.force_new_session or request.forceReset

        session_id, response, is_collecting_info, current_step, error_message = murder_agent.process_message(
            request.question,
            request.session_id,
            force_new_session=force_new_session
        )

        return MurderAgentResponse(
            success=True,
            data=MurderAgentData(
                analysis=response,
                is_collecting_info=is_collecting_info,
                current_step=current_step,
                collected_data=conversation_states[session_id]["collected_data"] if session_id in conversation_states else {},
                error=error_message
            ),
            session_id=session_id,
            message="Message processed successfully"
        )

    except Exception as e:
        logger.error(f"Error in murder_agent_endpoint: {str(e)}")
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
    logger.info("Starting Murder Agent API server on port 5001")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5001,
        reload=True,
        log_level="info"
    )
