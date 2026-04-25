# OpenEnv Submission

## Phase 2 Summary
Primary Phase 2 scenario:
- `incident_command`

Core themes covered:
- multi-agent interactions
- long-horizon planning and instruction following
- world modeling for professional workflows
- self-improving agent systems

Key differentiators:
- specialist-agent coordination
- configurable reward engine with score breakdown
- post-incident learning loop
- direct extension of an already working OpenEnv simulator
- full TRL training pipeline in `models/train.py`

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
python3 evaluation/run_incident_command_eval.py
python3 models/train.py --stage eval --model-name-or-path outputs/phase2_training/grpo
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

## Final Deliverables To Package
- environment deployment on OpenEnv / Hugging Face Space
- problem statement in `PHASE2_PROBLEM_STATEMENT.md`
- training pipeline in `models/train.py` plus `requirements-training.txt`
- stable public training Colab notebook: `https://colab.research.google.com/drive/16jxAyoxadyQglSzYBZe-Vo8Qe9P3oTcz?usp=sharing`
- before/after reward evidence or reward curves in `outputs/reward_evidence/`
- short blog post or short video demo draft in `docs/demo/MINI_BLOG.md`
