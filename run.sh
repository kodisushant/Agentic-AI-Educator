#!/usr/bin/env bash
set -e

echo "=========================================="
echo "Starting AI Virtual Teacher (MOCK_MODE=true)"
echo "=========================================="

export MOCK_MODE=true
export BACKEND_PORT=${BACKEND_PORT:-8000}

echo "Backend starting on http://localhost:${BACKEND_PORT}"
echo "API Docs available at http://localhost:${BACKEND_PORT}/docs"
echo "Contracts stored in /contracts"

python -m uvicorn backend.agent.main:app --host 0.0.0.0 --port "${BACKEND_PORT}" --reload
