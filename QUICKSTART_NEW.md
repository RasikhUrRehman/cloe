# 🚀 Cleo Chatbot - Quick Start Guide

## ✅ What's Been Done

### 1. **Organized Project Structure**
Created a new `chatbot/` folder with organized subfolders:
- `chatbot/core/` - Core agent and retrieval logic
- `chatbot/api/` - FastAPI application
- `chatbot/prompts/` - Centralized prompt configuration
- `chatbot/state/` - State management
- `chatbot/utils/` - Utility functions and configuration

### 2. **Separated Prompts**
All prompts are now in `chatbot/prompts/prompts.py`:
- **System Prompt** - Sets Cleo's personality and tone
- **Stage-Specific Prompts** - Detailed instructions for each conversation stage:
  - Engagement (building trust, getting consent)
  - Qualification (checking eligibility)
  - Application (collecting details)
  - Verification (document verification)

### 3. **FastAPI Integration**
Created a complete REST API (`chatbot/api/app.py`) with endpoints:
- `POST /api/v1/session/create` - Create new chat session
- `POST /api/v1/chat` - Send messages
- `GET /api/v1/session/{id}/status` - Get session status
- `DELETE /api/v1/session/{id}` - Delete session
- `POST /api/v1/session/{id}/reset` - Reset conversation
- `GET /health` - Health check

### 4. **Docker Support**
Updated Docker configuration:
- Dockerfile runs FastAPI by default
- docker-compose.yml includes new `cleo-api` service
- Full stack deployment with Milvus + API

### 5. **Multiple Entry Points**
- `main_new.py` - CLI interactive mode
- `run_api.py` - FastAPI server mode
- Both can run locally or in Docker

## 🏃 Quick Start

### Option A: Run API Server (Recommended)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment variables
# Create .env file with your OPENAI_API_KEY

# 3. Start the API server
python run_api.py

# 4. Test it
curl http://localhost:8000/health
```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### Option B: Run CLI Mode

```bash
# Interactive mode
python main_new.py

# Start a new session directly
python main_new.py new

# Resume a session
python main_new.py resume <session_id>
```

### Option C: Run with Docker

```bash
# Start everything (Milvus + Cleo API)
docker-compose up -d

# View logs
docker-compose logs -f cleo-api

# Stop
docker-compose down
```

## 📝 Using the API

### Python Example

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Create a session
response = requests.post(
    f"{BASE_URL}/api/v1/session/create",
    json={"retrieval_method": "hybrid", "language": "en"}
)
session_id = response.json()["session_id"]

# 2. Send a message
response = requests.post(
    f"{BASE_URL}/api/v1/chat",
    json={
        "session_id": session_id,
        "message": "Hi, I want to apply for a job"
    }
)
print(response.json()["response"])

# 3. Check status
response = requests.get(f"{BASE_URL}/api/v1/session/{session_id}/status")
print(response.json())
```

### Using the Example Client

```bash
# Interactive mode
python api_client_example.py

# Run demo conversation
python api_client_example.py demo
```

### cURL Examples

```bash
# Create session
curl -X POST http://localhost:8000/api/v1/session/create \
  -H "Content-Type: application/json" \
  -d '{"retrieval_method": "hybrid", "language": "en"}'

# Send message
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "YOUR_SESSION_ID", "message": "Hello!"}'

# Check status
curl http://localhost:8000/api/v1/session/YOUR_SESSION_ID/status
```

## 🎨 Customizing Prompts

Edit `chatbot/prompts/prompts.py` to customize Cleo's behavior:

```python
# System prompt - Overall personality and tone
SYSTEM_PROMPT = """You are Cleo, an AI assistant..."""

# Stage prompts - Specific instructions per stage
STAGE_PROMPTS = {
    ConversationStage.ENGAGEMENT: """...""",
    ConversationStage.QUALIFICATION: """...""",
    # etc.
}
```

## 📁 File Organization

### Old Structure (Still Available)
```
- agent.py
- states.py
- utils.py
- config.py
- etc.
```

### New Structure (Organized)
```
chatbot/
├── core/
│   ├── agent.py          # Refactored agent
│   ├── retrievers.py     # From root
│   └── ingestion.py      # From root
├── api/
│   └── app.py           # New FastAPI app
├── prompts/
│   └── prompts.py       # New prompt configuration
├── state/
│   └── states.py        # From root
└── utils/
    ├── config.py        # From root
    ├── utils.py         # From root
    ├── verification.py  # From root
    ├── fit_score.py    # From root
    └── report_generator.py
```

## 🔧 Configuration

Create a `.env` file:

```env
OPENAI_API_KEY=your-key-here
OPENAI_CHAT_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_TEMPERATURE=0.7
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

## 🧪 Testing

### Test API Endpoints

```bash
# 1. Start the API
python run_api.py

# 2. Open browser to
http://localhost:8000/docs

# 3. Or use the test client
python api_client_example.py
```

### Test CLI Mode

```bash
python main_new.py
```

## 📊 API Conversation Flow

1. **Create Session** → Get `session_id`
2. **Send Messages** → Get responses + current stage
3. **Check Status** → See progress through stages
4. **Complete Application** → All stages marked complete
5. **Delete Session** → Clean up when done

## 🔄 Migration Notes

- Old files remain in root for reference
- New code uses `chatbot.` prefix for imports
- Both structures work simultaneously
- Gradually migrate scripts to new imports

## 📚 Documentation

- `NEW_STRUCTURE_README.md` - Comprehensive guide
- `README.md` - Original documentation
- `http://localhost:8000/docs` - Interactive API docs

## 🎯 Next Steps

1. **Set up environment**
   ```bash
   pip install -r requirements.txt
   cp .env.example .env  # Add your API key
   ```

2. **Start Milvus** (for knowledge base)
   ```bash
   docker-compose up -d etcd minio milvus
   ```

3. **Ingest documents** (optional)
   ```bash
   python setup_knowledge_base.py
   ```

4. **Run the API**
   ```bash
   python run_api.py
   ```

5. **Test it**
   ```bash
   python api_client_example.py demo
   ```

## ✨ Features

- ✅ Organized modular structure
- ✅ Separated prompts for easy customization
- ✅ FastAPI REST API with full documentation
- ✅ CLI and API modes
- ✅ Docker support
- ✅ Session management
- ✅ Stage-based conversation flow
- ✅ Health checks and monitoring
- ✅ Example client code
- ✅ Backward compatible with old structure

## 🆘 Troubleshooting

**API won't start?**
- Check if port 8000 is available
- Ensure all dependencies are installed
- Check `.env` file has valid OpenAI API key

**Can't connect to Milvus?**
- Start Milvus: `docker-compose up -d milvus`
- Check connection: `MILVUS_HOST=localhost MILVUS_PORT=19530`

**Import errors?**
- Make sure you're in the project root
- Install all requirements: `pip install -r requirements.txt`

## 📞 Support

For detailed documentation, see:
- `NEW_STRUCTURE_README.md` - Complete API and structure guide
- `README.md` - Original project documentation
- `ARCHITECTURE.md` - System architecture
- `GETTING_STARTED.md` - Setup instructions

---

**You're all set! 🎉**

Start with: `python run_api.py` then visit `http://localhost:8000/docs`
