from typing import List, Optional

from loguru import logger

from backend.app.config import get_settings
from backend.app.models.domain import SearchResultItem


def is_llm_enabled() -> bool:
    """
    Check whether LLM-based answer generation is configured.
    """

    settings = get_settings()
    return bool(settings.llm_api_key)


def generate_answer(query: str, context_items: List[SearchResultItem]) -> Optional[str]:
    """
    Generate an answer using the configured LLM provider.

    For portability, this function uses a simple HTTP-based interface
    (e.g. OpenAI-compatible APIs). If no API key is configured,
    the function returns None and the caller should handle gracefully.
    """

    if not is_llm_enabled():
        return None

    settings = get_settings()

    try:
        import openai
    except ImportError:
        logger.warning("openai package not installed; skipping LLM generation.")
        return None

    openai.api_key = settings.llm_api_key

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

    try:
        response = openai.ChatCompletion.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
    except Exception as exc:
        logger.exception(f"LLM generation failed: {exc}")
        return None

    content = (
        response.choices[0].message["content"]
        if response and response.choices
        else None
    )
    return content

