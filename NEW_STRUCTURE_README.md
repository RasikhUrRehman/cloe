# Cleo RAG Chatbot - New Structure Guide

## 📁 Project Structure

```
cloe_chatbot/
├── chatbot/                    # Main chatbot package
│   ├── __init__.py
│   ├── core/                   # Core functionality
│   │   ├── __init__.py
│   │   ├── agent.py           # Main agent implementation
│   │   ├── retrievers.py      # Knowledge base retrieval
│   │   └── ingestion.py       # Document ingestion
│   ├── api/                    # FastAPI application
│   │   ├── __init__.py
│   │   └── app.py             # API endpoints
│   ├── prompts/                # Separated prompts
│   │   ├── __init__.py
│   │   └── prompts.py         # All prompts configuration
│   ├── state/                  # State management
│   │   ├── __init__.py
│   │   └── states.py          # Session states
│   └── utils/                  # Utility modules
│       ├── __init__.py
│       ├── config.py          # Configuration
│       ├── utils.py           # Helper functions
│       ├── verification.py    # Verification logic
│       ├── fit_score.py       # Scoring logic
│       └── report_generator.py # Report generation
├── main_new.py                 # CLI entry point
├── run_api.py                  # API server entry point
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose with API service
├── requirements.txt            # Python dependencies
└── [old files remain for reference]
```

## 🚀 Running the Application

### Option 1: CLI Mode (Interactive)

```bash
# Start interactive chat
python main_new.py

# Start a new session
python main_new.py new

# Resume an existing session
python main_new.py resume <session_id>

# Run API server from main
python main_new.py api
```

### Option 2: API Mode (FastAPI Server)

```bash
# Run the API server directly
python run_api.py

# Or using uvicorn with auto-reload
uvicorn chatbot.api.app:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Docker (Recommended for Production)

```bash
# Start all services (Milvus + Cleo API)
docker-compose up -d

# View logs
docker-compose logs -f cleo-api

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

## 🔌 API Endpoints

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. Health Check
```http
GET /health
GET /
```
**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-10-24T..."
}
```

#### 2. Create Session
```http
POST /api/v1/session/create
Content-Type: application/json

{
  "retrieval_method": "hybrid",
  "language": "en"
}
```
**Response:**
```json
{
  "session_id": "uuid-here",
  "message": "Session created successfully. You can now start chatting!",
  "current_stage": "engagement"
}
```

#### 3. Send Chat Message
```http
POST /api/v1/chat
Content-Type: application/json

{
  "session_id": "your-session-id",
  "message": "Hi, I want to apply for a job"
}
```
**Response:**
```json
{
  "session_id": "your-session-id",
  "response": "Hi there! I'm Cleo, your AI assistant...",
  "current_stage": "engagement",
  "timestamp": "2024-10-24T..."
}
```

#### 4. Get Session Status
```http
GET /api/v1/session/{session_id}/status
```
**Response:**
```json
{
  "session_id": "your-session-id",
  "current_stage": "qualification",
  "engagement_complete": true,
  "qualification_complete": false,
  "application_complete": false,
  "verification_complete": false
}
```

#### 5. Delete Session
```http
DELETE /api/v1/session/{session_id}
```

#### 6. Reset Session
```http
POST /api/v1/session/{session_id}/reset
```

## 📝 Using the API with curl

```bash
# Create a session
curl -X POST http://localhost:8000/api/v1/session/create \
  -H "Content-Type: application/json" \
  -d '{"retrieval_method": "hybrid", "language": "en"}'

# Send a message
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "message": "Hello, I want to apply for a job"
  }'

# Check session status
curl http://localhost:8000/api/v1/session/your-session-id/status
```

## 🐍 Using the API with Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Create a session
response = requests.post(
    f"{BASE_URL}/api/v1/session/create",
    json={"retrieval_method": "hybrid", "language": "en"}
)
session_data = response.json()
session_id = session_data["session_id"]
print(f"Session ID: {session_id}")

# Send a message
response = requests.post(
    f"{BASE_URL}/api/v1/chat",
    json={
        "session_id": session_id,
        "message": "Hi, I want to apply for a job"
    }
)
chat_response = response.json()
print(f"Cleo: {chat_response['response']}")

# Check status
response = requests.get(f"{BASE_URL}/api/v1/session/{session_id}/status")
status = response.json()
print(f"Current stage: {status['current_stage']}")
```

## 🎨 Prompts System

All prompts are now centralized in `chatbot/prompts/prompts.py`:

- **System Prompt**: Base instructions for Cleo's personality and behavior
- **Stage Prompts**: Specific instructions for each conversation stage:
  - Engagement
  - Qualification
  - Application
  - Verification

### Customizing Prompts

Edit `chatbot/prompts/prompts.py` to customize:

```python
from chatbot.prompts.prompts import CleoPrompts

# Get the system prompt
prompt = CleoPrompts.get_system_prompt(
    session_id="test",
    current_stage=ConversationStage.ENGAGEMENT,
    language="en"
)

# Get stage-specific prompt only
stage_prompt = CleoPrompts.get_stage_prompt(ConversationStage.QUALIFICATION)
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# OpenAI Configuration
OPENAI_API_KEY=your-api-key-here
OPENAI_CHAT_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_TEMPERATURE=0.7

# Milvus Configuration
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION_NAME=cleo_knowledge_base

# Application Settings
LOG_LEVEL=INFO
APP_NAME=Cleo RAG Agent
APP_VERSION=1.0.0
```

## 📦 Dependencies

Main dependencies include:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `langchain` - LLM orchestration
- `langchain-openai` - OpenAI integration
- `pymilvus` - Vector database client
- `pydantic` - Data validation

Install all dependencies:
```bash
pip install -r requirements.txt
```

## 🧪 Testing the API

### Using the Swagger UI

Navigate to `http://localhost:8000/docs` to access the interactive API documentation.

### Complete Conversation Flow

1. Create a session
2. Send initial greeting message
3. Provide consent to proceed
4. Answer qualification questions
5. Provide application details
6. Complete verification
7. Check final status

## 🌐 Docker Deployment

### Build and Run

```bash
# Build the image
docker build -t cleo-chatbot .

# Run API mode (default)
docker run -p 8000:8000 --env-file .env cleo-chatbot

# Run CLI mode
docker run -it --env-file .env cleo-chatbot python main_new.py
```

### Docker Compose (Full Stack)

```bash
# Start everything (Milvus + API)
docker-compose up -d

# View API logs
docker-compose logs -f cleo-api

# Scale the API service
docker-compose up -d --scale cleo-api=3
```

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Logs
```bash
# View real-time logs
docker-compose logs -f cleo-api

# View last 100 lines
docker-compose logs --tail=100 cleo-api
```

## 🔄 Migration from Old Structure

Old files remain in the root directory for reference. The new structure is fully backward compatible through imports. You can gradually migrate scripts by updating imports:

```python
# Old import
from agent import CleoRAGAgent

# New import
from chatbot.core.agent import CleoRAGAgent
```

## 🛠️ Development

### Running in Development Mode

```bash
# API with auto-reload
uvicorn chatbot.api.app:app --reload

# CLI interactive mode
python main_new.py
```

### Adding New Features

1. **New prompts**: Edit `chatbot/prompts/prompts.py`
2. **New endpoints**: Add to `chatbot/api/app.py`
3. **Core logic**: Modify `chatbot/core/agent.py`
4. **State management**: Update `chatbot/state/states.py`

## 📝 Notes

- Session data is persisted to CSV files in `storage/`
- Logs are written to `logs/`
- Reports are generated in `reports/`
- Both CLI and API modes share the same core logic
- The API service is production-ready with health checks and proper error handling

## 🎯 Next Steps

1. Set up your OpenAI API key in `.env`
2. Start Milvus: `docker-compose up -d etcd minio milvus`
3. Ingest knowledge base documents
4. Start the API: `python run_api.py`
5. Test with curl or the Swagger UI at `http://localhost:8000/docs`

For questions or issues, refer to the original documentation files in the root directory.
