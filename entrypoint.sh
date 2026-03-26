#!/bin/sh
set -e

echo "Starting FastAPI server..."
exec uvicorn main:app \
    --host "${HOST:-0.0.0.0}" \
    --port "${PORT:-8000}" \
