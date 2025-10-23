# Cleo RAG Agent - Project Overview

## 📖 Executive Summary

Cleo is a production-ready Conversational AI Agent designed to streamline the job application process through natural language interactions. Built with state-of-the-art RAG (Retrieval-Augmented Generation) architecture, it combines the power of OpenAI's GPT models, LangChain's agent framework, and Milvus vector database to create an intelligent, context-aware assistant.

## 🎯 Key Features

### 1. Agentic Architecture
- **Autonomous Decision Making**: Agent decides when to query knowledge base vs. respond directly
- **Tool-Based Framework**: Uses LangChain tools for retrieval and state management
- **Conversational Intelligence**: Maintains natural dialogue flow across multiple stages

### 2. Advanced RAG System
- **Multiple Retrieval Methods**: 
  - Semantic Search (pure vector similarity)
  - Similarity Search (with threshold filtering)
  - Hybrid Search (combines semantic + keyword matching)
- **OpenAI Embeddings**: Uses `text-embedding-3-large` for high-quality vector representations
- **Milvus Vector Database**: Scalable, production-ready vector storage

### 3. Structured Conversation Flow
Four distinct stages with resumability:
1. **Engagement**: Consent, company/job identification
2. **Qualification**: Basic eligibility screening
3. **Application**: Comprehensive information collection
4. **Verification**: Identity and background verification

### 4. Intelligent Scoring System
- **Fit Score Calculation**: Weighted composite (0-100 scale)
  - Qualification: 30%
  - Experience: 40%
  - Verification: 30%
- **Automatic Rating**: Excellent, Good, Fair, Below Average, Poor

### 5. Comprehensive Reporting
- **JSON Reports**: Structured data for system integration
- **PDF Reports**: Professional formatted documents
- **Configurable Output**: Include/exclude fit scores

## 🏛️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                          │
│                  (CLI / Future: Web/Mobile)                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   CLEO RAG AGENT                             │
│  ┌────────────────────────────────────────────────────┐     │
│  │          LangChain Agent Executor                  │     │
│  │  • Reasoning Engine                                │     │
│  │  • Tool Orchestration                              │     │
│  │  • Conversation Memory                             │     │
│  └────────────────┬───────────────────────────────────┘     │
│                   │                                          │
│  ┌────────────────▼───────────────────┐                     │
│  │           TOOLS                    │                     │
│  │  • Knowledge Base Query            │                     │
│  │  • State Management                │                     │
│  └────────────────┬───────────────────┘                     │
└───────────────────┼──────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│  RETRIEVER       │    │  STATE MANAGER   │
│  • Semantic      │    │  • CSV Storage   │
│  • Similarity    │    │  • Session Mgmt  │
│  • Hybrid        │    │  • Resume Logic  │
└────────┬─────────┘    └──────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│          MILVUS VECTOR DB                │
│  ┌────────────────────────────────┐      │
│  │  Embeddings + Metadata         │      │
│  │  • Document chunks             │      │
│  │  • Job types                   │      │
│  │  • Sections                    │      │
│  └────────────────────────────────┘      │
└──────────────────────────────────────────┘
         ▲
         │
┌────────┴─────────┐
│  INGESTION       │
│  • PDF Extract   │
│  • Text Chunk    │
│  • Embed Gen     │
└──────────────────┘
```

## 📦 Module Breakdown

### Core Modules

#### 1. `config.py`
- Centralized configuration management
- Environment variable handling with Pydantic
- Default values and validation
- Directory structure setup

#### 2. `utils.py`
- Logging setup with Loguru
- Session ID generation
- Timestamp utilities
- Language detection (basic)

#### 3. `ingestion.py`
- PDF text extraction (PyMuPDF)
- Text chunking (LangChain RecursiveCharacterTextSplitter)
- Embedding generation (OpenAI)
- Milvus collection management
- Batch and single document ingestion

#### 4. `retrievers.py`
- KnowledgeBaseRetriever class
- Three retrieval methods implementation
- Result formatting for LLM consumption
- Configurable top-k and thresholds

#### 5. `states.py`
- Pydantic models for all conversation stages
- CSV-based persistence layer
- StateManager for CRUD operations
- Session resume capability

#### 6. `fit_score.py`
- FitScoreCalculator with weighted scoring
- Component score calculations:
  - Qualification score (basic eligibility)
  - Experience score (work history + skills)
  - Verification score (ID + background)
- Rating system (Excellent to Poor)

#### 7. `agent.py`
- CleoRAGAgent main class
- LangChain agent creation and configuration
- Tool definitions (KB query, state save)
- Stage-specific system prompts
- Conversation state updates
- Message processing pipeline

#### 8. `report_generator.py`
- ReportGenerator class
- JSON report creation
- PDF report generation (ReportLab)
- Fit score analysis inclusion
- Professional formatting

#### 9. `verification.py`
- MockVerificationService for testing
- ID verification simulation
- Background check simulation
- Confidence scoring
- Production API integration placeholder

### Application Entry Points

#### 1. `main.py`
- CleoApplication wrapper class
- Session management (new/resume)
- Interactive CLI interface
- Command handling
- Report generation trigger

#### 2. `demo_conversation.py`
- End-to-end conversation simulation
- All four stages demonstrated
- Automatic state progression
- Report generation demo
- Retrieval testing

### Setup & Utilities

#### 1. `quickstart.py`
- Automated setup script
- Prerequisites checking
- Environment configuration
- Virtual environment creation
- Dependency installation
- Milvus stack initialization
- Knowledge base setup

#### 2. `create_sample_docs.py`
- Sample company handbook generator
- Sample job description generator
- PDF creation with ReportLab
- Realistic content for testing

#### 3. `setup_knowledge_base.py`
- Milvus collection initialization
- Document ingestion automation
- Retrieval testing
- Setup verification

## 🔄 Data Flow

### 1. Document Ingestion Flow
```
PDF Document → Text Extraction → Chunking → Embedding Generation → Milvus Storage
```

### 2. Conversation Flow
```
User Input → Agent Reasoning → Tool Selection → Action Execution → Response Generation
                                    ↓
                         ┌──────────┴──────────┐
                         ▼                     ▼
                   KB Query              State Update
                         ↓                     ↓
                   Retrieval            CSV Save
                         ↓                     ↓
                   Context              Session Data
```

### 3. Retrieval Flow
```
Query → Embedding → Vector Search → Score Calculation → Top-K Selection → Format Context
                         ↓
                    Milvus DB
```

### 4. Report Generation Flow
```
Session ID → State Loading → Fit Score Calc → Report Assembly → JSON + PDF Output
```

## 💾 Data Storage

### CSV Files (Development)
Located in `storage/` directory:
- `engagement_states.csv` - Engagement stage data
- `qualification_states.csv` - Qualification stage data
- `application_states.csv` - Application stage data
- `verification_states.csv` - Verification stage data
- `sessions.csv` - Session metadata

### Vector Database (Milvus)
Located in Docker volumes:
- **Collection**: `cleo_knowledge_base`
- **Fields**:
  - `id` (primary key, auto-generated)
  - `embedding` (3072-dimensional vector)
  - `text` (chunk content)
  - `document_name` (source document)
  - `job_type` (e.g., warehouse, retail)
  - `section` (e.g., requirements, benefits)
  - `chunk_index` (position in document)

### Generated Reports
Located in `reports/` directory:
- `eligibility_report_{session_id}.json`
- `eligibility_report_{session_id}.pdf`

## 🔧 Configuration

### Environment Variables

#### Essential
- `OPENAI_API_KEY` - OpenAI API key (required)
- `MILVUS_HOST` - Milvus server host
- `MILVUS_PORT` - Milvus server port

#### Customizable
- `OPENAI_CHAT_MODEL` - LLM model (default: gpt-4-turbo-preview)
- `OPENAI_EMBEDDING_MODEL` - Embedding model (default: text-embedding-3-large)
- `CHUNK_SIZE` - Text chunk size (default: 512)
- `CHUNK_OVERLAP` - Chunk overlap (default: 102)
- `TOP_K_RESULTS` - Retrieval results count (default: 5)
- `SIMILARITY_THRESHOLD` - Minimum similarity (default: 0.7)

#### Weights
- `QUALIFICATION_WEIGHT` - Qualification score weight (default: 0.30)
- `EXPERIENCE_WEIGHT` - Experience score weight (default: 0.40)
- `VERIFICATION_WEIGHT` - Verification score weight (default: 0.30)

## 🚀 Deployment Options

### Development (Recommended for Testing)
```bash
# Start Milvus only
docker-compose up -d

# Run application locally
python main.py
```

### Production (Full Containerization)
```bash
# Build and run everything
docker-compose -f docker-compose.prod.yml up -d
```

### Cloud Deployment
- **Milvus**: Use Zilliz Cloud (managed Milvus)
- **Application**: Deploy to AWS ECS, Google Cloud Run, or Azure Container Instances
- **Database**: Replace CSV with PostgreSQL/MongoDB
- **API**: Add FastAPI REST API layer

## 🧪 Testing Strategy

### Unit Tests (Recommended)
- Test each module independently
- Mock external dependencies (OpenAI, Milvus)
- Focus on business logic

### Integration Tests
- Test end-to-end conversation flow
- Verify state transitions
- Validate report generation

### Performance Tests
- Measure retrieval latency
- Test concurrent sessions
- Benchmark fit score calculation

## 🔐 Security Considerations

### Current Implementation
- Environment variables for secrets
- No authentication (development only)
- Local CSV storage (not encrypted)

### Production Requirements
- Implement JWT-based authentication
- Encrypt sensitive data at rest
- Use managed secret stores (AWS Secrets Manager, Azure Key Vault)
- Add rate limiting
- Implement CORS properly
- Use HTTPS/TLS for all communications
- Audit logging for compliance

## 📊 Analytics Opportunities

### Conversation Analytics
- Drop-off rate by stage
- Average time per stage
- Common questions/queries
- Qualification pass/fail rates

### Performance Metrics
- Response time percentiles
- Retrieval accuracy
- Fit score distribution
- Verification success rates

### Business Intelligence
- Application completion rates
- Top skills mentioned
- Preferred shift patterns
- Geographic distribution

## 🔮 Future Enhancements

### Short Term
1. Replace CSV with proper database (PostgreSQL)
2. Add FastAPI REST API
3. Implement real verification API
4. Add comprehensive unit tests
5. Create employer dashboard (Streamlit)

### Medium Term
1. Build React web interface
2. Add voice interface support
3. Implement advanced NER for data extraction
4. Multi-language support (full i18n)
5. Integration with ATS systems
6. Mobile app with QR code scanning

### Long Term
1. Fine-tuned models for specific industries
2. Video interview capability
3. Skills assessment automation
4. Predictive analytics for retention
5. Automated onboarding workflows
6. AI-powered interview scheduling

## 🤝 Integration Points

### Current
- OpenAI API (LLM + Embeddings)
- Milvus (Vector Database)

### Planned
- Verification APIs (IDology, Truework)
- ATS Systems (Greenhouse, Lever, Workday)
- Background Check Services (Checkr, Sterling)
- Communication Platforms (Twilio, SendGrid)
- Analytics Platforms (Segment, Mixpanel)

## 📝 License & Compliance

### Open Source Components
- LangChain (MIT)
- Milvus (Apache 2.0)
- PyMuPDF (AGPL)
- ReportLab (BSD)

### Data Privacy
- Implement GDPR compliance
- Add data retention policies
- Enable right to deletion
- Maintain audit trails

### Employment Law
- Ensure EEOC compliance
- Fair chance hiring considerations
- Accessibility requirements (WCAG)

## 👥 Team Roles

### Development
- Backend Engineer: API, agent logic
- Data Engineer: Ingestion, vector DB
- Frontend Engineer: Web UI
- Mobile Engineer: Mobile app

### Operations
- DevOps Engineer: Infrastructure, CI/CD
- Data Scientist: Model optimization, analytics
- Security Engineer: Security hardening

### Business
- Product Manager: Feature prioritization
- UX Designer: Conversation flow optimization
- Legal/Compliance: Regulatory compliance

## 📞 Support & Maintenance

### Monitoring
- Application logs (Loguru → ELK)
- Error tracking (Sentry)
- Performance monitoring (New Relic, DataDog)
- Uptime monitoring (Pingdom)

### Maintenance Windows
- Database backups: Daily
- Vector DB reindexing: Weekly
- Dependency updates: Monthly
- Security patches: As needed

---

**Document Version**: 1.0  
**Last Updated**: October 24, 2025  
**Status**: Development Complete, Production Ready with Enhancements
