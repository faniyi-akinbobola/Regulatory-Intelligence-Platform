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