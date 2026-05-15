import logging
from app.graph.state import AgentState

logger = logging.getLogger(__name__)


def _trace(state: AgentState, agent: str) -> list[dict]:
    """Appends an agent execution entry to the audit trace."""
    trace = list(state.get("agent_trace", []))
    trace.append({"agent": agent, "status": "completed"})
    return trace


async def orchestrator_node(state: AgentState) -> AgentState:
    logger.info("[ORCHESTRATOR] Decomposing query: %s", state.get("query"))
    # TODO: call OrchestratorAgent with ORCHESTRATOR_SYSTEM_PROMPT
    return {
        **state,
        "iteration_count": 0,
        "max_iterations": state.get("max_iterations", 2),
        "agent_trace": _trace(state, "orchestrator"),
    }


async def jurisdiction_node(state: AgentState) -> AgentState:
    logger.info("[JURISDICTION] Mapping regulators for query")
    # TODO: call JurisdictionMapperAgent with JURISDICTION_MAPPER_SYSTEM_PROMPT
    return {
        **state,
        "jurisdiction_result": {},
        "target_regulators": [],
        "agent_trace": _trace(state, "jurisdiction_mapper"),
    }


async def research_node(state: AgentState) -> AgentState:
    logger.info("[RESEARCH] Retrieving regulation chunks for query")
    # TODO: call RetrievalService with target_regulators as filter
    return {
        **state,
        "retrieved_chunks": [],
        "agent_trace": _trace(state, "researcher"),
    }


async def reasoning_node(state: AgentState) -> AgentState:
    logger.info(
        "[REASONING] Synthesising legal obligations from %d chunks",
        len(state.get("retrieved_chunks", [])),
    )
    # TODO: call RegulatoryReasoningAgent with REASONING_SYSTEM_PROMPT
    return {
        **state,
        "reasoning_result": {},
        "agent_trace": _trace(state, "reasoning"),
    }


async def auditor_node(state: AgentState) -> AgentState:
    logger.info("[AUDITOR] Generating compliance risk assessment")
    # TODO: call ComplianceAuditorAgent with AUDITOR_SYSTEM_PROMPT
    return {
        **state,
        "audit_result": {},
        "agent_trace": _trace(state, "auditor"),
    }


async def citation_node(state: AgentState) -> AgentState:
    logger.info("[CITATION] Verifying claims against retrieved chunks")
    # TODO: call CitationVerifierAgent with CITATION_VERIFIER_SYSTEM_PROMPT
    return {
        **state,
        "citation_result": {},
        "agent_trace": _trace(state, "citation_verifier"),
    }


async def critic_node(state: AgentState) -> AgentState:
    iteration = state.get("iteration_count", 0) + 1
    logger.info("[CRITIC] Reviewing output quality (iteration %d)", iteration)
    # TODO: call CriticAgent with CRITIC_SYSTEM_PROMPT
    return {
        **state,
        "critic_result": {},
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


