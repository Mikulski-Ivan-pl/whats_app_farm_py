import json
import logging
import time

from cerebras.cloud.sdk import APIConnectionError, APIStatusError, Cerebras
from cerebras.cloud.sdk import NOT_GIVEN

from config import settings
from locale import fallback_reply as _fallback_reply

logger = logging.getLogger(__name__)

_client = Cerebras(api_key=settings.llm_api_key)

_ROLE_MAP = {"bot": "assistant", "user": "user"}

_RETRY_DELAYS = (2, 4, 8)
_EMPTY_CONTENT_RETRIES = 2

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


def get_reply(
    messages: list[dict],
    summary: str = "",
    system_prompt: str = "",
    model: str = "",
    tools: list[dict] | None = None,
    previous_tool_calls: list[dict] | None = None,
    tool_results: list[dict] | None = None,
) -> tuple[str, list[dict]]:
    """Send conversation history to Cerebras and return (reply, tool_calls).

    Maps Go role names ('bot') to OpenAI-compatible names ('assistant').
    If tools is non-empty, enables function calling; may return tool_calls instead of reply.
    If previous_tool_calls + tool_results are provided, appends them to the conversation
    so the LLM can continue the agentic loop after executing tools.
    """
    system = system_prompt
    if summary:
        system = f"{system}\n\nConversation summary so far:\n{summary}"

    cerebras_messages = [
        {"role": _ROLE_MAP.get(m["role"], m["role"]), "content": m["content"]}
        for m in messages
    ]

    # Reconstruct agentic history: assistant tool_call message + tool result messages.
    if previous_tool_calls and tool_results:
        cerebras_messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc.get("args", {})),
                    },
                }
                for tc in previous_tool_calls
            ],
        })
        for tr in tool_results:
            cerebras_messages.append({
                "role": "tool",
                "tool_call_id": tr["tool_call_id"],
                "content": tr["content"],
            })

    cerebras_tools = NOT_GIVEN
    if tools:
        cerebras_tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("parameters", {"type": "object", "properties": {}}),
                },
            }
            for t in tools
        ]

    for attempt in range(1 + _EMPTY_CONTENT_RETRIES):
        response = _call_with_retry(
            _client.chat.completions.create,
            model=model or settings.cerebras_model,
            messages=[{"role": "system", "content": system}] + cerebras_messages,
            tools=cerebras_tools,
        )

        choice = response.choices[0]
        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            result_tool_calls = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "args": json.loads(tc.function.arguments or "{}"),
                }
                for tc in choice.message.tool_calls
            ]
            return "", result_tool_calls

        text = choice.message.content or ""
        if text:
            return text, []
        logger.warning(
            "cerebras returned empty content attempt=%d/%d",
            attempt + 1,
            1 + _EMPTY_CONTENT_RETRIES,
        )
    logger.error("cerebras returned empty content on all attempts, using fallback")
    return _fallback_reply(system_prompt), []


def summarize(messages: list[dict], model: str = "") -> str:
    """Ask Cerebras to summarize a conversation.

    If model is provided, it overrides the default from settings.
    """
    text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in messages
    )
    response = _call_with_retry(
        _client.chat.completions.create,
        model=model or settings.cerebras_model,
        messages=[
            {"role": "system", "content": _SUMMARIZE_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    return response.choices[0].message.content or ""
