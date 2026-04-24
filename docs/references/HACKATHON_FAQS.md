# Hackathon FAQ Notes

Converted and condensed from `Hackathon FAQs (participants).docx`.

## Core Ideas

### Reinforcement Learning for LLMs

The FAQ frames RL for LLMs as a loop:

1. the model generates an answer, plan, or action sequence
2. a verifier or environment evaluates it
3. the resulting reward shifts probability toward better behavior over time

The repo matches that setup directly: the DevOps simulator provides environment steps, and the reward engine scores full trajectories.

### Why Rewards Matter

The copied FAQ emphasizes that rewards are the task specification. If rewards are easy to game, optimization will exploit the loophole. That aligns well with this repo’s weighted reward engine, which scores:

- recovery
- root-cause accuracy
- efficiency
- safety
- coordination
- communication
- learning

### Rewards Engineering

The FAQ’s practical advice is to reward outcomes first, then add process constraints only where they matter. This project follows that pattern:

- outcome quality is still dominant
- process-level dimensions are explicit
- the weights live in `reward_profiles.json`

### RLVR and Verifiable Environments

One of the strongest themes in the FAQ is that verifier-driven rewards are more trustworthy than vague scalar judgments when success can be checked directly. This repo uses environment-native grading rather than a standalone learned reward model.

## Repo-Relevant Takeaways

- OpenEnv is the right abstraction for standardizing `reset`, `step`, `state`, rewards, and deployment
- TRL and Unsloth fit naturally on top of this kind of environment
- reward hacking is a real risk, so transparent component scores matter
- process supervision is useful when intermediate steps like communication and postmortems are important to the task

## Practical Mapping Into This Repo

- `openenv.yaml` defines the environment interface
- `server.app:app` is the runtime entrypoint
- `utils/reward_engine.py` contains the reward decomposition
- `evaluation/generate_reward_evidence.py` now provides a clean before/after reward artifact
- `docs/demo/MINI_BLOG.md` packages the presentation layer required by the hackathon
