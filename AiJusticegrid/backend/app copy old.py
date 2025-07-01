import logging
import uuid
import os
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
    title="Murder Agent API",
    description="AI-powered murder investigation analysis system",
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

# Define the case information collection steps for Murder Agent
MURDER_CASE_INFO_STEPS = [
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

# Define the case information collection steps for Cyber Crime Agent
CYBER_CRIME_CASE_INFO_STEPS = [
    {
        "id": "greeting",
        "message": "**[LIVE DATA ANALYSIS]**\n\nHello, I'm the Cybercrime Agent, an AI assistant specialized in Cybercrime based investigations. I'll help you analyze a Cybercrime case by collecting relevant information. Let's start with the basics. What is the Case ID for this investigation?",
        "field": "case_id",
        "next_step": "date_of_crime"
    },
    {
        "id": "date_of_crime",
        "message": "**[LIVE DATA ANALYSIS]**\n\nThank you. When was the cyber incident first noticed? (Date/time it was reported)",
        "field": "date_of_crime",
        "next_step": "who_involved"
    },
    {
        "id": "who_involved",
        "message": "**[LIVE DATA ANALYSIS]**\n\nHow was it determined whether the attack was by an outsider or an insider user? (Method of attribution)",
        "field": "who_involved",
        "next_step": "damage_description"
    },
    {
        "id": "damage_description",
        "message": "**[LIVE DATA ANALYSIS]**\n\nWhat is the extent of the Damage Description or loss (e.g. data stolen, service disruption, financial impact)?",
        "field": "damage_description",
        "next_step": "suspect_name"
    },
    {
        "id": "suspect_name",
        "message": "**[LIVE DATA ANALYSIS]**\n\nWho is the potential intruder or prime suspect? (Names or identifiers of suspect accounts or groups)",
        "field": "suspect_name",
        "next_step": "suspect_identity"
    },
    {
        "id": "suspect_identity",
        "message": "**[LIVE DATA ANALYSIS]**\n\nOn what basis was the suspect identified? (Evidence or indicators leading to suspicion)",
        "field": "suspect_identity",
        "next_step": "suspect_motive"
    },
    {
        "id": "suspect_motive",
        "message": "**[LIVE DATA ANALYSIS]**\n\nWhat is the likely motive or impact on the organization's operations? (Business disruption, financial gain, espionage)",
        "field": "suspect_motive",
        "next_step": "affected_assets"
    },
    {
        "id": "affected_assets",
        "message": "**[LIVE DATA ANALYSIS]**\n\nWhich critical systems, networks or data assets were involved or affected? (Servers, databases, user accounts)",
        "field": "affected_assets",
        "next_step": "evidence"
    },
    {
        "id": "evidence",
        "message": "**[LIVE DATA ANALYSIS]**\n\nWhat steps have been taken to preserve and analyze digital evidence? (Images of drives, log captures, malware samples)",
        "field": "evidence",
        "next_step": "evidence_collection"
    },
    {
        "id": "evidence_collection",
        "message": "**[LIVE DATA ANALYSIS]**\n\nWere all devices and data collected by trained personnel, following chain-of-custody procedures? (Evidence handling protocols)",
        "field": "evidence_collection",
        "next_step": "timeline_intrusion"
    },
    {
        "id": "timeline_intrusion",
        "message": "**[LIVE DATA ANALYSIS]**\n\nWhat is the timeline of the intrusion and incident events? (Dates/times of initial compromise, discovery, and response)",
        "field": "timeline_intrusion",
        "next_step": "type_of_crime"
    },
    {
        "id": "type_of_crime",
        "message": "**[LIVE DATA ANALYSIS]**\n\nWhat category of cybercrime is suspected (e.g. hacking, phishing, malware, ransomware, identity theft)?",
        "field": "type_of_crime",
        "next_step": "asset_affected"
    },
    {
        "id": "asset_affected",
        "message": "**[LIVE DATA ANALYSIS]**\n\nWhich digital assets or user accounts were targeted or compromised? (Email accounts, cloud storage, network credentials)",
        "field": "asset_affected",
        "next_step": "cyber_forensic"
    },
    {
        "id": "cyber_forensic",
        "message": "**[LIVE DATA ANALYSIS]**\n\nWhat cyber-forensic resources or agencies have been engaged? (e.g. CERTs, cybercrime units, external labs)",
        "field": "cyber_forensic",
        "next_step": "analysis"
    },
    {
        "id": "analysis",
        "message": "**[LIVE DATA ANALYSIS]**\n\nThank you for providing all the case details. I'll now analyze this information and provide you with a comprehensive report.",
        "field": None,
        "next_step": None
    }
]

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

class MurderPDFGenerator:
    """PDF generator for murder investigation reports"""

    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab")

    def generate_murder_pdf(self, case_data: Dict[str, Any], analysis_text: str) -> BytesIO:
        """Generate a murder investigation PDF report"""
        buffer = BytesIO()

        try:
            # Create the PDF document
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                                   topMargin=72, bottomMargin=18)

            # Get custom styles
            styles = self.create_murder_styles()

            # Build the story (content)
            story = []

            # Title
            story.append(Paragraph("HOMICIDE INVESTIGATION REPORT", styles['title']))
            story.append(Spacer(1, 20))

            # Header information with proper paragraph formatting
            header_data = [
                [self.create_table_cell_paragraph('Case ID:', styles, bold=True),
                 self.create_table_cell_paragraph(case_data.get('case_id', 'N/A'), styles, bold=False)],
                [self.create_table_cell_paragraph('Date Generated:', styles, bold=True),
                 self.create_table_cell_paragraph(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), styles, bold=False)],
                [self.create_table_cell_paragraph('Investigation Date:', styles, bold=True),
                 self.create_table_cell_paragraph(case_data.get('date_of_crime', 'N/A'), styles, bold=False)]
            ]

            header_table = Table(header_data, colWidths=[1.8*inch, 4.7*inch])
            header_table.setStyle(TableStyle([
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(header_table)
            story.append(Spacer(1, 15))

            # Case details section
            case_details = self.format_case_details(case_data)
            if case_details:
                story.append(Paragraph("CASE DETAILS", styles['section_header']))
                story.append(Spacer(1, 10))

                # Adjust column widths for better text wrapping
                case_table = Table(case_details, colWidths=[2.2*inch, 4.3*inch])
                case_table.setStyle(TableStyle([
                    # Remove font settings since we're using Paragraph objects now
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
                ]))
                story.append(case_table)
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

    def format_case_details(self, case_data: Dict[str, Any]) -> list:
        """Format case details for the PDF with proper text wrapping"""
        details = []
        styles = self.create_murder_styles()

        field_mapping = [
            ('date_of_crime', 'Date of Crime:'),
            ('time_of_crime', 'Time of Crime:'),
            ('location', 'Location:'),
            ('victim_name', 'Victim Name:'),
            ('victim_age', 'Victim Age:'),
            ('victim_gender', 'Victim Gender:'),
            ('cause_of_death', 'Cause of Death:'),
            ('weapon_used', 'Weapon Used:'),
            ('crime_scene_description', 'Crime Scene:'),
            ('witnesses', 'Witnesses:'),
            ('evidence_found', 'Evidence:'),
            ('suspects', 'Suspects:'),
            ('additional_notes', 'Additional Notes:')
        ]

        for data_key, display_name in field_mapping:
            if data_key in case_data and case_data[data_key]:
                value = str(case_data[data_key]).strip()
                if value and value.lower() not in ['n/a', 'none', 'unknown', '']:
                    # Format long text for better display in tables
                    if len(value) > 80:  # For longer text, add strategic breaks
                        formatted_value = self.format_long_text_for_table(value, max_length=80)
                    else:
                        formatted_value = value

                    # Create paragraphs for proper text wrapping
                    label_paragraph = self.create_table_cell_paragraph(display_name, styles, bold=True)
                    value_paragraph = self.create_table_cell_paragraph(formatted_value, styles, bold=False)
                    details.append([label_paragraph, value_paragraph])

        return details

    def create_table_cell_paragraph(self, text: str, styles: dict, bold: bool = False) -> Paragraph:
        """Create a paragraph for table cell with proper wrapping"""
        # Ensure text is properly escaped and cleaned
        clean_text = str(text).strip()

        # Create a style for table cells with better wrapping
        if bold:
            cell_style = ParagraphStyle(
                'TableCellBold',
                parent=styles['analysis_text'],
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
                parent=styles['analysis_text'],
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
        """Format analysis text into structured paragraphs with proper sub-sections"""
        paragraphs = []

        if not analysis_text:
            return paragraphs

        # Define the expected sub-sections with patterns
        section_patterns = [
            ("1. Comprehensive Analysis of the Case", "1."),
            ("2. Potential Motives and Suspects to Consider", "2."),
            ("3. Recommended Investigative Approaches", "3."),
            ("4. Key Evidence to Focus On and Analysis", "4."),
            ("5. Possible Solutions or Conclusions", "5.")
        ]

        # Split text into sections using regex-like approach
        import re

        # Clean the text first
        clean_text = self.clean_markdown_text(analysis_text)

        # Split by numbered sections
        sections = []
        current_section = ""
        current_title = ""

        lines = clean_text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip unwanted headers
            if '[LIVE DATA ANALYSIS]' in line or line.startswith('Case Analysis:'):
                continue

            # Check if this is a section header
            is_section_header = False
            for full_title, pattern in section_patterns:
                if (pattern in line and ("Comprehensive Analysis" in line or
                                       "Potential Motives" in line or
                                       "Recommended Investigative" in line or
                                       "Key Evidence" in line or
                                       "Possible Solutions" in line)):
                    is_section_header = True

                    # Save previous section if exists
                    if current_title and current_section:
                        sections.append((current_title, current_section.strip()))

                    # Start new section
                    current_title = line.replace('**', '').strip()
                    current_section = ""
                    break

            if not is_section_header and current_title:
                # Add content to current section
                clean_line = line.replace('**', '').replace('*', '').strip()
                if clean_line:
                    current_section += clean_line + " "

        # Add the last section
        if current_title and current_section:
            sections.append((current_title, current_section.strip()))

        # Convert sections to paragraphs
        for title, content in sections:
            if title and content:
                # Add section header
                paragraphs.append(Paragraph(title, styles['sub_header']))
                paragraphs.append(Spacer(1, 6))

                # Format content with bullet points
                formatted_content = content.replace('- ', '\n• ')
                if formatted_content.startswith('\n'):
                    formatted_content = formatted_content[1:]

                # Add content paragraph
                paragraphs.append(Paragraph(formatted_content, styles['analysis_text']))
                paragraphs.append(Spacer(1, 12))

        return paragraphs

    def clean_markdown_text(self, text: str) -> str:
        """Clean markdown formatting from text while preserving structure"""
        if not text:
            return ""

        clean_text = str(text).strip()

        # Remove specific unwanted headers but preserve structure
        clean_text = clean_text.replace('[LIVE DATA ANALYSIS]', '')

        # Remove excessive markdown formatting but keep basic structure
        # clean_text = clean_text.replace('###', '')
        # clean_text = clean_text.replace('##', '')
        # clean_text = clean_text.replace('#', '')

        # Preserve line breaks for section parsing
        # Don't normalize all whitespace - keep line structure
        lines = clean_text.split('\n')
        cleaned_lines = []
        for line in lines:
            cleaned_line = line.strip()
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
            else:
                cleaned_lines.append('')  # Preserve empty lines for section breaks

        return '\n'.join(cleaned_lines)

    def create_murder_styles(self):
        """Create professional styles for murder investigation PDFs"""
        styles = getSampleStyleSheet()

        custom_styles = {
            'title': ParagraphStyle(
                'MurderTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#8b0000'),
                fontName='Helvetica-Bold'
            ),
            'section_header': ParagraphStyle(
                'MurderHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=20,
                textColor=colors.HexColor('#8b0000'),
                fontName='Helvetica-Bold'
            ),
            'sub_header': ParagraphStyle(
                'SubHeader',
                parent=styles['Heading3'],
                fontSize=12,
                spaceAfter=8,
                spaceBefore=15,
                textColor=colors.HexColor('#2c3e50'),
                fontName='Helvetica-Bold',
                leftIndent=0,
                bulletIndent=0
            ),
            'analysis_text': ParagraphStyle(
                'AnalysisText',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=8,
                spaceBefore=4,
                alignment=TA_JUSTIFY,
                fontName='Helvetica',
                leftIndent=0
            ),
            'footer': ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                alignment=TA_CENTER,
                textColor=colors.grey,
                fontName='Helvetica'
            )
        }

        return custom_styles


class MurderAgent:
    def __init__(self):
        self.nvidia_api_key = NVIDIA_API_KEY
        self.nvidia_client = None

    def get_step_by_id(self, step_id):
        """Get step configuration by ID"""
        for step in MURDER_CASE_INFO_STEPS:
            if step["id"] == step_id:
                return step
        return None

    def create_new_conversation_state(self):
        """Create a new conversation state"""
        session_id = str(uuid.uuid4())
        murder_conversation_states[session_id] = {
            "current_step": "greeting",
            "collected_data": {},
            "last_updated": datetime.now().isoformat()
        }
        return session_id

    def store_user_input(self, session_id: str, step_id: str, user_input: str) -> Tuple[bool, Optional[str]]:
        """Store user input in the conversation state"""
        if session_id not in murder_conversation_states:
            return False, "Session not found"

        current_step = self.get_step_by_id(step_id)
        if not current_step:
            return False, "Invalid step"

        if current_step["field"]:
            murder_conversation_states[session_id]["collected_data"][current_step["field"]] = user_input

        return True, None

    def advance_to_next_step(self, session_id, current_step_id):
        """Advance to the next step in the conversation"""
        if session_id not in murder_conversation_states:
            return False

        current_step = self.get_step_by_id(current_step_id)
        if not current_step:
            return False

        if current_step["next_step"]:
            next_step_id = current_step["next_step"]
            murder_conversation_states[session_id]["current_step"] = next_step_id
            return True

        return False

    def call_nvidia_api(self, prompt: str) -> str:
        """Call NVIDIA API using OpenAI client"""
        try:
            # Get the NVIDIA client
            client = get_nvidia_client()
            if not client or not OPENAI_AVAILABLE:
                logger.warning("OpenAI client not available, using fallback analysis")
                return self.generate_fallback_analysis()

            logger.info(f"Calling NVIDIA API with model: {NVIDIA_MODEL}")

            # Create completion using OpenAI client
            completion = client.chat.completions.create(
                model=NVIDIA_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a specialized AI assistant for homicide investigations. Provide detailed, professional analysis of murder cases with comprehensive insights on motives, suspects, evidence, and investigative approaches."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.6,
                top_p=0.95,
                max_tokens=4096,
                frequency_penalty=0,
                presence_penalty=0,
                stream=False
            )

            # Extract the response content
            response_content = completion.choices[0].message.content
            logger.info("Successfully got response from NVIDIA API")
            return response_content

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
            if session_id and session_id in murder_conversation_states:
                del murder_conversation_states[session_id]
            session_id = self.create_new_conversation_state()
            current_step = self.get_step_by_id("greeting")
            return session_id, current_step["message"], True, "greeting", None

        # Create new session if none exists
        if not session_id or session_id not in murder_conversation_states:
            session_id = self.create_new_conversation_state()
            if not message:
                current_step = self.get_step_by_id("greeting")
                return session_id, current_step["message"], True, "greeting", None

        conv_state = murder_conversation_states[session_id]
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
                murder_conversation_states[session_id]["analysis_result"] = analysis
                murder_conversation_states[session_id]["analysis_completed"] = True
                murder_conversation_states[session_id]["current_step"] = "completed"
                return session_id, analysis, False, "completed", None

            # Return next question
            if current_step and current_step["message"]:
                return session_id, current_step["message"], True, current_step_id, None

        # Default response
        current_step = self.get_step_by_id(current_step_id)
        return session_id, current_step["message"] if current_step else "What would you like to know?", True, current_step_id, None


# Pydantic Models for Cyber Crime Agent
class CyberCrimeAgentRequest(BaseModel):
    question: str = Field(default="", description="User's question or input")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation continuity")
    force_new_session: bool = Field(default=False, description="Force creation of new session")
    forceReset: bool = Field(default=False, description="Alternative field for forcing reset")

class CyberCrimeAgentData(BaseModel):
    analysis: str = Field(description="AI analysis response")
    is_collecting_info: bool = Field(description="Whether still collecting case information")
    current_step: str = Field(description="Current step in the investigation process")
    collected_data: Dict[str, Any] = Field(default_factory=dict, description="Collected case data")
    error: Optional[str] = Field(default=None, description="Error message if any")

class CyberCrimeAgentResponse(BaseModel):
    success: bool = Field(description="Whether the request was successful")
    data: CyberCrimeAgentData = Field(description="Response data")
    session_id: str = Field(description="Session ID")
    message: str = Field(description="Status message")

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

class CyberCrimeAgent:
    def __init__(self):
        self.nvidia_api_key = NVIDIA_API_KEY
        self.nvidia_client = None

    def get_step_by_id(self, step_id):
        """Get step configuration by ID"""
        for step in CYBER_CRIME_CASE_INFO_STEPS:
            if step["id"] == step_id:
                return step
        return None

    def create_new_conversation_state(self):
        """Create a new conversation state"""
        session_id = str(uuid.uuid4())
        cybercrime_conversation_states[session_id] = {
            "current_step": "greeting",
            "collected_data": {},
            "last_updated": datetime.now().isoformat()
        }
        return session_id

    def store_user_input(self, session_id: str, step_id: str, user_input: str) -> Tuple[bool, Optional[str]]:
        """Store user input in the conversation state"""
        if session_id not in cybercrime_conversation_states:
            return False, "Session not found"

        current_step = self.get_step_by_id(step_id)
        if not current_step:
            return False, "Invalid step"

        if current_step["field"]:
            cybercrime_conversation_states[session_id]["collected_data"][current_step["field"]] = user_input

        return True, None

    def advance_to_next_step(self, session_id, current_step_id):
        """Advance to the next step in the conversation"""
        if session_id not in cybercrime_conversation_states:
            return False

        current_step = self.get_step_by_id(current_step_id)
        if not current_step:
            return False

        if current_step["next_step"]:
            next_step_id = current_step["next_step"]
            cybercrime_conversation_states[session_id]["current_step"] = next_step_id
            return True

        return False

    def call_nvidia_api(self, prompt: str) -> str:
        """Call NVIDIA API using OpenAI client for cybercrime analysis"""
        try:
            # Get the NVIDIA client
            client = get_nvidia_client()
            if not client or not OPENAI_AVAILABLE:
                logger.warning("OpenAI client not available for cybercrime analysis, using fallback")
                return self.generate_fallback_analysis()

            logger.info(f"Calling NVIDIA API for cybercrime with model: {NVIDIA_MODEL}")

            # Create completion using OpenAI client
            completion = client.chat.completions.create(
                model=NVIDIA_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a specialized AI assistant for cybercrime investigations and digital forensics. Provide detailed, professional analysis of cybercrime cases with comprehensive insights on digital evidence, threat actors, attack vectors, and investigative approaches."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.6,
                top_p=0.95,
                max_tokens=4096,
                frequency_penalty=0,
                presence_penalty=0,
                stream=False
            )

            # Extract the response content
            response_content = completion.choices[0].message.content
            logger.info("Successfully got cybercrime response from NVIDIA API")
            return response_content

        except Exception as e:
            logger.error(f"Error calling NVIDIA API for cybercrime: {str(e)}")
            return self.generate_fallback_analysis()

    def generate_fallback_analysis(self) -> str:
        """Generate fallback analysis for cybercrime cases if NVIDIA API fails"""
        return """**[LIVE DATA ANALYSIS]**

**Cybercrime Investigation Report**

I apologize, but I'm currently unable to connect to the advanced analysis system. However, I can provide a comprehensive framework for your cybercrime investigation:

**1. Executive Summary**
- Cybersecurity incident requiring immediate attention
- Digital forensics analysis in progress
- Comprehensive investigation framework established

**2. Incident Classification and Threat Assessment**
- Categorize the type of cybercrime (malware, phishing, data breach, etc.)
- Assess threat actor sophistication level
- Analyze attack vectors and entry points

**3. Technical Analysis**
- Preserve all digital evidence using forensically sound methods
- Analyze system logs and network traffic
- Identify compromised systems and data
- Reconstruct attack timeline and methodology

**4. Impact Assessment**
- Evaluate business operations impact
- Assess data compromise scope
- Calculate financial and reputational losses
- Review regulatory compliance implications

**5. Attribution Analysis**
- Analyze digital fingerprints and indicators
- Review threat intelligence sources
- Assess confidence levels in suspect identification
- Document evidence supporting attribution

**6. Forensic Findings**
- Maintain proper chain of custody
- Document all digital evidence
- Ensure evidence admissibility in legal proceedings
- Prepare forensic reports and documentation

**7. Recommended Actions**
- Immediate: Isolate affected systems
- Short-term: Implement containment measures
- Long-term: Strengthen security posture
- Legal: Prepare for potential prosecution

**8. Compliance and Regulatory Considerations**
- Review breach notification requirements
- Assess regulatory reporting obligations
- Consider industry-specific compliance needs
- Document all remediation efforts

**Important Notes:**
- Ensure all investigative steps follow legal procedures
- Maintain detailed documentation throughout the process
- Consider engaging external cybersecurity experts
- Coordinate with law enforcement if criminal activity is suspected

Please try refreshing the system or contact technical support if this issue persists.
"""

    def analyze_case(self, case_data):
        """Analyze the cybercrime case using NVIDIA API with fallback"""
        try:
            # Create a comprehensive prompt for cybercrime analysis
            prompt = f"""
            As an expert cybercrime investigator and digital forensics analyst, analyze the following cybercrime case data and provide a comprehensive investigation report:

            **CASE INFORMATION:**
            Case ID: {case_data.get('case_id', 'Not provided')}
            Date of Incident: {case_data.get('date_of_crime', 'Not provided')}
            Attribution Method: {case_data.get('who_involved', 'Not provided')}
            Damage Description: {case_data.get('damage_description', 'Not provided')}
            Suspect Information: {case_data.get('suspect_name', 'Not provided')}
            Suspect Identification Basis: {case_data.get('suspect_identity', 'Not provided')}
            Suspected Motive: {case_data.get('suspect_motive', 'Not provided')}
            Affected Assets: {case_data.get('affected_assets', 'Not provided')}
            Evidence Preservation: {case_data.get('evidence', 'Not provided')}
            Evidence Collection Procedures: {case_data.get('evidence_collection', 'Not provided')}
            Timeline of Events: {case_data.get('timeline_intrusion', 'Not provided')}
            Type of Cybercrime: {case_data.get('type_of_crime', 'Not provided')}
            Compromised Assets: {case_data.get('asset_affected', 'Not provided')}
            Forensic Resources: {case_data.get('cyber_forensic', 'Not provided')}

            **ANALYSIS REQUIREMENTS:**
            Please provide a detailed analysis covering:

            1. **Executive Summary**
               - Brief overview of the incident
               - Key findings and impact assessment

            2. **Incident Classification and Threat Assessment**
               - Categorization of the cybercrime
               - Threat actor profiling
               - Attack vector analysis

            3. **Technical Analysis**
               - Digital evidence evaluation
               - Attack methodology reconstruction
               - System vulnerabilities exploited

            4. **Impact Assessment**
               - Business impact analysis
               - Data compromise assessment
               - Financial and operational losses

            5. **Attribution Analysis**
               - Suspect identification confidence level
               - Evidence supporting attribution
               - Potential threat actor motivations

            6. **Forensic Findings**
               - Digital evidence summary
               - Chain of custody assessment
               - Evidence reliability and admissibility

            7. **Recommended Actions**
               - Immediate containment measures
               - Further investigative steps
               - Legal proceedings recommendations
               - Security improvements

            8. **Compliance and Regulatory Considerations**
               - Breach notification requirements
               - Regulatory compliance issues
               - Industry-specific considerations

            Provide professional, detailed analysis suitable for law enforcement, legal proceedings, and organizational decision-making.
            """

            return self.call_nvidia_api(prompt)

        except Exception as e:
            logger.error(f"Error in cybercrime analyze_case: {str(e)}")
            return self.generate_fallback_analysis()

    def process_message(self, message: str, session_id: Optional[str] = None, force_new_session: bool = False) -> Tuple[str, str, bool, str, Optional[str]]:
        """Process user message and return response"""
        try:
            logger.info(f"Processing message: {message[:100]}...")

            # Handle reset or new session requests
            if message and message.lower() in ["reset", "restart", "start over"] or force_new_session:
                if session_id and session_id in cybercrime_conversation_states:
                    del cybercrime_conversation_states[session_id]
                session_id = self.create_new_conversation_state()
                current_step = self.get_step_by_id("greeting")
                return session_id, current_step["message"], True, "greeting", None

            # Create new session if none exists
            if not session_id or session_id not in cybercrime_conversation_states:
                session_id = self.create_new_conversation_state()
                if not message:
                    current_step = self.get_step_by_id("greeting")
                    return session_id, current_step["message"], True, "greeting", None

            conv_state = cybercrime_conversation_states[session_id]
            current_step_id = conv_state["current_step"]

            # Handle greeting step without message
            if current_step_id == "greeting" and not message:
                current_step = self.get_step_by_id("greeting")
                return session_id, current_step["message"], True, "greeting", None

            # Store user input and advance to next step
            if message:
                success, error = self.store_user_input(session_id, current_step_id, message)
                if not success:
                    return session_id, f"Error storing input: {error}", True, current_step_id, error

                # Advance to next step
                if self.advance_to_next_step(session_id, current_step_id):
                    current_step_id = cybercrime_conversation_states[session_id]["current_step"]

            # Check if we've reached the analysis step
            if current_step_id == "analysis":
                analysis = self.analyze_case(conv_state["collected_data"])
                cybercrime_conversation_states[session_id]["analysis_result"] = analysis
                cybercrime_conversation_states[session_id]["analysis_completed"] = True
                cybercrime_conversation_states[session_id]["current_step"] = "completed"
                return session_id, analysis, False, "completed", None

            # Return next question
            current_step = self.get_step_by_id(current_step_id)
            if current_step:
                return session_id, current_step["message"], True, current_step_id, None

        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}")
            return session_id or "error", f"I apologize, but I encountered an error: {str(e)}", True, "error", str(e)

        # Default response
        current_step = self.get_step_by_id(current_step_id)
        return session_id, current_step["message"] if current_step else "What would you like to know?", True, current_step_id, None


class CybercrimePDFGenerator:
    """PDF generator for cybercrime investigation reports"""

    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab")

    def generate_cybercrime_pdf(self, case_data: Dict[str, Any], analysis_text: str) -> BytesIO:
        """Generate a cybercrime investigation PDF report"""
        buffer = BytesIO()

        try:
            # Create the PDF document
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                                   topMargin=72, bottomMargin=18)

            # Get custom styles
            styles = self.create_cybercrime_styles()

            # Build the story (content)
            story = []

            # Title
            story.append(Paragraph("CYBERCRIME INVESTIGATION REPORT", styles['title']))
            story.append(Spacer(1, 20))

            # Header information
            story.append(Paragraph("DIGITAL FORENSICS ANALYSIS", styles['section_header']))
            story.append(Spacer(1, 10))

            # Case details table
            case_details = self.format_cybercrime_case_details(case_data)
            if case_details:
                story.extend(case_details)
                story.append(Spacer(1, 20))

            # Analysis section
            if analysis_text:
                story.append(Paragraph("COMPREHENSIVE CYBERCRIME ANALYSIS", styles['section_header']))
                story.append(Spacer(1, 10))

                # Format analysis text
                analysis_paragraphs = self.format_analysis_text(analysis_text, styles)
                for paragraph in analysis_paragraphs:
                    story.append(paragraph)
                    story.append(Spacer(1, 6))

                story.append(Spacer(1, 15))

            # Digital evidence section
            story.append(Paragraph("DIGITAL EVIDENCE SUMMARY", styles['section_header']))
            story.append(Spacer(1, 10))

            evidence_summary = self.create_evidence_summary(case_data, styles)
            story.extend(evidence_summary)
            story.append(Spacer(1, 15))

            # Recommendations section
            story.append(Paragraph("CYBERSECURITY RECOMMENDATIONS", styles['section_header']))
            story.append(Spacer(1, 10))

            recommendations = self.create_cybersecurity_recommendations(styles)
            story.extend(recommendations)
            story.append(Spacer(1, 15))

            # Footer
            story.append(Spacer(1, 20))
            story.append(Paragraph("--- End of Cybercrime Investigation Report ---", styles['footer']))

            # Build the PDF
            doc.build(story)
            buffer.seek(0)

            return buffer

        except Exception as e:
            logger.error(f"Error generating cybercrime PDF: {str(e)}")
            # Create a simple error PDF
            buffer = BytesIO()
            try:
                doc = SimpleDocTemplate(buffer, pagesize=A4)
                styles = getSampleStyleSheet()
                story = [Paragraph(f"Error generating cybercrime PDF: {str(e)}", styles['Title'])]
                doc.build(story)
            except:
                buffer.write(f"Error generating cybercrime PDF: {str(e)}".encode('utf-8'))
            buffer.seek(0)
            return buffer

    def format_cybercrime_case_details(self, case_data: Dict[str, Any]) -> list:
        """Format cybercrime case details for the PDF"""
        details = []
        styles = self.create_cybercrime_styles()

        field_mapping = [
            ('case_id', 'Case ID:'),
            ('date_of_crime', 'Date of Incident:'),
            ('who_involved', 'Attribution Method:'),
            ('damage_description', 'Damage Description:'),
            ('suspect_name', 'Suspect Information:'),
            ('suspect_identity', 'Suspect Identification Basis:'),
            ('suspect_motive', 'Suspected Motive:'),
            ('affected_assets', 'Affected Assets:'),
            ('evidence', 'Evidence Preservation:'),
            ('evidence_collection', 'Evidence Collection Procedures:'),
            ('timeline_intrusion', 'Timeline of Events:'),
            ('type_of_crime', 'Type of Cybercrime:'),
            ('asset_affected', 'Compromised Assets:'),
            ('cyber_forensic', 'Forensic Resources:')
        ]

        # Create table data
        table_data = []
        for field_key, field_label in field_mapping:
            value = case_data.get(field_key, 'Not provided')
            if value and value.strip():
                # Wrap long text
                if len(str(value)) > 60:
                    wrapped_value = Paragraph(str(value), styles['table_text'])
                else:
                    wrapped_value = str(value)
                table_data.append([field_label, wrapped_value])

        if table_data:
            # Create table
            table = Table(table_data, colWidths=[2*inch, 4*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#dc3545')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            details.append(table)

        return details

    def create_evidence_summary(self, case_data: Dict[str, Any], styles) -> list:
        """Create digital evidence summary section"""
        content = []

        evidence_items = [
            "Digital Evidence Collected:",
            f"• Evidence Preservation: {case_data.get('evidence', 'Not specified')}",
            f"• Collection Procedures: {case_data.get('evidence_collection', 'Not specified')}",
            f"• Affected Systems: {case_data.get('affected_assets', 'Not specified')}",
            f"• Compromised Assets: {case_data.get('asset_affected', 'Not specified')}",
            "",
            "Chain of Custody:",
            "• All digital evidence has been properly documented",
            "• Forensic imaging completed using write-blocking tools",
            "• Hash values calculated for integrity verification",
            "• Evidence stored in secure, climate-controlled environment",
            "",
            "Technical Analysis:",
            f"• Forensic Resources Used: {case_data.get('cyber_forensic', 'Not specified')}",
            "• Network traffic analysis completed",
            "• Malware analysis performed where applicable",
            "• Timeline reconstruction based on system logs"
        ]

        for item in evidence_items:
            if item.strip():
                content.append(Paragraph(item, styles['body_text']))
            else:
                content.append(Spacer(1, 6))

        return content

    def create_cybersecurity_recommendations(self, styles) -> list:
        """Create cybersecurity recommendations section"""
        content = []

        recommendations = [
            "Immediate Actions:",
            "• Isolate affected systems to prevent further compromise",
            "• Change all potentially compromised passwords and credentials",
            "• Apply security patches to all systems",
            "• Monitor network traffic for suspicious activity",
            "",
            "Long-term Security Improvements:",
            "• Implement multi-factor authentication (MFA)",
            "• Deploy endpoint detection and response (EDR) solutions",
            "• Conduct regular security awareness training",
            "• Establish incident response procedures",
            "• Perform regular vulnerability assessments",
            "",
            "Compliance Considerations:",
            "• Review data breach notification requirements",
            "• Document all remediation efforts",
            "• Consider third-party security audit",
            "• Update security policies and procedures"
        ]

        for item in recommendations:
            if item.strip():
                content.append(Paragraph(item, styles['body_text']))
            else:
                content.append(Spacer(1, 6))

        return content

    def create_cybercrime_styles(self):
        """Create professional styles for cybercrime investigation PDFs"""
        styles = getSampleStyleSheet()

        custom_styles = {
            'title': ParagraphStyle(
                'CybercrimeTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#dc3545'),
                fontName='Helvetica-Bold'
            ),
            'section_header': ParagraphStyle(
                'CybercrimeHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=20,
                textColor=colors.HexColor('#dc3545'),
                fontName='Helvetica-Bold'
            ),
            'sub_header': ParagraphStyle(
                'SubHeader',
                parent=styles['Heading3'],
                fontSize=12,
                spaceAfter=8,
                spaceBefore=15,
                textColor=colors.HexColor('#2c3e50'),
                fontName='Helvetica-Bold',
                leftIndent=0,
                bulletIndent=0
            ),
            'body_text': ParagraphStyle(
                'CybercrimeBody',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                alignment=TA_JUSTIFY,
                leftIndent=0,
                rightIndent=0,
                fontName='Helvetica'
            ),
            'table_text': ParagraphStyle(
                'TableText',
                parent=styles['Normal'],
                fontSize=9,
                alignment=TA_LEFT,
                fontName='Helvetica'
            ),
            'footer': ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#666666'),
                fontName='Helvetica-Oblique'
            ),
            'bullet_point': ParagraphStyle(
                'BulletPoint',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=4,
                leftIndent=20,
                bulletIndent=10,
                fontName='Helvetica'
            ),
            'analysis_header': ParagraphStyle(
                'AnalysisHeader',
                parent=styles['Heading3'],
                fontSize=12,
                spaceAfter=8,
                spaceBefore=12,
                textColor=colors.HexColor('#dc3545'),
                fontName='Helvetica-Bold'
            )
        }

        return custom_styles

    def format_analysis_text(self, analysis_text: str, styles) -> list:
        """Format analysis text for cybercrime PDF with proper structure"""
        paragraphs = []

        if not analysis_text:
            return [Paragraph("No analysis available.", styles['body_text'])]

        # Split text into sections
        sections = analysis_text.split('\n\n')

        for section in sections:
            if not section.strip():
                continue

            lines = section.strip().split('\n')

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Check if this is a section header
                if any(header in line for header in [
                    'Executive Summary', 'Incident Classification', 'Technical Analysis',
                    'Impact Assessment', 'Attribution Analysis', 'Forensic Findings',
                    'Recommended Actions', 'Compliance', 'EXECUTIVE SUMMARY',
                    'INCIDENT CLASSIFICATION', 'TECHNICAL ANALYSIS', 'IMPACT ASSESSMENT',
                    'ATTRIBUTION ANALYSIS', 'FORENSIC FINDINGS', 'RECOMMENDED ACTIONS',
                    'COMPLIANCE'
                ]):
                    # Clean up the header
                    clean_header = line.replace('**', '').replace('*', '').strip()
                    if clean_header.endswith(':'):
                        clean_header = clean_header[:-1]
                    paragraphs.append(Paragraph(clean_header, styles['analysis_header']))

                elif line.startswith('- ') or line.startswith('• '):
                    # Bullet point
                    bullet_text = line[2:].strip()
                    paragraphs.append(Paragraph(f"• {bullet_text}", styles['bullet_point']))

                elif line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                    # Numbered list
                    paragraphs.append(Paragraph(line, styles['bullet_point']))

                else:
                    # Regular paragraph
                    # Clean up markdown formatting
                    clean_line = line.replace('**', '').replace('*', '')
                    if clean_line.strip():
                        paragraphs.append(Paragraph(clean_line, styles['body_text']))

        return paragraphs if paragraphs else [Paragraph("Analysis text could not be formatted.", styles['body_text'])]


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
            As an expert {agent_name.lower()} investigator and forensic analyst, analyze the following case data and provide a comprehensive investigation report:

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


# Initialize the agents
murder_agent = MurderAgent()
cybercrime_agent = CyberCrimeAgent()

# Initialize generic agents for JSON-configured types
humantrafficking_agent = GenericAgent("humantrafficking")
narcotics_agent = GenericAgent("narcotics")
moneylaundering_agent = GenericAgent("moneylaundering")
onlinefraud_agent = GenericAgent("onlinefraud")
sexualassault_agent = GenericAgent("sexualassualt")  # Note: keeping original filename spelling
surveillance_agent = GenericAgent("surveillance")
theft_agent = GenericAgent("theft")

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
            "theft_agent": "active"
        }
    }

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
                collected_data=murder_conversation_states[session_id]["collected_data"] if session_id in murder_conversation_states else {},
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

@app.post("/api/cybercrime", response_model=CyberCrimeAgentResponse)
async def cybercrime_agent_endpoint(request: CyberCrimeAgentRequest):
    """Main endpoint for cybercrime agent interactions"""
    try:
        # Health check
        if request.question == "ping":
            return CyberCrimeAgentResponse(
                success=True,
                data=CyberCrimeAgentData(
                    analysis="Cybercrime Agent is running",
                    is_collecting_info=False,
                    current_step="ping",
                    collected_data={},
                    error=None
                ),
                session_id="ping_session",
                message="Health check successful"
            )

        force_new_session = request.force_new_session or request.forceReset

        session_id, response, is_collecting_info, current_step, error_message = cybercrime_agent.process_message(
            request.question,
            request.session_id,
            force_new_session=force_new_session
        )

        return CyberCrimeAgentResponse(
            success=True,
            data=CyberCrimeAgentData(
                analysis=response,
                is_collecting_info=is_collecting_info,
                current_step=current_step,
                collected_data=cybercrime_conversation_states[session_id]["collected_data"] if session_id in cybercrime_conversation_states else {},
                error=error_message
            ),
            session_id=session_id,
            message="Message processed successfully"
        )

    except Exception as e:
        logger.error(f"Error in cybercrime_agent_endpoint: {str(e)}")
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

@app.post("/api/murder/download-pdf")
async def download_murder_pdf(request: PDFDownloadRequest):
    """Generate and download PDF report for murder investigation"""
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
        if not session_id or session_id not in murder_conversation_states:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": "Invalid session ID or session not found"
                }
            )

        conv_state = murder_conversation_states[session_id]

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
        pdf_generator = MurderPDFGenerator()
        pdf_buffer = pdf_generator.generate_murder_pdf(case_data, analysis_text)

        # Generate filename
        case_id = case_data.get('case_id', 'Unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Murder_Investigation_Report_{case_id}_{timestamp}.pdf"

        # Return PDF file as streaming response
        return StreamingResponse(
            BytesIO(pdf_buffer.read()),
            media_type='application/pdf',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in download_murder_pdf: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"Error generating PDF: {str(e)}"
            }
        )

@app.post("/api/cybercrime/download-pdf")
async def download_cybercrime_pdf(request: PDFDownloadRequest):
    """Generate and download PDF report for cybercrime investigation"""
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
        if not session_id or session_id not in cybercrime_conversation_states:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": "Invalid session ID or session not found"
                }
            )

        conv_state = cybercrime_conversation_states[session_id]

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

        # Generate PDF using cybercrime-specific generator
        pdf_generator = CybercrimePDFGenerator()
        pdf_buffer = pdf_generator.generate_cybercrime_pdf(case_data, analysis_text)

        # Generate filename
        case_id = case_data.get('case_id', 'Unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Cybercrime_Investigation_Report_{case_id}_{timestamp}.pdf"

        # Return PDF file as streaming response
        return StreamingResponse(
            BytesIO(pdf_buffer.read()),
            media_type='application/pdf',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in download_cybercrime_pdf: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"Error generating PDF: {str(e)}"
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
        """Format case details for the PDF"""
        details = []
        styles = self.create_generic_styles()

        if not case_data:
            details.append(Paragraph("No case data available", styles['body_text']))
            return details

        # Create table data
        table_data = []
        for key, value in case_data.items():
            if value:  # Only include non-empty values
                # Format field name
                field_name = key.replace('_', ' ').title() + ':'
                # Ensure value is string and limit length
                field_value = str(value)[:200] + ('...' if len(str(value)) > 200 else '')
                table_data.append([field_name, field_value])

        if table_data:
            # Create table
            table = Table(table_data, colWidths=[2*inch, 4*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            details.append(table)

        return details

    def format_analysis_text(self, analysis_text: str, styles) -> list:
        """Format analysis text into paragraphs"""
        paragraphs = []

        if not analysis_text:
            return [Paragraph("No analysis available.", styles['body_text'])]

        # Split text into lines and process
        lines = analysis_text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for headers
            if any(header in line.upper() for header in [
                'EXECUTIVE SUMMARY', 'CASE ASSESSMENT', 'EVIDENCE ANALYSIS',
                'RECOMMENDATIONS', 'NEXT STEPS', 'RISK ASSESSMENT', 'LEGAL CONSIDERATIONS'
            ]):
                clean_header = line.replace('**', '').replace('*', '').strip()
                if clean_header.endswith(':'):
                    clean_header = clean_header[:-1]
                paragraphs.append(Paragraph(clean_header, styles['analysis_header']))
            elif line.startswith('- ') or line.startswith('• '):
                bullet_text = line[2:].strip()
                paragraphs.append(Paragraph(f"• {bullet_text}", styles['bullet_point']))
            elif line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                paragraphs.append(Paragraph(line, styles['bullet_point']))
            else:
                clean_line = line.replace('**', '').replace('*', '')
                if clean_line.strip():
                    paragraphs.append(Paragraph(clean_line, styles['body_text']))

        return paragraphs if paragraphs else [Paragraph("Analysis text could not be formatted.", styles['body_text'])]

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
    return await create_pdf_download_endpoint("online fraud", onlinefraud_conversation_states)(request)

@app.post("/api/sexualassault/download-pdf")
async def download_sexualassault_pdf(request: PDFDownloadRequest):
    return await create_pdf_download_endpoint("sexualassault", sexualassault_conversation_states)(request)

@app.post("/api/surveillance/download-pdf")
async def download_surveillance_pdf(request: PDFDownloadRequest):
    return await create_pdf_download_endpoint("surveillance", surveillance_conversation_states)(request)

@app.post("/api/theft/download-pdf")
async def download_theft_pdf(request: PDFDownloadRequest):
    return await create_pdf_download_endpoint("theft", theft_conversation_states)(request)

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