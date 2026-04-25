from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export a plot-ready training metrics JSON from TRL trainer_state.json files. "
            "Output schema: {steps, loss, reward}."
        )
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/phase2_training",
        help="Training output directory containing sft/ and grpo/ checkpoints.",
    )
    parser.add_argument(
        "--out",
        default="outputs/phase2_training/training_metrics.json",
        help="Destination JSON path for plot-ready metrics.",
    )
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _checkpoint_id(path: Path) -> int:
    name = path.parent.name
    if name.startswith("checkpoint-"):
        suffix = name.split("checkpoint-", 1)[1]
        if suffix.isdigit():
            return int(suffix)
    return -1


def _latest_state_file(stage_dir: Path) -> Path:
    checkpoint_states = list(stage_dir.glob("checkpoint-*/trainer_state.json"))
    if checkpoint_states:
        return sorted(checkpoint_states, key=_checkpoint_id)[-1]

    fallback = stage_dir / "trainer_state.json"
    if fallback.exists():
        return fallback

    raise FileNotFoundError(
        f"No trainer_state.json found in {stage_dir}. "
        "Run training first so checkpoint metadata exists."
    )


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _extract_loss_series(log_history: list[dict[str, Any]]) -> list[tuple[int, float]]:
    points: list[tuple[int, float]] = []
    for row in log_history:
        step = row.get("step")
        if not isinstance(step, int):
            continue

        value = None
        if _is_number(row.get("loss")):
            value = float(row["loss"])
        else:
            for key, candidate in row.items():
                if "loss" in str(key).lower() and _is_number(candidate):
                    value = float(candidate)
                    break

        if value is not None:
            points.append((step, value))

    points.sort(key=lambda item: item[0])
    return points


def _reward_value(row: dict[str, Any]) -> float | None:
    preferred_keys = [
        "reward",
        "rewards",
        "mean_reward",
        "train/reward",
        "reward/environment_reward",
        "objective/rlhf_reward",
    ]
    for key in preferred_keys:
        value = row.get(key)
        if _is_number(value):
            return float(value)

    for key, value in row.items():
        key_text = str(key).lower()
        if "reward" in key_text and _is_number(value):
            return float(value)

    return None


def _extract_reward_series(log_history: list[dict[str, Any]]) -> list[tuple[int, float]]:
    points: list[tuple[int, float]] = []
    for row in log_history:
        step = row.get("step")
        if not isinstance(step, int):
            continue
        value = _reward_value(row)
        if value is not None:
            points.append((step, value))

    points.sort(key=lambda item: item[0])
    return points


def _align_for_plot(loss_points: list[tuple[int, float]], reward_points: list[tuple[int, float]]) -> dict[str, list[float]]:
    if not loss_points:
        raise SystemExit("No loss points found in SFT trainer_state log history.")
    if not reward_points:
        raise SystemExit("No reward points found in GRPO trainer_state log history.")

    # Keep the most recent window and align by index so render_training_curves.py can plot both series.
    count = min(len(loss_points), len(reward_points))
    loss_window = loss_points[-count:]
    reward_window = reward_points[-count:]

    return {
        "steps": list(range(1, count + 1)),
        "loss": [round(value, 6) for _, value in loss_window],
        "reward": [round(value, 6) for _, value in reward_window],
    }


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)

    sft_state_file = _latest_state_file(output_dir / "sft")
    grpo_state_file = _latest_state_file(output_dir / "grpo")

    sft_state = _read_json(sft_state_file)
    grpo_state = _read_json(grpo_state_file)

    sft_history = sft_state.get("log_history", [])
    grpo_history = grpo_state.get("log_history", [])
    if not isinstance(sft_history, list) or not isinstance(grpo_history, list):
        raise SystemExit("trainer_state.json missing list log_history field.")

    payload = _align_for_plot(
        _extract_loss_series(sft_history),
        _extract_reward_series(grpo_history),
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {out_path}")
    print(f"Used SFT state: {sft_state_file}")
    print(f"Used GRPO state: {grpo_state_file}")


if __name__ == "__main__":
    main()
