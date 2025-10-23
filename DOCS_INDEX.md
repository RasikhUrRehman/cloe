# 📖 Documentation Index

Welcome to the Cleo RAG Chatbot documentation! This index will help you find what you need quickly.

## 🚀 Getting Started

**Start here if you're new:**

1. **[QUICK_START.md](QUICK_START.md)** - ⭐ Get up and running in 5 minutes
2. **[REORGANIZATION_SUMMARY.md](REORGANIZATION_SUMMARY.md)** - Overview of the new structure
3. **[.env.example](.env.example)** - Environment configuration template

## 📚 Detailed Documentation

### Architecture & Design

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design patterns
- **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - High-level project overview
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes

### New Structure (After Reorganization)

- **[NEW_STRUCTURE_README.md](NEW_STRUCTURE_README.md)** - 📘 Complete guide to new structure
  - API endpoints documentation
  - Usage examples (Python, curl)
  - Docker deployment guide
  - Prompts customization
  - Migration guide

### Original Documentation

- **[README.md](README.md)** - Original project README
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Original getting started guide

## 🗂️ Code Organization

### Main Entry Points

| File | Purpose | Usage |
|------|---------|-------|
| `main.py` | CLI interface | `python main.py` |
| `run_api.py` | API server | `python run_api.py` |
| `api_client_example.py` | Example API client | `python api_client_example.py` |

### Package Structure

```
chatbot/
├── core/          # Core agent and retrieval logic
│   └── agent.py   # Main CleoRAGAgent class
├── api/           # FastAPI REST API
│   └── app.py     # API endpoints
├── prompts/       # ⭐ PROMPTS (centralized)
│   └── prompts.py # All prompts configuration
├── state/         # State management
│   └── states.py  # Session state classes
└── utils/         # Utilities
    └── config.py  # Configuration
```

## 💬 Prompts Documentation

**Location:** `chatbot/prompts/prompts.py`

This file contains ALL prompts for the chatbot:

- **System Prompt** - Base personality and behavior
- **Engagement Stage Prompt** - Building trust and getting consent
- **Qualification Stage Prompt** - Verifying basic requirements
- **Application Stage Prompt** - Collecting detailed information
- **Verification Stage Prompt** - Identity verification

**To customize:** Simply edit `chatbot/prompts/prompts.py`

## 🌐 API Documentation

### Quick Reference

- **Base URL:** `http://localhost:8000`
- **Interactive Docs:** `http://localhost:8000/docs` (Swagger UI)
- **Health Check:** `GET /health`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/session/create` | Create new session |
| POST | `/api/v1/chat` | Send message |
| GET | `/api/v1/session/{id}/status` | Get session status |
| DELETE | `/api/v1/session/{id}` | Delete session |
| POST | `/api/v1/session/{id}/reset` | Reset session |

**Full API docs:** See [NEW_STRUCTURE_README.md](NEW_STRUCTURE_README.md#-api-endpoints)

## 🐳 Docker Documentation

### Quick Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f cleo-api

# Stop services
docker-compose down
```

**Full Docker guide:** See [NEW_STRUCTURE_README.md](NEW_STRUCTURE_README.md#-docker-deployment)

## 📁 Additional Resources

### Scripts

See **[scripts/README.md](scripts/README.md)** for utility scripts:
- Setup scripts
- Test scripts
- Demo scripts

### Old Structure

See **[old_structure/README.md](old_structure/README.md)** for information about the old file structure and migration notes.

## 🔧 Configuration

**Environment Variables:** Edit `.env` file

Key settings:
- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `OPENAI_CHAT_MODEL` - Model to use (default: gpt-4-turbo-preview)
- `MILVUS_HOST` - Milvus host (default: localhost)
- `MILVUS_PORT` - Milvus port (default: 19530)

**Full config reference:** See `chatbot/utils/config.py`

## 🎯 Common Tasks

### Task: Run the chatbot

**CLI Mode:**
```bash
python main.py
```

**API Mode:**
```bash
python run_api.py
# Then visit http://localhost:8000/docs
```

### Task: Customize prompts

1. Open `chatbot/prompts/prompts.py`
2. Edit the prompt you want to change
3. Save the file
4. Restart the application

### Task: Add API endpoint

1. Open `chatbot/api/app.py`
2. Add your endpoint function
3. Test at `http://localhost:8000/docs`

### Task: Deploy with Docker

```bash
# Build and start
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f cleo-api
```

## 🆘 Troubleshooting

### Import errors

Make sure you're in the project root directory and run:
```bash
python -c "from chatbot.core.agent import CleoRAGAgent; print('✓ OK')"
```

### API not starting

Check if port 8000 is available:
```bash
# Windows
netstat -ano | findstr :8000

# Then if needed, change port in run_api.py
```

### Milvus connection errors

Ensure Milvus is running:
```bash
docker-compose ps
docker-compose restart milvus
```

## 📞 Need Help?

1. Check the relevant documentation file above
2. Look at the code examples in `api_client_example.py`
3. Explore the interactive API docs at `http://localhost:8000/docs`

## 🎉 Quick Links

- [🚀 Quick Start](QUICK_START.md)
- [📘 Full API Guide](NEW_STRUCTURE_README.md)
- [💬 Prompts File](chatbot/prompts/prompts.py)
- [🌐 API Code](chatbot/api/app.py)
- [⚙️ Agent Code](chatbot/core/agent.py)

---

**Last Updated:** October 24, 2025

**Project Status:** ✅ Reorganized and Production Ready
