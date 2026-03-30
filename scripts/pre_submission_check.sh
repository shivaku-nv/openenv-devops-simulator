#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:7860}"

require_file() {
  local path="$1"
  [[ -f "$path" ]] || { echo "[FAIL] missing file: $path"; exit 1; }
  echo "[PASS] file present: $path"
}

check_status() {
  local path="$1"
  local expected="${2:-200}"
  local code
  code="$(curl -o /dev/null -s -w "%{http_code}" "$BASE_URL$path")"
  [[ "$code" == "$expected" ]] || { echo "[FAIL] $path returned $code (expected $expected)"; exit 1; }
  echo "[PASS] $path returned $expected"
}

echo "Running pre-submission checks against: $BASE_URL"

require_file "openenv.yaml"
require_file "Dockerfile"
require_file "inference.py"

check_status "/"
check_status "/web" 200
check_status "/log-ui" 200

tasks="$(curl -sS "$BASE_URL/tasks")"
[[ "$tasks" == *"easy"* && "$tasks" == *"medium"* && "$tasks" == *"hard"* ]] || {
  echo "[FAIL] /tasks does not list easy, medium, hard"
  exit 1
}
echo "[PASS] /tasks lists easy, medium, hard"

reset_body="$(curl -sS -X POST "$BASE_URL/reset?task_name=easy")"
[[ "$reset_body" == *"logs"* ]] || { echo "[FAIL] /reset did not return logs"; exit 1; }
echo "[PASS] /reset returned an observation"

baseline="$(curl -sS "$BASE_URL/baseline")"
[[ "$baseline" == *"\"score\":1.0"* ]] || { echo "[FAIL] /baseline did not score 1.0"; exit 1; }
echo "[PASS] /baseline returned score 1.0"

echo "Pre-submission checks passed."
