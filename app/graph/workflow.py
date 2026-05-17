from langgraph.graph import StateGraph, END
from app.graph.nodes import (
    orchestrator_node,
    jurisdiction_node,
    research_node,
    reasoning_node,
    auditor_node,
    citation_node,
    critic_node,
    route_after_critic,
)
from app.graph.state import AgentState


def build_workflow():
    """Builds and compiles the LangGraph multi-agent workflow."""
    graph = StateGraph(AgentState)

    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("jurisdiction", jurisdiction_node)
    graph.add_node("research", research_node)
    graph.add_node("reasoning", reasoning_node)
    graph.add_node("auditor", auditor_node)
    graph.add_node("citation_verifier", citation_node)
    graph.add_node("critic", critic_node)

    graph.set_entry_point("orchestrator")
    graph.add_edge("orchestrator", "jurisdiction")
    graph.add_edge("jurisdiction", "research")
    graph.add_edge("research", "reasoning")
    graph.add_edge("reasoning", "auditor")
    graph.add_edge("auditor", "citation_verifier")
    graph.add_edge("citation_verifier", "critic")

    # Critic either loops back to reasoning or ends
    graph.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "reasoning": "reasoning",
            "end": END,
        },
    )

    return graph.compile()


# Compiled workflow — import this in compliance_service.py
workflow = build_workflow()