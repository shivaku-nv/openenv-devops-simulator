#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:7860}"

pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; exit 1; }

request() {
  local method="$1"
  local path="$2"
  local data="${3:-}"
  if [[ -n "$data" ]]; then
    curl -sS -X "$method" "$BASE_URL$path" -H "Content-Type: application/json" -d "$data"
  else
    curl -sS -X "$method" "$BASE_URL$path"
  fi
}

check_contains() {
  local body="$1"
  local needle="$2"
  local label="$3"
  [[ "$body" == *"$needle"* ]] && pass "$label" || fail "$label (missing: $needle)"
}

echo "Running smoke tests against: $BASE_URL"

tasks="$(request GET /tasks)" || fail "GET /tasks reachable"
check_contains "$tasks" "easy" "GET /tasks has easy"
check_contains "$tasks" "medium" "GET /tasks has medium"
check_contains "$tasks" "hard" "GET /tasks has hard"

state="$(request GET /state)" || fail "GET /state reachable"
check_contains "$state" "history" "GET /state returns history"

run_task_flow() {
  local task_name="$1"
  local fix="$2"

  reset_body="$(request POST "/reset?task_name=$task_name")" || fail "POST /reset ($task_name)"
  check_contains "$reset_body" "logs" "reset returns logs ($task_name)"

  step1="$(request POST /step '{"action_type":"analyze_logs"}')" || fail "POST /step analyze_logs ($task_name)"
  check_contains "$step1" "reward" "analyze_logs returns reward ($task_name)"

  step2="$(request POST /step "{\"action_type\":\"take_action\",\"payload\":{\"fix\":\"$fix\"}}")" || fail "POST /step take_action ($task_name)"
  check_contains "$step2" "\"done\":true" "take_action marks done=true ($task_name)"

  grade_body="$(request POST /grader)" || fail "POST /grader ($task_name)"
  check_contains "$grade_body" "\"score\":1.0" "grader score is 1.0 ($task_name)"
}

run_task_flow "easy" "clear_disk"
run_task_flow "medium" "restart_service"
run_task_flow "hard" "scale_up"

baseline="$(request GET /baseline)" || fail "GET /baseline reachable"
check_contains "$baseline" "\"score\":1.0" "baseline returns score 1.0"
check_contains "$baseline" "\"done\":true" "baseline returns done=true"

echo "All smoke tests passed."
