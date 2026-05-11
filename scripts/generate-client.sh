#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

# Skip gracefully when the backend isn't running (e.g. in pre-commit without a live server).
if ! curl -sf "$BACKEND_URL/openapi.json" -o /dev/null 2>&1; then
    echo "Backend not reachable at $BACKEND_URL — skipping client generation."
    echo "Start the backend and re-run: bash ./scripts/generate-client.sh"
    exit 0
fi

echo "Generating frontend API client from $BACKEND_URL/openapi.json ..."

npx --prefix "$ROOT/frontend" @hey-api/openapi-ts \
    --input "$BACKEND_URL/openapi.json" \
    --output "$ROOT/frontend/src/client" \
    --client @hey-api/client-axios

echo "Done. Client written to frontend/src/client/"
