from app.prompts.citation_verifier import CITATION_VERIFIER_PROMPT
from app.core.config import settings
import httpx
import json
import logging

logger = logging.getLogger(__name__)

model = settings.llm_model_name
ollama_url = settings.llm_base_url

async def run_reasoning() -> dict:
    # Placeholder for future reasoning logic — for now just returns an empty dict
    return {}
