// Global variables
let sessionId = null;
let isWaitingForResponse = false;

// API Configuration
const API_BASE_URL = 'http://localhost:5001';
const API_ENDPOINT = `${API_BASE_URL}/api/interactive`;

// Session management
const SESSION_KEY = 'aiJusticeGrid_session';

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    checkAuthentication();
    initializeChat();
    setupEventListeners();
});

function checkAuthentication() {
    const session = getSession();
    console.log('Interactive Agent - Session check:', session);
    if (!session || !session.isValid) {
        console.log('Interactive Agent - No valid session, redirecting to login');
        window.location.href = 'login.html';
        return;
    }
    console.log('Interactive Agent - Authentication successful');
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

function clearSession() {
    localStorage.removeItem(SESSION_KEY);
    sessionStorage.removeItem(SESSION_KEY);
}

function logout() {
    if (confirm('Are you sure you want to logout? Any unsaved progress will be lost.')) {
        clearSession();
        window.location.href = 'login.html';
    }
}

function setupEventListeners() {
    const messageInput = document.getElementById('messageInput');
    
    // Auto-resize input and handle Enter key
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(e);
        }
    });
    
    // Focus input on load
    messageInput.focus();
}

function initializeChat() {
    // Start a new conversation
    startNewConversation();
}

async function startNewConversation() {
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

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (data.success) {
            sessionId = data.session_id;
            addMessage(data.data.analysis, 'assistant');
        } else {
            throw new Error(data.error || 'Failed to start conversation');
        }
    } catch (error) {
        console.error('Error starting conversation:', error);
        addMessage('Sorry, I encountered an error while starting our conversation. Please try refreshing the page.', 'assistant');
    }
}

async function sendMessage(event) {
    event.preventDefault();
    
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message || isWaitingForResponse) {
        return;
    }
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input and disable form
    messageInput.value = '';
    setWaitingState(true);
    
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

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (data.success) {
            sessionId = data.session_id;
            addMessage(data.data.analysis, 'assistant');
        } else {
            throw new Error(data.error || 'Failed to get response');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        addMessage('I apologize, but I encountered an error while processing your message. Please try again.', 'assistant');
    } finally {
        setWaitingState(false);
    }
}

function sendQuickMessage(message) {
    const messageInput = document.getElementById('messageInput');
    messageInput.value = message;
    sendMessage({ preventDefault: () => {} });
}

function addMessage(content, sender) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Format content with basic markdown-like formatting
    const formattedContent = formatMessage(content);
    contentDiv.innerHTML = formattedContent;
    
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);
    
    // Insert before typing indicator
    const typingIndicator = document.getElementById('typingIndicator');
    messagesContainer.insertBefore(messageDiv, typingIndicator);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function formatMessage(content) {
    // Basic formatting for better readability
    return content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>')
        .replace(/(\d+\.\s)/g, '<br>$1')
        .replace(/(-\s)/g, '<br>• ');
}

function setWaitingState(waiting) {
    isWaitingForResponse = waiting;
    const sendButton = document.getElementById('sendButton');
    const messageInput = document.getElementById('messageInput');
    const typingIndicator = document.getElementById('typingIndicator');
    
    sendButton.disabled = waiting;
    messageInput.disabled = waiting;
    
    if (waiting) {
        typingIndicator.style.display = 'flex';
        sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    } else {
        typingIndicator.style.display = 'none';
        sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
    }
    
    // Scroll to bottom to show typing indicator
    if (waiting) {
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

function goBack() {
    if (confirm('Are you sure you want to go back to the dashboard? Your conversation will be saved.')) {
        window.location.href = 'dashboard.html';
    }
}

function clearChat() {
    const messagesContainer = document.getElementById('chatMessages');
    const messages = messagesContainer.querySelectorAll('.message');
    messages.forEach(message => message.remove());
    
    // Restart conversation
    startNewConversation();
}

// Add some utility functions for enhanced functionality
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
}

function showNotification(message) {
    // Create a simple notification
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #4facfe;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Add CSS for notification animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
`;
document.head.appendChild(style);
