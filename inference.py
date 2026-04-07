"""Root inference entrypoint for submission validation."""

from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from env.base_env import Action
from env.devops_env import DevOpsEnv
from graders.registry import grade
from tasks.registry import TASKS

ALLOWED_FIXES = ("clear_disk", "restart_service", "scale_up")
DEFAULT_API_BASE_URL = "https://api.together.xyz/v1"
DEFAULT_MODEL_NAME = "nvidia/llama-3.1-nemotron-70b-instruct"
API_BASE_URL = os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL).strip()
MODEL_NAME = os.getenv("MODEL_NAME", DEFAULT_MODEL_NAME).strip()
HF_TOKEN = os.getenv("HF_TOKEN", "").strip()
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME", "").strip()


def format_value(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return f"{value:.4f}"
    text = str(value)
    return text.replace(" ", "_")


def emit(tag: str, **fields: Any) -> None:
    parts = [f"{key}={format_value(value)}" for key, value in fields.items()]
    print(f"[{tag}] {' '.join(parts)}", flush=True)


def heuristic_fix(log_text: str) -> str:
    lowered = (log_text or "").lower()
    if "space" in lowered or "disk" in lowered:
        return "clear_disk"
    if "timeout" in lowered or "network" in lowered or "resolution" in lowered:
        return "scale_up"
    return "restart_service"


def choose_fix_with_llm(log_text: str) -> str:
    fallback = heuristic_fix(log_text)

    if not HF_TOKEN:
        return fallback

    client = OpenAI(base_url=API_BASE_URL.rstrip("/"), api_key=HF_TOKEN)
    prompt = (
        "You are a DevOps incident triage assistant.\n"
        f"Pick exactly one fix from {list(ALLOWED_FIXES)}.\n"
        "Respond with only the fix string.\n\n"
        f"Log:\n{log_text}"
    )

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
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
        logs_preview=observation.logs[:80].replace("\n", " "),
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
    score = max(0.01, min(0.99, float(score)))
    emit("END", task=task_name, score=score, steps=env.steps, fix=fix, done=done)

    return {
        "task": task_name,
        "predicted_fix": fix,
        "done": done,
        "reward": reward,
        "score": score,
    }


def main() -> None:
    for task_name in TASKS:
        run_once(task_name)


if __name__ == "__main__":
    main()
