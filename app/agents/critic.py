from app.prompts.critic import CRITIC_SYSTEM_PROMPT
from app.utils.llm_client import chat
import json
import logging

logger = logging.getLogger(__name__)

async def run_critic(
    query: str,
    reasoning_result: dict,
    audit_result: dict,
    citation_result: dict,
) -> dict:
    user_message = (
        f"Original query: {query}\n\n"
        f"Reasoning output:\n{json.dumps(reasoning_result, indent=2)}\n\n"
        f"Audit output:\n{json.dumps(audit_result, indent=2)}\n\n"
        f"Citation verification output:\n{json.dumps(citation_result, indent=2)}\n\n"
        "Review the above agent outputs critically. "
        "Return your assessment as a JSON object matching the output format in your instructions."
    )

    messages = [
        {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    logger.info("[CRITIC] Calling LLM...")
    content = await chat(messages, timeout=120.0)

    try:
        # Strip markdown code fences if the model wraps JSON in them
        clean = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        logger.warning("[CRITIC] LLM response was not valid JSON — returning raw content")
        return {
            "overall_assessment": "FAIL",
            "quality_score": 0,
            "summary_feedback": content,
            "issues_found": [],
            "missing_analysis": [],
        }