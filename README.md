# 🧠 DocuMind — Chat with Any Document

> **RAG (Retrieval-Augmented Generation) pipeline** that lets you upload PDFs, DOCX, and TXT files, then ask questions and get grounded, source-cited answers — powered by **Groq LLaMA 3.1**, **ChromaDB**, and **HuggingFace Embeddings**.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react)](https://react.dev)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?logo=langchain)](https://langchain.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5.5-FF6B35)](https://trychroma.com)
[![Groq](https://img.shields.io/badge/Groq-LLaMA_3.1-F55036)](https://groq.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📸 What it Does

| Feature | Details |
|---|---|
| 📄 **Document Upload** | PDF, DOCX, TXT — up to 20 MB. Drag-and-drop or click-to-browse |
| 🔍 **RAG Pipeline** | Chunks → Embeddings → Vector Search → LLM Answer |
| 💬 **Multi-turn Chat** | Conversation history maintained per browser session |
| 🔦 **Source Highlighting** | Every answer shows which document chunks were used + relevance scores |
| 📚 **Multi-document** | Upload many docs, filter chat to specific ones |
| ⚡ **Groq LLaMA 3.1** | Extremely fast inference, completely free |
| 💾 **Zero-cost Stack** | HuggingFace embeddings (local CPU), ChromaDB embedded, Groq free tier |

---

## 🏗️ Architecture

### High-Level System Design

```mermaid
graph TB
    subgraph Client ["🌐 Client (React + Vite)"]
        UI[Chat UI]
        Upload[Upload Zone]
        Sources[Source Panel]
    end

    subgraph Backend ["⚙️ Backend (FastAPI)"]
        API[FastAPI Router]
        DP[Document Processor]
        ES[Embedding Service]
        VS[Vector Store]
        LLM[LLM Service]
        REG[Doc Registry]
    end

    subgraph Storage ["💾 Storage"]
        CHROMA[(ChromaDB\nEmbedded)]
        JSON[(doc_registry.json)]
    end

    subgraph External ["☁️ External Services"]
        GROQ[Groq API\nLLaMA 3.1]
        HF[HuggingFace\nall-MiniLM-L6-v2\n local CPU]
    end

    Upload -->|"POST /api/upload"| API
    UI -->|"POST /api/chat/ask"| API

    API --> DP
    DP -->|"chunks"| ES
    ES -->|"embeddings"| VS
    VS --> CHROMA
    API --> REG
    REG --> JSON

    API --> LLM
    LLM -->|"similarity_search"| VS
    LLM -->|"chat completion"| GROQ
    ES -->|"embed_texts"| HF

    API -->|"ChatResponse"| UI
    UI --> Sources

    style Client fill:#0A1428,stroke:#162850,color:#CBD5E1
    style Backend fill:#0F1E3C,stroke:#162850,color:#CBD5E1
    style Storage fill:#050A18,stroke:#162850,color:#CBD5E1
    style External fill:#0A1428,stroke:#FBBF24,color:#CBD5E1
```

---

### RAG Pipeline (Full Flow)

```mermaid
sequenceDiagram
    actor User
    participant FE as React Frontend
    participant API as FastAPI Backend
    participant DP as DocumentProcessor
    participant ES as EmbeddingService<br/>(HuggingFace local)
    participant VS as VectorStore<br/>(ChromaDB)
    participant LLM as LLMService<br/>(Groq)

    Note over User,LLM: ── Document Upload Flow ──────────────────────────────

    User->>FE: Drag & drop PDF
    FE->>API: POST /api/upload (multipart)
    API->>DP: process(file_bytes, filename)
    DP->>DP: Extract text (pypdf / python-docx)
    DP->>DP: Split into 1000-char chunks<br/>with 200-char overlap
    DP-->>API: List[TextChunk]
    API->>ES: embed_texts(chunk_texts)
    ES->>ES: Run all-MiniLM-L6-v2 locally
    ES-->>API: List[List[float]] embeddings
    API->>VS: add_document(doc_id, filename, chunks)
    VS->>VS: upsert into ChromaDB collection
    API-->>FE: {doc_id, num_chunks, filename}
    FE-->>User: ✅ "42 chunks ingested"

    Note over User,LLM: ── Q&A Flow ──────────────────────────────────────────

    User->>FE: "What are the key findings?"
    FE->>API: POST /api/chat/ask {question, doc_ids, history}
    API->>LLM: ask(question, doc_ids, history)
    LLM->>ES: embed_query(question)
    ES-->>LLM: query_embedding[384]
    LLM->>VS: similarity_search(embedding, top_k=4)
    VS->>VS: cosine distance search in ChromaDB
    VS-->>LLM: top 4 chunks + scores
    LLM->>LLM: Build grounded system prompt<br/>with retrieved context
    LLM->>LLM: Inject conversation history (last 6 turns)
    LLM->>Groq: ChatCompletion (LLaMA 3.1 70B)
    Groq-->>LLM: Grounded answer text
    LLM-->>API: ChatResponse {answer, sources, tokens}
    API-->>FE: JSON response
    FE-->>User: Answer + Source chunks (with relevance %)
```

---

### Component Architecture

```mermaid
graph LR
    subgraph Frontend
        App --> Header
        App --> Sidebar
        App --> ChatPanel
        Sidebar --> DropZone
        Sidebar --> DocList
        ChatPanel --> MessageList
        ChatPanel --> InputBar
        MessageList --> Message
        Message --> SourcePanel
        SourcePanel --> SourceCard
    end

    subgraph Backend
        main.py --> upload_router
        main.py --> chat_router
        main.py --> documents_router
        upload_router --> DocumentProcessor
        upload_router --> VectorStore
        upload_router --> doc_registry
        chat_router --> LLMService
        LLMService --> VectorStore
        LLMService --> EmbeddingService
        documents_router --> doc_registry
        documents_router --> VectorStore
    end

    style Frontend fill:#0A1428,stroke:#162850,color:#CBD5E1
    style Backend fill:#0F1E3C,stroke:#162850,color:#CBD5E1
```

---

### Data Model

```mermaid
erDiagram
    DOCUMENT {
        string doc_id PK "UUID4"
        string filename
        string file_type
        int num_chunks
        int size_bytes
        datetime uploaded_at
    }

    CHUNK {
        string chunk_id PK "doc_id_chunkIndex"
        string doc_id FK
        string filename
        string page_content
        int chunk_index
        int page_number
        float[] embedding "384-dim vector"
    }

    CHAT_MESSAGE {
        string role "user | assistant"
        string content
    }

    DOCUMENT ||--o{ CHUNK : "has many"
    CHAT_MESSAGE }o--|| DOCUMENT : "references"
```

---

## 🗂️ Project Structure

```
documind/
├── backend/
│   ├── main.py                    # FastAPI app, CORS, lifespan hooks
│   ├── requirements.txt           # Python dependencies
│   ├── .env.example               # Environment variable template
│   │
│   ├── models/
│   │   └── schemas.py             # Pydantic request/response models
│   │
│   ├── routes/
│   │   ├── upload.py              # POST /api/upload — file ingestion
│   │   ├── chat.py                # POST /api/chat/ask — Q&A endpoint
│   │   └── documents.py           # GET/DELETE /api/documents — CRUD
│   │
│   ├── services/
│   │   ├── document_processor.py  # Text extraction + chunking
│   │   ├── embedding_service.py   # HuggingFace local embeddings
│   │   ├── vector_store.py        # ChromaDB wrapper
│   │   └── llm_service.py         # RAG orchestration + Groq LLM
│   │
│   └── utils/
│       └── doc_registry.py        # JSON-based document metadata store
│
├── frontend/
│   ├── index.html                 # HTML entry point
│   ├── package.json
│   ├── vite.config.js             # Vite + dev proxy config
│   ├── tailwind.config.js
│   │
│   └── src/
│       ├── main.jsx               # React root
│       ├── App.jsx                # Global state + layout
│       ├── index.css              # Global styles + Tailwind
│       │
│       ├── components/
│       │   ├── Header.jsx         # Top nav bar
│       │   ├── Sidebar.jsx        # Document upload + list
│       │   ├── ChatPanel.jsx      # Chat UI + message history
│       │   └── SourcePanel.jsx    # Retrieved chunk display
│       │
│       └── services/
│           └── api.js             # Axios API client
│
└── README.md
```

---

## ⚡ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Backend** | Python 3.11 + FastAPI | Async, fast, auto-docs, type-safe |
| **LLM** | Groq API (LLaMA 3.1 70B) | 100% free, 10× faster than OpenAI |
| **Orchestration** | LangChain 0.3 | RAG pipeline, prompt management |
| **Vector DB** | ChromaDB (embedded) | Zero cost, zero server, persists to disk |
| **Embeddings** | HuggingFace all-MiniLM-L6-v2 | Free, local CPU, 384-dim, excellent quality |
| **PDF Parsing** | pypdf | Actively maintained, page-level metadata |
| **DOCX Parsing** | python-docx | Native DOCX support |
| **Frontend** | React 18 + Vite | Fast HMR, modern React |
| **Styling** | Tailwind CSS | Utility-first, dark theme |
| **Backend Deploy** | Render.com | Free tier, auto-deploy from GitHub |
| **Frontend Deploy** | Vercel | Free, global CDN, auto-deploy |

---

## 🚀 Quick Start (Local Development)

### Prerequisites

- Python 3.10+ and pip
- Node.js 18+ and npm
- Git

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/documind.git
cd documind
```

### 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 3. Start the backend

```bash
uvicorn main:app --reload --port 8000
# Docs available at: http://localhost:8000/docs
```

### 4. Frontend setup (new terminal)

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
# Opens at: http://localhost:5173
```

---

## 🔑 Getting Your API Keys

### Groq API (LLM) — Free

1. Visit [console.groq.com](https://console.groq.com)
2. Sign up / log in
3. Navigate to **API Keys** → **Create API Key**
4. Copy the key into `backend/.env` as `GROQ_API_KEY`

> Groq's free tier is extremely generous — rate limits are high enough for development and light production use.

---

## 🌐 Deployment

See `DEPLOYMENT.md` for full step-by-step instructions including:
- Backend → Render.com (free tier)
- Frontend → Vercel (free tier)
- Environment variable configuration
- Custom domain setup

---

## 🧪 API Reference

After starting the backend, interactive docs are at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/upload/` | Upload and ingest a document |
| `GET` | `/api/documents/` | List all documents |
| `DELETE` | `/api/documents/{id}` | Delete a document |
| `POST` | `/api/chat/ask` | Ask a question (RAG) |
| `GET` | `/health` | Health check |

### Chat request example

```json
POST /api/chat/ask
{
  "question": "What are the key findings?",
  "doc_ids": ["uuid1", "uuid2"],
  "history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help?"}
  ],
  "top_k": 4
}
```

---

## 🧩 Key Design Decisions

### Why overlapping chunks?
Text at chunk boundaries (e.g., a conclusion sentence that spans two chunks) would otherwise be lost. A 200-character overlap ensures boundary content appears in at least one chunk.

### Why cosine similarity?
Normalised HuggingFace embeddings represent direction, not magnitude. Cosine similarity captures semantic orientation without being thrown off by sentence length differences.

### Why a JSON registry instead of a database?
For a portfolio project deployed on a free tier, a JSON file is simpler to set up and zero additional cost. Replace with SQLite or PostgreSQL for production multi-user deployments.

### Why Groq instead of OpenAI?
Groq's free tier provides more than enough throughput for demos and portfolio projects, and inference is measurably faster due to their custom LPU hardware.

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.


