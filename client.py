"""OpenEnv client for root environment package."""

from typing import Dict

try:
    from openenv.core import EnvClient
    from openenv.core.client_types import StepResult
    from openenv.core.env_server.types import State
except Exception as e:  # pragma: no cover
    raise ImportError(
        "openenv-core is required for client usage. Install dependencies with `uv sync`."
    ) from e

try:
    from .models import DevopsAction, DevopsObservation
except Exception:
    from models import DevopsAction, DevopsObservation


class DevopsIncidentEnv(
    EnvClient[DevopsAction, DevopsObservation, State]
):
    def _step_payload(self, action: DevopsAction) -> Dict:
        return {
            "action_type": action.action_type,
            "payload": action.payload,
        }

    def _parse_result(self, payload: Dict) -> StepResult[DevopsObservation]:
        obs_data = payload.get("observation", {})
        observation = DevopsObservation(
            logs=obs_data.get("logs", ""),
            metrics=obs_data.get("metrics", {}),
            history=obs_data.get("history", []),
            done=payload.get("done", False),
            reward=payload.get("reward"),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
