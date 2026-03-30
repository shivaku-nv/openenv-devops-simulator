
import random
import uuid
from .base_env import BaseEnv, Observation, Action
from models.log_classifier import classify_log
from tasks.registry import TASKS

class DevOpsEnv(BaseEnv):
    def __init__(self):
        self.episode_id = None
        self.task = None
        self.task_name = None
        self.history = []
        self.done = False
        self.steps = 0
        self.max_steps = 5

    def reset(self, task_name=None):
        self.episode_id = str(uuid.uuid4())
        self.task_name = task_name or random.choice(list(TASKS.keys()))
        self.task = TASKS[self.task_name]()
        self.history = []
        self.done = False
        self.steps = 0

        return Observation(
            logs=self.task["logs"],
            metrics=self.task["metrics"],
            history=[]
        )

    def step(self, action: Action):
        reward = -0.05
        self.steps += 1

        if action.action_type == "analyze_logs":
            pred = classify_log(self.task["logs"])
            if pred == self.task["label"]:
                reward += 0.4
            else:
                reward -= 0.1

        elif action.action_type == "take_action":
            if action.payload.get("fix") == self.task["solution"]:
                reward += 0.7
                self.done = True
            else:
                reward -= 0.3

        if self.history and self.history[-1]["action_type"] == action.action_type:
            reward -= 0.1

        self.history.append(action.dict())

        if self.steps >= self.max_steps:
            self.done = True

        return Observation(
            logs=self.task["logs"],
            metrics=self.task["metrics"],
            history=self.history
        ), reward, self.done, {}

    def state(self):
        return {
            "episode_id": self.episode_id,
            "step_count": self.steps,
            "task_name": self.task_name,
            "task": self.task,
            "history": self.history,
            "done": self.done
        }
