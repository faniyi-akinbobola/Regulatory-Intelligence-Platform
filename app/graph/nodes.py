import logging
from app.graph.state import AgentState
from app.agents.orchestrator import run_orchestrator
from app.agents.jurisdiction_mapper import run_jurisdiction_mapping
from app.agents.reasoning import run_reasoning
from app.agents.auditor import run_audit
from app.agents.citation_verifier import run_citation_verification
from app.agents.critic import run_critic
from app.services.retrieval_service import RetrievalService
from app.services.embedding_service import EmbeddingService
from app.services.sparse_embedding_service import SparseEmbeddingService
from app.repositories.vector_repository import VectorRepository
from app.core.config import settings

logger = logging.getLogger(__name__)

_retrieval_service: RetrievalService | None = None


async def _get_retrieval_service() -> RetrievalService:
    
    global _retrieval_service
    if _retrieval_service is None:
        from app.db.qdrant import get_qdrant_client
        client = await get_qdrant_client()
        _retrieval_service = RetrievalService(
            embedding_service=EmbeddingService(settings.embedding_model_name),
            vector_repository=VectorRepository(client),
            sparse_embedding_service=SparseEmbeddingService(),
        )
    return _retrieval_service


def _trace(state: AgentState, agent: str) -> list[dict]:
    """Appends an agent execution entry to the audit trace."""
    trace = list(state.get("agent_trace", []))
    trace.append({"agent": agent, "status": "completed"})
    return trace


async def orchestrator_node(state: AgentState) -> AgentState:
    """Orchestrator node: decomposes the query and identifies target regulators."""
    logger.info("[ORCHESTRATOR] Decomposing query: %s", state.get("query"))
    result = await run_orchestrator(
        query=state.get("query", ""),
        organization_context=state.get("organization_context"),
    )
    return {
        **state,
        "iteration_count": 0,
        "max_iterations": state.get("max_iterations", 2),
        "target_regulators": result.get("target_regulators", []),
        "agent_trace": _trace(state, "orchestrator"),
    }


async def jurisdiction_node(state: AgentState) -> AgentState:
    """Jurisdiction node: maps the query to applicable regulators."""
    logger.info("[JURISDICTION] Mapping regulators for query")
    result = await run_jurisdiction_mapping(
        query=state.get("query", ""),
        context_summary=state.get("organization_context") or "",
    )
    return {
        **state,
        "jurisdiction_result": result,
        "target_regulators": [
            r.get("regulator") for r in result.get("applicable_regulators", [])
            if r.get("regulator")
        ],
        "agent_trace": _trace(state, "jurisdiction_mapper"),
    }


async def research_node(state: AgentState) -> AgentState:
    """Research node: retrieves relevant chunks for the query."""
    target_regulators = state.get("target_regulators") or []
    logger.info(
        "[RESEARCH] Retrieving chunks for query, regulators=%s",
        target_regulators,
    )
    retrieval_service = await _get_retrieval_service()
    chunks = await retrieval_service.retrieve(
        query=state.get("query", ""),
        filter_regulators=target_regulators if target_regulators else None,
    )
    logger.info("[RESEARCH] Retrieved %d chunks", len(chunks))
    return {
        **state,
        "retrieved_chunks": chunks,
        "agent_trace": _trace(state, "researcher"),
    }


async def reasoning_node(state: AgentState) -> AgentState:
    """Reasoning node: synthesises information from retrieved chunks."""
    chunks = state.get("retrieved_chunks", [])
    logger.info("[REASONING] Synthesising from %d chunks", len(chunks))
    result = await run_reasoning(
        query=state.get("query", ""),
        retrieved_chunks=chunks,
        jurisdiction_result=state.get("jurisdiction_result") or {},
    )
    return {
        **state,
        "reasoning_result": result,
        "agent_trace": _trace(state, "reasoning"),
    }


async def auditor_node(state: AgentState) -> AgentState:
    """Auditor node: generates compliance risk assessment."""
    logger.info("[AUDITOR] Generating compliance risk assessment")
    result = await run_audit(
        query=state.get("query", ""),
        reasoning_result=state.get("reasoning_result") or {},
        retrieved_chunks=state.get("retrieved_chunks", []),
    )
    return {
        **state,
        "audit_result": result,
        "agent_trace": _trace(state, "auditor"),
    }


async def citation_node(state: AgentState) -> AgentState:
    """Citation node: verifies claims against retrieved chunks."""
    logger.info("[CITATION] Verifying claims against retrieved chunks")
    result = await run_citation_verification(
        reasoning_result=state.get("reasoning_result") or {},
        audit_result=state.get("audit_result") or {},
        retrieved_chunks=state.get("retrieved_chunks", []),
    )
    return {
        **state,
        "citation_result": result,
        "agent_trace": _trace(state, "citation_verifier"),
    }


async def critic_node(state: AgentState) -> AgentState:
    """Critic node: assesses output quality and determines if a re-run is needed."""
    iteration = state.get("iteration_count", 0) + 1
    logger.info("[CRITIC] Reviewing output quality (iteration %d)", iteration)
    result = await run_critic(
        query=state.get("query", ""),
        reasoning_result=state.get("reasoning_result") or {},
        audit_result=state.get("audit_result") or {},
        citation_result=state.get("citation_result") or {},
    )
    return {
        **state,
        "critic_result": result,
        "iteration_count": iteration,
        "agent_trace": _trace(state, "critic"),
    }


def route_after_critic(state: AgentState) -> str:
    """
    Routing function after the critic node.
    Loops back to reasoning if quality is poor and iterations remain.
    Otherwise ends the workflow.
    """
    critic_result = state.get("critic_result", {})
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 2)

    overall_assessment = critic_result.get("overall_assessment", "PASS")
    quality_score = critic_result.get("quality_score", 10)

    if overall_assessment == "FAIL" and iteration_count < max_iterations:
        logger.info(
            "[CRITIC] Quality insufficient (score=%s) — looping back to reasoning",
            quality_score,
        )
        return "reasoning"

    logger.info(
        "[CRITIC] Assessment: %s (score=%s) — proceeding to END",
        overall_assessment,
        quality_score,
    )
    return "end"
