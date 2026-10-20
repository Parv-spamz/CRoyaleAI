# Reward-shaping plan for icebow RL (2026-09-30, DRAFT for owner approval)

Owner's rule: "We can bring shaped rewards back but we can't blindly introduce terms anymore; we need to carefully
plan out and implement the reward system to prevent collapses."

## 0. What history says (the failures we must not repeat)

| # | What broke | Evidence | Lesson |
|---|---|---|---|
| 1 | A **free-standing** penalty (`threat_miss_idle`) charged every step | bar at 0-2 for 91% of steps; hold-to-6 scored 8.5x worse than spend-immediately (HANDOFF §4.1) | Never add terms that are not potential differences; test scripted behaviours BEFORE training |
| 2 | Play gate collapsed with no gate prior | engA 36 -> 0.12 plays/match, gate max 0.23 < tau (§5cs.46) | Keep the gate prior; watch an UNCONDITIONAL play rate |
| 3 | Placement collapse under PPO | row 13 from 41% to 84.5% of plays, 28/432 cells (§4.3) | Per-card cell-entropy alarms, not just a global one |
| 4 | Graded placement reward narrowed cells | Knight 1 distinct cell; watchdog "cell head collapsed"; no control run (archive :12611) | Every shaping arm needs a matched no-shaping control |
| 5 | KL leash froze learning | pro agreement 15.44 -> 16.33 -> 15.64 (§5cs.44-51) | The leash stops collapse AND learning; its tightness is its own experiment |
| 6 | Conditional-metric blindness | top-1 16.73 while playing 0.12 times per match (:1921) | Every conditional metric needs an unconditional companion |
| 7 | Friend's elixir potential as loud as winning | 0.80 vs terminal 0.80 per episode (RoyaleLearn rewards.py:446); his run then played Hog 95%, Cannon 0.6%, Log 1.0% (hog26-9 notes) | Budget each term's magnitude; spells and buildings need fair pricing or none |

## 1. The key structural fact about OUR learner

`pipeline/rl_royale.py` gives every decision in a match the SAME advantage: the match's win/loss, minus a
leave-one-out group baseline (`loo_advantage`, :460-475). There is no per-step return and no critic.

Potential-based shaping adds `F_t = gamma * Phi(s_{t+1}) - Phi(s_t)` per step with `Phi(terminal) = 0`. Summed over a
match this **telescopes to a constant** (`-Phi(s_0)`, identical for every match of the same start). So **added to our
current per-match advantage, shaping changes nothing at all.** Shaping only helps through per-decision credit: the
return from each decision onward. Hence two separate changes, in order.

## 2. The plan: one change per experiment, each gated

**R0 (running now): league1c.** league1b plus the learner always on icebow (opponent decks unchanged). No reward change.
It tells us whether concentrating the signal on one deck matters. It is the baseline for everything below.

**R1: per-decision credit, win/loss only.** Replace the per-match advantage with per-decision returns-to-go plus a value
baseline (GAE; the model already has a value head, currently trained only as an auxiliary crown-difference predictor).
Reward still win/loss only. This is what makes shaping possible, and it is a change on its own, so it gets its own
run and its own verdict against R0. Risk: a poor critic makes noisy advantages. The value head's outcome accuracy is
0.70 at init. Mitigation: fit the critic for N updates with the policy frozen before any policy step.

**R2: potential-based shaping, two terms only.** On top of R1:
- `Phi_tower = w_t * (sum own tower HP fraction - sum foe tower HP fraction) / 3`
- `Phi_crown = w_c * (own crowns - foe crowns) / 3`
- `F = gamma * Phi(s') - Phi(s)`, `Phi(terminal) = 0`, gamma the same gamma the returns use (checked by a test).

**No elixir potential in R2.** It is the term that dominated the friend's run, the kind of term behind our own §4.1
collapse, and it misprices spells (a spell never becomes a board unit, so casting one always "loses" elixir
potential). It gets its own step R3 only if R2 is clean, with spell pricing fixed and a hard magnitude cap.

## 3. Pre-flight checks before ANY shaped training run (cheap, CPU, minutes)

1. **Telescoping test:** on recorded matches, the per-match sum of F equals `-Phi(s_0)` to float precision.
2. **Magnitude budget:** on 100 matches of the IL policy, mean |sum of per-step F| per match is at most 0.5 x the
   terminal magnitude (the friend's term was 1.0x). If it is over, reduce w before training.
3. **Scripted-behaviour audit** (the check that caught §4.1): compute per-decision advantages under R1+R2 for scripted
   policies: IL policy, never-play, spend-immediately, hold-to-9, spam-one-card, never-buildings, never-spells.
   No degenerate policy may have a HIGHER mean advantage than the IL policy. If one does, stop and redesign.

## 3b. Correction after building the tools (2026-09-30 night, R2 builder's findings, accepted)
- **Check 2 as written cannot fail.** The per-match sum of F is -Phi(s_0) = 0 at a symmetric start, whatever the
  weights. Replacement: bound the per-decision potential, which is exactly the shaping part of every return-to-go
  (-Phi(s_t)). |phi_tower| < 1 and |phi_crown| <= 2/3 before the end, so |Phi| < (5/3) w. **w_tower = w_crown = 0.3**
  keeps |Phi| <= 0.5 x terminal on every reachable state. The IL-only measurement (max |Phi| 0.357 at w=1) is looser,
  because IL matches never reach the extremes.
- **Check 3 is biased without a critic.** Under pure returns-to-go the shaping adds -Phi(s_t), a state-only term: it
  adds no gradient bias in expectation, but it shifts the audit's means in favour of losing policies (smoke at w=1:
  IL ranked last on the shaping part). The clean audit needs R1's critic (lambda < 1). Until then a flag is a STOP
  only if the same policy is also flagged under terminal-only (R1) returns.
- **What R2 can actually do.** With a critic, potential shaping is equivalent to starting the critic from Phi
  (Wiewiora 2003). R2 therefore gives the value function a hand-made prior: ahead on towers and crowns is good. That
  is useful exactly because our critic is weak (outcome accuracy 0.70 at init). It also means R2 can only matter on
  top of R1 (lambda < 1). With pure Monte-Carlo returns it changes the variance, not the expected gradient.
- Gamma is per KEPT decision row (gate sampled or played; ~290 of ~350 decisions a match; 0.999^290 ~ 0.75), the same unit in R1 and R2 (verified 2026-09-30).
- R2 run: start with a critic warm-up (critic_warmup_updates > 0). Switching an R1 critic to the shaped target moves its target by -Phi at once, and V is limited to [-1, 1] while the shaped target can reach about 1.5 (R2 verifier F4, untested; measure explained variance in the first updates).

## 4. Collapse alarms during training (automatic stop rules)

The existing guards stay: entropy floor per head, plays/min band, KL stop, screen exploit guards, pro-agreement
tripwire. New ones:

| Alarm | Stops when | Catches |
|---|---|---|
| per-card play rate per opportunity | any card < 25% of its IL-baseline rate for 3 consecutive updates | Cannon/Log-style suppression (friend), 4-costs never played (§4.1) |
| unconditional play rate | plays/match < 50% of init, or gate p90 == max to 3 decimals | gate collapse (engA) |
| elixir at play and leak share | mean elixir-at-play leaves [0.6x, 1.5x] of init, or 10-elixir share > 2x init | bar emptying / hoarding |
| per-card cell entropy | any card's cell entropy < 50% of init | placement collapse (§4.3, arm G) |
| shaping dominance | per-update mean |F| > 0.5 x terminal magnitude | a term louder than winning |
| spell and building share | share of plays that are spells or buildings < 50% of init | friend's building and spell decline |

Each alarm logs its reading every update, so a stop comes with the curve that caused it.

## 5. Evaluation (unchanged instrument, closed loop)

Each candidate is scored as league1 was (the pinned 299 train-split screen vs init) **plus** the S0 harness's plain arm:
candidate vs frozen gen_v1 and vs S1 on the same 24 seeds, paired. That is a closed-loop head-to-head the ghost
screen cannot provide. A matched no-shaping control is always the previous step's run (R0 for R1, R1 for R2).

## 6. Cost and order

- R0 league1c: one overnight GPU run (now).
- R1: code change (worker + verifier, about 1 day), critic warm-up, then one overnight run.
- R2: potential functions + the 3 pre-flight checks (CPU, hours), then one overnight run.
- R3 (elixir potential): only if R2 is clean.

Nothing here is implemented until the owner approves the plan.

## 7. Roadmap after the outside review (owner: "go with whatever order you suggest", 2026-09-30)

Principles: (1) every simulator or policy change gets its own short re-baseline (the pinned 299 screen, ~15 min of
GPU), so each effect is attributable; (2) the R-series keeps gen_v1_s0 as its init until it finishes, so R0'/R1/R2
compare cleanly; better imitation models (gen_v2) are trained alongside and the winning RL recipe is re-applied to
them afterwards; (3) one GPU: league runs at night, imitation retrains in daytime slots the owner frees.

**Day 1 (2026-10-01)**
1. 07:00 league1c stops -> evaluate vs league1b at equal updates on the CURRENT engine.
2. Royale update + rebuild + tests -> re-baseline.
3. Evolutions on (Evo Tesla, Evo Knight via reset forms) -> re-baseline.
4. Placement legality mask (sim via RoyaleSim's deploy-legality query; live via the same rules from the reader's
   board) -> re-baseline; live: fewer refused taps.
5. Live acceptance protocol v1 (below) run by the owner after 2-4 deploy.
6. Pre-flight measurements on CPU (telescope, magnitude, scripted audit).
7. League training pool re-census with the new cards (eval stays the pinned 299).
**Night 1:** R0' = league1c settings on the new setup (the control for R1).
**Day 2:** scorer upgrade (current HP + a position term) + scorer-vs-full-match validation (CPU); label fix (wait
rows on own play ticks) -> gen_v2 retrain (GPU slot, ~4 h) -> re-baseline + live acceptance.
**Night 2:** R1 (per-decision credit). **Night 3:** R2 (shaping + critic warm-up), each vs the previous run.
**Later, gated on results:** opponent cycle/history features (gen_v3 retrain); exploiters in the league once an RL
step shows a real gain; search again only after the scorer validates.

**Live acceptance protocol v1** (every deployed change): 20 friendlies vs JinxTheCat's bot (or Training Camp),
logged per match: tap latency (median/max), confirmation rate, placement error (tiles), refused/unconfirmed taps,
plays/min, elixir-leak share, outcome. Pass = no regression in the mechanics metrics vs the previous deployment
(these are tight with 20 matches); win rate is reported with its interval (about +-20 pp at n=20) and is a
tripwire, not a gate.

## 7b. Second outside review (2026-10-01) — accepted changes
**Before R1 runs (Night 2), learner fixes (one ticket, default-identical, verified):**
- Shaped critic: with potential shaping the exact shaped value is V(s) - Phi(s) (Wiewiora). Keep the critic on the
  UNSHAPED win/loss value (bounded [-1, 1] is then correct) and form shaped advantages with V'(s) = V(s) - Phi(s).
  Fixes the "target 1.2-1.5 unreachable" problem without a new head (also R2 verifier F4).
  **CORRECTED 2026-10-01 (builder's algebra, verified):** with the same gamma_t in F and GAE, V' = V - Phi gives
  delta' = delta for ANY V, i.e. R2 == R1 (no-op). Implemented instead (303f3bc): residual critic V_eff = Phi + s*v_net,
  A = GAE(r, V_eff) on the unshaped r (== the shaped-critic method), v_net target (ret - Phi)/s, s = 1.5 >= 1 + |Phi|max;
  critic warm-up mandatory (enforced).
- Time-based discount: gamma per TICK, gamma_row = gamma_tick^(ticks between consecutive kept rows), in both GAE and
  the shaping F (the potential identity requires the same per-step discount).
**Acceptance instrument:** every R-step and every new imitation model (gen_v2+) is accepted on COMPLETE REACTIVE PLAY:
the S0 harness plain arm (candidate vs frozen gen_v1 and vs S1, 24 fixed seeds, paired, greedy live rule), plus the
pinned 299 ghost screen for continuity. An RL gain only counts if it appears under the GREEDY live rule (training
samples; deployment is greedy). Imitation checkpoint selection must stop relying on cell accuracy with the expert's
card supplied: select gen_v2 on the joint gate+card+cell metric and the reactive-play arm.
**Live (with a live acceptance round):** decide only on the sim's 10-tick grid (today live decides every ~100 ms; the
gate's per-decision probability assumes the 500 ms cadence). Cost: ~0.25 s mean extra latency vs the existing 1.3 s.
**Later:** opponent memory as an ordered-sequence model; a snapshot curriculum (restart episodes from saved states
where the policy lost; RoyaleSim save/load); search with sampled opponent hands/responses and extra rollouts on
close decisions (after the scorer validates).
**Measured, for the record:** sampling-vs-greedy does not explain league1's null (its SAMPLED self-play vs init was
~52%); our screens already measure the greedy rule.
