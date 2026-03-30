
from pydantic import BaseModel
from pydantic import Field
from typing import Dict, Any, Tuple

class Observation(BaseModel):
    logs: str
    metrics: Dict[str, float]
    history: list

class Action(BaseModel):
    action_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)

class BaseEnv:
    def reset(self):
        raise NotImplementedError

    def step(self, action: Action) -> Tuple[Observation, float, bool, Dict]:
        raise NotImplementedError

    def state(self):
        raise NotImplementedError
