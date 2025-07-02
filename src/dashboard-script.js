// Dashboard Script
const SESSION_KEY = 'aiJusticeGrid_session';

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Check authentication
    checkAuthentication();

    // Check system status
    checkSystemStatus();

    // Setup event listeners
    setupEventListeners();
});

function checkAuthentication() {
    const session = getSession();
    if (!session || !session.isValid) {
        // User is not authenticated, redirect to login
        window.location.href = 'login.html';
        return;
    }

    // Update user info in header
    updateUserInfo(session);
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

function updateUserInfo(session) {
    // Extract username from email (everything before @)
    const username = session.username.split('@')[0];
    const userInfoElement = document.querySelector('.user-info span');
    if (userInfoElement) {
        userInfoElement.textContent = `Detective ${username.charAt(0).toUpperCase() + username.slice(1)}`;
    }
}

function setupEventListeners() {
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+1 for Murder Agent
        if (e.ctrlKey && e.key === '1') {
            e.preventDefault();
            selectAgent('murder');
        }
        // Ctrl+2 for Cyber Crime Agent
        if (e.ctrlKey && e.key === '2') {
            e.preventDefault();
            selectAgent('cyber');
        }
        // Escape to close modals
        if (e.key === 'Escape') {
            closeModals();
        }
    });
}

// async function checkSystemStatus() {
//     try {
//         // Check Murder Agent
//         const murderResponse = await fetch('https://aijusticegrid.onrender.com/api/murder', {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json',
//             },
//             body: JSON.stringify({
//                 question: 'ping'
//             })
//         });

//         // Check Cyber Crime Agent
//         const cyberResponse = await fetch('https://aijusticegrid.onrender.com/api/cyber', {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json',
//             },
//             body: JSON.stringify({
//                 question: 'ping'
//             })
//         });

//         if (murderResponse.ok && cyberResponse.ok) {
//             updateSystemStatus('online', 'System Online');
//         } else {
//             updateSystemStatus('warning', 'Partial Service');
//         }
//     } catch (error) {
//         console.error('System status check failed:', error);
//         updateSystemStatus('offline', 'System Offline');
//     }
// }

function updateSystemStatus(status, text) {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    if (statusDot && statusText) {
        statusDot.className = `status-dot ${status}`;
        statusText.textContent = text;
    }
}

function selectAgent(agentType) {
    // Show loading modal
    showLoadingModal(agentType);

    // Simulate initialization delay
    setTimeout(() => {
        if (agentType === 'murder') {
            window.location.href = 'index.html';
        } else if (agentType === 'cyber') {
            window.location.href = 'cybercrime.html';
        } else if (agentType === 'antismuggle') {
            window.location.href = 'antismuggling.html';
        } else if (agentType === 'customsborder') {
            window.location.href = 'customborder.html';
        } else if (agentType === 'humantrafficking') {
            window.location.href = 'humantrafficking.html';
        } else if (agentType === 'narcotics') {
            window.location.href = 'narcotics.html';
        } else if (agentType === 'moneylaundering') {
            window.location.href = 'moneylaundering.html';
        } else if (agentType === 'onlinefraud') {
            window.location.href = 'onlinefraud.html';
        } else if (agentType === 'sexualassault') {
            window.location.href = 'sexualassault.html';
        } else if (agentType === 'surveillance') {
            window.location.href = 'surveillance.html';
        } else if (agentType === 'theft') {
            window.location.href = 'theft.html';
        }
    }, 2000);
}

function showLoadingModal(agentType) {
    const modal = document.getElementById('loadingModal');
    const loadingText = document.getElementById('loadingText');

    if (modal && loadingText) {
        // Map agent types to display names
        const agentDisplayNames = {
            murder: "Murder Agent",
            cyber: "Cybercrime Agent",
            antismuggle: "Anti-Smuggling Agent",
            customsborder: "Customs & Border Agent",
            humantrafficking: "Human Trafficking Agent",
            narcotics: "Narcotics Agent",
            moneylaundering: "Money Laundering Agent",
            onlinefraud: "Online Fraud Agent",
            sexualassault: "Sexual Assault Agent",
            surveillance: "Surveillance Agent",
            theft: "Theft Agent"
        };

        // Fallback to generic if not matched
        const agentName = agentDisplayNames[agentType] || "Investigation Agent";

        // Update modal
        loadingText.textContent = `Initializing ${agentName}...`;
        modal.style.display = 'flex';
    }
}


function closeModals() {
    const modals = document.querySelectorAll('.modal-overlay');
    modals.forEach(modal => {
        modal.style.display = 'none';
    });
}

function logout() {
    // Clear session
    clearSession();

    // Show logout confirmation
    if (confirm('Are you sure you want to logout?')) {
        // Redirect to login page
        window.location.href = 'login.html';
    }
}

// function showHelp() {
//     alert('Help:\n\n' +
//           '• Select an investigation agent to begin case analysis\n' +
//           '• Murder Agent: For homicide investigations\n' +
//           '• Cyber Crime Agent: For cybercrime investigations\n' +
//           '• Use Ctrl+1 for Murder Agent, Ctrl+2 for Cyber Crime Agent\n' +
//           '• Contact system administrator for technical support');
// }

function showAbout() {
    alert('AiJusticeGrid v2.1.0\n\n' +
          'Advanced Criminal Investigation System\n' +
          'Powered by AI technology for enhanced case analysis\n\n' +
          '© 2024 AiJusticeGrid\n' +
          'Authorized Personnel Only');
}

function showPrivacy() {
    alert('Privacy Notice:\n\n' +
          '• All case data is encrypted and securely stored\n' +
          '• Access is logged and monitored\n' +
          '• Data is retained according to legal requirements\n' +
          '• Unauthorized access is strictly prohibited\n' +
          '• Contact your administrator for data requests');
}

// Add CSS for additional status states
const additionalStyles = document.createElement('style');
additionalStyles.textContent = `
    .status-dot.warning {
        background: #ffc107;
    }

    .status-dot.offline {
        background: #dc3545;
    }

    .status-indicator.warning {
        background: rgba(255, 193, 7, 0.1);
        border-color: rgba(255, 193, 7, 0.3);
    }

    .status-indicator.offline {
        background: rgba(220, 53, 69, 0.1);
        border-color: rgba(220, 53, 69, 0.3);
    }
`;
document.head.appendChild(additionalStyles);
