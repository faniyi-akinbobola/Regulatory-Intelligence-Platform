from app.prompts.auditor import AUDITOR_SYSTEM_PROMPT
from app.utils.llm_client import chat
import json
import logging

logger = logging.getLogger(__name__)


async def run_audit(query: str, reasoning_result: dict, retrieved_chunks: list[dict]) -> dict:
    chunks_text = "\n\n".join(
        f"[{c.get('regulator', '')} | {c.get('source', '')} | {c.get('section', '')}]\n{c.get('text', '')}"
        for c in retrieved_chunks[:10]
    )
    user_message = (
        f"Original query: {query}\n\n"
        f"Legal reasoning output:\n{json.dumps(reasoning_result, indent=2)}\n\n"
        f"Supporting regulation chunks:\n{chunks_text}\n\n"
        "Perform a full compliance audit of the above. "
        "Return your assessment as a JSON object matching the output format in your instructions."
    )

    messages = [
        {"role": "system", "content": AUDITOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    logger.info("[AUDITOR] Calling LLM...")
    content = await chat(messages, timeout=120.0)

    try:
        clean = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        logger.warning("[AUDITOR] LLM response was not valid JSON — returning raw content")
        return {
            "risk_score": 0,
            "risk_level": "UNKNOWN",
            "compliance_gaps": [],
            "compliance_checklist": [],
            "licensing_requirements": [],
            "recommendations": [],
            "raw_feedback": content,
        }