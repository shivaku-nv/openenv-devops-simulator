"""OpenEnv models for root environment package."""

from pydantic import BaseModel, Field
from pathlib import Path

try:
    from openenv.core.env_server.types import Action, Observation
except Exception:
    Action = BaseModel
    Observation = BaseModel


class DevopsAction(Action):
    action_type: str = Field(..., description="Action name, e.g. analyze_logs or take_action")
    payload: dict = Field(default_factory=dict, description="Optional action payload")


class DevopsObservation(Observation):
    logs: str = Field(default="", description="Current log text")
    metrics: dict = Field(default_factory=dict, description="Current environment metrics")
    history: list = Field(default_factory=list, description="Action history")


# Allow coexistence with existing `models/` package imports like `models.log_classifier`.
__path__ = [str(Path(__file__).resolve().parent / "models")]
