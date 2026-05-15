from app.prompts.citation_verifier import CITATION_VERIFIER_PROMPT
from app.core.config import settings
import httpx
import json
import logging

logger = logging.getLogger(__name__)

model = settings.llm_model_name
ollama_url = settings.llm_base_url

def run_orchestrator(
    query: str,
    reasoning_result: dict,
    audit_result: dict,
    citation_result: dict,
) -> dict:
    # For now this is just a placeholder that returns the inputs — in the future it could do more complex orchestration logic if needed
    return {
        "query": query,
        "reasoning_result": reasoning_result,
        "audit_result": audit_result,
        "citation_result": citation_result,
    }