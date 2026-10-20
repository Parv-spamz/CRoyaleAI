# L68 RL layer on RoyaleSim -- plan (lead-authored, 2026-09-23)

Owner goal (verbatim, 2026-09-23): "set everything up so training can start on a whim". Earlier rulings this
session: RL is an ADDITIONAL layer on the IL framework, initialised from `icebow/data/pipeline/s1_icebow_v6aug_s1.pt`;
the KL leash's budget grows only as REAL-ENGINE held-out gains are confirmed; pro agreement is a collapse TRIPWIRE, not
a hard floor. Deliverable = built + smoke-tested + one-command launch. NOT a long training run.

Base design: `scratchpad/gauntlet/L67/e1_engine_rl_design.md` sections 2.3 and 3-4 (owner-reviewed, HANDOFF §AN), ported
from the socket engine to RoyaleSim. Differences from E1 are listed here; everything not listed follows E1.

## Measured facts this plan rests on (all (a), HANDOFF §BT)
- `pipeline/royale_env.py` RoyalePoolEnv = the PoolV1Env interface on RoyaleSim; `e1_eval.Match` / `run_batch` run the
  S1 policy + live rule on it; batched == sequential, identical play sequences 58/58.
- Loadable in RoyaleSim (Tornado landed): **train split 299 / 1,505, held-out 58 / 293**.
- Wall: ~3 s/match, one process, 29 in flight, under ~91% background CPU. Profile: obs noise model + from_engine ~37 s,
  per-row live_decide ~19.5 s, encode ~25 s, engine ~7 s (per 23 matches, profiled).
- RoyaleSim v6lat 60.3% vs v6aug 74.1% on the 58 (8-0 paired); v6lat equals its real-engine rate on the same 58.
- INIT pro agreement, v3 VAL clean (`python -m pipeline.eval_s1 icebow --data icebow/data/pipeline/s1_dataset.npz
  icebow/data/pipeline/s1_icebow_v6aug_s1.pt`, measured L68): **cell_half_top1 0.2073, card_top1 0.6394,
  gate_bal_acc 0.7636** (grid lattice, epoch 12). The tripwire thresholds below are relative to THESE (not to
  HANDOFF's 21.56, which is a different instrument).

## Differences from E1
1. **Pool revisits.** 299 train entries cannot be used once each. Each update samples E entries uniformly WITH
   replacement across updates (without replacement within one update), G rollouts each. Visit counts logged. Pool-fitting
   is caught by the held-out screen (below), not prevented.
2. **Held-out screen on RoyaleSim, cheap and frequent.** Every `screen_every` updates: greedy LIVE rule (tau 0.27, the
   deploy rule), live_view obs, all 58 playable held-out entries, eval seed k=0, paired against the init's same 58
   (computed once at startup and cached). Real-engine confirmation is a separate, manual gate (`pipeline/rl_gate.py`).
3. **Pro-agreement tripwire (owner ruling), not a floor.** Every `proagree_every` updates evaluate v3 VAL clean
   (`train_s1.evaluate`, `icebow/data/pipeline/s1_dataset.npz`, the eval_s1 instrument). STOP when BOTH hold:
   exact-cell < init - 1.0 pp AND the latest held-out screen paired delta <= 0 pp (agreement falling with no winrate
   gain = collapse signature). HARD STOP regardless: exact-cell < init - 3.0 pp or card < init - 3.0 pp or
   gate_bal_acc < init - 0.05 (collapse, not strategy change).
4. **KL budget is owner-controlled.** Adaptive beta as E1 3.4 (start 0.3, x2 / /2 around target kappa on KL_cell,
   clamp [0.03, 3]). kappa comes from config (`kl_target`, default 0.10) and is NEVER raised by the trainer; raising it is
   a manual step after `rl_gate.py` confirms a real-engine gain.
5. **Actors are processes, not engine slots.** A learner process + `n_actors` actor processes (torch.multiprocessing,
   spawn). Synchronous on-policy: learner broadcasts the policy state_dict, actors roll out their share of (entry, g)
   jobs with `run_batch`-style batching (`in_flight` matches per actor), return trajectories, learner updates. Model on
   `actor_device` (default cuda) in actors, `learner_device` (default cuda) in the learner.
6. **Exploit guards** = E1 section 4.2 items 1-3 as monitors + stop rules (outlived-the-script share, <=10-delivered win
   share, ghost refusal rate), init baselines measured at startup on the TRAIN rollouts of update 0's behaviour policy.

## Behaviour policy (E1 3.3, exact)
Per decision, from the same forward the live rule uses (heads over the current `live_view` tokens):
- allowed = in hand AND cost <= floored elixir (existing `allowed_slots`); stalled = existing `anti_stall(...)`.
- none allowed -> WAIT, no log-prob (environment decided).
- stalled -> play is FORCED: gate not sampled, lp_gate = 0 and excluded from the loss.
- else gate: p_b = sigmoid((z_gate - logit(tau)) / T); sample g ~ Bernoulli(p_b).
- if play: card c ~ softmax(z_card / T) over allowed slots; cell x ~ softmax(z_cell(enc, c) / T) over all 2,304 cells.
- log pi = lp_gate + g * (lp_card + lp_cell). T from config (default 0.5; smoke measures plays/min vs the greedy rule).
- As T -> 0 this reproduces the greedy live rule (tie-free rows); that is the unit test of the sampler.
- RNG: one numpy Generator per match seeded `crc32(f"{tag}:behaviour:{g}:{update}")`; live_view RNG seeded
  `crc32(f"{tag}:obs:{g}:{update}")`. Deterministic given (weights, update, entry, g).

## Learner (E1 3.2, 3.4-3.6)
- Reward +1/-1/0 terminal; group leave-one-out baseline over the G rollouts of an entry; |A| <= 2; no critic, no
  value loss, no entropy bonus. PPO-clip 0.2, `ppo_epochs` 2, minibatch 256 decisions, loss averaged per match then
  over the batch. Adam lr 1e-5, grad-norm clip 0.5. Model in eval() mode for BOTH rollout and update (dropout trap).
- Frozen ref = init, eval(), no grad. KL on the same tempered distributions: gate (Bernoulli, rows where the gate was
  sampled), card (allowed support, play rows), cell (2,304, play rows, sampled card).
- Assert on update 0, epoch 0, minibatch 0: |ratio - 1| < 1e-4 max, KL < 1e-6.
- Monitors, checkpoints (`<run>_u{NNNN}.pt` every `save_every`, `<run>_latest.pt` EVERY update via tmp+os.replace,
  crash save), non-finite guard, stop rules 1/2/6 of E1 3.6 plus 3/4 above. Checkpoint = train_s1 layout
  (`{"model","args","deck","epoch","val","n_params"}`) + `rl` dict, loadable by `engine_play.load_model`.
- Outputs: checkpoints under `icebow/data/bench/rl_royale/<run>/` (gitignored), logs `train_log.jsonl` + human log +
  config copy + pid under `scratchpad/gauntlet/L68/rl/<run>/`. Refuse to overwrite an existing run dir unless --resume.
  Resume from `<run>_latest.pt` (optimizer + beta + update counter + rng state saved in it).

## Launch
`research/ext/Royale/.venv/Scripts/python.exe -m pipeline.rl_royale --config pipeline/rl_royale.yaml --run <name>`
`... --smoke` = 2 updates with E=4, G=2, 1 actor, then exits 0 with a SMOKE PASS line (asserts above + checkpoint
round trip reproduces init pro agreement on 1,000 VAL rows exactly).
STOP file: `scratchpad/gauntlet/L68/rl/<run>/STOP` -> save latest, exit cleanly after the current update.

## Real-engine gate (separate, manual)
`pipeline/rl_gate.py`: scores two e1_eval runs (init vs candidate) paired by (tag, k): winrate each, paired delta,
entry-clustered bootstrap 95% CI (10,000 draws, seed 0), McNemar discordant counts, winrate over matches decided before
the ghost script ended, plays/min ratio, outlived-script share; prints PASS/FAIL vs E1 2.3 (i)(iii)(iv). Also prints the
two e1_eval command lines to produce the runs on the real engine (ports 38031/38032) or on RoyaleSim (--engine royale).
