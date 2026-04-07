# OpenEnv Submission

## Step 1
```bash
openenv init devops_incident_sim
```

## Step 2
Test locally
```bash
uv sync --active
uv run server
```

## Step 3
verify:
```bash
curl -s http://localhost:7860/tasks
./scripts/smoke_test.sh
./scripts/pre_submission_check.sh
python3 inference.py
```

log-ui:
```text
http://localhost:7860/log-ui
```

## Step 4
Hugging Face push
```bash
openenv push --repo-id shivakunv/devops_incident_sim
```

## Step 5 
Check deployment: 
Browser
```bash
https://shivakunv-devops-incident-sim.hf.space/
https://shivakunv-devops-incident-sim.hf.space/web
https://shivakunv-devops-incident-sim.hf.space/log-ui
```
Command Line:
```bash
SPACE_URL="https://shivakunv-devops-incident-sim.hf.space"
curl -i "$SPACE_URL/"
curl -i "$SPACE_URL/web"
curl -i "$SPACE_URL/log-ui"
curl -s "$SPACE_URL/tasks"
curl -s -X POST "$SPACE_URL/ingest_log" \
  -H "Content-Type: application/json" \
  -d '{"source":"manual_text","log":"Out of memory: Killed process 2145 (python3)"}'
```

Command Line:
```bash
./validate-submission.sh https://shivakunv-devops-incident-sim.hf.space
```
