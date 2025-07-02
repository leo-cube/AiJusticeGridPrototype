# Murder Agent Backend API

FastAPI-based backend service for the AI-powered murder investigation system.

## Features

- **FastAPI Framework**: Modern, fast web framework with automatic API documentation
- **Async/Await Support**: High-performance asynchronous request handling
- **Pydantic Models**: Request/response validation and serialization
- **NVIDIA API Integration**: AI-powered case analysis using NVIDIA's LLM services
- **PDF Generation**: Professional investigation reports using ReportLab
- **CORS Support**: Cross-origin resource sharing for frontend integration
- **Session Management**: Stateful conversation handling for case collection

## API Endpoints

### Health Check
- `GET /` - Basic health check
- `GET /health` - Detailed health status with available endpoints

### Murder Investigation
- `POST /api/murder` - Main investigation endpoint for case processing
- `POST /api/murder/download-pdf` - Generate and download PDF reports

### Documentation
- `GET /docs` - Interactive Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## Installation

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Backend

### Option 1: Using the run script (Recommended)
```bash
python run.py
```

### Option 2: Direct uvicorn command
```bash
uvicorn app:app --host 0.0.0.0 --port 5001 --reload
```

### Option 3: From root directory
```bash
python run-backend.py
```

## Configuration

### Environment Variables
- `NVIDIA_API_KEY`: Your NVIDIA API key for LLM services (configured in app.py)

### Default Settings
- **Host**: 0.0.0.0 (all interfaces)
- **Port**: 5001
- **Reload**: Enabled in development mode

## API Usage Examples

### Start Investigation
```bash
curl -X POST "http://localhost:5001/api/murder" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "",
    "force_new_session": true
  }'
```

### Send Case Information
```bash
curl -X POST "http://localhost:5001/api/murder" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Case ID: MURDER-2024-001",
    "session_id": "your-session-id"
  }'
```

### Download PDF Report
```bash
curl -X POST "http://localhost:5001/api/murder/download-pdf" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id"
  }' \
  --output report.pdf
```

## Dependencies

- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **httpx**: Async HTTP client for NVIDIA API calls
- **pydantic**: Data validation and serialization
- **requests**: HTTP library for API calls
- **reportlab**: PDF generation
- **python-dateutil**: Date parsing utilities

## Development

### Code Structure
- `app.py`: Main FastAPI application
- `run.py`: Development server launcher
- `requirements.txt`: Python dependencies

### Adding New Endpoints
1. Define Pydantic models for request/response
2. Create async route handlers
3. Add proper error handling
4. Update documentation

### Testing
Access the interactive API documentation at:
- Swagger UI: http://localhost:5001/docs
- ReDoc: http://localhost:5001/redoc

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Find process using port 5001
   lsof -i :5001
   # Kill the process
   kill -9 <PID>
   ```

2. **Missing dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **NVIDIA API errors**
   - Check API key configuration
   - Verify network connectivity
   - Review API rate limits

### Logs
The application logs important events and errors to the console. Check the terminal output for debugging information.

## Production Deployment

For production deployment, consider:
- Using a production ASGI server like Gunicorn with Uvicorn workers
- Setting up proper environment variables
- Configuring reverse proxy (nginx)
- Implementing proper logging and monitoring
- Setting up SSL/TLS certificates
