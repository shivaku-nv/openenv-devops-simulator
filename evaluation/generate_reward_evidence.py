from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from env.base_env import Action
from env.devops_env import DevOpsEnv
from graders.registry import grade


OUTPUT_DIR = Path("outputs/reward_evidence")


@dataclass
class EpisodeResult:
    task_name: str
    variant: str
    actions: list[dict[str, Any]]
    score: float
    profile: str
    components: dict[str, float]
    weighted_components: dict[str, float]


def run_episode(task_name: str, variant: str, actions: list[dict[str, Any]]) -> EpisodeResult:
    env = DevOpsEnv()
    env.reset(task_name)

    for action in actions:
        env.step(Action(action_type=action["action_type"], payload=action.get("payload", {})))

    grading = grade(env.state())
    return EpisodeResult(
        task_name=task_name,
        variant=variant,
        actions=actions,
        score=float(grading["score"]),
        profile=str(grading["profile"]),
        components={key: float(value) for key, value in grading["components"].items()},
        weighted_components={key: float(value) for key, value in grading["weighted_components"].items()},
    )


def classic_policy_comparison() -> dict[str, Any]:
    before_fix = "restart_service"
    before_results = [
        run_episode(
            task_name=task_name,
            variant="before_naive_single_fix",
            actions=[
                {"action_type": "analyze_logs"},
                {"action_type": "take_action", "payload": {"fix": before_fix}},
            ],
        )
        for task_name in ("easy", "medium", "hard")
    ]

    oracle_fixes = {
        "easy": "clear_disk",
        "medium": "restart_service",
        "hard": "scale_up",
    }
    after_results = [
        run_episode(
            task_name=task_name,
            variant="after_task_aligned_fix",
            actions=[
                {"action_type": "analyze_logs"},
                {"action_type": "take_action", "payload": {"fix": fix}},
            ],
        )
        for task_name, fix in oracle_fixes.items()
    ]

    before_mean = round(mean(result.score for result in before_results), 4)
    after_mean = round(mean(result.score for result in after_results), 4)
    return {
        "experiment": "classic_task_reward_uplift",
        "before_mean_score": before_mean,
        "after_mean_score": after_mean,
        "absolute_gain": round(after_mean - before_mean, 4),
        "before": [asdict(result) for result in before_results],
        "after": [asdict(result) for result in after_results],
    }


def incident_command_comparison() -> dict[str, Any]:
    before = run_episode(
        task_name="incident_command",
        variant="before_minimal_recovery_only",
        actions=[
            {"action_type": "analyze_logs"},
            {"action_type": "take_action", "payload": {"fix": "restart_service"}},
        ],
    )
    after = run_episode(
        task_name="incident_command",
        variant="after_full_incident_playbook",
        actions=[
            {
                "action_type": "delegate_investigation",
                "payload": {
                    "role": "sre_agent",
                    "objective": "Check memory pressure and recent deployment changes",
                },
            },
            {
                "action_type": "communicate_status",
                "payload": {
                    "audience": "stakeholders",
                    "summary": "Investigating checkout degradation and elevated latency.",
                },
            },
            {"action_type": "analyze_logs"},
            {"action_type": "take_action", "payload": {"fix": "restart_service"}},
            {
                "action_type": "write_postmortem",
                "payload": {
                    "summary": "checkout-api memory pressure after deployment caused failed checkouts.",
                    "action_items": [
                        "Add memory regression guard to rollout checks",
                        "Create alert for sustained OOM restart loops",
                    ],
                },
            },
        ],
    )

    component_gain = {
        key: round(after.components[key] - before.components[key], 4)
        for key in before.components
    }
    return {
        "experiment": "incident_command_reward_uplift",
        "before": asdict(before),
        "after": asdict(after),
        "absolute_gain": round(after.score - before.score, 4),
        "component_gain": component_gain,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_summary_markdown(path: Path, classic: dict[str, Any], phase2: dict[str, Any]) -> None:
    lines = [
        "# Reward Evidence",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "This evidence is generated directly from the local environment and reward engine.",
        "It does not require the HTTP server, which keeps the artifact reproducible in restricted sandboxes.",
        "",
        "## Classic Tasks",
        "",
        "| Comparison | Mean Score |",
        "| --- | ---: |",
        f"| Before: single fallback fix (`restart_service`) | {classic['before_mean_score']:.4f} |",
        f"| After: task-aligned remediation | {classic['after_mean_score']:.4f} |",
        f"| Absolute gain | {classic['absolute_gain']:.4f} |",
        "",
        "| Task | Before | After |",
        "| --- | ---: | ---: |",
    ]

    before_by_task = {row["task_name"]: row for row in classic["before"]}
    after_by_task = {row["task_name"]: row for row in classic["after"]}
    for task_name in ("easy", "medium", "hard"):
        lines.append(
            f"| {task_name} | {before_by_task[task_name]['score']:.4f} | {after_by_task[task_name]['score']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Phase 2 Incident Command",
            "",
            "| Comparison | Score |",
            "| --- | ---: |",
            f"| Before: minimal recovery only | {phase2['before']['score']:.4f} |",
            f"| After: delegate + communicate + remediate + postmortem | {phase2['after']['score']:.4f} |",
            f"| Absolute gain | {phase2['absolute_gain']:.4f} |",
            "",
            "| Component | Gain |",
            "| --- | ---: |",
        ]
    )

    for key, value in phase2["component_gain"].items():
        lines.append(f"| {key} | {value:.4f} |")

    lines.extend(
        [
            "",
            "## Reproduce",
            "",
            "```bash",
            "source ~/venv/bin/activate",
            "python3 evaluation/generate_reward_evidence.py",
            "```",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    classic = classic_policy_comparison()
    phase2 = incident_command_comparison()
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classic": classic,
        "incident_command": phase2,
    }

    write_json(OUTPUT_DIR / "classic_policy_comparison.json", classic)
    write_json(OUTPUT_DIR / "incident_command_comparison.json", phase2)
    write_json(OUTPUT_DIR / "summary.json", summary)
    write_summary_markdown(OUTPUT_DIR / "README.md", classic, phase2)


if __name__ == "__main__":
    main()
