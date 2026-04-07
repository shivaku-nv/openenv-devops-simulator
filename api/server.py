
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from env.devops_env import DevOpsEnv
from env.base_env import Action
from tasks.registry import TASKS
from graders.registry import grade
from models.log_classifier import classify_log
from tasks.registry import compute_score

app = FastAPI()
env = DevOpsEnv()


def render_log_ui() -> str:
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Live Log Ingestion</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 900px; margin: 24px auto; padding: 0 16px; }
    textarea { width: 100%; height: 220px; }
    .row { margin-bottom: 14px; }
    button { padding: 8px 14px; margin-right: 8px; }
    pre { background: #f5f5f5; padding: 12px; overflow: auto; }
  </style>
</head>
<body>
  <h2>Live Log Analyzer</h2>
  <div class="row">
    <label>Paste raw logs:</label>
    <textarea id="logText" placeholder="Paste syslog/dmesg/core-dump text here"></textarea>
  </div>
  <div class="row">
    <button onclick="analyzeText()">Analyze Pasted Log</button>
  </div>
  <div class="row">
    <label>Or upload a log file:</label>
    <input type="file" id="logFile" />
    <button onclick="analyzeFile()">Upload and Analyze</button>
  </div>
  <h3>Result</h3>
  <pre id="result">No result yet.</pre>
  <script>
    async function analyzeText() {
      const log = document.getElementById('logText').value;
      const res = await fetch('/ingest_log', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({source: 'ui_text', log})
      });
      const data = await res.json();
      document.getElementById('result').textContent = JSON.stringify(data, null, 2);
    }
    async function analyzeFile() {
      const fileInput = document.getElementById('logFile');
      if (!fileInput.files.length) {
        document.getElementById('result').textContent = 'Please choose a file first.';
        return;
      }
      const form = new FormData();
      form.append('file', fileInput.files[0]);
      form.append('source', 'ui_file');
      const res = await fetch('/ingest_log_file', {method: 'POST', body: form});
      const data = await res.json();
      document.getElementById('result').textContent = JSON.stringify(data, null, 2);
      fileInput.value = '';
    }
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def home():
    return render_log_ui()


@app.get("/web", response_class=HTMLResponse)
def web_home():
    return render_log_ui()

def run_ingestion(log_text: str, source: str = "unknown"):
    text = (log_text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Missing log text")

    predicted_label = classify_log(text)
    remediation_map = {
        "disk_full": ("easy", "clear_disk"),
        "memory_leak": ("medium", "restart_service"),
        "crash": ("medium", "restart_service"),
        "network_issue": ("hard", "scale_up"),
    }
    task_name, fix = remediation_map[predicted_label]

    env.reset(task_name)
    env.task["logs"] = text
    env.step(Action(action_type="analyze_logs"))
    _, reward, done, _ = env.step(Action(action_type="take_action", payload={"fix": fix}))
    state = env.state()
    score = compute_score(reward, task_name)
    return {
        "source": source,
        "predicted_label": predicted_label,
        "mapped_task": task_name,
        "recommended_fix": fix,
        "done": done,
        "last_reward": reward,
        "score": score
    }

@app.post("/reset")
def reset(task_name: str = None):
    return env.reset(task_name)

@app.post("/step")
def step(action: dict):
    act = Action(**action)
    obs, reward, done, _ = env.step(act)
    return {"observation": obs, "reward": reward, "done": done}

@app.get("/state")
def state():
    return env.state()

@app.get("/tasks")
def tasks():
    return {"tasks": list(TASKS.keys())}

@app.post("/grader")
def grader():
    state = env.state()
    reward = state["history"][-1].get("reward", 0.5) if state["history"] else 0.5
    score = compute_score(reward, state["task"]["name"])
    return {"score": score}

@app.get("/baseline")
def baseline(task_name: str = None):
    env.reset(task_name)
    env.step(Action(action_type="analyze_logs"))
    solution = env.task["solution"]
    _, reward, done, _ = env.step(Action(action_type="take_action", payload={"fix": solution}))
    state = env.state()
    score = compute_score(reward, env.task_name)
    return {
        "task_name": env.task_name,
        "done": done,
        "last_reward": reward,
        "score": score
    }

@app.post("/ingest_log")
def ingest_log(payload: dict):
    log_text = (payload or {}).get("log", "")
    source = (payload or {}).get("source", "json")
    return run_ingestion(log_text, source)

@app.post("/ingest_log_file")
async def ingest_log_file(file: UploadFile = File(...), source: str = Form("file_upload")):
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    try:
        log_text = raw.decode("utf-8")
    except UnicodeDecodeError:
        log_text = raw.decode("latin-1")
    return run_ingestion(log_text, source)

@app.get("/log-ui", response_class=HTMLResponse)
def log_ui():
    return render_log_ui()
