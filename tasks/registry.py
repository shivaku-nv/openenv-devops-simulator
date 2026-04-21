
from tasks.task_easy import get_easy_task
from tasks.task_medium import get_medium_task
from tasks.task_hard import get_hard_task
from tasks.task_incident_command import get_incident_command_task
from utils.reward_engine import evaluate_episode

TASKS = {
    "easy": get_easy_task,
    "medium": get_medium_task,
    "hard": get_hard_task,
    "incident_command": get_incident_command_task,
}

def compute_score(reward: float, task: str) -> float:
    done = reward >= 0.6
    result = evaluate_episode(
        task_name=task,
        task={"reward_profile": task},
        history=[
            {
                "action_type": "analyze_logs",
                "outcome": {"label_correct": done},
            },
            {
                "action_type": "take_action",
                "outcome": {"fix_correct": done},
            },
        ],
        steps=2 if done else 5,
        max_steps=5,
        done=done,
    )
    return result["score"]
