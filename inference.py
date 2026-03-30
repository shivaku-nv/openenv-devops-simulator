"""Root inference entrypoint for submission validation."""

from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from env.base_env import Action
from env.devops_env import DevOpsEnv
from graders.registry import grade
from tasks.registry import TASKS

ALLOWED_FIXES = ("clear_disk", "restart_service", "scale_up")


def emit(tag: str, **fields: Any) -> None:
    parts = [f"{key}={json.dumps(value)}" for key, value in fields.items()]
    print(f"[{tag}] {' '.join(parts)}", flush=True)


def heuristic_fix(log_text: str) -> str:
    lowered = (log_text or "").lower()
    if "space" in lowered or "disk" in lowered:
        return "clear_disk"
    if "timeout" in lowered or "network" in lowered or "resolution" in lowered:
        return "scale_up"
    return "restart_service"


def choose_fix_with_llm(log_text: str) -> str:
    api_base = os.getenv("API_BASE_URL", "").strip()
    model_name = os.getenv("MODEL_NAME", "").strip()
    api_key = os.getenv("HF_TOKEN", "").strip()
    fallback = heuristic_fix(log_text)

    if not api_base or not model_name or not api_key:
        return fallback

    client = OpenAI(base_url=api_base.rstrip("/"), api_key=api_key)
    prompt = (
        "You are a DevOps incident triage assistant.\n"
        f"Pick exactly one fix from {list(ALLOWED_FIXES)}.\n"
        "Respond with only the fix string.\n\n"
        f"Log:\n{log_text}"
    )

    try:
        response = client.chat.completions.create(
            model=model_name,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception:
        return fallback

    content = response.choices[0].message.content or ""
    lowered = content.lower()
    for fix in ALLOWED_FIXES:
        if fix in lowered:
            return fix
    return fallback


def run_once(task_name: str) -> dict[str, Any]:
    env = DevOpsEnv()
    observation = env.reset(task_name)
    emit("START", task=task_name, episode_id=env.episode_id)

    log_text = env.task["logs"]
    fix = choose_fix_with_llm(log_text)

    _, analyze_reward, analyze_done, _ = env.step(Action(action_type="analyze_logs"))
    emit(
        "STEP",
        task=task_name,
        step=1,
        action="analyze_logs",
        reward=round(analyze_reward, 4),
        done=analyze_done,
        logs_preview=observation.logs[:80],
    )

    _, reward, done, _ = env.step(Action(action_type="take_action", payload={"fix": fix}))
    emit(
        "STEP",
        task=task_name,
        step=2,
        action="take_action",
        fix=fix,
        reward=round(reward, 4),
        done=done,
    )

    score = grade(env.history, env.task)
    emit("END", task=task_name, score=score, steps=env.steps, fix=fix, done=done)

    return {
        "task": task_name,
        "predicted_fix": fix,
        "done": done,
        "reward": reward,
        "score": score,
    }


def main() -> None:
    results = [run_once(task_name) for task_name in TASKS]
    avg_score = sum(row["score"] for row in results) / len(results)
    emit("END", task="summary", score=round(avg_score, 4), steps=len(results), done=True)


if __name__ == "__main__":
    main()
