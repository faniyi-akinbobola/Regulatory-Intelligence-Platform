import asyncio
import logging
import time
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


async def orchestrator_jurisdiction_node(state: AgentState) -> AgentState:
    """Runs orchestrator and jurisdiction mapper in parallel — saves ~8–12s per request."""
    t0 = time.time()
    logger.info("▶ [1-2/7] ORCHESTRATOR + JURISDICTION MAPPER — running in parallel")

    orch_task = run_orchestrator(
        query=state.get("query", ""),
        organization_context=state.get("organization_context"),
    )
    jur_task = run_jurisdiction_mapping(
        query=state.get("query", ""),
        context_summary=state.get("organization_context") or "",
    )
    orch_result, jur_result = await asyncio.gather(orch_task, jur_task)

    # Jurisdiction mapper is more specialised — use its regulator list as primary
    jur_regulators = [
        r.get("regulator")
        for r in jur_result.get("applicable_regulators", [])
        if r.get("regulator")
    ]
    target_regulators = jur_regulators or orch_result.get("target_regulators", [])

    logger.info(
        "✔ [1-2/7] ORCHESTRATOR + JURISDICTION — done in %.1fs | regulators=%s",
        time.time() - t0, target_regulators,
    )

    trace = list(state.get("agent_trace", []))
    trace.append({"agent": "orchestrator", "status": "completed"})
    trace.append({"agent": "jurisdiction_mapper", "status": "completed"})

    return {
        **state,
        "iteration_count": 0,
        "max_iterations": state.get("max_iterations", 2),
        "target_regulators": target_regulators,
        "jurisdiction_result": jur_result,
        "agent_trace": trace,
    }


async def orchestrator_node(state: AgentState) -> AgentState:
    """Orchestrator node: decomposes the query and identifies target regulators."""
    t0 = time.time()
    logger.info("▶ [1/7] ORCHESTRATOR — decomposing query")
    result = await run_orchestrator(
        query=state.get("query", ""),
        organization_context=state.get("organization_context"),
    )
    logger.info("✔ [1/7] ORCHESTRATOR — done in %.1fs | regulators=%s", time.time() - t0, result.get("target_regulators", []))
    return {
        **state,
        "iteration_count": 0,
        "max_iterations": state.get("max_iterations", 2),
        "target_regulators": result.get("target_regulators", []),
        "agent_trace": _trace(state, "orchestrator"),
    }


async def jurisdiction_node(state: AgentState) -> AgentState:
    """Jurisdiction node: maps the query to applicable regulators."""
    t0 = time.time()
    logger.info("▶ [2/7] JURISDICTION MAPPER — identifying applicable regulators")
    result = await run_jurisdiction_mapping(
        query=state.get("query", ""),
        context_summary=state.get("organization_context") or "",
    )
    mapped = [r.get("regulator") for r in result.get("applicable_regulators", []) if r.get("regulator")]
    logger.info("✔ [2/7] JURISDICTION MAPPER — done in %.1fs | mapped=%s", time.time() - t0, mapped)
    return {
        **state,
        "jurisdiction_result": result,
        "target_regulators": mapped,
        "agent_trace": _trace(state, "jurisdiction_mapper"),
    }


async def research_node(state: AgentState) -> AgentState:
    """Research node: retrieves relevant chunks for the query."""
    target_regulators = state.get("target_regulators") or []
    t0 = time.time()
    logger.info("▶ [3/7] RESEARCH AGENT — retrieving chunks | regulators=%s", target_regulators)
    retrieval_service = await _get_retrieval_service()
    chunks = await retrieval_service.retrieve(
        query=state.get("query", ""),
        filter_regulators=target_regulators if target_regulators else None,
    )
    logger.info("✔ [3/7] RESEARCH AGENT — done in %.1fs | %d chunks retrieved", time.time() - t0, len(chunks))
    return {
        **state,
        "retrieved_chunks": chunks,
        "agent_trace": _trace(state, "researcher"),
    }


async def reasoning_node(state: AgentState) -> AgentState:
    """Reasoning node: synthesises information from retrieved chunks."""
    chunks = state.get("retrieved_chunks", [])
    t0 = time.time()
    logger.info("▶ [4/7] REASONING AGENT — synthesising from %d chunks", len(chunks))
    result = await run_reasoning(
        query=state.get("query", ""),
        retrieved_chunks=chunks,
        jurisdiction_result=state.get("jurisdiction_result") or {},
    )
    logger.info("✔ [4/7] REASONING AGENT — done in %.1fs | obligations=%d prohibitions=%d",
                time.time() - t0, len(result.get("obligations", [])), len(result.get("prohibitions", [])))
    return {
        **state,
        "reasoning_result": result,
        "agent_trace": _trace(state, "reasoning"),
    }


async def auditor_node(state: AgentState) -> AgentState:
    """Auditor node: generates compliance risk assessment."""
    t0 = time.time()
    logger.info("▶ [5/7] COMPLIANCE AUDITOR — generating risk assessment")
    result = await run_audit(
        query=state.get("query", ""),
        reasoning_result=state.get("reasoning_result") or {},
        retrieved_chunks=state.get("retrieved_chunks", []),
    )
    logger.info("✔ [5/7] COMPLIANCE AUDITOR — done in %.1fs | risk=%s score=%s",
                time.time() - t0, result.get("risk_level"), result.get("risk_score"))
    return {
        **state,
        "audit_result": result,
        "agent_trace": _trace(state, "auditor"),
    }


async def citation_node(state: AgentState) -> AgentState:
    """Citation node: verifies claims against retrieved chunks."""
    t0 = time.time()
    logger.info("▶ [6/7] CITATION VERIFIER — checking all claims against evidence")
    result = await run_citation_verification(
        reasoning_result=state.get("reasoning_result") or {},
        audit_result=state.get("audit_result") or {},
        retrieved_chunks=state.get("retrieved_chunks", []),
    )
    logger.info("✔ [6/7] CITATION VERIFIER — done in %.1fs | grounding=%.0f%% hallucination_risk=%s",
                time.time() - t0,
                (result.get("overall_grounding_score") or 0) * 100,
                result.get("hallucination_risk"))
    return {
        **state,
        "citation_result": result,
        "agent_trace": _trace(state, "citation_verifier"),
    }


async def critic_node(state: AgentState) -> AgentState:
    """Critic node: assesses output quality and determines if a re-run is needed."""
    iteration = state.get("iteration_count", 0) + 1
    t0 = time.time()
    logger.info("▶ [7/7] CRITIC AGENT — reviewing output quality (iteration %d/%d)",
                iteration, state.get("max_iterations", 2))
    result = await run_critic(
        query=state.get("query", ""),
        reasoning_result=state.get("reasoning_result") or {},
        audit_result=state.get("audit_result") or {},
        citation_result=state.get("citation_result") or {},
    )
    logger.info("✔ [7/7] CRITIC AGENT — done in %.1fs | assessment=%s quality_score=%s",
                time.time() - t0, result.get("overall_assessment"), result.get("quality_score"))
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
