"""Locale detection and locale-aware static strings for the LLM service.

Uses the same Unicode-block frequency heuristics as worker/locale.go in the
Go service — no external dependencies, no extra LLM calls.
"""

# Fallback replies used when the model fails to produce any content after all
# retries. Intentionally casual and human — a cold "try again later" feels like
# a broken bot; these sound like a person who is momentarily unavailable.
FALLBACK_REPLIES: dict[str, str] = {
    "en": (
        "Sorry, I can't respond right now — will definitely get back to you a bit later. "
        "If I don't, please feel free to remind me!"
    ),
    "ru": (
        "Извините, сейчас не могу ответить — обязательно вернусь к вам чуть позже. "
        "Если не напишу, пожалуйста, напомните!"
    ),
    "uk": (
        "Вибачте, зараз немає можливості відповісти — обов'язково повернуся до вас трохи пізніше. "
        "Якщо не напишу, будь ласка, нагадайте!"
    ),
    "ar": (
        "أعتذر، لا أستطيع الرد الآن — سأعود إليكم قريباً. "
        "إذا لم أرد، فضلاً ذكّروني!"
    ),
    "zh": (
        "抱歉，暂时无法回复 — 稍后一定会回复您的。"
        "如果没有收到回复，请提醒我一下！"
    ),
}


def detect_lang(text: str) -> str:
    """Return a language tag based on the dominant Unicode script in *text*.

    Recognised tags: 'ru', 'uk', 'ar', 'zh'.  Everything else returns 'en'.
    Mirrors the logic in worker/locale.go so both services behave identically.
    """
    total = cyrillic = uk_specific = arabic = cjk = 0
    for ch in text:
        if ch in " \t\n\r":
            continue
        total += 1
        cp = ord(ch)
        if 0x0400 <= cp <= 0x04FF:
            cyrillic += 1
            if ch in "їЇєЄіІґҐ":
                uk_specific += 1
        elif (
            0x0600 <= cp <= 0x06FF
            or 0x0750 <= cp <= 0x077F
            or 0xFB50 <= cp <= 0xFDFF
            or 0xFE70 <= cp <= 0xFEFF
        ):
            arabic += 1
        elif (
            0x4E00 <= cp <= 0x9FFF
            or 0x3400 <= cp <= 0x4DBF
            or 0xF900 <= cp <= 0xFAFF
        ):
            cjk += 1

    if total == 0:
        return "en"
    if cyrillic * 100 // total > 8:
        return "uk" if uk_specific else "ru"
    if arabic * 100 // total > 8:
        return "ar"
    if cjk * 100 // total > 8:
        return "zh"
    return "en"


def fallback_reply(system_prompt: str) -> str:
    """Return the locale-appropriate fallback reply for the given system prompt.

    detect_lang always returns a key that is present in FALLBACK_REPLIES,
    so direct indexing is safe here.
    """
    return FALLBACK_REPLIES[detect_lang(system_prompt)]
