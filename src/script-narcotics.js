// Global variables for cyber agent
let NarcoticsSessionId = null;
let NarcoticsCurrentStep = 0;
let NarcoticsTotalSteps = 14;
let NarcoticsIsWaitingForResponse = false;

// API Configuration - Updated for unified server
// const API_BASE_URL = 'https://aijusticegrid-1.onrender.com';
const API_BASE_URL = 'http://localhost:9000';

// Updated endpoint for unified server
const API_ENDPOINT = `${API_BASE_URL}/api/narcotics`;

// Session management
const SESSION_KEY = 'aiJusticeGrid_session';

// Step names for progress tracking - cyber agent
const NarcoticsStepNames = [
    'Case ID',
    'Type Of Substance',
    'Drugs Acquired',
    'Identified Individuals',
    'Trafficker Identity',
    'Supply Chain',
    'Concealment',
    'Evidence Trafficking',
    'Tx Type',
    'Informant Details',
    'Controlled delivery',
    'Forensic Evidence',
    'Penalty Type',
    'International Links'
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

// Navigation function to go back to agent selection
function goBack() {
    window.location.href = 'index.html';
}

// Setup event listeners for cyber agent
function setupEventListeners() {
    const messageInput = document.getElementById('narcoticMessageInput');
    const sendBtn = document.getElementById('narcoticSendBtn');

    if (messageInput && sendBtn) {
        // Enter key to send message
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage_narcotics();
            }
        });

        // Auto-resize input and enable/disable send button
        messageInput.addEventListener('input', function() {
            const hasText = this.value.trim().length > 0;
            sendBtn.disabled = !hasText || NarcoticsIsWaitingForResponse;
        });
    }
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

// Update connection status (cyber-specific)
function updateStatus(status, text) {
    // For cyber agent, we'll use the same status elements as murder
    // since they share the same header, but we'll make it cyber-aware
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    if (statusDot && statusText) {
        statusDot.className = `status-dot ${status}`;
        statusText.textContent = text;
    }
}

// Start investigation
async function startInvestigation_narcotics() {
    console.log('Starting narcotics investigation...');
    showLoading(true);

    try {
        console.log('Making API request to:', API_ENDPOINT);
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

        console.log('API response status:', response.status);
        const data = await response.json();
        console.log('API response data:', data);

        if (data.success) {
            NarcoticsSessionId = data.session_id;
            console.log('Narcotics session ID:', NarcoticsSessionId);

            // Hide welcome message and show chat interface
            const welcomeMsg = document.querySelector('#NarcoticsChatMessages .welcome-message');
            if (welcomeMsg) {
                welcomeMsg.style.display = 'none';
                console.log('Welcome message hidden');
            } else {
                console.error('Welcome message not found');
            }

            const progressSection = document.getElementById('narcoticsProgressSection');
            const inputSection = document.getElementById('NarcoticsInputSection');

            if (progressSection) {
                progressSection.style.display = 'block';
                console.log('Progress section shown');
            } else {
                console.error('Progress section not found');
            }

            if (inputSection) {
                inputSection.style.display = 'block';
                console.log('Input section shown');
            } else {
                console.error('Input section not found');
            }

            // Add agent's first message
            addMessage('agent', data.data.analysis);

            // Update progress
            updateProgress();

            // Focus on input
            const messageInput = document.getElementById('narcoticMessageInput');
            if (messageInput) {
                messageInput.focus();
                console.log('Input focused');
            } else {
                console.error('Message input not found');
            }
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
async function sendMessage_narcotics() {
    const messageInput = document.getElementById('narcoticMessageInput');
    const message = messageInput.value.trim();

    if (!message || NarcoticsIsWaitingForResponse) return;

    // Add user message to chat
    addMessage('user', message);

    // Clear input and disable send button
    messageInput.value = '';
    const sendBtn = document.getElementById('narcoticSendBtn');
    if (sendBtn) sendBtn.disabled = true;
    NarcoticsIsWaitingForResponse = true;

    showLoading(true);

    try {
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: message,
                session_id: NarcoticsSessionId
            })
        });

        const data = await response.json();

        if (data.success) {
            // Add agent response
            addMessage('agent', data.data.analysis);

            // Update progress if still collecting info
            if (data.data.is_collecting_info) {
                NarcoticsCurrentStep++;
                updateProgress();
            } else {
                // Investigation complete
                NarcoticsCurrentStep = NarcoticsTotalSteps;
                updateProgress();
                const currentStepInfo = document.getElementById('NarcoticsCurrentStepInfo');
                if (currentStepInfo) {
                    currentStepInfo.innerHTML = '<i class="fas fa-check-circle"></i><span>Investigation Complete</span>';
                }

                // Show download button
                const downloadBtn = document.getElementById('narcoticsDownloadBtn');
                if (downloadBtn) downloadBtn.style.display = 'flex';
            }
        } else {
            throw new Error(data.error || 'Failed to send message');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        addMessage('agent', 'Sorry, I encountered an error processing your message. Please try again.');
    } finally {
        showLoading(false);
        NarcoticsIsWaitingForResponse = false;
        const messageInput = document.getElementById('narcoticMessageInput');
        if (messageInput) messageInput.focus();
    }
}

// Add message to chat (narcotics-specific)
function addMessage(sender, content) {
    const chatMessages = document.getElementById('NarcoticsChatMessages');

    if (!chatMessages) {
        console.error('NarcoticsChatMessages element not found');
        return;
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = sender === 'agent' ? '<i class="fas fa-laptop-code"></i>' : '<i class="fas fa-user"></i>';

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

// Format message content (cyber-specific)
function formatMessageContent(content) {
    // Convert **text** to bold
    content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Convert line breaks
    content = content.replace(/\n/g, '<br>');

    // Highlight [LIVE DATA ANALYSIS] header for cyber
    content = content.replace(/\[LIVE DATA ANALYSIS\]/g,
        '<span style="color: #10b981; font-weight: 600;">[NARCOTICS ANALYSIS]</span>');

    return content;
}

// Update progress (narcotics-specific)
function updateProgress() {
    const progressFill = document.getElementById('NarcoticsProgressFill');
    const progressText = document.getElementById('NarcoticsProgressText');
    const currentStepInfo = document.getElementById('NarcoticsCurrentStepInfo');

    if (progressFill && progressText && currentStepInfo) {
        const percentage = (NarcoticsCurrentStep / NarcoticsTotalSteps) * 100;
        progressFill.style.width = `${percentage}%`;
        progressText.textContent = `${NarcoticsCurrentStep}/${NarcoticsTotalSteps} Steps Completed`;

        if (NarcoticsCurrentStep < NarcoticsTotalSteps) {
            const stepName = NarcoticsStepNames[NarcoticsCurrentStep] || 'Unknown Step';
            currentStepInfo.innerHTML =
                `<i class="fas fa-laptop-code"></i><span>Current: ${stepName}</span>`;
        }
    } else {
        console.error('Narcotics progress elements not found:', {
            progressFill: !!progressFill,
            progressText: !!progressText,
            currentStepInfo: !!currentStepInfo
        });
    }
}

// Reset conversation
async function resetConversation_narcotics() {
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
                NarcoticsSessionId = data.session_id;
                NarcoticsCurrentStep = 0;
                NarcoticsIsWaitingForResponse = false;

                // Clear chat messages
                const chatMessages = document.getElementById('NarcoticsChatMessages');
                chatMessages.innerHTML = '';

                // Add agent's first message
                addMessage('agent', data.data.analysis);

                // Update progress
                updateProgress();

                // Clear input
                const messageInput = document.getElementById('narcoticMessageInput');
                if (messageInput) messageInput.value = '';
                const sendBtn = document.getElementById('narcoticSendBtn');
                if (sendBtn) sendBtn.disabled = true;

                // Hide download button
                const downloadBtn = document.getElementById('narcoticsDownloadBtn');
                if (downloadBtn) downloadBtn.style.display = 'none';

                // Focus on input
                if (messageInput) messageInput.focus();
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
async function downloadPDF_narcotics() {
    if (!NarcoticsSessionId) {
        alert('No active session found. Please complete an investigation first.');
        return;
    }

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/api/narcotics/download-pdf`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: NarcoticsSessionId
            })
        });

        if (response.ok) {
            // Get the filename from the response headers or create a default one
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'Narcotics_Investigation_Report.pdf';

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
            addMessage('agent', '✅ **PDF Report Downloaded Successfully!**\n\nYour comprehensive narcotics investigation report has been downloaded to your device.');

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

// Navigation function
function goBack() {
    if (confirm('Are you sure you want to go back? Any unsaved progress will be lost.')) {
        window.location.href = 'index.html';
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
