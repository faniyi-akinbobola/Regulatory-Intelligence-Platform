import httpx
import logging
from app.core.config import settings
from app.utils import cost_tracker

logger = logging.getLogger(__name__)


async def chat(messages: list[dict], timeout: float = 120.0) -> str:
    """
    Unified LLM client. Routes to OpenAI or Ollama based on settings.llm_provider.
    Returns the raw assistant message text. Token usage is automatically
    accumulated into the current-context cost tracker.
    """
    if settings.llm_provider == "openai":
        return await _openai_chat(messages, timeout)
    return await _ollama_chat(messages, timeout)


async def _openai_chat(messages: list[dict], timeout: float) -> str:
    logger.debug("[LLM] Calling OpenAI model=%s", settings.openai_model)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            settings.openai_url,
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={"model": settings.openai_model, "messages": messages},
        )
    if response.status_code != 200:
        raise ValueError(f"OpenAI API error: {response.status_code} {response.text}")
    data = response.json()
    usage = data.get("usage", {})
    cost_tracker.record(
        model=settings.openai_model,
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
    )
    logger.debug(
        "[LLM] tokens — prompt=%d completion=%d",
        usage.get("prompt_tokens", 0),
        usage.get("completion_tokens", 0),
    )
    return data["choices"][0]["message"]["content"]


async def _ollama_chat(messages: list[dict], timeout: float) -> str:
    logger.debug("[LLM] Calling Ollama model=%s", settings.llm_model_name)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            f"{settings.llm_base_url}/api/chat",
            json={"model": settings.llm_model_name, "messages": messages, "stream": False},
        )
    if response.status_code != 200:
        raise ValueError(f"Ollama API error: {response.status_code} {response.text}")
    return response.json()["message"]["content"]
