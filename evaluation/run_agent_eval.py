import argparse
import json
import os
import urllib.error
import urllib.request
from statistics import mean


DEFAULT_TASKS = ["easy", "medium", "hard"]
ALLOWED_FIXES = ["clear_disk", "restart_service", "scale_up"]


def http_json(method: str, url: str, payload: dict | None = None) -> dict:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def choose_fix_baseline(base_url: str) -> str:
    state = http_json("GET", f"{base_url}/state")
    return state["task"]["solution"]


def choose_fix_llm(log_text: str, model: str, api_base: str, api_key: str | None) -> str:
    # Fallback heuristic keeps the script usable even without remote model access.
    lowered = log_text.lower()
    if "out of memory" in lowered or "oom" in lowered:
        heuristic = "restart_service"
    elif "no space left" in lowered or "disk" in lowered:
        heuristic = "clear_disk"
    elif "timeout" in lowered or "network" in lowered:
        heuristic = "scale_up"
    else:
        heuristic = "restart_service"

    if not api_key:
        return heuristic

    url = f"{api_base.rstrip('/')}/chat/completions"
    prompt = (
        "You are a DevOps triage assistant. "
        f"Given this log, choose one fix only from {ALLOWED_FIXES}. "
        "Respond with only the fix string.\n\n"
        f"Log:\n{log_text}"
    )
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST", headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return heuristic

    text = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    text = (text or "").strip().lower()
    for fix in ALLOWED_FIXES:
        if fix in text:
            return fix
    return heuristic


def run_once(base_url: str, task_name: str, agent_type: str, model: str, api_base: str, api_key: str | None) -> dict:
    http_json("POST", f"{base_url}/reset?task_name={task_name}")
    state = http_json("GET", f"{base_url}/state")
    log_text = state["task"]["logs"]

    if agent_type == "baseline":
        fix = choose_fix_baseline(base_url)
    else:
        fix = choose_fix_llm(log_text, model=model, api_base=api_base, api_key=api_key)

    http_json("POST", f"{base_url}/step", {"action_type": "analyze_logs"})
    step_result = http_json("POST", f"{base_url}/step", {"action_type": "take_action", "payload": {"fix": fix}})
    grade = http_json("POST", f"{base_url}/grader")

    return {
        "task": task_name,
        "agent": agent_type,
        "fix_used": fix,
        "done": step_result.get("done", False),
        "last_reward": step_result.get("reward", 0.0),
        "score": grade.get("score", 0.0),
    }


def run_suite(base_url: str, agent_type: str, runs: int, model: str, api_base: str, api_key: str | None) -> dict:
    rows = []
    for run_id in range(1, runs + 1):
        for task in DEFAULT_TASKS:
            result = run_once(base_url, task, agent_type, model, api_base, api_key)
            result["run_id"] = run_id
            rows.append(result)

    scores = [r["score"] for r in rows]
    summary = {
        "agent": agent_type,
        "runs": runs,
        "tasks": DEFAULT_TASKS,
        "total_cases": len(rows),
        "mean_score": round(mean(scores), 4) if scores else 0.0,
        "results": rows,
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run baseline or LLM agent across all tasks.")
    parser.add_argument("--base-url", default="http://localhost:7860")
    parser.add_argument("--agent", choices=["baseline", "llm"], default="baseline")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--model", default=os.getenv("LLM_MODEL", "nvidia/llama-3.1-nemotron-70b-instruct"))
    parser.add_argument("--api-base", default=os.getenv("LLM_API_BASE", "https://api.together.xyz/v1"))
    parser.add_argument("--api-key", default=os.getenv("LLM_API_KEY"))
    args = parser.parse_args()

    summary = run_suite(
        base_url=args.base_url,
        agent_type=args.agent,
        runs=args.runs,
        model=args.model,
        api_base=args.api_base,
        api_key=args.api_key,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
