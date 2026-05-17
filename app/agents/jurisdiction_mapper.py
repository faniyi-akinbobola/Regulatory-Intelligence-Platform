from app.prompts.jurisdiction_mapper import JURISDICTION_MAPPER_SYSTEM_PROMPT
from app.utils.llm_client import chat
import json
import logging

logger = logging.getLogger(__name__)


async def run_jurisdiction_mapping(query: str, context_summary: str) -> dict:
    user_message = (
        f"Business/regulatory query: {query}\n\n"
        f"Context: {context_summary}\n\n"
        "Identify all applicable Nigerian regulators and map jurisdictional overlaps. "
        "Return your response as a JSON object matching the output format in your instructions."
    )

    messages = [
        {"role": "system", "content": JURISDICTION_MAPPER_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    logger.info("[JURISDICTION] Calling LLM...")
    content = await chat(messages, timeout=60.0)

    try:
        clean = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        logger.warning("[JURISDICTION] LLM response was not valid JSON — returning raw content")
        return {
            "applicable_regulators": [],
            "overlap_risks": [],
            "primary_regulator": "UNKNOWN",
            "raw_feedback": content,
        }