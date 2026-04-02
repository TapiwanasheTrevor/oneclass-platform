#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/5] Backend compile verification"
(
  cd backend
  python3 -m compileall -q main.py api services shared
)

echo "[2/5] Backend import smoke verification"
backend/venv/bin/python - <<'PY'
import importlib
import sys

sys.path.insert(0, "backend")

modules = [
    "main",
    "services.domain_management.routes",
    "services.mobile_auth.routes",
    "services.mobile_auth.service",
    "services.sso_integration.routes",
    "services.sso_integration.service",
]

for name in modules:
    importlib.import_module(name)
    print(f"OK {name}")
PY

echo "[3/5] Backend route contract verification"
backend/venv/bin/python - <<'PY'
import sys

sys.path.insert(0, "backend")

from main import app

required_route_contracts = {
    ("GET", "/api/v1/auth/me"),
    ("POST", "/api/v1/auth/refresh"),
    ("POST", "/api/v1/auth/switch-school"),
    ("GET", "/api/v1/auth/me/schools"),
    ("GET", "/api/v1/platform/schools/by-subdomain/{subdomain}"),
    ("GET", "/api/v1/platform/schools/by-id/{school_id}"),
    ("GET", "/api/v1/platform/schools/{school_id}/context"),
    ("GET", "/api/v1/sis/health"),
    ("GET", "/api/v1/academic/health"),
    ("GET", "/api/v1/finance/health"),
    ("GET", "/api/v1/migration-services/health"),
}

registered_route_contracts = set()
for route in app.routes:
    path = getattr(route, "path", None)
    methods = getattr(route, "methods", None)
    if not path or not methods:
        continue

    for method in methods:
        if method in {"HEAD", "OPTIONS"}:
            continue
        registered_route_contracts.add((method, path))

missing_route_contracts = sorted(required_route_contracts - registered_route_contracts)
if missing_route_contracts:
    details = "\n".join(
        f"- {method} {path}" for method, path in missing_route_contracts
    )
    raise SystemExit(f"Missing required route contracts:\n{details}")

print(f"Verified {len(required_route_contracts)} required backend route contracts")
PY

echo "[4/5] Frontend type-check verification"
(
  cd frontend
  npm run type-check
)

echo "[5/5] Full build verification"
npm run build

cat <<'EOF'

Expansion readiness verification passed.

Default guarded module:
- migration services routes are disabled unless `ONECLASS_ENABLE_EXPERIMENTAL_MIGRATION_SERVICES=true`
EOF
