import argparse
import json
import urllib.request


def http_json(method: str, url: str, payload: dict | None = None) -> dict:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def step(base_url: str, action_type: str, payload: dict | None = None) -> dict:
    body = {"action_type": action_type}
    if payload:
        body["payload"] = payload
    return http_json("POST", f"{base_url}/step", body)


def run_once(base_url: str) -> dict:
    http_json("POST", f"{base_url}/reset?task_name=incident_command")

    steps = [
        step(
            base_url,
            "delegate_investigation",
            {"role": "sre_agent", "objective": "Check memory pressure and recent deployment changes"},
        ),
        step(
            base_url,
            "communicate_status",
            {"audience": "stakeholders", "summary": "Investigating checkout degradation and elevated latency."},
        ),
        step(base_url, "analyze_logs"),
        step(base_url, "take_action", {"fix": "restart_service"}),
        step(
            base_url,
            "write_postmortem",
            {
                "summary": "checkout-api memory pressure after deployment caused failed checkouts.",
                "action_items": [
                    "Add memory regression guard to rollout checks",
                    "Create alert for sustained OOM restart loops",
                ],
            },
        ),
    ]

    state = http_json("GET", f"{base_url}/state")
    grading = http_json("POST", f"{base_url}/grader")
    return {
        "steps": steps,
        "phase": state.get("phase"),
        "communication_log": state.get("communication_log", []),
        "postmortem": state.get("postmortem"),
        "grading": grading,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Phase 2 incident_command scenario.")
    parser.add_argument("--base-url", default="http://localhost:7860")
    args = parser.parse_args()

    result = run_once(args.base_url)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
