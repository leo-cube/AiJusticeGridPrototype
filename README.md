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
```

## Configuration

### Default Settings
- **Port**: 8080
- **Backend API**: https://aijusticegrid.onrender.com
- **Auto-open browser**: Enabled

### Customization
To change the backend API URL, edit the `API_BASE_URL` constant in `script.js`:
```javascript
const API_BASE_URL = 'https://aijusticegrid.onrender.com';
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

## Development

### Code Structure

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

## Troubleshooting

### Common Issues

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
