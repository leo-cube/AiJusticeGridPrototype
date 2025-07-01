// Global variables
let sessionId = null;
let currentStep = 0;
let totalSteps = 12;
let isWaitingForResponse = false;
let isAnalysisComplete = false;

// API Configuration
const API_BASE_URL = 'http://localhost:5001';
const API_ENDPOINT = `${API_BASE_URL}/api/narcotics`;

// Session management
const SESSION_KEY = 'aiJusticeGrid_session';

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    checkAuthentication();
    initializeUserInfo();
    checkSystemStatus();
    setupEventListeners();
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
        const sessionData = localStorage.getItem(SESSION_KEY) || sessionStorage.getItem(SESSION_KEY);
        if (sessionData) {
            const session = JSON.parse(sessionData);
            if (session.expiresAt && Date.now() < session.expiresAt) {
                return session;
            }
        }
    } catch (error) {
        console.error('Error reading session:', error);
    }
    return null;
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

function clearSession() {
    localStorage.removeItem(SESSION_KEY);
    sessionStorage.removeItem(SESSION_KEY);
}

function goBack() {
    if (confirm('Are you sure you want to go back to the dashboard? Any unsaved progress will be lost.')) {
        window.location.href = 'dashboard.html';
    }
}

function setupEventListeners() {
    // Enter key to send message
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        messageInput.addEventListener('input', function() {
            const sendBtn = document.getElementById('sendBtn');
            if (sendBtn) {
                sendBtn.disabled = this.value.trim() === '' || isWaitingForResponse;
            }
        });
    }
}

async function checkSystemStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            updateStatus('connected', 'System Online');
        } else {
            updateStatus('error', 'System Error');
        }
    } catch (error) {
        console.error('Health check failed:', error);
        updateStatus('error', 'Connection Failed');
    }
}

function updateStatus(status, text) {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    
    if (statusDot && statusText) {
        statusDot.className = `status-dot ${status}`;
        statusText.textContent = text;
    }
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
        document.getElementById('sendBtn').disabled = false;
    }
}

function addMessage(sender, content) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const timestamp = new Date().toLocaleTimeString();
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-text">${formatMessage(content)}</div>
            <div class="message-time">${timestamp}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatMessage(content) {
    // Convert markdown-style formatting to HTML
    return content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
}

function updateProgress() {
    const progressFill = document.getElementById('progressFill');
    const progressCounter = document.getElementById('progressCounter');
    
    const percentage = (currentStep / totalSteps) * 100;
    
    if (progressFill) {
        progressFill.style.width = `${percentage}%`;
    }
    
    if (progressCounter) {
        if (currentStep >= totalSteps) {
            progressCounter.textContent = 'Complete';
        } else {
            progressCounter.textContent = `Step ${currentStep + 1} of ${totalSteps}`;
        }
    }
}

function showLoading(show) {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = show ? 'flex' : 'none';
    }
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
                    <i class="fas fa-pills"></i>
                </div>
                <div class="welcome-content">
                    <h2>Narcotics Agent</h2>
                    <p>I'm your AI assistant specialized in narcotics investigations. I'll help you analyze drug-related cases, track distribution networks, and provide comprehensive investigative support.</p>
                    <button class="start-btn" onclick="startInvestigation()">
                        <i class="fas fa-play"></i>
                        Start Investigation
                    </button>
                </div>
            </div>
        `;
        
        // Show welcome message and hide other sections
        document.querySelector('.welcome-message').style.display = 'flex';
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

        const response = await fetch(`${API_BASE_URL}/api/narcotics/download-pdf`, {
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
            a.download = `NarcoticsAgent_Investigation_Report_${new Date().toISOString().slice(0, 10)}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            throw new Error('Failed to generate PDF report');
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