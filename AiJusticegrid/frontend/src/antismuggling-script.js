// Global variables
let sessionId = null;
let currentStep = 0;
let totalSteps = 14;
let isWaitingForResponse = false;
let isAnalysisComplete = false;

// API Configuration
const API_BASE_URL = 'http://localhost:5001';
const API_ENDPOINT = `${API_BASE_URL}/api/antismuggling`;

// Session management
const SESSION_KEY = 'aiJusticeGrid_session';

// Step names for progress tracking
const stepNames = [
    'Case ID',
    'Date of Incident',
    'Port of Entry',
    'Type of Smuggling',
    'Detection Method',
    'Suspect Information',
    'Travel Document Review',
    'Vehicle or Conveyance',
    'Contraband Description',
    'Interview Summary',
    'Surveillance or Intel',
    'Seizure Details',
    'Agency Coordination',
    'Case Status'
];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Check authentication
    checkAuthentication();

    // Setup event listeners
    setupEventListeners();

    // Check server status
    checkServerStatus();

    // Load user info
    loadUserInfo();
});

function checkAuthentication() {
    const session = getSession();
    if (!session || !session.isValid) {
        window.location.href = 'login.html';
        return;
    }
}

function getSession() {
    try {
        const sessionData = localStorage.getItem(SESSION_KEY);
        return sessionData ? JSON.parse(sessionData) : null;
    } catch (error) {
        console.error('Error parsing session data:', error);
        return null;
    }
}

function loadUserInfo() {
    const session = getSession();
    if (session && session.user) {
        document.getElementById('userName').textContent = session.user.name || 'User';
    }
}

function logout() {
    localStorage.removeItem(SESSION_KEY);
    window.location.href = 'login.html';
}

function goBack() {
    window.location.href = 'dashboard.html';
}

// Setup event listeners
function setupEventListeners() {
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');

    // Enter key to send message
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize input and enable/disable send button
    messageInput.addEventListener('input', function() {
        const hasText = this.value.trim().length > 0;
        sendBtn.disabled = !hasText || isWaitingForResponse;
    });
}

// Check server status
async function checkServerStatus() {
    try {
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: 'ping'
            })
        });

        if (response.ok) {
            updateStatus('connected', 'Connected');
        } else {
            updateStatus('error', 'Server Error');
        }
    } catch (error) {
        updateStatus('error', 'Disconnected');
        console.error('Server connection failed:', error);
    }
}

// Update connection status
function updateStatus(status, text) {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    statusDot.className = `status-dot ${status}`;
    statusText.textContent = text;
}

// Start investigation
async function startInvestigation() {
    showLoading(true);

    try {
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: '',
                force_new_session: true
            })
        });

        const data = await response.json();

        if (data.success) {
            sessionId = data.session_id;

            // Hide welcome message and show chat interface
            document.querySelector('.welcome-message').style.display = 'none';
            document.getElementById('progressSection').style.display = 'block';
            document.getElementById('inputSection').style.display = 'block';

            // Add agent's first message
            addMessage('agent', data.data.analysis);

            // Update progress
            updateProgress();

            // Focus on input
            document.getElementById('messageInput').focus();
        } else {
            throw new Error(data.error || 'Failed to start investigation');
        }
    } catch (error) {
        console.error('Error starting investigation:', error);
        addMessage('agent', 'Sorry, I encountered an error starting the investigation. Please try again.');
    } finally {
        showLoading(false);
    }
}

// Send message
async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();

    if (!message || isWaitingForResponse) return;

    // Add user message to chat
    addMessage('user', message);

    // Clear input and disable send button
    messageInput.value = '';
    isWaitingForResponse = true;
    document.getElementById('sendBtn').disabled = true;

    // Show loading
    showLoading(true);

    try {
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: message,
                session_id: sessionId
            })
        });

        const data = await response.json();

        if (data.success) {
            // Add agent response
            addMessage('agent', data.data.analysis);

            // Update progress if we moved to next step
            if (data.data.current_step !== undefined) {
                currentStep = data.data.current_step;
                updateProgress();
            }

            // Check if analysis is complete
            if (data.data.analysis_complete) {
                isAnalysisComplete = true;
                document.getElementById('downloadBtn').style.display = 'inline-flex';
                addMessage('agent', '🎉 **Investigation Complete!** You can now download the comprehensive PDF report.');
            }
        } else {
            throw new Error(data.error || 'Failed to send message');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        addMessage('agent', 'Sorry, I encountered an error processing your message. Please try again.');
    } finally {
        showLoading(false);
        isWaitingForResponse = false;
        messageInput.focus();
    }
}

// Add message to chat
function addMessage(sender, content) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = sender === 'agent' ? '<i class="fas fa-shield-alt"></i>' : '<i class="fas fa-user"></i>';

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.innerHTML = formatMessage(content);

    const timestamp = document.createElement('div');
    timestamp.className = 'message-timestamp';
    timestamp.textContent = new Date().toLocaleTimeString();

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    messageDiv.appendChild(timestamp);

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Format message content
function formatMessage(content) {
    // Convert markdown-style formatting
    return content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
}

// Update progress
function updateProgress() {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const currentStepInfo = document.getElementById('currentStepInfo');

    const percentage = (currentStep / totalSteps) * 100;
    progressFill.style.width = `${percentage}%`;
    progressText.textContent = `${currentStep}/${totalSteps} Steps Completed`;

    if (currentStep < totalSteps) {
        currentStepInfo.innerHTML = `
            <i class="fas fa-clipboard-list"></i>
            <span>Current: ${stepNames[currentStep] || 'Processing...'}</span>
        `;
    } else {
        currentStepInfo.innerHTML = `
            <i class="fas fa-check-circle"></i>
            <span>Investigation Complete</span>
        `;
    }
}

// Show/hide loading overlay
function showLoading(show) {
    const loadingOverlay = document.getElementById('loadingOverlay');
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

// Reset conversation
function resetConversation() {
    if (confirm('Are you sure you want to reset the investigation? All progress will be lost.')) {
        sessionId = null;
        currentStep = 0;
        isAnalysisComplete = false;
        
        // Clear chat messages
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = `
            <div class="welcome-message">
                <div class="agent-avatar">
                    <i class="fas fa-shield-alt"></i>
                </div>
                <div class="welcome-content">
                    <h2>Welcome to Anti Smuggling Investigation Assistant</h2>
                    <p>I'm your specialized AI assistant for anti-smuggling operations. I'll guide you through a comprehensive border security analysis process.</p>
                    <button class="start-btn" onclick="startInvestigation()">
                        <i class="fas fa-play"></i>
                        Start Investigation
                    </button>
                </div>
            </div>
        `;

        // Hide progress and input sections
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('inputSection').style.display = 'none';
        document.getElementById('downloadBtn').style.display = 'none';

        // Reset progress
        updateProgress();
    }
}

// Download PDF report
async function downloadPDF() {
    if (!sessionId || !isAnalysisComplete) {
        alert('Please complete the investigation before downloading the report.');
        return;
    }

    try {
        showLoading(true);
        
        const response = await fetch(`${API_BASE_URL}/api/download-pdf`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId,
                report_type: 'antismuggling'
            })
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `anti_smuggling_report_${sessionId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            throw new Error('Failed to download PDF');
        }
    } catch (error) {
        console.error('Error downloading PDF:', error);
        alert('Failed to download PDF report. Please try again.');
    } finally {
        showLoading(false);
    }
}

// Show help modal
function showHelp() {
    document.getElementById('helpModal').style.display = 'flex';
}

// Close help modal
function closeHelp() {
    document.getElementById('helpModal').style.display = 'none';
}
