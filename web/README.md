# Cleo Web UI

A modern web interface for the Cleo AI Job Application Assistant.

## Features

- **Landing Page**: Clean welcome screen with a "Start Conversation" button
- **Real-time Chat**: Interactive chat interface with the AI assistant
- **Session Management**: Create, track, and reset conversation sessions
- **Status Sidebar**: Live updates showing:
  - Current conversation stage
  - Progress through application stages (Engagement, Qualification, Application, Verification)
  - API connection status
  - Session ID
- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Sleek dark theme with smooth animations

## Getting Started

### Prerequisites

1. Make sure the Cleo backend API is running:
   ```bash
   # From the project root
   docker-compose up --build -d
   ```
   
   Or run directly with Python:
   ```bash
   python run_api.py
   ```

2. The API should be accessible at `http://localhost:8000`

### Running the Web UI

#### Option 1: Using Python's HTTP Server

```bash
# Navigate to the web directory
cd web

# Start a simple HTTP server (Python 3)
python -m http.server 8080
```

Then open your browser and navigate to: `http://localhost:8080`

#### Option 2: Using Node.js HTTP Server

```bash
# Install http-server globally (if not already installed)
npm install -g http-server

# Navigate to the web directory
cd web

# Start the server
http-server -p 8080
```

Then open your browser and navigate to: `http://localhost:8080`

#### Option 3: Open Directly in Browser

You can also open the `index.html` file directly in your browser, but this may cause CORS issues when connecting to the API. Using a local server (Options 1 or 2) is recommended.

## Usage

1. **Start a Session**:
   - Click the "Start Conversation" button on the landing page
   - A new session will be created and you'll be taken to the chat interface

2. **Chat with Cleo**:
   - Type your messages in the input field at the bottom
   - Press Enter or click the send button to send
   - Cleo will respond and guide you through the application process

3. **Monitor Progress**:
   - Check the left sidebar to see your current stage
   - Track completion of each application phase
   - View your session ID and API connection status

4. **Session Actions**:
   - **New Session**: Start completely fresh with a new session ID
   - **Reset Chat**: Clear the conversation while keeping the same session

## Configuration

To change the API URL, edit the `API_BASE_URL` constant in `app.js`:

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

You can also adjust the status update interval (default: 5 seconds):

```javascript
const STATUS_UPDATE_INTERVAL = 5000; // milliseconds
```

## File Structure

```
web/
├── index.html      # Main HTML structure
├── styles.css      # All styling and animations
├── app.js          # JavaScript functionality and API integration
└── README.md       # This file
```

## API Endpoints Used

- `GET /health` - Check API health status
- `POST /api/v1/session/create` - Create a new conversation session
- `POST /api/v1/chat` - Send a message and receive response
- `GET /api/v1/session/{session_id}/status` - Get current session status
- `POST /api/v1/session/{session_id}/reset` - Reset conversation memory

## Browser Compatibility

The web UI works best in modern browsers:
- Chrome/Edge (recommended)
- Firefox
- Safari
- Opera

## Troubleshooting

### API Connection Issues

If you see "Disconnected" status:
1. Verify the backend is running: `docker-compose ps` or check if the API process is active
2. Check the API URL is correct in `app.js`
3. Look for CORS errors in browser console

### Session Not Starting

1. Open browser developer console (F12) to check for errors
2. Verify the API returns a valid response at `http://localhost:8000/health`
3. Check network tab in developer tools for failed requests

### Messages Not Sending

1. Ensure your session is still active
2. Check the API logs for errors
3. Try creating a new session

## Development

To modify the UI:

1. **Styling**: Edit `styles.css` for visual changes
2. **Functionality**: Edit `app.js` for behavior changes
3. **Structure**: Edit `index.html` for layout changes

All changes will be reflected immediately upon page refresh (no build process required).

## Future Enhancements

Potential improvements:
- File upload support for resume/CV
- Download conversation transcript
- Multiple language support
- Voice input/output
- Dark/light theme toggle
- Session history and management
- Export application data

## License

This web UI is part of the Cleo project. Refer to the main project license.