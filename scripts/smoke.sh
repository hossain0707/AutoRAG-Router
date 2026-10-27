#!/usr/bin/env bash
set -euo pipefail
BASE="${AUTORAG_URL:-http://127.0.0.1:8000}"
HEADER=()
if [[ -n "${AUTORAG_API_KEY:-}" ]]; then HEADER=(-H "x-api-key: ${AUTORAG_API_KEY}"); fi
curl --fail --silent "${BASE}/healthz"
printf '\n'
curl --fail --silent -X POST "${BASE}/v1/documents" "${HEADER[@]}" -H 'Content-Type: application/json' -d '{"documents":[{"id":"smoke","tenant_id":"smoke","title":"Demo","text":"Atlas sends records to Beacon for indexing.","entities":["Atlas","Beacon"]}]}'
printf '\n'
curl --fail --silent -X POST "${BASE}/v1/query" "${HEADER[@]}" -H 'Content-Type: application/json' -d '{"query":"How are Atlas and Beacon connected?","tenant_id":"smoke"}'
printf '\n'
