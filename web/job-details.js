// Configuration
const API_BASE_URL = 'https://scanandhire.com:8001';
//const API_BASE_URL = 'http://localhost:8000'; // For local testing
const XANO_JOB_BY_ID_URL = 'https://xoho-w3ng-km3o.n7e.xano.io/api:L-QNLSmb/job';

// Get job ID from URL
function getJobIdFromURL() {
    const pathParts = window.location.pathname.split('/');
    const jobDetailsIndex = pathParts.indexOf('job-details');
    if (jobDetailsIndex !== -1 && pathParts.length > jobDetailsIndex + 1) {
        return pathParts[jobDetailsIndex + 1];
    }
    return null;
}

// Format date
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
    } catch (e) {
        return dateString;
    }
}

// Parse and render list data (array or string)
function renderListData(data) {
    if (!data) return '<p>Not specified</p>';
    
    if (Array.isArray(data)) {
        if (data.length === 0) return '<p>Not specified</p>';
        return '<ul>' + data.map(item => `<li>${item}</li>`).join('') + '</ul>';
    }
    
    if (typeof data === 'string') {
        // Try to parse as JSON first
        try {
            const parsed = JSON.parse(data);
            if (Array.isArray(parsed)) {
                return '<ul>' + parsed.map(item => `<li>${item}</li>`).join('') + '</ul>';
            }
        } catch (e) {
            // If not JSON, check if it contains line breaks or bullets
            if (data.includes('\n') || data.includes('•') || data.includes('-')) {
                const lines = data.split(/[\n•-]/).filter(line => line.trim());
                if (lines.length > 1) {
                    return '<ul>' + lines.map(line => `<li>${line.trim()}</li>`).join('') + '</ul>';
                }
            }
        }
        return `<p>${data}</p>`;
    }
    
    return '<p>Not specified</p>';
}

// Render job meta information
function renderJobMeta(job) {
    const metaContainer = document.getElementById('jobMeta');
    const metaItems = [];
    
    if (job.job_location) {
        metaItems.push(`
            <div class="job-meta-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                    <circle cx="12" cy="10" r="3"></circle>
                </svg>
                <span>${job.job_location}</span>
            </div>
        `);
    }
    
    if (job.job_type) {
        metaItems.push(`
            <div class="job-meta-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
                    <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
                </svg>
                <span>${job.job_type}</span>
            </div>
        `);
    }
    
    if (job.posted_date) {
        metaItems.push(`
            <div class="job-meta-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="16" y1="2" x2="16" y2="6"></line>
                    <line x1="8" y1="2" x2="8" y2="6"></line>
                    <line x1="3" y1="10" x2="21" y2="10"></line>
                </svg>
                <span>Posted: ${formatDate(job.posted_date)}</span>
            </div>
        `);
    }
    
    if (job.status) {
        const statusClass = job.status.toLowerCase() === 'open' ? '' : 'closed';
        metaItems.push(`
            <div class="job-meta-item">
                <span class="status-badge ${statusClass}">${job.status}</span>
            </div>
        `);
    }
    
    metaContainer.innerHTML = metaItems.join('');
}

// Render info grid
function renderInfoGrid(job) {
    const infoGrid = document.getElementById('infoGrid');
    const cards = [];
    
    if (job.salary_range) {
        cards.push(`
            <div class="info-card">
                <div class="info-card-label">Salary Range</div>
                <div class="info-card-value">${job.salary_range}</div>
            </div>
        `);
    }
    
    if (job.application_deadline) {
        cards.push(`
            <div class="info-card">
                <div class="info-card-label">Application Deadline</div>
                <div class="info-card-value">${formatDate(job.application_deadline)}</div>
            </div>
        `);
    }
    
    if (job.posted_date) {
        cards.push(`
            <div class="info-card">
                <div class="info-card-label">Posted Date</div>
                <div class="info-card-value">${formatDate(job.posted_date)}</div>
            </div>
        `);
    }
    
    if (cards.length > 0) {
        infoGrid.innerHTML = cards.join('');
        infoGrid.style.display = 'grid';
    } else {
        infoGrid.style.display = 'none';
    }
}

// Render job details
function renderJobDetails(job) {
    // Set title and company
    const jobTitle = document.getElementById('jobTitle');
    const companyName = document.getElementById('companyName');
    if (jobTitle) {
        jobTitle.textContent = job.job_title || 'Job Title Not Available';
    }
  
    
    // Set page title
    document.title = `${job.job_title || 'Job Details'} - ${job.company_name || 'Cleo'}`;
    
    // Render meta information
    renderJobMeta(job);
    
    // Render info grid
    renderInfoGrid(job);
    
    // Description
    const descriptionSection = document.getElementById('descriptionSection');
    const descriptionDiv = document.getElementById('jobDescription');
    if (descriptionSection && descriptionDiv) {
        if (job.job_description || job.description) {
            descriptionDiv.innerHTML = renderListData(job.job_description || job.description);
            descriptionSection.style.display = 'block';
        } else {
            descriptionSection.style.display = 'none';
        }
    }
    
    // Shift Information
    const shiftSection = document.getElementById('shiftSection');
    const shiftDiv = document.getElementById('jobShift');
    if (shiftSection && shiftDiv) {
        if (job.Shift || job.shift) {
            shiftDiv.innerHTML = `<p>${job.Shift || job.shift}</p>`;
            shiftSection.style.display = 'block';
        } else {
            shiftSection.style.display = 'none';
        }
    }
    
    // Required Experience
    const experienceSection = document.getElementById('experienceSection');
    const experienceDiv = document.getElementById('jobExperience');
    if (experienceSection && experienceDiv) {
        if (job.required_experience || job.RequiredExperience) {
            const expValue = job.required_experience || job.RequiredExperience;
            experienceDiv.innerHTML = `<p>${expValue} ${typeof expValue === 'number' ? 'years' : ''}</p>`;
            experienceSection.style.display = 'block';
        } else {
            experienceSection.style.display = 'none';
        }
    }
    
    // Starting Date
    const startDateSection = document.getElementById('startDateSection');
    const startDateDiv = document.getElementById('jobStartDate');
    if (startDateSection && startDateDiv) {
        if (job.Starting_Date || job.starting_date || job.start_date) {
            const startDate = job.Starting_Date || job.starting_date || job.start_date;
            startDateDiv.innerHTML = `<p>${formatDate(startDate)}</p>`;
            startDateSection.style.display = 'block';
        } else {
            startDateSection.style.display = 'none';
        }
    }
    
    // Hide all other sections
    const requirementsSection = document.getElementById('requirementsSection');
    if (requirementsSection) requirementsSection.style.display = 'none';
    
    const responsibilitiesSection = document.getElementById('responsibilitiesSection');
    if (responsibilitiesSection) responsibilitiesSection.style.display = 'none';
    
    const benefitsSection = document.getElementById('benefitsSection');
    if (benefitsSection) benefitsSection.style.display = 'none';
    
    const additionalInfoSection = document.getElementById('additionalInfoSection');
    if (additionalInfoSection) additionalInfoSection.style.display = 'none';
    
    // Update apply button with job ID
    const applyButton = document.getElementById('applyButton');
    if (applyButton) {
        applyButton.dataset.jobId = job.id;
    }
    
    // // Show QR code if available
    // const qrCodeSection = document.getElementById('qrCodeSection');
    // const qrCodeImg = document.getElementById('qrCodeImage');
    
    // if (qrCodeSection && qrCodeImg) {
    //     // Check for QR code in multiple possible fields
    //     const qrUrl = job.Company_QR || job.qr_code_url || job.qr_code_image || job.qr_image || job.qrCode || job.qr_code;
        
    //     if (qrUrl && qrUrl !== 'ljkhkjhk') { // Also check for dummy values
    //         qrCodeImg.src = qrUrl;
    //         qrCodeImg.alt = 'QR Code to apply for this position';
    //         qrCodeSection.style.display = 'block';
    //     } else {
    //         // Hide QR section if no valid QR code
    //         qrCodeSection.style.display = 'none';
    //     }
    // }
    
    // Show the content
    const loadingState = document.getElementById('loadingState');
    if (loadingState) {
        loadingState.style.display = 'none';
    }
    const jobDetailContent = document.getElementById('jobDetailContent');
    if (jobDetailContent) {
        jobDetailContent.style.display = 'block';
        jobDetailContent.classList.add('loaded');
    }
}

// Show error state
function showError(message) {
    document.getElementById('loadingState').style.display = 'none';
    const errorState = document.getElementById('errorState');
    errorState.style.display = 'flex';
    
    if (message) {
        errorState.querySelector('.error-description').textContent = message;
    }
}

// Fetch job details
async function fetchJobDetails(jobId) {
    try {
        // Try fetching directly from Xano first
        const response = await fetch(`${XANO_JOB_BY_ID_URL}/${jobId}`);
        
        if (!response.ok) {
            if (response.status === 404) {
                showError('The job you are looking for does not exist or has been removed.');
            } else {
                showError('An error occurred while fetching job details. Please try again later.');
            }
            return;
        }
        
        const job = await response.json();
        renderJobDetails(job);
        
    } catch (error) {
        console.error('Error fetching job details from Xano:', error);
        
        // Fallback to backend API
        try {
            const backendResponse = await fetch(`${XANO_JOB_BY_ID_URL}/${jobId}`);
            
            if (!backendResponse.ok) {
                if (backendResponse.status === 404) {
                    showError('The job you are looking for does not exist or has been removed.');
                } else {
                    showError('An error occurred while fetching job details. Please try again later.');
                }
                return;
            }
            
            const job = await backendResponse.json();
            renderJobDetails(job);
            
        } catch (backendError) {
            console.error('Backend fallback also failed:', backendError);
            showError('Unable to connect to the server. Please check your connection and try again.');
        }
    }
}

// Apply button functionality
function setupApplyButton() {
    const applyButton = document.getElementById('applyButton');
    applyButton.addEventListener('click', async (e) => {
        e.preventDefault();
        
        const jobId = applyButton.dataset.jobId;
        if (!jobId) {
            alert('Job ID not available');
            return;
        }
        
        // Disable button and show loading state
        applyButton.disabled = true;
        const originalText = applyButton.textContent;
        applyButton.textContent = 'Creating Session...';
        
        try {
            // Create session with job_id
            const response = await fetch(`${API_BASE_URL}/api/v1/sessions/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    job_id: jobId,
                    retrieval_method: 'hybrid',
                    language: 'en'
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const sessionData = await response.json();
            
            // Store session data in sessionStorage for retrieval on home page
            sessionStorage.setItem('welcomeMessage', sessionData.message || 'Welcome! Let\'s get started with your application.');
            
            // Redirect to home page with session started
            window.location.href = `/?session_id=${sessionData.session_id}&job_id=${jobId}`;
            
        } catch (error) {
            console.error('Error creating session:', error);
            alert('Failed to start application session. Please try again or go to the home page.');
            applyButton.disabled = false;
            applyButton.textContent = originalText;
        }
    });
}

// Share button functionality
function setupShareButton() {
    const shareButton = document.getElementById('shareButton');
    shareButton.addEventListener('click', () => {
        if (navigator.share) {
            navigator.share({
                title: document.getElementById('jobTitle').textContent,
                text: `Check out this job: ${document.getElementById('jobTitle').textContent}`,
                url: window.location.href
            }).catch(err => console.log('Error sharing:', err));
        } else {
            // Fallback: Copy to clipboard
            navigator.clipboard.writeText(window.location.href).then(() => {
                const originalText = shareButton.textContent;
                shareButton.textContent = 'Link Copied!';
                setTimeout(() => {
                    shareButton.textContent = originalText;
                }, 2000);
            });
        }
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    const jobId = getJobIdFromURL();
    
    if (!jobId) {
        showError('No job ID provided in the URL.');
        return;
    }
    
    fetchJobDetails(jobId);
    setupApplyButton();
    setupShareButton();
});
