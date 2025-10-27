// Configuration
const API_BASE_URL = 'http://localhost:8000';
const XANO_API_URL = 'https://xoho-w3ng-km3o.n7e.xano.io/api:L-QNLSmb/get_all_job_';
const STATUS_UPDATE_INTERVAL = 5000; // 5 seconds

// State
let sessionId = null;
let statusUpdateTimer = null;
let availableJobs = [];
let selectedJobId = null;
let selectedJobDetails = null;

// DOM Elements
const landingPage = document.getElementById('landingPage');
const chatInterface = document.getElementById('chatInterface');
const startButton = document.getElementById('startButton');
const landingError = document.getElementById('landingError');
const chatMessages = document.getElementById('chatMessages');
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const typingIndicator = document.getElementById('typingIndicator');
const sessionIdDisplay = document.getElementById('sessionIdDisplay');
const currentStageDisplay = document.getElementById('currentStage');
const apiStatus = document.getElementById('apiStatus');
const newSessionButton = document.getElementById('newSessionButton');
const resetButton = document.getElementById('resetButton');

// Job selection elements
const jobsLoadingIndicator = document.getElementById('jobsLoadingIndicator');
const jobSelectionDropdown = document.getElementById('jobSelectionDropdown');
const jobSelect = document.getElementById('jobSelect');
const refreshJobsButton = document.getElementById('refreshJobsButton');
const selectedJobInfo = document.getElementById('selectedJobInfo');
const jobsError = document.getElementById('jobsError');
const jobInfoSection = document.getElementById('jobInfoSection');
const jobInfo = document.getElementById('jobInfo');

// Progress elements
const engagementProgress = document.getElementById('engagementProgress');
const qualificationProgress = document.getElementById('qualificationProgress');
const applicationProgress = document.getElementById('applicationProgress');
const verificationProgress = document.getElementById('verificationProgress');

// Fit score elements
const fitScoreSection = document.getElementById('fitScoreSection');
const fitScoreValue = document.getElementById('fitScoreValue');
const fitScoreRating = document.getElementById('fitScoreRating');
const qualificationScore = document.getElementById('qualificationScore');
const experienceScore = document.getElementById('experienceScore');
const verificationScore = document.getElementById('verificationScore');
const calculateFitScoreButton = document.getElementById('calculateFitScoreButton');

// Document upload elements
const documentUploadForm = document.getElementById('documentUploadForm');
const documentFile = document.getElementById('documentFile');
const fileDisplayText = document.getElementById('fileDisplayText');
const fileBrowseButton = document.getElementById('fileBrowseButton');
const companyName = document.getElementById('companyName');
const documentType = document.getElementById('documentType');
const jobType = document.getElementById('jobType');
const documentSection = document.getElementById('documentSection');
const uploadButton = document.getElementById('uploadButton');
const uploadProgress = document.getElementById('uploadProgress');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const uploadResults = document.getElementById('uploadResults');
const uploadError = document.getElementById('uploadError');
const documentsList = document.getElementById('documentsList');
const refreshDocumentsButton = document.getElementById('refreshDocumentsButton');

// Utility Functions
function showError(element, message) {
    element.textContent = message;
    element.style.display = 'block';
    setTimeout(() => {
        element.style.display = 'none';
    }, 5000);
}

function formatTimestamp(isoString) {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

function addMessage(text, isUser = false, timestamp = new Date().toISOString()) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = isUser ? 'U' : 'C';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const text_p = document.createElement('p');
    text_p.className = 'message-text';
    text_p.textContent = text;
    
    const timestampDiv = document.createElement('div');
    timestampDiv.className = 'message-timestamp';
    timestampDiv.textContent = formatTimestamp(timestamp);
    
    content.appendChild(text_p);
    content.appendChild(timestampDiv);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function setInputEnabled(enabled) {
    messageInput.disabled = !enabled;
    sendButton.disabled = !enabled;
}

function showTypingIndicator() {
    typingIndicator.style.display = 'flex';
}

function hideTypingIndicator() {
    typingIndicator.style.display = 'none';
}

function updateApiStatus(status) {
    apiStatus.className = `api-status ${status}`;
    const statusText = apiStatus.querySelector('span');
    
    switch(status) {
        case 'connected':
            statusText.textContent = 'Connected';
            break;
        case 'error':
            statusText.textContent = 'Disconnected';
            break;
        default:
            statusText.textContent = 'Checking...';
    }
}

function updateSessionStatus(status) {
    // Update current stage
    currentStageDisplay.textContent = status.current_stage;
    
    // Update progress indicators
    updateProgressItem(engagementProgress, status.engagement_complete);
    updateProgressItem(qualificationProgress, status.qualification_complete);
    updateProgressItem(applicationProgress, status.application_complete);
    updateProgressItem(verificationProgress, status.verification_complete);
    
    // Show fit score section if application is complete
    if (status.application_complete) {
        fitScoreSection.style.display = 'block';
        updateFitScore();
    } else {
        fitScoreSection.style.display = 'none';
    }
}

function updateProgressItem(element, completed) {
    if (completed) {
        element.classList.add('completed');
        element.querySelector('.progress-icon').textContent = '✓';
    } else {
        element.classList.remove('completed');
        element.querySelector('.progress-icon').textContent = '○';
    }
}

async function updateFitScore() {
    try {
        const fitScoreData = await getFitScore();
        
        if (fitScoreData && fitScoreData.fit_score) {
            const score = fitScoreData.fit_score;
            
            // Update main score display
            fitScoreValue.textContent = Math.round(score.total_score);
            fitScoreRating.textContent = score.rating;
            
            // Update rating color
            fitScoreRating.className = 'fit-score-rating';
            const ratingClass = score.rating.toLowerCase().replace(' ', '-');
            fitScoreRating.classList.add(ratingClass);
            
            // Update breakdown scores
            qualificationScore.textContent = Math.round(score.qualification_score);
            experienceScore.textContent = Math.round(score.experience_score);
            verificationScore.textContent = Math.round(score.verification_score);
            
            // Hide calculate button since score is available
            calculateFitScoreButton.style.display = 'none';
        } else {
            // Show calculate button if no score available
            calculateFitScoreButton.style.display = 'block';
        }
    } catch (error) {
        console.error('Error updating fit score:', error);
        // Show calculate button on error
        calculateFitScoreButton.style.display = 'block';
    }
}

async function handleCalculateFitScore() {
    try {
        calculateFitScoreButton.disabled = true;
        calculateFitScoreButton.textContent = 'Calculating...';
        
        const result = await calculateFitScore();
        
        if (result && result.fit_score) {
            const score = result.fit_score;
            
            // Update displays
            fitScoreValue.textContent = Math.round(score.total_score);
            fitScoreRating.textContent = score.rating;
            
            // Update rating color
            fitScoreRating.className = 'fit-score-rating';
            const ratingClass = score.rating.toLowerCase().replace(' ', '-');
            fitScoreRating.classList.add(ratingClass);
            
            // Update breakdown scores
            qualificationScore.textContent = Math.round(score.qualification_score);
            experienceScore.textContent = Math.round(score.experience_score);
            verificationScore.textContent = Math.round(score.verification_score);
            
            // Hide the button
            calculateFitScoreButton.style.display = 'none';
            
            // Show success message
            addMessage('Your fit score has been calculated! Check the sidebar for details.', false);
            
            // Update session status to reflect changes
            const status = await getSessionStatus();
            updateSessionStatus(status);
        }
    } catch (error) {
        console.error('Error calculating fit score:', error);
        addMessage('Sorry, I encountered an error while calculating your fit score. Please try again.', false);
    } finally {
        calculateFitScoreButton.disabled = false;
        calculateFitScoreButton.textContent = 'Calculate Fit Score';
    }
}

// API Functions
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            updateApiStatus('connected');
            return true;
        } else {
            updateApiStatus('error');
            return false;
        }
    } catch (error) {
        console.error('Health check failed:', error);
        updateApiStatus('error');
        return false;
    }
}

async function fetchJobs() {
    try {
        const response = await fetch(XANO_API_URL, { timeout: 10000 });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const jobs = await response.json();
        return jobs;
    } catch (error) {
        console.error('Error fetching jobs:', error);
        throw error;
    }
}

async function loadJobs() {
    jobsLoadingIndicator.style.display = 'flex';
    jobSelectionDropdown.style.display = 'none';
    jobsError.style.display = 'none';
    
    try {
        availableJobs = await fetchJobs();
        
        // Clear existing options except the first one
        jobSelect.innerHTML = '<option value="">General Application (No specific job)</option>';
        
        // Add job options
        availableJobs.forEach(job => {
            const option = document.createElement('option');
            option.value = job.id;
            // Show job title, type, pay rate, and shift
            const payRate = job.PayRate ? `$${job.PayRate}/hr` : 'N/A';
            const jobType = job.job_type || 'N/A';
            const shift = job.Shift || 'N/A';
            option.textContent = `${job.job_title} - ${jobType} - ${payRate} - ${shift} shift`;
            option.dataset.job = JSON.stringify(job);
            jobSelect.appendChild(option);
        });
        
        jobsLoadingIndicator.style.display = 'none';
        jobSelectionDropdown.style.display = 'flex';
        
    } catch (error) {
        console.error('Error loading jobs:', error);
        jobsLoadingIndicator.style.display = 'none';
        showError(jobsError, 'Failed to load jobs. You can proceed without selecting a job.');
        // Show dropdown anyway so user can proceed
        jobSelectionDropdown.style.display = 'flex';
    }
}

async function createSession() {
    try {
        const payload = {
            retrieval_method: 'hybrid',
            language: 'en'
        };
        
        // Add job_id if a job is selected
        if (selectedJobId) {
            payload.job_id = selectedJobId;
        }
        
        const response = await fetch(`${API_BASE_URL}/api/v1/session/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error creating session:', error);
        throw error;
    }
}

async function sendMessage(message) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId,
                message: message
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error sending message:', error);
        throw error;
    }
}

async function getSessionStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/session/${sessionId}/status`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error getting session status:', error);
        throw error;
    }
}

async function getFitScore() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/session/${sessionId}/fit_score`);
        
        if (!response.ok) {
            if (response.status === 400) {
                // Application not complete yet
                return null;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error getting fit score:', error);
        return null;
    }
}

async function calculateFitScore() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/session/${sessionId}/calculate_fit_score`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error calculating fit score:', error);
        throw error;
    }
}

async function resetSession() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/session/${sessionId}/reset`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error resetting session:', error);
        throw error;
    }
}

// Event Handlers
function handleJobSelection() {
    const selectedOption = jobSelect.options[jobSelect.selectedIndex];
    selectedJobId = jobSelect.value || null;
    
    if (selectedJobId && selectedOption.dataset.job) {
        selectedJobDetails = JSON.parse(selectedOption.dataset.job);
        
        // Determine age requirement
        let ageReq = "Not specified";
        if (selectedJobDetails.Age_18_Above) {
            ageReq = "18+";
        } else if (selectedJobDetails.Age_16_above) {
            ageReq = "16+";
        }
        
        // Show job info preview
        selectedJobInfo.innerHTML = `
            <div class="job-preview">
                <h4>${selectedJobDetails.job_title}</h4>
                <p><strong>Job Type:</strong> ${selectedJobDetails.job_type || 'N/A'}</p>
                <p><strong>Pay Rate:</strong> $${selectedJobDetails.PayRate || 'N/A'}/hour</p>
                <p><strong>Shift:</strong> ${selectedJobDetails.Shift || 'N/A'}</p>
                <p><strong>Experience Required:</strong> ${selectedJobDetails.required_experience || 'N/A'} years</p>
                <p><strong>Age Requirement:</strong> ${ageReq}</p>
                <p><strong>Starting Date:</strong> ${selectedJobDetails.Starting_Date || 'N/A'}</p>
                ${selectedJobDetails.description ? `<p><strong>Description:</strong> ${selectedJobDetails.description.substring(0, 150)}...</p>` : ''}
            </div>
        `;
        selectedJobInfo.style.display = 'block';
    } else {
        selectedJobDetails = null;
        selectedJobInfo.style.display = 'none';
    }
}

async function handleStartConversation() {
    startButton.disabled = true;
    startButton.textContent = 'Starting...';
    
    try {
        // Check API health
        const isHealthy = await checkHealth();
        if (!isHealthy) {
            throw new Error('API is not available. Please make sure the backend is running.');
        }
        
        // Create session (with job_id if selected)
        const sessionData = await createSession();
        sessionId = sessionData.session_id;
        
        // Update UI
        sessionIdDisplay.textContent = sessionId;
        
        // Show job info in sidebar if a job was selected
        if (selectedJobDetails) {
            const ageReq = selectedJobDetails.Age_18_Above ? "18+" : 
                          selectedJobDetails.Age_16_above ? "16+" : "N/A";
            
            jobInfo.innerHTML = `
                <div class="job-info-content">
                    <div class="job-info-title">${selectedJobDetails.job_title}</div>
                    <div class="job-info-detail"><strong>Type:</strong> ${selectedJobDetails.job_type || 'N/A'}</div>
                    <div class="job-info-detail"><strong>Pay:</strong> $${selectedJobDetails.PayRate || 'N/A'}/hr</div>
                    <div class="job-info-detail"><strong>Shift:</strong> ${selectedJobDetails.Shift || 'N/A'}</div>
                    <div class="job-info-detail"><strong>Experience:</strong> ${selectedJobDetails.required_experience || 'N/A'} yrs</div>
                    <div class="job-info-detail"><strong>Age:</strong> ${ageReq}</div>
                </div>
            `;
            jobInfoSection.style.display = 'block';
        }
        
        // Hide landing page and show chat
        landingPage.style.display = 'none';
        chatInterface.style.display = 'grid';
        
        // Add Cleo's welcome message (it's already personalized from the API)
        addMessage(sessionData.message, false);
        
        // Start status updates
        startStatusUpdates();
        
        // Focus input
        messageInput.focus();
        
    } catch (error) {
        console.error('Error starting conversation:', error);
        showError(landingError, error.message);
        startButton.disabled = false;
        startButton.textContent = 'Start Conversation';
    }
}

async function handleSendMessage(e) {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addMessage(message, true);
    
    // Clear input
    messageInput.value = '';
    
    // Disable input and show typing indicator
    setInputEnabled(false);
    showTypingIndicator();
    
    try {
        // Send message to API
        const response = await sendMessage(message);
        
        // Hide typing indicator before adding messages
        hideTypingIndicator();
        
        // Add assistant response(s) - handle multiple messages
        if (response.responses && Array.isArray(response.responses)) {
            // Add multiple messages with slight delays for natural flow
            for (let i = 0; i < response.responses.length; i++) {
                // Show typing indicator before each message (except the first)
                if (i > 0) {
                    showTypingIndicator();
                    await new Promise(resolve => setTimeout(resolve, 800)); // 800ms delay between messages
                    hideTypingIndicator();
                }
                
                addMessage(response.responses[i], false, response.timestamp);
                
                // Small delay after adding message for smooth scrolling
                if (i < response.responses.length - 1) {
                    await new Promise(resolve => setTimeout(resolve, 400));
                }
            }
        } else {
            // Fallback for backward compatibility (if API returns single response)
            const messageText = response.response || response.responses[0] || "I'm sorry, I didn't get that.";
            addMessage(messageText, false, response.timestamp);
        }
        
        // Update session status
        const status = await getSessionStatus();
        updateSessionStatus(status);
        
    } catch (error) {
        console.error('Error sending message:', error);
        hideTypingIndicator();
        addMessage('Sorry, I encountered an error. Please try again.', false);
    } finally {
        setInputEnabled(true);
        messageInput.focus();
    }
}

async function handleNewSession() {
    if (confirm('Are you sure you want to start a new session? This will clear the current conversation.')) {
        // Stop status updates
        stopStatusUpdates();
        
        // Clear messages
        chatMessages.innerHTML = '';
        
        // Show landing page
        chatInterface.style.display = 'none';
        landingPage.style.display = 'flex';
        
        // Reset state
        sessionId = null;
        
        // Reset button
        startButton.disabled = false;
        startButton.textContent = 'Start Conversation';
    }
}

async function handleResetSession() {
    if (confirm('Are you sure you want to reset the conversation? This will clear all messages.')) {
        try {
            await resetSession();
            
            // Clear messages
            chatMessages.innerHTML = '';
            
            // Add reset confirmation
            addMessage('Conversation has been reset. You can start over!', false);
            
            // Update status
            const status = await getSessionStatus();
            updateSessionStatus(status);
            
        } catch (error) {
            console.error('Error resetting session:', error);
            addMessage('Sorry, I encountered an error while resetting. Please try again.', false);
        }
    }
}

function startStatusUpdates() {
    // Initial status check
    checkHealth();
    
    // Update status periodically
    statusUpdateTimer = setInterval(async () => {
        try {
            await checkHealth();
            if (sessionId) {
                const status = await getSessionStatus();
                updateSessionStatus(status);
            }
        } catch (error) {
            console.error('Error updating status:', error);
        }
    }, STATUS_UPDATE_INTERVAL);
}

function stopStatusUpdates() {
    if (statusUpdateTimer) {
        clearInterval(statusUpdateTimer);
        statusUpdateTimer = null;
    }
}

// Document Upload Functions
async function handleDocumentUpload(event) {
    event.preventDefault();
    
    const formData = new FormData(documentUploadForm);
    const file = documentFile.files[0];
    
    if (!file) {
        showUploadError('Please select a PDF file.');
        return;
    }
    
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showUploadError('Only PDF files are allowed.');
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) { // 10MB limit
        showUploadError('File size must be less than 10MB.');
        return;
    }
    
    try {
        showUploadProgress(true);
        hideUploadError();
        hideUploadResults();
        
        // Simulate upload progress
        updateUploadProgress(0, 'Uploading...');
        
        const response = await fetch(`${API_BASE_URL}/api/v1/documents/upload`, {
            method: 'POST',
            body: formData
        });
        
        updateUploadProgress(100, 'Processing...');
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Upload failed');
        }
        
        const result = await response.json();
        showUploadSuccess(result);
        resetUploadForm();
        loadUploadedDocuments(); // Refresh the documents list
        
    } catch (error) {
        console.error('Upload error:', error);
        showUploadError(error.message || 'Upload failed');
    } finally {
        showUploadProgress(false);
    }
}

function handleFileSelection() {
    const file = documentFile.files[0];
    if (file) {
        fileDisplayText.textContent = file.name;
        fileDisplayText.classList.add('file-selected');
    } else {
        fileDisplayText.textContent = 'Choose PDF file...';
        fileDisplayText.classList.remove('file-selected');
    }
}

function handleBrowseClick() {
    documentFile.click();
}

function handleFileInputDisplayClick() {
    documentFile.click();
}

function showUploadProgress(show) {
    uploadProgress.style.display = show ? 'block' : 'none';
    uploadButton.disabled = show;
    
    if (show) {
        uploadButton.querySelector('.upload-text').style.display = 'none';
        uploadButton.querySelector('.upload-spinner').style.display = 'inline-block';
    } else {
        uploadButton.querySelector('.upload-text').style.display = 'inline';
        uploadButton.querySelector('.upload-spinner').style.display = 'none';
    }
}

function updateUploadProgress(percentage, text) {
    progressFill.style.width = percentage + '%';
    progressText.textContent = text;
}

function showUploadSuccess(result) {
    uploadResults.innerHTML = `
        <div class="upload-success">
            <div class="success-icon">✓</div>
            <div class="success-message">
                <strong>${result.filename}</strong> uploaded successfully!
                <div class="upload-details">
                    <span>Type: ${result.document_type}</span>
                    <span>Category: ${result.job_type}</span>
                    <span>Section: ${result.section}</span>
                </div>
            </div>
        </div>
    `;
    uploadResults.style.display = 'block';
    setTimeout(() => {
        uploadResults.style.display = 'none';
    }, 5000);
}

function showUploadError(message) {
    uploadError.textContent = message;
    uploadError.style.display = 'block';
}

function hideUploadError() {
    uploadError.style.display = 'none';
}

function hideUploadResults() {
    uploadResults.style.display = 'none';
}

function resetUploadForm() {
    documentUploadForm.reset();
    fileDisplayText.textContent = 'Choose PDF file...';
    fileDisplayText.classList.remove('file-selected');
    companyName.value = '';
    documentType.value = '';
    jobType.value = 'general';
    documentSection.value = 'general';
}

async function loadUploadedDocuments() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/documents`);
        
        if (!response.ok) {
            throw new Error('Failed to load documents');
        }
        
        const data = await response.json();
        displayUploadedDocuments(data.documents);
        
    } catch (error) {
        console.error('Error loading documents:', error);
        documentsList.innerHTML = '<div class="error-message">Failed to load documents</div>';
    }
}

function displayUploadedDocuments(documents) {
    if (!documents || documents.length === 0) {
        documentsList.innerHTML = '<div class="no-documents">No documents uploaded yet.</div>';
        return;
    }
    
    const documentsHtml = documents.map(doc => {
        const uploadDate = new Date(doc.upload_date).toLocaleDateString();
        const fileSize = formatFileSize(doc.file_size);
        
        return `
            <div class="document-item" data-document-id="${doc.document_id}">
                <div class="document-info">
                    <div class="document-name">${doc.original_filename || doc.filename}</div>
                    <div class="document-details">
                        <span class="document-type">${doc.document_type}</span>
                        <span class="document-category">${doc.job_type}</span>
                        <span class="document-section">${doc.section}</span>
                    </div>
                    <div class="document-meta">
                        <span class="file-size">${fileSize}</span>
                        <span class="upload-date">${uploadDate}</span>
                    </div>
                </div>
                <div class="document-actions">
                    <button class="delete-document-button" onclick="deleteDocument('${doc.document_id}')" title="Delete document">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
                        </svg>
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    documentsList.innerHTML = documentsHtml;
}

async function deleteDocument(documentId) {
    if (!confirm('Are you sure you want to delete this document?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/documents/${documentId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete document');
        }
        
        loadUploadedDocuments(); // Refresh the list
        
    } catch (error) {
        console.error('Error deleting document:', error);
        alert('Failed to delete document: ' + error.message);
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Event Listeners
startButton.addEventListener('click', handleStartConversation);
chatForm.addEventListener('submit', handleSendMessage);
newSessionButton.addEventListener('click', handleNewSession);
resetButton.addEventListener('click', handleResetSession);
jobSelect.addEventListener('change', handleJobSelection);
refreshJobsButton.addEventListener('click', loadJobs);
calculateFitScoreButton.addEventListener('click', handleCalculateFitScore);

// Document upload event listeners
documentUploadForm.addEventListener('submit', handleDocumentUpload);
documentFile.addEventListener('change', handleFileSelection);
fileBrowseButton.addEventListener('click', handleBrowseClick);
document.querySelector('.file-input-display').addEventListener('click', handleFileInputDisplayClick);
refreshDocumentsButton.addEventListener('click', loadUploadedDocuments);

// Load jobs and documents on page load
loadJobs();
loadUploadedDocuments();

// Initial health check
checkHealth();

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    stopStatusUpdates();
});
