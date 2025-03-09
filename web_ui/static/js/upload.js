/**
 * Upload functionality for Door Installation Assistant
 * Handles document and image uploads
 */

/**
 * Initialize the upload functionality
 * @param {object} apiInstance - The API client instance
 */
function initUpload(apiInstance) {
    // Set up file upload listeners
    const fileUpload = document.getElementById('fileUpload');
    const fileName = document.getElementById('fileName');
    const uploadForm = document.getElementById('uploadForm');
    
    // Door image upload listeners
    const btnImportImage = document.getElementById('btnImportImage');
    const doorImageUpload = document.getElementById('doorImageUpload');
    const imageFileName = document.getElementById('imageFileName');
    const imagePreview = document.getElementById('imagePreview');
    const imageUploadModal = document.getElementById('imageUploadModal');
    const btnCloseImageUpload = document.getElementById('btnCloseImageUpload');
    const btnUploadImage = document.getElementById('btnUploadImage');
    const btnCancelImageUpload = document.getElementById('btnCancelImageUpload');
    
    // File upload event listeners
    fileUpload.addEventListener('change', handleFileSelect);
    uploadForm.addEventListener('submit', (e) => handleUploadDocument(e, apiInstance));
    
    // Door image upload event listeners
    if (btnImportImage) {
        btnImportImage.addEventListener('click', handleOpenImageUploadModal);
    }
    
    if (doorImageUpload) {
        doorImageUpload.addEventListener('change', handleImageSelect);
    }
    
    if (btnCloseImageUpload) {
        btnCloseImageUpload.addEventListener('click', handleCloseImageUploadModal);
    }
    
    if (btnCancelImageUpload) {
        btnCancelImageUpload.addEventListener('click', handleCloseImageUploadModal);
    }
    
    if (btnUploadImage) {
        btnUploadImage.addEventListener('click', () => handleUploadDoorImage(apiInstance));
    }
}

/**
 * Handle file selection for document upload
 * @param {Event} event - The change event
 */
function handleFileSelect(event) {
    const fileUpload = event.target;
    const fileName = document.getElementById('fileName');
    
    if (fileUpload.files.length > 0) {
        const file = fileUpload.files[0];
        
        // Update file name display
        fileName.textContent = file.name;
        
        // Enable upload button
        const uploadButton = document.getElementById('btnUpload');
        if (uploadButton) {
            uploadButton.disabled = false;
        }
    } else {
        fileName.textContent = '';
        
        // Disable upload button
        const uploadButton = document.getElementById('btnUpload');
        if (uploadButton) {
            uploadButton.disabled = true;
        }
    }
}

/**
 * Handle document upload
 * @param {Event} event - The submit event
 * @param {object} apiInstance - The API client instance
 */
async function handleUploadDocument(event, apiInstance) {
    event.preventDefault();
    
    const fileUpload = document.getElementById('fileUpload');
    const fileName = document.getElementById('fileName');
    
    if (fileUpload.files.length === 0) {
        showToast('Please select a file to upload.', 'warning');
        return;
    }
    
    const file = fileUpload.files[0];
    
    if (file.type !== 'application/pdf') {
        showToast('Please select a PDF file.', 'warning');
        return;
    }
    
    try {
        // Show loading state
        showLoading(true);
        
        // Get additional metadata from form
        const metadata = collectUploadMetadata();
        
        // Upload document
        const result = await apiInstance.uploadDocument(file, metadata);
        
        // Show success message
        showToast(`Document "${file.name}" uploaded successfully.`, 'success');
        
        if (typeof addSystemMessageToChat === 'function') {
            addSystemMessageToChat(`
                <p>✅ Document "${file.name}" uploaded successfully.</p>
                <p>Processed ${result.chunks} text segments from the document.</p>
                <p>You can now ask questions about the content of this document.</p>
            `);
        }
        
        // Reset form
        fileUpload.value = '';
        fileName.textContent = '';
        
        // Disable upload button
        const uploadButton = document.getElementById('btnUpload');
        if (uploadButton) {
            uploadButton.disabled = true;
        }
        
    } catch (error) {
        console.error('Error uploading document:', error);
        showToast(`Error uploading document: ${error.message}`, 'error');
        
        if (typeof addSystemMessageToChat === 'function') {
            addSystemMessageToChat(`❌ Error uploading document: ${error.message}`);
        }
    } finally {
        showLoading(false);
    }
}

/**
 * Collect metadata from upload form
 * @returns {object} Metadata object
 */
function collectUploadMetadata() {
    const metadata = {};
    
    // Get document type
    const documentTypeRadios = document.getElementsByName('documentType');
    if (documentTypeRadios.length > 0) {
        for (const radio of documentTypeRadios) {
            if (radio.checked) {
                metadata.document_type = radio.value;
                break;
            }
        }
    }
    
    // Get door category
    const doorCategoryRadios = document.getElementsByName('doorCategory');
    if (doorCategoryRadios.length > 0) {
        for (const radio of doorCategoryRadios) {
            if (radio.checked) {
                metadata.door_category = radio.value;
                break;
            }
        }
    } else {
        // Get from select element if radios don't exist
        const doorCategorySelect = document.getElementById('doorCategory');
        if (doorCategorySelect) {
            metadata.door_category = doorCategorySelect.value;
        }
    }
    
    // Get door type
    const doorTypeRadios = document.getElementsByName('doorType');
    if (doorTypeRadios.length > 0) {
        for (const radio of doorTypeRadios) {
            if (radio.checked) {
                metadata.door_type = radio.value;
                break;
            }
        }
    } else {
        // Get from select element if radios don't exist
        const doorTypeSelect = document.getElementById('doorType');
        if (doorTypeSelect) {
            metadata.door_type = doorTypeSelect.value;
        }
    }
    
    return metadata;
}

/**
 * Handle image selection for door identification
 * @param {Event} event - The change event
 */
function handleImageSelect(event) {
    const imageUpload = event.target;
    const imageFileName = document.getElementById('imageFileName');
    const imagePreview = document.getElementById('imagePreview');
    
    if (imageUpload.files.length > 0) {
        const file = imageUpload.files[0];
        
        // Update file name display
        imageFileName.textContent = file.name;
        
        // Show image preview
        const reader = new FileReader();
        reader.onload = function(e) {
            imagePreview.innerHTML = `<img src="${e.target.result}" alt="Door Image Preview">`;
        };
        reader.readAsDataURL(file);
        
        // Enable upload button
        const uploadButton = document.getElementById('btnUploadImage');
        if (uploadButton) {
            uploadButton.disabled = false;
        }
    } else {
        imageFileName.textContent = '';
        imagePreview.innerHTML = '';
        
        // Disable upload button
        const uploadButton = document.getElementById('btnUploadImage');
        if (uploadButton) {
            uploadButton.disabled = true;
        }
    }
}

/**
 * Handle opening the image upload modal
 */
function handleOpenImageUploadModal() {
    const imageUploadModal = document.getElementById('imageUploadModal');
    if (imageUploadModal) {
        imageUploadModal.classList.add('show');
    }
}

/**
 * Handle closing the image upload modal
 */
function handleCloseImageUploadModal() {
    const imageUploadModal = document.getElementById('imageUploadModal');
    if (imageUploadModal) {
        imageUploadModal.classList.remove('show');
    }
}

/**
 * Handle door image upload
 * @param {object} apiInstance - The API client instance
 */
async function handleUploadDoorImage(apiInstance) {
    const doorImageUpload = document.getElementById('doorImageUpload');
    
    if (!doorImageUpload || doorImageUpload.files.length === 0) {
        showToast('Please select an image to upload.', 'warning');
        return;
    }
    
    const file = doorImageUpload.files[0];
    
    try {
        // Show loading state
        showLoading(true);
        
        // Upload image for identification
        const result = await apiInstance.identifyDoorImage(file);
        
        // Close modal
        handleCloseImageUploadModal();
        
        if (result.identified) {
            // Update door info
            const doorCategory = result.door_category;
            const doorType = result.door_type;
            
            // Update select elements
            updateDoorInfoSelect('doorCategory', doorCategory);
            updateDoorInfoSelect('doorType', doorType);
            
            // Show success message
            showToast('Door identified successfully!', 'success');
            
            if (typeof addSystemMessageToChat === 'function') {
                addSystemMessageToChat(`
                    <p>✅ Door identified from image:</p>
                    <ul>
                        <li><strong>Category:</strong> ${doorCategory}</li>
                        <li><strong>Type:</strong> ${doorType}</li>
                        <li><strong>Confidence:</strong> ${(result.confidence * 100).toFixed(0)}%</li>
                    </ul>
                    <p>You can now ask specific questions about this door type.</p>
                `);
            }
        } else {
            // Show error message
            showToast('Could not identify the door from the image.', 'warning');
            
            if (typeof addSystemMessageToChat === 'function') {
                addSystemMessageToChat(`
                    <p>⚠️ Could not identify the door from the image.</p>
                    <p>Please select the door type manually or try with a clearer image.</p>
                `);
            }
        }
        
        // Reset form
        doorImageUpload.value = '';
        document.getElementById('imageFileName').textContent = '';
        document.getElementById('imagePreview').innerHTML = '';
        
        // Disable upload button
        const uploadButton = document.getElementById('btnUploadImage');
        if (uploadButton) {
            uploadButton.disabled = true;
        }
        
    } catch (error) {
        console.error('Error uploading door image:', error);
        showToast(`Error uploading image: ${error.message}`, 'error');
        
        if (typeof addSystemMessageToChat === 'function') {
            addSystemMessageToChat(`❌ Error uploading image: ${error.message}`);
        }
    } finally {
        showLoading(false);
    }
}

/**
 * Update a door info select element with the specified value
 * @param {string} selectId - The ID of the select element
 * @param {string} value - The value to select
 */
function updateDoorInfoSelect(selectId, value) {
    const select = document.getElementById(selectId);
    if (!select) return;
    
    // Find and select the option with the matching value
    for (const option of select.options) {
        if (option.value === value || option.textContent.toLowerCase() === value.toLowerCase()) {
            option.selected = true;
            
            // If updating the category, also update the type options
            if (selectId === 'doorCategory' && typeof updateDoorTypeOptions === 'function') {
                updateDoorTypeOptions(value);
            }
            
            break;
        }
    }
}

// Export functions
window.handleFileSelect = handleFileSelect;
window.handleUploadDocument = handleUploadDocument;
window.collectUploadMetadata = collectUploadMetadata;
window.handleImageSelect = handleImageSelect;
window.handleOpenImageUploadModal = handleOpenImageUploadModal;
window.handleCloseImageUploadModal = handleCloseImageUploadModal;
window.handleUploadDoorImage = handleUploadDoorImage;
window.updateDoorInfoSelect = updateDoorInfoSelect;