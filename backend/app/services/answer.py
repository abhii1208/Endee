import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import List, Optional

from loguru import logger

from backend.app.config import get_settings
from backend.app.models.domain import SearchResultItem


def is_llm_enabled() -> bool:
    settings = get_settings()
    return bool(settings.llm_api_key)


def _call_llm(system_prompt: str, user_prompt: str) -> Optional[str]:
    settings = get_settings()
    try:
        import openai
    except ImportError:
        return None
    openai.api_key = settings.llm_api_key
    response = openai.ChatCompletion.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    if response and response.choices:
        return response.choices[0].message.get("content")
    return None


def generate_answer(query: str, context_items: List[SearchResultItem]) -> Optional[str]:
    if not is_llm_enabled():
        return None

    settings = get_settings()
    timeout = settings.llm_timeout_seconds
    max_retries = max(0, settings.llm_max_retries)

    context_text_parts = []
    for idx, item in enumerate(context_items[:5]):
        context_text_parts.append(
            f"[{idx+1}] ({item.type.value.upper()}) {item.title}\n"
            f"Snippet: {item.snippet}\n"
            f"Product: {item.product} | Severity: {item.severity}\n"
        )
    context_text = "\n\n".join(context_text_parts)
    system_prompt = (
        "You are a senior support engineer. "
        "Given the user's issue and relevant historical tickets, FAQs, and runbooks, "
        "compose a clear, step-by-step response. "
        "If unsure, be honest about uncertainties."
    )
    user_prompt = (
        f"User issue:\n{query}\n\n"
        f"Relevant context:\n{context_text}\n\n"
        "Write a proposed response to the user and, if appropriate, "
        "include concrete troubleshooting steps and references to the context items."
    )

    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            with ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(_call_llm, system_prompt, user_prompt)
                result = future.result(timeout=timeout)
            if result is not None:
                return result
        except FuturesTimeoutError:
            last_exc = TimeoutError(f"LLM call timed out after {timeout}s")
            logger.warning("LLM attempt %s timed out", attempt + 1)
        except Exception as exc:
            last_exc = exc
            logger.warning("LLM attempt %s failed: %s", attempt + 1, exc)
        if attempt < max_retries:
            time.sleep(1.0 * (attempt + 1))
    if last_exc:
        logger.exception("LLM generation failed after retries: %s", last_exc)
    return None

