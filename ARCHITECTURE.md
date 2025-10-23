# Cleo RAG Agent - Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION LAYER                           │
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │     CLI      │  │   REST API   │  │   Web UI     │  (Future)         │
│  │  (main.py)   │  │   (Future)   │  │   (Future)   │                   │
│  └──────┬───────┘  └──────────────┘  └──────────────┘                   │
└─────────┼────────────────────────────────────────────────────────────────┘
          │
          │ User Messages / Commands
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        CLEO RAG AGENT (agent.py)                         │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                  LangChain Agent Executor                         │  │
│  │                                                                   │  │
│  │  ┌─────────────────────────────────────────────────────────┐     │  │
│  │  │              OpenAI GPT-4 Turbo                         │     │  │
│  │  │          (Reasoning & Response Generation)              │     │  │
│  │  └─────────────────────────────────────────────────────────┘     │  │
│  │                                                                   │  │
│  │  ┌─────────────────────────────────────────────────────────┐     │  │
│  │  │         Conversation Buffer Memory                      │     │  │
│  │  │      (Context Retention Across Messages)                │     │  │
│  │  └─────────────────────────────────────────────────────────┘     │  │
│  │                                                                   │  │
│  │  ┌─────────────────────────────────────────────────────────┐     │  │
│  │  │              Stage-Specific Prompts                     │     │  │
│  │  │  • Engagement    • Qualification                        │     │  │
│  │  │  • Application   • Verification                         │     │  │
│  │  └─────────────────────────────────────────────────────────┘     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                              │                                            │
│                  ┌───────────┴───────────┐                               │
│                  │                       │                               │
│                  ▼                       ▼                               │
│  ┌──────────────────────────┐  ┌──────────────────────────┐             │
│  │      TOOL: KB Query      │  │   TOOL: State Save       │             │
│  │   (retrievers.py)        │  │   (states.py)            │             │
│  └──────────┬───────────────┘  └──────────┬───────────────┘             │
└─────────────┼──────────────────────────────┼──────────────────────────────┘
              │                              │
              │                              │
              ▼                              ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│   KNOWLEDGE BASE RETRIEVER   │   │     STATE MANAGER           │
│     (retrievers.py)          │   │      (states.py)            │
│                              │   │                             │
│  ┌────────────────────────┐ │   │  ┌───────────────────────┐ │
│  │  Semantic Search       │ │   │  │  CSV Storage          │ │
│  │  (Vector Similarity)   │ │   │  │  • engagement.csv     │ │
│  └────────────────────────┘ │   │  │  • qualification.csv  │ │
│                              │   │  │  • application.csv    │ │
│  ┌────────────────────────┐ │   │  │  • verification.csv   │ │
│  │  Similarity Search     │ │   │  │  • sessions.csv       │ │
│  │  (Threshold Filter)    │ │   │  └───────────────────────┘ │
│  └────────────────────────┘ │   │                             │
│                              │   │  ┌───────────────────────┐ │
│  ┌────────────────────────┐ │   │  │  Pydantic Models      │ │
│  │  Hybrid Search         │ │   │  │  • EngagementState    │ │
│  │  (60% Semantic +       │ │   │  │  • QualificationState │ │
│  │   40% Keyword)         │ │   │  │  • ApplicationState   │ │
│  └────────────────────────┘ │   │  │  • VerificationState  │ │
│              │               │   │  └───────────────────────┘ │
└──────────────┼───────────────┘   └─────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MILVUS VECTOR DATABASE                        │
│                      (docker-compose.yml)                        │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │           cleo_knowledge_base Collection               │    │
│  │                                                         │    │
│  │  Fields:                                                │    │
│  │  • id (primary key)                                     │    │
│  │  • embedding (3072-dim vector)                          │    │
│  │  • text (chunk content)                                 │    │
│  │  • document_name                                        │    │
│  │  • job_type (warehouse, retail, etc.)                   │    │
│  │  • section (requirements, benefits, etc.)               │    │
│  │  • chunk_index                                          │    │
│  │                                                         │    │
│  │  Index: IVF_FLAT with COSINE similarity                │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │  Milvus  │  │   etcd   │  │  MinIO   │                      │
│  │  :19530  │  │  :2379   │  │  :9000   │                      │
│  └──────────┘  └──────────┘  └──────────┘                      │
└─────────────────────────────────────────────────────────────────┘
               ▲
               │
               │ Insert Embeddings
               │
┌──────────────┴───────────────────────────────────────────────────┐
│                  DOCUMENT INGESTION PIPELINE                      │
│                       (ingestion.py)                              │
│                                                                   │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐        │
│  │   Extract   │ ──▶ │    Chunk    │ ──▶ │   Embed     │        │
│  │  (PyMuPDF)  │     │ (LangChain) │     │  (OpenAI)   │        │
│  └─────────────┘     └─────────────┘     └─────────────┘        │
│        ▲                                                          │
│        │                                                          │
│  ┌─────┴──────────────────────────────────┐                      │
│  │        PDF Documents                   │                      │
│  │  • Company handbooks                   │                      │
│  │  • Job descriptions                    │                      │
│  │  • Policy documents                    │                      │
│  │  • Benefits information                │                      │
│  └────────────────────────────────────────┘                      │
└───────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                     AUXILIARY SYSTEMS                                    │
│                                                                           │
│  ┌──────────────────────┐  ┌──────────────────────┐                     │
│  │   FIT SCORE          │  │   REPORT GENERATOR   │                     │
│  │   CALCULATOR         │  │   (report_generator  │                     │
│  │   (fit_score.py)     │  │        .py)          │                     │
│  │                      │  │                      │                     │
│  │  Components:         │  │  Outputs:            │                     │
│  │  • Qualification 30% │  │  • JSON reports      │                     │
│  │  • Experience 40%    │  │  • PDF reports       │                     │
│  │  • Verification 30%  │  │  • Fit score         │                     │
│  │                      │  │  • Recommendations   │                     │
│  │  Output: 0-100       │  │                      │                     │
│  │  Rating: Excellent   │  │  ReportLab           │                     │
│  │          to Poor     │  │  formatting          │                     │
│  └──────────────────────┘  └──────────────────────┘                     │
│                                                                           │
│  ┌──────────────────────────────────────────────────┐                   │
│  │         VERIFICATION SERVICE                     │                   │
│  │         (verification.py)                        │                   │
│  │                                                  │                   │
│  │  Mock Services:                                  │                   │
│  │  • ID Verification (driver's license, passport)  │                   │
│  │  • Background Check                              │                   │
│  │  • Confidence Scoring                            │                   │
│  │                                                  │                   │
│  │  Production: Integrate real APIs                 │                   │
│  │  (IDology, Truework, Checkr, etc.)               │                   │
│  └──────────────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                         CONFIGURATION & UTILITIES                        │
│                                                                           │
│  ┌──────────────────────┐  ┌──────────────────────┐                     │
│  │   CONFIG             │  │   UTILS              │                     │
│  │   (config.py)        │  │   (utils.py)         │                     │
│  │                      │  │                      │                     │
│  │  • Environment vars  │  │  • Logging (Loguru)  │                     │
│  │  • Pydantic settings │  │  • Session ID gen    │                     │
│  │  • Defaults          │  │  • Timestamps        │                     │
│  │  • Directory setup   │  │  • Lang detection    │                     │
│  └──────────────────────┘  └──────────────────────┘                     │
│                                                                           │
│  ┌──────────────────────────────────────────────────────┐               │
│  │              LOGGING SYSTEM                          │               │
│  │                                                      │               │
│  │  • Console output (colored, formatted)               │               │
│  │  • File output (logs/cleo_YYYY-MM-DD.log)            │               │
│  │  • Daily rotation, 30-day retention                  │               │
│  │  • Configurable log levels (INFO, DEBUG, etc.)       │               │
│  └──────────────────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                          DATA FLOW SUMMARY                               │
│                                                                           │
│  1. USER INPUT                                                           │
│     ↓                                                                    │
│  2. AGENT REASONING (LangChain + GPT-4)                                  │
│     ↓                                                                    │
│  3. DECISION: Query KB? Save State?                                      │
│     ↓                                                                    │
│  4a. RETRIEVAL (Milvus)  OR  4b. STATE UPDATE (CSV)                     │
│     ↓                          ↓                                         │
│  5a. CONTEXT ENRICHMENT    5b. SESSION SAVE                              │
│     ↓                          ↓                                         │
│  6. RESPONSE GENERATION ◀──────┘                                         │
│     ↓                                                                    │
│  7. USER OUTPUT                                                          │
│                                                                           │
│  At Completion:                                                          │
│  8. FIT SCORE CALCULATION                                                │
│  9. REPORT GENERATION (JSON + PDF)                                       │
│  10. EMPLOYER DASHBOARD (Future)                                         │
└─────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                        CONVERSATION STAGES                               │
│                                                                           │
│  Stage 1: ENGAGEMENT                                                     │
│  ├─ Greet applicant                                                      │
│  ├─ Explain process                                                      │
│  ├─ Get consent                                                          │
│  ├─ Capture company_id, job_id                                           │
│  └─ Detect language                                                      │
│     ↓                                                                    │
│  Stage 2: QUALIFICATION                                                  │
│  ├─ Age confirmation (18+)                                               │
│  ├─ Work authorization                                                   │
│  ├─ Shift preference                                                     │
│  ├─ Availability start date                                              │
│  ├─ Transportation                                                       │
│  └─ Hours preference (full/part-time)                                    │
│     ↓                                                                    │
│  Stage 3: APPLICATION                                                    │
│  ├─ Personal information (name, phone, email, address)                   │
│  ├─ Previous employment                                                  │
│  ├─ Job title & experience                                               │
│  ├─ Skills                                                               │
│  ├─ References                                                           │
│  └─ Communication preference                                             │
│     ↓                                                                    │
│  Stage 4: VERIFICATION                                                   │
│  ├─ ID upload request                                                    │
│  ├─ ID verification                                                      │
│  ├─ Background check (optional)                                          │
│  └─ Verification confirmation                                            │
│     ↓                                                                    │
│  COMPLETED                                                               │
│  ├─ Generate fit score                                                   │
│  ├─ Create eligibility report                                            │
│  └─ Hand-off to employer dashboard                                       │
└─────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                         TECHNOLOGY STACK                                 │
│                                                                           │
│  Frontend (Future):  React, Tailwind CSS                                 │
│  Backend:            Python 3.11+, FastAPI (Future)                      │
│  Agent:              LangChain 0.1.20                                    │
│  LLM:                OpenAI GPT-4 Turbo Preview                          │
│  Embeddings:         OpenAI text-embedding-3-large (3072-dim)            │
│  Vector DB:          Milvus 2.3.3                                        │
│  Storage:            etcd 3.5.5, MinIO RELEASE.2023-03-20                │
│  Persistence:        CSV (dev), PostgreSQL (prod)                        │
│  PDF Processing:     PyMuPDF 1.23.26                                     │
│  Report Gen:         ReportLab 4.0.9                                     │
│  Validation:         Pydantic 2.6.1                                      │
│  Logging:            Loguru 0.7.2                                        │
│  Deployment:         Docker, Docker Compose                              │
│  Future:             Kubernetes, AWS/Azure/GCP                           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Key Architecture Highlights

### 1. **Agentic Core**
   - Agent makes autonomous decisions
   - Not a rigid chatbot, but intelligent reasoning system
   - Tools-based architecture for extensibility

### 2. **RAG Implementation**
   - Knowledge base queried on-demand
   - Three retrieval strategies for flexibility
   - Context-aware response generation

### 3. **Modular Design**
   - Each component is independent
   - Easy to swap implementations (e.g., CSV → PostgreSQL)
   - Clear interfaces between modules

### 4. **State Management**
   - Four distinct stages with clear transitions
   - Resume capability at any point
   - Data persistence with type safety

### 5. **Scalability**
   - Milvus handles millions of vectors
   - Docker containerization ready
   - Horizontal scaling possible

### 6. **Production Ready**
   - Comprehensive error handling
   - Structured logging
   - Monitoring-ready
   - Security considerations documented

---

**Version**: 1.0.0  
**Last Updated**: October 24, 2025  
**Status**: Production Ready
