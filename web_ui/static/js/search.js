/**
 * Search functionality for Door Installation Assistant
 * Handles document search and result display
 */

/**
 * Initialize the search functionality
 * @param {object} apiInstance - The API client instance
 */
function initSearch(apiInstance) {
    // Set up event listeners
    const btnSearch = document.getElementById('btnSearch');
    const btnDoSearch = document.getElementById('btnDoSearch');
    const btnCloseSearch = document.getElementById('btnCloseSearch');
    const searchInput = document.getElementById('searchInput');
    
    btnSearch.addEventListener('click', handleOpenSearch);
    btnDoSearch.addEventListener('click', () => handleSearch(apiInstance));
    btnCloseSearch.addEventListener('click', handleCloseSearch);
    
    // Add keydown event listener to search input
    searchInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            handleSearch(apiInstance);
        }
    });
}

/**
 * Handle opening the search panel
 */
function handleOpenSearch() {
    const searchPanel = document.getElementById('searchPanel');
    searchPanel.classList.add('show');
    
    // Focus search input
    const searchInput = document.getElementById('searchInput');
    searchInput.focus();
}

/**
 * Handle closing the search panel
 */
function handleCloseSearch() {
    const searchPanel = document.getElementById('searchPanel');
    searchPanel.classList.remove('show');
}

/**
 * Handle search submission
 * @param {object} apiInstance - The API client instance
 */
async function handleSearch(apiInstance) {
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');
    const query = searchInput.value.trim();
    
    if (!query) {
        searchResults.innerHTML = '<div class="search-no-results">Please enter a search query</div>';
        return;
    }
    
    try {
        // Show loading state
        searchResults.innerHTML = '<div class="search-loading">Searching...</div>';
        
        // Perform search
        const results = await apiInstance.searchDocuments(query);
        
        // Display results
        displaySearchResults(results.results || []);
        
    } catch (error) {
        console.error('Error performing search:', error);
        searchResults.innerHTML = `<div class="search-error">Error: ${error.message}</div>`;
    }
}

/**
 * Display search results
 * @param {Array} results - The search results to display
 */
function displaySearchResults(results) {
    const searchResults = document.getElementById('searchResults');
    
    if (!results || results.length === 0) {
        searchResults.innerHTML = '<div class="search-no-results">No results found</div>';
        return;
    }
    
    // Build results HTML
    let resultsHTML = '';
    
    results.forEach((result, index) => {
        const score = result.score ? (result.score * 100).toFixed(0) + '%' : 'N/A';
        const doorCategory = result.metadata?.door_category || 'unknown';
        const doorType = result.metadata?.door_type || 'unknown';
        const contentType = result.metadata?.content_type || 'general';
        
        // Format metadata as tags
        let tags = '';
        if (doorCategory !== 'unknown') {
            tags += `<span class="result-tag category-tag">${doorCategory}</span>`;
        }
        if (doorType !== 'unknown') {
            tags += `<span class="result-tag type-tag">${doorType}</span>`;
        }
        if (contentType !== 'general') {
            tags += `<span class="result-tag content-tag">${contentType}</span>`;
        }
        
        // Format text content
        let textContent = result.text;
        // Limit to 300 characters and add ellipsis if longer
        if (textContent.length > 300) {
            textContent = textContent.substring(0, 300) + '...';
        }
        
        resultsHTML += `
            <div class="search-result">
                <div class="result-header">
                    <span class="result-number">#${index + 1}</span>
                    <span class="result-score">Relevance: ${score}</span>
                </div>
                <div class="result-tags">
                    ${tags}
                </div>
                <div class="result-content">
                    <p>${textContent}</p>
                </div>
                <div class="result-actions">
                    <button class="btn btn-sm" onclick="useResultInChat('${index}')">
                        <i class="fa fa-comment"></i> Use in Chat
                    </button>
                    <button class="btn btn-sm" onclick="copyResultToClipboard('${index}')">
                        <i class="fa fa-copy"></i> Copy
                    </button>
                </div>
            </div>
        `;
    });
    
    // Update search results container
    searchResults.innerHTML = resultsHTML;
    
    // Store results for later use
    window.currentSearchResults = results;
}

/**
 * Use a search result in the chat
 * @param {number} index - The index of the result to use
 */
function useResultInChat(index) {
    const results = window.currentSearchResults;
    if (!results || !results[index]) return;
    
    // Get result text
    const resultText = results[index].text;
    
    // Set input value
    const chatInput = document.getElementById('chatInput');
    chatInput.value = `I found this information: "${resultText.substring(0, 100)}..." Can you explain this to me in simpler terms?`;
    
    // Close search panel
    handleCloseSearch();
    
    // Focus chat input
    chatInput.focus();
}

/**
 * Copy a search result to the clipboard
 * @param {number} index - The index of the result to copy
 */
function copyResultToClipboard(index) {
    const results = window.currentSearchResults;
    if (!results || !results[index]) return;
    
    // Get result text
    const resultText = results[index].text;
    
    // Copy to clipboard
    navigator.clipboard.writeText(resultText)
        .then(() => {
            // Show a tooltip or some indication that the copy was successful
            const resultElement = document.querySelectorAll('.search-result')[index];
            const copyButton = resultElement.querySelector('.result-actions button:nth-child(2)');
            
            const originalText = copyButton.innerHTML;
            copyButton.innerHTML = '<i class="fa fa-check"></i> Copied!';
            
            setTimeout(() => {
                copyButton.innerHTML = originalText;
            }, 2000);
        })
        .catch(err => {
            console.error('Error copying to clipboard:', err);
        });
}

// Export functions
window.handleOpenSearch = handleOpenSearch;
window.handleCloseSearch = handleCloseSearch;
window.handleSearch = handleSearch;
window.useResultInChat = useResultInChat;
window.copyResultToClipboard = copyResultToClipboard;