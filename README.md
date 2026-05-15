<!-- What the 3 Services Are For
Qdrant — Vector database

Stores document chunk embeddings + metadata (section, page, regulator, document name)
Handles semantic search: "find regulations similar to this query"
The Research Agent queries this exclusively
PostgreSQL — Persistent relational storage

Stores audit traces, compliance reports, session history, user data
Structured data that needs querying, relationships, and persistence
The audit_repository and document_repository write here
Redis — In-memory cache + session store

Stores active LangGraph workflow state during execution
Caches frequent queries (same business question asked twice)
Handles streaming state between FastAPI and the frontend
Data here is ephemeral — it's not for long-term storage
Your guess was correct: Qdrant = vector DB, Redis = session/cache, Postgres = persistent storage. -->


User Query (via FastAPI)
        │
        ▼
┌─────────────────────────────────────────┐
│           LangGraph Workflow            │
│                                         │
│  graph/state.py  ← shared state object  │
│  graph/nodes.py  ← each agent = a node  │
│  graph/workflow.py ← edges/routing      │
│                                         │
│  Node 1: Orchestrator                   │
│    └─ decomposes query, sets plan       │
│                                         │
│  Node 2: Jurisdiction Mapper            │
│    └─ identifies CBN/SEC/NDIC/FIRS      │
│                                         │
│  Node 3: Research Agent                 │
│    └─ calls RetrievalService            │
│         └─ EmbeddingService.embed_text()│
│         └─ VectorRepository.search()   │
│         └─ reranking.py                 │
│                                         │
│  Node 4: Regulatory Reasoning Agent     │
│    └─ receives chunks from state        │
│    └─ calls LLM with reasoning prompt   │
│                                         │
│  Node 5: Compliance Auditor             │
│    └─ receives reasoning output         │
│    └─ calls LLM with auditor prompt     │
│                                         │
│  Node 6: Citation Verifier              │
│    └─ cross-checks all claims vs chunks │
│                                         │
│  Node 7: Critic                         │
│    └─ reviews everything                │
│    └─ if quality_score < threshold      │
│         └─ loops back to Node 4         │
│                                         │
│  END → structured ComplianceReport      │
└─────────────────────────────────────────┘
        │
        ▼
AuditService.persist(trace)  → PostgreSQL
        │
        ▼
FastAPI returns structured JSON response