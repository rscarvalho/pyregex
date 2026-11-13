#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Explicit project on every command: never stop the default development stack.
project="${SMOKE_PROJECT:-pyregex-ci-smoke}"
if [[ ! "$project" =~ ^pyregex-ci-smoke(-[a-z0-9]+)*$ ]]; then
  echo 'SMOKE_PROJECT must be pyregex-ci-smoke or pyregex-ci-smoke-<lowercase-alphanumeric-suffix>.' >&2
  exit 2
fi
compose=(docker compose -p "$project" -f compose.local.yaml -f compose.smoke.yaml)
cleanup() {
  status=$?
  if (( status != 0 )); then "${compose[@]}" logs --no-color || true; fi
  "${compose[@]}" down --remove-orphans || true
  exit "$status"
}
trap cleanup EXIT
"${compose[@]}" build backend frontend
"${compose[@]}" up -d backend frontend
"${compose[@]}" exec -T backend timeout -k 5s 60s nosetests -c nose.cfg
# Wait for the HTTP listener, rather than assuming container creation is readiness.
"${compose[@]}" exec -T backend timeout -k 2s 30s python -c '
import socket, time
for attempt in range(50):
    try:
        with socket.create_connection(("127.0.0.1", 5000), timeout=1):
            break
    except OSError:
        time.sleep(0.2)
else:
    raise SystemExit("backend did not become ready")
'
"${compose[@]}" exec -T backend timeout -k 2s 30s python local/smoke.py
"${compose[@]}" exec -T frontend timeout -k 2s 30s node local/frontend-test.js
backend="$("${compose[@]}" ps -q backend)"
# Same loopback namespace as both services; no host ports or app URL rewrites.
# Keep image and ci/browser/package.json versions in sync.
docker run --rm --init --network "container:$backend" --ipc=host \
  -v "$PWD/ci/browser:/tests" -w /tests \
  mcr.microsoft.com/playwright:v1.64.1-noble@sha256:2f05f8a734509a7b3f26a912639488ee08f58a7b292d14d62271bcff9038768f npm test
