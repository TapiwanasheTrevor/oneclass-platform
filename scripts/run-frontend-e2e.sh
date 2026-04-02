#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
PLAYWRIGHT_BIN="$FRONTEND_DIR/node_modules/.bin/playwright"

if [ ! -x "$PLAYWRIGHT_BIN" ]; then
  cat >&2 <<'EOF'
Frontend E2E tests are not provisioned in this workspace.
Install the frontend E2E toolchain, including Playwright, before using E2E commands.
Expansion readiness is currently enforced by `npm run verify:readiness`.
EOF
  exit 1
fi

cd "$FRONTEND_DIR"
"$PLAYWRIGHT_BIN" test "$@"
