#!/bin/sh
set -e

echo "Starting FastAPI server..."
exec uvicorn main:app \
    --host "${LLM_HOST:-0.0.0.0}" \
    --port "${LLM_PORT:-8000}" \
