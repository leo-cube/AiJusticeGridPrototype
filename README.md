<<<<<<< HEAD
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
=======
# Murder Agent Frontend

Modern web interface for the AI-powered murder investigation system.

## Features

- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Real-time Communication**: Live interaction with the AI investigation agent
- **Progress Tracking**: Visual progress indicator for case information collection
- **Secure Authentication**: Login system with session management
- **PDF Download**: Generate and download comprehensive investigation reports
- **Modern UI/UX**: Clean, professional interface with smooth animations
- **Dark Theme**: Eye-friendly dark theme optimized for long investigation sessions

## Technology Stack

- **HTML5**: Semantic markup structure
- **CSS3**: Modern styling with animations and responsive design
- **Vanilla JavaScript**: No framework dependencies for fast loading
- **Font Awesome**: Professional icons
- **Inter Font**: Clean, readable typography

## File Structure

```
frontend/
├── src/
│   ├── index.html          # Main application interface
│   ├── login.html          # Authentication page
│   ├── styles.css          # Main application styles
│   ├── login-styles.css    # Login page styles
│   ├── script.js           # Main application logic
│   └── login-script.js     # Login functionality
├── run.py                  # Development server
└── README.md              # This file
```

## Installation

No installation required! The frontend is a static web application that runs in any modern web browser.

## Running the Frontend

### Option 1: Using the Python server (Recommended)
```bash
cd frontend
python run.py
```

### Option 2: From root directory
```bash
python run-frontend.py
```

### Option 3: Using any static file server
```bash
cd frontend/src
python -m http.server 8080
>>>>>>> e381a5067922ad09620d83ea0b79aad4c61bef6e
```

## Configuration

<<<<<<< HEAD
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
=======
### Default Settings
- **Port**: 8080
- **Backend API**: http://localhost:5001
- **Auto-open browser**: Enabled

### Customization
To change the backend API URL, edit the `API_BASE_URL` constant in `script.js`:
```javascript
const API_BASE_URL = 'http://localhost:5001';
```

## Authentication

### Default Credentials
- **Username**: admin@police.gov
- **Password**: policecrime@586$gov

### Session Management
- Sessions last 24 hours
- "Remember me" option for persistent login
- Automatic session validation
- Secure logout functionality

## User Interface

### Login Page
- Secure authentication form
- Animated background elements
- Professional branding
- Error handling and feedback

### Main Application
- **Header**: Logo, user info, connection status, logout
- **Chat Interface**: Real-time conversation with AI agent
- **Progress Tracker**: Visual indication of case collection progress
- **Input Section**: Message input with action buttons
- **Modals**: Help information and success notifications

### Features
- **Start Investigation**: Begin new case analysis
- **Progress Tracking**: 14-step case information collection
- **Real-time Chat**: Interactive conversation with AI agent
- **PDF Download**: Generate comprehensive reports
- **Reset Functionality**: Start over with new case
- **Help System**: Built-in guidance and instructions

## Browser Compatibility

### Supported Browsers
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

### Required Features
- ES6 JavaScript support
- CSS Grid and Flexbox
- Fetch API
- Local/Session Storage
>>>>>>> e381a5067922ad09620d83ea0b79aad4c61bef6e

## Development

### Code Structure
<<<<<<< HEAD
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
=======

#### script.js
- Session management
- API communication
- UI state management
- Progress tracking
- PDF download handling

#### styles.css
- Responsive design
- Dark theme
- Animations and transitions
- Component styling

#### login-script.js
- Authentication logic
- Session creation
- Form validation
- Security features

### Customization

#### Styling
Modify CSS variables in `styles.css` for theme customization:
```css
:root {
  --primary-color: #3b82f6;
  --secondary-color: #1d4ed8;
  --background-color: #0f1419;
}
```

#### API Integration
Update API endpoints in `script.js`:
```javascript
const API_ENDPOINT = `${API_BASE_URL}/api/murder`;
```

## Security Features

- **Authentication Required**: All pages require valid session
- **Session Validation**: Automatic session expiry handling
- **CORS Protection**: Proper cross-origin request handling
- **Input Validation**: Client-side form validation
- **XSS Prevention**: Proper content escaping
>>>>>>> e381a5067922ad09620d83ea0b79aad4c61bef6e

## Troubleshooting

### Common Issues

<<<<<<< HEAD
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
=======
1. **Backend Connection Failed**
   - Ensure backend server is running on port 5001
   - Check CORS configuration
   - Verify network connectivity

2. **Login Issues**
   - Verify credentials are correct
   - Clear browser cache and cookies
   - Check browser console for errors

3. **PDF Download Problems**
   - Ensure investigation is completed
   - Check browser download settings
   - Verify backend PDF generation is working

### Browser Console
Press F12 to open developer tools and check the console for error messages.

## Mobile Responsiveness

The interface is fully responsive and optimized for:
- **Desktop**: Full feature set with optimal layout
- **Tablet**: Adapted layout with touch-friendly controls
- **Mobile**: Simplified interface with essential features

## Performance

### Optimization Features
- Minimal JavaScript dependencies
- Optimized CSS with efficient selectors
- Lazy loading of non-critical resources
- Efficient DOM manipulation
- Debounced input handling

### Loading Times
- Initial page load: < 2 seconds
- Subsequent interactions: < 500ms
- API responses: Depends on backend processing

## Accessibility

- Semantic HTML structure
- Keyboard navigation support
- Screen reader compatibility
- High contrast color scheme
- Focus indicators
- ARIA labels where appropriate
>>>>>>> e381a5067922ad09620d83ea0b79aad4c61bef6e
