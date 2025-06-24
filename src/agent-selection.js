// Agent Selection Page Script
// Session management
const SESSION_KEY = 'aiJusticeGrid_session';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Check authentication first
    if (!checkAuthentication()) {
        return; // Will redirect to login
    }

    // Initialize user info
    initializeUserInfo();
    
    // Add hover effects to agent cards
    setupCardEffects();
});

// Navigate to specific agent page
function navigateToAgent(agentType) {
    if (agentType === 'murder') {
        window.location.href = 'murder.html';
    } else if (agentType === 'cyber') {
        window.location.href = 'cyber.html';
    }
}

// Setup card hover effects
function setupCardEffects() {
    const cards = document.querySelectorAll('.agent-card');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
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
    if (confirm('Are you sure you want to logout?')) {
        clearSession();
        window.location.href = 'login.html';
    }
}

// Periodic session validation
setInterval(function() {
    if (!getSession()) {
        alert('Your session has expired. Please login again.');
        window.location.href = 'login.html';
    }
}, 60000); // Check every minute
