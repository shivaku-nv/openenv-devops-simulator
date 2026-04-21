from __future__ import annotations

from typing import Any

from utils.reward_engine import evaluate_episode


def grade(state: dict[str, Any]) -> dict[str, Any]:
    return evaluate_episode(
        task_name=state.get("task_name"),
        task=state.get("task"),
        history=state.get("history", []),
        steps=state.get("step_count", 0),
        max_steps=state.get("max_steps", 0),
        done=state.get("done", False),
    )
