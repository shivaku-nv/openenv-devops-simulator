
from tasks.task_easy import get_easy_task
from tasks.task_medium import get_medium_task
from tasks.task_hard import get_hard_task

TASKS = {
    "easy": get_easy_task,
    "medium": get_medium_task,
    "hard": get_hard_task
}

def compute_score(reward: float, task: str) -> float:
    task_bonus = {
        "easy": 0.1,
        "medium": 0.0,
        "hard": -0.1,
    }

    score = float(reward) + task_bonus.get(task, 0.0)
    return max(0.01, min(0.99, score))
