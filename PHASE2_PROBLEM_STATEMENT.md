# Phase 2 Problem Statement

## Title
OpenEnv Incident Command: A Multi-Agent DevOps Response and Self-Improvement Simulator

## One-Line Pitch
We extend the current DevOps incident simulator into a long-horizon, multi-agent OpenEnv environment where specialized agents must coordinate to diagnose, mitigate, communicate, and learn from realistic production incidents.

## Problem Statement
Modern incident response is not a single classification problem. Real-world outages require multiple actors to reason over incomplete evidence, coordinate across roles, execute safe recovery actions, communicate with stakeholders, and improve future operating procedures after the incident is resolved.

This project proposes a realistic OpenEnv environment in which a team of AI agents handles production incidents that evolve over time. The environment exposes logs, metrics, deployment history, alerts, customer reports, and internal operational context. Agents must collaborate to:

1. identify the likely root cause,
2. plan a mitigation strategy,
3. execute a sequence of safe actions,
4. communicate status updates,
5. restore service quality, and
6. generate post-incident learning artifacts that improve future performance.

The goal is to simulate a professional workflow that reflects how SRE, infrastructure, and application teams actually operate during incidents, while preserving clear reward signals and measurable evaluation.

## Why This Fits OpenEnv
This design is intentionally aligned with the OpenEnv course structure and training philosophy:

- It follows the standard environment abstraction of `reset()`, `step()`, and `state()`, which the OpenEnv course describes as the core interaction loop for environments.
- It uses typed observations, actions, and state, matching the course recommendation to make the environment interface explicit and machine-checkable.
- It supports richer reward shaping rather than binary success alone, similar to the course guidance that multiple reward signals provide better training signal than win/loss outcomes only.
- It is compatible with future rollout-based RL fine-tuning, where agent actions can be evaluated over full trajectories and optimized with reward functions.

## Core Theme Coverage

### 1. Multi-Agent Interactions
The environment is explicitly designed around multiple specialized agents with partial perspectives and different action permissions.

### 2. Long-Horizon Planning and Instruction Following
Episodes require multi-step diagnosis, action sequencing, re-planning, and recovery rather than one-shot prediction.

### 3. World Modeling Across Professional and Personal Tasks
The world state includes technical signals and human coordination tasks such as stakeholder messaging, prioritization, and incident documentation.

### 4. Self-Improving Agent Systems
Each episode produces structured experience that can be converted into better prompts, memories, playbooks, or post-training data for later runs.

## Explicit Hackathon Alignment
This proposal is designed to cover multiple Round 2 themes simultaneously instead of matching only one theme loosely.

### Primary alignment
- `Theme #1: Multi-Agent Interactions`
- `Theme #2: Long-Horizon Planning & Instruction Following`
- `Theme #3.1: World Modeling for Professional Tasks`
- `Theme #4: Self-Improvement`

### Bonus-theme relevance
- `Fleet AI / Scalable Oversight`: the Incident Commander can act as an oversight agent that monitors and coordinates other specialist agents.
- `Halluminate / Multi-Actor Environments`: the environment requires one agent to manage and integrate multiple role-specific actors.
- `Scaler AI Labs / Enterprise Workflows`: incident response is a realistic enterprise workflow with business rules, stakeholder communication, and operational constraints.
- `Snorkel AI / Simulated Experts-in-the-Loop`: stakeholder updates, postmortems, and evolving operational preferences can be extended into expert-feedback loops.

## Environment
The environment simulates a cloud service stack under incident conditions. Each episode contains a hidden ground-truth cause and a partially observable operational state.

### Observable inputs
- application logs
- system logs
- service-level metrics such as latency, error rate, memory, CPU, and queue depth
- recent deployment history
- alert feed
- customer or support reports
- runbook snippets
- prior incident notes

### Hidden state
- true root cause
- dependency failures
- whether mitigation actions are safe or harmful in the current context
- evolving service condition over time

### Episode dynamics
The environment changes in response to agent actions. For example:
- scaling up may reduce latency but hide a memory leak,
- restarting a service may restore availability but not fix the bad deployment,
- premature rollback may recover one service while breaking another,
- delayed communication may increase stakeholder penalty even if recovery succeeds.

This makes the task more realistic than simple label prediction and encourages causal reasoning.

## Agent Capabilities
We propose three required agents and one optional agent.

### 1. Incident Commander Agent
Responsibilities:
- set the plan for the episode
- assign subtasks
- integrate evidence from other agents
- choose final mitigation or escalation actions
- decide when the incident is resolved

Actions:
- request investigation
- approve mitigation
- escalate severity
- request rollback
- declare incident status

### 2. SRE / Infrastructure Agent
Responsibilities:
- inspect infrastructure metrics and system health
- investigate autoscaling, networking, resource saturation, deployment stability
- recommend infrastructure-level actions

Actions:
- inspect metrics
- inspect deployment timeline
- scale service
- restart instance
- rollback deployment
- isolate failing node

### 3. Application / Logs Agent
Responsibilities:
- analyze application logs and crash traces
- infer likely application-level failures
- verify root-cause hypotheses
- recommend application-level fixes

Actions:
- inspect logs
- inspect trace summary
- identify suspect service
- recommend restart or config change
- confirm or reject hypotheses

### 4. Communications Agent (optional but high-value)
Responsibilities:
- summarize user impact
- draft stakeholder updates
- maintain an incident timeline
- produce a short postmortem summary

Actions:
- send status update
- summarize impact
- close communication loop

## Tasks
Each episode is a structured incident-response task with multiple stages.

### Stage 1: Triage
- classify urgency
- identify affected service area
- assign initial investigative subtasks

### Stage 2: Investigation
- gather evidence from logs, metrics, alerts, and deployment history
- form an initial root-cause hypothesis
- resolve conflicting evidence between agents

### Stage 3: Mitigation
- choose a recovery plan
- execute one or more actions in sequence
- monitor effect of actions on system state
- revise plan if the first intervention fails

### Stage 4: Coordination
- communicate status to stakeholders
- record what was tried and why
- avoid duplicated or contradictory actions

### Stage 5: Resolution and Learning
- confirm recovery
- identify true root cause
- generate a postmortem summary
- extract reusable playbook updates for future incidents

## Example Scenario Types
- memory leak causing intermittent latency spikes
- bad deployment causing elevated 5xx errors
- disk pressure leading to service crashes
- network partition affecting one region
- cascading dependency failure from a message queue backlog
- noisy alerts masking a genuine customer-impacting outage

## Observation and Action Design
To align with OpenEnv best practices, the environment should expose typed observations and actions.

### Observation should include
- current logs snapshot
- current metrics snapshot
- alert summary
- visible deployment history
- agent communication history
- prior actions taken
- remaining step budget
- current severity and estimated impact

### Action space should include
- investigate specific source
- propose hypothesis
- delegate subtask
- execute remediation
- request confirmation
- communicate update
- finalize root cause
- write postmortem summary

## Reward Model and Evaluation Logic
The reward system should combine outcome quality, process quality, and collaboration quality. Rather than using one hardcoded score, we propose a configurable reward engine that computes several sub-scores and combines them according to the scenario.

### Reward engine design
Each episode produces component-level scores such as:
- service recovery success
- root-cause accuracy
- action efficiency and step economy
- safety of remediation choices
- quality of multi-agent coordination
- communication completeness
- postmortem and learning artifact quality

The final reward is computed as a weighted combination of these components, but the weights are externalized and configurable rather than fixed in code.

### Example reward formula
```text
final_reward =
w_recovery * recovery_score +
w_root_cause * root_cause_score +
w_efficiency * efficiency_score +
w_safety * safety_score +
w_coordination * coordination_score +
w_communication * communication_score +
w_learning * learning_score
```

where each sub-score is normalized to a common range, such as `[0, 1]`.

### Why configurable rewards are better
- different incident types have different priorities
- high-severity outages should value safety and restoration more heavily
- exploratory training phases may reward investigation quality more strongly
- evaluation stays transparent because each component score is logged separately

### Scenario-aware reward profiles
Instead of a single universal weight vector, the environment can support multiple reward profiles.

Examples:
- `sev1_outage`: prioritize service restoration and safety
- `ambiguous_failure`: prioritize root-cause accuracy and investigation quality
- `stakeholder_sensitive_incident`: prioritize communication and coordination

This makes the evaluation system more realistic and prevents the reward function from feeling arbitrary.

### Example configuration
```yaml
reward_profiles:
  default:
    recovery: 0.25
    root_cause: 0.20
    efficiency: 0.15
    safety: 0.15
    coordination: 0.10
    communication: 0.05
    learning: 0.10

  sev1_outage:
    recovery: 0.35
    root_cause: 0.15
    efficiency: 0.10
    safety: 0.20
    coordination: 0.10
    communication: 0.05
    learning: 0.05
```

### Positive reward signals
- selecting a useful investigation step
- converging on the correct hypothesis
- improving service health metrics
- restoring the service within budget
- producing a correct and concise status update
- generating a useful postmortem with actionable prevention items

### Penalties
- repeated actions with no new information
- contradictory actions between agents
- harmful remediation
- incorrect root-cause declaration
- unnecessary escalation
- failure to communicate during a user-impacting incident
- recovering symptoms without resolving the cause

### Rule-based event rewards
In addition to the weighted final reward, the environment can emit event-level rewards during the episode. For example:
- positive reward when an investigation step reveals useful evidence
- negative reward for unsafe or contradictory actions
- step penalties for wasted time
- positive reward when service health measurably improves

This hybrid design creates better training signal for long-horizon optimization than only scoring the final outcome.

### Evaluation metrics
- incident resolution rate
- mean steps to recovery
- root-cause identification accuracy
- harmful action rate
- coordination efficiency
- postmortem usefulness score
- generalization across unseen incident templates

## Measurable Success Criteria
A strong agent system in this environment should:

- recover service in fewer steps than baseline heuristics,
- correctly identify root cause in the majority of episodes,
- avoid high-cost or unsafe actions,
- produce coherent cross-agent coordination traces,
- improve on repeated incident families over time.

## Judging Criteria Alignment

### 1. Environment Innovation
This environment is not just a log classifier. It combines partially observable technical signals, multi-agent coordination, dynamic state transitions, and organizational artifacts such as communications and postmortems. That makes it a more novel and behaviorally rich OpenEnv task.

### 2. Storytelling
The incident-command framing is easy to explain in a short live pitch:
- something is broken in production,
- several specialist agents investigate from different perspectives,
- the commander coordinates actions,
- the system recovers service,
- then the team learns from the incident.

This creates a strong demo narrative with visible state changes, coordination traces, and score breakdowns.

### 3. Showing Improvement in Rewards
The environment supports before/after comparisons through:
- baseline versus multi-agent runs,
- memory-free versus memory-enabled agents,
- shorter recovery paths after repeated incident families,
- component-wise reward improvements such as better communication, safer remediation, and more accurate root-cause identification.

### 4. Reward and Training Pipeline Setup
The reward model is explicit, modular, and externally configurable. The environment already supports trajectory-level scoring, making it suitable for later RL fine-tuning or policy optimization with OpenEnv-compatible training loops.

## Baselines
To support robust evaluation, we propose the following baselines:

### Baseline 1: Single-Agent Triage Heuristic
Equivalent to the current repo behavior: inspect logs, predict label, take one mapped action.

### Baseline 2: Single LLM Agent
A general model with no specialization and no persistent learning memory.

### Baseline 3: Multi-Agent Without Learning
Specialized agents are used, but no post-episode adaptation or memory update occurs.

### Target System: Multi-Agent With Self-Improvement
Specialized agents coordinate and update memory, prompts, or training data after each episode.

## Post-Training and Self-Improvement Strategy
The environment is designed not only for evaluation, but also for iterative improvement.

### 1. Trajectory Collection
Store full trajectories for each episode:
- observations
- agent messages
- actions
- rewards
- final outcome
- postmortem

### 2. Reflection
After each episode, run a lightweight analysis step:
- What evidence was ignored?
- Which action caused improvement?
- Where did coordination fail?
- Was the root cause found or only the symptom?

### 3. Persistent Incident Memory
Convert successful and failed episodes into structured memory:
- incident signature
- reliable indicators
- failed actions to avoid
- best recovery sequence
- communication templates

### 4. Prompt and Policy Refinement
Use the stored memory to improve future rollouts:
- better system prompts per role
- better delegation heuristics
- better action ordering
- better escalation thresholds

### 5. RL / Reward-Based Fine-Tuning
Because the environment exposes structured rewards over trajectories, it is compatible with later GRPO-style training. A rollout function can execute full multi-step episodes, score outcomes using the reward components above, and optimize agent policies over time.

## Minimum Requirement Readiness
The hackathon note also calls out a few explicit deliverables beyond the environment design itself.

### Already covered by this repo
- OpenEnv-compatible environment structure
- environment API with `reset`, `step`, and `state`
- deterministic baseline and evaluation scripts
- clear reward logic and score breakdown
- a Phase 2 scenario with measurable outcomes

### Still required for final packaging
- a short reward-improvement demo, such as before/after metrics or reward curves
- a mini-blog or short video walkthrough of the submission

The training-script requirement is already covered in this repo via `models/train.py`, which implements supervised bootstrap plus GRPO fine-tuning against the local reward engine. The remaining items are presentation artifacts rather than missing design pieces.

## Why This Is Realistic
Real incidents are:
- partially observable,
- time-sensitive,
- collaborative,
- safety-constrained,
- and shaped by both technical and human decisions.

This environment captures those characteristics while remaining evaluable, reproducible, and modular.

## Why This Is Different From a Simple Log Classifier
The current simulator already proves the usefulness of log-driven incident diagnosis. This proposal upgrades it from:

- single-agent,
- one-shot classification,
- one remediation action,
- binary grading

to:

- multi-agent collaboration,
- multi-turn diagnosis,
- dynamic world state,
- weighted rewards,
- and explicit self-improvement.

That makes it a stronger OpenEnv environment for training and evaluating agentic behavior.

## Proposed Implementation Path From Current Repo
This proposal is intentionally incremental so it can be built from the existing codebase.

### Phase 2 environment upgrades
- expand tasks from static labels to evolving incident scenarios
- add agent roles and role-specific action permissions
- extend environment state with alerts, deployment events, and communication history
- upgrade the grader from binary success to weighted trajectory scoring
- add post-episode artifact generation such as postmortems and playbook memory

### Reuse from current repo
- current `reset`, `step`, `state` environment loop
- log ingestion paths
- task registry structure
- baseline evaluation scripts
- reward and grading infrastructure

## Submission-Ready Short Version
We propose a multi-agent DevOps incident command simulator built on OpenEnv. In this environment, specialized agents such as an Incident Commander, SRE Agent, and Application Logs Agent must collaboratively respond to realistic production failures using logs, metrics, alerts, deployment history, and stakeholder context. The task requires long-horizon planning, safe action selection, delegation, communication, and post-incident learning. Evaluation rewards not only service recovery, but also root-cause accuracy, action safety, collaboration quality, efficiency, and the usefulness of generated postmortem artifacts. The system improves over time by converting prior incident trajectories into structured operational memory and better policies, making it a strong fit for OpenEnv’s focus on realistic, measurable agent environments.

## Judge-Facing Differentiators
- grounded in a real professional workflow with measurable outcomes
- supports multiple interacting agents rather than isolated prompts
- evaluates both process and outcome quality
- compatible with OpenEnv deployment and future RL training loops
- naturally extends an already working simulator rather than being a purely conceptual design
- fits several official Round 2 themes at once, including bonus-theme directions

## References
- OpenEnv course repository: https://github.com/raun/openenv-course/tree/main
- Module 4, "Building Your Own Environment": https://github.com/raun/openenv-course/blob/main/module-4/README.md
- Module 5, "Training with OpenEnv + TRL": https://github.com/raun/openenv-course/blob/main/module-5/README.md
