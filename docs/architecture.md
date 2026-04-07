# LLM Service — Architecture

## Overview

Stateless FastAPI service. Receives conversation history from the Go backend via HTTP, calls Cerebras, returns the reply. No database, no session state — all context is passed in the request body.

## Request flow

```
Go worker → POST /reply → get_reply() → Cerebras API → reply text → Go worker
```

For summarization (triggered by Go every 20 messages):
```
Go worker → POST /summarize → summarize() → Cerebras API → summary text → Go worker
```

## Key design decisions

| Decision | Choice | Reason |
|---|---|---|
| Stateless | No DB, no cache | Go owns all session state; Python is a pure function |
| system_prompt | Passed per-request by Go | Enables per-account prompts without Python changes |
| model | Passed per-request by Go (`model` field, optional) | Enables per-account model selection; falls back to `CEREBRAS_MODEL` env var when empty |
| Role mapping | `bot` → `assistant` | Go uses `bot`; Cerebras expects OpenAI-compatible `assistant` |
| Slow logging | WARNING when ≥ 10s | Makes slow Cerebras responses visible at a glance |
| Empty-content retry | Up to 3 attempts in `get_reply()` | Cerebras occasionally returns HTTP 200 with `content=None` (model quirk / token limit); retrying usually produces a valid reply |
| Fallback reply | `FALLBACK_REPLY` env var | If all retry attempts return empty, the user gets a polite message instead of silence |

## Files

- **`main.py`** — FastAPI app, route handlers, timing/logging
- **`llm.py`** — Cerebras SDK calls: `get_reply()`, `summarize()`
- **`schemas.py`** — Pydantic models for request/response validation
- **`config.py`** — `pydantic-settings` loading from `.env`

## Cerebras response times

With a large system prompt + knowledge base, Cerebras can take 30–60 seconds. The Go service timeout is set to 120s (`LLM_TIMEOUT_SEC`). Requests ≥ 10s are logged as WARNING.
