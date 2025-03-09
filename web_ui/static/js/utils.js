/**
 * Utility functions for Door Installation Assistant
 */

/**
 * Generate a unique session ID
 * @returns {string} - A unique session ID
 */
function generateSessionId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

/**
 * Initialize the application
 * @param {string} sessionId - The session ID
 */
function initApp(sessionId) {
    // Get saved API URL from local storage or use default
    const savedApiUrl = localStorage.getItem('apiUrl') || 'http://localhost:8000';
    document.getElementById('apiUrl').value = savedApiUrl;
    
    // Initialize API client
    const api = new DoorAssistantAPI(savedApiUrl, sessionId);
    
    // Check connection to API
    checkApiConnection(api);
    
    // Initialize settings
    initSettings(api);
    
    // Initialize chat functionality
    initChat(sessionId, api);
    
    // Initialize search functionality
    initSearch(api);
    
    // Initialize upload functionality
    initUpload(api);
}

/**
 * Check connection to the API
 * @param {object} api - The API client instance
 */
async function checkApiConnection(api) {
    try {
        const connected = await api.checkConnection();
        updateConnectionStatus(connected);
    } catch (error) {
        console.error('Error checking API connection:', error);
        updateConnectionStatus(false);
    }
}

/**
 * Update the connection status indicator
 * @param {boolean} connected - Whether the API is connected
 */
function updateConnectionStatus(connected) {
    const statusIndicator = document.getElementById('connectionStatus');
    const statusText = statusIndicator.nextElementSibling;
    
    if (connected) {
        statusIndicator.className = 'status-indicator connected';
        statusText.textContent = 'Connected';
    } else {
        statusIndicator.className = 'status-indicator disconnected';
        statusText.textContent = 'Disconnected';
        
        // Show warning message
        addSystemMessageToChat(`
            <p>⚠️ <strong>API Connection Error</strong></p>
            <p>Could not connect to the Door Installation Assistant API.</p>
            <p>Please check your connection and API settings.</p>
        `);
    }
}

/**
 * Initialize settings functionality
 * @param {object} api - The API client instance
 */
function initSettings(api) {
    // Settings elements
    const btnSettings = document.getElementById('btnSettings');
    const settingsModal = document.getElementById('settingsModal');
    const btnCloseSettings = document.getElementById('btnCloseSettings');
    const btnSaveSettings = document.getElementById('btnSaveSettings');
    const btnCancelSettings = document.getElementById('btnCancelSettings');
    const apiUrlInput = document.getElementById('apiUrl');
    const fontSizeSelect = document.getElementById('fontSize');
    const themeSelect = document.getElementById('theme');
    
    // Load saved settings
    const savedFontSize = localStorage.getItem('fontSize') || 'medium';
    const savedTheme = localStorage.getItem('theme') || 'light';
    
    fontSizeSelect.value = savedFontSize;
    themeSelect.value = savedTheme;
    
    // Apply saved settings
    applyFontSize(savedFontSize);
    applyTheme(savedTheme);
    
    // Event listeners
    btnSettings.addEventListener('click', () => {
        settingsModal.classList.add('show');
    });
    
    btnCloseSettings.addEventListener('click', () => {
        settingsModal.classList.remove('show');
    });
    
    btnCancelSettings.addEventListener('click', () => {
        // Reset values to saved settings
        apiUrlInput.value = localStorage.getItem('apiUrl') || 'http://localhost:8000';
        fontSizeSelect.value = localStorage.getItem('fontSize') || 'medium';
        themeSelect.value = localStorage.getItem('theme') || 'light';
        
        // Close modal
        settingsModal.classList.remove('show');
    });
    
    btnSaveSettings.addEventListener('click', () => {
        // Save settings
        const apiUrl = apiUrlInput.value.trim();
        const fontSize = fontSizeSelect.value;
        const theme = themeSelect.value;
        
        // Update API URL
        if (apiUrl !== api.baseUrl) {
            api.setBaseUrl(apiUrl);
            localStorage.setItem('apiUrl', apiUrl);
            
            // Check connection to new API URL
            checkApiConnection(api);
        }
        
        // Update font size
        localStorage.setItem('fontSize', fontSize);
        applyFontSize(fontSize);
        
        // Update theme
        localStorage.setItem('theme', theme);
        applyTheme(theme);
        
        // Close modal
        settingsModal.classList.remove('show');
    });
    
    // Font size change listener
    fontSizeSelect.addEventListener('change', () => {
        applyFontSize(fontSizeSelect.value);
    });
    
    // Theme change listener
    themeSelect.addEventListener('change', () => {
        applyTheme(themeSelect.value);
    });
}

/**
 * Apply the selected font size
 * @param {string} fontSize - The font size to apply (small, medium, large)
 */
function applyFontSize(fontSize) {
    const htmlElement = document.documentElement;
    
    // Remove existing font-size classes
    htmlElement.classList.remove('font-size-small', 'font-size-medium', 'font-size-large');
    
    // Add the selected font-size class
    htmlElement.classList.add(`font-size-${fontSize}`);
}

/**
 * Apply the selected theme
 * @param {string} theme - The theme to apply (light, dark)
 */
function applyTheme(theme) {
    const htmlElement = document.documentElement;
    
    if (theme === 'dark') {
        htmlElement.setAttribute('data-theme', 'dark');
    } else {
        htmlElement.removeAttribute('data-theme');
    }
}

/**
 * Add a system message to the chat
 * This function is defined in chat.js but needs to be accessible globally
 * @param {string} content - The message content
 */
/**
 * Add a system message to the chat
 * This function is defined in chat.js but needs to be accessible globally
 * @param {string} content - The message content
 */
function addSystemMessageToChat(content) {
    // This will be properly defined in chat.js
    // We're just providing the interface here for accessibility
    if (typeof window.addSystemMessageToChat === 'function') {
        window.addSystemMessageToChat(content);
    } else {
        console.error('addSystemMessageToChat is not defined');
    }
}

/**
 * Show or hide the loading overlay
 * @param {boolean} show - Whether to show the loading overlay
 */
function showLoading(show) {
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    if (show) {
        loadingOverlay.classList.add('show');
    } else {
        loadingOverlay.classList.remove('show');
    }
}

/**
 * Show a toast notification
 * @param {string} message - The message to show
 * @param {string} type - The type of toast (success, error, warning, info)
 * @param {number} duration - The duration in milliseconds
 */
function showToast(message, type = 'info', duration = 5000) {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Set icon based on type
    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    if (type === 'error') icon = 'exclamation-circle';
    if (type === 'warning') icon = 'exclamation-triangle';
    
    // Create toast content
    toast.innerHTML = `
        <span class="toast-icon"><i class="fa fa-${icon}"></i></span>
        <span class="toast-message">${message}</span>
        <button class="toast-close"><i class="fa fa-times"></i></button>
    `;
    
    // Add toast to container
    toastContainer.appendChild(toast);
    
    // Add close event
    const closeButton = toast.querySelector('.toast-close');
    closeButton.addEventListener('click', () => {
        toast.remove();
    });
    
    // Auto remove after duration
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, duration);
}

// Export functions
window.generateSessionId = generateSessionId;
window.initApp = initApp;
window.checkApiConnection = checkApiConnection;
window.updateConnectionStatus = updateConnectionStatus;
window.applyFontSize = applyFontSize;
window.applyTheme = applyTheme;
window.addSystemMessageToChat = addSystemMessageToChat;
window.showLoading = showLoading;
window.showToast = showToast;