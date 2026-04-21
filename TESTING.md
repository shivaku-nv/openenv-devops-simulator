# README - Live Logs Usage

This guide explains how to use raw log files from `data/live_logs/` (like `dmesg`, `syslog`, `coredump`) with this app and how to understand the output.

## Log Files
Available sample files:
- `data/live_logs/dmesg.log`
- `data/live_logs/syslog.log`
- `data/live_logs/coredump.log`
- `data/live_logs/live_logs_bundle.txt`

These are plain text logs, similar to what we normally get from Ubuntu/Linux systems.

## What the App Does With Uploaded Logs
When you upload or post log text, the app:
1. Classifies the log into one issue label (`disk_full`, `memory_leak`, `crash`, `network_issue`).
2. Maps that label to a simulator task and recommended fix.
3. Runs internal environment flow (`analyze_logs -> take_action`).
4. Returns reward, weighted score, and score breakdown.

## Start the API
```bash
docker build -t openenv-devops .
docker run -p 7860:7860 openenv-devops
```

## Method 1: Upload a File (curl)
Upload any `.log` or `.txt` file:

```bash
curl -s -X POST http://localhost:7860/ingest_log_file \
  -F "file=@data/live_logs/dmesg.log" \
  -F "source=curl_upload"
```

Try with other files:

```bash
curl -s -X POST http://localhost:7860/ingest_log_file \
  -F "file=@data/live_logs/syslog.log" \
  -F "source=curl_upload"

curl -s -X POST http://localhost:7860/ingest_log_file \
  -F "file=@data/live_logs/coredump.log" \
  -F "source=curl_upload"
```

## Method 2: Send Raw Log Text (curl JSON)
```bash
curl -s -X POST http://localhost:7860/ingest_log \
  -H "Content-Type: application/json" \
  -d '{"source":"manual_text","log":"Out of memory: Killed process 2145 (python3)"}'
```

## Method 3: Upload in UI
Open:
- `http://localhost:7860/log-ui`

From UI you can:
- paste log text and click `Analyze Pasted Log`
- choose a file and click `Upload and Analyze`

## Response Meaning
A typical response:

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

Field meanings:
- `source`: where the input came from (your custom tag).
- `predicted_label`: model’s issue classification.
- `mapped_task`: internal simulator task selected from label.
- `recommended_fix`: action chosen by simulator for that label.
- `done`: whether the episode finished.
- `last_reward`: reward from final step.
- `score`: weighted episode score.
- `score_breakdown`: component scores used by the reward engine.
- `reward_profile`: scoring profile chosen for that task.

## Expected Label/Fix Mapping
- `disk_full` -> `clear_disk`
- `memory_leak` -> `restart_service`
- `crash` -> `restart_service`
- `network_issue` -> `scale_up`

## Quick Verification Checklist
1. `curl http://localhost:7860/tasks` returns `easy`, `medium`, `hard`, `incident_command`.
2. Upload `dmesg.log` using `/ingest_log_file`.
3. Confirm response includes `predicted_label`, `recommended_fix`, `score`, `score_breakdown`.
4. Confirm `score` is `1.0` for successful run.

## Troubleshooting
- `{"detail":"Not Found"}`:
  - Rebuild/restart container so latest routes are loaded.
- Connection failed:
  - Ensure app is running on `localhost:7860`.

## Task-wise JSON Testing (easy / medium / hard)

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

## Phase 2 Incident Command Testing

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
curl -s http://localhost:7860/state
curl -s -X POST http://localhost:7860/grader
```

Expected:
- `/state` includes `phase`, `alerts`, `deployment_history`, `stakeholder_updates`, `communication_log`, and `postmortem`
- `/grader` returns `score`, `components`, `weighted_components`, and `profile`

You can also run:
```bash
python3 evaluation/run_incident_command_eval.py
```

## Round 2 Coverage Checklist
- problem statement clearly defined: yes
- environment clearly defined: yes
- agent capabilities defined: yes
- tasks defined: yes
- reward logic defined: yes
- self-improvement strategy defined: yes

For final hackathon packaging, also prepare:
- a short reward-improvement demo artifact
- a mini-blog or short video

## Training Pipeline Verification
Install training dependencies:
```bash
source ~/venv/bin/activate
pip install -r requirements-training.txt
```

Smoke-test the training entrypoint:
```bash
python3 models/train.py --help
```

Recommended full run:
```bash
python3 models/train.py \
  --stage all \
  --model-name-or-path Qwen/Qwen2.5-0.5B-Instruct \
  --output-dir outputs/phase2_training
```

Expected artifacts:
- `outputs/phase2_training/sft/`
- `outputs/phase2_training/grpo/`
- `outputs/phase2_training/sft_dataset.jsonl`
- `outputs/phase2_training/eval_metrics.json`
