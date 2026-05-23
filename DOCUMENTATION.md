# Regulatory Intelligence Platform — Technical Documentation

> **Audience**: Developers · Product Managers · Executives · Designers · QA Engineers · New Hires
> **Version**: 0.1.0 (MVP)
> **Last Updated**: May 2026

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

### What It Is

The **Regulatory Intelligence Platform** is an AI-powered compliance intelligence system purpose-built for Nigerian financial regulation. It is designed for fintechs, banks, insurance companies, digital lenders, capital market operators, and legal or compliance teams who need rapid, reliable answers to regulatory questions.

When a user describes a business model, product, or planned operation, the platform does not simply look up a FAQ. Instead, it triggers a **6-node LangGraph multi-agent AI workflow** that:

- decomposes the query
- identifies every Nigerian regulator with jurisdiction
- retrieves the most relevant chunks from a vetted regulatory document library
- performs legal reasoning over those chunks
- generates a structured compliance report with risk scores, obligations, prohibitions, compliance gaps, and a prioritised action checklist
- verifies every claim against evidence before returning the result
- and runs an adversarial quality review that can trigger a full re-run if quality is insufficient

**Every output is traceable to a specific regulation, section, and page number.** No legal conclusions are generated from LLM memory alone — all claims must be grounded in retrieved regulatory text.

### Core Mission

> Enable any business in Nigeria to understand its regulatory obligations, licensing requirements, and compliance risks — in minutes, not weeks — with the same depth as a qualified compliance officer.

### Primary Users

| User | Need |
|---|---|
| **Fintech founders / CTOs** | Understand licence requirements before building |
| **Compliance officers** | Rapid compliance gap analysis against specific regulations |
| **Legal teams** | Citation-backed regulatory research with audit trails |
| **Product managers** | Identify which features trigger which regulatory obligations |
| **Investors / due diligence teams** | Assess portfolio company regulatory risk |
| **New hires / onboarding** | Quickly understand applicable regulatory landscape |

### Key Value Proposition

Traditional regulatory research in Nigeria requires:
- Access to expensive compliance lawyers
- Hours of reading dense legal documents
- Manual cross-referencing across CBN, SEC, NDIC, FIRS, and other bodies
- No automated audit trail

This platform compresses that to ~60–120 seconds with a structured, citation-backed report that can be audited end-to-end.

---

## 2. Problem Statement

### The Industry Pain

Nigeria's financial regulatory landscape is **fragmented, overlapping, and fast-changing**:

- **CBN** regulates payments, banking, wallets, mobile money, agent banking, forex, and microfinance banks
- **SEC Nigeria** governs capital markets, investment products, VASPs, and collective investment schemes
- **NDIC** oversees deposit insurance and bank resolution
- **FIRS** enforces corporate tax, VAT, withholding tax, and stamp duties
- **FCCPC** covers consumer protection and competition
- **NDPA / NITDA** regulate data protection and IT standards
- **EFCC / NFIU** enforce AML/CFT

A single fintech product — say, a mobile wallet that also offers yield-bearing savings — may simultaneously trigger CBN (wallet), SEC (investment scheme), NDIC (deposit insurance), FIRS (withholding tax), and NDPA (data protection) obligations. Missing one can lead to:

- Regulatory fines
- Licence revocation
- Criminal liability for directors
- Forced product shutdown
- Reputational damage

### Why Existing Solutions Fail

| Approach | Limitation |
|---|---|
| Hire external lawyers | Expensive (₦200k–₦500k/hour), slow (days/weeks), not scalable |
| Internal compliance teams | Expertise gap, manual research, non-auditable |
| Generic legal AI (ChatGPT, etc.) | Hallucinated references, not grounded in actual Nigerian documents, no citations |
| Reading regulations yourself | Requires deep legal expertise, time-consuming |

### Consequences of Non-Compliance

- CBN fines can reach 2% of annual turnover plus ₦2 million/day for ongoing breaches
- SEC sanctions include suspension of licences and revocation of registrations
- NDPA non-compliance can result in fines of up to 2% of annual global turnover
- Criminal liability under EFCC/MLPPA can include imprisonment of directors

---

## 3. Product Overview

### Main Capabilities

| Capability | Description |
|---|---|
| **Business Model Analysis** | Submit a description of any Nigerian business or fintech product; receive a full structured compliance report |
| **Compliance Gap Analysis** | Describe your current compliance posture; identify what controls, licences, and filings are missing |
| **Regulatory Document Ingestion** | Upload CBN, SEC, NDIC, FIRS, and other regulatory PDFs; system parses, chunks, embeds, and indexes them |
| **Audit Trail** | Every analysis is persisted to PostgreSQL with the full agent decision trace for explainability |
| **Session History** | All analyses in a single console session are grouped by session ID for easy retrieval |
| **Real-Time Progress** | The Chainlit UI shows live agent step progress as the workflow executes |
| **Citation Grounding** | Every legal conclusion traces back to a document, section, and page — hallucinated references are flagged |

### User Journeys

#### Journey 1: Business Model Analysis

1. User opens the Regulatory Intelligence Console at `http://localhost:8080`
2. User clicks **Analyze Business Model**
3. User types: *"We are launching a digital lending app in Nigeria offering SME loans via mobile. We use credit scoring and collect repayments via direct debit."*
4. System queues the workflow and shows live agent progress (7 named steps)
5. After ~60–90 seconds, the system returns:
   - Applicable Regulators: `CBN` · `FIRS` · `EFCC / SCUML`
   - Risk Level: **HIGH**
   - 4 obligations (CBN licence, KYC/AML, credit bureau reporting, data protection)
   - 2 prohibitions (no deposit-taking without DMB/MFB licence)
   - Licensing Requirements: Finance Company Licence (CBN), or MFB licence
   - Compliance Checklist with 8 items
   - 7 citations from CBN Consumer Protection, BOFIA 2020, and NDPA 2023

#### Journey 2: Compliance Gap Analysis

1. User clicks **Check Compliance Gaps**
2. User types: *"We are a CBN-licensed payment processor. We have KYC, an AML policy, and PCI-DSS certification. We recently added a fixed-yield savings product."*
3. System identifies: the savings product triggers SEC Nigeria collective investment scheme registration, which is missing → flagged as CRITICAL compliance gap

#### Journey 3: Document Ingestion (Admin/Developer)

1. Developer POSTs to `POST /regulations/upload` with a PDF and regulator metadata
2. System parses the PDF (PyMuPDF → pdfplumber → Tesseract OCR fallback)
3. Chunks the text preserving section numbers, hierarchy, and page references
4. Generates dense (768-dim) and sparse (BM25) embeddings
5. Stores both vector types in Qdrant under the `regulations` collection
6. Saves document metadata to PostgreSQL

---

## 4. High-Level System Architecture

### Architectural Pattern

The system is a **modular monolith** — a single Python process with clean internal layer separation. It is not a microservices architecture at this stage; all computation happens within one FastAPI application. The separation is conceptual (by layer and responsibility) rather than deployment-based.

This was intentional for MVP: faster development, simpler debugging, no distributed tracing overhead.

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     REGULATORY INTELLIGENCE PLATFORM                │
│                                                                     │
│  ┌──────────────────────┐          ┌───────────────────────────┐   │
│  │   Chainlit UI        │          │     FastAPI Backend        │   │
│  │   Port 8080          │◄────────►│     Port 8000             │   │
│  │   (chainlit_app.py)  │  httpx   │     (app/main.py)         │   │
│  └──────────────────────┘          └────────────┬──────────────┘   │
│                                                  │                  │
│                          ┌───────────────────────▼──────────┐      │
│                          │      LangGraph Workflow           │      │
│                          │   (app/graph/workflow.py)         │      │
│                          │                                   │      │
│                          │  [orchestrator_jurisdiction]      │      │
│                          │           │                       │      │
│                          │  [research] ──► [reasoning]       │      │
│                          │           │         │             │      │
│                          │       [auditor] ◄───┘             │      │
│                          │           │                       │      │
│                          │  [citation_verifier]              │      │
│                          │           │                       │      │
│                          │      [critic] ────► END           │      │
│                          │           │                       │      │
│                          │      (loop back to reasoning      │      │
│                          │       if FAIL, max 2x)            │      │
│                          └───────────────────────────────────┘      │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   Qdrant     │  │  PostgreSQL  │  │   Redis                  │  │
│  │   Port 6333  │  │  Port 5432   │  │   Port 6379              │  │
│  │   Dense+BM25 │  │  Audit + Docs│  │   (provisioned, unused)  │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    External Services                          │  │
│  │  OpenAI API (gpt-4o-mini)  │  Ollama (local, optional)       │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Layer Separation

```
Request → API Layer (FastAPI routes)
            ↓
        Service Layer (ComplianceService, IngestionService, AuditService)
            ↓
        Graph/Agent Layer (LangGraph nodes → individual agents)
            ↓
        Repository Layer (VectorRepository, AuditRepository, DocumentRepository)
            ↓
        Database Layer (Qdrant, PostgreSQL)
```

Each layer has **one responsibility** and does not reach past its adjacent layer.

---

## 5. Detailed Backend Documentation

### Repository Root Structure

```
Regulatory-Intelligence-Platform/
├── app/                             # All backend Python source code
├── data/                            # Local document storage (raw PDFs, ingested files)
├── tests/                           # Pytest test suite
├── scripts/                         # Utility scripts (reset_collection.py, etc.)
├── .chainlit/                       # Chainlit config + i18n translations
├── .env                             # Local environment variables (not committed)
├── .env.example                     # Environment variable template (committed)
├── .gitignore
├── chainlit_app.py                  # Chainlit frontend — Regulatory Intelligence Console (614 lines)
├── chainlit.md                      # Chainlit welcome screen content
├── docker-compose.yml               # PostgreSQL 16, Qdrant, Redis containers
├── Example-Queries.md               # 50 example queries (25 business model, 25 compliance gap)
├── DOCUMENTATION.md                 # This file — full technical documentation
├── README.md                        # Project overview and quick-start
├── pyproject.toml                   # Python project metadata + dependencies (uv)
├── uv.lock                          # Locked dependency tree
├── server.sh                        # Server management script (start / stop / status)
├── test_routes.py                   # Full async route test suite (12 tests)
└── test_smoke.sh                    # Bash smoke test suite for CI
```

### Application Folder Structure

```
app/
├── main.py                          # FastAPI app: lifespan, CORS, router registration
├── core/
│   └── config.py                    # Pydantic Settings loaded from .env
├── api/
│   ├── dependencies.py              # Optional + required auth dependencies
│   └── routes/
│       ├── health.py                # GET /health
│       ├── regulations.py           # POST /regulations/upload, GET /regulations/, DELETE /regulations/{id}
│       ├── analysis.py              # POST /analyze/analyze-business, /analyze/compliance-gap, GET /analyze/report/{id}, GET /analyze/report/{id}/stream
│       └── audit.py                 # GET /audit/trace/{id}, GET /audit/session/{id}
├── graph/
│   ├── state.py                     # AgentState TypedDict — shared workflow state
│   ├── nodes.py                     # LangGraph node functions (one per agent step)
│   └── workflow.py                  # StateGraph construction, edge wiring, compile()
├── agents/
│   ├── orchestrator.py              # run_orchestrator() — query decomposition
│   ├── jurisdiction_mapper.py       # run_jurisdiction_mapping() — regulator identification
│   ├── reasoning.py                 # run_reasoning() — legal synthesis
│   ├── auditor.py                   # run_audit() — risk assessment + gaps
│   ├── citation_verifier.py         # run_citation_verification() — grounding check
│   └── critic.py                    # run_critic() — adversarial quality review
├── prompts/
│   ├── orchestrator.py              # ORCHESTRATOR_SYSTEM_PROMPT
│   ├── jurisdiction_mapper.py       # JURISDICTION_MAPPER_SYSTEM_PROMPT
│   ├── reasoning.py                 # REASONING_SYSTEM_PROMPT
│   ├── auditor.py                   # AUDITOR_SYSTEM_PROMPT
│   ├── citation_verifier.py         # CITATION_VERIFIER_SYSTEM_PROMPT
│   └── critic.py                    # CRITIC_SYSTEM_PROMPT
├── services/
│   ├── compliance_service.py        # Orchestrates LangGraph invoke + audit persistence
│   ├── ingestion_service.py         # Full PDF → chunk → embed → store pipeline
│   ├── retrieval_service.py         # 7-step RAG pipeline
│   ├── embedding_service.py         # Dense embeddings (SentenceTransformers)
│   ├── sparse_embedding_service.py  # BM25 sparse embeddings (fastembed)
│   └── audit_service.py             # AuditRecord CRUD + session queries
├── repositories/
│   ├── vector_repository.py         # Qdrant upsert + hybrid search + RRF fusion
│   ├── document_repository.py       # DocumentRecord CRUD + hash dedup
│   └── audit_repository.py          # AuditRecord CRUD + session listing
├── models/
│   ├── requests.py                  # Pydantic request models (BusinessAnalysisRequest, etc.)
│   ├── responses.py                 # Pydantic response models (ReportStatusResponse, etc.)
│   └── database_models.py           # SQLAlchemy ORM (DocumentRecord, AuditRecord)
├── db/
│   ├── postgres.py                  # Async SQLAlchemy engine, session factory, Base, init_db()
│   └── qdrant.py                    # AsyncQdrantClient singleton, collection init with dense+sparse
└── utils/
    ├── llm_client.py                # Unified OpenAI/Ollama async chat client
    ├── cost_tracker.py              # Per-request token cost tracking via contextvars
    ├── chunking.py                  # Section-aware legal document chunker
    ├── parsers.py                   # PDF parsing: PyMuPDF + pdfplumber + Tesseract OCR
    ├── reranking.py                 # Cross-encoder reranking (BAAI/bge-reranker-v2-m3)
    └── citations.py                 # Citation formatting utilities
```

### Startup Lifecycle (app/main.py)

On startup (`lifespan` async context manager), in order:

1. `await init_db()` — creates PostgreSQL tables via SQLAlchemy `create_all` (idempotent)
2. `await init_qdrant_collection()` — creates the `regulations` collection with dense+sparse vector config if it doesn't exist
3. `_get_reranker()` runs in an executor (thread pool) to pre-load the 2.27 GB cross-encoder model synchronously without blocking the event loop

This ensures all I/O-heavy initialisation completes before the first request is accepted.

### Configuration (app/core/config.py)

All configuration is loaded from `.env` via `pydantic-settings`. Accessed application-wide via the `settings` singleton:

```python
from app.core.config import settings
settings.postgres_url      # computed property
settings.openai_api_key
settings.qdrant_collection_name
settings.embedding_model_name
```

The `Settings` class uses `extra="ignore"` so undeclared `.env` variables do not raise errors. All values have sensible defaults to prevent crashes in CI environments without a `.env` file.

### Request Lifecycle (Analysis)

```
POST /analyze/analyze-business
        │
        ▼
FastAPI validates BusinessAnalysisRequest (Pydantic)
        │
        ▼
Background task _run_workflow() is scheduled
        │
        ▼ (response returned immediately)
AnalysisInitiatedResponse { report_id, workflow_status: "pending" }
        │
        │  (background)
        ▼
ComplianceService.analyze()
        │
        ▼
workflow.ainvoke(initial_state)  — runs full LangGraph graph
        │
        ▼
AuditService.create_record()     — persists to PostgreSQL
        │
        ▼
_reports[report_id] = { status: "completed", report: result }

        (meanwhile, UI polls)
GET /analyze/report/{report_id}
        │
        ▼
ReportStatusResponse { status, report, audit_id, llm_metrics, ... }
```

### Background Task Pattern

The analysis workflow takes 60–120 seconds. FastAPI's `BackgroundTasks` is used to schedule `_run_workflow()` as a fire-and-forget task. The client receives `HTTP 200` immediately with a `report_id`, then polls `GET /analyze/report/{report_id}` every 3 seconds.

Results are stored in `_reports: dict[str, dict]` — an in-memory Python dictionary on the process. This is intentionally simple for the MVP; the plan is to replace it with Redis in production.

### Authentication (app/api/dependencies.py)

Two dependency types are defined:

- `OptionalUser` — reads Bearer token if present; allows unauthenticated access. Used on all current routes.
- `CurrentUser` — raises `HTTP 401` if no token provided. Reserved for future protected routes.

Token verification is scaffolded but not fully implemented — it currently returns a placeholder dict. JWT validation against a user database is the intended implementation.

### Error Handling

Each API route uses `HTTPException` with explicit status codes:

| Code | Condition |
|---|---|
| `400` | Non-PDF file uploaded |
| `404` | Report or audit record not found |
| `409` | Duplicate document (identical SHA256 hash) |
| `422` | Document parsing failed (zero text extracted) |
| `500` | Unhandled exception (surfaced via `error` field) |

Agents individually catch `json.JSONDecodeError` and return structured fallback dicts rather than propagating exceptions. This prevents a malformed LLM response from crashing the entire workflow.

### Middleware

`CORSMiddleware` is the only middleware applied. Origins are configured via `settings.allowed_origins` (defaults to `localhost:3000` and `localhost:8000`). Production deployments should restrict this to the actual frontend domain.

### Async Strategy

The entire application is async-first:
- All database queries use SQLAlchemy `async_sessionmaker` + `AsyncSession`
- Qdrant uses `AsyncQdrantClient`
- All LLM calls use `httpx.AsyncClient`
- The orchestrator and jurisdiction mapper run in **parallel** via `asyncio.gather()` — saving 8–12 seconds per request
- The cross-encoder reranker is CPU-bound (no async API) and is called synchronously inside the async node function — this blocks the event loop briefly. The startup loader pre-warms the model to avoid first-request penalties

---

## 6. Frontend Documentation

### Technology

The frontend is built with **Chainlit 2.11.1** — a Python-native framework for building conversational AI interfaces. It connects to the FastAPI backend via httpx.

The UI is intentionally positioned as a **Regulatory Intelligence Console**, not a chatbot. It does not accept arbitrary free-text conversation — it routes all interactions through structured workflows.

### Session Management

When a user opens a new browser tab or starts a new chat:

1. `@cl.on_chat_start` fires
2. A fresh `uuid.uuid4()` is generated as `console_session_id`
3. This UUID is stored in `cl.user_session` — a per-connection server-side session store
4. Every API request payload includes `"session_id": console_session_id`
5. All analyses in one browser session share the same `session_id` in audit records
6. Opening a new chat creates a new UUID → separate audit history

### Interaction Flow

```
User opens console
        │
        ▼
on_chat_start(): health check, generate UUID, render welcome screen with action buttons
        │
User clicks "Analyze Business Model"
        │
        ▼
on_analyze_action(): sets mode="analyze" in user_session, prompts for description
        │
User types description and presses Enter
        │
        ▼
on_message(): reads mode, validates length (>=20 chars), calls _run_analysis()
        │
        ▼
_run_analysis():
  1. POST to /analyze/analyze-business
  2. Display report_id + "Running workflow..." message
  3. Open cl.Step("Multi-Agent Workflow") with live update
  4. Poll /analyze/report/{id} every 3s for up to 60 attempts (3 min)
  5. On "completed": close step, render individual agent steps, render report
  6. Display follow-up actions
```

### Report Rendering

The `_build_report_message()` function assembles the full structured report as Markdown. It renders:

- Risk level with colour badge
- Risk score bar (`█████░░░░░  5/10`)
- Applicable regulators as inline code badges
- Executive summary paragraph
- Obligations, prohibitions, permissions (lists)
- Regulatory conflicts (if detected)
- Licensing requirements (with regulator badges and legal basis)
- Compliance gaps (with risk levels and remediation actions)
- Compliance checklist (MET / UNMET / UNKNOWN)
- Recommendations
- Regulatory citations (with source document, section, page)
- Audit metadata table (Audit ID, Session ID, Grounding Score, Hallucination Risk, Iterations)

### Chainlit Steps

Agent execution is visualised as collapsible `cl.Step` elements:

- `Multi-Agent Workflow` — top-level container step
- One step per agent in the `agent_trace` array
- `Sources Retrieved` — lists citation documents with page numbers
- `Workflow Metrics` — token counts, LLM calls, cost in USD

### API Communication

All httpx clients use:
- `follow_redirects=True` (FastAPI redirects `/regulations` → `/regulations/` with HTTP 307)
- Appropriate timeouts: 10s for GET requests, 30s for POST submissions, 3s poll retries

---

## 7. Database Documentation

### Databases Used

| Database | Purpose | Client |
|---|---|---|
| **PostgreSQL 16** | Persistent audit records, document registry | SQLAlchemy async + asyncpg |
| **Qdrant** | Vector embeddings for regulatory text retrieval | AsyncQdrantClient |
| **Redis 7** | Provisioned, reserved for session state and caching | Not yet used |

### PostgreSQL Schema

#### documents table

Tracks every regulatory PDF that has been ingested.

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` | Auto-increment primary key |
| `file_name` | `VARCHAR(512)` | Original filename |
| `file_hash` | `VARCHAR(64)` | SHA256 hash, unique, indexed — prevents duplicate ingestion |
| `regulator` | `VARCHAR(100)` | e.g. "CBN", "SEC Nigeria" |
| `document_type` | `VARCHAR(100)` | e.g. "Regulation", "Circular", "Act" |
| `total_pages` | `INTEGER` | Page count from parser |
| `chunks_ingested` | `INTEGER` | Number of chunks stored in Qdrant |
| `ingested_at` | `TIMESTAMPTZ` | UTC timestamp, auto-populated |
| `notes` | `TEXT` | Optional free-text notes |

#### audit_records table

Full audit trail for every compliance analysis. Each row represents one complete workflow execution.

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID` | Primary key, auto-generated |
| `session_id` | `UUID` | Indexed — links records to a user session |
| `query` | `TEXT` | The original user query |
| `organization_context` | `TEXT` | Optional context provided with the query |
| `target_regulators` | `JSON` | List of regulators identified by jurisdiction agent |
| `agent_trace` | `JSON` | Array of {agent, status} objects |
| `jurisdiction_result` | `JSON` | Full output of the jurisdiction mapping agent |
| `reasoning_result` | `JSON` | Full output of the reasoning agent |
| `audit_result` | `JSON` | Full output of the compliance auditor agent |
| `citation_result` | `JSON` | Full output of the citation verifier agent |
| `critic_result` | `JSON` | Full output of the critic agent |
| `final_report` | `JSON` | Assembled final compliance report |
| `overall_risk_level` | `VARCHAR(20)` | CRITICAL / HIGH / MEDIUM / LOW |
| `hallucination_risk` | `VARCHAR(20)` | NONE / LOW / MEDIUM / HIGH |
| `grounding_score` | `INTEGER` | 0–100: percentage of verified citations |
| `iteration_count` | `INTEGER` | Number of reasoning loops (max 2) |
| `status` | `VARCHAR(20)` | Always "COMPLETED" for now |
| `duration_ms` | `INTEGER` | Workflow wall-clock time in milliseconds |
| `created_at` | `TIMESTAMPTZ` | Server-side default timestamp |

### Qdrant Collection: regulations

The `regulations` collection stores regulatory text chunks as hybrid (dense + sparse) vectors.

**Vector configuration:**

| Vector name | Type | Dimensions | Distance | Model |
|---|---|---|---|---|
| `dense` | Float | 768 | Cosine | `BAAI/bge-base-en-v1.5` |
| `sparse` | Sparse | Variable | — | `Qdrant/bm25` (BM25) |

**Point payload (metadata per chunk):**

| Field | Description |
|---|---|
| `text` | The actual regulatory text of the chunk |
| `source` | Document file name |
| `page` | 1-based page number |
| `section` | Section number (e.g. "Section 23", "3.2") |
| `title` | Section title |
| `hierarchy` | List of parent headings (e.g. ["PART II", "CHAPTER 1", "Section 9"]) |
| `regulator` | Issuing regulator |
| `document_type` | Type of document |
| `issued_date` | ISO date string for freshness scoring |

**Chunk IDs** are deterministic: `UUID(MD5("{document_name}::{chunk_index}"))`. Re-ingesting the same document with the same name will overwrite existing vectors rather than creating duplicates.

### Migration Strategy

Currently using SQLAlchemy `create_all()` on startup (development-friendly, not production-safe). `alembic` is listed as a dependency for when schema migrations are needed. The migration from `create_all` to Alembic is a planned improvement.

---

## 8. AI / LLM / RAG Documentation

### Why AI/LLM Is Used

Nigerian regulatory documents are dense, lengthy, cross-referencing legal texts. No single lookup can answer "does my business need a CBN licence?" — it requires:
1. Understanding the business model described in natural language
2. Mapping it to applicable regulators
3. Retrieving the exact sections of law that apply
4. Synthesising obligations across multiple documents from multiple regulators
5. Identifying what the business is missing
6. Validating that every conclusion is evidence-based

This is exactly what LLMs combined with structured retrieval are designed for.

### LLM Configuration

| Setting | Default | Alternative |
|---|---|---|
| Provider | `openai` | `ollama` |
| Model | `gpt-4o-mini` | `qwen2.5:14b` / `qwen2.5:7b` |
| Entry point | `chat()` in `app/utils/llm_client.py` | Same |

The `chat()` function is the single LLM entry point for the entire system. Every agent uses it. Switching provider requires only a `.env` change — no code changes.

**Cost profile (OpenAI gpt-4o-mini, per analysis):**
- ~6 LLM calls
- ~28,000 tokens total
- ~$0.006 per request

### Cost Tracking

`app/utils/cost_tracker.py` uses Python `contextvars.ContextVar` to maintain per-request token accumulators:

```python
cost_tracker.reset()         # called before workflow.ainvoke()
final_state = await workflow.ainvoke(...)
usage = cost_tracker.get()   # reads accumulated tokens/cost for this invocation
```

Each `chat()` call records its token usage via `cost_tracker.record(model, prompt_tokens, completion_tokens)`. Because each workflow runs in its own async task context, the ContextVar is naturally isolated — no global state, no race conditions between concurrent requests.

### Agent Architecture

The platform uses **6 agents**, coordinated through LangGraph. Each agent is:
- A Python async function that accepts input dicts, calls `chat()`, parses the JSON response, and returns a structured dict
- Guided by a system prompt in `app/prompts/`
- Decoupled from other agents — communicates only through `AgentState`

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            AGENT RESPONSIBILITIES                        │
├─────────────────┬───────────────────────────────────────────────────────┤
│ Orchestrator    │ Decomposes query; identifies target regulators;        │
│                 │ produces task_breakdown and context_summary            │
├─────────────────┼───────────────────────────────────────────────────────┤
│ Jurisdiction    │ Identifies all applicable Nigerian regulators;         │
│ Mapper          │ maps overlapping obligations; assigns confidence scores │
├─────────────────┼───────────────────────────────────────────────────────┤
│ Research Agent  │ NOT an LLM agent — runs the 7-step RAG pipeline;      │
│                 │ retrieves top-k regulatory chunks from Qdrant          │
├─────────────────┼───────────────────────────────────────────────────────┤
│ Reasoning       │ Performs legal synthesis over retrieved chunks;        │
│ Agent           │ produces obligations, prohibitions, permissions,       │
│                 │ conflicts, and a reasoning summary                     │
├─────────────────┼───────────────────────────────────────────────────────┤
│ Compliance      │ Generates risk score (1-10) and risk level;           │
│ Auditor         │ identifies compliance gaps; produces checklist;        │
│                 │ identifies licensing requirements                      │
├─────────────────┼───────────────────────────────────────────────────────┤
│ Citation        │ Verifies every claim in reasoning + audit output       │
│ Verifier        │ against retrieved chunks; scores grounding 0-100;     │
│                 │ flags hallucination risk                               │
├─────────────────┼───────────────────────────────────────────────────────┤
│ Critic Agent    │ Adversarial review: challenges weak conclusions,       │
│                 │ checks for missed regulators, inconsistencies;         │
│                 │ scores quality 1-10; returns PASS / FAIL               │
└─────────────────┴───────────────────────────────────────────────────────┘
```

### LangGraph Workflow State

`AgentState` is a `TypedDict(total=False)` — all fields are optional to allow partial state at any node:

```python
class AgentState(TypedDict, total=False):
    # Input
    query: str
    session_id: str
    organization_context: str | None

    # Jurisdiction mapping output
    target_regulators: list[str]
    jurisdiction_result: dict

    # Research agent output
    retrieved_chunks: list[dict]

    # Reasoning agent output
    reasoning_result: dict

    # Auditor agent output
    audit_result: dict

    # Citation verifier output
    citation_result: dict

    # Critic agent output
    critic_result: dict

    # Final assembled report
    final_report: dict

    # Loop control
    iteration_count: int
    max_iterations: int

    # Workflow metadata
    agent_trace: list[dict]
```

State is **immutable in transit** — each node returns `{**state, ...updated_fields}` using spread syntax. This ensures previous outputs are always available to downstream agents.

### Workflow Graph

```
orchestrator_jurisdiction  (parallel: orchestrator + jurisdiction mapper)
        │
        ▼
    research               (vector retrieval)
        │
        ▼
    reasoning              (legal synthesis)
        │
        ▼
     auditor               (risk + gap assessment)
        │
        ▼
  citation_verifier        (grounding check)
        │
        ▼
      critic               (quality review)
        │
        ├── overall_assessment == "FAIL" and iteration_count < 2
        │         └──► back to reasoning
        │
        └── PASS / PASS_WITH_REVISIONS, or max iterations reached
                  └──► END
```

The critic routing function (`route_after_critic`) enables up to 2 full reasoning loops — meaning in the worst case the reasoning → auditor → citation_verifier → critic pipeline runs twice. This adds ~40–60s to worst-case latency but improves quality of borderline outputs.

### Parallel Execution

The orchestrator and jurisdiction mapper run **in parallel** via `asyncio.gather()` in the `orchestrator_jurisdiction_node`. Both are LLM calls; their outputs are independent. This saves 8–12 seconds per request compared to sequential execution.

### RAG Pipeline (7 Steps)

Implemented in `app/services/retrieval_service.py`:

```
Step 1: Query normalisation
        └── Single query variant used (LLM query expansion disabled for latency)

Step 2: Hybrid search (dense + sparse per query)
        ├── Dense: SentenceTransformers encode → Qdrant cosine search
        └── Sparse: fastembed BM25 → Qdrant sparse vector search
                ↓
Step 3: RRF Fusion (Reciprocal Rank Fusion)
        └── Merges dense and sparse result lists by rank position score

Step 4: Post-retrieval deduplication
        └── By {source}::{section}::{page} key

Step 5: Regulator alias expansion + metadata filtering
        └── "SEC Nigeria" → ["SEC Nigeria", "SEC"]
        └── Filter applied at Qdrant query level (MatchAny) + post-filter safety net

Step 6: Cross-encoder reranking
        └── BAAI/bge-reranker-v2-m3 scores all (query, chunk) pairs
        └── Returns top-8 by reranker score (not vector similarity)

Step 7: Freshness scoring
        └── Documents < 180 days: multiplier = 1.0 (no penalty)
        └── Documents 5+ years old: multiplier = 0.80
        └── Linear decay between

Step 8: MMR diversity
        └── Prevents multiple chunks from the same section
        └── Promotes cross-regulator document diversity
```

### Chunking Strategy

`app/utils/chunking.py` implements section-aware legal chunking:

- Detects PART / CHAPTER / Section / Rule headers via regex
- Maintains a **breadcrumb hierarchy** stack as it scans pages
- Each section is emitted as one chunk with its full hierarchy preserved
- Oversized sections (>4000 chars) are split with `RecursiveCharacterTextSplitter` and 400-char overlap
- Each chunk carries: `document_name`, `page_number`, `section_number`, `section_title`, `hierarchy`, `chunk_index`, `metadata`

This is critical for citation accuracy — downstream agents can cite specific sections and pages because the chunker preserved that structure.

### Embedding Models

| Model | Type | Dimensions | Use |
|---|---|---|---|
| `BAAI/bge-base-en-v1.5` | Dense, neural | 768 | Semantic similarity search |
| `Qdrant/bm25` (fastembed) | Sparse, statistical | Variable | Keyword/term matching |
| `BAAI/bge-reranker-v2-m3` | Cross-encoder | — | Post-retrieval reranking |

Both retrieval models are loaded in-process (no external embedding API). The reranker is 2.27 GB and is loaded synchronously in a thread pool during startup.

### Prompt Engineering

Each agent's system prompt is stored in `app/prompts/{agent}.py` as a constant string. Key design decisions:

- **Reasoning prompt** includes explicit rules: "never cite CAMA for financial compliance", "flag structural conflicts between business model and licence restrictions"
- **Auditor prompt** includes "a checklist item is MET only if already implemented — intention does not count"
- **Critic prompt** is explicitly adversarial: "your job is to find what other agents missed"
- **Citation verifier** defines three states: VERIFIED, UNVERIFIED, CONTRADICTED — not just pass/fail

All agents parse LLM output as JSON and have fallback dicts for when the model returns invalid JSON (e.g., includes markdown code fences).

### Hallucination Prevention

Multiple layers:

1. **Retrieval-first**: no reasoning happens without retrieved chunks
2. **Citation verifier**: explicitly checks whether each claim appears in the retrieved evidence
3. **Grounding score**: 0–100 percentage of verified citations
4. **Critic agent**: flags claims with HIGH confidence but LOW grounding
5. **Reasoning prompt rule**: "If the retrieved context is insufficient, state: 'Insufficient regulatory basis to conclude on [topic]'"
6. **Regulator attribution rules**: specific prompt rules prevent SEC documents being attributed to CBN, or CAMA being cited for financial compliance

---

## 9. API Documentation

### GET /health

**Purpose**: Health check for monitoring and liveness probes.

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "services": {
    "postgres": "connected",
    "qdrant": "connected"
  }
}
```

**Auth**: None required.

---

### POST /regulations/upload

**Purpose**: Upload a regulatory PDF for ingestion into the vector store.

**Request**: `multipart/form-data`

| Field | Type | Required | Notes |
|---|---|---|---|
| `file` | `UploadFile` | Yes | Must be `application/pdf` |
| `regulator` | `string` | Yes | e.g. "CBN", "SEC Nigeria" |
| `document_type` | `string` | Yes | e.g. "Regulation", "Act", "Circular" |
| `issued_date` | `string` | No | ISO date, e.g. "2024-03-15" |
| `notes` | `string` | No | Free text |

**Responses:**

| Code | Meaning |
|---|---|
| `201` | Ingested successfully |
| `400` | Non-PDF file |
| `409` | Duplicate document (same SHA256 hash) |
| `422` | PDF parsed but zero text extracted |

**Internal flow**: Validates → SHA256 check → write to tempfile → parse (PyMuPDF + pdfplumber + OCR) → chunk → embed (dense + sparse) → upsert to Qdrant → save `DocumentRecord` to PostgreSQL → delete tempfile.

---

### GET /regulations/

**Purpose**: List all indexed regulatory documents.

**Response**: Array of document objects with `id`, `file_name`, `regulator`, `document_type`, `total_pages`, `chunks_ingested`, `ingested_at`.

---

### DELETE /regulations/{doc_id}

**Purpose**: Remove a document from the registry.

**Note**: This removes the PostgreSQL record. Qdrant vectors are not automatically deleted (known limitation).

---

### POST /analyze/analyze-business

**Purpose**: Submit a business model description for full compliance analysis.

**Request body (BusinessAnalysisRequest):**
```json
{
  "business_description": "We are a digital lending startup...",
  "business_sector": "Fintech",
  "target_regulators": ["CBN", "FIRS"],
  "organization_context": "Early-stage, not yet licensed",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

| Field | Required | Notes |
|---|---|---|
| `business_description` | Yes | 20–5000 chars |
| `business_sector` | No | Prepended to query as context |
| `target_regulators` | No | Restricts Qdrant metadata filter |
| `organization_context` | No | Passed to orchestrator + reasoning agents |
| `session_id` | No | Groups audit records; generated if not provided |

**Response (AnalysisInitiatedResponse):**
```json
{
  "report_id": "uuid",
  "workflow_status": "pending",
  "message": "Analysis initiated. Poll /analyze/report/{report_id} for results."
}
```

HTTP 200 is returned immediately. The workflow runs in the background.

---

### POST /analyze/compliance-gap

**Purpose**: Identify compliance gaps between a business and applicable regulations.

**Request body (ComplianceGapRequest):**
```json
{
  "business_description": "We are a payment gateway with CBN PSSP approval...",
  "target_regulators": ["CBN", "NDPA"],
  "session_id": "uuid"
}
```

Internally wraps the description in a gap-analysis prefix query and calls the same compliance workflow. Same poll pattern as above.

---

### GET /analyze/report/{report_id}

**Purpose**: Retrieve the status and result of a submitted workflow.

**Response (ReportStatusResponse):**
```json
{
  "report_id": "uuid",
  "status": "completed",
  "audit_id": "uuid",
  "session_id": "uuid",
  "report": {
    "query": "...",
    "executive_summary": "...",
    "applicable_regulators": ["CBN", "SEC Nigeria"],
    "obligations": [],
    "prohibitions": [],
    "permissions": [],
    "conflicts": [],
    "compliance_gaps": [],
    "compliance_checklist": [],
    "licensing_requirements": [],
    "recommendations": [],
    "risk_score": 7,
    "risk_level": "HIGH",
    "citations": []
  },
  "llm_metrics": {
    "llm_calls": 6,
    "prompt_tokens": 22000,
    "completion_tokens": 6000,
    "total_tokens": 28000,
    "cost_usd": 0.006,
    "model": "gpt-4o-mini"
  },
  "grounding_score": 85,
  "hallucination_risk": "LOW",
  "iteration_count": 1,
  "agent_trace": []
}
```

**Status values**: `running` | `completed` | `failed`

404 if `report_id` was not found in the in-memory store (process restart clears it).

---

### GET /analyze/report/{report_id}/stream

**Purpose**: Server-Sent Events (SSE) stream of real-time agent progress.

Sends one `data: {...}` event per completed agent step. Clients that prefer SSE over polling can use this endpoint. Closes when workflow completes or fails.

---

### GET /audit/trace/{audit_id}

**Purpose**: Retrieve the complete agent execution trace for a compliance report.

Returns the full `AuditRecord` including all agent outputs in JSON. Supports explainability and forensic review.

---

### GET /audit/session/{session_id}

**Purpose**: List all audit traces for a given session (newest first).

Supports `?limit=20` query parameter. Returns summary objects (not full agent outputs).

---

## 10. DevOps & Infrastructure

### Infrastructure Components

| Service | Image | Port | Data Persistence |
|---|---|---|---|
| PostgreSQL | `postgres:16-alpine` | 5432 | `postgres_data` named volume |
| Qdrant | `qdrant/qdrant:latest` | 6333 (REST), 6334 (gRPC) | `qdrant_data` named volume |
| Redis | `redis:7-alpine` | 6379 | `redis_data` named volume |

All three services are defined in `docker-compose.yml` and managed as a local stack.

### Starting Infrastructure

```bash
docker compose up -d
```

All data is persisted in Docker named volumes — stopping and restarting containers does not lose indexed documents or audit records.

### Starting the Application

```bash
# Activate virtual environment
source .venv/bin/activate

# Start FastAPI backend (do NOT use --reload — it creates duplicate lifespan events)
uvicorn app.main:app --port 8000

# In a second terminal — start the Chainlit UI
chainlit run chainlit_app.py --port 8080
```

### Dependency Management

The project uses `uv` (Astral) as the package manager. `pyproject.toml` lists all dependencies; `uv.lock` pins exact versions.

```bash
uv sync           # install all dependencies
uv add <package>  # add a new dependency
```

### Python Runtime

Python 3.12+ is required (uses `str | None` union syntax, `match`/`case`, improved asyncio). Version is pinned in `.python-version`.

### Secrets Management

All secrets are stored in `.env` in the project root (gitignored). `.env.example` is committed with placeholder values.

**Never commit `.env` to git.**

Production deployments should use environment variable injection via the hosting platform or a secrets manager (AWS Secrets Manager, GCP Secret Manager, Doppler, etc.).

### CI/CD

No CI/CD pipeline is currently configured. When implementing:

1. GitHub Actions is the natural choice (repository is already on GitHub)
2. Suggested workflow: `pytest` → `ruff` linting → `docker build` → push to registry → deploy

### Scaling Considerations

**Current (single process):**
- One uvicorn worker handles all requests
- `_reports` dict is in-process memory → lost on restart
- Heavy models (reranker, embedder) loaded once per process

**Horizontal scaling path:**
- Replace `_reports` dict with Redis
- Use `uvicorn --workers N` or `gunicorn` with uvicorn workers
- Reranker and embedder can be moved to a dedicated embedding service
- Qdrant and PostgreSQL are already external — scale independently

---

## 11. Security Analysis

### Authentication & Authorization

**Current state**: Optional Bearer token auth is scaffolded but token verification is not implemented. All routes accept unauthenticated requests.

**Planned**: JWT-based auth via `python-jose`. The `get_current_user` dependency is ready to be wired to a users table once implemented.

**Risk**: In the current state, any user with network access can upload documents, trigger analysis workflows, and read audit records. This is acceptable for a local MVP but must be locked down before any public deployment.

### Input Validation

- All request bodies are Pydantic models with field-level constraints (`min_length`, `max_length`)
- File upload validates `content_type == "application/pdf"` before processing
- All UUIDs in route parameters are validated via `uuid.UUID()` — invalid UUIDs return `404` / graceful `None` rather than propagating
- SQL queries use SQLAlchemy parameterised expressions — no raw string concatenation → no SQL injection risk

### Content Deduplication

SHA256 hashing of uploaded files prevents the same document being ingested twice. This is both a storage optimisation and a data integrity measure.

### LLM Prompt Security

All agent system prompts are static string constants loaded at import time — they cannot be modified by user input. User queries are passed only in the `user` role messages, never in system prompts. This prevents prompt injection via the query field.

### Sensitive Data Handling

- API keys are loaded from environment variables, never hardcoded
- Database credentials are in `.env` (gitignored)
- The `.gitignore` excludes `.env`, `*.log`, `test_results*.txt`, `data/raw/`, `.venv/`
- No PII is collected or stored beyond the user's query text and organization context

### OWASP Top 10 Considerations

| Risk | Mitigation |
|---|---|
| A01 Broken Access Control | Currently no access control (MVP only). Auth scaffolded for future. |
| A02 Cryptographic Failures | API keys in env vars. No sensitive data encrypted at rest (planned for production). |
| A03 Injection | Pydantic validation + SQLAlchemy parameterised queries. LLM prompts are static. |
| A04 Insecure Design | Clean architecture with separation of concerns. No business logic in routes. |
| A05 Security Misconfiguration | CORS restricted to specific origins. Debug mode off in production. |
| A06 Vulnerable Components | `uv.lock` pins all dependency versions. No known CVEs in current deps. |
| A07 Auth/Identification Failures | Not fully implemented — highest priority security gap for production. |
| A08 Software Integrity | No dependency confusion risks — all packages from PyPI. `uv.lock` ensures reproducibility. |
| A09 Logging Failures | Structured logging via Python logging module. No sensitive data in logs. |
| A10 SSRF | httpx is used for OpenAI/Ollama calls with explicit URLs from settings — no user-controlled URLs. |

---

## 12. Observability & Monitoring

### Logging

The application uses Python's standard `logging` module throughout. The `app` logger namespace is configured in `main.py` with a `StreamHandler` that bypasses uvicorn's root handler to prevent duplicate log lines.

**Log format**: `HH:MM:SS [LEVEL] module.name: message`

Each major operation is logged with a recognisable prefix:

| Prefix | Component |
|---|---|
| `[INGEST]` | IngestionService |
| `[PARSE]` | PDF parser |
| `[CHUNK]` | Chunker |
| `[EMBED]` | EmbeddingService |
| `[SPARSE]` | SparseEmbeddingService |
| `[STORE]` | VectorRepository |
| `[RETRIEVAL]` | RetrievalService |
| `[LLM]` | llm_client |
| `[ORCHESTRATOR]` | Orchestrator agent |
| `[JURISDICTION]` | Jurisdiction mapper |
| `[REASONING]` | Reasoning agent |
| `[AUDITOR]` | Compliance auditor |
| `[CITATION]` | Citation verifier |
| `[CRITIC]` | Critic agent |
| `[COMPLIANCE]` | ComplianceService |
| `[AUDIT]` | AuditService |
| `[QDRANT]` | Qdrant client |

**Timing**: Every agent node logs `done in X.Xs` with key output metrics (e.g., number of chunks, regulator list, risk score).

### Health Checks

`GET /health` actively tests PostgreSQL (via `SELECT 1`) and Qdrant (via `collection_exists()`) and returns their connection status. Suitable for liveness/readiness probes.

### Metrics

No Prometheus / Grafana / Datadog integration currently. LLM metrics (token counts, cost, call count, model name) are returned in every completed report via the `llm_metrics` field and stored in the `AuditRecord`. Duration in milliseconds is also stored per record.

### Audit Trail

Every completed analysis is persisted to PostgreSQL with the full workflow state — including every agent's complete output JSON, the citations used, the risk score, grounding score, and iteration count. This provides a post-hoc audit capability without needing distributed tracing.

### Error Tracking

Exceptions in background tasks are caught and stored in `_reports[report_id]["error"]`. The Chainlit UI surfaces these as analysis failed messages. No external error tracking service (Sentry, etc.) is currently configured.

---

## 13. End-to-End Request Walkthrough

### Scenario

User query: "We are launching a mobile app that lets users invest in Nigerian Treasury Bills, earn interest, and send money to other users. We plan to hold customer funds in a pooled account."

### Step-by-Step Trace

#### 1. User Interaction (Chainlit)

- User has clicked "Analyze Business Model" — `cl.user_session["mode"] = "analyze"`
- User types the query and presses Enter
- `on_message()` fires, validates query length >= 20 chars
- `console_session_id = cl.user_session["console_session_id"]` (e.g. `"abc-123-..."`)
- Calls `_run_analysis("/analyze/analyze-business", {"business_description": "...", "session_id": "abc-123-..."}, "analyze", "abc-123-...")`

#### 2. Submit to FastAPI (POST /analyze/analyze-business)

- httpx POSTs to `http://localhost:8000/analyze/analyze-business`
- FastAPI receives, Pydantic validates `BusinessAnalysisRequest`
- `report_id = str(uuid.uuid4())` — e.g. `"f4e3d2c1-..."`
- Background task `_run_workflow(report_id, query, db, session_id="abc-123-...")` is scheduled
- HTTP 200 returned immediately: `{"report_id": "f4e3d2c1-...", "workflow_status": "pending", ...}`

#### 3. UI Starts Polling

- Chainlit receives `report_id`
- Opens `cl.Step("Multi-Agent Workflow")`
- Every 3 seconds: `GET /analyze/report/f4e3d2c1-...`
- While running: updates step with elapsed time

#### 4. Background Workflow Executes

**A. ComplianceService initialises state:**
```python
initial_state = {
    "query": "[Sector: Fintech] We are launching a mobile app...",
    "session_id": "abc-123-...",
    "organization_context": None,
    "iteration_count": 0,
    "max_iterations": 2,
    "agent_trace": [],
}
cost_tracker.reset()
```

**B. Node 1: orchestrator_jurisdiction_node (parallel execution)**

- `asyncio.gather(run_orchestrator(...), run_jurisdiction_mapping(...))`
- Orchestrator LLM call returns: `{task_breakdown: [...], target_regulators: ["CBN", "SEC Nigeria", "NDIC"], context_summary: "...", query_type: "LICENSING"}`
- Jurisdiction mapper LLM call (simultaneously) returns: `{applicable_regulators: [{regulator: "CBN", ...}, {regulator: "SEC Nigeria", ...}, {regulator: "NDIC", ...}], primary_regulator: "CBN"}`
- State gains: `target_regulators`, `jurisdiction_result`, updated `agent_trace`

**C. Node 2: research_node**

- `RetrievalService.retrieve(query="...", filter_regulators=["CBN", "SEC Nigeria", "NDIC"])`
- Regulator aliases expanded: "SEC Nigeria" → ["SEC Nigeria", "SEC"]
- Dense embedding generated via `BAAI/bge-base-en-v1.5`
- BM25 sparse embedding generated via `Qdrant/bm25`
- Parallel dense + sparse search in Qdrant with `MatchAny` filter on regulator field
- RRF fusion merges result lists
- Deduplication by `source::section::page` key
- Cross-encoder reranks top 16 → keeps top 8
- Freshness multiplier applied
- MMR diversity applied
- Returns ~8 chunks from BOFIA 2020, CBN PSB Guidelines, ISA 2025, CBN Consumer Protection Regulations

**D. Node 3: reasoning_node**

- LLM receives chunks formatted as: `[CBN | BOFIA-2020.pdf | Section 9 | Page 14]\n{text}`
- Returns obligations, prohibitions, conflicts, reasoning_summary

**E. Node 4: auditor_node**

- Returns: risk_score: 8, risk_level: "HIGH", compliance_gaps: 5 items, compliance_checklist: 9 items, licensing_requirements

**F. Node 5: citation_node**

- Returns: overall_grounding_score: 82, hallucination_risk: "LOW", recommendation: "APPROVE"

**G. Node 6: critic_node**

- Returns: overall_assessment: "PASS_WITH_REVISIONS", quality_score: 7
- `route_after_critic`: PASS_WITH_REVISIONS → END (not FAIL → no loop back)

**H. AuditService persists record**

- New `AuditRecord` row written to PostgreSQL with full JSON state

**I. ComplianceService assembles final response**

- `_reports["f4e3d2c1-..."] = {"status": "completed", "report": result}`

#### 5. UI Receives Completed Report

- Next poll returns `status: "completed"`
- Chainlit closes workflow step
- Renders individual agent steps from `agent_trace`
- Renders Sources Retrieved with 8 citation documents
- Renders Workflow Metrics: 6 LLM calls, ~28,000 tokens, $0.006
- Renders full compliance report card
- Displays follow-up action buttons

**Total elapsed time**: ~70–90 seconds

---

## 14. Engineering Decisions

### LangGraph over Custom Orchestration

**Decision**: Use LangGraph to manage multi-agent workflow state and routing.

**Why**: LangGraph provides a typed state graph with conditional edges, loop support, and guaranteed state immutability between nodes. Implementing this manually would require significant boilerplate. The critic→reasoning feedback loop in particular benefits from LangGraph's conditional edge routing.

**Alternative considered**: Direct function call chain. Rejected because it provides no loop support, no state tracing, and tightly couples agent logic.

### Pydantic v2 + FastAPI

**Decision**: Use Pydantic v2 models for all API boundaries.

**Why**: Automatic request validation, serialisation, and OpenAPI schema generation. Type safety at the API boundary reduces an entire class of runtime errors.

### Hybrid Search (Dense + Sparse)

**Decision**: Use both `BAAI/bge-base-en-v1.5` (semantic) and `Qdrant/bm25` (keyword) with RRF fusion.

**Why**: Legal text retrieval has two distinct patterns:
1. Semantic queries ("what are my AML obligations") → semantic search wins
2. Exact term queries ("Payment Service Bank licence requirements") → BM25 wins

Pure semantic search misses exact legal term matches. Pure BM25 misses paraphrased or conceptual queries. Hybrid with RRF gives best-of-both-worlds results, consistently outperforming either alone for regulatory text.

### Cross-Encoder Reranking

**Decision**: Use `BAAI/bge-reranker-v2-m3` as a second-stage reranker.

**Why**: First-stage retrieval (vector search) optimises for recall — it returns 15–30 potentially relevant chunks. The cross-encoder reads each (query, chunk) pair together, providing much higher-precision ranking. The top 8 after reranking are significantly more relevant than the top 8 by vector similarity alone.

**Tradeoff**: The model is 2.27 GB and requires 1–3 seconds CPU time per reranking call. Pre-loading at startup eliminates cold-start latency.

### Section-Aware Chunking

**Decision**: Custom legal chunker rather than generic `RecursiveCharacterTextSplitter`.

**Why**: Generic text splitters break mid-section, destroying the legal context. A clause split across two chunks loses meaning. The custom chunker emits one chunk per legal section, preserving section numbers, page references, and hierarchy. This is critical for citation accuracy.

### Per-Request Cost Tracking via ContextVars

**Decision**: Use Python `contextvars.ContextVar` for LLM cost accumulation.

**Why**: Multiple concurrent requests each run their own async task. A global variable would create race conditions. Thread-local storage does not apply to asyncio. `ContextVar` provides true per-async-task isolation — each `workflow.ainvoke()` call gets its own cost accumulator across all 6 LLM calls.

### Parallel Orchestrator + Jurisdiction Mapper

**Decision**: Run orchestrator and jurisdiction mapper simultaneously with `asyncio.gather()`.

**Why**: Both are LLM calls (~10s each) with completely independent inputs and no dependency on each other's outputs. Running sequentially would add 8–12 unnecessary seconds to every request.

### In-Memory Report Store (MVP)

**Decision**: `_reports: dict[str, dict]` in the analysis route module.

**Why**: Simple, zero-dependency, works for a single-process MVP. The alternative (Redis) adds operational complexity without adding value for a single-node demonstration.

**Limitation**: Reports are lost on process restart. This is the number one production migration item.

### Polling over WebSockets

**Decision**: Client polls `GET /analyze/report/{id}` every 3 seconds.

**Why**: Simpler to implement and debug than WebSockets. The workflow is 60–120 seconds — the difference between 3-second polling and real-time push is negligible UX impact. SSE (`/stream`) is available as an alternative for clients that prefer push semantics.

---

## 15. Technical Debt & Risks

### Critical (Must Fix Before Production)

| Issue | Risk | Fix |
|---|---|---|
| No authentication implementation | Any user can access all data and trigger workflows | Implement JWT validation in `get_optional_user` / `get_current_user` |
| In-memory `_reports` dict | Reports lost on restart; not shareable across workers | Replace with Redis |
| `create_all()` instead of Alembic migrations | Schema changes require manual intervention or data loss | Set up Alembic migration files |
| No rate limiting | Malicious actor can trigger unlimited LLM calls (cost) | Add `slowapi` or API gateway rate limiting |
| No input sanitisation beyond length validation | Prompt injection via `business_description` | Add content filtering or sanitisation layer |

### High Priority

| Issue | Risk | Fix |
|---|---|---|
| Reranker blocks event loop | Concurrent requests during reranking experience latency | Move to thread pool executor or separate process |
| No document deletion from Qdrant | `DELETE /regulations/{id}` removes PostgreSQL record but leaves vectors | Add `vector_repository.delete_by_document(name)` |
| No tests beyond smoke test | Regressions go undetected | Add pytest unit tests for chunker, retrieval service, agent parsing |
| Report ID not in persistent store | GET /report/{id} returns 404 after restart | Fix via Redis migration |
| Redis provisioned but unused | Wasted resource | Either implement session caching or remove from docker-compose |

### Medium Priority

| Issue | Risk | Fix |
|---|---|---|
| Query expansion disabled | Slightly lower recall on paraphrased queries | Re-enable with 1 variant to limit latency |
| Contextual compression disabled | Chunks may contain noise that dilutes reasoning | Re-enable selectively for long chunks |
| No Qdrant index on `regulator` field | Full scan on regulator filter (acceptable at small scale) | Add `create_payload_index` for regulator field |
| Duplicate nodes in `nodes.py` | `orchestrator_node` and `jurisdiction_node` exist as dead code | Delete or document as deprecated |
| No document versioning | Uploading a new version requires manual delete + re-upload | Add version field and supersession logic |

### Low Priority / Future

| Issue | Description |
|---|---|
| No streaming LLM responses | Agents wait for full LLM response before proceeding |
| No caching of retrieval results | Same query retrieves from Qdrant every time |
| No multi-language support | Only English regulatory documents supported |
| No document freshness alerts | No notification when a regulation document is superseded |

---

## 16. Future Roadmap

### Phase 1: Production Hardening

- Implement JWT authentication with user management
- Replace in-memory `_reports` with Redis
- Set up Alembic migrations
- Add rate limiting (e.g., 10 analyses/hour per API key)
- Add Sentry for error tracking
- Containerise the FastAPI app + Chainlit into Docker images
- Set up GitHub Actions CI (lint + test on every PR)

### Phase 2: Capability Expansion

- **Broader regulator coverage**: NAICOM (insurance), NCC (telecoms/USSD), PenCom (pensions), NDIC resolution framework
- **Document freshness alerts**: Detect when a regulation in Qdrant has been superseded by a newer upload and flag outdated citations
- **Multi-document conflict detection**: Explicitly surface cases where two indexed regulations contradict each other
- **Regulatory change monitoring**: Crawl CBN/SEC websites for new circulars; trigger re-analysis if a change affects indexed content
- **Conversation follow-up**: Allow users to ask follow-up questions within the same session, building on prior analysis context

### Phase 3: Platform Features

- **Multi-tenant support**: Organisation-level accounts; each org has isolated audit history
- **Team collaboration**: Share reports, comment on findings, assign remediation tasks
- **Regulatory calendar**: Track filing deadlines, renewal dates, and reporting obligations extracted from indexed documents
- **API access tier**: REST API for enterprise customers to integrate compliance checks into their own workflows
- **Batch analysis**: Upload a portfolio of products/entities and generate compliance reports for all
- **Custom document libraries**: Per-organisation private document stores for internal policies

### Phase 4: Intelligence Enhancements

- **Agentic document scraping**: Automatically download and ingest new regulations from CBN/SEC/FIRS portals
- **Precedent and enforcement tracking**: Index CBN/SEC enforcement actions and surface similar precedents when analysing risk
- **Cross-jurisdictional analysis**: Extend beyond Nigeria to ECOWAS harmonised regulations and international standards (FATF, PCI-DSS, GDPR)
- **Fine-tuned models**: Fine-tune a smaller model (7B) on Nigerian regulatory text to reduce OpenAI dependency and cost

---

## 17. Local Development Setup

### Prerequisites

| Requirement | Version | Install |
|---|---|---|
| Python | 3.12+ | python.org or `pyenv` |
| uv | Latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Docker Desktop | Latest | docker.com |
| Tesseract OCR | Latest | `brew install tesseract` (macOS) |
| git | Any | Pre-installed on most systems |

### Step 1: Clone and Install

```bash
git clone git@github.com:faniyi-akinbobola/Regulatory-Intelligence-Platform.git
cd Regulatory-Intelligence-Platform

# Install all Python dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

### Step 2: Configure Environment

```bash
cp .env.example .env
# Edit .env with your values
```

Required values:

```bash
# OpenAI (required unless using Ollama)
OPENAI_API_KEY=sk-proj-...

# PostgreSQL (defaults match docker-compose.yml)
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
OPENAI_MODEL=gpt-4o-mini

# Embeddings
EMBEDDING_MODEL_NAME=BAAI/bge-base-en-v1.5
EMBEDDING_DIMENSION=768
```

### Step 3: Start Infrastructure

```bash
docker compose up -d
```

### Step 4: Start the Backend

```bash
# Option A — convenience script (handles port cleanup automatically)
bash server.sh          # start
bash server.sh stop     # kill server on port 8000
bash server.sh status   # show what's running on port 8000

# Option B — direct uvicorn (do NOT use --reload, it causes duplicate lifespan events)
uvicorn app.main:app --port 8000
```

Expected output:
```
Starting up Regulatory Intelligence Platform...
PostgreSQL tables ready
Qdrant collection ready
Reranker model loaded     <- downloads 2.27 GB on first run (takes several minutes)
```

### Step 5: Ingest Regulatory Documents

```bash
curl -X POST http://localhost:8000/regulations/upload \
  -F "file=@path/to/CBN_Consumer_Protection.pdf" \
  -F "regulator=CBN" \
  -F "document_type=Regulation" \
  -F "issued_date=2019-12-20"
```

### Step 6: Start the UI

```bash
# Second terminal
source .venv/bin/activate
chainlit run chainlit_app.py --port 8080
```

Open `http://localhost:8080`.

### Step 7: Run Tests

```bash
# Full async route test suite (12 tests — requires running server + infrastructure)
python test_routes.py

# Bash smoke tests (curl-based, good for CI)
bash test_smoke.sh
```

### Example Queries

The repository includes `Example-Queries.md` with 50 pre-written example inputs:
- **25 business model analysis queries** — covering digital lending, wallets, capital markets, insurance tech, crypto, agent banking, and more
- **25 compliance gap analysis queries** — covering specific regulatory obligations, missing licences, AML/CFT gaps, and data protection

Use these to demo the platform or validate retrieval quality after ingesting documents.

### Common Developer Workflows

**Reset the vector store:**
```bash
python scripts/reset_collection.py
# Then re-ingest all documents
```

**View recent audit records:**
```bash
docker exec -it postgres psql -U regplatform -d regulatory_db \
  -c "SELECT id, overall_risk_level, grounding_score, duration_ms, created_at FROM audit_records ORDER BY created_at DESC LIMIT 10;"
```

**View indexed documents:**
```bash
curl http://localhost:8000/regulations/ | python3 -m json.tool
```

**Debugging tips:**
- If the first request takes 4+ minutes, the reranker model is downloading. Wait for it.
- If `GET /regulations` returns 307, your client needs `follow_redirects=True`
- If Qdrant returns no results, check that `issued_date` format is ISO (`YYYY-MM-DD`)
- If agents return "Insufficient regulatory basis", the relevant regulation document may not be ingested

---

## 18. Glossary

### Technical Terms

| Term | Definition |
|---|---|
| **Agent** | An LLM-powered function with a specific role that takes structured input, calls an LLM with a domain-specific prompt, and returns structured JSON output |
| **AgentState** | The shared `TypedDict` that flows through the LangGraph workflow, accumulating agent outputs at each node |
| **asyncio.gather** | Python async primitive that runs multiple coroutines concurrently in the same event loop |
| **BM25** | Best Match 25 — a statistical text ranking algorithm based on term frequency and inverse document frequency. Used for keyword-based search in Qdrant's sparse vector index |
| **Chainlit** | Python framework for building AI-powered conversational interfaces with step visualisation, file uploads, and action buttons |
| **Chunk / DocumentChunk** | A section of a regulatory document, bounded by legal section headers, carrying metadata (page, section, regulator, hierarchy) |
| **ContextVar** | Python mechanism for storing per-async-task state. Used here to isolate LLM cost tracking between concurrent workflow invocations |
| **Cross-encoder** | A reranking model that scores (query, document) pairs jointly — more accurate than bi-encoder similarity for relevance but slower |
| **Dense vector** | A fixed-size floating-point vector (768 dimensions) produced by a neural embedding model. Captures semantic meaning |
| **FastAPI** | Modern Python async web framework built on Starlette. Used for the REST API layer |
| **Freshness scoring** | A multiplier (0.80–1.0) applied to retrieved chunk scores based on document age. Newer documents are scored higher |
| **LangGraph** | Library from LangChain that enables stateful, multi-step LLM workflows with typed state graphs, conditional edges, and loop support |
| **Lifespan** | FastAPI's startup/shutdown hook mechanism using an async context manager |
| **MMR (Maximal Marginal Relevance)** | A diversity algorithm that prevents returning multiple chunks from the same section, promoting cross-document variety |
| **Modular monolith** | An architecture pattern where the codebase is a single deployable unit with clear internal layer boundaries, as opposed to microservices |
| **Pydantic** | Python data validation library used for request/response models and settings |
| **RAG (Retrieval-Augmented Generation)** | A technique that grounds LLM outputs in retrieved external documents, preventing hallucinations |
| **RRF (Reciprocal Rank Fusion)** | An algorithm that combines ranked lists from multiple search systems by summing the reciprocal of each item's rank position |
| **Sparse vector** | A high-dimensional vector with mostly zero values. Used for BM25 keyword matching in Qdrant |
| **SQLAlchemy** | Python ORM and SQL toolkit. Used with asyncpg for async PostgreSQL access |
| **TypedDict** | Python type hint for dictionaries with fixed keys and value types. Used for `AgentState` |
| **uv** | A fast Python package manager written in Rust (by Astral). Replaces pip + virtualenv |

### Domain Terms

| Term | Definition |
|---|---|
| **AML/CFT** | Anti-Money Laundering / Countering the Financing of Terrorism — regulatory obligations to detect and report suspicious financial activity |
| **BOFIA** | Banks and Other Financial Institutions Act — primary legislation governing Nigerian banks, supervised by CBN |
| **CBN** | Central Bank of Nigeria — Nigeria's apex financial regulator for banking, payments, forex, and monetary policy |
| **CIS** | Collective Investment Scheme — a pooled investment vehicle (mutual fund, unit trust) regulated by SEC Nigeria |
| **Compliance Gap** | A specific area where a business's current practices do not meet a regulatory requirement |
| **DMB** | Deposit Money Bank — a full commercial bank licensed by CBN (e.g., Access Bank, GTBank) |
| **EFCC** | Economic and Financial Crimes Commission — enforces AML/CFT and financial crimes laws in Nigeria |
| **FCCPC** | Federal Competition and Consumer Protection Commission — enforces consumer rights and competition law |
| **FIRS** | Federal Inland Revenue Service — Nigeria's federal tax authority |
| **Grounding score** | 0–100 percentage of claims in a compliance report that are directly supported by retrieved regulatory text |
| **Hallucination** | An LLM generating a confident-sounding but factually incorrect or unsupported claim |
| **ISA 2025** | Investments and Securities Act 2025 — the primary legislation governing Nigerian capital markets, supervised by SEC Nigeria |
| **KYC** | Know Your Customer — identity verification obligations imposed on financial institutions |
| **MFB** | Microfinance Bank — a tier of CBN-licensed financial institution serving unbanked/underbanked segments |
| **MLPPA** | Money Laundering (Prevention and Prohibition) Act — primary AML legislation in Nigeria |
| **NDIC** | Nigeria Deposit Insurance Corporation — insures bank deposits and handles bank resolution |
| **NDPA** | Nigeria Data Protection Act 2023 — Nigeria's primary data protection legislation |
| **NFIU** | Nigerian Financial Intelligence Unit — the national body for AML/CFT reporting, suspicious transaction reports |
| **NCC** | Nigerian Communications Commission — regulates telecoms, including USSD-based fintech |
| **NITDA** | National Information Technology Development Agency — enforces IT standards and data protection frameworks |
| **PenCom** | National Pension Commission — regulates pension fund administrators and RSA schemes |
| **PSB** | Payment Service Bank — a CBN licence category for mobile-money focused financial institutions |
| **PSSP** | Payment Solution Service Provider — a CBN category for payment processing infrastructure providers |
| **Regulator** | A government body with statutory authority to license, supervise, and enforce rules in a specific sector |
| **Risk level** | Classification of compliance risk: CRITICAL (licence/criminal exposure) → HIGH → MEDIUM → LOW |
| **SEC Nigeria** | Securities and Exchange Commission Nigeria — regulates capital markets, investment schemes, and VASPs |
| **SCUML** | Special Control Unit Against Money Laundering — part of EFCC, registers and supervises DNFBPs |
| **Session ID** | A UUID that groups all analyses performed in a single Chainlit chat session, linking them in the audit database |
| **Structural conflict** | A situation where a described business feature is fundamentally incompatible with the available licence category |
| **VASP** | Virtual Asset Service Provider — an entity dealing in crypto assets, regulated by SEC Nigeria |
| **Workflow** | The sequential execution of all 6 LangGraph nodes that transforms a user query into a structured compliance report |
