// Global variables
let sessionId = null;
let currentStep = 0;
let totalSteps = 14;
let isWaitingForResponse = false;

// API Configuration
const API_BASE_URL = 'https://aijusticegrid-1.onrender.com';
const API_ENDPOINT = `${API_BASE_URL}/api/murder`;

// Session management
const SESSION_KEY = 'aiJusticeGrid_session';

// Step names for progress tracking
const stepNames = [
    'Case ID',
    'Date of Crime',
    'Time of Crime',
    'Location',
    'Victim Name',
    'Victim Age',
    'Victim Gender',
    'Cause of Death',
    'Weapon Used',
    'Crime Scene Description',
    'Witnesses',
    'Evidence Found',
    'Suspects',
    'Additional Notes'
];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Check authentication first
    if (!checkAuthentication()) {
        return; // Will redirect to login
    }

    // Initialize user info
    initializeUserInfo();

    checkServerStatus();
    setupEventListeners();
});

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
        const response = await fetch(`${API_BASE_URL}/health`);
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
                updateProgress();
                document.getElementById('currentStepInfo').innerHTML =
                    '<i class="fas fa-check-circle"></i><span>Investigation Complete</span>';

                // Show download button
                document.getElementById('downloadBtn').style.display = 'flex';
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
    messageDiv.className = `message ${sender}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = sender === 'agent' ? '<i class="fas fa-user-secret"></i>' : '<i class="fas fa-user"></i>';

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';

    // Format content with markdown-like styling
    const formattedContent = formatMessageContent(content);
    messageContent.innerHTML = formattedContent;

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);

    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Format message content
function formatMessageContent(content) {
    // Convert **text** to bold
    content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Convert line breaks
    content = content.replace(/\n/g, '<br>');

    // Highlight [LIVE DATA ANALYSIS] header
    content = content.replace(/\[LIVE DATA ANALYSIS\]/g,
        '<span style="color: #3b82f6; font-weight: 600;">[LIVE DATA ANALYSIS]</span>');

    return content;
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
        const stepName = stepNames[currentStep] || 'Unknown Step';
        currentStepInfo.innerHTML =
            `<i class="fas fa-clipboard-list"></i><span>Current: ${stepName}</span>`;
    }
}

// Reset conversation
async function resetConversation() {
    if (confirm('Are you sure you want to reset the investigation? All progress will be lost.')) {
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
                // Reset variables
                sessionId = data.session_id;
                currentStep = 0;
                isWaitingForResponse = false;

                // Clear chat messages
                const chatMessages = document.getElementById('chatMessages');
                chatMessages.innerHTML = '';

                // Add agent's first message
                addMessage('agent', data.data.analysis);

                // Update progress
                updateProgress();

                // Clear input
                document.getElementById('messageInput').value = '';
                document.getElementById('sendBtn').disabled = true;

                // Hide download button
                document.getElementById('downloadBtn').style.display = 'none';

                // Focus on input
                document.getElementById('messageInput').focus();
            } else {
                throw new Error(data.error || 'Failed to reset conversation');
            }
        } catch (error) {
            console.error('Error resetting conversation:', error);
            addMessage('agent', 'Sorry, I encountered an error resetting the investigation. Please refresh the page.');
        } finally {
            showLoading(false);
        }
    }
}

// Show/hide loading overlay
function showLoading(show) {
    const loadingOverlay = document.getElementById('loadingOverlay');
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

// Show help modal
function showHelp() {
    document.getElementById('helpModal').style.display = 'flex';
}

// Close help modal
function closeHelp() {
    document.getElementById('helpModal').style.display = 'none';
}

// Close modal when clicking outside
document.getElementById('helpModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeHelp();
    }
});

// Download PDF report
async function downloadPDF() {
    if (!sessionId) {
        alert('No active session found. Please complete an investigation first.');
        return;
    }

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/api/murder/download-pdf`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        });

        if (response.ok) {
            // Get the filename from the response headers or create a default one
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'Murder_Investigation_Report.pdf';

            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1].replace(/['"]/g, '');
                }
            }

            // Create blob and download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            // Show success message
            addMessage('agent', '✅ **PDF Report Downloaded Successfully!**\n\nYour comprehensive murder investigation report has been downloaded to your device.');

        } else {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to download PDF');
        }

    } catch (error) {
        console.error('Error downloading PDF:', error);
        addMessage('agent', `❌ **PDF Download Failed**\n\nSorry, there was an error downloading the PDF report: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

// Authentication functions
function checkAuthentication() {
    const session = getSession();
    if (!session || !session.isValid) {
        // Redirect to login page
        window.location.href = 'login.html';
        return false;
    }
    return true;
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

function initializeUserInfo() {
    const session = getSession();
    if (session) {
        const userName = document.getElementById('userName');
        if (userName) {
            userName.textContent = session.username;
        }
    }
}

function logout() {
    if (confirm('Are you sure you want to logout? Any unsaved progress will be lost.')) {
        clearSession();
        window.location.href = 'login.html';
    }
}

// Periodic server status check
setInterval(checkServerStatus, 30000); // Check every 30 seconds

// Periodic session validation
setInterval(function() {
    if (!getSession()) {
        alert('Your session has expired. Please login again.');
        window.location.href = 'login.html';
    }
}, 60000); // Check every minute
