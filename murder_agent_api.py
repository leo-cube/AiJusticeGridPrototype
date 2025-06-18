import logging
import uuid
import os
import requests
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from typing import Dict, Any, Tuple, Optional
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

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
    }
})

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
        """Format analysis text into paragraphs"""
        paragraphs = []

        # Clean the text
        clean_text = self.clean_markdown_text(analysis_text)

        # Split by double newlines to get sections
        sections = clean_text.split('\n\n')

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Check if this looks like a header
            if (section.startswith('**') and section.endswith('**')) or section.isupper():
                header_text = section.replace('**', '').strip()
                paragraphs.append(Paragraph(header_text, styles['section_header']))
            else:
                paragraphs.append(Paragraph(section, styles['analysis_text']))

        return paragraphs

    def clean_markdown_text(self, text: str) -> str:
        """Clean markdown formatting from text"""
        if not text:
            return ""

        clean_text = str(text).strip()

        # Remove markdown formatting
        clean_text = clean_text.replace('**', '')
        clean_text = clean_text.replace('*', '')
        clean_text = clean_text.replace('__', '')
        clean_text = clean_text.replace('_', '')
        clean_text = clean_text.replace('###', '')
        clean_text = clean_text.replace('##', '')
        clean_text = clean_text.replace('#', '')
        clean_text = clean_text.replace('- ', '')
        clean_text = clean_text.replace('+ ', '')

        # Remove [LIVE DATA ANALYSIS] headers
        clean_text = clean_text.replace('[LIVE DATA ANALYSIS]', '')

        # Normalize whitespace
        clean_text = ' '.join(clean_text.split())

        return clean_text

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
            'analysis_text': ParagraphStyle(
                'AnalysisText',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=6,
                alignment=TA_JUSTIFY,
                fontName='Helvetica'
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

@app.route('/api/murder', methods=['POST'])
def murder_agent_endpoint():
    """Main endpoint for murder agent interactions"""
    try:
        case_details = request.json
        if not case_details:
            return jsonify({
                "success": False,
                "error": "No case details provided",
                "data": {
                    "analysis": "No case details provided. Please provide case details."
                }
            }), 400

        # Health check
        if case_details.get("question") == "ping":
            return jsonify({
                "success": True,
                "data": {
                    "analysis": "Murder Agent is running"
                },
                "status": "healthy",
                "session_id": "ping_session"
            }), 200

        session_id = case_details.get("session_id")
        user_input = case_details.get("question", "")
        force_new_session = case_details.get("force_new_session", False) or case_details.get("forceReset", False)

        session_id, response, is_collecting_info, current_step, error_message = murder_agent.process_message(
            user_input,
            session_id,
            force_new_session=force_new_session
        )

        return jsonify({
            "success": True,
            "data": {
                "analysis": response,
                "is_collecting_info": is_collecting_info,
                "current_step": current_step,
                "collected_data": conversation_states[session_id]["collected_data"] if session_id in conversation_states else {},
                "error": error_message
            },
            "session_id": session_id,
            "message": "Message processed successfully"
        })

    except Exception as e:
        logger.error(f"Error in murder_agent_endpoint: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "data": {
                "analysis": "An error occurred while processing your request."
            }
        }), 500

@app.route('/api/murder/download-pdf', methods=['POST'])
def download_murder_pdf():
    """Generate and download PDF report for murder investigation"""
    try:
        if not REPORTLAB_AVAILABLE:
            return jsonify({
                "success": False,
                "error": "PDF generation not available. ReportLab library not installed."
            }), 500

        request_data = request.json
        if not request_data:
            return jsonify({
                "success": False,
                "error": "No data provided for PDF generation"
            }), 400

        session_id = request_data.get("session_id")
        if not session_id or session_id not in conversation_states:
            return jsonify({
                "success": False,
                "error": "Invalid session ID or session not found"
            }), 400

        conv_state = conversation_states[session_id]

        # Check if analysis is completed
        if not conv_state.get("analysis_completed"):
            return jsonify({
                "success": False,
                "error": "Analysis not completed yet. Please complete the investigation first."
            }), 400

        # Get case data and analysis
        case_data = conv_state.get("collected_data", {})
        analysis_text = conv_state.get("analysis_result", "")

        if not analysis_text:
            return jsonify({
                "success": False,
                "error": "No analysis available for PDF generation"
            }), 400

        # Generate PDF
        pdf_generator = MurderPDFGenerator()
        pdf_buffer = pdf_generator.generate_murder_pdf(case_data, analysis_text)

        # Generate filename
        case_id = case_data.get('case_id', 'Unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Murder_Investigation_Report_{case_id}_{timestamp}.pdf"

        # Return PDF file
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )

    except Exception as e:
        logger.error(f"Error in download_murder_pdf: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Error generating PDF: {str(e)}"
        }), 500

@app.route('/')
def home():
    """Home endpoint"""
    logger.info("Received GET request for home endpoint")
    return jsonify({"message": "Murder Agent API is running"})

@app.route('/health')
def health_check():
    """Health check endpoint"""
    logger.info("Received GET request for health endpoint")
    return jsonify({
        "status": "healthy",
        "message": "Murder Agent API is running",
        "endpoints": [
            "/",
            "/health",
            "/api/murder"
        ]
    })

if __name__ == "__main__":
    logger.info("Starting Murder Agent API server on port 5001")
    app.run(host="0.0.0.0", port=5001, debug=True)
