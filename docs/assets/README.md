# Training Plot Assets

This directory stores committed training plot images used by README inline embeds.

Required files:
- training_loss_curve.png
- training_reward_curve.png

Generate from a real training run:

```bash
source ~/venv/bin/activate
python3 models/train.py --stage all --output-dir outputs/phase2_training
python3 scripts/export_training_metrics.py --output-dir outputs/phase2_training --out outputs/phase2_training/training_metrics.json
python3 scripts/render_training_curves.py --input outputs/phase2_training/training_metrics.json --output-dir docs/assets
```

Expected input JSON schema:

```json
{
  "steps": [1, 2, 3],
  "loss": [1.4, 1.1, 0.9],
  "reward": [0.2, 0.4, 0.7]
}
```

Commit the generated PNG files before final submission.
