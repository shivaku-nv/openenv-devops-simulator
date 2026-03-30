
from tasks.task_easy import get_easy_task
from tasks.task_medium import get_medium_task
from tasks.task_hard import get_hard_task

TASKS = {
    "easy": get_easy_task,
    "medium": get_medium_task,
    "hard": get_hard_task
}
