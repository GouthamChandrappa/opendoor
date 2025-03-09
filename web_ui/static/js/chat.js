/**
 * Chat functionality for Door Installation Assistant
 * Handles user input, message display, and interaction with the API
 */

let api; // API client instance
let doorInfo = { category: 'unknown', type: 'unknown' }; // Current door information
let isProcessing = false; // Flag to prevent multiple submissions

/**
 * Initialize the chat functionality
 * @param {string} sessionId - The session ID for the current user
 */
function initChat(sessionId, apiInstance) {
    api = apiInstance;
    
    // Initialize elements
    const chatInput = document.getElementById('chatInput');
    const btnSend = document.getElementById('btnSend');
    const btnVoice = document.getElementById('btnVoice');
    const btnClearChat = document.getElementById('btnClearChat');
    
    // Initialize door info selectors
    const doorCategorySelect = document.getElementById('doorCategory');
    const doorTypeSelect = document.getElementById('doorType');
    
    // Set up event listeners
    chatInput.addEventListener('keydown', handleInputKeydown);
    btnSend.addEventListener('click', handleSendMessage);
    btnVoice.addEventListener('click', handleVoiceInput);
    btnClearChat.addEventListener('click', handleClearChat);
    
    // Door info change listeners
    doorCategorySelect.addEventListener('change', handleDoorCategoryChange);
    doorTypeSelect.addEventListener('change', handleDoorTypeChange);
    
    // Set initial door info
    updateDoorTypeOptions(doorCategorySelect.value);
    
    // Load conversation history
    loadConversationHistory();
    
    // Auto-focus the input field
    chatInput.focus();
}

/**
 * Handle keydown event in the chat input
 * @param {KeyboardEvent} event - The keydown event
 */
function handleInputKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleSendMessage();
    }
}

/**
 * Handle sending a message
 */
async function handleSendMessage() {
    if (isProcessing) return;
    
    const chatInput = document.getElementById('chatInput');
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    try {
        isProcessing = true;
        showLoading(true);
        
        // Add user message to chat
        addMessageToChat('user', message);
        
        // Clear input
        chatInput.value = '';
        
        // Show typing indicator
        showTypingIndicator(true);
        
        // Process query with API
        const response = await api.processQuery(message);
        
        // Hide typing indicator
        showTypingIndicator(false);
        
        // Add assistant response to chat
        addMessageToChat('assistant', response.response);
        
        // Update door info if provided in response
        if (response.door_category && response.door_category !== 'unknown') {
            doorInfo.category = response.door_category;
            updateDoorInfoSelect('doorCategory', response.door_category);
        }
        
        if (response.door_type && response.door_type !== 'unknown') {
            doorInfo.type = response.door_type;
            updateDoorInfoSelect('doorType', response.door_type);
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        addSystemMessageToChat('Error: Could not process your request. Please try again.');
    } finally {
        isProcessing = false;
        showLoading(false);
        chatInput.focus();
    }
}

/**
 * Add a message to the chat window
 * @param {string} role - The role of the message sender (user, assistant, system)
 * @param {string} content - The message content
 */
function addMessageToChat(role, content) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const time = new Date();
    const timeString = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Format the content with Markdown if it's from the assistant
    let formattedContent = content;
    if (role === 'assistant') {
        formattedContent = formatMarkdown(content);
    }
    
    // Create message HTML
    let messageHTML = '';
    
    if (role === 'user' || role === 'assistant') {
        const avatar = role === 'user' ? 'U' : 'A';
        messageHTML += `<div class="message-avatar">${avatar}</div>`;
    }
    
    messageHTML += `
        <div class="message-content">
            ${formattedContent}
        </div>
        <div class="message-time">${timeString}</div>
    `;
    
    // Add message actions for assistant messages
    if (role === 'assistant') {
        messageHTML += `
            <div class="message-actions">
                <button class="message-action" onclick="copyMessageToClipboard(this)">
                    <i class="fa fa-copy"></i>
                </button>
                <button class="message-action" onclick="addToSearchQuery(this)">
                    <i class="fa fa-search"></i>
                </button>
            </div>
        `;
    }
    
    messageDiv.innerHTML = messageHTML;
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Add a system message to the chat
 * @param {string} content - The message content
 */
function addSystemMessageToChat(content) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';
    
    messageDiv.innerHTML = `
        <div class="message-content">
            ${content}
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Show or hide the typing indicator
 * @param {boolean} show - Whether to show the indicator
 */
function showTypingIndicator(show) {
    const chatMessages = document.getElementById('chatMessages');
    const existingIndicator = document.querySelector('.typing-indicator');
    
    if (show && !existingIndicator) {
        const indicatorDiv = document.createElement('div');
        indicatorDiv.className = 'typing-indicator';
        indicatorDiv.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        chatMessages.appendChild(indicatorDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } else if (!show && existingIndicator) {
        existingIndicator.remove();
    }
}

/**
 * Format markdown content to HTML
 * @param {string} content - The markdown content
 * @returns {string} - The HTML content
 */
function formatMarkdown(content) {
    // Replace headings
    content = content.replace(/^### (.*$)/gm, '<h3>$1</h3>');
    content = content.replace(/^## (.*$)/gm, '<h2>$1</h2>');
    content = content.replace(/^# (.*$)/gm, '<h1>$1</h1>');
    
    // Replace lists
    content = content.replace(/^\* (.*$)/gm, '<ul><li>$1</li></ul>');
    content = content.replace(/^- (.*$)/gm, '<ul><li>$1</li></ul>');
    content = content.replace(/^\d\. (.*$)/gm, '<ol><li>$1</li></ol>');
    
    // Fix lists (combine consecutive list items)
    content = content.replace(/<\/ul>\s*<ul>/g, '');
    content = content.replace(/<\/ol>\s*<ol>/g, '');
    
    // Replace emphasis and strong
    content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Replace code blocks
    content = content.replace(/```(\w+)?\s*\n([\s\S]*?)\n```/g, (match, language, code) => {
        const lang = language || 'plaintext';
        return `
            <div class="code-block">
                <div class="code-header">
                    <span class="code-language">${lang}</span>
                    <button class="copy-button" onclick="copyCodeToClipboard(this)">
                        <i class="fa fa-copy"></i> Copy
                    </button>
                </div>
                <pre><code class="language-${lang}">${escapeHTML(code)}</code></pre>
            </div>
        `;
    });
    
    // Replace inline code
    content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Replace links
    content = content.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    // Replace paragraphs
    content = content.split('\n\n').map(paragraph => {
        if (!paragraph.startsWith('<h') && 
            !paragraph.startsWith('<ul') && 
            !paragraph.startsWith('<ol') && 
            !paragraph.startsWith('<div class="code-block"')) {
            return `<p>${paragraph}</p>`;
        }
        return paragraph;
    }).join('');
    
    return `<div class="markdown-content">${content}</div>`;
}

/**
 * Escape HTML entities in a string
 * @param {string} html - The HTML string to escape
 * @returns {string} - The escaped HTML string
 */
function escapeHTML(html) {
    const div = document.createElement('div');
    div.textContent = html;
    return div.innerHTML;
}

/**
 * Handle voice input
 */
function handleVoiceInput() {
    // Check if speech recognition is available
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        addSystemMessageToChat('Voice input is not supported in this browser.');
        return;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    
    // Show recording indicator
    const btnVoice = document.getElementById('btnVoice');
    btnVoice.innerHTML = '<i class="fa fa-microphone" style="color: red;"></i>';
    addSystemMessageToChat('Listening...');
    
    recognition.start();
    
    recognition.onresult = function(event) {
        const speechResult = event.results[0][0].transcript;
        document.getElementById('chatInput').value = speechResult;
        
        // Reset recording indicator
        btnVoice.innerHTML = '<i class="fa fa-microphone"></i>';
        
        // Send the message
        handleSendMessage();
    };
    
    recognition.onerror = function(event) {
        console.error('Speech recognition error:', event.error);
        addSystemMessageToChat(`Error: ${event.error}`);
        
        // Reset recording indicator
        btnVoice.innerHTML = '<i class="fa fa-microphone"></i>';
    };
    
    recognition.onend = function() {
        // Reset recording indicator if it hasn't been reset already
        btnVoice.innerHTML = '<i class="fa fa-microphone"></i>';
    };
}

/**
 * Handle clearing the chat
 */
async function handleClearChat() {
    if (isProcessing) return;
    
    if (!confirm('Are you sure you want to clear the conversation?')) {
        return;
    }
    
    try {
        isProcessing = true;
        showLoading(true);
        
        // Clear chat in the API
        await api.clearConversationHistory();
        
        // Clear chat in the UI
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = '';
        
        // Add welcome message
        addSystemMessageToChat(`
            <p>Welcome to the Door Installation Assistant! I'm here to help you with installing various types of doors. You can ask me questions about:</p>
            <ul>
                <li>Step-by-step installation procedures</li>
                <li>Required tools and materials</li>
                <li>Troubleshooting common issues</li>
                <li>Safety guidelines</li>
            </ul>
            <p>What kind of door are you working with today?</p>
        `);
        
    } catch (error) {
        console.error('Error clearing chat:', error);
        addSystemMessageToChat('Error: Could not clear the conversation. Please try again.');
    } finally {
        isProcessing = false;
        showLoading(false);
    }
}

/**
 * Load conversation history from the API
 */
async function loadConversationHistory() {
    try {
        showLoading(true);
        
        // Get conversation history from the API
        const response = await api.getConversationHistory();
        
        if (response.messages && response.messages.length > 0) {
            // Clear existing messages
            const chatMessages = document.getElementById('chatMessages');
            chatMessages.innerHTML = '';
            
            // Add messages to chat
            response.messages.forEach(message => {
                addMessageToChat(message.role, message.content);
            });
        }
        
    } catch (error) {
        console.error('Error loading conversation history:', error);
        addSystemMessageToChat('Error: Could not load conversation history.');
    } finally {
        showLoading(false);
    }
}

/**
 * Handle door category change
 * @param {Event} event - The change event
 */
function handleDoorCategoryChange(event) {
    const category = event.target.value;
    doorInfo.category = category;
    
    // Update door type options based on the selected category
    updateDoorTypeOptions(category);
}

/**
 * Handle door type change
 * @param {Event} event - The change event
 */
function handleDoorTypeChange(event) {
    const type = event.target.value;
    doorInfo.type = type;
}

/**
 * Update door type options based on the selected category
 * @param {string} category - The selected door category
 */
function updateDoorTypeOptions(category) {
    const doorTypeSelect = document.getElementById('doorType');
    
    // Clear existing options
    doorTypeSelect.innerHTML = '<option value="unknown">Unknown</option>';
    
    // Add options based on category
    if (category === 'interior') {
        addOption(doorTypeSelect, 'bifold', 'Bifold');
        addOption(doorTypeSelect, 'prehung', 'Prehung');
    } else if (category === 'exterior') {
        addOption(doorTypeSelect, 'entry-door', 'Entry Door');
        addOption(doorTypeSelect, 'patio-door', 'Patio Door');
        addOption(doorTypeSelect, 'dentil-shelf', 'Dentil Shelf');
    }
    
    // Update the UI to show the currently selected type if it's valid for the category
    if (doorInfo.type !== 'unknown') {
        updateDoorInfoSelect('doorType', doorInfo.type);
    }
}

/**
 * Add an option to a select element
 * @param {HTMLSelectElement} select - The select element
 * @param {string} value - The option value
 * @param {string} text - The option text
 */
function addOption(select, value, text) {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = text;
    select.appendChild(option);
}

/**
 * Update a door info select element with the specified value
 * @param {string} selectId - The ID of the select element
 * @param {string} value - The value to select
 */
function updateDoorInfoSelect(selectId, value) {
    const select = document.getElementById(selectId);
    
    // Find and select the option with the matching value
    for (const option of select.options) {
        if (option.value === value || option.textContent.toLowerCase() === value.toLowerCase()) {
            option.selected = true;
            
            // If updating the category, also update the type options
            if (selectId === 'doorCategory') {
                updateDoorTypeOptions(value);
            }
            
            break;
        }
    }
}

/**
 * Copy message content to clipboard
 * @param {HTMLButtonElement} button - The button that was clicked
 */
function copyMessageToClipboard(button) {
    const messageContent = button.closest('.message').querySelector('.message-content').innerText;
    
    navigator.clipboard.writeText(messageContent)
        .then(() => {
            // Show a tooltip or some indication that the copy was successful
            const originalIcon = button.innerHTML;
            button.innerHTML = '<i class="fa fa-check"></i>';
            
            setTimeout(() => {
                button.innerHTML = originalIcon;
            }, 2000);
        })
        .catch(err => {
            console.error('Error copying to clipboard:', err);
        });
}

/**
 * Copy code to clipboard
 * @param {HTMLButtonElement} button - The button that was clicked
 */
function copyCodeToClipboard(button) {
    const codeBlock = button.closest('.code-block');
    const code = codeBlock.querySelector('code').innerText;
    
    navigator.clipboard.writeText(code)
        .then(() => {
            // Show a tooltip or some indication that the copy was successful
            const originalText = button.innerText;
            button.innerHTML = '<i class="fa fa-check"></i> Copied!';
            
            setTimeout(() => {
                button.innerHTML = originalText;
            }, 2000);
        })
        .catch(err => {
            console.error('Error copying to clipboard:', err);
        });
}

/**
 * Add content to search query
 * @param {HTMLButtonElement} button - The button that was clicked
 */
function addToSearchQuery(button) {
    const messageContent = button.closest('.message').querySelector('.message-content').innerText;
    const searchPanel = document.getElementById('searchPanel');
    const searchInput = document.getElementById('searchInput');
    
    // Extract a reasonable search query from the message
    const maxLength = 100;
    let searchQuery = messageContent.substring(0, maxLength);
    if (messageContent.length > maxLength) {
        searchQuery = searchQuery.substring(0, searchQuery.lastIndexOf(' ')) + '...';
    }
    
    // Show search panel
    searchPanel.classList.add('show');
    
    // Set search input value
    searchInput.value = searchQuery;
    
    // Focus search input
    searchInput.focus();
    searchInput.select();
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

// Export functions
window.handleSendMessage = handleSendMessage;
window.handleVoiceInput = handleVoiceInput;
window.handleClearChat = handleClearChat;
window.copyMessageToClipboard = copyMessageToClipboard;
window.copyCodeToClipboard = copyCodeToClipboard;
window.addToSearchQuery = addToSearchQuery;