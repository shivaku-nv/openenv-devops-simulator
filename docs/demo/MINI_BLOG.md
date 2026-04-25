# OpenEnv DevOps Incident Simulator

## Mini Blog Draft

This project turns DevOps incident response into an OpenEnv environment that can be used for evaluation and RL post-training. Instead of treating incidents as one-shot classification, the environment models a more realistic workflow: inspect evidence, coordinate across roles, choose a remediation, communicate status, and capture the learning after the incident is resolved.

The repo now supports four task shapes:

- `easy`, `medium`, and `hard` for classic log-triage and remediation
- `incident_command` for the multi-step Phase 2 scenario

The Phase 2 scenario is where the environment gets interesting. The agent has to reason over logs, metrics, deployment context, and stakeholder pressure. The reward system does not only check whether the service recovered. It also scores root-cause accuracy, safety, efficiency, coordination, communication, and learning artifacts like postmortems.

That reward design matters because it prevents the environment from collapsing into a shallow “guess the fix” benchmark. A minimal recovery-only flow scores well, but not perfectly. The full playbook reaches the maximum score because it includes delegation, stakeholder updates, and post-incident learning.

The repo also includes a practical training path in `models/train.py`. It supports supervised bootstrap on oracle plans plus GRPO fine-tuning against the local reward engine. That makes the environment usable not just for demos, but for actual post-training experiments.

## Demo Points

Use this order for a short walkthrough:

1. Show `README.md` and the task list (`easy`, `medium`, `hard`, `incident_command`)
2. Explain that the environment exposes `reset`, `step`, `state`, `grader`, and log-ingestion endpoints
3. Run the reward-evidence generator and show the before/after lift in `outputs/reward_evidence/README.md`
4. Show the `incident_command` task definition and explain why communication and postmortem actions matter
5. Close with `models/train.py` as the path to SFT and GRPO experimentation

## Short Video Script

If you record a sub-2-minute video, this script is ready to use:

“We built an OpenEnv DevOps incident simulator for the Round 2 hackathon. The environment starts from realistic logs and expands into a full incident-command workflow. Agents can analyze logs, delegate investigation, communicate status, remediate safely, and write a postmortem. The reward engine scores not just recovery, but also root-cause accuracy, safety, coordination, communication, and learning. We included a reproducible reward-evidence artifact in the repo showing that fuller incident behavior earns higher scores than a shallow recovery-only strategy. Finally, the project includes a TRL-compatible training pipeline for supervised bootstrap and GRPO fine-tuning, so the environment is ready for both demo and post-training work.”
