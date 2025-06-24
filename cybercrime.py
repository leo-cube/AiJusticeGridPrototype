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
    title="Cybercrime Agent API",
    description="AI-powered cybercrime investigation analysis system",
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

# NVIDIA API Configuration
NVIDIA_API_KEY = "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"
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

# Define the case information collection steps
CASE_INFO_STEPS = [
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
        "next_step": "Damage Description:"
    },
    {
        "id": "Damage Description:",
        "message": "**[LIVE DATA ANALYSIS]**\n\nWhat is the extent of the Damage Description: or loss (e.g. data stolen, service disruption, financial impact)?",
        "field": "Damage Description:",
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
        "message": "**[LIVE DATA ANALYSIS]**\n\nWhat is the likely motive or impact on the organization’s operations? (Business disruption, financial gain, espionage)",
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

# Dictionary to store conversation states
conversation_states = {}

# Pydantic Models for Request/Response validation
class CyberAgentRequest(BaseModel):
    question: str = Field(default="", description="User's question or input")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation continuity")
    force_new_session: bool = Field(default=False, description="Force creation of new session")
    forceReset: bool = Field(default=False, description="Alternative field for forcing reset")

class CyberAgentData(BaseModel):
    analysis: str = Field(description="AI analysis response")
    is_collecting_info: bool = Field(description="Whether still collecting case information")
    current_step: str = Field(description="Current step in the investigation process")
    collected_data: Dict[str, Any] = Field(default_factory=dict, description="Collected case data")
    error: Optional[str] = Field(default=None, description="Error message if any")

class CyberAgentResponse(BaseModel):
    success: bool = Field(description="Whether the request was successful")
    data: CyberAgentData = Field(description="Response data")
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

class CyberPDFGenerator:
    """PDF generator for cybercrime investigation reports"""

    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab")

    def generate_cyber_pdf(self, case_data: Dict[str, Any], analysis_text: str) -> BytesIO:
        """Generate a cybercrime investigation PDF report"""
        buffer = BytesIO()

        try:
            # Create the PDF document
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                                   topMargin=72, bottomMargin=18)

            # Get custom styles
            styles = self.create_cyber_styles()

            # Build the story (content)
            story = []

            # Title
            story.append(Paragraph("CYBERCRIME INVESTIGATION REPORT", styles['title']))
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
        styles = self.create_cyber_styles()

        field_mapping = [
            ('date_of_crime', 'Date of Crime:'),
            ('who_involved', 'Who Involved:'),
            ('Damage Description:', 'Damage Description::'),
            ('suspect_name', 'Suspect Name:'),
            ('suspect_identity', 'Suspect Identity:'),
            ('suspect_motive', 'Suspect Motive:'),
            ('affected_assets', 'Affected Assets:'),
            ('evidence', 'Evidence Found:'),
            ('evidence_collection', 'Evidence Collection Method:'),
            ('timeline_intrusion', 'Timeline of Events:'),
            ('type_of_crime', 'Type of Crime:'),
            ('asset_affected', 'Asset Affected:'),
            ('cyber_forensic', 'Cyber Forensic Notes:')
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
            ("2. Potential Motives and asset_affected to Consider", "2."),
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
        clean_text = clean_text.replace('###', '')
        clean_text = clean_text.replace('##', '')
        clean_text = clean_text.replace('#', '')

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

    def create_cyber_styles(self):
        """Create professional styles for cypercrime investigation PDFs"""
        styles = getSampleStyleSheet()

        custom_styles = {
            'title': ParagraphStyle(
                'CybercrimeTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#8b0000'),
                fontName='Helvetica-Bold'
            ),
            'section_header': ParagraphStyle(
                'CybercrimeHeading',
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

class CybercrimeAgent:
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
                        "content": "You are a specialized AI assistant for crybercrime investigations. Provide detailed, professional analysis of crybercrime cases with comprehensive insights on motives, asset_affected, evidence, and investigative approaches."
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
- Review all collected evidence and evidence_collection thoroughly
- Establish a clear timeline_intrusion of the incident
- Analyze suspect_name, suspect_identity, and suspect_motive for behavioral patterns
- Cross-reference the date_of_crime and who_involved to confirm involvement and timeline accuracy

**2. Potential Motives and asset_affected to Consider**
- Investigate suspect_motive for clues around emotional, personal, or ideological triggers
- Assess damage and affected_assets for material, digital, or physical losses
- Distinguish between targeted attacks and random intrusions based on patterns
- Consider how the asset_affected connects to the victim or suspects

**3. Recommended Investigative Approaches**
- Interview all individuals linked to the timeline_intrusion and who_involved
- Reconstruct evidence_collection procedures to validate integrity
- Cross-verify suspect_identity and alibis related to affected assets and presence near crime scene

**4. Key Evidence to Focus On and Analysis**
- Prioritize analysis of the crime scene and collected evidence
- Review witness details mentioned in evidence_collection
- Apply forensic techniques to cyber_forensic data and correlate with physical findings
- Validate the authenticity of asset_affected and affected_assets links to the case

**5. Possible Solutions or Conclusions**
- Proceed with a systematic evidence-based investigation
- Focus on leads connected to suspect_motive, timeline inconsistencies, and unusual damage patterns
- If technical elements (like cyber intrusion) are involved, deepen cyber_forensic assessments
- Seek outside expert consultation for specialized domains (e.g., digital, forensic, psychological)

Please ensure all evidence is properly documented and chain of custody is maintained."""

    def generate_analysis_prompt(self, case_details: Dict[str, Any]) -> str:
        """Generate prompt for NVIDIA API analysis"""
        prompt = f"""
Analyze the following cybercrime case and provide a comprehensive investigation report:

**Case Details:**
Case ID: {case_details.get('case_id', 'N/A')}
Date of Crime: {case_details.get('date_of_crime', 'N/A')}
Who Involved: {case_details.get('who_involved', 'N/A')}
Damage Description: {case_details.get('Damage Description:', 'N/A')}
Suspect Name: {case_details.get('suspect_name', 'N/A')}
Suspect Identity: {case_details.get('suspect_identity', 'N/A')}
Suspect Motive: {case_details.get('suspect_motive', 'N/A')}
Affected Assets: {case_details.get('affected_assets', 'N/A')}
Evidence Found: {case_details.get('evidence', 'N/A')}
Crime Scene Description: {case_details.get('evidence_collection', 'N/A')}
Timeline of Events: {case_details.get('timeline_intrusion', 'N/A')}
Crime Type: {case_details.get('type_of_crime', 'N/A')}
Asset Affected: {case_details.get('asset_affected', 'N/A')}
Cyber Forensic Notes: {case_details.get('cyber_forensic', 'N/A')}

Please provide a detailed analysis following this structure:

**1. Comprehensive Analysis of the Case**
- Review all collected evidence and evidence_collection thoroughly
- Establish a clear timeline_intrusion of the incident
- Analyze suspect_name, suspect_identity, and suspect_motive for behavioral patterns
- Cross-reference the date_of_crime and who_involved to confirm involvement and timeline accuracy

**2. Potential Motives and asset_affected to Consider**
- Investigate suspect_motive for clues around emotional, personal, or ideological triggers
- Assess damage and affected_assets for material, digital, or physical losses
- Distinguish between targeted attacks and random intrusions based on patterns
- Consider how the asset_affected connects to the victim or suspects

**3. Recommended Investigative Approaches**
- Interview all individuals linked to the timeline_intrusion and who_involved
- Reconstruct evidence_collection procedures to validate integrity
- Cross-verify suspect_identity and alibis related to affected assets and presence near crime scene

**4. Key Evidence to Focus On and Analysis**
- Prioritize analysis of the crime scene and collected evidence
- Review witness details mentioned in evidence_collection
- Apply forensic techniques to cyber_forensic data and correlate with physical findings
- Validate the authenticity of asset_affected and affected_assets links to the case

**5. Possible Solutions or Conclusions**
- Proceed with a systematic evidence-based investigation
- Focus on leads connected to suspect_motive, timeline inconsistencies, and unusual damage patterns
- If technical elements (like cyber intrusion) are involved, deepen cyber_forensic assessments
- Seek outside expert consultation for specialized domains (e.g., digital, forensic, psychological)


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


# Initialize the Cyber Agent
cyber_agent = CybercrimeAgent()

# FastAPI Routes
@app.get("/", response_model=Dict[str, str])
async def home():
    """Home endpoint"""
    logger.info("Received GET request for home endpoint")
    return {"message": "Cybercrime Agent API is running"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    logger.info("Received GET request for health endpoint")
    return HealthResponse(
        status="healthy",
        message="Cybercrime Agent API is running",
        endpoints=[
            "/",
            "/health",
            "/api/cyber",
            "/api/cyber/download-pdf",
            "/docs",
            "/redoc"
        ]
    )

@app.post("/api/cyber", response_model=CyberAgentResponse)
async def cyber_agent_endpoint(request: CyberAgentRequest):
    """Main endpoint for cybercrime agent interactions"""
    try:
        # Health check
        if request.question == "ping":
            return CyberAgentResponse(
                success=True,
                data=CyberAgentData(
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

        session_id, response, is_collecting_info, current_step, error_message = cyber_agent.process_message(
            request.question,
            request.session_id,
            force_new_session=force_new_session
        )

        return CyberAgentResponse(
            success=True,
            data=CyberAgentData(
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
        logger.error(f"Error in cyber_agent_endpoint: {str(e)}")
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

@app.post("/api/cyber/download-pdf")
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
        pdf_generator = CyberPDFGenerator()
        pdf_buffer = pdf_generator.generate_cyber_pdf(case_data, analysis_text)

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

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Cybercrime Agent API server on port 5001")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5001,
        reload=True,
        log_level="info"
    )