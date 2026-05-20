# Regulatory Intelligence Platform

An agentic AI system for Nigerian financial compliance intelligence. Submit a regulatory question, receive a structured, citation-backed compliance report — produced by a 7-agent LangGraph workflow grounded entirely in indexed regulatory documents.

> **Not a chatbot.** Every response is a structured compliance output: obligations, risk scores, compliance checklists, licensing requirements, and citations — all traceable to specific regulatory documents, sections, and pages.

---

## What It Does

| Capability              | Description                                                                                                 |
| ----------------------- | ----------------------------------------------------------------------------------------------------------- |
| **Regulatory Analysis** | Submit a business query; receive a full compliance report with risk level, obligations, gaps, and citations |
| **Document Ingestion**  | Upload CBN, SEC, NDIC, FIRS PDFs; system parses, chunks, embeds, and indexes them                           |
| **Audit Trail**         | Every analysis is persisted to PostgreSQL with the full agent decision trace                                |
| **Citation Grounding**  | Every claim traces back to a specific document, section, and page number                                    |

---

## Stack

| Layer         | Technology                                               |
| ------------- | -------------------------------------------------------- |
| API           | FastAPI + uvicorn                                        |
| Workflow      | LangGraph (7-agent state machine)                        |
| Vector DB     | Qdrant (dense + BM25 hybrid search)                      |
| Relational DB | PostgreSQL 16 + SQLAlchemy async                         |
| Cache         | Redis 7 (provisioned, reserved for sessions)             |
| LLM           | OpenAI `gpt-4o-mini` (or Ollama local)                   |
| Embeddings    | `BAAI/bge-base-en-v1.5` (768-dim, sentence-transformers) |
| Sparse        | `Qdrant/bm25` via fastembed                              |
| Reranker      | `BAAI/bge-reranker-v2-m3` (cross-encoder)                |
| PDF Parsing   | PyMuPDF + pdfplumber + Tesseract OCR                     |
| Runtime       | Python 3.12, uv                                          |

---

## Project Structure

```
app/
├── main.py                        # FastAPI app entry point, lifespan, router registration
├── api/routes/
│   ├── regulations.py             # POST /regulations/upload
│   ├── analysis.py                # POST /analysis/analyze-business
│   └── audit.py                   # GET  /audit/trace/{id}, /audit/session/{id}
├── agents/                        # One file per LangGraph agent
│   ├── orchestrator.py
│   ├── jurisdiction_mapper.py
│   ├── reasoning.py
│   ├── auditor.py
│   ├── citation_verifier.py
│   └── critic.py
├── graph/
│   ├── state.py                   # AgentState TypedDict (shared workflow state)
│   ├── nodes.py                   # LangGraph node functions
│   └── workflow.py                # Graph construction and compilation
├── services/
│   ├── compliance_service.py      # Orchestrates workflow + audit persistence
│   ├── ingestion_service.py       # Document ingestion pipeline
│   ├── retrieval_service.py       # 8-step RAG pipeline
│   ├── embedding_service.py       # Dense embeddings
│   ├── sparse_embedding_service.py
│   └── audit_service.py
├── repositories/
│   ├── vector_repository.py       # Qdrant upsert + hybrid search + RRF fusion
│   ├── document_repository.py
│   └── audit_repository.py
├── models/database_models.py      # SQLAlchemy ORM (DocumentRecord, AuditRecord)
├── db/
│   ├── postgres.py                # Async engine, session factory
│   └── qdrant.py                  # Async Qdrant client, collection init
├── utils/
│   ├── llm_client.py              # Unified OpenAI/Ollama async chat client
│   ├── chunking.py                # Section-aware legal document chunking
│   ├── parsers.py                 # PDF parsing with OCR fallback
│   ├── reranking.py               # Cross-encoder reranking singleton
│   └── citations.py               # Citation formatting utilities
├── prompts/                       # System prompt constants per agent
└── core/config.py                 # Pydantic Settings, loaded from .env
```

---

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Tesseract OCR — `brew install tesseract` (macOS)

---

## Local Setup

### 1. Install dependencies

```bash
uv sync
source .venv/bin/activate
```

### 2. Configure environment

Create a `.env` file in the project root:

```bash
# PostgreSQL
POSTGRES_USER=regplatform
POSTGRES_PASSWORD=regpassword1111
POSTGRES_DB=regulatory_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# LLM — OpenAI (default)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini

# Embedding
EMBEDDING_MODEL_NAME=BAAI/bge-base-en-v1.5
EMBEDDING_DIMENSION=768
```

### 3. Start infrastructure

```bash
docker compose up -d
```

### 4. Start the server

```bash
uvicorn app.main:app --reload
```

On startup you should see:

```
Starting up Regulatory Intelligence Platform...
PostgreSQL tables ready
Qdrant collection ready
```

---

## API

### Upload a regulation document

```bash
curl -X POST http://localhost:8000/regulations/upload \
  -F "file=@CBN_Consumer_Protection.pdf" \
  -F "regulator=CBN" \
  -F "document_type=Regulation" \
  -F "issued_date=2019-12-20"
```

### Analyze a business query

```bash
curl -s -X POST http://localhost:8000/analysis/analyze-business \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What complaint resolution timelines must we follow under CBN regulations?",
    "organization_context": "Digital bank with retail customers"
  }' | python3 -m json.tool
```

Response includes: `audit_id`, `session_id`, `final_report` (obligations, risk score, checklist, citations), `agent_trace`, `duration_ms`.

### Retrieve an audit trace

```bash
curl http://localhost:8000/audit/trace/<audit_id>
```

### List session audit records

```bash
curl http://localhost:8000/audit/session/<session_id>
```

### Health check

```bash
curl http://localhost:8000/health
```

Interactive API docs available at `http://localhost:8000/docs`.

---

## How It Works

A query triggers a 7-node LangGraph workflow:

```
User Query
    │
    ▼ Orchestrator       — decomposes query, identifies target regulators
    │
    ▼ Jurisdiction Mapper — maps applicable regulators (CBN/SEC/NDIC/FIRS)
    │
    ▼ Research Agent      — 8-step RAG: query expansion → hybrid search →
    │                       reranking → freshness scoring → MMR → compression
    │
    ▼ Reasoning Agent     — legal synthesis from retrieved chunks (citations required)
    │
    ▼ Compliance Auditor  — risk score (1–10), compliance gaps, checklist, licensing
    │
    ▼ Citation Verifier   — cross-checks every claim against retrieved evidence
    │
    ▼ Critic Agent        — adversarial quality review; loops back on FAIL (max 2×)
    │
    ▼ AuditService        — persists full workflow state to PostgreSQL
    │
    ▼ Structured JSON response
```

### RAG Pipeline (8 steps)

1. **Query rewriting** — LLM generates 2 legal rephrasings
2. **Multi-query hybrid search** — dense (semantic) + BM25 (keyword) per variant
3. **Deduplication** — by `source::section::page` key
4. **Metadata filter** — by regulator and/or document type
5. **Cross-encoder reranking** — `BAAI/bge-reranker-v2-m3`
6. **Freshness scoring** — penalty for documents older than 180 days
7. **MMR diversity** — prevents duplicate sections in results
8. **Contextual compression** — LLM extracts only relevant sentences per chunk

---

## Switching to Local LLM (Ollama)

```bash
# Pull models
ollama pull qwen2.5:14b
ollama pull qwen2.5:7b

# Update .env
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434
LLM_MODEL_NAME=qwen2.5:14b
LLM_SMALL_MODEL_NAME=qwen2.5:7b
```

---

## Accessing the Database

```bash
# Connect to PostgreSQL
docker exec -it postgres psql -U regplatform -d regulatory_db

# Recent audit records
SELECT id, overall_risk_level, grounding_score, duration_ms, created_at
FROM audit_records ORDER BY created_at DESC LIMIT 10;

# Indexed documents
SELECT file_name, regulator, document_type, chunks_ingested FROM documents;
```

---

## Common Issues

| Issue                          | Fix                                                                              |
| ------------------------------ | -------------------------------------------------------------------------------- |
| First request takes 4+ minutes | Reranker model (2.27 GB) downloading on first use — subsequent requests are fast |
| `No text extracted from PDF`   | Install Tesseract: `brew install tesseract`                                      |
| `409 Conflict` on upload       | Same document already indexed — intentional dedup by content hash                |
| `Connection refused :6333`     | Run `docker compose up -d`                                                       |
| Server exits with code 1       | Activate venv first: `source .venv/bin/activate`                                 |

---

## Full Documentation

See [DOCUMENTATION.md](DOCUMENTATION.md) for the complete technical reference covering architecture, all API routes, database schema, AI/RAG pipeline, security analysis, engineering decisions, and development guide.

A Word version is available at [DOCUMENTATION.docx](DOCUMENTATION.docx).
