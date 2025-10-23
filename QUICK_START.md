# 🚀 Quick Start Guide - New Structure

## Prerequisites

1. Python 3.11+
2. OpenAI API key
3. Docker & Docker Compose (for Milvus)

## Step 1: Environment Setup

Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```env
OPENAI_API_KEY=your-actual-api-key-here
```

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 3: Start Milvus (Vector Database)

```bash
# Start Milvus services
docker-compose up -d etcd minio milvus

# Wait for services to be ready (about 30 seconds)
docker-compose ps
```

## Step 4: Choose Your Mode

### Option A: CLI Mode (Interactive Chat)

```bash
python main.py
```

Then type `new` to start a session and begin chatting!

### Option B: API Mode (REST API Server)

```bash
python run_api.py
```

API will be available at: http://localhost:8000

View docs at: http://localhost:8000/docs

### Option C: Full Docker Mode

```bash
# Start everything (Milvus + Cleo API)
docker-compose up -d

# Check logs
docker-compose logs -f cleo-api
```

## Step 5: Test the API

### Using curl:
```bash
# Health check
curl http://localhost:8000/health

# Create session
curl -X POST http://localhost:8000/api/v1/session/create \
  -H "Content-Type: application/json" \
  -d '{"retrieval_method": "hybrid", "language": "en"}'

# Chat (replace SESSION_ID with actual ID)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "SESSION_ID",
    "message": "Hi, I want to apply for a job"
  }'
```

### Using Python client:
```bash
# Interactive mode
python api_client_example.py

# Demo mode
python api_client_example.py demo
```

## 📝 Customizing Prompts

Edit `chatbot/prompts/prompts.py` to customize:
- System prompt (personality and behavior)
- Stage-specific prompts (engagement, qualification, application, verification)
- Language-specific messages

## 🔍 Troubleshooting

### Import Errors
Make sure you're running from the project root directory.

### Milvus Connection Errors
Check if Milvus is running:
```bash
docker-compose ps
```

Restart if needed:
```bash
docker-compose restart milvus
```

### OpenAI API Errors
Verify your API key in `.env` file.

## 📚 Next Steps

1. **Ingest Documents**: Add your knowledge base documents
   ```bash
   python scripts/setup_knowledge_base.py
   ```

2. **Customize Prompts**: Edit `chatbot/prompts/prompts.py`

3. **Explore API**: Visit http://localhost:8000/docs

4. **Read Full Docs**: Check `NEW_STRUCTURE_README.md`

## 🎯 Quick Commands Reference

```bash
# CLI interactive mode
python main.py

# API server
python run_api.py

# Docker (full stack)
docker-compose up -d

# View logs
docker-compose logs -f cleo-api

# Stop everything
docker-compose down

# Test API
curl http://localhost:8000/health
```

## ✅ You're Ready!

Choose your preferred mode and start using Cleo!
