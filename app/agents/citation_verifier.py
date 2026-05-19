from app.prompts.citation_verifier import CITATION_VERIFIER_SYSTEM_PROMPT
from app.utils.llm_client import chat
import json
import logging

logger = logging.getLogger(__name__)


async def run_citation_verification(
    reasoning_result: dict,
    audit_result: dict,
    retrieved_chunks: list[dict],
) -> dict:
    chunks_text = "\n\n".join(
        f"[CHUNK_ID: {i} | {c.get('regulator', '')} | {c.get('source', '')} | {c.get('section', '')}]\n{c.get('text', '')}"
        for i, c in enumerate(retrieved_chunks)
    )
    user_message = (
        f"Legal reasoning output:\n{json.dumps(reasoning_result, indent=2)}\n\n"
        f"Audit output:\n{json.dumps(audit_result, indent=2)}\n\n"
        f"Retrieved evidence chunks (ground truth):\n{chunks_text}\n\n"
        "Verify every claim and citation in the above against the evidence chunks. "
        "Return your verification as a JSON object matching the output format in your instructions."
    )

    messages = [
        {"role": "system", "content": CITATION_VERIFIER_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    logger.info("[CITATION] Calling LLM...")
    content = await chat(messages, timeout=120.0)

    try:
        clean = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        logger.warning("[CITATION] LLM response was not valid JSON — returning raw content")
        return {
            "verified_citations": [],
            "failed_citations": [],
            "overall_grounding_score": 0,
            "hallucination_risk": "HIGH",
            "recommendation": "REJECT",
            "raw_feedback": content,
        }