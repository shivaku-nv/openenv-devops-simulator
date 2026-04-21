
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
        self.last_reward = 0.0
        self.reward_history = []
        self.last_info = {}
        self.phase = "idle"
        self.investigation_notes = []
        self.communication_log = []
        self.postmortem = None

    def reset(self, task_name=None):
        self.episode_id = str(uuid.uuid4())
        self.task_name = task_name or random.choice(list(TASKS.keys()))
        self.task = TASKS[self.task_name]()
        self.history = []
        self.done = False
        self.steps = 0
        self.last_reward = 0.0
        self.reward_history = []
        self.last_info = {}
        self.phase = "triage"
        self.investigation_notes = []
        self.communication_log = []
        self.postmortem = None

        return Observation(
            logs=self.task["logs"],
            metrics=self.task["metrics"],
            history=[]
        )

    def step(self, action: Action):
        reward = -0.05
        self.steps += 1
        info = {"step": self.steps, "action_type": action.action_type, "outcome": {}}

        if action.action_type == "analyze_logs":
            pred = classify_log(self.task["logs"])
            label_correct = pred == self.task["label"]
            info["outcome"] = {"predicted_label": pred, "label_correct": label_correct}
            self.phase = "investigation"
            if label_correct:
                reward += 0.4
            else:
                reward -= 0.1

        elif action.action_type == "take_action":
            chosen_fix = action.payload.get("fix")
            fix_correct = chosen_fix == self.task["solution"]
            info["outcome"] = {"fix": chosen_fix, "fix_correct": fix_correct}
            self.phase = "mitigation"
            if fix_correct:
                reward += 0.7
                self.done = True
                self.phase = "resolved"
            else:
                reward -= 0.3

        elif action.action_type == "delegate_investigation":
            role = action.payload.get("role", "unassigned")
            objective = action.payload.get("objective", "")
            note = {"role": role, "objective": objective}
            self.investigation_notes.append(note)
            info["outcome"] = {"delegated": True, "role": role}
            self.phase = "investigation"
            reward += 0.15 if objective else 0.05

        elif action.action_type == "communicate_status":
            audience = action.payload.get("audience", "stakeholders")
            summary = action.payload.get("summary", "").strip()
            entry = {"audience": audience, "summary": summary}
            self.communication_log.append(entry)
            info["outcome"] = {"communicated": bool(summary), "audience": audience}
            reward += 0.2 if summary else -0.05

        elif action.action_type == "write_postmortem":
            summary = action.payload.get("summary", "").strip()
            action_items = action.payload.get("action_items", [])
            wrote_postmortem = bool(summary and action_items)
            self.postmortem = {"summary": summary, "action_items": action_items}
            info["outcome"] = {
                "postmortem_written": wrote_postmortem,
                "action_item_count": len(action_items),
            }
            reward += 0.2 if wrote_postmortem else -0.05

        if self.history and self.history[-1]["action_type"] == action.action_type:
            reward -= 0.1

        action_record = action.model_dump()
        action_record["reward"] = reward
        action_record["done"] = self.done
        action_record["step"] = self.steps
        action_record["outcome"] = info["outcome"]
        self.history.append(action_record)
        self.last_reward = reward
        self.reward_history.append(reward)
        self.last_info = info

        if self.steps >= self.max_steps:
            self.done = True

        return Observation(
            logs=self.task["logs"],
            metrics=self.task["metrics"],
            history=self.history
        ), reward, self.done, info

    def state(self):
        return {
            "episode_id": self.episode_id,
            "step_count": self.steps,
            "task_name": self.task_name,
            "task": self.task,
            "history": self.history,
            "reward_history": self.reward_history,
            "last_reward": self.last_reward,
            "last_info": self.last_info,
            "max_steps": self.max_steps,
            "phase": self.phase,
            "alerts": self.task.get("alerts", []),
            "deployment_history": self.task.get("deployment_history", []),
            "stakeholder_updates": self.task.get("stakeholder_updates", []),
            "recommended_roles": self.task.get("recommended_roles", []),
            "investigation_notes": self.investigation_notes,
            "communication_log": self.communication_log,
            "postmortem": self.postmortem,
            "done": self.done
        }
