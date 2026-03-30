
import json
import urllib.request


BASE = "http://localhost:7860"


def http_json(method: str, path: str, payload: dict | None = None) -> dict:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run() -> None:
    http_json("POST", "/reset")
    http_json("POST", "/step", {"action_type": "analyze_logs"})
    state = http_json("GET", "/state")
    fix = state["task"]["solution"]
    result = http_json("POST", "/step", {"action_type": "take_action", "payload": {"fix": fix}})
    score = http_json("POST", "/grader")["score"]
    print({"done": result["done"], "reward": result["reward"], "score": score})


if __name__ == "__main__":
    run()
