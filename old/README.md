# AiJusticeGrid - Murder Investigation System

An AI-powered murder investigation system that helps law enforcement professionals conduct comprehensive case analysis through structured data collection and intelligent analysis.

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Running the Application

#### Option 1: Separate Frontend and Backend (Recommended)

**Terminal 1 - Backend API:**
```bash
python run-backend.py
```
This starts the FastAPI backend server on http://localhost:5001

**Terminal 2 - Frontend Web Interface:**
```bash
python run-frontend.py
```
This starts the web interface on http://localhost:8080

#### Option 2: Individual Components

**Backend Only:**
```bash
cd backend
python run.py
```

**Frontend Only:**
```bash
cd frontend
python run.py
```

### Access the Application
1. Open your browser to http://localhost:8080
2. Login with credentials:
   - **Username**: admin@police.gov
   - **Password**: policecrime@586$gov
3. Start a new investigation

## 📁 Project Structure

```
AiJusticeGridPrototype/
├── backend/                 # FastAPI backend service
│   ├── app.py              # Main FastAPI application
│   ├── run.py              # Backend server launcher
│   ├── requirements.txt    # Python dependencies
│   └── README.md           # Backend documentation
├── frontend/               # Web interface
│   ├── src/                # Frontend source files
│   │   ├── index.html      # Main application
│   │   ├── login.html      # Authentication page
│   │   ├── styles.css      # Application styles
│   │   ├── script.js       # Application logic
│   │   └── ...            # Additional assets
│   ├── run.py              # Frontend server launcher
│   └── README.md           # Frontend documentation
├── run-backend.py          # Convenience script for backend
├── run-frontend.py         # Convenience script for frontend
└── README.md              # This file
```

## 🔧 Features

### Backend (FastAPI)
- **Modern API Framework**: FastAPI with automatic documentation
- **AI Integration**: NVIDIA API for intelligent case analysis
- **PDF Generation**: Professional investigation reports
- **Session Management**: Stateful conversation handling
- **Async Processing**: High-performance request handling

### Frontend (Web Interface)
- **Responsive Design**: Works on all devices
- **Real-time Chat**: Interactive AI conversation
- **Progress Tracking**: Visual case collection progress
- **Secure Authentication**: Session-based login system
- **PDF Downloads**: Generate comprehensive reports

## 🔍 Investigation Process

The system guides users through a structured 14-step investigation process:

1. Case ID
2. Date of Crime
3. Time of Crime
4. Location
5. Victim Name
6. Victim Age
7. Victim Gender
8. Cause of Death
9. Weapon Used
10. Crime Scene Description
11. Witnesses
12. Evidence Found
13. Suspects
14. Additional Notes

After collecting all information, the AI provides comprehensive analysis including:
- Case analysis and patterns
- Potential motives and suspects
- Recommended investigative approaches
- Key evidence priorities
- Possible conclusions

## 📚 API Documentation

When the backend is running, access interactive API documentation:
- **Swagger UI**: http://localhost:5001/docs
- **ReDoc**: http://localhost:5001/redoc

## 🛠 Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --port 5001
```

### Frontend Development
The frontend uses vanilla HTML/CSS/JavaScript for maximum compatibility and performance.

### Adding Features
- Backend: Add new FastAPI routes in `backend/app.py`
- Frontend: Modify files in `frontend/src/`

## 🔒 Security

- **Authentication Required**: All access requires valid credentials
- **Session Management**: Secure session handling with expiration
- **Input Validation**: Both client and server-side validation
- **CORS Protection**: Proper cross-origin request handling

## 📋 Requirements

### Backend Dependencies
- fastapi
- uvicorn
- httpx
- pydantic
- requests
- reportlab
- python-dateutil

### Frontend Requirements
- Modern web browser with JavaScript enabled
- No additional dependencies required

## 🚨 Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 5001 (backend) and 8080 (frontend) are available
2. **Dependencies**: Run `pip install -r backend/requirements.txt`
3. **Browser compatibility**: Use a modern browser with JavaScript enabled
4. **API connection**: Verify backend is running before starting frontend

### Getting Help
- Check the console output for error messages
- Review individual README files in backend/ and frontend/ directories
- Ensure all dependencies are properly installed

## 📄 License

This project is a prototype for law enforcement use. Authorized personnel only.

## 🤝 Contributing

This is a prototype system. For production use, additional security measures, testing, and compliance features would be required.
