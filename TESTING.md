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
4. Returns reward and grader score.

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
  "score": 1.0
}
```

Field meanings:
- `source`: where the input came from (your custom tag).
- `predicted_label`: model’s issue classification.
- `mapped_task`: internal simulator task selected from label.
- `recommended_fix`: action chosen by simulator for that label.
- `done`: whether the episode finished.
- `last_reward`: reward from final step.
- `score`: deterministic grader score (`1.0` success, `0.0` failure).

## Expected Label/Fix Mapping
- `disk_full` -> `clear_disk`
- `memory_leak` -> `restart_service`
- `crash` -> `restart_service`
- `network_issue` -> `scale_up`

## Quick Verification Checklist
1. `curl http://localhost:7860/tasks` returns `easy`, `medium`, `hard`.
2. Upload `dmesg.log` using `/ingest_log_file`.
3. Confirm response includes `predicted_label`, `recommended_fix`, `score`.
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
