---
title: OpenEnv DevOps Incident Simulator
sdk: docker
app_port: 7860
---

# OpenEnv DevOps Incident Simulator

This project helps you test DevOps incident handling from real-looking logs.
You can paste or upload logs (dmesg/syslog/core dump style), get a predicted issue, apply a mapped fix, and see a score.
It now also includes a Phase 2 `incident_command` scenario for richer multi-step response, communication, and postmortem evaluation.

## Deployment On Hugging Face
This app is intended to run as a Hugging Face Docker Space.

- Deployment is triggered manually from the GitHub Actions workflow file [`.github/workflows/deploy-openenv.yml`].
- The Space should use port `7860`.
- The app UI is available at `/`, `/web`, and `/log-ui`.
- If Hugging Face probes `/web`, it should still load the same log UI.

## Submission Runtime
- The root inference entrypoint is `inference.py`.
- LLM configuration is read from `API_BASE_URL`, `MODEL_NAME`, and `HF_TOKEN`.
- LLM calls use the OpenAI Python client and fall back to a deterministic heuristic if the remote endpoint is unavailable.

## What The App Does
Core behavior:
1. Ingests logs (raw text or uploaded log file).
2. Predicts incident label (`disk_full`, `memory_leak`, `crash`, `network_issue`).
3. Maps predicted label to an internal remediation action.
4. Runs environment episode (`analyze_logs -> take_action`).
5. Returns `reward`, `done`, and grader `score`.

Goal: make log triage easy to test and demo.

Phase 2 behavior:
1. Runs a richer `incident_command` environment task.
2. Supports delegation, stakeholder communication, and postmortem actions.
3. Grades episodes with a configurable reward engine and score breakdown.

## Main Capabilities
- Raw log ingestion via JSON (`/ingest_log`)
- File upload ingestion via multipart (`/ingest_log_file`)
- Browser UI for paste/upload (`/log-ui`)
- Configurable reward scoring with component breakdown (`/grader`)
- Classic OpenEnv endpoints (`/reset`, `/step`, `/state`, `/tasks`, `/baseline`)
- Phase 2 multi-step task: `incident_command`
- Docker-ready deployment

## Dir Highlights
- `api/server.py` - API routes and ingestion logic
- `env/` - simulator environment and reward mechanics
- `tasks/` - easy/medium/hard plus `incident_command`
- `graders/` - episode grading
- `models/` - log classifier
- `data/live_logs/` - sample realistic log files
- `scripts/smoke_test.sh` - endpoint smoke tests
- `evaluation/run_incident_command_eval.py` - Phase 2 scenario evaluator

## install Docker
```bash
sudo apt update
sudo apt install ca-certificates curl gnupg lsb-release -y

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io -y
```
## Build and Run (Docker)
```bash
apt install python3.12-venv
python3 -m venv venv
source venv/bin/activate
docker build -t openenv-devops .
docker run -p 7860:7860 openenv-devops
```

Base URL:
`http://localhost:7860`

## Log Analysis Workflows

### 1) Upload log file
```bash
curl -s -X POST http://localhost:7860/ingest_log_file \
  -F "file=@data/live_logs/dmesg.log" \
  -F "source=curl_upload"
```

### 2) Send pasted/raw log text
```bash
curl -s -X POST http://localhost:7860/ingest_log \
  -H "Content-Type: application/json" \
  -d '{"source":"manual_text","log":"Out of memory: Killed process 2145 (python3)"}'
```

### 3) Use browser UI
Open:
`http://localhost:7860/log-ui`

You can paste logs or upload `.log/.txt` and receive result JSON.

## Result JSON Meaning
Example response:
```json
{
  "source": "curl_upload",
  "predicted_label": "memory_leak",
  "mapped_task": "medium",
  "recommended_fix": "restart_service",
  "done": true,
  "last_reward": 1.05,
  "score": 1.0,
  "score_breakdown": {
    "recovery": 1.0,
    "root_cause": 1.0,
    "efficiency": 1.0,
    "safety": 1.0,
    "coordination": 1.0,
    "communication": 1.0,
    "learning": 1.0
  },
  "reward_profile": "medium"
}
```

Field meaning:
- `predicted_label`: detected incident type from log
- `mapped_task`: internal scenario selected by label
- `recommended_fix`: remediation action selected
- `done`: episode completion status
- `last_reward`: reward from final action step
- `score`: weighted episode score
- `score_breakdown`: per-dimension component scores used by the reward engine
- `reward_profile`: scoring profile applied to the task

## Label to Action Mapping
- `disk_full` -> `clear_disk`
- `memory_leak` -> `restart_service`
- `crash` -> `restart_service`
- `network_issue` -> `scale_up`

## Other API Endpoints
- `POST /reset`
- `POST /step`
- `GET /state`
- `GET /tasks`
- `POST /grader`
- `GET /baseline`

## Available Tasks
- `easy`
- `medium`
- `hard`
- `incident_command`

`incident_command` is the new Phase 2 scenario. It simulates a checkout outage with memory pressure, deployment context, stakeholder updates, and rewards for coordination work beyond simple remediation.

## Round 2 Positioning
This repo now targets the April 2026 Round 2 OpenEnv hackathon themes through one unified environment design:
- multi-agent interactions
- long-horizon planning and instruction following
- world modeling for professional workflows
- self-improving agent systems

The `incident_command` task is the main Phase 2 scenario used to demonstrate those themes.

## Training Pipeline
The repo now includes a full TRL-based training pipeline in `models/train.py`.

It supports:
- supervised fine-tuning on oracle action plans for all tasks
- GRPO fine-tuning using the local environment reward engine
- local evaluation that writes reward metrics to `outputs/phase2_training/eval_metrics.json`

Install the optional training stack:
```bash
source ~/venv/bin/activate
pip install -r requirements-training.txt
```

Run the full pipeline:
```bash
source ~/venv/bin/activate
python3 models/train.py \
  --stage all \
  --model-name-or-path Qwen/Qwen2.5-0.5B-Instruct \
  --output-dir outputs/phase2_training
```

Run only SFT:
```bash
python3 models/train.py --stage sft --output-dir outputs/phase2_training
```

Run only GRPO starting from an existing checkpoint:
```bash
python3 models/train.py \
  --stage grpo \
  --model-name-or-path outputs/phase2_training/sft \
  --output-dir outputs/phase2_training
```

Run evaluation:
```bash
python3 models/train.py \
  --stage eval \
  --model-name-or-path outputs/phase2_training/grpo \
  --output-dir outputs/phase2_training
```

Main outputs:
- `outputs/phase2_training/sft/`
- `outputs/phase2_training/grpo/`
- `outputs/phase2_training/sft_dataset.jsonl`
- `outputs/phase2_training/eval_metrics.json`

## Phase 2 Actions
The classic tasks still use:
- `analyze_logs`
- `take_action`

The new `incident_command` task also supports:
- `delegate_investigation`
- `communicate_status`
- `write_postmortem`

Example flow:
```bash
curl -s -X POST "http://localhost:7860/reset?task_name=incident_command"
curl -s -X POST http://localhost:7860/step -H "Content-Type: application/json" \
  -d '{"action_type":"delegate_investigation","payload":{"role":"sre_agent","objective":"Check memory pressure and recent deploy changes"}}'
curl -s -X POST http://localhost:7860/step -H "Content-Type: application/json" \
  -d '{"action_type":"communicate_status","payload":{"audience":"stakeholders","summary":"Investigating checkout degradation and elevated latency."}}'
curl -s -X POST http://localhost:7860/step -H "Content-Type: application/json" \
  -d '{"action_type":"analyze_logs"}'
curl -s -X POST http://localhost:7860/step -H "Content-Type: application/json" \
  -d '{"action_type":"take_action","payload":{"fix":"restart_service"}}'
curl -s -X POST http://localhost:7860/step -H "Content-Type: application/json" \
  -d '{"action_type":"write_postmortem","payload":{"summary":"checkout-api memory pressure after deployment caused failed checkouts.","action_items":["Add memory regression guard to rollout checks"]}}'
curl -s -X POST http://localhost:7860/grader
```

## Quick Validation
```bash
curl -s http://localhost:7860/tasks
./scripts/smoke_test.sh
```

## High-Level Testing Strategy
If you want a clean test flow, use this order.

1. Service Health Check
- Start container and check if API is reachable:
```bash
docker build -t openenv-devops .
docker run -p 7860:7860 openenv-devops
curl -s http://localhost:7860/tasks
```
- Confirm task list has `easy`, `medium`, `hard`, and `incident_command`.

2. End-to-End API Regression
- Run the built-in smoke test:
```bash
./scripts/smoke_test.sh
```
- This validates `reset -> step -> grader` for easy/medium/hard and baseline.
- For the Phase 2 flow, also run:
```bash
python3 evaluation/run_incident_command_eval.py
```

3. Log Ingestion Path Testing
- JSON text ingestion:
```bash
curl -s -X POST http://localhost:7860/ingest_log \
  -H "Content-Type: application/json" \
  -d '{"source":"manual_text","log":"Out of memory: Killed process 2145 (python3)"}'
```
- File upload ingestion:
```bash
curl -s -X POST http://localhost:7860/ingest_log_file \
  -F "file=@data/live_logs/dmesg.log" \
  -F "source=curl_upload"
```
- Confirm output has: `predicted_label`, `recommended_fix`, `done`, `score`.

4. Sample Log Coverage
- Test with all sample files:
  - `data/live_logs/dmesg.log`
  - `data/live_logs/syslog.log`
  - `data/live_logs/coredump.log`
  - `data/live_logs/live_logs_bundle.txt`
- Goal: every input path should work and return valid JSON.

5. UI Workflow Validation
- Open `http://localhost:7860/log-ui`.
- Validate both:
  - paste log text flow
  - upload file flow
- Confirm returned JSON fields match API output.

6. Result Interpretation Validation
- Functional success criteria:
  - request succeeds (2xx)
  - `done` is `true`
  - `score` is present (`1.0` indicates successful mapped remediation)

# Before running the evaluation commands below, start the server:
```bash
uv run --active server
```

7. Baseline Agent Re-run
```bash
python3 evaluation/run_agent_eval.py --agent baseline --runs 5
```
- This re-runs baseline across `easy`, `medium`, `hard` for multiple rounds.

8. Phase 2 Incident Command Run
```bash
python3 evaluation/run_incident_command_eval.py
```
- Runs the new multi-step incident-response scenario and prints grading breakdown.

9. Standard LLM Agent Run (all tasks)
```bash
export LLM_API_KEY=<your_api_key>
python3 evaluation/run_agent_eval.py \
  --agent llm \
  --runs 1 \
  --model nvidia/llama-3.1-nemotron-70b-instruct
```
- Runs LLM-driven fix selection for all tasks.

10. Score Variance Check
```bash
python3 evaluation/variance_check.py --agent baseline --runs 10
```

## Hackathon Deliverables Checklist
- OpenEnv environment: implemented
- measurable reward model: implemented
- Phase 2 multi-agent scenario: implemented
- full HF TRL training pipeline: implemented in `models/train.py`
- reward-improvement evidence for demo: still to be prepared
- mini-blog or short video: still to be prepared

Optional variance check for LLM:
```bash
export LLM_API_KEY=<your_api_key>
python3 evaluation/variance_check.py \
  --agent llm \
  --runs 10 \
  --model nvidia/llama-3.1-nemotron-70b-instruct
```


## Developer Debugging Guide

1. Confirm latest routes are loaded
```bash
curl -s http://localhost:7860/openapi.json | rg "ingest_log|ingest_log_file|log-ui"
```

2. Verify server is responding
```bash
curl -i http://localhost:7860/tasks
curl -i http://localhost:7860/state
```

3. Debug ingestion requests with verbose curl
```bash
curl -v -X POST http://localhost:7860/ingest_log \
  -H "Content-Type: application/json" \
  -d '{"source":"debug","log":"Connection timed out during TLS handshake"}'
```

4. Debug file upload path
```bash
curl -v -X POST http://localhost:7860/ingest_log_file \
  -F "file=@data/live_logs/dmesg.log" \
  -F "source=debug_upload"
```

5. Validate full environment flow manually
```bash
curl -s -X POST "http://localhost:7860/reset?task_name=easy"
curl -s -X POST http://localhost:7860/step -H "Content-Type: application/json" -d '{"action_type":"analyze_logs"}'
curl -s -X POST http://localhost:7860/step -H "Content-Type: application/json" -d '{"action_type":"take_action","payload":{"fix":"clear_disk"}}'
curl -s -X POST http://localhost:7860/grader
```

## Sample Log Files
- `data/live_logs/coredump.log`
- `data/live_logs/dmesg.log`
- `data/live_logs/syslog.log`
- `data/live_logs/live_logs_bundle.txt`

## Task-wise JSON Testing (easy / medium / hard)
Use this exact flow to validate core environment logic per task.

### Easy
```bash
curl -s -X POST "http://localhost:7860/reset?task_name=easy"
curl -s -X POST http://localhost:7860/step -H "Content-Type: application/json" -d '{"action_type":"analyze_logs"}'
curl -s -X POST http://localhost:7860/step -H "Content-Type: application/json" -d '{"action_type":"take_action","payload":{"fix":"clear_disk"}}'
curl -s -X POST http://localhost:7860/grader
```

### Medium
```bash
curl -s -X POST "http://localhost:7860/reset?task_name=medium"
curl -s -X POST http://localhost:7860/step -H "Content-Type: application/json" -d '{"action_type":"analyze_logs"}'
curl -s -X POST http://localhost:7860/step -H "Content-Type: application/json" -d '{"action_type":"take_action","payload":{"fix":"restart_service"}}'
curl -s -X POST http://localhost:7860/grader
```

### Hard
```bash
curl -s -X POST "http://localhost:7860/reset?task_name=hard"
curl -s -X POST http://localhost:7860/step -H "Content-Type: application/json" -d '{"action_type":"analyze_logs"}'
curl -s -X POST http://localhost:7860/step -H "Content-Type: application/json" -d '{"action_type":"take_action","payload":{"fix":"scale_up"}}'
curl -s -X POST http://localhost:7860/grader
```

Expected for all three:
- final `take_action` response contains `"done":true`
- `POST /grader` returns `"score":1.0`
