# LLM Service — Plan & Backlog

## Done

- [x] `POST /reply` — conversation history → Cerebras → AI reply
- [x] `POST /summarize` — conversation history → Cerebras → compact summary
- [x] `GET /health` — health check
- [x] Per-request `system_prompt` override (passed by Go)
- [x] Summary injected into system prompt when present
- [x] Slow-request logging: WARNING when Cerebras takes ≥ 10s, duration on every response

## Backlog

- [ ] **Cerebras retry** — when Cerebras returns 503 (`queue_exceeded`) or any 5xx, retry
  up to 3 times with exponential backoff (2s → 4s → 8s) before raising an error.
  Implement in `src/llm.py` around `_client.chat.completions.create(...)`.
  No changes needed in Go — transient overload becomes a delayed reply instead of an error.
