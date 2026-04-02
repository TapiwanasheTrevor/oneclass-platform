#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
VITEST_BIN="$FRONTEND_DIR/node_modules/.bin/vitest"

if [ ! -x "$VITEST_BIN" ]; then
  cat >&2 <<'EOF'
Frontend behavioral tests are not provisioned in this workspace.
Install the frontend test toolchain, including vitest, before using test commands.
Expansion readiness is currently enforced by `npm run verify:readiness`.
EOF
  exit 1
fi

cd "$FRONTEND_DIR"
"$VITEST_BIN" "$@"
