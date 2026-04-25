# OpenEnv DevOps Incident Simulator: A Multi-Step RL Environment for Incident Response

The strongest production incidents are never just classification problems. They are coordination problems. Teams have to inspect logs, reconcile metrics, react to operational context, communicate clearly, and convert the incident into learning after recovery. That is the gap this project tries to close.

We built an OpenEnv environment for DevOps incident response that starts with realistic logs and expands into a richer, multi-step workflow. The project supports classic log-triage scenarios and a Phase 2 `incident_command` scenario designed around the OpenEnv Round 2 themes: multi-agent interaction, long-horizon planning, world modeling for professional workflows, and self-improvement.

## What the Environment Does

The environment exposes the standard OpenEnv-style interaction loop:

- `reset`
- `step`
- `state`
- `grader`

The classic tasks are intentionally simple:

- `easy`: disk pressure
- `medium`: memory leak
- `hard`: network issue

Each of those tasks supports the familiar flow of:

1. analyze the logs
2. choose a remediation
3. receive reward and grading

That baseline is useful because it gives a compact, reproducible environment for testing simple policy behavior. But the more interesting work happens in the Phase 2 scenario.

## The Phase 2 Incident Command Scenario

The `incident_command` task models a production checkout outage with memory pressure, deployment context, user impact, and operational coordination requirements. The environment includes:

- logs
- metrics
- alert state
- deployment history
- stakeholder updates
- recommended roles

The agent can take a richer set of actions:

- `delegate_investigation`
- `communicate_status`
- `analyze_logs`
- `take_action`
- `write_postmortem`

This matters because the task is not just “guess the correct fix.” A strong response should behave more like an actual incident commander:

- delegate quickly
- keep stakeholders informed
- restore service safely
- preserve learning after resolution

## Why the Reward Design Matters

The reward engine is intentionally decomposed rather than binary. It scores:

- recovery
- root-cause accuracy
- efficiency
- safety
- coordination
- communication
- learning

That choice makes the environment much harder to game with shallow strategies. A policy that restores service but skips communication and postmortem work will still score well, but not perfectly. A fuller incident-response trajectory earns the maximum score because it reflects better operational behavior.

## Reward Evidence

The repo now includes a reproducible reward-evidence artifact generated directly from the local environment and reward engine.

Current results:

- classic tasks improve from `0.5833` mean score to `1.0000`
- `incident_command` improves from `0.8400` to `1.0000`

The classic comparison measures the difference between:

- a naive single-fix fallback policy
- a task-aligned remediation policy

The Phase 2 comparison measures the difference between:

- a minimal recovery-only flow
- a fuller playbook with delegation, communication, remediation, and postmortem

That evidence is important for hackathon judging because it shows the environment is sensitive to better behavior, not just task completion.

## Training Path

The project also includes a practical training entrypoint in `models/train.py`. It supports:

- supervised fine-tuning on oracle action plans
- GRPO fine-tuning against the local reward engine
- local evaluation artifacts

This gives the project a clear bridge from environment design to post-training, which is exactly what OpenEnv is built to support.

## Why This Project Fits Round 2

This submission aligns well with the Round 2 themes:

- Multi-Agent Interactions: the Phase 2 task explicitly rewards delegation and coordination
- Long-Horizon Planning: success depends on sequencing investigation, action, communication, and learning
- World Modeling for Professional Tasks: the environment models real operational context, not just toy prompts
- Self-Improvement: the environment produces structured trajectories that can be reused for better prompts, better playbooks, or RL post-training

## Links

- Space: `https://shivakunv-devops-incident-sim.hf.space/`
- Repository: `https://github.com/shivaku-nv/openenv-devops-simulator`
- Reward evidence: `outputs/reward_evidence/README.md`
- Notebook: `notebooks/openenv_devops_submission.ipynb`

If published as a Hugging Face article, this post can be pasted directly into the blog editor with minor formatting cleanup only.
