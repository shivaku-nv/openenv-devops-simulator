from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


DEFAULT_PROFILE_NAME = "default"
PROFILE_PATH = Path(__file__).resolve().parent.parent / "reward_profiles.json"


@lru_cache(maxsize=1)
def load_reward_profiles() -> dict[str, dict[str, Any]]:
    with PROFILE_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload.get("profiles", {})


def _find_events(history: list[dict[str, Any]], action_type: str) -> list[dict[str, Any]]:
    return [entry for entry in history if entry.get("action_type") == action_type]


def _score_efficiency(steps: int, max_steps: int, recovered: bool, ideal_steps: int) -> float:
    if not recovered or max_steps <= 0:
        return 0.0
    budget = max(max_steps - ideal_steps, 0)
    overshoot = max(steps - ideal_steps, 0)
    if budget == 0:
        return 1.0 if steps <= ideal_steps else 0.0
    return max(0.0, 1.0 - (overshoot / budget))


def _score_safety(remediation_events: list[dict[str, Any]], recovered: bool) -> float:
    if not remediation_events:
        return 0.0
    harmful = sum(1 for entry in remediation_events if not entry.get("outcome", {}).get("fix_correct", False))
    if harmful == 0:
        return 1.0
    total = len(remediation_events)
    base = max(0.0, 1.0 - (harmful / total))
    return min(base, 0.5 if recovered else base)


def _score_coordination(history: list[dict[str, Any]]) -> float:
    if len(history) <= 1:
        return 1.0
    penalties = 0
    for prev, current in zip(history, history[1:]):
        if prev.get("action_type") == current.get("action_type"):
            penalties += 1
    return max(0.0, 1.0 - penalties / (len(history) - 1))


def _score_optional_dimension(task: dict[str, Any], key: str) -> float:
    return 0.0 if task.get(key) else 1.0


def _score_communication(task: dict[str, Any], history: list[dict[str, Any]]) -> float:
    if not task.get("requires_communication"):
        return 1.0
    communication_events = _find_events(history, "communicate_status")
    return 1.0 if communication_events else 0.0


def _score_learning(task: dict[str, Any], history: list[dict[str, Any]]) -> float:
    if not task.get("requires_postmortem"):
        return 1.0
    postmortem_events = _find_events(history, "write_postmortem")
    return 1.0 if postmortem_events else 0.0


def evaluate_episode(
    *,
    task_name: str | None,
    task: dict[str, Any] | None,
    history: list[dict[str, Any]],
    steps: int,
    max_steps: int,
    done: bool,
) -> dict[str, Any]:
    task = task or {}
    profile_name = task.get("reward_profile") or task_name or DEFAULT_PROFILE_NAME
    profiles = load_reward_profiles()
    weights = profiles.get(profile_name, profiles.get(DEFAULT_PROFILE_NAME, {}))
    ideal_steps = int(weights.get("ideal_steps", 2))

    analyze_events = _find_events(history, "analyze_logs")
    remediation_events = _find_events(history, "take_action")

    root_cause_correct = any(entry.get("outcome", {}).get("label_correct", False) for entry in analyze_events)
    recovered = any(entry.get("outcome", {}).get("fix_correct", False) for entry in remediation_events) and done

    components = {
        "recovery": 1.0 if recovered else 0.0,
        "root_cause": 1.0 if root_cause_correct else 0.0,
        "efficiency": _score_efficiency(
            steps=steps,
            max_steps=max_steps,
            recovered=recovered,
            ideal_steps=ideal_steps,
        ),
        "safety": _score_safety(remediation_events=remediation_events, recovered=recovered),
        "coordination": _score_coordination(history),
        "communication": _score_communication(task, history),
        "learning": _score_learning(task, history),
    }

    weighted_components = {
        name: round(float(weights.get(name, 0.0)) * value, 4) for name, value in components.items()
    }
    score = round(sum(weighted_components.values()), 4)

    return {
        "profile": profile_name,
        "weights": weights,
        "components": components,
        "weighted_components": weighted_components,
        "score": score,
    }
