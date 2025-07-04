import logging
import uuid
import os
from dotenv import load_dotenv
load_dotenv()
import requests
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Dict, Any, Tuple, Optional, Union, List
from io import BytesIO

# OpenAI client for NVIDIA API
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

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
    title="Investigation Agent API",
    description="AI-powered investigation analysis system",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mount static files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "src")
if os.path.exists(frontend_path):
    app.mount("/frontend/src", StaticFiles(directory=frontend_path), name="frontend")
    logger.info(f"Mounted static files from: {frontend_path}")
else:
    logger.warning(f"Frontend path not found: {frontend_path}")

# NVIDIA API Configuration
NVIDIA_API_KEY = "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"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "nvidia/llama-3.1-nemotron-ultra-253b-v1"

# Initialize OpenAI client for NVIDIA (will be initialized in agent classes)
nvidia_client = None

def get_nvidia_client():
    """Get or create NVIDIA OpenAI client"""
    global nvidia_client
    if nvidia_client is None and OPENAI_AVAILABLE:
        try:
            nvidia_client = OpenAI(
                base_url=NVIDIA_BASE_URL,
                api_key=NVIDIA_API_KEY
            )
        except Exception as e:
            logger.error(f"Failed to initialize NVIDIA client: {e}")
            nvidia_client = None
    return nvidia_client

class PDFDownloadRequest(BaseModel):
    session_id: str = Field(description="Session ID for PDF generation")

# Generic Agent Models
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


# Dictionary to store conversation states for all agents
murder_conversation_states = {}
cybercrime_conversation_states = {}
humantrafficking_conversation_states = {}
narcotics_conversation_states = {}
moneylaundering_conversation_states = {}
onlinefraud_conversation_states = {}
sexualassault_conversation_states = {}
surveillance_conversation_states = {}
theft_conversation_states = {}
anti_smuggling_states = {}
customs_border_states = {}
interactive_conversation_states = {}

class GenericAgent:
    """Generic agent class that loads configuration from JSON files"""

    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.nvidia_api_key = NVIDIA_API_KEY
        self.nvidia_client = None
        self.case_info_steps = self.load_agent_config()

    def load_agent_config(self) -> List[Dict[str, Any]]:
        """Load agent configuration from JSON file"""
        try:
            json_path = os.path.join(os.path.dirname(__file__), 'json', f'{self.agent_type}.json')
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found for agent type: {self.agent_type}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON configuration for {self.agent_type}: {str(e)}")
            return []

    def get_step_by_id(self, step_id):
        """Get step configuration by ID"""
        for step in self.case_info_steps:
            if step["id"] == step_id:
                return step
        return None

    def create_new_conversation_state(self, conversation_states: Dict):
        """Create a new conversation state"""
        session_id = str(uuid.uuid4())
        conversation_states[session_id] = {
            "current_step": "greeting",
            "collected_data": {},
            "last_updated": datetime.now().isoformat()
        }
        return session_id

    def call_nvidia_api(self, prompt: str) -> str:
        """Call NVIDIA API using OpenAI client"""
        try:
            client = get_nvidia_client()
            if not client or not OPENAI_AVAILABLE:
                logger.warning(f"OpenAI client not available for {self.agent_type} analysis, using fallback")
                return self.generate_fallback_analysis()

            response = client.chat.completions.create(
                model="nvidia/llama-3.1-nemotron-ultra-253b-v1",
                messages=[
                    {"role": "system", "content": f"You are an expert {self.agent_type.replace('_', ' ')} investigator and forensic analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error calling NVIDIA API for {self.agent_type}: {str(e)}")
            return self.generate_fallback_analysis()

    def generate_fallback_analysis(self) -> str:
        """Generate fallback analysis when API is unavailable"""
        agent_name = self.agent_type.replace('_', ' ').title()
        return f"""
**{agent_name} Investigation Report**

I apologize, but I'm currently unable to connect to the advanced analysis system. However, I can provide a comprehensive framework for your {agent_name.lower()} investigation:

**1. Executive Summary**
- {agent_name} case requiring immediate attention
- Comprehensive investigation framework established
- Evidence collection and analysis in progress

**2. Case Assessment**
- Initial case evaluation completed
- Key evidence identified and catalogued
- Investigation priorities established

**3. Recommended Actions**
- Continue evidence collection following standard procedures
- Coordinate with relevant departments and agencies
- Maintain detailed documentation throughout the process
- Consider engaging external experts if needed

**Important Notes:**
- Ensure all investigative steps follow legal procedures
- Maintain chain of custody for all evidence
- Document all findings thoroughly
- Coordinate with law enforcement as appropriate

Please try refreshing the system or contact technical support if this issue persists.
"""

    def analyze_case(self, case_data):
        """Analyze the case using NVIDIA API with fallback"""
        try:
            agent_name = self.agent_type.replace('_', ' ').title()
            prompt = f"""
As an expert {agent_name.lower()} investigator, analyze the following case data and provide a comprehensive investigation report:

            Case Information:
            {json.dumps(case_data, indent=2)}

            Please provide a detailed analysis including:
            1. Executive Summary
            2. Case Assessment and Key Findings
            3. Evidence Analysis
            4. Investigative Recommendations
            5. Next Steps and Follow-up Actions
            6. Risk Assessment (if applicable)
            7. Legal Considerations

            Format the response in a professional investigative report style with clear sections and actionable recommendations.
            """

            return self.call_nvidia_api(prompt)

        except Exception as e:
            logger.error(f"Error in {self.agent_type} case analysis: {str(e)}")
            return self.generate_fallback_analysis()

    def process_message(self, message: str, session_id: Optional[str] = None,
                       force_new_session: bool = False, conversation_states: Dict = None):
        """Process user message and return response"""
        try:
            if conversation_states is None:
                conversation_states = {}

            # Handle session management
            if force_new_session or not session_id or session_id not in conversation_states:
                session_id = self.create_new_conversation_state(conversation_states)
                current_step = self.get_step_by_id("greeting")
                return session_id, current_step["message"] if current_step else "Hello! How can I help you?", True, "greeting", None

            conv_state = conversation_states[session_id]
            current_step_id = conv_state["current_step"]
            current_step = self.get_step_by_id(current_step_id)

            if not current_step:
                return session_id, "Error: Invalid step configuration", True, current_step_id, "Invalid step"

            # Store the user's response
            if current_step.get("field"):
                conv_state["collected_data"][current_step["field"]] = message

            # Move to next step
            next_step_id = current_step.get("next_step")
            if next_step_id:
                next_step = self.get_step_by_id(next_step_id)
                if next_step:
                    conv_state["current_step"] = next_step_id
                    conv_state["last_updated"] = datetime.now().isoformat()
                    return session_id, next_step["message"], True, next_step_id, None
                else:
                    # Analysis step - generate final report
                    analysis_result = self.analyze_case(conv_state["collected_data"])
                    conv_state["analysis_result"] = analysis_result
                    conv_state["analysis_completed"] = True
                    conv_state["last_updated"] = datetime.now().isoformat()
                    return session_id, analysis_result, False, "analysis", None
            else:
                # Final step reached - generate analysis
                analysis_result = self.analyze_case(conv_state["collected_data"])
                conv_state["analysis_result"] = analysis_result
                conv_state["analysis_completed"] = True
                conv_state["last_updated"] = datetime.now().isoformat()
                return session_id, analysis_result, False, "analysis", None

        except Exception as e:
            logger.error(f"Error in {self.agent_type} process_message: {str(e)}")
            return session_id or "error", f"An error occurred: {str(e)}", True, current_step_id if 'current_step_id' in locals() else "error", str(e)


class InteractiveAgent:
    """Interactive agent for general conversations and assistance"""

    def __init__(self):
        self.agent_type = "interactive"
        self.nvidia_api_key = NVIDIA_API_KEY
        self.nvidia_client = None

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
                logger.warning("OpenAI client not available for interactive agent, using fallback")
                return self.generate_fallback_response()

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
                    messages.append({"role": "user", "content": entry.get("user", "")})
                    messages.append({"role": "assistant", "content": entry.get("assistant", "")})

            # Add current prompt
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model="nvidia/llama-3.1-nemotron-ultra-253b-v1",
                messages=messages,
                temperature=0.7,
                max_tokens=4000
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error calling NVIDIA API for interactive agent: {str(e)}")
            return self.generate_fallback_response()

    def generate_fallback_response(self) -> str:
        """Generate fallback response when API is unavailable"""
        return """I'm here to help! However, I'm currently experiencing some technical difficulties with my AI processing capabilities.

While I work to resolve this issue, I can still assist you with basic information and guidance. Please feel free to ask your question, and I'll do my best to provide a helpful response.

For the most comprehensive assistance, please try again in a few moments when my full capabilities are restored."""

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
            logger.error(f"Error in interactive agent process_message: {str(e)}")
            return session_id or str(uuid.uuid4()), f"I apologize, but I encountered an error while processing your message: {str(e)}", False, "error", str(e)


# Initialize generic agents for JSON-configured types
murder_agent = GenericAgent("murder")
cybercrime_agent = GenericAgent("cyber")
humantrafficking_agent = GenericAgent("humantrafficking")
narcotics_agent = GenericAgent("narcotics")
moneylaundering_agent = GenericAgent("moneylaundering")
onlinefraud_agent = GenericAgent("onlinefraud")
sexualassault_agent = GenericAgent("sexualassualt")  # Note: keeping original filename spelling
surveillance_agent = GenericAgent("surveillance")
theft_agent = GenericAgent("theft")
anti_smuggling = GenericAgent("antismuggle")
customs_border = GenericAgent("customsborder")
interactive_agent = InteractiveAgent()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Received GET request for health endpoint")
    return {
        "status": "healthy",
        "message": "AiJusticeGrid API is running",
        "timestamp": datetime.now().isoformat(),
        "agents": {
            "murder_agent": "active",
            "cybercrime_agent": "active",
            "humantrafficking_agent": "active",
            "narcotics_agent": "active",
            "moneylaundering_agent": "active",
            "onlinefraud_agent": "active",
            "sexualassault_agent": "active",
            "surveillance_agent": "active",
            "theft_agent": "active",
            "anti_smuggling" : "active",
            "customs_border" : "active",
            "interactive_agent": "active"
        }
    }

# FastAPI Routes
@app.get("/", response_model=Dict[str, str])
async def home():
    """Home endpoint"""
    logger.info("Received GET request for home endpoint")
    return {"message": "Investigation Agent API is running"}


# Helper function to create generic agent endpoint
def create_agent_endpoint(agent_name: str, agent_instance: GenericAgent, conversation_states: Dict):
    """Create endpoint function for a generic agent"""
    async def agent_endpoint(request: GenericAgentRequest):
        f"""Main endpoint for {agent_name} agent interactions"""
        try:
            # Health check
            if request.question == "ping":
                return GenericAgentResponse(
                    success=True,
                    data=GenericAgentData(
                        analysis=f"{agent_name.title()} Agent is running",
                        is_collecting_info=False,
                        current_step="ping",
                        collected_data={},
                        error=None
                    ),
                    session_id="ping_session",
                    message="Health check successful"
                )

            force_new_session = request.force_new_session or request.forceReset

            session_id, response, is_collecting_info, current_step, error_message = agent_instance.process_message(
                request.question,
                request.session_id,
                force_new_session=force_new_session,
                conversation_states=conversation_states
            )

            return GenericAgentResponse(
                success=True,
                data=GenericAgentData(
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
            logger.error(f"Error in {agent_name}_agent_endpoint: {str(e)}")
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

    return agent_endpoint

# Create endpoints for all generic agents
@app.post("/api/murder", response_model=GenericAgentResponse)
async def murder_agent_endpoint(request: GenericAgentRequest):
    return await create_agent_endpoint("murder", murder_agent, murder_conversation_states)(request)

@app.post("/api/cyber", response_model=GenericAgentResponse)
async def cyber_agent_endpoint(request: GenericAgentRequest):
    return await create_agent_endpoint("cyber", cybercrime_agent, cybercrime_conversation_states)(request)

@app.post("/api/humantrafficking", response_model=GenericAgentResponse)
async def humantrafficking_agent_endpoint(request: GenericAgentRequest):
    return await create_agent_endpoint("humantrafficking", humantrafficking_agent, humantrafficking_conversation_states)(request)

@app.post("/api/narcotics", response_model=GenericAgentResponse)
async def narcotics_agent_endpoint(request: GenericAgentRequest):
    return await create_agent_endpoint("narcotics", narcotics_agent, narcotics_conversation_states)(request)

@app.post("/api/moneylaundering", response_model=GenericAgentResponse)
async def moneylaundering_agent_endpoint(request: GenericAgentRequest):
    return await create_agent_endpoint("moneylaundering", moneylaundering_agent, moneylaundering_conversation_states)(request)

@app.post("/api/onlinefraud", response_model=GenericAgentResponse)
async def onlinefraud_agent_endpoint(request: GenericAgentRequest):
    return await create_agent_endpoint("onlinefraud", onlinefraud_agent, onlinefraud_conversation_states)(request)

@app.post("/api/sexualassault", response_model=GenericAgentResponse)
async def sexualassault_agent_endpoint(request: GenericAgentRequest):
    return await create_agent_endpoint("sexualassault", sexualassault_agent, sexualassault_conversation_states)(request)

@app.post("/api/surveillance", response_model=GenericAgentResponse)
async def surveillance_agent_endpoint(request: GenericAgentRequest):
    return await create_agent_endpoint("surveillance", surveillance_agent, surveillance_conversation_states)(request)

@app.post("/api/theft", response_model=GenericAgentResponse)
async def theft_agent_endpoint(request: GenericAgentRequest):
    return await create_agent_endpoint("theft", theft_agent, theft_conversation_states)(request)

@app.post("/api/antismuggle", response_model=GenericAgentResponse)
async def antiSmuggle_agent_endpoint(request: GenericAgentRequest):
    return await create_agent_endpoint("antismuggle", anti_smuggling, anti_smuggling_states)(request)

@app.post("/api/customsborder", response_model=GenericAgentResponse)
async def customsBorder_agent_endpoint(request: GenericAgentRequest):
    return await create_agent_endpoint("customsborder", customs_border, customs_border_states)(request)

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


class GenericPDFGenerator:
    """Generic PDF generator for investigation reports"""

    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab")

    def generate_generic_pdf(self, agent_type: str, case_data: Dict[str, Any], analysis_text: str) -> BytesIO:
        """Generate a generic investigation PDF report"""
        buffer = BytesIO()

        try:
            # Create the PDF document
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                                   topMargin=72, bottomMargin=18)

            # Get custom styles
            styles = self.create_generic_styles()

            # Build the story (content)
            story = []

            # Title
            agent_title = agent_type.replace('_', ' ').title()
            story.append(Paragraph(f"{agent_title.upper()} INVESTIGATION REPORT", styles['title']))
            story.append(Spacer(1, 20))

            # Header information
            story.append(Paragraph("CASE INFORMATION", styles['section_header']))
            story.append(Spacer(1, 10))

            # Case details table
            case_details = self.format_generic_case_details(case_data)
            if case_details:
                story.extend(case_details)
                story.append(Spacer(1, 20))

            # Analysis section
            if analysis_text:
                story.append(Paragraph("COMPREHENSIVE CASE ANALYSIS", styles['section_header']))
                story.append(Spacer(1, 10))

                # Format analysis text
                analysis_paragraphs = self.format_analysis_text(analysis_text, styles)
                for paragraph in analysis_paragraphs:
                    story.append(paragraph)
                    story.append(Spacer(1, 6))

                story.append(Spacer(1, 15))

            # Footer
            story.append(Spacer(1, 20))
            story.append(Paragraph("--- End of Report ---", styles['footer']))

            # Build the PDF
            doc.build(story)
            buffer.seek(0)

            return buffer

        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            # Create a simple error PDF
            buffer = BytesIO()
            try:
                doc = SimpleDocTemplate(buffer, pagesize=A4)
                styles = getSampleStyleSheet()
                story = [Paragraph(f"Error generating PDF: {str(e)}", styles['Title'])]
                doc.build(story)
            except:
                buffer.write(f"Error generating PDF: {str(e)}".encode('utf-8'))
            buffer.seek(0)
            return buffer

    def format_generic_case_details(self, case_data: Dict[str, Any]) -> list:
        """Format case details for the PDF with proper text wrapping"""
        details = []
        styles = self.create_generic_styles()

        if not case_data:
            details.append(Paragraph("No case data available", styles['body_text']))
            return details

        # Create table data with proper text wrapping
        table_data = []
        for key, value in case_data.items():
            if value:  # Only include non-empty values
                # Format field name
                field_name = key.replace('_', ' ').title() + ':'
                field_value = str(value).strip()

                if field_value and field_value.lower() not in ['n/a', 'none', 'unknown', '']:
                    # Create paragraphs for proper text wrapping
                    label_paragraph = self.create_table_cell_paragraph(field_name, styles, bold=True)
                    value_paragraph = self.create_table_cell_paragraph(field_value, styles, bold=False)
                    table_data.append([label_paragraph, value_paragraph])

        if table_data:
           # Create table with adjusted column widths for better text wrappingAdd commentMore actions
            table = Table(table_data, colWidths=[2.2*inch, 4.3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            details.append(table)

        return details

    def create_table_cell_paragraph(self, text: str, styles: dict, bold: bool = False) -> Paragraph:
        """Create a paragraph for table cell with proper wrapping"""
        # Ensure text is properly escaped and cleaned
        clean_text = str(text).strip()

        # Remove markdown formatting from table cell text
        clean_text = self.clean_markdown_formatting(clean_text)

        # Format long text for better display in tables
        if len(clean_text) > 80:  # For longer text, add strategic breaks
            clean_text = self.format_long_text_for_table(clean_text, max_length=80)

        # Create a style for table cells with better wrapping
        if bold:
            cell_style = ParagraphStyle(
                'TableCellBold',
                parent=styles['body_text'],
                fontSize=10,
                fontName='Helvetica-Bold',
                alignment=TA_LEFT,
                spaceAfter=2,
                spaceBefore=2,
                leftIndent=0,
                rightIndent=0,
                wordWrap='LTR',  # Enable word wrapping
                allowWidows=1,   # Allow single lines at page breaks
                allowOrphans=1   # Allow single lines at page breaks
            )
        else:
            cell_style = ParagraphStyle(
                'TableCell',
                parent=styles['body_text'],
                fontSize=10,
                fontName='Helvetica',
                alignment=TA_LEFT,
                spaceAfter=2,
                spaceBefore=2,
                leftIndent=0,
                rightIndent=0,
                wordWrap='LTR',  # Enable word wrapping
                allowWidows=1,   # Allow single lines at page breaks
                allowOrphans=1   # Allow single lines at page breaks
            )

        return Paragraph(clean_text, cell_style)

    def format_long_text_for_table(self, text: str, max_length: int = 100) -> str:
        """Format long text for better table display by adding strategic line breaks"""
        if not text or len(text) <= max_length:
            return text

        # Split long text into smaller chunks at natural break points
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 <= max_length:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)

        if current_line:
            lines.append(' '.join(current_line))

        return '<br/>'.join(lines)    

    def format_analysis_text(self, analysis_text: str, styles) -> list:
        """Format analysis text into paragraphs"""
        paragraphs = []

        if not analysis_text:
            return [Paragraph("No analysis available.", styles['body_text'])]
        
        # Clean the entire text firstAdd commentMore actions
        clean_text = self.clean_markdown_formatting(analysis_text)    

        # Split text into lines and process
        lines = clean_text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip unwanted headers
            if '[LIVE DATA ANALYSIS]' in line or line.startswith('Case Analysis:'):
                continue

            # Check for headers
            if any(header in line.upper() for header in [
                'EXECUTIVE SUMMARY', 'CASE ASSESSMENT', 'EVIDENCE ANALYSIS',
                'RECOMMENDATIONS', 'NEXT STEPS', 'RISK ASSESSMENT', 'LEGAL CONSIDERATIONS',
                'COMPREHENSIVE ANALYSIS', 'POTENTIAL MOTIVES', 'INVESTIGATIVE APPROACHES',
                'KEY EVIDENCE', 'POSSIBLE SOLUTIONS', 'CONCLUSIONS'
            ]):
                clean_header = line.strip()
                if clean_header.endswith(':'):
                    clean_header = clean_header[:-1]
                paragraphs.append(Paragraph(clean_header, styles['analysis_header']))
            elif line.startswith('- ') or line.startswith('• '):
                bullet_text = line[2:].strip()
               
                if bullet_text:
                    paragraphs.append(Paragraph(f"• {bullet_text}", styles['bullet_point']))
            elif line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                paragraphs.append(Paragraph(line, styles['bullet_point']))
            else:
                if line.strip():
                    paragraphs.append(Paragraph(line, styles['body_text']))

        return paragraphs if paragraphs else [Paragraph("Analysis text could not be formatted.", styles['body_text'])]

    def clean_markdown_formatting(self, text: str) -> str:
        """Remove all markdown formatting symbols from text"""
        if not text:
            return ""

        clean_text = str(text).strip()

        # Remove markdown headers (###, ##, #)
        clean_text = clean_text.replace('###', '')
        clean_text = clean_text.replace('##', '')
        clean_text = clean_text.replace('#', '')

        # Remove bold and italic markdown
        clean_text = clean_text.replace('**', '')
        clean_text = clean_text.replace('*', '')

        # Remove other common markdown symbols
        clean_text = clean_text.replace('`', '')
        clean_text = clean_text.replace('~~', '')

        # Remove specific unwanted headers
        clean_text = clean_text.replace('[LIVE DATA ANALYSIS]', '')

        # Clean up extra whitespace while preserving line structure
        lines = clean_text.split('\n')
        cleaned_lines = []
        for line in lines:
            cleaned_line = line.strip()
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
            elif cleaned_lines and cleaned_lines[-1]:  # Preserve section breaks
                cleaned_lines.append('')

        return '\n'.join(cleaned_lines)

    def create_generic_styles(self):
        """Create professional styles for generic investigation PDFs"""
        styles = getSampleStyleSheet()

        custom_styles = {
            'title': ParagraphStyle(
                'GenericTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#2c3e50'),
                fontName='Helvetica-Bold'
            ),
            'section_header': ParagraphStyle(
                'GenericHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=20,
                textColor=colors.HexColor('#2c3e50'),
                fontName='Helvetica-Bold'
            ),
            'analysis_header': ParagraphStyle(
                'AnalysisHeader',
                parent=styles['Heading3'],
                fontSize=12,
                spaceAfter=8,
                spaceBefore=15,
                textColor=colors.HexColor('#34495e'),
                fontName='Helvetica-Bold'
            ),
            'body_text': ParagraphStyle(
                'GenericBody',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                alignment=TA_JUSTIFY,
                textColor=colors.black,
                fontName='Helvetica'
            ),
            'bullet_point': ParagraphStyle(
                'BulletPoint',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=4,
                leftIndent=20,
                textColor=colors.black,
                fontName='Helvetica'
            ),
            'footer': ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#7f8c8d'),
                fontName='Helvetica-Oblique'
            )
        }

        return custom_styles

# Helper function to create generic PDF download endpoint
def create_pdf_download_endpoint(agent_name: str, conversation_states: Dict):
    """Create PDF download endpoint function for a generic agent"""
    async def pdf_download_endpoint(request: PDFDownloadRequest):
        f"""Generate and download PDF report for {agent_name} investigation"""
        try:
            if not REPORTLAB_AVAILABLE:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "success": False,
                        "error": "PDF generation not available. ReportLab library not installed."
                    }
                )

            session_id = request.session_id
            if not session_id or session_id not in conversation_states:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "error": "Invalid session ID or session not found"
                    }
                )

            conv_state = conversation_states[session_id]

            # Check if analysis is completed
            if not conv_state.get("analysis_completed"):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "error": "Analysis not completed yet. Please complete the investigation first."
                    }
                )

            # Get case data and analysis
            case_data = conv_state.get("collected_data", {})
            analysis_text = conv_state.get("analysis_result", "")

            if not analysis_text:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "error": "No analysis available for PDF generation"
                    }
                )

            # Generate PDF
            pdf_generator = GenericPDFGenerator()
            pdf_buffer = pdf_generator.generate_generic_pdf(agent_name, case_data, analysis_text)

            # Generate filename
            case_id = case_data.get('case_id', 'Unknown')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            agent_title = agent_name.replace('_', ' ').title().replace(' ', '')
            filename = f"{agent_title}_Investigation_Report_{case_id}_{timestamp}.pdf"

            # Return PDF file as streaming response
            return StreamingResponse(
                BytesIO(pdf_buffer.read()),
                media_type='application/pdf',
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in download_{agent_name}_pdf: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": f"Error generating PDF: {str(e)}"
                }
            )

    return pdf_download_endpoint

# Create PDF download endpoints for all generic agents
@app.post("/api/murder/download-pdf")
async def download_murder_pdf(request: PDFDownloadRequest):
    return await create_pdf_download_endpoint("murder", murder_conversation_states)(request)

@app.post("/api/cyber/download-pdf")
async def download_cybercrime_pdf(request: PDFDownloadRequest):
    return await create_pdf_download_endpoint("cyber", cybercrime_conversation_states)(request)    

@app.post("/api/humantrafficking/download-pdf")
async def download_humantrafficking_pdf(request: PDFDownloadRequest):
    return await create_pdf_download_endpoint("humantrafficking", humantrafficking_conversation_states)(request)

@app.post("/api/narcotics/download-pdf")
async def download_narcotics_pdf(request: PDFDownloadRequest):
    return await create_pdf_download_endpoint("narcotics", narcotics_conversation_states)(request)

@app.post("/api/moneylaundering/download-pdf")
async def download_moneylaundering_pdf(request: PDFDownloadRequest):
    return await create_pdf_download_endpoint("moneylaundering", moneylaundering_conversation_states)(request)

@app.post("/api/onlinefraud/download-pdf")
async def download_onlinefraud_pdf(request: PDFDownloadRequest):
    return await create_pdf_download_endpoint("onlinefraud", onlinefraud_conversation_states)(request)

@app.post("/api/sexualassault/download-pdf")
async def download_sexualassault_pdf(request: PDFDownloadRequest):
    return await create_pdf_download_endpoint("sexualassault", sexualassault_conversation_states)(request)

@app.post("/api/surveillance/download-pdf")
async def download_surveillance_pdf(request: PDFDownloadRequest):
    return await create_pdf_download_endpoint("surveillance", surveillance_conversation_states)(request)

@app.post("/api/theft/download-pdf")
async def download_theft_pdf(request: PDFDownloadRequest):
    return await create_pdf_download_endpoint("theft", theft_conversation_states)(request)

@app.post("/api/antismuggle/download-pdf")
async def download_antiSmuggling_pdf(request: PDFDownloadRequest):
    return await create_pdf_download_endpoint("antismuggle", anti_smuggling_states)(request)

@app.post("/api/customsborder/download-pdf")
async def download_customs_pdf(request: PDFDownloadRequest):
    return await create_pdf_download_endpoint("customsborder", customs_border_states)(request)

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Investigation Agent API server on port 5001")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5001,
        reload=True,
        log_level="info"
    )