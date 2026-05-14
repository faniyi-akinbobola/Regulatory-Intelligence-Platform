# Project Overview

We are building an Agentic AI Regulatory Intelligence Platform focused on Nigerian financial and compliance regulations.

This is NOT a generic chatbot or ChatGPT wrapper.

The system is designed as a multi-agent AI workflow platform capable of:
- regulatory reasoning,
- compliance analysis,
- citation-grounded legal retrieval,
- auditability,
- explainable AI workflows,
- and cross-regulatory intelligence.

The platform helps businesses, fintechs, compliance teams, and legal teams understand:
- what regulations apply,
- what licenses are required,
- compliance risks,
- operational obligations,
- and regulatory gaps.

The system must prioritize:
- grounded retrieval,
- explainability,
- structured outputs,
- audit traces,
- and hallucination prevention.

Core regulators include:
- CBN
- SEC Nigeria
- NDIC
- FIRS

Future expansion may include:
- FCCPC
- NITDA
- NDPA
- BOFIA
- AML/CFT Acts

------------------------------------------------------------
# CORE ENGINEERING PRINCIPLES
------------------------------------------------------------

1. THIS IS NOT A CHATBOT
The system must not be implemented as:
Prompt -> LLM -> Response

Instead, the architecture is:
User Request -> FastAPI -> LangGraph Multi-Agent Workflow -> Retrieval/Reasoning -> Structured Compliance Output

2. AGENTIC WORKFLOWS
The platform uses specialized AI agents coordinated through LangGraph.

Agents include:
- Orchestrator Agent
- Research Agent
- Jurisdiction Mapping Agent
- Regulatory Reasoning Agent
- Compliance Auditor Agent
- Citation Verification Agent
- Critic Agent

3. EXPLAINABILITY FIRST
Every response should:
- contain citations,
- expose reasoning traces,
- support auditability,
- and avoid hallucinated claims.

4. RETRIEVAL-GROUNDED AI
Rule:
No retrieval -> No answer.

The system should avoid unsupported legal claims.

5. STRUCTURED OUTPUTS
Responses should prioritize:
- compliance checklists,
- risk matrices,
- obligations,
- licensing requirements,
- audit reports,
- and compliance gap analysis.

Do not generate only conversational paragraphs.

6. SEPARATION OF CONCERNS
Each layer must have a single responsibility:
- API Layer
- Orchestration Layer
- Retrieval Layer
- Agent Layer
- Repository Layer
- Database Layer
- Utility Layer

------------------------------------------------------------
# HIGH LEVEL ARCHITECTURE
------------------------------------------------------------

Frontend:
- Chainlit used as a Regulatory Intelligence Console
- NOT presented as a chatbot
- Used for workflow visualization and agent traces

Backend:
- FastAPI
- REST APIs
- Session management
- Workflow triggering
- Streaming
- Audit logging

AI Orchestration:
- LangGraph
- Stateful multi-agent workflows

Vector Database:
- Qdrant

Persistent Storage:
- PostgreSQL

Session/Cache:
- Redis

LLM Layer:
- Ollama or vLLM
- Qwen/Llama models

------------------------------------------------------------
# SYSTEM FLOW
------------------------------------------------------------

Example workflow:

User submits:
"Can we launch a wallet product with investment features?"

System flow:
1. FastAPI receives request
2. LangGraph workflow is triggered
3. Orchestrator decomposes tasks
4. Jurisdiction agent identifies regulators
5. Research agent retrieves regulations
6. Reasoning agent synthesizes obligations
7. Auditor agent calculates risks
8. Citation verifier validates evidence
9. Final structured report is generated
10. Audit trace is persisted

------------------------------------------------------------
# API ROUTES
------------------------------------------------------------

POST /upload-regulation
Purpose:
- Upload and ingest regulatory documents.
- Parse PDFs.
- Chunk legal sections.
- Generate embeddings.
- Store vectors in Qdrant.

POST /analyze-business
Purpose:
- Main regulatory intelligence endpoint.
- Analyze fintech/business models.
- Identify regulators.
- Determine licensing requirements.
- Generate risk assessments.
- Produce citation-backed compliance reports.

POST /compliance-gap-analysis
Purpose:
- Upload company compliance/policy documents.
- Compare against regulations.
- Detect missing controls.
- Generate gap analysis reports.

GET /audit-trace/{id}
Purpose:
- Retrieve workflow execution traces.
- Show agent decisions.
- Show citations used.
- Support explainability and transparency.

------------------------------------------------------------
# MULTI-AGENT RESPONSIBILITIES
------------------------------------------------------------

Orchestrator Agent:
- Coordinates workflow execution.
- Delegates tasks to agents.
- Maintains workflow state.

Research Agent:
- Retrieves regulations from vector DB.
- Uses semantic retrieval and reranking.

Jurisdiction Mapping Agent:
- Determines applicable regulators.
- Maps overlapping compliance obligations.

Regulatory Reasoning Agent:
- Performs legal reasoning.
- Synthesizes obligations across multiple regulations.

Compliance Auditor Agent:
- Generates risk assessments.
- Detects compliance gaps.
- Produces structured compliance recommendations.

Citation Verification Agent:
- Ensures all claims are grounded.
- Verifies citations exist.
- Prevents hallucinated references.

Critic Agent:
- Reviews outputs.
- Detects inconsistencies.
- Challenges weak reasoning.

------------------------------------------------------------
# SESSION AND STATE MANAGEMENT
------------------------------------------------------------

The platform is stateful.

Sessions should persist:
- organization context,
- prior analyses,
- workflow traces,
- uploaded documents,
- compliance history,
- and audit logs.

Redis:
- active workflow state
- caching
- streaming state

PostgreSQL:
- persistent audit traces
- compliance reports
- user/session history

LangGraph:
- workflow state
- agent state transitions

------------------------------------------------------------
# LEGAL DOCUMENT INGESTION
------------------------------------------------------------

Documents include:
- CBN guidelines
- SEC rules
- NDIC regulations
- FIRS regulations

Document ingestion flow:
1. Upload PDF
2. Parse document
3. Extract sections/subsections
4. Chunk legal text semantically
5. Generate metadata
6. Generate embeddings
7. Store in Qdrant

Chunking should preserve:
- section numbers,
- titles,
- page numbers,
- hierarchy,
- citations.

Avoid arbitrary chunking.

------------------------------------------------------------
# REPOSITORY STRUCTURE
------------------------------------------------------------

backend/
│
├── app/
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── regulations.py
│   │   │   ├── analysis.py
│   │   │   ├── audit.py
│   │   │   └── health.py
│   │   │
│   │   └── dependencies.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── logging.py
│   │   └── constants.py
│   │
│   ├── agents/
│   │   ├── orchestrator.py
│   │   ├── researcher.py
│   │   ├── auditor.py
│   │   ├── critic.py
│   │   ├── citation_verifier.py
│   │   └── jurisdiction_mapper.py
│   │
│   ├── graph/
│   │   ├── workflow.py
│   │   ├── state.py
│   │   └── nodes.py
│   │
│   ├── services/
│   │   ├── ingestion_service.py
│   │   ├── embedding_service.py
│   │   ├── retrieval_service.py
│   │   ├── audit_service.py
│   │   └── compliance_service.py
│   │
│   ├── repositories/
│   │   ├── vector_repository.py
│   │   ├── document_repository.py
│   │   └── audit_repository.py
│   │
│   ├── models/
│   │   ├── requests.py
│   │   ├── responses.py
│   │   └── database_models.py
│   │
│   ├── db/
│   │   ├── postgres.py
│   │   └── qdrant.py
│   │
│   ├── utils/
│   │   ├── chunking.py
│   │   ├── citations.py
│   │   ├── parsers.py
│   │   └── reranking.py
│   │
│   └── main.py
│
├── tests/
│
├── docker-compose.yml
├── requirements.txt
└── README.md

------------------------------------------------------------
# IMPLEMENTATION EXPECTATIONS
------------------------------------------------------------

Code generated for this project should:
- follow clean architecture principles,
- support async execution where appropriate,
- use dependency injection patterns,
- separate business logic from routes,
- keep agents modular,
- avoid tightly coupled implementations,
- use typed Pydantic models,
- support observability and logging,
- and prioritize maintainability.

Prefer:
- service classes,
- repository abstractions,
- reusable utilities,
- and composable agent workflows.

Avoid:
- monolithic files,
- business logic inside API routes,
- tightly coupled agent code,
- and chatbot-style implementations.

------------------------------------------------------------
# UI/UX EXPECTATIONS
------------------------------------------------------------

Chainlit should behave as:
- a Regulatory Intelligence Console,
NOT:
- a generic chatbot.

The UI should expose:
- workflow stages,
- agent traces,
- compliance analysis,
- risk scoring,
- citations,
- and audit information.

The UI should feel:
- enterprise-grade,
- explainable,
- and workflow-oriented.

------------------------------------------------------------
# GOAL OF THE MVP
------------------------------------------------------------

The MVP should demonstrate:
- multi-agent orchestration,
- grounded legal retrieval,
- citation-backed reasoning,
- explainability,
- auditability,
- and structured compliance intelligence.

The goal is NOT to build:
- a generic legal chatbot.

The goal IS to build:
- an AI Regulatory Intelligence Platform.