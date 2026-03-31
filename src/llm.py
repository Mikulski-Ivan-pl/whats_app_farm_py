import logging
import time

from cerebras.cloud.sdk import APIConnectionError, APIStatusError, Cerebras

from config import settings

logger = logging.getLogger(__name__)

_client = Cerebras(api_key=settings.llm_api_key)

_ROLE_MAP = {"bot": "assistant", "user": "user"}

_RETRY_DELAYS = (2, 4, 8)

_SUMMARIZE_PROMPT = (
    "Summarize the following conversation briefly and clearly. "
    "Focus on key topics, decisions, and context that would help continue the conversation. "
    "Reply with the summary only, no preamble."
)


def _call_with_retry(fn, *args, **kwargs):
    """Call fn(*args, **kwargs) with up to 3 retries on transient Cerebras errors.

    Retries on APIStatusError with status_code >= 500 and APIConnectionError.
    Delays: 2s, 4s, 8s between attempts. Raises the last exception on exhaustion.
    """
    last_exc = None
    for attempt, delay in enumerate((*_RETRY_DELAYS, None), start=1):
        try:
            return fn(*args, **kwargs)
        except APIStatusError as exc:
            if exc.status_code < 500:
                raise
            last_exc = exc
            logger.warning(
                "cerebras API server error status=%d attempt=%d/%d",
                exc.status_code,
                attempt,
                len(_RETRY_DELAYS) + 1,
            )
        except APIConnectionError as exc:
            last_exc = exc
            logger.warning(
                "cerebras API connection error type=%s attempt=%d/%d",
                type(exc).__name__,
                attempt,
                len(_RETRY_DELAYS) + 1,
            )
        if delay is not None:
            time.sleep(delay)
    raise last_exc


def get_reply(messages: list[dict], summary: str = "", system_prompt: str = "") -> str:
    """Send conversation history to Cerebras and return the AI reply.

    Maps Go role names ('bot') to OpenAI-compatible names ('assistant').
    If a summary is provided, it is prepended to the system prompt.
    If system_prompt is provided, it overrides the default from settings.
    """
    system = system_prompt or settings.system_prompt
    if summary:
        system = f"{system}\n\nConversation summary so far:\n{summary}"

    cerebras_messages = [
        {"role": _ROLE_MAP.get(m["role"], m["role"]), "content": m["content"]}
        for m in messages
    ]

    response = _call_with_retry(
        _client.chat.completions.create,
        model=settings.cerebras_model,
        messages=[{"role": "system", "content": system}] + cerebras_messages,
    )
    return response.choices[0].message.content


def summarize(messages: list[dict]) -> str:
    """Ask Cerebras to summarize a conversation."""
    text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in messages
    )
    response = _call_with_retry(
        _client.chat.completions.create,
        model=settings.cerebras_model,
        messages=[
            {"role": "system", "content": _SUMMARIZE_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    return response.choices[0].message.content
