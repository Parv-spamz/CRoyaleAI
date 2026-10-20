# CRoyaleAI: Autonomous Neural Policy and Reinforcement Learning System for Clash Royale

A research platform and autonomous agent system for real-time imperfect-information strategy games, applied to Supercell's Clash Royale. The architecture combines large-scale imitation learning from verified competitive replays with regularized reinforcement learning in a deterministic simulation environment, operating strictly under public-information constraints without private state leakage.

---

## Abstract

Real-time strategy games with partial observability and continuous spatial action spaces present substantial challenges for autonomous decision systems. CRoyaleAI implements an end-to-end policy network that selects card plays, timing, and coordinate placements in real time. Rather than relying on approximate image-based perception or privileged memory inspection, the system formulates an observation contract strictly limited to publicly observable game dynamics: visible unit positions, health fractions, flight trajectories of active projectiles, residual durations of spell area effects, and an algorithmic public counter for opponent elixir estimation.

Training leverages a two-stage methodology:
1. **Empirical Policy Distillation (Imitation Learning):** Over 14,000 professional-tier replay recordings are deterministically re-driven tick-by-tick through the native game engine inside a headless environment, extracting synchronized spatial lattice tokens and generating millions of causal training rows.
2. **Constrained Policy Optimization (Reinforcement Learning):** Imitation policies are fine-tuned via Proximal Policy Optimization (PPO) with Generalized Advantage Estimation (GAE) inside RoyaleSim, bounded by a Kullback-Leibler (KL) divergence penalty to retain human tactical realism while optimizing win value.

The resulting policy executes live on physical hardware via an Android emulator runtime with automated state-machine navigation and sub-second decision latency.

---

## System Architecture

```
[ Competitive Human Play ]
       |
       | 14,818 recordings (RoyaleAPI / HuggingFace)
       v
[ Deterministic Re-Drive Engine ]
       | Native Android sandbox execution
       | Tick-synchronized public state extraction (units, projectiles, spells)
       v
[ Public Observation Contract ]
       | Explicit causal masking
       | In-flight projectile extrapolation & public elixir counter
       v
[ Generalized Transformer Policy (GenModel) ]
       |
       +---> [ Action Gate Head ]: binary play / wait decision
       +---> [ Card Selection Head ]: pointer network over hand slots
       +---> [ Spatial Placement Head ]: coordinate lattice logits (32x18 grid)
       +---> [ Value Estimation Head ]: expected match outcome
       |
       v
[ Policy Optimization & Acceptance ]
       | Reinforcement Learning (PPO + KL anchor in RoyaleSim)
       | Paired ghost screen acceptance (299 held-out pro games)
       | Reactive gauntlet validation (vs frozen benchmarks)
       v
[ Real-Time Live Execution ]
       | Read-only memory telemetry (MuMu emulator)
       | Extrapolation engine (latency compensation)
       | Hardware tap dispatch (hand selection + grid coordinates)
       | Autonomous ladder state machine & telemetry logging
```

---

## Core Methodological Principles

### 1. The Strict Public-Information Constraint

A central design mandate is that the model must never inspect private opponent data. Commercial game memory readers frequently leak hidden opponent variables (hand order, upcoming cards, exact elixir pools). Relying on private data produces artificial strategies that fail in competitive human parity and risk game integrity.

In CRoyaleAI:
- **Zero Opponent Hand Telemetry:** The opponent's active hand and next-card queues are completely excluded from both training datasets and live inference tensors.
- **Algorithmic Elixir Accounting:** Opponent elixir is estimated solely via an empirical event counter (`pipeline/opp_elixir_count.py`). The counter tracks regeneration curves, double/triple elixir phases, and subtracts deterministic card costs as deployments become visible on the board.
- **Observable World State:** The version-4 observation tensor (`pipeline/public_observation.py`) encodes only verified visible entities: ground and air units, structural hitpoints, in-flight projectile trajectories with computed time-to-impact, spell area-of-effect boundaries with remaining lifetimes, and the agent's own confirmed abilities.

### 2. High-Fidelity Engine Re-Drive

Handcrafted game simulators frequently suffer from subtle dynamic discrepancies (pathfinding quirks, collision physics, mass displacement, attack animation clipping) that degrade transferred policies.

To eliminate distribution shift between training data and true game dynamics, the pipeline re-drives human replay inputs through the real native engine (`research/sandbox_tools/`). Because the core game simulation is deterministic, replaying identical input logs yields byte-exact intermediate world states. High-throughput reinforcement learning and paired acceptance testing are then offloaded to RoyaleSim, anchored against empirical real-engine benchmarks.

### 3. Policy Network Topology (`pipeline/model_gen.py`)

The generalist policy (`GenModel`) processes board states through a hybrid architecture:
- **Spatial Transformer Backbone:** Converts discrete cell occupancy, unit tokens, and hitpoint distributions across the battlefield lattice into latent embeddings.
- **Decoupled Hierarchical Heads:**
  - *Gate Head:* Formulates the decision to commit an action or conserve elixir.
  - *Card Selection Pointer:* Attends across available card identities in hand, invariant to slot ordering.
  - *Conditional Spatial Placement Head:* Computes a spatial logit distribution conditioned on the selected card's operational range and role (e.g., troop vs. direct damage spell).
  - *Value Head:* Predicts scalar game outcome for variance reduction in RL updates.

---

## Model Evolution and Checkpoints

| Model Identifier | Architecture and Training Formulation | Simulator Acceptance Status |
| :--- | :--- | :--- |
| `S1` | Single-deck baseline (X-Bow / IceBow specific). Uses fixed deck-slot indexing. | Benchmark reference policy |
| `gen_v1` | First generalist transformer policy. Uses card identity embeddings; supports arbitrary decks. | Baseline generalist anchor |
| `gen_v2`, `gen_v3` | Incorporates refined wait-label logic, evolution tags, and opponent play history. | No statistically significant gain over `gen_v1` |
| `league1c_u0075` | Early PPO iteration in simulator; demonstrated initial league progression. | Superseded |
| `rseries_r0p` | Re-anchored PPO run; failed to transfer improvements to updated engine revisions. | Deprecated |
| **`rseries_r1_u0155`** | PPO from `gen_v1` with Generalized Advantage Estimation (GAE), per-tick discounting, and critic pre-training (155 updates). | **Primary active reinforcement learning checkpoint** |
| `rseries_r1u`, `r2` | Experimental reward shaping ablation (undiscounted returns, crown weighting, terminal rewards). | Neutral to negative impact on win rate |
| `gen_v3.1a` | Imitation learning on full version-4 public observation contract (3,517,863 real-engine rows). | Statistically level with `gen_v1` |
| **`gen_v3.1b`** | `gen_v3.1a` augmented with 6-class loss re-weighting on critical tactical scenarios (tower Rocket conversions, Rocket-Tornado combinations, defensive X-Bow placements). | **Primary active imitation checkpoint** |

---

## Empirical Evaluation

Candidate models are verified through two isolated empirical instruments. Subjective evaluations and unseeded match samples are excluded from acceptance criteria.

### 1. Paired Ghost Screen
The evaluation policy executes against recorded opponent actions across 299 pinned, held-out competitive replays inside RoyaleSim. Performance is measured as paired difference in win value (percentage points, pp) with 95% clustered bootstrap confidence intervals.

### 2. Reactive Gauntlet
The policy competes in closed-loop play against frozen reference opponents (`gen_v1` and `S1`) across 24 fixed seeds.

| Evaluation Pair | Ghost Screen Delta (Paired pp, 95% CI) | Reactive Win Rate (vs `gen_v1`, vs `S1`) | Empirical Conclusion |
| :--- | :--- | :--- | :--- |
| `gen_v1` (Re-baseline) | Reference (0.0 pp) | 12 / 24, 20 / 24 | Baseline established |
| `gen_v3` vs `gen_v1` | -2.3 [-6.4, +1.7] | 13 / 24, 20 / 24 | Null result; feature additions yielded no advantage |
| **`rseries_r1_u0155` vs `gen_v1`** | **+3.0 [-0.3, +6.4]** | **14 / 24, 24 / 24** | Statistically significant performance gain |
| `rseries_r1` (u0080) vs `r0p` | +5.0 [+1.7, +8.7] | -- | Replaced initial RL series |
| `rseries_r1` (u0155) vs `r0p` | +4.7 [+1.3, +8.4] | -- | Sustained advantage confirmed |
| `gen_v3.1a` vs `rseries_r1_u0155` | -3.3 [-7.0, +0.3] | 11 / 24, 15 / 24 | Pure imitation lags behind RL policy |
| `gen_v3.1b` vs `rseries_r1_u0155` | -2.8 [-6.4, +0.7] | 15 / 24, 16 / 24 | Context-weighted imitation narrows simulator gap |
| `gen_v3.1b` vs `gen_v3.1a` | +0.5 [-3.0, +3.8] | -- | Context weighting improves target coordination |

---

## Analytical Case Studies & Identified Failure Modes

Rigorous logging and post-hoc audits of hundreds of unattended live matches revealed critical edge cases in policy execution:

### 1. Rocket Conversion Frequency & Argmax Distribution Collapse
In professional human play with the IceBow archetype, Rocket accounts for approximately 5.8% of all card commitments, frequently deployed to punish high-cost backline units or execute low-health towers.
- **Empirical Deficit:** Live audits of `league1c_u0075` over 201 matches revealed Rocket usage dropped to 1.0% (72 plays out of 7,024). In 14 clear opportunities where an enemy tower fell below lethal threshold (497 HP), the model completed zero conversions.
- **Root Cause Diagnosis:** Diagnostic evaluation (`scratchpad/gauntlet/L71/rocket_diag/`) confirmed the network outputs appropriate class probabilities ($P \approx 0.24$) at human Rocket moments (AUC 0.84). However, argmax decoding consistently favoured defensive alternatives with slightly higher single-frame certainty. Furthermore, spatial argmax distributions for high-damage spells exhibited mode collapse, selecting tower-centered cells in only 28.5% of argmax outputs.

### 2. Spatial Placement Collapse (X-Bow Deployment)
Competitive players utilize approximately 24 discrete coordinate cells for X-Bow placements, adjusting 1 to 2 tiles laterally or vertically to account for opponent tank paths, Earthquake ranges, and Royal Giant lanes.
- The learned continuous spatial head collapsed 93% to 94% of all deployment density onto two canonical lane cells. While sampling across higher temperatures widened placement variance, it reduced overall replay agreement metrics, indicating that fine-grained tactical adjustments require explicit relational features rather than uniform temperature scaling.

### 3. Perception Latency & Projectile Extrapolation Look-Ahead
The live loop incurs a communication and capture delay of approximately 120 ms to 150 ms between physical memory read and emulator tap execution.
- While the extrapolation module (`pipeline/extrapolate.py`, 26 ticks) projected ground troop positions into the future, active spells and air projectiles (e.g., Goblin Barrel) were initially unextrapolated. Consequently, the agent perceived incoming barrels approximately 1.3 seconds behind their physical impact trajectory, resulting in delayed Log timings.
- Extending extrapolation vectors to airborne projectiles and effect durations improved pre-emptive Log timing from 23.5% (`gen_v3.1a`) to 46.0% (`gen_v3.1b`).

---

## Repository Structure

```
CRoyaleAI/
|-- pipeline/                  # Core deck-agnostic research pipeline
|   |-- obs_contract.py        # Formal observation specification and validation
|   |-- public_observation.py  # Zero-privilege state tensor construction
|   |-- opp_elixir_count.py    # Algorithmic opponent elixir tracking
|   |-- model_gen.py           # GenModel transformer architecture
|   |-- dataset_gen.py         # Replay extraction and training dataset builder
|   |-- train_gen.py           # Multi-GPU imitation policy trainer
|   |-- rl_royale.py           # PPO implementation with KL leash constraints
|   |-- royale_env.py          # Gym interface to RoyaleSim environment
|   |-- live_gen.py            # Real-time inference controller (GenPilot)
|   |-- extrapolate.py         # Latency compensation and entity projection
|   |-- decks/                 # Deck composition definitions and card mappings
|   `-- tests/                 # Unit test suite for contracts, models, and math
|-- icebow/                    # X-Bow specialized deployment environment
|   |-- run.py                 # CLI entry point for deck operations
|   |-- src/clashrl/           # Module implementation
|   `-- tools/                 # Deck-specific telemetry and audit utilities
|-- hogeq/                     # Hog Rider / Earthquake secondary deck pipeline
|-- research/                  # Experimental ledgers, sandbox tools, and runtimes
|   |-- sandbox_tools/         # Native game engine re-drive harness
|   `-- ext/                   # External engine runtime configurations
|-- scratchpad/gauntlet/       # Sequential experimental records (L64 through L72)
|   |-- L68/live_reader/       # Production memory reader, navigation, and live loop
|   `-- L71/                   # Porting and verification benchmarks
`-- tools/                     # Corpus ingestion, scraping, and verification scripts
```

---

## Setup and Verification

### Prerequisites
- Python 3.10+ (64-bit)
- PyTorch 2.1+ with CUDA acceleration for model training
- Android Emulator (MuMu Player 12 recommended) configured for ADB access
- Pinned RoyaleSim runtime for RL and acceptance workflows

### 1. Environment Installation

```powershell
# Initialize core virtual environment
python -m venv icebow\.venv
.\icebow\.venv\Scripts\python.exe -m pip install -r icebow\requirements.txt
```

### 2. Running Contract and Unit Tests

Verify observation contracts, spatial lattice conversions, and model forward-pass integrity:

```powershell
.\icebow\.venv\Scripts\python.exe -m unittest pipeline.tests.test_obs_contract pipeline.tests.test_model_gen
```

### 3. Dataset Generation and Model Training

Extract causal training instances from re-driven engine replays and train the generalist policy:

```powershell
# Compile feature version 4 public observations
.\icebow\.venv\Scripts\python.exe -m pipeline.dataset_gen `
  --feature-version 4 `
  --corpus <path_to_redrive_corpus> `
  --out data\gen_dataset_v4.npz `
  --grid lattice

# Train transformer policy with BF16 mixed precision
.\icebow\.venv\Scripts\python.exe -m pipeline.train_gen `
  --data data\gen_dataset_v4.npz `
  --seed 42 `
  --epochs 6 `
  --grid lattice `
  --feature-version 4 `
  --amp bf16 `
  --out-dir checkpoints\croyale_v1
```

### 4. Running Live Inference

Execute unattended live play with automatic match navigation on an active emulator instance:

```powershell
.\icebow\.venv\Scripts\python.exe scratchpad\gauntlet\L68\live_reader\live_play.py `
  --ladder `
  --matches 100 `
  --ckpt checkpoints\rseries_r1_u0155.pt `
  --tau 0.35 `
  --max-seconds 600
```

---

## Technical Audit and Reproducibility

- **Code Integrity:** All decision-making components operate through pure mathematical tensors and documented observation schemas.
- **Simulation Parity:** Runtime versions are pinned in `research/ext/` with matching checksums; acceptance scores are never compared across mismatched simulator revisions.
- **Disclaimer:** This software is an independent machine learning research initiative. It is not affiliated with, endorsed by, or sponsored by Supercell.
