#!/bin/bash
# Local deployment validation test
# Run before pushing to catch issues that would fail in CI/CD
# Usage: ./scripts/test-deploy.sh
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

pass() { echo -e "  ${GREEN}PASS${NC} $1"; PASS=$((PASS + 1)); }
fail() { echo -e "  ${RED}FAIL${NC} $1"; FAIL=$((FAIL + 1)); }
warn() { echo -e "  ${YELLOW}WARN${NC} $1"; WARN=$((WARN + 1)); }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

echo "================================================"
echo "  Zerve App - Pre-Deploy Validation"
echo "================================================"
echo ""

# ---- 1. Required Files ----
echo "1. Required Files"

for f in handler.py run_web_service.py requirements.txt; do
    if [ -f "$BACKEND_DIR/$f" ]; then
        pass "$f exists"
    else
        fail "$f is MISSING"
    fi
done

echo ""

# ---- 2. Dead Import Check ----
echo "2. Dead Import Check (removed functions & SQLAlchemy)"

cd "$BACKEND_DIR"

DEAD_IMPORTS="hash_password|verify_password|create_access_token|create_refresh_token"
FOUND=$(grep -rn --include="*.py" -E "import.+($DEAD_IMPORTS)|from.+import.+($DEAD_IMPORTS)" . \
    --exclude-dir=__pycache__ --exclude-dir=.git --exclude-dir=package --exclude-dir=tests 2>/dev/null || true)

if [ -z "$FOUND" ]; then
    pass "No old auth function imports (hash_password, create_access_token, etc.)"
else
    fail "Dead auth imports found:"
    echo "$FOUND" | while IFS= read -r line; do echo "        $line"; done
fi

SQLALCHEMY_IMPORTS=$(grep -rn --include="*.py" -E "from database.models|from database.db import SessionLocal|import sqlalchemy" . \
    --exclude-dir=__pycache__ --exclude-dir=.git --exclude-dir=package --exclude-dir=tests 2>/dev/null || true)

if [ -z "$SQLALCHEMY_IMPORTS" ]; then
    pass "No SQLAlchemy/old model imports"
else
    fail "SQLAlchemy imports found:"
    echo "$SQLALCHEMY_IMPORTS" | while IFS= read -r line; do echo "        $line"; done
fi

echo ""

# ---- 3. Dependency Check ----
echo "3. Dependency Check"

if grep -qE "^boto3|^botocore" requirements.txt 2>/dev/null; then
    fail "boto3/botocore in requirements.txt (Lambda provides these)"
else
    pass "boto3/botocore excluded (Lambda runtime provides them)"
fi

if grep -qE "^pytest|^black|^flake8" requirements.txt 2>/dev/null; then
    fail "Dev dependencies in requirements.txt (move to requirements-dev.txt)"
else
    pass "No dev dependencies in requirements.txt"
fi

REMOVED_PKGS=0
for pkg in "google-cloud-storage" "stripe" "bcrypt" "mangum"; do
    if grep -qi "^$pkg" requirements.txt 2>/dev/null; then
        fail "Removed package '$pkg' still in requirements.txt"
        REMOVED_PKGS=1
    fi
done
[ "$REMOVED_PKGS" -eq 0 ] && pass "No removed packages in requirements.txt"

echo ""

# ---- 4. Backend Import + Health Check ----
echo "4. Backend Import + Health Check"
echo "   Testing Flask app creation and /api/health..."

cd "$BACKEND_DIR"

HEALTH_RESULT=$(python3 << 'PYEOF' 2>&1
import sys, os
# Set minimal env vars so app can start without real AWS
os.environ["COGNITO_USER_POOL_ID"] = os.environ.get("COGNITO_USER_POOL_ID", "test-pool")
os.environ["COGNITO_CLIENT_ID"] = os.environ.get("COGNITO_CLIENT_ID", "test-client")
os.environ["DYNAMODB_TABLE_PREFIX"] = os.environ.get("DYNAMODB_TABLE_PREFIX", "test")
os.environ["AWS_REGION_NAME"] = os.environ.get("AWS_REGION_NAME", "us-east-1")
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
sys.path.insert(0, ".")
try:
    from run_web_service import create_app
    app = create_app()
    # Test health endpoint
    client = app.test_client()
    resp = client.get("/api/health")
    if resp.status_code == 200:
        print(f"HEALTH_OK:{resp.status_code}")
    else:
        print(f"HEALTH_FAIL:{resp.status_code}:{resp.get_data(as_text=True)}")
    # Test handler import
    from handler import handler as h
    if callable(h):
        print("HANDLER_OK")
    else:
        print("HANDLER_FAIL:not callable")
except Exception as e:
    print(f"IMPORT_ERROR:{e}")
PYEOF
)

if echo "$HEALTH_RESULT" | grep -q "HEALTH_OK"; then
    pass "/api/health returns 200"
else
    fail "/api/health failed: $(echo "$HEALTH_RESULT" | grep -E 'HEALTH_FAIL|IMPORT_ERROR')"
fi

if echo "$HEALTH_RESULT" | grep -q "HANDLER_OK"; then
    pass "handler.handler is callable (Lambda entry point)"
else
    fail "handler.handler failed: $(echo "$HEALTH_RESULT" | grep -E 'HANDLER_FAIL|IMPORT_ERROR')"
fi

echo ""

# ---- 5. Frontend TypeScript Check ----
echo "5. Frontend TypeScript Check"

if [ -d "$FRONTEND_DIR" ] && [ -f "$FRONTEND_DIR/tsconfig.json" ]; then
    cd "$FRONTEND_DIR"
    if npx tsc --noEmit 2>/dev/null; then
        pass "TypeScript compilation passes"
    else
        fail "TypeScript compilation errors"
    fi
else
    warn "Frontend not found, skipping TypeScript check"
fi

echo ""

# ---- 6. CI Config Check ----
echo "6. CI Config Check"

CI_FILE="$ROOT_DIR/.github/workflows/ci.yml"
if [ -f "$CI_FILE" ]; then
    if grep -q "passWithNoTests" "$CI_FILE"; then
        pass "Jest --passWithNoTests flag present"
    else
        warn "Missing --passWithNoTests in CI (will fail if no tests)"
    fi

    if grep -q "apig.wsgi\|apig_wsgi\|handler.handler" "$CI_FILE" || grep -q "handler.py" "$CI_FILE"; then
        pass "CI packages handler.py"
    else
        warn "handler.py may not be included in Lambda package"
    fi
else
    warn "CI config not found"
fi

echo ""

# ---- Summary ----
echo "================================================"
echo -e "  Results: ${GREEN}${PASS} passed${NC}, ${RED}${FAIL} failed${NC}, ${YELLOW}${WARN} warnings${NC}"
echo "================================================"

if [ "$FAIL" -gt 0 ]; then
    echo -e "${RED}FIX ISSUES ABOVE BEFORE PUSHING${NC}"
    exit 1
else
    echo -e "${GREEN}All checks passed - safe to deploy${NC}"
    exit 0
fi
