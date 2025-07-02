// Login credentials
const VALID_CREDENTIALS = {
    username: 'admin@police.gov',
    password: 'policecrime@586$gov'
};

// Session management
const SESSION_KEY = 'aiJusticeGrid_session';
const SESSION_DURATION = 24 * 60 * 60 * 1000; // 24 hours

// Initialize the login page
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is already logged in
    checkExistingSession();

    // Setup event listeners
    setupEventListeners();

    // Add input animations
    setupInputAnimations();
});

function checkExistingSession() {
    const session = getSession();
    if (session && session.isValid) {
        // User is already logged in, redirect to dashboard
        showSuccessModal();
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 2000);
    }
}

function setupEventListeners() {
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');

    // Form submission
    loginForm.addEventListener('submit', handleLogin);

    // Enter key handling
    usernameInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            passwordInput.focus();
        }
    });

    passwordInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleLogin(e);
        }
    });

    // Clear error message on input
    usernameInput.addEventListener('input', clearErrorMessage);
    passwordInput.addEventListener('input', clearErrorMessage);

    // Forgot password link
    document.querySelector('.forgot-password').addEventListener('click', function(e) {
        e.preventDefault();
        showAssistanceModal();
    });
}

function setupInputAnimations() {
    const inputs = document.querySelectorAll('input[type="email"], input[type="password"]');

    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });

        input.addEventListener('blur', function() {
            if (!this.value) {
                this.parentElement.classList.remove('focused');
            }
        });

        // Check if input has value on load
        if (input.value) {
            input.parentElement.classList.add('focused');
        }
    });
}

async function handleLogin(e) {
    e.preventDefault();

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const rememberMe = document.getElementById('rememberMe').checked;

    // Clear any existing error messages
    clearErrorMessage();

    // Validate inputs
    if (!username || !password) {
        showErrorMessage('Please enter both username and password');
        return;
    }

    // Show loading state
    setLoadingState(true);

    // Simulate authentication delay for better UX
    await new Promise(resolve => setTimeout(resolve, 1500));

    // Validate credentials
    if (validateCredentials(username, password)) {
        // Create session
        createSession(rememberMe);

        // Show success modal
        showSuccessModal();

        // Redirect after delay
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 3000);

    } else {
        setLoadingState(false);
        showErrorMessage('Invalid credentials. Please check your username and password.');

        // Add shake animation to form
        const loginForm = document.getElementById('loginForm');
        loginForm.classList.add('shake');
        setTimeout(() => {
            loginForm.classList.remove('shake');
        }, 500);
    }
}

function validateCredentials(username, password) {
    return username === VALID_CREDENTIALS.username && password === VALID_CREDENTIALS.password;
}

function createSession(rememberMe) {
    const session = {
        username: VALID_CREDENTIALS.username,
        loginTime: Date.now(),
        expiresAt: Date.now() + SESSION_DURATION,
        rememberMe: rememberMe,
        isValid: true
    };

    if (rememberMe) {
        localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    } else {
        sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
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

function setLoadingState(loading) {
    const loginBtn = document.getElementById('loginBtn');
    const btnText = loginBtn.querySelector('.btn-text');
    const btnIcon = loginBtn.querySelector('.btn-icon');
    const btnLoading = loginBtn.querySelector('.btn-loading');

    if (loading) {
        loginBtn.disabled = true;
        btnText.style.display = 'none';
        btnIcon.style.display = 'none';
        btnLoading.style.display = 'block';
        loginBtn.style.cursor = 'not-allowed';
    } else {
        loginBtn.disabled = false;
        btnText.style.display = 'block';
        btnIcon.style.display = 'block';
        btnLoading.style.display = 'none';
        loginBtn.style.cursor = 'pointer';
    }
}

function showErrorMessage(message) {
    const errorElement = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');

    errorText.textContent = message;
    errorElement.style.display = 'flex';

    // Auto-hide after 5 seconds
    setTimeout(() => {
        clearErrorMessage();
    }, 5000);
}

function clearErrorMessage() {
    const errorElement = document.getElementById('errorMessage');
    errorElement.style.display = 'none';
}

function showSuccessModal() {
    const modal = document.getElementById('successModal');
    modal.style.display = 'flex';
}

function showAssistanceModal() {
    alert('For assistance with login credentials, please contact your system administrator or IT support team.\n\nAuthorized personnel only.');
}

function togglePassword() {
    const passwordInput = document.getElementById('password');
    const toggleIcon = document.getElementById('passwordToggleIcon');

    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleIcon.className = 'fas fa-eye-slash';
    } else {
        passwordInput.type = 'password';
        toggleIcon.className = 'fas fa-eye';
    }
}

// Security features
document.addEventListener('contextmenu', function(e) {
    e.preventDefault(); // Disable right-click
});

document.addEventListener('keydown', function(e) {
    // Disable F12, Ctrl+Shift+I, Ctrl+U
    if (e.key === 'F12' ||
        (e.ctrlKey && e.shiftKey && e.key === 'I') ||
        (e.ctrlKey && e.key === 'u')) {
        e.preventDefault();
    }
});

// Add CSS for shake animation
const style = document.createElement('style');
style.textContent = `
    .shake {
        animation: shake 0.5s ease-in-out;
    }

    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-10px); }
        75% { transform: translateX(10px); }
    }
`;
document.head.appendChild(style);
