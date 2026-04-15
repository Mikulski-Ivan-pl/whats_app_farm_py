# LLM Service — Plan & Backlog

## Done

- [x] `POST /reply` — conversation history → Cerebras → AI reply
- [x] `POST /summarize` — conversation history → Cerebras → compact summary
- [x] `GET /health` — health check
- [x] Per-request `system_prompt` override (passed by Go)
- [x] Summary injected into system prompt when present
- [x] Slow-request logging: WARNING when Cerebras takes ≥ 10s, duration on every response
- [x] Per-request `model` override — both `/reply` and `/summarize` accept optional `model` field; falls back to `CEREBRAS_MODEL` env var when empty or absent
- [x] Model logged on every request (`model=llama-4-scout-17b-16e-instruct` or `model=auto`)

- [x] **Cerebras retry on 5xx** — `_call_with_retry` wraps all Cerebras calls; retries on 5xx and `APIConnectionError` with 2s → 4s → 8s backoff.
- [x] **Empty-content retry + fallback** — `get_reply()` retries up to 3 times when Cerebras returns HTTP 200 but `content=None`; on exhaustion returns `FALLBACK_REPLY` so the user always gets a message. `summarize()` guards against `None` with `or ""`.

- [x] **MCP function calling** ✓ — `POST /reply` now supports tool calling:
  - Request: `tools` (list of tool definitions from MCP server), `previous_tool_calls` (from previous agentic iteration), `tool_results` (results of executed tool calls)
  - Response: either `reply` (final text) or `tool_calls` (list of tools LLM wants to invoke)
  - `get_reply()` passes tool definitions to Cerebras via OpenAI-compatible function calling API
  - If `previous_tool_calls` + `tool_results` present: reconstructs proper assistant tool_call message + tool result messages in conversation history
  - Go worker handles the actual agentic loop and MCP server HTTP calls; this service is purely the LLM bridge
  - Empty-content retry loop wraps the full Cerebras call; tool_calls responses are never retried (they're valid)

## Backlog

- [ ] **E2E test with MCP stub** — send a request with dummy tools, verify tool_calls returned; send follow-up with tool_results, verify final reply.
