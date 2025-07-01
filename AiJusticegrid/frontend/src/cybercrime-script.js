// Global variables
let sessionId = null;
let currentStep = 0;
let totalSteps = 14;
let isWaitingForResponse = false;
let isAnalysisComplete = false;

// API Configuration
const API_BASE_URL = 'http://localhost:5001';
const API_ENDPOINT = `${API_BASE_URL}/api/cybercrime`;

// Session management
const SESSION_KEY = 'aiJusticeGrid_session';

// Step names for progress tracking
const stepNames = [
    'Case ID',
    'Date of Incident',
    'Attribution Method',
    'Damage Description',
    'Suspect Information',
    'Suspect Identification Basis',
    'Suspected Motive',
    'Affected Assets',
    'Evidence Preservation',
    'Evidence Collection Procedures',
    'Timeline of Events',
    'Type of Cybercrime',
    'Compromised Assets',
    'Forensic Resources'
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
        // User is not authenticated, redirect to login
        window.location.href = 'login.html';
        return;
    }
}

function getSession() {
    let session = null;

    // Check localStorage first (remember me)
    const localSession = localStorage.getItem(SESSION_KEY);
    if (localSession) {
        session = JSON.parse(localSession);
    }

    // Check sessionStorage if no local session
    if (!session) {
        const sessionData = sessionStorage.getItem(SESSION_KEY);
        if (sessionData) {
            session = JSON.parse(sessionData);
        }
    }

    // Validate session
    if (session && session.expiresAt > Date.now()) {
        session.isValid = true;
        return session;
    }

    // Clear invalid session
    clearSession();
    return null;
}

function clearSession() {
    localStorage.removeItem(SESSION_KEY);
    sessionStorage.removeItem(SESSION_KEY);
}

function loadUserInfo() {
    const session = getSession();
    if (session && session.username) {
        const userName = document.getElementById('userName');
        if (userName) {
            // Extract username from email (everything before @)
            const displayName = session.username.split('@')[0];
            userName.textContent = `Detective ${displayName.charAt(0).toUpperCase() + displayName.slice(1)}`;
        }
    }
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
    document.getElementById('sendBtn').disabled = true;
    isWaitingForResponse = true;

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

            // Update progress if still collecting info
            if (data.data.is_collecting_info) {
                currentStep++;
                updateProgress();
            } else {
                // Investigation complete
                currentStep = totalSteps;
                isAnalysisComplete = true;
                updateProgress();
                document.getElementById('currentStepInfo').innerHTML =
                    '<i class="fas fa-check-circle"></i><span>Investigation Complete</span>';

                // Show download button
                document.getElementById('downloadBtn').style.display = 'inline-flex';
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
    }
}

// Add message to chat
function addMessage(sender, content) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = sender === 'agent' ? '<i class="fas fa-shield-virus"></i>' : '<i class="fas fa-user"></i>';

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.innerHTML = formatMessage(content);

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Format message content
function formatMessage(content) {
    // Convert markdown-style formatting to HTML
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
        const stepName = stepNames[currentStep] || 'Processing';
        currentStepInfo.innerHTML = `<i class="fas fa-clipboard-list"></i><span>Current: ${stepName}</span>`;
    }
}

// Show/hide loading
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
                    <i class="fas fa-shield-virus"></i>
                </div>
                <div class="welcome-content">
                    <h2>Welcome to Cyber Crime Investigation Assistant</h2>
                    <p>I'm your specialized AI assistant for cybercrime investigations. I'll guide you through a comprehensive digital forensics analysis process.</p>
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
    }
}

// Download PDF report
async function downloadPDF() {
    if (!sessionId) {
        alert('No active session found. Please complete an investigation first.');
        return;
    }

    if (!isAnalysisComplete) {
        alert('Please complete the investigation before downloading the report.');
        return;
    }

    try {
        showLoading(true);

        const response = await fetch(`${API_BASE_URL}/api/cybercrime/download-pdf`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Cybercrime_Investigation_Report_${new Date().toISOString().slice(0, 10)}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            throw new Error('Failed to generate PDF report');
        }
    } catch (error) {
        console.error('Error downloading report:', error);
        alert('Failed to download report. Please try again.');
    } finally {
        showLoading(false);
    }
}

// Navigation functions
function logout() {
    if (confirm('Are you sure you want to logout? Any unsaved progress will be lost.')) {
        clearSession();
        window.location.href = 'login.html';
    }
}

function goBack() {
    if (confirm('Are you sure you want to go back to the dashboard? Any unsaved progress will be lost.')) {
        window.location.href = 'dashboard.html';
    }
}

function showHelp() {
    document.getElementById('helpModal').style.display = 'flex';
}

function closeHelp() {
    document.getElementById('helpModal').style.display = 'none';
}

// Close modal when clicking outside
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        closeHelp();
    }
});
