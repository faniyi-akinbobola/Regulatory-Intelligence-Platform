from typing import TypedDict


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

    # Loop control — critic can trigger a re-run of reasoning+audit
    iteration_count: int
    max_iterations: int

    # Workflow metadata for audit trace
    agent_trace: list[dict]
