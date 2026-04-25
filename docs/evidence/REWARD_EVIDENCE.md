# Reward Evidence

This page summarizes the checked-in reward evidence under [`outputs/reward_evidence/`](../../outputs/reward_evidence/README.md).

## What It Shows

The repo now includes a reproducible reward-evidence generator:

```bash
source ~/venv/bin/activate
python3 evaluation/generate_reward_evidence.py
```

That script runs the environment directly and writes:

- `outputs/reward_evidence/classic_policy_comparison.json`
- `outputs/reward_evidence/incident_command_comparison.json`
- `outputs/reward_evidence/summary.json`
- `outputs/reward_evidence/README.md`

## Current Results

Classic tasks:

- Before: a naive single-fix policy scores `0.5833` mean reward across `easy`, `medium`, and `hard`
- After: a task-aligned remediation policy scores `1.0000`
- Absolute gain: `0.4167`

Phase 2 `incident_command`:

- Before: a minimal recovery-only flow scores `0.8400`
- After: the full incident playbook scores `1.0000`
- Absolute gain: `0.1600`

## Why This Counts

This is honest, local evidence of reward improvement inside the exact environment used by the project:

- the same task definitions are used
- the same reward engine is used
- the same action interface is used

If you later run GRPO or SFT+GRPO training, these artifacts can be extended with learned-policy checkpoints and reward curves. For the current submission package, this gives a clean before/after proof that the environment rewards fuller, better incident behavior.
