from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render training loss and reward curves from a JSON metrics trace."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to a JSON file with keys `steps`, `loss`, and `reward`.",
    )
    parser.add_argument(
        "--output-dir",
        default="docs/assets",
        help="Directory where PNG images will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    steps = payload["steps"]
    loss = payload["loss"]
    reward = payload["reward"]

    if not (len(steps) == len(loss) == len(reward)):
        raise SystemExit("`steps`, `loss`, and `reward` must have the same length.")

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "matplotlib is required to render training curves. "
            "Install it in the active environment before running this script."
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)

    plt.style.use("default")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(steps, loss, color="#b94e48", linewidth=2.5)
    ax.set_title("Training Loss Curve")
    ax.set_xlabel("Step")
    ax.set_ylabel("Loss")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "training_loss_curve.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(steps, reward, color="#1f6f5f", linewidth=2.5)
    ax.set_title("Training Reward Curve")
    ax.set_xlabel("Step")
    ax.set_ylabel("Reward")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "training_reward_curve.png", dpi=160)
    plt.close(fig)

    print(f"Wrote {output_dir / 'training_loss_curve.png'}")
    print(f"Wrote {output_dir / 'training_reward_curve.png'}")


if __name__ == "__main__":
    main()
