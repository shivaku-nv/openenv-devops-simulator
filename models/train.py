"""Full training pipeline for the Phase 2 OpenEnv DevOps simulator.

This script provides a practical hackathon-ready training workflow with:
1. Supervised fine-tuning (SFT) on oracle action plans.
2. GRPO reinforcement learning using the local environment reward engine.
3. Local evaluation before and after training.

The design follows Hugging Face TRL's documented prompt-completion SFT flow and
custom-reward GRPO flow. The reward function executes the generated plan inside
the local environment and scores it with the same grader used by the API.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import torch

# Allow `python3 models/train.py` to resolve sibling packages from the repo root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.logs_dataset import generate_dataset
from env.base_env import Action
from env.devops_env import DevOpsEnv
from graders.registry import grade
from tasks.registry import TASKS


DEFAULT_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
DEFAULT_OUTPUT_DIR = Path("outputs/phase2_training")
SYSTEM_PROMPT = (
    "You are an OpenEnv DevOps incident-response agent. "
    "Return only valid JSON with keys `summary` and `actions`. "
    "Each item in `actions` must contain `action_type` and `payload`."
)


@dataclass
class TrainingExample:
    prompt: str
    completion: str
    task_name: str


def _import_training_stack() -> tuple[Any, ...]:
    try:
        from datasets import Dataset
        from peft import AutoPeftModelForCausalLM, LoraConfig
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, set_seed
        from trl import GRPOConfig, GRPOTrainer, SFTConfig, SFTTrainer
    except ImportError as exc:  # pragma: no cover - import guard for missing training deps
        raise SystemExit(
            "Training dependencies are missing. Install them with:\n"
            "  pip install -r requirements-training.txt\n"
            "or\n"
            "  pip install '.[training]'"
        ) from exc
    return Dataset, LoraConfig, AutoPeftModelForCausalLM, AutoModelForCausalLM, AutoTokenizer, pipeline, set_seed, GRPOConfig, GRPOTrainer, SFTConfig, SFTTrainer


def _use_bf16() -> bool:
    return bool(torch.cuda.is_available() and torch.cuda.is_bf16_supported())


def _metrics_to_text(metrics: dict[str, Any]) -> str:
    if not metrics:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(metrics.items()))


def _list_to_text(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- none"


def build_prompt(task_name: str, task: dict[str, Any]) -> str:
    lines = [
        SYSTEM_PROMPT,
        "",
        f"Task: {task_name}",
        f"Target label to resolve: {task.get('label', 'unknown')}",
        f"Logs:\n{task.get('logs', '')}",
        f"Metrics: {_metrics_to_text(task.get('metrics', {}))}",
        f"Alerts:\n{_list_to_text(task.get('alerts', []))}",
        f"Deployment history:\n{_list_to_text(task.get('deployment_history', []))}",
        f"Stakeholder updates:\n{_list_to_text(task.get('stakeholder_updates', []))}",
        f"Reward profile: {task.get('reward_profile', task_name)}",
        "",
        "Available actions:",
        "- analyze_logs",
        "- take_action",
        "- delegate_investigation",
        "- communicate_status",
        "- write_postmortem",
        "",
        "Return JSON in this exact shape:",
        '{"summary": "...", "actions": [{"action_type": "...", "payload": {...}}]}',
    ]
    return "\n".join(lines)


def oracle_plan(task_name: str, task: dict[str, Any]) -> dict[str, Any]:
    if task_name == "incident_command":
        return {
            "summary": (
                "Assign an investigation, communicate early, validate the memory-pressure hypothesis, "
                "restart the affected service, and record the learning artifact."
            ),
            "actions": [
                {
                    "action_type": "delegate_investigation",
                    "payload": {
                        "role": "sre_agent",
                        "objective": "Check memory saturation, restart loops, and the recent deployment timeline.",
                    },
                },
                {
                    "action_type": "communicate_status",
                    "payload": {
                        "audience": "stakeholders",
                        "summary": "Investigating checkout degradation, elevated latency, and failed payments after the latest deployment.",
                    },
                },
                {"action_type": "analyze_logs", "payload": {}},
                {"action_type": "take_action", "payload": {"fix": task["solution"]}},
                {
                    "action_type": "write_postmortem",
                    "payload": {
                        "summary": "checkout-api memory pressure after deployment caused user-facing checkout failures.",
                        "action_items": [
                            "Add memory regression gating to rollout checks",
                            "Alert on sustained OOM restart loops before customer impact",
                        ],
                    },
                },
            ],
        }

    return {
        "summary": f"Inspect the logs and apply the correct remediation for {task_name}.",
        "actions": [
            {"action_type": "analyze_logs", "payload": {}},
            {"action_type": "take_action", "payload": {"fix": task["solution"]}},
        ],
    }


def render_completion(plan: dict[str, Any]) -> str:
    return json.dumps(plan, ensure_ascii=True, separators=(",", ":"), indent=2)


def _base_task_snapshot(task_name: str) -> dict[str, Any]:
    task = TASKS[task_name]()
    snapshot = dict(task)
    snapshot.setdefault("reward_profile", task_name)
    return snapshot


def _label_to_task_name(label: str) -> str:
    mapping = {
        "disk_full": "easy",
        "memory_leak": "medium",
        "crash": "medium",
        "network_issue": "hard",
    }
    return mapping[label]


def build_training_examples(seed: int, repeats: int) -> list[TrainingExample]:
    rng = random.Random(seed)
    examples: list[TrainingExample] = []

    for _ in range(repeats):
        for task_name in ("easy", "medium", "hard", "incident_command"):
            task = _base_task_snapshot(task_name)
            plan = oracle_plan(task_name, task)
            examples.append(
                TrainingExample(
                    prompt=build_prompt(task_name, task),
                    completion=render_completion(plan),
                    task_name=task_name,
                )
            )

    synthetic_logs = generate_dataset(max(12, repeats * 8))
    for row in synthetic_logs:
        task_name = _label_to_task_name(row["label"])
        task = _base_task_snapshot(task_name)
        task["logs"] = row["text"]
        plan = oracle_plan(task_name, task)
        examples.append(
            TrainingExample(
                prompt=build_prompt(task_name, task),
                completion=render_completion(plan),
                task_name=task_name,
            )
        )

    rng.shuffle(examples)
    return examples


def build_rl_examples(seed: int, repeats: int) -> list[dict[str, str]]:
    rows = []
    for example in build_training_examples(seed=seed, repeats=repeats):
        rows.append({"prompt": example.prompt, "task_name": example.task_name})
    return rows


def write_dataset_artifacts(examples: list[TrainingExample], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = output_dir / "sft_dataset.jsonl"
    with dataset_path.open("w", encoding="utf-8") as handle:
        for example in examples:
            handle.write(json.dumps(asdict(example), ensure_ascii=True) + "\n")


def parse_plan_blob(text: str) -> dict[str, Any] | None:
    text = (text or "").strip()
    if not text:
        return None
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict) or "actions" not in payload:
        return None
    actions = payload.get("actions")
    if not isinstance(actions, list):
        return None
    return payload


def run_plan_in_environment(task_name: str, plan: dict[str, Any], max_actions: int = 6) -> dict[str, Any]:
    env = DevOpsEnv()
    env.reset(task_name)

    for step in plan.get("actions", [])[:max_actions]:
        action_type = step.get("action_type")
        payload = step.get("payload", {})
        if not action_type:
            continue
        env.step(Action(action_type=action_type, payload=payload))

    return grade(env.state())


def _format_reward(completions: list[str], **_: Any) -> list[float]:
    rewards = []
    for completion in completions:
        parsed = parse_plan_blob(completion)
        rewards.append(0.2 if parsed is not None else -0.5)
    return rewards


def _environment_reward(completions: list[str], task_name: list[str], **_: Any) -> list[float]:
    rewards = []
    for completion, current_task_name in zip(completions, task_name):
        parsed = parse_plan_blob(completion)
        if parsed is None:
            rewards.append(-1.0)
            continue
        try:
            result = run_plan_in_environment(current_task_name, parsed)
            rewards.append(float(result["score"]))
        except Exception:
            rewards.append(-1.0)
    return rewards


def _coverage_reward(completions: list[str], task_name: list[str], **_: Any) -> list[float]:
    rewards = []
    for completion, current_task_name in zip(completions, task_name):
        parsed = parse_plan_blob(completion)
        if parsed is None:
            rewards.append(0.0)
            continue
        action_types = [action.get("action_type") for action in parsed.get("actions", [])]
        if current_task_name == "incident_command":
            required = {"delegate_investigation", "communicate_status", "analyze_logs", "take_action", "write_postmortem"}
            rewards.append(0.2 if required.issubset(set(action_types)) else 0.0)
        else:
            required = {"analyze_logs", "take_action"}
            rewards.append(0.1 if required.issubset(set(action_types)) else 0.0)
    return rewards


def evaluate_policy(
    model_path: str,
    tokenizer_path: str | None,
    output_dir: Path,
    eval_repeats: int,
    seed: int,
) -> dict[str, Any]:
    _, _, AutoPeftModelForCausalLM, AutoModelForCausalLM, AutoTokenizer, pipeline, _, _, _, _, _ = _import_training_stack()
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path or model_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    try:
        model = AutoPeftModelForCausalLM.from_pretrained(model_path)
    except Exception:
        model = AutoModelForCausalLM.from_pretrained(model_path)

    device = 0 if getattr(model, "device", None) and "cuda" in str(model.device) else -1
    generator = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device=device,
    )

    rows = []
    for row in build_rl_examples(seed=seed, repeats=eval_repeats):
        generated = generator(
            row["prompt"],
            max_new_tokens=256,
            do_sample=False,
            temperature=0.0,
            return_full_text=False,
        )[0]["generated_text"]
        parsed = parse_plan_blob(generated)
        grading = run_plan_in_environment(row["task_name"], parsed or {"actions": []})
        rows.append(
            {
                "task_name": row["task_name"],
                "score": grading["score"],
                "components": grading["components"],
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / "eval_metrics.json"
    summary = {
        "model_path": model_path,
        "num_examples": len(rows),
        "mean_score": round(sum(row["score"] for row in rows) / max(len(rows), 1), 4),
        "results": rows,
    }
    metrics_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def run_sft(
    model_name_or_path: str,
    output_dir: Path,
    seed: int,
    sft_repeats: int,
    learning_rate: float,
    batch_size: int,
    gradient_accumulation_steps: int,
    num_epochs: float,
    max_length: int,
) -> Path:
    Dataset, LoraConfig, _, _, AutoTokenizer, _, set_seed, _, _, SFTConfig, SFTTrainer = _import_training_stack()
    set_seed(seed)

    examples = build_training_examples(seed=seed, repeats=sft_repeats)
    write_dataset_artifacts(examples, output_dir)
    dataset = Dataset.from_list([asdict(example) for example in examples])

    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )
    trainer = SFTTrainer(
        model=model_name_or_path,
        processing_class=tokenizer,
        train_dataset=dataset,
        peft_config=peft_config,
        args=SFTConfig(
            output_dir=str(output_dir / "sft"),
            learning_rate=learning_rate,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            num_train_epochs=num_epochs,
            logging_steps=5,
            save_strategy="epoch",
            report_to="none",
            bf16=_use_bf16(),
            completion_only_loss=True,
            max_length=max_length,
            packing=False,
            model_init_kwargs={
                "trust_remote_code": True,
                "torch_dtype": torch.bfloat16 if _use_bf16() else torch.float32,
            },
        ),
    )
    trainer.train()
    trainer.save_model(str(output_dir / "sft"))
    tokenizer.save_pretrained(str(output_dir / "sft"))
    return output_dir / "sft"


def run_grpo(
    model_name_or_path: str,
    output_dir: Path,
    seed: int,
    rl_repeats: int,
    learning_rate: float,
    batch_size: int,
    gradient_accumulation_steps: int,
    num_epochs: float,
    max_completion_length: int,
    num_generations: int,
) -> Path:
    Dataset, LoraConfig, _, _, AutoTokenizer, _, set_seed, GRPOConfig, GRPOTrainer, _, _ = _import_training_stack()
    set_seed(seed)

    rows = build_rl_examples(seed=seed, repeats=rl_repeats)
    dataset = Dataset.from_list(rows)

    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"

    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )
    trainer = GRPOTrainer(
        model=model_name_or_path,
        processing_class=tokenizer,
        train_dataset=dataset,
        reward_funcs=[_environment_reward, _format_reward, _coverage_reward],
        peft_config=peft_config,
        args=GRPOConfig(
            output_dir=str(output_dir / "grpo"),
            learning_rate=learning_rate,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            num_train_epochs=num_epochs,
            logging_steps=5,
            save_strategy="epoch",
            report_to="none",
            bf16=_use_bf16(),
            remove_unused_columns=False,
            max_completion_length=max_completion_length,
            num_generations=num_generations,
            beta=0.0,
        ),
    )
    trainer.train()
    trainer.save_model(str(output_dir / "grpo"))
    tokenizer.save_pretrained(str(output_dir / "grpo"))
    return output_dir / "grpo"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the Phase 2 OpenEnv DevOps policy with TRL.")
    parser.add_argument("--stage", choices=["sft", "grpo", "all", "eval"], default="all")
    parser.add_argument("--model-name-or-path", default=DEFAULT_MODEL)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--sft-repeats", type=int, default=16)
    parser.add_argument("--rl-repeats", type=int, default=16)
    parser.add_argument("--eval-repeats", type=int, default=4)
    parser.add_argument("--sft-learning-rate", type=float, default=2e-4)
    parser.add_argument("--grpo-learning-rate", type=float, default=5e-6)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=4)
    parser.add_argument("--sft-epochs", type=float, default=2.0)
    parser.add_argument("--grpo-epochs", type=float, default=1.0)
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--max-completion-length", type=int, default=256)
    parser.add_argument("--num-generations", type=int, default=4)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    current_model_path = args.model_name_or_path

    if args.stage in {"sft", "all"}:
        current_model_path = str(
            run_sft(
                model_name_or_path=current_model_path,
                output_dir=output_dir,
                seed=args.seed,
                sft_repeats=args.sft_repeats,
                learning_rate=args.sft_learning_rate,
                batch_size=args.batch_size,
                gradient_accumulation_steps=args.gradient_accumulation_steps,
                num_epochs=args.sft_epochs,
                max_length=args.max_length,
            )
        )

    if args.stage in {"grpo", "all"}:
        current_model_path = str(
            run_grpo(
                model_name_or_path=current_model_path,
                output_dir=output_dir,
                seed=args.seed,
                rl_repeats=args.rl_repeats,
                learning_rate=args.grpo_learning_rate,
                batch_size=args.batch_size,
                gradient_accumulation_steps=args.gradient_accumulation_steps,
                num_epochs=args.grpo_epochs,
                max_completion_length=args.max_completion_length,
                num_generations=args.num_generations,
            )
        )

    if args.stage in {"eval", "all"}:
        summary = evaluate_policy(
            model_path=current_model_path,
            tokenizer_path=current_model_path,
            output_dir=output_dir,
            eval_repeats=args.eval_repeats,
            seed=args.seed,
        )
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
