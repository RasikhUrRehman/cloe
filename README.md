# Cleo RAG Agent 🤖

A production-ready Conversational AI Agent for job application processing, built with LangChain, OpenAI, and Milvus vector database.

## 📋 Overview

Cleo is an intelligent RAG (Retrieval-Augmented Generation) agent that:
- Converses naturally with job applicants through four structured stages
- Dynamically retrieves information from a knowledge base when needed
- Maintains conversation state with resume capability
- Calculates fit scores based on qualification, experience, and verification
- Generates comprehensive eligibility reports (JSON & PDF)

## 🏗️ Architecture

### Core Components

1. **Vector Database (Milvus)**
   - Stores document embeddings with metadata
   - Supports semantic, similarity, and hybrid search
   - Runs via Docker Compose with etcd and MinIO

2. **Document Ingestion Pipeline**
   - Extracts text from PDFs using PyMuPDF
   - Chunks text (512 chars, 20% overlap) using LangChain
   - Generates embeddings with OpenAI `text-embedding-3-large`

3. **Agentic Framework**
   - Built with LangChain's agent framework
   - Reasons about when to query knowledge base vs. respond directly
   - Uses tools for retrieval and state management

4. **Conversation State Management**
   - Four stages: Engagement → Qualification → Application → Verification
   - CSV-based persistence (easily replaced with database)
   - Session resume capability

5. **Fit Score Calculation**
   - Weighted composite: Qualification (30%) + Experience (40%) + Verification (30%)
   - Internal metric (0-100) for employer dashboard

6. **Report Generation**
   - Structured JSON reports
   - Professional PDF reports with ReportLab
   - Optional fit score inclusion

## 📁 Project Structure

```
cloe_chatbot/
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── .dockerignore             # Docker ignore rules
├── requirements.txt          # Python dependencies
├── Dockerfile                # Application container
├── docker-compose.yml        # Milvus stack (etcd, MinIO, Milvus)
│
├── config.py                 # Configuration management
├── utils.py                  # Logging and utilities
│
├── ingestion.py              # Document ingestion & embedding
├── retrievers.py             # Retrieval methods (semantic/similarity/hybrid)
├── states.py                 # Conversation state models & persistence
├── fit_score.py              # Fit score calculation
├── agent.py                  # Main RAG agent with LangChain
├── report_generator.py       # JSON & PDF report generation
│
├── main.py                   # Application entry point
├── demo_conversation.py      # End-to-end demo script
│
├── data/                     # Document storage
│   ├── raw/                  # Original PDFs
│   └── processed/            # Processed data
├── storage/                  # CSV files for state persistence
├── uploads/                  # User uploaded documents
├── reports/                  # Generated reports
└── logs/                     # Application logs
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   cd cloe_chatbot
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

3. **Start Milvus stack** (etcd, MinIO, Milvus)
   ```powershell
   docker-compose up -d
   ```
   
   Verify services are running:
   ```powershell
   docker-compose ps
   ```

4. **Install Python dependencies**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

5. **Initialize directories**
   ```powershell
   python -c "from chatbot.utils.config import ensure_directories; ensure_directories()"
   ```

### First Run

1. **Populate knowledge base** (optional but recommended)
   
   Place PDF documents in `data/raw/` directory, then:
   ```powershell
   python ingestion.py
   ```
   
   Or programmatically:
   ```python
   from ingestion import DocumentIngestion
   
   ingestion = DocumentIngestion()
   ingestion.create_collection()
   ingestion.ingest_document(
       pdf_path="data/raw/company_handbook.pdf",
       document_name="company_handbook",
       job_type="warehouse",
       section="requirements"
   )
   ```

2. **Run the demo**
   ```powershell
   python demo_conversation.py
   ```

3. **Run interactive mode**
   ```powershell
   python main.py
   ```

## 💬 Usage

### Interactive Mode

```powershell
python main.py
```

Commands:
- `new` - Start a new session
- `resume <session_id>` - Resume existing session
- `summary` - Show current session summary
- `report` - Generate eligibility report
- `quit` - Exit

### Programmatic Usage

```python
from agent import CleoRAGAgent
from retrievers import RetrievalMethod

# Create agent
agent = CleoRAGAgent(retrieval_method=RetrievalMethod.HYBRID)

# Chat
response = agent.process_message("Hi, I want to apply for a job")
print(response)

# Get summary
summary = agent.get_conversation_summary()
print(summary)

# Generate report
from report_generator import ReportGenerator
generator = ReportGenerator()
result = generator.generate_report(
    session_id=agent.session_state.session_id,
    include_fit_score=True
)
```

## 🔧 Configuration

Key settings in `.env`:

### OpenAI
```
OPENAI_API_KEY=your_key
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_CHAT_MODEL=gpt-4-turbo-preview
OPENAI_TEMPERATURE=0.7
```

### Milvus
```
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION_NAME=cleo_knowledge_base
```

### Embedding
```
EMBEDDING_DIMENSION=3072
CHUNK_SIZE=512
CHUNK_OVERLAP=102
```

### Fit Score Weights
```
QUALIFICATION_WEIGHT=0.30
EXPERIENCE_WEIGHT=0.40
VERIFICATION_WEIGHT=0.30
```

### Retrieval
```
DEFAULT_RETRIEVAL_METHOD=hybrid
TOP_K_RESULTS=5
SIMILARITY_THRESHOLD=0.7
```

## 🎯 Conversation Flow

### 1. Engagement Stage
- Greets applicant
- Explains the process
- Gets consent
- Captures company_id and job_id

**Collected Data:**
- `session_id`, `start_time`, `consent_given`, `company_id`, `job_id`, `language`

### 2. Qualification Stage
- Confirms age eligibility
- Verifies work authorization
- Asks about shift preferences
- Confirms availability
- Checks transportation
- Determines hours preference

**Collected Data:**
- `age_confirmed`, `work_authorization`, `shift_preference`, `availability_start`, `transportation`, `hours_preference`, `qualification_status`

**Exit Condition:** If not qualified, politely ends process

### 3. Application Stage
- Collects personal information
- Gathers work history
- Documents skills and experience
- Gets reference information

**Collected Data:**
- `full_name`, `phone_number`, `email`, `address`, `previous_employer`, `job_title`, `years_experience`, `skills`, `references`, `communication_preference`

### 4. Verification Stage
- Requests ID upload
- Performs verification (mock or API)
- Confirms verification status

**Collected Data:**
- `id_uploaded`, `id_type`, `verification_source`, `verification_status`, `timestamp_verified`

## 📊 Fit Score Calculation

**Formula:**
```
fit_score = (qualification_score × 0.30) + 
            (experience_score × 0.40) + 
            (verification_score × 0.30)
```

**Qualification Score (0-100):**
- Age confirmed: 20 pts
- Work authorization: 25 pts
- Shift preference: 15 pts
- Availability: 20 pts
- Transportation: 10 pts
- Hours preference: 10 pts

**Experience Score (0-100):**
- Years of experience: 0-40 pts (scaled)
- Previous employer: 15 pts
- Job title relevance: 15 pts
- Skills: 0-20 pts (4 pts per skill, max 5)
- References: 10 pts

**Verification Score (0-100):**
- ID uploaded: 40 pts
- Verification verified: 60 pts
- Verification pending: 30 pts

**Rating Scale:**
- 85-100: Excellent
- 70-84: Good
- 55-69: Fair
- 40-54: Below Average
- 0-39: Poor

## 🔍 Retrieval Methods

### 1. Semantic Search
Pure vector similarity using cosine distance
```python
retriever.retrieve(query, method=RetrievalMethod.SEMANTIC, top_k=5)
```

### 2. Similarity Search
Vector search with threshold filtering
```python
retriever.retrieve(query, method=RetrievalMethod.SIMILARITY, threshold=0.7)
```

### 3. Hybrid Search (Recommended)
Combines semantic similarity (60%) with keyword matching (40%)
```python
retriever.retrieve(query, method=RetrievalMethod.HYBRID, top_k=5)
```

## 📄 Report Generation

### JSON Report
Structured data with all application information:
```json
{
  "report_metadata": {...},
  "applicant_information": {...},
  "qualification_status": {...},
  "application_details": {...},
  "verification_status": {...},
  "eligibility_summary": {...},
  "fit_score": {...}
}
```

### PDF Report
Professional formatted report with:
- Applicant information
- Qualification status table
- Application details
- Verification status
- Eligibility summary
- Fit score analysis (if enabled)

## 🐳 Docker Deployment

### Local Development
```powershell
# Start Milvus stack only
docker-compose up -d

# Run application locally
python main.py
```

### Full Containerized Deployment
```powershell
# Build application container
docker build -t cleo-agent .

# Run application
docker run -it --network cleo_network `
  --env-file .env `
  -v ${PWD}/data:/app/data `
  -v ${PWD}/storage:/app/storage `
  -v ${PWD}/reports:/app/reports `
  cleo-agent
```

## 🧪 Testing

### Test Document Ingestion
```powershell
python ingestion.py
```

### Test Retrievers
```powershell
python retrievers.py
```

### Test State Management
```powershell
python states.py
```

### Test Fit Score
```powershell
python fit_score.py
```

### Test Report Generation
```powershell
python report_generator.py
```

### Run Complete Demo
```powershell
python demo_conversation.py
```

## 🌐 Multilingual Support

Basic language detection included. To extend:

1. Update `utils.detect_language()` with better detection
2. Add language-specific prompts in `agent.py`
3. Update system prompts based on detected language

Currently supported:
- English (en) - default
- Spanish (es) - basic detection

## 📈 Analytics & Monitoring

Logs are stored in `logs/` directory:
- `cleo_YYYY-MM-DD.log` - Daily rotating logs
- Retention: 30 days

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

To change log level:
```
LOG_LEVEL=DEBUG
```

## 🔐 Security Considerations

1. **Environment Variables:** Never commit `.env` file
2. **API Keys:** Use secure key management in production
3. **User Data:** Implement encryption for sensitive data
4. **Verification:** Use real verification API in production
5. **Access Control:** Add authentication for dashboard access

## 🚧 Production Readiness Checklist

- [ ] Replace CSV storage with proper database (PostgreSQL, MongoDB)
- [ ] Implement real ID verification API
- [ ] Add authentication and authorization
- [ ] Set up SSL/TLS for API endpoints
- [ ] Configure production-grade logging (e.g., ELK stack)
- [ ] Implement rate limiting
- [ ] Add comprehensive error handling
- [ ] Set up monitoring and alerting
- [ ] Implement data backup strategy
- [ ] Add unit and integration tests
- [ ] Configure CI/CD pipeline
- [ ] Set up load balancing for scale
- [ ] Implement caching strategy (Redis)
- [ ] Add data retention policies
- [ ] Configure CORS properly
- [ ] Implement webhook notifications

## 🛠️ Troubleshooting

### Milvus Connection Error
```
Error: Failed to connect to Milvus
```
**Solution:** Ensure Milvus is running:
```powershell
docker-compose ps
docker-compose up -d
```

### OpenAI API Error
```
Error: Incorrect API key provided
```
**Solution:** Check `.env` file has valid `OPENAI_API_KEY`

### Import Errors
```
Import "pymilvus" could not be resolved
```
**Solution:** Activate virtual environment and install dependencies:
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### PDF Generation Error
```
Error: No module named 'reportlab'
```
**Solution:** Install reportlab:
```powershell
pip install reportlab
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **LangChain** - Agent framework
- **OpenAI** - LLM and embeddings
- **Milvus** - Vector database
- **PyMuPDF** - PDF processing
- **ReportLab** - PDF generation

## 📞 Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Contact: [Your Contact Info]

## 🗺️ Roadmap

### Phase 1 (Current)
- ✅ Core RAG agent functionality
- ✅ Vector database integration
- ✅ Conversation state management
- ✅ Fit score calculation
- ✅ Report generation

### Phase 2 (Future)
- [ ] FastAPI REST API
- [ ] React-based web interface
- [ ] Real-time dashboard for employers
- [ ] Advanced NER for data extraction
- [ ] Multi-language support
- [ ] Voice interface integration
- [ ] Mobile app (QR code scanning)
- [ ] Advanced analytics dashboard
- [ ] A/B testing framework
- [ ] Integration with ATS systems

### Phase 3 (Advanced)
- [ ] Fine-tuned models for specific industries
- [ ] Video interview capability
- [ ] Skills assessment integration
- [ ] Background check automation
- [ ] Onboarding automation
- [ ] Predictive analytics for retention

---

**Built with ❤️ by the Cleo Team**
