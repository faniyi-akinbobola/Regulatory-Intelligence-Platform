from app.prompts.reasoning import REASONING_SYSTEM_PROMPT
from app.utils.llm_client import chat
import json
import logging

logger = logging.getLogger(__name__)


async def run_reasoning(
    query: str,
    retrieved_chunks: list[dict],
    jurisdiction_result: dict,
) -> dict:
    chunks_text = "\n\n".join(
        f"[{c.get('regulator', '')} | {c.get('source', '')} | {c.get('section', '')} | Page {c.get('page', '')}]\n{c.get('text', '')}"
        for c in retrieved_chunks
    )
    regulators = ", ".join(
        r.get("regulator", "") for r in jurisdiction_result.get("applicable_regulators", [])
    )
    user_message = (
        f"Original query: {query}\n\n"
        f"Applicable regulators: {regulators}\n\n"
        f"Retrieved regulation chunks:\n{chunks_text}\n\n"
        "Perform full legal synthesis on the above. "
        "Return your analysis as a JSON object matching the output format in your instructions."
    )

    messages = [
        {"role": "system", "content": REASONING_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    logger.info("[REASONING] Calling LLM...")
    content = await chat(messages, timeout=180.0)

    try:
        clean = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        logger.warning("[REASONING] LLM response was not valid JSON — returning raw content")
        return {
            "obligations": [],
            "prohibitions": [],
            "permissions": [],
            "conflicts": [],
            "reasoning_summary": content,
            "confidence": "LOW",
        }