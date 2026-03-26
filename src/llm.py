from cerebras.cloud.sdk import Cerebras

from config import settings

_client = Cerebras(api_key=settings.llm_api_key)

_ROLE_MAP = {"bot": "assistant", "user": "user"}

_SUMMARIZE_PROMPT = (
    "Summarize the following conversation briefly and clearly. "
    "Focus on key topics, decisions, and context that would help continue the conversation. "
    "Reply with the summary only, no preamble."
)


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

    response = _client.chat.completions.create(
        model=settings.cerebras_model,
        messages=[{"role": "system", "content": system}] + cerebras_messages,
    )
    return response.choices[0].message.content


def summarize(messages: list[dict]) -> str:
    """Ask Cerebras to summarize a conversation."""
    text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in messages
    )
    response = _client.chat.completions.create(
        model=settings.cerebras_model,
        messages=[
            {"role": "system", "content": _SUMMARIZE_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    return response.choices[0].message.content
