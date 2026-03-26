# LLM Service

Stateless FastAPI service — receives conversation history from the Go backend, returns an AI reply via Cerebras.

## Structure

```
python/
├── src/
│   ├── main.py      # FastAPI app: POST /reply, POST /summarize, GET /health
│   ├── llm.py       # Cerebras client: get_reply(), summarize()
│   ├── schemas.py   # Pydantic request/response models
│   └── config.py    # Settings via pydantic-settings (.env)
├── docs/
│   ├── architecture.md
│   └── plan.md
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── .env             # local only, not committed
└── .env.example
```

## Quick start

```bash
cp .env.example .env
# Fill in LLM_API_KEY

uv sync
uvicorn main:app --app-dir src --port 8000 --reload
```

## Environment variables

| Variable | Description |
|---|---|
| `LLM_API_KEY` | Cerebras API key (required) |
| `CEREBRAS_MODEL` | Model name, e.g. `llama3.1-8b` |
| `SYSTEM_PROMPT` | Fallback system prompt if Go does not send one |

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/reply` | Send conversation history, get AI reply |
| `POST` | `/summarize` | Summarize conversation history |
| `GET` | `/health` | Health check |

### POST /reply

```json
{
  "phone": "account-uuid:user-id",
  "messages": [{"role": "user", "content": "Hello"}],
  "summary": "",
  "system_prompt": "You are a helpful assistant."
}
```

Response: `{"reply": "Hi! How can I help?"}`

Requests taking ≥ 10 seconds are logged at WARNING level with duration.
