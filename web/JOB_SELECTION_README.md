# Web Interface - Job Selection Feature

## Overview

The web interface has been updated to support job-specific sessions. Users can now select a specific job position before starting their conversation with Cleo.

## New Features

### 1. Job Selection on Landing Page

- **Job Dropdown**: Displays all available jobs from the Xano API
- **Auto-load**: Jobs are automatically loaded when the page loads
- **Refresh Button**: Users can manually refresh the job list
- **Job Preview**: Shows basic job details when a job is selected
- **Optional Selection**: Users can proceed without selecting a job (general application)

### 2. Job Information Display

- **Sidebar Info**: Selected job is displayed in the chat interface sidebar
- **Welcome Message**: Includes job title and company in the initial greeting
- **Context Awareness**: Agent knows which job the applicant is applying for

## How to Use

### For Users:

1. **Open the web interface** in your browser (typically `http://localhost:8000` or open `index.html`)

2. **Select a Job** (optional):
   - Wait for jobs to load in the dropdown
   - Choose a job from the list
   - See job preview below the dropdown
   - Or leave it as "General Application"

3. **Start Conversation**:
   - Click "Start Conversation"
   - Chat interface opens with job information (if selected)
   - Cleo knows which position you're applying for

4. **Chat Normally**:
   - Ask questions about the job
   - Proceed through application stages
   - Cleo will assess your fit for the specific position

### Visual Flow:

```
Landing Page
    ↓
[Job Dropdown Loads]
    ↓
User selects job (optional)
    ↓
[Job Preview Shows]
    ↓
User clicks "Start Conversation"
    ↓
Chat Interface Opens
    ↓
Job info shown in sidebar
    ↓
Welcome message includes job details
```

## Technical Changes

### Files Modified:

1. **`index.html`**:
   - Added job selection dropdown
   - Added job info preview section
   - Added job info display in sidebar
   - Added loading indicator

2. **`app.js`**:
   - Added Xano API configuration
   - Added job state variables
   - Added `fetchJobs()` function
   - Added `loadJobs()` function
   - Updated `createSession()` to include `job_id`
   - Added job selection event handlers
   - Updated welcome message to include job info

3. **`styles.css`**:
   - Added `.job-selection-container` styles
   - Added `.job-select` dropdown styles
   - Added `.job-preview` styles
   - Added `.job-info-display` sidebar styles
   - Added loading spinner animation

### New UI Elements:

#### Landing Page:
- Job selection dropdown with all available positions
- Refresh button to reload jobs
- Job preview card showing selected job details
- Loading indicator while fetching jobs

#### Chat Sidebar:
- "Job Position" section showing:
  - Job Title
  - Company Name
  - Location

## Configuration

### API Endpoints:

The web interface uses two APIs:

1. **Chatbot API** (default: `http://localhost:8000`)
   - Session creation: `POST /api/v1/session/create`
   - Chat: `POST /api/v1/chat`
   - Status: `GET /api/v1/session/{id}/status`

2. **Xano Jobs API**
   - URL: `https://xoho-w3ng-km3o.n7e.xano.io/api:L-QNLSmb/get_all_job_`
   - Returns array of job objects

### Customization:

To change the API URLs, edit `app.js`:

```javascript
const API_BASE_URL = 'http://localhost:8000';
const XANO_API_URL = 'https://your-api-url-here';
```

## Example User Experience

### Scenario 1: With Job Selection

1. User opens web interface
2. Sees dropdown with jobs:
   - "Software Engineer - Tech Corp (San Francisco)"
   - "Data Analyst - StartupXYZ (Remote)"
   - etc.
3. Selects "Software Engineer - Tech Corp"
4. Sees preview:
   ```
   Software Engineer
   Company: Tech Corp
   Location: San Francisco
   Type: Full-time
   ```
5. Clicks "Start Conversation"
6. Welcome message: "Hi! I'm Cleo... You're applying for: Software Engineer at Tech Corp"
7. Cleo asks targeted questions based on this specific role

### Scenario 2: General Application

1. User opens web interface
2. Leaves dropdown on "General Application (No specific job)"
3. Clicks "Start Conversation"
4. Standard welcome message
5. Cleo guides through general application process

## Troubleshooting

### Jobs not loading?

- Check browser console for errors
- Verify Xano API is accessible
- Check network tab in browser dev tools
- Jobs list will still show "General Application" option

### Job info not showing in chat?

- Check that job_id is being sent to API
- Verify backend is processing job_id correctly
- Check session creation response

### Refresh button not working?

- Click the refresh button (circular arrow icon)
- Wait for loading indicator
- Jobs should reload from API

## Mobile Responsiveness

The job selection interface is responsive and works on mobile devices:
- Dropdown adjusts to screen size
- Touch-friendly buttons
- Readable job previews

## Future Enhancements

Potential improvements:
- [ ] Search/filter jobs
- [ ] Job details modal
- [ ] Save job preferences
- [ ] Multi-job comparison
- [ ] Job recommendations based on profile
- [ ] Recent jobs history

## Testing

### Manual Testing:

1. **Load Test**:
   ```bash
   # Open web interface
   # Check if jobs load automatically
   # Try refresh button
   ```

2. **Selection Test**:
   ```bash
   # Select different jobs
   # Check preview updates
   # Verify job info in sidebar after starting chat
   ```

3. **Integration Test**:
   ```bash
   # Select a job
   # Start conversation
   # Ask about the job
   # Verify Cleo knows job details
   ```

### Browser Console Commands:

```javascript
// Check loaded jobs
console.log(availableJobs);

// Check selected job
console.log(selectedJobDetails);

// Check session ID
console.log(sessionId);
```

## Support

If you encounter issues:
1. Check browser console for errors
2. Verify both APIs are running
3. Check network requests in browser dev tools
4. Ensure CORS is properly configured on backend
