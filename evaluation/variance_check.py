import argparse
import json
import os
import sys
from pathlib import Path
from statistics import mean, pstdev

try:
    from evaluation.run_agent_eval import run_suite
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from run_agent_eval import run_suite


def main() -> None:
    parser = argparse.ArgumentParser(description="Score variance check for baseline/LLM agent runs.")
    parser.add_argument("--base-url", default="http://localhost:7860")
    parser.add_argument("--agent", choices=["baseline", "llm"], default="baseline")
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--model", default=os.getenv("LLM_MODEL", "nvidia/llama-3.1-nemotron-70b-instruct"))
    parser.add_argument("--api-base", default=os.getenv("LLM_API_BASE", "https://api.together.xyz/v1"))
    parser.add_argument("--api-key", default=os.getenv("LLM_API_KEY"))
    args = parser.parse_args()

    summary = run_suite(
        base_url=args.base_url,
        agent_type=args.agent,
        runs=args.runs,
        model=args.model,
        api_base=args.api_base,
        api_key=args.api_key,
    )

    run_scores = {}
    for row in summary["results"]:
        run_scores.setdefault(row["run_id"], []).append(row["score"])

    mean_per_run = [mean(scores) for _, scores in sorted(run_scores.items())]
    out = {
        "agent": args.agent,
        "runs": args.runs,
        "run_mean_scores": mean_per_run,
        "overall_mean_score": round(mean(mean_per_run), 4) if mean_per_run else 0.0,
        "score_std_dev": round(pstdev(mean_per_run), 6) if len(mean_per_run) > 1 else 0.0,
        "min_run_score": round(min(mean_per_run), 4) if mean_per_run else 0.0,
        "max_run_score": round(max(mean_per_run), 4) if mean_per_run else 0.0,
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
