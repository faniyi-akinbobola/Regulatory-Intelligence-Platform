# Regulatory Intelligence Platform — Complete Technical Documentation

> **Version:** 0.1.0 (MVP)
> **Stack:** Python 3.12 · FastAPI · LangGraph · Qdrant · PostgreSQL · OpenAI
> **Last Updated:** May 2026

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Product Overview](#3-product-overview)
4. [High-Level System Architecture](#4-high-level-system-architecture)
5. [Detailed Backend Documentation](#5-detailed-backend-documentation)
6. [Frontend Documentation](#6-frontend-documentation)
7. [Database Documentation](#7-database-documentation)
8. [AI / LLM / RAG Documentation](#8-ai--llm--rag-documentation)
9. [API Documentation](#9-api-documentation)
10. [DevOps & Infrastructure](#10-devops--infrastructure)
11. [Security Analysis](#11-security-analysis)
12. [Observability & Monitoring](#12-observability--monitoring)
13. [End-to-End Request Walkthrough](#13-end-to-end-request-walkthrough)
14. [Engineering Decisions](#14-engineering-decisions)
15. [Technical Debt & Risks](#15-technical-debt--risks)
16. [Future Roadmap](#16-future-roadmap)
17. [Local Development Setup](#17-local-development-setup)
18. [Glossary](#18-glossary)

---

## 1. Executive Summary

### Project Overview

The **Regulatory Intelligence Platform** is an agentic AI system designed to help businesses, fintechs, compliance teams, and legal professionals understand and navigate Nigerian financial regulations. It accepts natural-language questions about compliance, licensing, and regulatory obligations and returns structured, citation-backed compliance intelligence reports — not chatbot responses.

### Core Mission

To eliminate the ambiguity, cost, and time burden of manual regulatory research in Nigeria by providing instant, auditable, and citation-grounded compliance analysis for any business activity.

### Primary Users

| User Type                    | Use Case                                                      |
| ---------------------------- | ------------------------------------------------------------- |
| **Fintech founders**         | Determine licensing requirements before launch                |
| **Compliance officers**      | Check whether internal policies meet CBN/SEC obligations      |
| **Legal teams**              | Quickly retrieve applicable regulations with citations        |
| **Product managers**         | Understand what regulatory constraints apply to a new feature |
| **Executives / boards**      | Receive risk-level reports on business activities             |
| **Regulatory affairs teams** | Gap analysis between current operations and regulations       |

### Key Value Proposition

- **Speed**: What previously took a compliance lawyer hours to research returns in ~90–120 seconds
- **Grounding**: Every claim cites a specific regulatory document, section, and page — no hallucinated rules
- **Auditability**: Every analysis is persisted with a complete agent decision trace for audit review
- **Structure**: Outputs are compliance checklists, risk matrices, and gap reports — not paragraphs

### Business Problem Being Solved

Nigeria's financial regulatory landscape spans at least four major regulators (CBN, SEC, NDIC, FIRS) with thousands of pages of guidelines, circulars, and acts that are frequently updated. Businesses routinely:

- Launch products without understanding licensing requirements
- Miss compliance obligations across overlapping regulatory jurisdictions
- Pay expensive legal fees for basic regulatory research
- Expose themselves to regulatory sanctions due to information asymmetry

This platform transforms regulatory documents into a queryable intelligence layer.

---

## 2. Problem Statement

### The Exact Problem

Nigerian financial regulation is fragmented, voluminous, and constantly evolving. There is no unified source of truth. CBN, SEC Nigeria, NDIC, and FIRS all issue regulations independently, and many business activities fall under multiple overlapping jurisdictions simultaneously.

### Current Pain Points

1. **Information fragmentation**: Regulations are scattered across regulator websites in PDF format with no semantic search capability.
2. **Jurisdictional ambiguity**: A payment wallet product may be subject to CBN guidelines, NDIC deposit protection rules, and FIRS tax obligations — simultaneously.
3. **Legal research cost**: Engaging a regulatory lawyer for basic compliance questions costs ₦500K–₦2M+ per engagement.
4. **Hallucination risk in generic AI**: Using general-purpose LLMs like ChatGPT to answer compliance questions is dangerous — they confidently fabricate non-existent regulations.
5. **Audit trail absence**: Manual legal research produces no structured, reproducible audit record.

### Why Existing Solutions Are Insufficient

Generic LLMs lack grounding in specific regulatory documents and hallucinate legal citations. Legal databases (where available) are search-only with no reasoning or synthesis capability. Human compliance consultants are expensive, slow, and not available on-demand.

### Consequences of Not Solving This

- Regulatory sanctions from CBN/SEC for unlicensed operations
- Criminal liability under BOFIA or CAMA for executives
- Loss of operating license
- Reputational damage
- Investor risk in regulated fintech ventures

---

## 3. Product Overview

### Main Capabilities

| Capability                        | Description                                                                                                        |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **Regulatory Document Ingestion** | Upload PDFs from CBN, SEC, NDIC, FIRS. System parses, chunks, embeds, and indexes them.                            |
| **Business Compliance Analysis**  | Submit a business query; receive a structured compliance report with risk score, obligations, gaps, and citations. |
| **Audit Trace Retrieval**         | Every analysis is stored. Retrieve the full agent decision trace at any time for audit or review.                  |
| **Session Chaining**              | Multiple analyses under the same `session_id` for tracking a compliance investigation over time.                   |

### Core Workflow

```
1. Compliance team submits query: "Can we offer a wallet with investment features?"
2. Platform identifies applicable regulators: CBN (wallet), SEC (investment)
3. Platform retrieves relevant regulation chunks from its knowledge base
4. Legal reasoning agent synthesises obligations, prohibitions, permissions
5. Compliance auditor scores risk and identifies gaps
6. Citation verifier ensures every claim is grounded in retrieved text
7. Critic agent reviews output quality; may loop for refinement
8. Structured compliance report returned with audit ID
```

### User Personas

**Persona 1: Sarah — Head of Compliance, Digital Bank**

> "I need to confirm our new overdraft product complies with CBN consumer protection rules before launch. I need a documented compliance review I can show our board."

**Persona 2: Tunde — Fintech Founder**

> "We're building a P2P lending app. What licenses do we need? Are we subject to FIRS? What are our consumer disclosure obligations?"

**Persona 3: Adeola — Legal Counsel**

> "A client is being investigated by CBN. I need to quickly understand their consumer complaint resolution obligations and whether they've breached any timelines."

### Real-World Use Cases

- **Pre-launch licensing check**: "What CBN licences does a mobile money operator require?"
- **Consumer protection audit**: "What disclosure requirements apply to our loan product?"
- **Complaint handling review**: "What are the mandated complaint resolution timelines under CBN regulations?"
- **Cross-regulatory analysis**: "What obligations apply to a payment company that also handles tax remittances?"
- **Penalty exposure assessment**: "What sanctions does CBN impose for unresolved consumer complaints?"

---

## 4. High-Level System Architecture

### Architectural Pattern

The platform is a **modular monolith** with **agentic AI orchestration** internally. It is not a microservices architecture (all Python in one process) but is designed for clean separation of concerns between layers, making it straightforward to extract services later.

```
┌──────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                               │
│  curl / Postman / Chainlit UI / Future Web Frontend               │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTP REST
┌────────────────────────────▼─────────────────────────────────────┐
│                        API LAYER (FastAPI)                        │
│  POST /regulations/upload                                         │
│  POST /analysis/analyze-business                                  │
│  GET  /audit/trace/{id}                                           │
│  GET  /audit/session/{id}                                         │
│  GET  /health                                                     │
└────────────────────────────┬─────────────────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
┌─────────▼──────┐  ┌────────▼──────┐  ┌───────▼────────────┐
│IngestionService│  │ComplianceServ.│  │ AuditService        │
│  (document     │  │ (workflow      │  │ (record persistence)│
│   pipeline)    │  │  orchestration)│  └────────────────────┘
└─────────┬──────┘  └────────┬──────┘
          │                  │
          │         ┌────────▼──────────────────────────────────┐
          │         │         LANGGRAPH WORKFLOW                 │
          │         │                                            │
          │         │  ┌────────────┐    ┌──────────────────┐  │
          │         │  │Orchestrator│───▶│Jurisdiction Mapper│  │
          │         │  └────────────┘    └────────┬─────────┘  │
          │         │                             │             │
          │         │                    ┌────────▼─────────┐  │
          │         │                    │  Research Agent   │  │
          │         │                    │ (RetrievalService)│  │
          │         │                    └────────┬─────────┘  │
          │         │                             │             │
          │         │                    ┌────────▼─────────┐  │
          │         │                    │ Reasoning Agent   │  │
          │         │                    └────────┬─────────┘  │
          │         │                             │             │
          │         │                    ┌────────▼─────────┐  │
          │         │                    │  Auditor Agent    │  │
          │         │                    └────────┬─────────┘  │
          │         │                             │             │
          │         │                    ┌────────▼─────────┐  │
          │         │                    │Citation Verifier  │  │
          │         │                    └────────┬─────────┘  │
          │         │                             │             │
          │         │                    ┌────────▼─────────┐  │
          │         │          ┌─────────│   Critic Agent    │  │
          │         │          │ FAIL    └────────┬─────────┘  │
          │         │          │ (loop)           │ PASS        │
          │         │          └─────────────────┘             │
          │         │                    END                    │
          │         └───────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────────────┐
│                      DATA LAYER                                  │
│                                                                  │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │   Qdrant         │  │   PostgreSQL      │  │    Redis      │  │
│  │ (vector DB)      │  │ (audit records,   │  │ (future:      │  │
│  │ dense + sparse   │  │  document index)  │  │  sessions,    │  │
│  │ hybrid search    │  │                   │  │  caching)     │  │
│  └─────────────────┘  └──────────────────┘  └───────────────┘  │
└────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────┐
│                    EXTERNAL SERVICES                             │
│  OpenAI API (gpt-4o-mini)  /  Ollama (local, optional)          │
└────────────────────────────────────────────────────────────────┘
```

### Major Components

| Component           | Technology                        | Responsibility                                   |
| ------------------- | --------------------------------- | ------------------------------------------------ |
| **API Server**      | FastAPI + uvicorn                 | HTTP request handling, routing, validation       |
| **Workflow Engine** | LangGraph                         | Multi-agent state machine orchestration          |
| **Vector Store**    | Qdrant                            | Semantic + keyword search over regulation chunks |
| **Relational DB**   | PostgreSQL + SQLAlchemy async     | Persistent audit records, document registry      |
| **Cache/Session**   | Redis                             | Provisioned, reserved for future session state   |
| **LLM Provider**    | OpenAI gpt-4o-mini (or Ollama)    | Natural language reasoning across all agents     |
| **Dense Embedder**  | `BAAI/bge-base-en-v1.5` (768-dim) | Semantic similarity encoding                     |
| **Sparse Embedder** | `Qdrant/bm25` via fastembed       | Keyword (BM25) search vectors                    |
| **Reranker**        | `BAAI/bge-reranker-v2-m3`         | Cross-encoder re-ranking of retrieved chunks     |
| **PDF Parser**      | PyMuPDF + pdfplumber + Tesseract  | Regulatory document parsing and OCR              |

---

## 5. Detailed Backend Documentation

### Folder Structure

```
app/
├── main.py                    # FastAPI app, lifespan, router registration
│
├── api/
│   └── routes/
│       ├── regulations.py     # POST /regulations/upload
│       ├── analysis.py        # POST /analysis/analyze-business
│       └── audit.py           # GET /audit/trace/{id}, /audit/session/{id}
│
├── agents/                    # One file per LangGraph agent
│   ├── orchestrator.py        # Query decomposition + task planning
│   ├── jurisdiction_mapper.py # Regulator identification
│   ├── reasoning.py           # Legal synthesis
│   ├── auditor.py             # Risk scoring + gap analysis
│   ├── citation_verifier.py   # Hallucination prevention
│   └── critic.py              # Adversarial quality review
│
├── graph/
│   ├── state.py               # AgentState TypedDict (shared workflow state)
│   ├── nodes.py               # LangGraph node functions (one per agent)
│   └── workflow.py            # Graph construction + compilation
│
├── services/
│   ├── compliance_service.py  # Orchestrates LangGraph + audit persistence
│   ├── ingestion_service.py   # Document ingestion pipeline
│   ├── retrieval_service.py   # 8-step RAG pipeline
│   ├── embedding_service.py   # Dense embeddings (sentence-transformers)
│   ├── sparse_embedding_service.py  # BM25 sparse embeddings (fastembed)
│   └── audit_service.py       # Creates + retrieves audit records
│
├── repositories/
│   ├── vector_repository.py   # Qdrant upsert + hybrid search
│   ├── document_repository.py # PostgreSQL document registry CRUD
│   └── audit_repository.py    # PostgreSQL audit record CRUD
│
├── models/
│   └── database_models.py     # SQLAlchemy ORM models (DocumentRecord, AuditRecord)
│
├── db/
│   ├── postgres.py            # Async engine, session factory, init_db()
│   └── qdrant.py              # Async Qdrant client, collection init
│
├── utils/
│   ├── llm_client.py          # Unified OpenAI/Ollama async chat client
│   ├── chunking.py            # Legal document chunking (section-aware)
│   ├── parsers.py             # PDF parsing (PyMuPDF + pdfplumber + OCR)
│   ├── reranking.py           # Cross-encoder reranking singleton
│   └── citations.py           # Citation string formatting utilities
│
├── prompts/                   # System prompt constants per agent
│   ├── orchestrator.py
│   ├── jurisdiction_mapper.py
│   ├── reasoning.py
│   ├── auditor.py
│   ├── citation_verifier.py
│   └── critic.py
│
└── core/
    └── config.py              # Pydantic Settings, loaded from .env
```

### Design Patterns

| Pattern                  | Where Applied                                                                                          |
| ------------------------ | ------------------------------------------------------------------------------------------------------ |
| **Repository pattern**   | `AuditRepository`, `DocumentRepository`, `VectorRepository` — isolates DB access from business logic   |
| **Service layer**        | `ComplianceService`, `IngestionService`, `AuditService` — all business logic lives here, not in routes |
| **Dependency injection** | FastAPI `Depends(get_db_session)`, `Depends(get_qdrant_client)` for testability                        |
| **Singleton**            | Reranker model, Qdrant client, sparse embedding model — loaded once, reused across requests            |
| **Strategy pattern**     | `llm_client.chat()` routes to OpenAI or Ollama based on `settings.llm_provider` config                 |
| **State machine**        | LangGraph `StateGraph` with typed state transitions                                                    |

### Application Startup Lifecycle

`app/main.py` uses FastAPI's `lifespan` context manager:

```
1. logging.basicConfig() — configure structured logging
2. await init_db()        — SQLAlchemy creates PostgreSQL tables if not exist
3. await init_qdrant_collection() — creates Qdrant 'regulations' collection with
                                    dense (768-dim cosine) + sparse (BM25) vectors
                                    if not already present
4. yield (server running)
5. Shutdown logged
```

### Configuration Management

All configuration lives in `app/core/config.py` using `pydantic-settings`. Values are loaded from a `.env` file automatically.

```python
# Key settings
llm_provider: str = "openai"          # "openai" or "ollama"
openai_api_key: str = ""              # Set in .env
openai_model: str = "gpt-4o-mini"
openai_url: str = "https://api.openai.com/v1/chat/completions"
llm_base_url: str = "http://localhost:11434"  # Ollama
embedding_model_name: str = "BAAI/bge-base-en-v1.5"
embedding_dimension: int = 768
qdrant_collection_name: str = "regulations"
```

### Dependency Injection

Routes receive database sessions via FastAPI's dependency system:

```python
@router.post("/analyze-business")
async def analyze_business(
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_db_session),  # injected
):
```

`get_db_session()` in `app/db/postgres.py` yields an `AsyncSession`, auto-commits on success, rolls back on exception, and closes after the request.

### Error Handling

- **Route level**: `HTTPException` raised for known errors (404 not found, 400 bad request, 409 conflict)
- **Service level**: `ValueError` raised for business rule violations (e.g., zero chunks after parsing), caught and converted to HTTP 500 in routes
- **Agent level**: Each agent has a `try/except json.JSONDecodeError` fallback that returns a safe default dict — the workflow never crashes due to a malformed LLM response
- **Retrieval level**: `_expand_queries` and `_compress_chunk` both have `except Exception` guards with `logger.debug` — gracefully degrade to original query / uncompressed chunk

### Validation

- **Request validation**: Pydantic `BaseModel` on all request bodies via FastAPI — wrong types return HTTP 422 automatically
- **File validation**: `file.content_type != "application/pdf"` check in upload route
- **Deduplication**: SHA-256 hash check before ingesting a document — returns HTTP 409 if content already indexed
- **UUID validation**: `uuid.UUID(audit_id)` parse attempt in `AuditService.get_record()` — returns `None` on invalid UUID

### Async Architecture

The entire backend is async (`async def` throughout). Key async boundaries:

- All database operations via `asyncpg` through SQLAlchemy async engine
- All Qdrant operations via `AsyncQdrantClient`
- All LLM calls via `httpx.AsyncClient`
- All LangGraph node functions are `async def`
- `asyncio.gather()` used in `_compress_chunks()` for concurrent chunk compression

---

## 6. Frontend Documentation

### Current Status

The MVP has **no dedicated frontend**. The system is a pure REST API consumed via curl, Postman, or any HTTP client.

**Chainlit** is provisioned in the architecture plan as a "Regulatory Intelligence Console" (not a chatbot UI). It will visualize:

- Active workflow stages and agent traces
- Compliance reports with structured sections
- Risk scores and citations
- Audit history per session

### Planned Frontend Architecture

```
Chainlit Application
├── Workflow visualization panel (LangGraph step progress)
├── Compliance report renderer (obligations / checklist / citations)
├── Risk score dashboard (score + risk level + recommendations)
├── Agent trace explorer (expandable decision tree per agent)
└── Document upload interface (drag-and-drop regulation PDFs)
```

**Note**: Chainlit is not yet implemented. This section describes the intended design per the architecture document.

---

## 7. Database Documentation

### Database Overview

| Database       | Technology                                   | Purpose                                                                      |
| -------------- | -------------------------------------------- | ---------------------------------------------------------------------------- |
| **PostgreSQL** | PostgreSQL 16 via asyncpg + SQLAlchemy async | Persistent relational storage for audit records and document registry        |
| **Qdrant**     | Qdrant (latest)                              | Vector database for semantic + keyword search over regulation chunks         |
| **Redis**      | Redis 7                                      | Provisioned for future session management and query caching — dormant in MVP |

---

### PostgreSQL Schema

#### Table: `documents`

Tracks every regulation document ingested into the system.

| Column            | Type                     | Description                                                         |
| ----------------- | ------------------------ | ------------------------------------------------------------------- |
| `id`              | SERIAL PRIMARY KEY       | Auto-increment integer                                              |
| `file_name`       | VARCHAR(512)             | Original filename (e.g., "CBN Consumer Protection Regulations.pdf") |
| `file_hash`       | VARCHAR(64) UNIQUE INDEX | SHA-256 hash for deduplication                                      |
| `regulator`       | VARCHAR(100)             | e.g., "CBN", "SEC", "NDIC", "FIRS"                                  |
| `document_type`   | VARCHAR(100)             | e.g., "Regulation", "Circular", "Act", "Guideline"                  |
| `total_pages`     | INTEGER                  | Total parsed pages                                                  |
| `chunks_ingested` | INTEGER                  | Number of semantic chunks stored in Qdrant                          |
| `ingested_at`     | TIMESTAMPTZ              | UTC timestamp of ingestion                                          |
| `notes`           | TEXT                     | Optional operator notes                                             |

#### Table: `audit_records`

Stores the complete state of every workflow execution for auditability.

| Column                 | Type             | Description                                              |
| ---------------------- | ---------------- | -------------------------------------------------------- |
| `id`                   | UUID PRIMARY KEY | Auto-generated UUID — returned to callers as `audit_id`  |
| `session_id`           | UUID INDEX       | Links multiple analyses in one investigation             |
| `query`                | TEXT             | Original user query                                      |
| `organization_context` | TEXT             | Optional business context provided by caller             |
| `target_regulators`    | JSON             | List of regulators identified by jurisdiction agent      |
| `agent_trace`          | JSON             | Ordered list of `{agent, status}` for each node executed |
| `jurisdiction_result`  | JSON             | Full output of the Jurisdiction Mapper agent             |
| `reasoning_result`     | JSON             | Full output of the Reasoning agent                       |
| `audit_result`         | JSON             | Full output of the Auditor agent                         |
| `citation_result`      | JSON             | Full output of the Citation Verifier agent               |
| `critic_result`        | JSON             | Full output of the Critic agent                          |
| `final_report`         | JSON             | Assembled compliance report                              |
| `overall_risk_level`   | VARCHAR(20)      | CRITICAL / HIGH / MEDIUM / LOW                           |
| `hallucination_risk`   | VARCHAR(20)      | NONE / LOW / MEDIUM / HIGH                               |
| `grounding_score`      | INTEGER          | % of claims verified by Citation agent (0–100)           |
| `iteration_count`      | INTEGER          | How many critic–reasoning loops occurred                 |
| `status`               | VARCHAR(20)      | Always "COMPLETED" in current implementation             |
| `duration_ms`          | INTEGER          | End-to-end workflow duration in milliseconds             |
| `created_at`           | TIMESTAMPTZ      | Server-generated UTC timestamp                           |

#### Entity Relationship

```
documents (1) ←——————————————— (many) [Qdrant vectors]
                                        (linked by source filename in payload)

audit_records (many) ——————————— (1) session_id
                                        (UUID used to group related analyses)
```

### Qdrant Schema

**Collection name**: `regulations`

**Vector configuration**:

- `"dense"`: 768-dimensional cosine similarity (BAAI/bge-base-en-v1.5 output)
- `"sparse"`: BM25 sparse vectors (Qdrant/bm25 via fastembed)

**Point payload** (stored per chunk):

| Field           | Type         | Description                                                    |
| --------------- | ------------ | -------------------------------------------------------------- |
| `text`          | string       | The regulation text content                                    |
| `source`        | string       | PDF filename                                                   |
| `page`          | integer      | 1-based page number                                            |
| `section`       | string       | Section identifier (e.g., "PART FOUR", "4.1")                  |
| `title`         | string       | Section title text                                             |
| `hierarchy`     | list[string] | Breadcrumb path (e.g., ["PART TWO", "3.1 GENERAL PROVISIONS"]) |
| `regulator`     | string       | e.g., "CBN" — used for metadata filtering                      |
| `document_type` | string       | e.g., "Regulation", "Circular" — used for filtering            |
| `issued_date`   | string       | ISO date for freshness scoring                                 |

**Point ID strategy**: Deterministic MD5-based UUID from `{document_name}::{chunk_index}` — re-ingesting the same document overwrites rather than duplicates.

### Data Lifecycle

```
PDF Upload
    │
    ▼
parse_document() ──── PyMuPDF primary, pdfplumber for tables, Tesseract for images
    │
    ▼
chunk_document() ──── Section-aware chunking preserving section numbers + hierarchy
    │
    ▼
embed_texts() ──────── BAAI/bge-base-en-v1.5 dense vectors (batch 32)
    │
    ▼
sparse embed() ──────── Qdrant/bm25 sparse BM25 vectors
    │
    ▼
VectorRepository.upsert() ──── Qdrant write (deterministic IDs)
    │
    ▼
DocumentRepository.save() ──── PostgreSQL document registry entry
```

### Migration Strategy

Currently: `Base.metadata.create_all` on startup creates tables if they do not exist.
**Production recommendation**: Migrate to Alembic (already in `pyproject.toml` dependencies) for versioned schema migrations. Scripts in `alembic/versions/` would replace the `create_all` call.

---

## 8. AI / LLM / RAG Documentation

### Why AI/LLM is Used

Regulatory compliance is a language-heavy domain. Rules are expressed in natural language with legal nuance, cross-references, and contextual interpretation requirements. LLMs provide:

1. **Query understanding** — mapping "can I launch a wallet?" to precise regulatory questions
2. **Legal synthesis** — identifying obligations, prohibitions, and conflicts across multiple retrieved chunks
3. **Risk reasoning** — assessing compliance risk relative to a specific business context
4. **Adversarial review** — checking whether the analysis is logically consistent

### LLM Configuration

| Setting             | Value                              | Notes                                    |
| ------------------- | ---------------------------------- | ---------------------------------------- |
| **Provider**        | OpenAI (default) or Ollama (local) | Controlled by `llm_provider` in config   |
| **Model**           | `gpt-4o-mini`                      | Configurable via `openai_model`          |
| **Unified client**  | `app/utils/llm_client.py`          | All 9 LLM call sites go through `chat()` |
| **Ollama fallback** | `qwen2.5:14b` / `qwen2.5:7b`       | For local/offline operation              |

### Multi-Agent Workflow Architecture

The system uses **LangGraph** — a stateful directed graph for orchestrating AI agents. The workflow is a Directed Acyclic Graph (with one conditional back-edge for quality looping).

#### Agent Responsibilities

**Agent 1: Orchestrator** (`orchestrator.py`)

- Input: raw user query + optional organization context
- Output: `task_breakdown` (subtask list), `target_regulators` (e.g., ["CBN", "SEC"]), `context_summary`, `query_type`
- LLM timeout: 60 seconds
- Role: Does NOT perform legal analysis — only task decomposition and routing

**Agent 2: Jurisdiction Mapper** (`jurisdiction_mapper.py`)

- Input: query + context summary from orchestrator
- Output: `applicable_regulators` (list with regulator + jurisdiction rationale), `overlap_risks`, `primary_regulator`
- LLM timeout: 60 seconds
- Role: Identifies which of CBN / SEC / NDIC / FIRS / FCCPC / NITDA / NDPA apply

**Agent 3: Research** (via `RetrievalService`)

- No LLM call for retrieval itself — uses embedding models
- LLM used for query expansion (timeout: 30s) and contextual compression (timeout: 20s per chunk)
- Role: Retrieves the most relevant regulation chunks from Qdrant via 8-step pipeline (see below)

**Agent 4: Regulatory Reasoning** (`reasoning.py`)

- Input: original query + retrieved chunks + jurisdiction result
- Output: `obligations`, `prohibitions`, `permissions`, `conflicts`, `reasoning_summary`, `confidence`
- LLM timeout: 180 seconds (most complex step)
- Role: Performs actual legal synthesis — every conclusion must cite a specific chunk

**Agent 5: Compliance Auditor** (`auditor.py`)

- Input: query + reasoning output + top-10 retrieved chunks
- Output: `risk_score` (1–10), `risk_level`, `compliance_gaps`, `compliance_checklist`, `licensing_requirements`, `recommendations`
- LLM timeout: 120 seconds
- Role: Structured risk assessment and gap analysis

**Agent 6: Citation Verifier** (`citation_verifier.py`)

- Input: reasoning output + audit output + all retrieved chunks
- Output: `verified_citations`, `failed_citations`, `overall_grounding_score` (0–100%), `hallucination_risk`, `recommendation`
- LLM timeout: 120 seconds
- Role: Cross-checks every claim against the retrieved evidence — the hallucination firewall

**Agent 7: Critic** (`critic.py`)

- Input: query + reasoning + audit + citation outputs
- Output: `issues_found` (with severity), `missing_analysis`, `quality_score` (1–10), `overall_assessment` (PASS / PASS_WITH_REVISIONS / FAIL), `summary_feedback`
- LLM timeout: 120 seconds
- Role: Adversarial reviewer — finds what other agents missed

#### Workflow Routing Logic

```python
def route_after_critic(state: AgentState) -> str:
    if overall_assessment == "FAIL" and iteration_count < max_iterations:
        return "reasoning"  # Loop back: re-run reasoning → auditor → citation → critic
    return "end"
```

The critic can trigger at most `max_iterations` (default: 2) re-runs of the reasoning–auditor–citation cycle. This prevents infinite loops while allowing quality refinement.

### RAG Pipeline (8 Steps)

The `RetrievalService.retrieve()` method implements a production-grade RAG pipeline:

```
Query Input
    │
    ▼ Step 1: Query Rewriting (LLM)
    │   → Generates 2 legal rephrasings of the query
    │   → Returns: [original_query, rephrasing_1, rephrasing_2]
    │   → Fallback: original query only if LLM call fails
    │
    ▼ Step 2: Multi-Query Hybrid Search (per variant)
    │   → Dense search: query text → BAAI/bge-base-en-v1.5 → 768-dim vector → Qdrant cosine
    │   → Sparse search: query text → BM25 (fastembed) → sparse vector → Qdrant sparse index
    │   → Runs for each of the 3 query variants
    │   → Deduplication by source::section::page key
    │
    ▼ Step 3: Post-Retrieval Metadata Filter
    │   → If multiple regulators identified, filter chunks to those regulators only
    │   → Supports filtering by document_type (e.g., "Regulation" only)
    │
    ▼ Step 4: Cross-Encoder Reranking
    │   → BAAI/bge-reranker-v2-m3 (2.27GB model, loaded once as singleton)
    │   → Scores (query, chunk_text) pairs with cross-attention
    │   → Reranks top_k × 2 candidates, keeps top_k × 2 for next step
    │   → More accurate than cosine similarity alone
    │
    ▼ Step 5: Temporal / Freshness Scoring
    │   → Documents < 180 days old: no penalty (multiplier = 1.0)
    │   → Older documents: linear decay to 0.80 over 5 years
    │   → Applies penalty to score; marks chunk as freshness_penalized=True
    │
    ▼ Step 6: MMR Diversity Filtering
    │   → Maximal Marginal Relevance: prevents multiple chunks from same section
    │   → Promotes cross-regulator diversity in results
    │   → Returns top rerank_top_k diverse chunks
    │
    ▼ Step 7: Contextual Compression (LLM)
    │   → For chunks > 300 chars: asks LLM to extract only sentences relevant to query
    │   → Runs concurrently via asyncio.gather()
    │   → Reduces noise in chunks passed to reasoning agent
    │
    ▼ Returns: list of enriched chunk dicts
```

### Embedding Strategy

| Model                   | Type                          | Dimension | Use Case                                             |
| ----------------------- | ----------------------------- | --------- | ---------------------------------------------------- |
| `BAAI/bge-base-en-v1.5` | Dense (sentence-transformers) | 768       | Semantic similarity — understanding meaning          |
| `Qdrant/bm25`           | Sparse (fastembed)            | Variable  | Keyword matching — exact terms like regulation names |

Both run locally on CPU — no GPU required, no external API calls for embedding.

**RRF Fusion**: Reciprocal Rank Fusion combines dense and sparse result rankings into a single merged list. Formula: `score(doc) = Σ 1 / (rank + k)` where k=60.

### Prompt Engineering

All system prompts are stored in `app/prompts/` as Python string constants. Key design principles:

1. **Role clarity**: Each prompt starts with a precise role definition ("You are the Compliance Auditor Agent...")
2. **Output format specification**: Every prompt specifies exact JSON output structure
3. **Constraint enforcement**: Critical rules listed explicitly (e.g., "Every legal conclusion MUST cite a specific retrieved chunk")
4. **Hallucination prevention**: Reasoning and citation prompts explicitly prohibit introducing information not in retrieved chunks
5. **No redundancy**: Agents are given only what they need — orchestrator does not reason, reasoning agent does not audit

### Hallucination Prevention Strategy

The system uses a **layered defense**:

1. **Retrieval-grounded prompts**: Reasoning agent is explicitly told: "Never introduce regulatory knowledge not present in the retrieved chunks"
2. **Citation Verifier**: Dedicated agent cross-checks every claim against chunk evidence, produces `hallucination_risk` score and `overall_grounding_score`
3. **Critic adversarial review**: Checks "Claims made with HIGH confidence that have MEDIUM or LOW citation grounding"
4. **Stored evidence**: All retrieved chunks are persisted in the audit record, making post-hoc verification possible

---

## 9. API Documentation

### Base URL

```
http://localhost:8000
```

---

### GET /health

**Purpose**: Service liveness check.

**Response**:

```json
{ "status": "ok" }
```

---

### POST /regulations/upload

**Purpose**: Ingest a regulatory PDF document into the knowledge base.

**Request**: `multipart/form-data`

| Field           | Type       | Required | Description                                               |
| --------------- | ---------- | -------- | --------------------------------------------------------- |
| `file`          | File (PDF) | Yes      | The regulation PDF                                        |
| `regulator`     | string     | Yes      | e.g., `CBN`, `SEC`, `NDIC`, `FIRS`                        |
| `document_type` | string     | Yes      | e.g., `Regulation`, `Circular`, `Act`, `Guideline`        |
| `issued_date`   | string     | No       | ISO date, e.g., `2024-03-15` — used for freshness scoring |
| `notes`         | string     | No       | Optional operator notes                                   |

**Example**:

```bash
curl -X POST http://localhost:8000/regulations/upload \
  -F "file=@CBN_Consumer_Protection.pdf" \
  -F "regulator=CBN" \
  -F "document_type=Regulation" \
  -F "issued_date=2019-12-20"
```

**Success Response** (HTTP 201):

```json
{
  "message": "Document ingested successfully",
  "file_name": "CBN_Consumer_Protection.pdf",
  "regulator": "CBN",
  "document_type": "Regulation",
  "total_pages": 45,
  "chunks_ingested": 19
}
```

**Error Responses**:

- `400`: Non-PDF file uploaded
- `409`: Document with identical content already ingested
- `422`: Missing required fields
- `500`: Parse error or embedding failure

**Internal Flow**:

1. Validate `content_type == "application/pdf"`
2. Compute SHA-256 hash; reject if already in `documents` table
3. Write to temp file (parsers need file path)
4. `IngestionService.ingest()` → parse → chunk → embed (dense + sparse) → upsert to Qdrant
5. `DocumentRepository.save()` → write to PostgreSQL
6. Delete temp file

---

### POST /analysis/analyze-business

**Purpose**: The core endpoint. Submits a compliance/regulatory question and receives a structured analysis report.

**Request**: `application/json`

| Field                  | Type          | Required | Description                                                    |
| ---------------------- | ------------- | -------- | -------------------------------------------------------------- |
| `query`                | string        | Yes      | The regulatory question or business description                |
| `session_id`           | string (UUID) | No       | Link this analysis to an existing session; generated if absent |
| `organization_context` | string        | No       | Business description to give agents context                    |

**Example**:

```bash
curl -X POST http://localhost:8000/analysis/analyze-business \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What CBN obligations apply to a mobile wallet offering micro-investments?",
    "organization_context": "Fintech startup targeting retail customers",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**Success Response** (HTTP 200):

```json
{
  "audit_id": "a040e06d-ec99-4f6f-8ee0-3540463adeb0",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "query": "What CBN obligations apply to a mobile wallet offering micro-investments?",
  "final_report": {
    "query": "...",
    "executive_summary": "...",
    "obligations": [
      {"description": "...", "citation": "CBN Consumer Protection Regulations, Part Four", "regulator": "CBN"}
    ],
    "prohibitions": [...],
    "permissions": [...],
    "conflicts": [...],
    "compliance_gaps": [...],
    "compliance_checklist": [
      {"requirement": "...", "status": "UNMET", "citation": "...", "notes": "..."}
    ],
    "licensing_requirements": [...],
    "recommendations": [...],
    "risk_score": 7,
    "risk_level": "HIGH",
    "citations": [
      {
        "citation_string": "CBN | CBN Consumer Protection Regulations.pdf | PART FOUR | Page 22",
        "document": "CBN Consumer Protection Regulations.pdf",
        "section": "PART FOUR",
        "page": 22,
        "regulator": "CBN",
        "text_excerpt": "..."
      }
    ]
  },
  "agent_trace": [
    {"agent": "orchestrator", "status": "completed"},
    {"agent": "jurisdiction_mapper", "status": "completed"},
    {"agent": "researcher", "status": "completed"},
    {"agent": "reasoning", "status": "completed"},
    {"agent": "auditor", "status": "completed"},
    {"agent": "citation_verifier", "status": "completed"},
    {"agent": "critic", "status": "completed"}
  ],
  "duration_ms": 106474
}
```

**Error Responses**:

- `422`: Missing `query` field
- `500`: Workflow execution error (wrapped with detail message)

**Typical Latency**: 90–120 seconds (OpenAI gpt-4o-mini, 20 indexed chunks, reranker cached)

---

### GET /audit/trace/{audit_id}

**Purpose**: Retrieve the complete, immutable audit trace for a workflow run.

**Path parameter**: `audit_id` — UUID returned by `/analyze-business`

**Example**:

```bash
curl http://localhost:8000/audit/trace/a040e06d-ec99-4f6f-8ee0-3540463adeb0
```

**Success Response** (HTTP 200): Full audit record including all agent outputs, citations, trace, risk level, grounding score, and iteration count.

**Error Responses**:

- `404`: Audit ID not found

---

### GET /audit/session/{session_id}

**Purpose**: List all audit records for a session, newest first.

**Query parameter**: `limit` (default: 20)

**Example**:

```bash
curl "http://localhost:8000/audit/session/550e8400-e29b-41d4-a716-446655440000?limit=5"
```

**Success Response** (HTTP 200): Array of summary audit records (without full agent outputs).

---

## 10. DevOps & Infrastructure

### Infrastructure Overview

```
┌─────────────────────────────────────────────────┐
│              Docker Compose (Local)              │
│                                                  │
│  ┌───────────┐  ┌─────────────┐  ┌───────────┐  │
│  │  Qdrant   │  │  PostgreSQL │  │   Redis   │  │
│  │ :6333     │  │  :5432      │  │  :6379    │  │
│  │ :6334(RPC)│  │             │  │           │  │
│  └───────────┘  └─────────────┘  └───────────┘  │
└─────────────────────────────────────────────────┘

FastAPI Application (uvicorn, host process — not containerized in MVP)
├── port: 8000
├── --reload flag for development
└── Connects to Docker containers via localhost ports
```

### Docker Compose Services

**Qdrant**

- Image: `qdrant/qdrant:latest`
- Ports: `6333` (REST API), `6334` (gRPC)
- Volume: `qdrant_data:/qdrant/storage` (persistent)
- Restart: `unless-stopped`

**PostgreSQL**

- Image: `postgres:16-alpine`
- Port: `5432`
- Credentials: from `.env` (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`)
- Volume: `postgres_data:/var/lib/postgresql/data` (persistent)
- Restart: `unless-stopped`

**Redis**

- Image: `redis:7-alpine`
- Port: `6379`
- Persistence: `appendonly yes` (AOF persistence enabled)
- Volume: `redis_data:/data`
- Restart: `unless-stopped`

### Starting Infrastructure

```bash
# Start all Docker services
docker compose up -d

# Start the FastAPI application
uvicorn app.main:app --reload

# Verify services
curl http://localhost:8000/health
curl http://localhost:6333/healthz
```

### Package Management

Uses `uv` — a fast Python package manager. `pyproject.toml` defines dependencies.

```bash
uv sync          # Install all dependencies
uv add <pkg>     # Add new dependency
```

### Environment Variables

All environment variables defined in `.env` (not committed to version control):

```bash
POSTGRES_USER=regplatform
POSTGRES_PASSWORD=<secret>
POSTGRES_DB=regulatory_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

QDRANT_HOST=localhost
QDRANT_PORT=6333

OPENAI_API_KEY=sk-proj-...
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-4o-mini
```

### CI/CD

Not yet configured. Recommended future setup:

- GitHub Actions for lint (ruff), type check (mypy), test (pytest) on PR
- Docker image build for FastAPI application
- Automated deployment to cloud on merge to main

---

## 11. Security Analysis

### Current State (MVP)

**Authentication**: None implemented. All API endpoints are open.
**Authorization**: None implemented. Any caller can access any audit record.

This is acceptable for an internal MVP/demo but must be addressed before any external or production deployment.

### Implemented Security Controls

| Control                      | Implementation                                                                    |
| ---------------------------- | --------------------------------------------------------------------------------- |
| **Input validation**         | Pydantic models on all request bodies; FastAPI returns 422 for type violations    |
| **File type validation**     | MIME type check on uploads (`application/pdf` only)                               |
| **Content deduplication**    | SHA-256 hash prevents re-ingestion of identical files                             |
| **SQL injection prevention** | SQLAlchemy ORM with parameterized queries — no raw SQL                            |
| **Secrets management**       | API keys in `.env`, loaded via pydantic-settings — not hardcoded                  |
| **LLM output sanitization**  | JSON parsing with `try/except` — malformed LLM responses never crash the workflow |
| **Async session isolation**  | Each request gets its own `AsyncSession`; auto-rollback on exception              |

### OWASP Top 10 Analysis

| Risk                          | Status               | Notes                                                               |
| ----------------------------- | -------------------- | ------------------------------------------------------------------- |
| A01 Broken Access Control     | ⚠️ **Not addressed** | No auth on any endpoint                                             |
| A02 Cryptographic Failures    | ✅ Partial           | Secrets in `.env`; HTTPS not configured (no TLS in dev)             |
| A03 Injection                 | ✅ Mitigated         | ORM parameterized queries; Pydantic validation                      |
| A04 Insecure Design           | ✅ Partial           | Clean separation of concerns; no business logic in routes           |
| A05 Security Misconfiguration | ⚠️ **Risk**          | `echo=False` in SQLAlchemy (good); no CORS config; no rate limiting |
| A06 Vulnerable Components     | ✅ Active            | Modern pinned dependencies via uv/pyproject.toml                    |
| A07 Auth Failures             | ⚠️ **Not addressed** | No authentication at all                                            |
| A09 Logging Failures          | ✅ Good              | Structured logging at INFO level; sensitive data not logged         |
| A10 SSRF                      | ✅ Mitigated         | LLM URL configurable but from env only; no user-supplied URLs       |

### Security Roadmap (Required Before Production)

1. JWT Bearer token authentication on all endpoints
2. Role-based access control (RBAC) — admin, analyst, read-only
3. Rate limiting on `/analyze-business` (LLM calls are expensive)
4. CORS configuration
5. HTTPS/TLS termination (nginx reverse proxy or load balancer)
6. Secrets rotation strategy (not hardcoded keys)
7. Audit log for authentication events

---

## 12. Observability & Monitoring

### Logging

Structured logging is configured at startup in `app/main.py`:

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
```

**Log prefixes** make log filtering easy:

| Prefix           | Source                      | What It Logs                          |
| ---------------- | --------------------------- | ------------------------------------- |
| `[ORCHESTRATOR]` | orchestrator.py             | Query decomposition, LLM calls        |
| `[JURISDICTION]` | jurisdiction_mapper.py      | Regulator mapping, LLM calls          |
| `[RESEARCH]`     | nodes.py                    | Chunk retrieval count, query variants |
| `[RETRIEVAL]`    | retrieval_service.py        | Query variants, expansion failures    |
| `[RERANKER]`     | reranking.py                | Failures, fallback to original order  |
| `[REASONING]`    | reasoning.py                | Chunk synthesis, LLM calls            |
| `[AUDITOR]`      | auditor.py                  | Risk assessment calls                 |
| `[CITATION]`     | citation_verifier.py        | Claim verification                    |
| `[CRITIC]`       | critic.py                   | Quality assessment                    |
| `[COMPLIANCE]`   | compliance_service.py       | Workflow duration, iteration count    |
| `[AUDIT]`        | audit_service.py            | Record persistence with ID            |
| `[INGEST]`       | ingestion_service.py        | Parse/chunk/embed progress            |
| `[QDRANT]`       | qdrant.py                   | Collection creation/validation        |
| `[SPARSE]`       | sparse_embedding_service.py | BM25 model loading                    |
| `[LLM]`          | llm_client.py               | Provider + model used (DEBUG level)   |

### Metrics Available in Audit Records

Every workflow run produces the following observable metrics stored in PostgreSQL:

- `duration_ms` — total end-to-end latency
- `iteration_count` — number of critic loops triggered
- `overall_risk_level` — CRITICAL / HIGH / MEDIUM / LOW
- `hallucination_risk` — NONE / LOW / MEDIUM / HIGH
- `grounding_score` — % of claims verified (0–100)
- `status` — COMPLETED / (future: FAILED, TIMEOUT)

### Health Check

```bash
GET /health  →  {"status": "ok"}
```

### Missing Observability (Gaps)

- No distributed tracing (OpenTelemetry not configured)
- No metrics exporter (Prometheus not configured)
- No error alerting (Sentry/Datadog not integrated)
- No structured log aggregation (ELK/Datadog not configured)
- No LLM cost tracking per request

---

## 13. End-to-End Request Walkthrough

### Scenario

> A compliance officer at a digital bank submits: "What complaint resolution timelines must we follow under CBN regulations?"

### Step-by-Step Trace

**Step 1 — HTTP Request received**

```
POST /analysis/analyze-business
{
  "query": "What complaint resolution timelines must we follow under CBN regulations?",
  "organization_context": "Digital bank with retail customers"
}
```

FastAPI validates the request body via `AnalysisRequest` Pydantic model. A new `session_id` UUID is generated (none provided). `ComplianceService(db).analyze()` is called.

---

**Step 2 — LangGraph workflow starts**

`workflow.ainvoke(initial_state)` is called with:

```python
{
    "query": "What complaint resolution timelines...",
    "session_id": "abc-123-...",
    "organization_context": "Digital bank with retail customers",
    "iteration_count": 0,
    "max_iterations": 2,
    "agent_trace": []
}
```

---

**Step 3 — Orchestrator Node**

`run_orchestrator()` calls OpenAI gpt-4o-mini with `ORCHESTRATOR_SYSTEM_PROMPT` + the query.

LLM returns:

```json
{
  "task_breakdown": [
    "identify complaint handling regulations",
    "retrieve CBN consumer protection rules",
    "analyse resolution timelines"
  ],
  "target_regulators": ["CBN"],
  "context_summary": "Query about consumer complaint resolution obligations for a digital bank under CBN supervision.",
  "query_type": "OBLIGATION_ANALYSIS"
}
```

State updated: `target_regulators=["CBN"]`, `agent_trace=[{agent: "orchestrator", status: "completed"}]`

---

**Step 4 — Jurisdiction Node**

`run_jurisdiction_mapping()` calls LLM. Returns:

```json
{
  "applicable_regulators": [
    {
      "regulator": "CBN",
      "rationale": "CBN Consumer Protection Regulations govern complaint handling for licensed financial institutions"
    }
  ],
  "primary_regulator": "CBN",
  "overlap_risks": []
}
```

---

**Step 5 — Research Node**

`RetrievalService.retrieve(query, filter_regulators=["CBN"])` executes the 8-step pipeline:

1. LLM generates 2 legal rephrasings:
   - "mandated timelines for consumer complaint resolution under CBN guidelines"
   - "financial institution obligations for dispute resolution pursuant to CBN Consumer Protection Regulations"

2. For each of the 3 queries → dense embed → BM25 sparse embed → Qdrant hybrid search
   - Retrieves chunks about: Part Five (Complaints Handling), Annexure D (resolution timelines), Part Six (sanctions for non-resolution)

3. Deduplication → cross-encoder reranking → freshness scoring → MMR diversity → contextual compression

Returns 6 highly relevant chunks specifically about complaint procedures.

---

**Step 6 — Reasoning Node**

`run_reasoning()` sends all 6 chunks to LLM with `REASONING_SYSTEM_PROMPT`.

LLM synthesises:

```json
{
  "obligations": [
    {
      "description": "Institutions must resolve declined transaction complaints within 3 working days",
      "citation": "CBN Consumer Protection Regulations, Part Six, Annexure D, Page 39",
      "regulator": "CBN"
    }
  ],
  "prohibitions": [...],
  "conflicts": [],
  "reasoning_summary": "The CBN Consumer Protection Regulations impose specific complaint resolution timelines...",
  "confidence": "HIGH"
}
```

---

**Step 7 — Auditor Node**

`run_audit()` receives the reasoning output and produces a compliance checklist:

```json
{
  "risk_score": 4,
  "risk_level": "MEDIUM",
  "compliance_checklist": [
    {
      "requirement": "Complaint tracking system",
      "status": "UNKNOWN",
      "citation": "Part Five, 6.1"
    },
    {
      "requirement": "Summary Resolution Communication (SRC)",
      "status": "UNKNOWN",
      "citation": "Part Five, 6.3.11"
    }
  ],
  "licensing_requirements": [],
  "recommendations": [
    "Implement a complaint management system with SLA tracking",
    "Send SRC for all resolved complaints"
  ]
}
```

---

**Step 8 — Citation Verifier**

Checks every claim in reasoning + audit output against the 6 retrieved chunks.

- Finds 8 of 9 claims have direct chunk support
- `overall_grounding_score: 89`
- `hallucination_risk: LOW`

---

**Step 9 — Critic Node**

Reviews all outputs. Finds one issue: "Missing analysis of sanctions for non-compliance with timelines."

- `quality_score: 7`
- `overall_assessment: PASS_WITH_REVISIONS`

Since assessment is not "FAIL", `route_after_critic()` returns `"end"`.

---

**Step 10 — Audit Persistence**

`AuditService.create_record()` builds the audit record from the final workflow state and writes to PostgreSQL.

Record saved: `id = a040e06d-...`, `duration_ms = 98320`, `grounding_score = 89`, `risk_level = MEDIUM`.

---

**Step 11 — Response returned**

FastAPI returns the structured JSON response with `audit_id`, `session_id`, `final_report`, `citations`, `agent_trace`, `duration_ms`.

The compliance officer has a citation-backed, auditable compliance report in under 2 minutes.

---

## 14. Engineering Decisions

### Why FastAPI?

- Native async support — critical for concurrent LLM calls and DB operations
- Pydantic v2 integration — automatic request/response validation
- OpenAPI schema auto-generated — instant API documentation at `/docs`
- Lightweight — no ORM framework overhead in the HTTP layer

### Why LangGraph over LangChain Chains?

LangGraph provides **stateful, typed, graph-based** workflow control. This is essential because:

- Agents need to share accumulated state (chunks, reasoning, audit results)
- Conditional routing is needed (critic can loop back to reasoning)
- Each node is independently testable
- State transitions are explicit and auditable

Plain LangChain chains are sequential and don't support conditional back-edges or typed shared state cleanly.

### Why Qdrant with Hybrid Search (Dense + Sparse)?

Pure semantic search (dense vectors) excels at meaning but misses exact terms like regulation names, section numbers, or specific legal phrases. BM25 (sparse) excels at exact term matching. Combining both via RRF fusion captures both:

- Dense: "what are the consumer complaint rules?" → finds semantically related chunks
- Sparse: "CBN CPR Section 6.3.11" → finds exact section references

### Why BAAI/bge-base-en-v1.5?

- 768 dimensions — sufficient resolution for legal text
- Normalized embeddings (cosine = dot product) — Qdrant cosine similarity works correctly
- Runs on CPU — no GPU infrastructure required for MVP
- Strong performance on domain-specific English text

### Why a Cross-Encoder Reranker?

Bi-encoders (like the embedding model) compute query and document embeddings independently. Cross-encoders see both query and document simultaneously via attention, capturing interaction between them. This produces significantly better ranking quality at the cost of being slower (can't pre-compute). Used as a post-retrieval step where latency allows.

### Why gpt-4o-mini over gpt-4o?

For MVP/demo purposes, `gpt-4o-mini`:

- ~10× cheaper than `gpt-4o`
- Sufficient reasoning quality for structured JSON output tasks
- ~2–3× faster response times
- Configurable — swap to `gpt-4o` or `gpt-4-turbo` for production

### Why Python `TypedDict` for LangGraph State (not Pydantic)?

LangGraph's `StateGraph` requires `TypedDict` for state definitions. This is a framework constraint — LangGraph performs internal state merging that is incompatible with Pydantic's validation model.

### Why Synchronous Embeddings (no `await`)?

`sentence-transformers` uses PyTorch under the hood and is CPU-bound (not I/O-bound). Running it synchronously is correct — making it async would add overhead without benefit, and wrapping in `asyncio.run_in_executor` would be premature optimization for MVP.

### Why `total=False` on AgentState?

```python
class AgentState(TypedDict, total=False):
```

`total=False` means all keys are optional. This is correct because the state is built incrementally — early nodes don't have `reasoning_result` or `audit_result` yet. Without `total=False`, TypedDict would require all keys to be present at all times.

---

## 15. Technical Debt & Risks

### P0 — Must fix before production

| Issue                               | Risk                                                         | Location                       |
| ----------------------------------- | ------------------------------------------------------------ | ------------------------------ |
| **No authentication**               | Any user can submit queries and read all audit records       | All API routes                 |
| **No rate limiting**                | LLM API costs unbounded; potential DoS via expensive queries | `/analysis/analyze-business`   |
| **`create_all` instead of Alembic** | Schema changes will not migrate existing databases           | `app/db/postgres.py:init_db()` |
| **OPENAI_API_KEY in .env**          | If `.env` is committed or exposed, key is leaked             | `.env` / deployment            |

### P1 — Should fix soon

| Issue                               | Risk                                                                               | Location                      |
| ----------------------------------- | ---------------------------------------------------------------------------------- | ----------------------------- |
| **No test suite**                   | Regressions undetected; agents untestable in isolation                             | `tests/` (empty)              |
| **No CORS configuration**           | Browser-based frontends blocked or open to all origins                             | `app/main.py`                 |
| **Reranker cold start**             | First request takes 4+ minutes to download 2.27GB model                            | `app/utils/reranking.py`      |
| **Orchestrator prompt duplication** | Two versions of `ORCHESTRATOR_SYSTEM_PROMPT` in same file (second overrides first) | `app/prompts/orchestrator.py` |
| **Redis dormant**                   | Provisioned but unused — no caching or session persistence                         | `docker-compose.yml`          |

### P2 — Technical debt

| Issue                                       | Notes                                                                                           |
| ------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| **Inline Pydantic models in routes**        | `AnalysisRequest` defined directly in `analysis.py` — should move to `app/models/requests.py`   |
| **No request ID / correlation ID**          | Multi-agent logs are hard to trace across concurrent requests                                   |
| **Synchronous embedding blocks event loop** | `embed_text()` is CPU-bound synchronous; should use `run_in_executor` for production throughput |
| **`max_iterations` hardcoded to 2**         | Should be a request-level parameter                                                             |
| **Chunking uses approximate token count**   | `MAX_CHUNK_SIZE = 1000` in chars/4 — real token counts differ                                   |
| **No embedding model versioning**           | If model changes, re-ingestion of all documents required                                        |
| **Qdrant `qdrant/qdrant:latest` tag**       | Unpinned version in docker-compose risks breaking changes on pull                               |

### Bottlenecks

1. **LLM sequential pipeline**: 7 agents × (30–180s each) = 90–120s total. Not parallelizable without architectural changes (each agent depends on prior output).
2. **Cross-encoder reranker on CPU**: 2.27GB model, CPU inference — scales poorly under concurrent load.
3. **Single Qdrant instance**: No replication; single point of failure for retrieval.
4. **Synchronous database session per request**: Connection pool (size=10, max_overflow=20) limits concurrency.

---

## 16. Future Roadmap

### Near-Term (MVP → Production)

1. **Authentication & RBAC** — JWT tokens, user management, organization-level access control
2. **Alembic migrations** — versioned database schema management
3. **Test suite** — unit tests for agents (mock LLM), integration tests for API routes, RAG pipeline evaluation
4. **Rate limiting** — per-user and per-organization request quotas
5. **Model warm-up** — pre-load reranker and embedding models at startup, not on first request
6. **Streaming responses** — stream agent progress to the client in real-time via SSE/WebSocket

### Medium-Term (Scale & Quality)

7. **Chainlit frontend** — Regulatory Intelligence Console with agent trace visualization
8. **Redis session management** — persistent conversation sessions, query caching
9. **More regulators** — FCCPC, NITDA, NDPA, BOFIA documents
10. **Compliance gap analysis endpoint** — upload company policy docs; compare against regulations
11. **Evaluation framework** — RAG evaluation with RAGAS (faithfulness, answer relevance, context precision)
12. **LLM cost tracking** — per-request token usage tracked and stored
13. **Async embedding** — `run_in_executor` for CPU-bound embedding to unblock event loop

### Long-Term (Platform)

14. **Multi-tenancy** — Organization isolation, custom document collections per client
15. **Regulatory monitoring** — watch regulator websites for new circulars/guidelines; auto-ingest and notify
16. **Compliance workflow integration** — export reports to compliance management systems (e.g., Jira, Confluence)
17. **Fine-tuned embedding model** — domain-adapted embedding model trained on Nigerian legal text
18. **Graph-based regulatory knowledge** — regulatory knowledge graph linking regulations, sections, entities
19. **Audit trail API for third parties** — signed, exportable audit records for regulatory submission
20. **Mobile app** — compliance officer mobile interface for on-the-go analysis

---

## 17. Local Development Setup

### Prerequisites

| Requirement    | Version | Install                                            |
| -------------- | ------- | -------------------------------------------------- |
| Python         | 3.12+   | `brew install python@3.12`                         |
| uv             | Latest  | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Docker Desktop | Latest  | [docker.com](https://docker.com)                   |
| Tesseract OCR  | Latest  | `brew install tesseract`                           |

### 1. Clone and Install

```bash
git clone <repo-url>
cd regulatory-intelligence-platform

# Create virtual environment and install all dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

### 2. Configure Environment

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

# LLM
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-<your-key>
OPENAI_MODEL=gpt-4o-mini

# Embedding
EMBEDDING_MODEL_NAME=BAAI/bge-base-en-v1.5
EMBEDDING_DIMENSION=768
```

### 3. Start Infrastructure

```bash
docker compose up -d

# Verify all services are running
docker compose ps

# Verify Qdrant
curl http://localhost:6333/healthz

# Verify PostgreSQL
docker exec -it postgres psql -U regplatform -d regulatory_db -c "\dt"
```

### 4. Start the Application

```bash
uvicorn app.main:app --reload
```

On startup you should see:

```
Starting up Regulatory Intelligence Platform...
PostgreSQL tables ready
Qdrant collection ready
```

### 5. Ingest a Regulation Document

```bash
curl -X POST http://localhost:8000/regulations/upload \
  -F "file=@/path/to/CBN_Consumer_Protection.pdf" \
  -F "regulator=CBN" \
  -F "document_type=Regulation" \
  -F "issued_date=2019-12-20"
```

### 6. Test the Analysis Endpoint

```bash
curl -s -X POST http://localhost:8000/analysis/analyze-business \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What complaint resolution timelines apply to a digital bank?",
    "organization_context": "Digital bank with retail customers"
  }' | python3 -m json.tool
```

### 7. Access PostgreSQL Audit Records

```bash
# Connect to database
docker exec -it postgres psql -U regplatform -d regulatory_db

# Useful queries
SELECT id, session_id, overall_risk_level, grounding_score, duration_ms, created_at
FROM audit_records
ORDER BY created_at DESC
LIMIT 10;

SELECT * FROM documents;

\q
```

### 8. Developer Workflow

```bash
# Check Qdrant indexed chunks
curl -X POST http://localhost:6333/collections/regulations/points/scroll \
  -H "Content-Type: application/json" \
  -d '{"limit": 10, "with_payload": true, "with_vector": false}'

# Tail application logs while running a test
# (run uvicorn in foreground, then curl in another terminal)

# Reset Qdrant collection (drops all indexed data — re-ingest required)
# python scripts/reset_collection.py

# Install a new dependency
uv add <package-name>
```

### 9. Switching to Local LLM (Ollama)

```bash
# Install Ollama: https://ollama.com
# Pull models
ollama pull qwen2.5:14b
ollama pull qwen2.5:7b

# Update .env
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434
LLM_MODEL_NAME=qwen2.5:14b
LLM_SMALL_MODEL_NAME=qwen2.5:7b
```

### Common Issues

| Issue                          | Cause                               | Fix                                                          |
| ------------------------------ | ----------------------------------- | ------------------------------------------------------------ |
| First request takes 4+ minutes | Reranker model downloading (2.27GB) | Wait; subsequent requests are fast (model cached)            |
| `No text extracted from PDF`   | Scanned image PDF                   | Ensure Tesseract is installed: `brew install tesseract`      |
| `409 Conflict` on upload       | Same PDF already ingested           | Document already in system; this is by design                |
| `Connection refused :6333`     | Qdrant not running                  | `docker compose up -d qdrant`                                |
| `422 Unprocessable Entity`     | Wrong request body                  | Check required fields with `curl http://localhost:8000/docs` |

---

## 18. Glossary

### Technical Terms

| Term                     | Definition                                                                                                                                                                              |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Agent**                | An LLM-powered module with a specific role in the workflow (e.g., "Auditor Agent"). Each agent receives structured input, calls an LLM, and returns structured output.                  |
| **AgentState**           | A Python `TypedDict` that holds all data shared across agents in the LangGraph workflow. Each node reads from and writes to this shared state.                                          |
| **Async**                | A Python programming pattern (`async def`, `await`) that allows multiple operations (DB calls, LLM calls) to run concurrently without blocking, using Python's event loop.              |
| **BM25**                 | "Best Match 25" — a classic information retrieval scoring formula that scores documents based on term frequency and inverse document frequency. Used for keyword-based search.          |
| **Cross-encoder**        | A neural network that takes a query and a document as joint input and scores their relevance. More accurate than bi-encoders but slower (can't pre-compute document scores).            |
| **Dense vector**         | A fixed-length array of floating point numbers representing semantic meaning of text. Two semantically similar texts produce similar dense vectors.                                     |
| **Dependency injection** | A design pattern where dependencies (e.g., database sessions) are injected into functions/classes from outside rather than created internally. FastAPI's `Depends()` implements this.   |
| **Embedding**            | The process of converting text into a numeric vector representation. Used to enable semantic search.                                                                                    |
| **Hallucination**        | When an LLM generates plausible-sounding but factually incorrect information, in this case fabricating regulatory citations that do not exist.                                          |
| **Hybrid search**        | A retrieval technique combining dense (semantic) and sparse (keyword) search results, typically via Reciprocal Rank Fusion.                                                             |
| **LangGraph**            | A library built on top of LangChain for creating stateful, directed-graph-based multi-agent AI workflows.                                                                               |
| **Lifespan**             | A FastAPI feature (`asynccontextmanager`) for running code on application startup and shutdown.                                                                                         |
| **MMR**                  | Maximal Marginal Relevance — an algorithm for selecting diverse results by penalizing candidates that are too similar to already-selected results.                                      |
| **Pydantic**             | A Python library for data validation using type annotations. Used for request/response models and configuration settings.                                                               |
| **RAG**                  | Retrieval-Augmented Generation — an AI architecture that retrieves relevant context from a knowledge base before asking an LLM to generate an answer, grounding responses in real data. |
| **RRF**                  | Reciprocal Rank Fusion — a technique for combining ranked lists from multiple retrieval systems into a single merged ranking.                                                           |
| **Sparse vector**        | A vector where most values are zero, with non-zero values at positions corresponding to specific vocabulary terms. BM25 produces sparse vectors.                                        |
| **SQLAlchemy**           | Python ORM (Object-Relational Mapper) for interacting with relational databases using Python objects instead of raw SQL.                                                                |
| **TypedDict**            | A Python type hint construct for dictionaries with known, typed keys. Used for LangGraph's `AgentState`.                                                                                |
| **uvicorn**              | An ASGI (Asynchronous Server Gateway Interface) web server for Python. Runs the FastAPI application.                                                                                    |
| **uv**                   | A fast Python package manager and virtual environment tool (replacement for pip + venv).                                                                                                |

### Domain / Business Terms

| Term                | Definition                                                                                                                                               |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **AML/CFT**         | Anti-Money Laundering / Countering the Financing of Terrorism — regulatory obligations for financial institutions                                        |
| **BOFIA**           | Banks and Other Financial Institutions Act — primary legislation governing banks in Nigeria                                                              |
| **CBN**             | Central Bank of Nigeria — primary regulator for banks, payment service providers, and financial institutions                                             |
| **CAMA**            | Companies and Allied Matters Act — governs corporate entities in Nigeria                                                                                 |
| **Compliance gap**  | A specific area where a business's current operations or policies fall short of regulatory requirements                                                  |
| **FCCPC**           | Federal Competition and Consumer Protection Commission — consumer protection regulator                                                                   |
| **FIRS**            | Federal Inland Revenue Service — Nigeria's federal tax authority                                                                                         |
| **Fintech**         | Financial technology — companies using technology to deliver financial services                                                                          |
| **Grounding score** | A metric (0–100%) produced by the Citation Verifier agent indicating what percentage of claims in the analysis are backed by retrieved regulatory text.  |
| **KYC**             | Know Your Customer — regulatory obligation to verify customer identity                                                                                   |
| **NDIC**            | Nigeria Deposit Insurance Corporation — regulates deposit insurance for banks                                                                            |
| **NDPA**            | Nigeria Data Protection Act — data protection regulation                                                                                                 |
| **NITDA**           | National Information Technology Development Agency — IT and data governance regulator                                                                    |
| **PSB**             | Payment Service Bank — a category of licensed institution under CBN regulations                                                                          |
| **SEC Nigeria**     | Securities and Exchange Commission Nigeria — regulates capital markets and investment products                                                           |
| **SRC**             | Summary Resolution Communication — a required communication to customers upon resolving their complaint, mandated by CBN Consumer Protection Regulations |

### Internal Terminology

| Term                       | Definition                                                                                                                                                                    |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Audit record**           | A PostgreSQL row in `audit_records` capturing the complete state of a workflow run — all agent outputs, citations, timing, and risk scores.                                   |
| **Audit trace**            | The `agent_trace` field in an audit record — an ordered list showing which agents executed and in what sequence.                                                              |
| **Chunk**                  | A semantically coherent section of a regulatory document, produced by the chunking pipeline and stored as a vector in Qdrant.                                                 |
| **Contextual compression** | Step 7 of the RAG pipeline — using an LLM to reduce each retrieved chunk to only the sentences relevant to the query.                                                         |
| **Critic loop**            | When the Critic agent assigns `overall_assessment: FAIL`, the workflow routes back to the Reasoning agent for refinement. Max 2 iterations by default.                        |
| **Freshness penalty**      | A score multiplier (0.80–1.00) applied to chunks based on the age of their source document — older documents are ranked slightly lower.                                       |
| **Ingestion pipeline**     | The full process of converting a PDF into indexed, searchable vectors: parse → chunk → embed → store.                                                                         |
| **Query expansion**        | Step 1 of the RAG pipeline — using an LLM to generate 2 legal rephrasings of the user's query, improving retrieval recall.                                                    |
| **Session**                | A UUID linking multiple `/analyze-business` calls for the same investigation. In MVP, session IDs are request-scoped (one per call unless provided explicitly by the caller). |
| **Workflow**               | The compiled LangGraph `StateGraph` that orchestrates the 7-agent sequence for a single compliance analysis request.                                                          |
