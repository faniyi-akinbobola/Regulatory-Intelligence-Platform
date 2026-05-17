from app.prompts.orchestrator import ORCHESTRATOR_SYSTEM_PROMPT
from app.utils.llm_client import chat
import json
import logging

logger = logging.getLogger(__name__)


async def run_orchestrator(query: str, organization_context: str | None = None) -> dict:
    context_line = f"\nOrganisation context: {organization_context}" if organization_context else ""
    user_message = (
        f"Regulatory query:{context_line}\n{query}\n\n"
        "Decompose this query and produce a structured orchestration plan. "
        "Return your response as a JSON object matching the output format in your instructions."
    )

    messages = [
        {"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    logger.info("[ORCHESTRATOR] Calling LLM...")
    content = await chat(messages, timeout=60.0)

    try:
        clean = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        logger.warning("[ORCHESTRATOR] LLM response was not valid JSON — returning raw content")
        return {
            "task_breakdown": [],
            "target_regulators": [],
            "context_summary": content,
            "query_type": "GENERAL_REGULATORY",
        }