# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Local Development
```bash
cp .env.example .env   # then fill in LLM_API_KEY, CEREBRAS_MODEL, SYSTEM_PROMPT
uv sync
uvicorn main:app --app-dir src --port 8000 --reload
```

### Docker (Development)
```bash
docker compose -f docker-compose.dev.yml up -d --build
docker compose -f docker-compose.dev.yml logs -f
docker compose -f docker-compose.dev.yml down
```

## Architecture

Stateless FastAPI microservice acting as an LLM proxy:

```
Go Backend → HTTP POST → FastAPI (Python) → Cerebras API → Response
```

**Endpoints:**
- `POST /reply` — Takes conversation history + optional system_prompt, returns AI reply
- `POST /summarize` — Summarizes conversation history (called by Go every 20 messages)
- `GET /health` — Returns `{"status": "ok"}`

**Module layout (`src/`):**
- `main.py` — Route handlers; logs requests ≥10s as WARNING
- `llm.py` — Cerebras SDK client singleton; maps Go's "bot" role → OpenAI "assistant"
- `schemas.py` — Pydantic request/response models
- `config.py` — Pydantic Settings loaded from `.env`

**Key design choices:**
- All conversation context is passed per-request (no server-side session state)
- `system_prompt` is per-request, enabling per-WhatsApp-account customization
- Shares a Docker network (`whats_app_farm_network`) with the Go backend

## Environment Variables
| Variable | Required | Description |
|---|---|---|
| `LLM_API_KEY` | Yes | Cerebras API key |
| `CEREBRAS_MODEL` | Yes | Model name (e.g. `llama3.1-8b`) |
| `SYSTEM_PROMPT` | Yes | Fallback system prompt |
| `LLM_HOST` | No (default: 0.0.0.0) | Bind address |
| `LLM_PORT` | No (default: 8000) | Server port |

## Deployment
CI/CD via `.github/workflows/main.yml`: pushes to `main` trigger rsync to the server followed by `docker compose -f docker-compose.dev.yml up -d --build`.

Required GitHub secrets: `HOST`, `PORT`, `USERNAME`, `KEY`, `PASSPHRASE`, `REMOTE_PATH`, `LLM_API_KEY`, `CEREBRAS_MODEL`, `SYSTEM_PROMPT`, `LLM_HOST`, `LLM_PORT`.
