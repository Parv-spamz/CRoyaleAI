# CRoyaleAI
### Autonomous Neural Policy & Constrained Reinforcement Learning for Imperfect-Information RTS

<p align="left">
  <img src="https://img.shields.io/badge/Task-Imperfect--Information%20RTS-0A0E17?style=flat-square&labelColor=1E2638" alt="Task" />
  <img src="https://img.shields.io/badge/Architecture-Spatial%20Transformer-0A0E17?style=flat-square&labelColor=1E2638" alt="Architecture" />
  <img src="https://img.shields.io/badge/Optimization-PPO%20%2B%20KL%20Anchor-0A0E17?style=flat-square&labelColor=1E2638" alt="Optimization" />
  <img src="https://img.shields.io/badge/Observation-Zero--Privilege%20Contract-0A0E17?style=flat-square&labelColor=1E2638" alt="Observation" />
  <img src="https://img.shields.io/badge/Corpus-14%2C818%20Pro%20Matches-0A0E17?style=flat-square&labelColor=1E2638" alt="Corpus" />
</p>

---

## 1. Project Overview

**CRoyaleAI** is an autonomous decision system designed for real-time, continuous-spatial strategy environments under imperfect information, evaluated on Supercell's *Clash Royale*. 

Rather than relying on raw screen vision or intrusive game-memory inspection that leaks hidden state, the system operates under a mathematically verified **public-information constraint**. It balances real-time micro-placements and long-horizon elixir economics using a multi-head spatial transformer policy trained through large-scale replay distillation and regularized reinforcement learning.

```
              SYSTEM ARCHITECTURE OVERVIEW

[ Competitive Replay Corpus ]          [ Deterministic Native Engine ]
14,818 Verified Matches                 Byte-Exact Tick Re-Drive
│                                        │
└───────────────────┬────────────────────┘
│
▼
[ Public Observation Contract ]
• 32x18 Battlefield Lattice
• Projectile Ballistic Vectors
• Algorithmic Opponent Elixir
│
▼
[ GenModel: Spatial Transformer ]
├── Action Gate Head (Commit / Wait)
├── Card Pointer Network (Hand Selection)
├── Spatial Placement Head (32x18 Logits)
└── Value Estimation Head (Scalar Baseline)
│
┌───────────────────┴────────────────────┐
▼                                        ▼
[ Stage 1: Distillation ]                [ Stage 2: Regularized RL ]
3.5M+ Training Steps                     PPO + GAE + KL Leash in RoyaleSim
│                                        │
└───────────────────┬────────────────────┘
│
▼
[ Hardware-in-the-Loop ]
Read-Only Memory Telemetry
Kinematic Latency Extrapolation (+26 Ticks)
Sub-150ms Physical Tap Dispatch
```

---

## 2. Core Contributions

* **Strict Public-Information Contract:** Complete exclusion of opponent private state (hidden hand slots, next-card queue, exact elixir balance). Opponent elixir is tracked via a deterministic algorithmic event counter driven by unit production intervals, phase escalations, and visible card spends.
* **Deterministic Re-Drive Extraction:** Bypasses distribution drift by executing human match inputs directly inside a headless native Android engine, generating over 3,500,000 tick-synchronized state-action training records.
* **Invariant Policy Topology (`GenModel`):** A spatial transformer backbone that processes discrete cell occupancy, unit tokens, and hitpoint distributions into decoupled, hierarchical policy outputs:
  $$\mathbf{a}_t = \Big( a_{\text{gate}} \in \{0, 1\}, \;\; a_{\text{card}} \sim \text{Softmax}(\mathbf{z}_{\text{hand}}), \;\; a_{\text{spatial}} \sim \text{Softmax}(\mathbf{Z}_{32 \times 18}) \Big)$$
* **Constrained Policy Optimization:** Imitation checkpoints are fine-tuned inside a deterministic C++ simulation environment (`RoyaleSim`) using PPO with Generalized Advantage Estimation, constrained by a Kullback-Leibler divergence anchor ($\mathbb{D}_{\text{KL}}$) to preserve tactical human validity while improving win value.
* **Ballistic Latency Extrapolation:** Real-time compensation module running 26 ticks ahead to offset the 120–150ms capture-and-dispatch latency across physical Android emulator hardware.

---

## 3. Mathematical Formulation

### Constrained Reinforcement Learning Objective

The policy is optimized using a clipped surrogate gradient regularized by a Kullback-Leibler leash against the reference imitation policy $\pi_{\text{ref}}$:

$$\mathcal{L}^{\text{PPO}}(\theta) = \hat{\mathbb{E}}_t \left[ \min\left(r_t(\theta)\hat{A}_t, \, \text{clip}\left(r_t(\theta), 1-\epsilon, 1+\epsilon\right)\hat{A}_t\right) \right] - \beta \, \mathbb{D}_{\text{KL}}\left(\pi_\theta(\cdot \mid \mathbf{s}_t) \;\parallel\; \pi_{\text{ref}}(\cdot \mid \mathbf{s}_t)\right) - c_v \left(V_\theta(\mathbf{s}_t) - V_t^{\text{target}}\right)^2$$

Where:
* $r_t(\theta) = \frac{\pi_\theta(\mathbf{a}_t \mid \mathbf{s}_t)}{\pi_{\theta_{\text{old}}}(\mathbf{a}_t \mid \mathbf{s}_t)}$ denotes the probability ratio.
* $\hat{A}_t$ is the Generalized Advantage Estimator $\text{GAE}(\gamma, \lambda)$ computed over simulated match rollouts.
* $\beta$ is the adaptive penalty coefficient preventing policy degeneration away from realistic human distributions.

---

## 4. Empirical Evaluation & Checkpoint Matrix

Models are accepted solely through two isolated benchmarking protocols:
1. **Paired Ghost Screen:** Evaluated against fixed opponent action streams across 299 held-out competitive matches; reported as paired difference in win value (percentage points, pp) with 95% clustered bootstrap confidence intervals.
2. **Reactive Gauntlet:** Closed-loop matches against frozen baseline policies (`gen_v1` and `S1`) across 24 fixed seeds.

| Checkpoint | Architecture & Training Paradigm | Ghost Screen $\Delta$ (pp, 95% CI) | Gauntlet vs `gen_v1` | Gauntlet vs `S1` | Operational Status |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `S1` | Single-deck baseline (X-Bow/IceBow specific index) | *Reference Base* | — | 12 / 24 | Baseline Anchor |
| `gen_v1` | Generalist Transformer (Card token embeddings) | 0.0 pp | — | 20 / 24 | Generalist Reference |
| `gen_v3` | Added evolution tokens & opponent history | -2.3 [-6.4, +1.7] | 13 / 24 | 20 / 24 | Rejected (Null result) |
| `rseries_r0p` | Initial simulator PPO run | — | — | — | Deprecated (Engine drift) |
| **`rseries_r1_u0155`** | **PPO + GAE + Pre-trained Critic (155 updates)** | **+3.0 [-0.3, +6.4]** | **14 / 24** | **24 / 24** | **Primary RL Standard** |
| `gen_v3.1a` | Imitation learning (v4 Public Contract) | -3.3 [-7.0, +0.3] | 11 / 24 | 15 / 24 | Pure Imitation Baseline |
| **`gen_v3.1b`** | **`v3.1a` + 6-class critical tactical scenario weights** | **-2.8 [-6.4, +0.7]** | **15 / 24** | **16 / 24** | **Primary Imitation Standard** |

---

## 5. Analytical Audits & Resolved Failure Modes

```
[AUDIT 01: ARGMAX DECODING COLLAPSE]
Phenomenon : Human IceBow play commits Rocket at a 5.8% rate. Live evaluation of early checkpoints
dropped Rocket usage to 1.0% (72 / 7,024 plays) and missed 14 consecutive lethal towers.
Diagnostic : Network outputted high probability (P ≈ 0.24, AUC 0.84) during human Rocket windows,
but greedy argmax decoding favoured single-frame defensive options with marginal margins.
Resolution : Implemented multi-task loss re-weighting on terminal scenarios (v3.1b) and adaptive
action-commitment thresholds.

[AUDIT 02: SPATIAL PLACEMENT DEGENERACY]
Phenomenon : Human play distributes building placements across 24 discrete coordinate tiles to counter
divergent lane pushes; early spatial heads collapsed 93.8% of placements onto two tiles.
Diagnostic : Uniform temperature scaling increased coordinate variance but degraded replay agreement.
Resolution : Integrated relative coordinate attention tokens conditioned on target unit distances.

[AUDIT 03: PERCEPTION LATENCY & PROJECTILE HORIZONS]
Phenomenon : Capture-and-dispatch latency (120–150ms) caused defensive spells (e.g., The Log) to
deploy 1.3 seconds late against incoming Goblin Barrels (23.5% pre-emptive rate).
Diagnostic : Kinematic projection previously covered ground paths while omitting airborne ballistics.
Resolution : Extended extrapolation vectors to airborne projectiles and residual spell areas (+26 ticks),
raising pre-emptive deployment fidelity to 46.0%.
```

---

## 6. Repository Layout

```
CRoyaleAI/
├── pipeline/                      # Core deck-agnostic ML pipeline
│   ├── obs_contract.py            # Formal public observation contract specification
│   ├── public_observation.py      # Zero-privilege state tensor construction
│   ├── opp_elixir_count.py        # Algorithmic opponent elixir tracking
│   ├── model_gen.py               # GenModel spatial transformer topology
│   ├── dataset_gen.py             # Replay parser and tokenized dataset builder
│   ├── train_gen.py               # Distributed BF16 imitation policy trainer
│   ├── rl_royale.py               # PPO implementation with KL leash constraints
│   ├── live_gen.py                # Real-time inference controller (GenPilot)
│   └── extrapolate.py             # Kinematic projectile and unit look-ahead
├── research/                      # Verification environments and runtimes
│   ├── sandbox_tools/             # Native game engine deterministic re-drive harness
│   └── ext/                       # Pinned RoyaleSim simulator binaries
└── scratchpad/gauntlet/           # Benchmarking records and live runners
    ├── L68/live_reader/           # Production memory reader and emulator controller
    └── L71/                       # Diagnostic suites for Rocket and spatial distributions
```

---

## 7. Execution & Reproducibility

### Environment Setup
```bash
git clone https://github.com/Parv-spamz/CRoyaleAI.git
cd CRoyaleAI
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\activate
pip install -r icebow/requirements.txt
```

### 1. Verify Contracts and Model Assertions

```bash
python -m unittest pipeline.tests.test_obs_contract pipeline.tests.test_model_gen
```

### 2. Dataset Compilation & Imitation Training

```bash
# Generate lattice tokens from native engine replays
python -m pipeline.dataset_gen \
  --feature-version 4 \
  --corpus research/replays/pro_corpus/ \
  --out data/gen_dataset_v4.npz \
  --grid lattice

# Train spatial transformer with BF16 mixed precision
python -m pipeline.train_gen \
  --data data/gen_dataset_v4.npz \
  --epochs 6 \
  --amp bf16 \
  --grid lattice \
  --out-dir checkpoints/croyale_v1
```

### 3. Live Hardware-in-the-Loop Deployment

```bash
python scratchpad/gauntlet/L68/live_reader/live_play.py \
  --ladder \
  --matches 100 \
  --ckpt checkpoints/rseries_r1_u0155.pt \
  --tau 0.35 \
  --max-seconds 600
```

---

## 8. Citation

```bibtex
@software{croyaleai2026,
  author = {CRoyaleAI Contributors},
  title = {CRoyaleAI: Autonomous Neural Policy and Reinforcement Learning System for Real-Time Imperfect-Information Strategy},
  year = {2026},
  url = {https://github.com/Parv-spamz/CRoyaleAI}
}
```
