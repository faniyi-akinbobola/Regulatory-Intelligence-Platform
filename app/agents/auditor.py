from app.prompts.citation_verifier import CITATION_VERIFIER_PROMPT
from app.core.config import settings
import httpx
import json
import logging

logger = logging.getLogger(__name__)

model = settings.llm_model_name
ollama_url = settings.llm_base_url

async def run_audit(query: str, reasoning_result: dict) -> dict:
    user_message = (
        f"Original query: {query}\n\n"
        f"Reasoning output:\n{json.dumps(reasoning_result, indent=2)}\n\n"
        "Audit the reasoning output for correctness, completeness, and potential issues. "
        "Return your audit as a JSON object matching the output format in your instructions."
    )

    messages = [
        {"role": "system", "content": CITATION_VERIFIER_PROMPT},
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
        logger.warning("[AUDITOR] LLM response was not valid JSON — returning raw content")
        return {
            "correctness": "UNKNOWN",
            "completeness": "UNKNOWN",
            "potential_issues": [],
            "raw_feedback": content,
        }