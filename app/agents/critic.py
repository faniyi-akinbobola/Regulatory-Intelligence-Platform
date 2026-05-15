from app.prompts.critic import CRITIC_SYSTEM_PROMPT
from app.core.config import settings
import httpx
import json
import logging

logger = logging.getLogger(__name__)

model = settings.llm_model_name
ollama_url = settings.llm_base_url


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

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{ollama_url}/api/chat",
            json={"model": model, "messages": messages, "stream": False},
        )

    if response.status_code != 200:
        raise ValueError(f"LLM API error: {response.status_code} {response.text}")

    content = response.json().get("message", {}).get("content", "")

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