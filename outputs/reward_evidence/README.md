# Reward Evidence

Generated: 2026-04-24T08:22:02.176267+00:00

This evidence is generated directly from the local environment and reward engine.
It does not require the HTTP server, which keeps the artifact reproducible in restricted sandboxes.

## Classic Tasks

| Comparison | Mean Score |
| --- | ---: |
| Before: single fallback fix (`restart_service`) | 0.5833 |
| After: task-aligned remediation | 1.0000 |
| Absolute gain | 0.4167 |

| Task | Before | After |
| --- | ---: | ---: |
| easy | 0.4000 | 1.0000 |
| medium | 1.0000 | 1.0000 |
| hard | 0.3500 | 1.0000 |

## Phase 2 Incident Command

| Comparison | Score |
| --- | ---: |
| Before: minimal recovery only | 0.8400 |
| After: delegate + communicate + remediate + postmortem | 1.0000 |
| Absolute gain | 0.1600 |

| Component | Gain |
| --- | ---: |
| recovery | 0.0000 |
| root_cause | 0.0000 |
| efficiency | 0.0000 |
| safety | 0.0000 |
| coordination | 0.0000 |
| communication | 1.0000 |
| learning | 1.0000 |

## Reproduce

```bash
source ~/venv/bin/activate
python3 evaluation/generate_reward_evidence.py
```
