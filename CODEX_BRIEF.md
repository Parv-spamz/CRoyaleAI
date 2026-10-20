# CODEX BRIEF -- continue ClashBot until Claude's usage resets (Tuesday 2026-10-06)

Written by the lead (Claude) on 2026-10-04 (final update ~20:55 EDT). Read this file first, then `README.md` (the project overview) and the TOP of
`HANDOFF.md` (the blocks dated 2026-10-04: every number below comes from there, with its context). The owner will talk
to you directly. This brief tells you what was done, what was measured, what to do next, and -- most important -- HOW
the work is done here, so the project does not drift.

## 1. How we work (non-negotiable; this is what keeps the project on course)

1. **Measure, then claim.** Every claim is labelled *measured* (cite the number + file), *untested* (say so, propose the
   measurement) or *contradicted* (give the evidence). Never present a guess as a result. The owner is a student who
   asks to be corrected: if the owner's diagnosis or idea is wrong or untested, say so plainly, with evidence, before
   acting on it.
2. **Acceptance instruments, not impressions.** A model or setting is better only on:
   - the **paired ghost screen** (`scratchpad/gauntlet/L68/generalist/screen_gen/run_screen.py`, 299 pinned replays,
     flags exactly as in `scratchpad/gauntlet/L71/gen_v31/accept_v31a.sh`: `--split train --noise-off all --opp-elixir
     counter --action-delay 26 --extrapolate 26 --seeds 0 --device cuda --forms-mode deck --tau 0.27 --only-tags-from
     scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl --behaviour-telemetry`), scored with `--pair A B`
     (paired pp with a 95% bootstrap CI), AND
   - **reactive play** (`python -m pipeline.search_s0 --seeds 0:24 --opps gen,s1 --arms plain ...`, wins out of 24), AND
   - the **behaviour telemetry** (Rocket share, tower Rockets, finish-offs, multi-Rocket cycles, defensive Rockets, both
     Rocket/Tornado orders, X-Bow cells/lanes, pre-emptive Log) -- compare with the pro baselines in HANDOFF.
   Always pair against a baseline run with the SAME code (a code change between two screens invalidates the pairing --
   see the R8 mistake in HANDOFF 14:5x). Write the decision rule BEFORE you see the result.
3. **One change per experiment.** Each run changes one thing so its effect is attributable. New behaviour goes behind an
   opt-in flag/config key whose default is byte-identical to today, with a test proving that.
4. **No hand-written playstyles.** The owner's rule: the bot learns from pros (imitation from re-driven pro replays,
   weighting of pro situations, RL). Do not add rules like "Rocket when tower < X HP". The only hand-written rule
   allowed is the owner-ordered interim Hero Ice Wizard ability rule (`hero_button.py`), until pro data exists.
5. **Public information only.** The opponent's hand, next card, elixir and ability readiness are NEVER model inputs.
   Measurements may use recorded hidden state; models may not.
6. **Machine discipline.** One GPU job at a time (check `nvidia-smi` and running python first). The laptop is shared.
   Never kill or edit a running script (write a `_v2` file instead). Kill processes only by exact command-line match in
   a command that does not itself contain the pattern. Long jobs: write a launcher script, log to a file, poll it.
7. **Live play.** Never start, stop or reconfigure live unless the owner asks (the owner starts it with
   `bash scratchpad/gauntlet/L70/live/start_live.sh`, stops with `stop_live.sh`; the model is the path in
   `scratchpad/gauntlet/L70/live/CKPT_OVERRIDE`). Never deploy a checkpoint without the owner's explicit approval:
   post "APPROVAL NEEDED: <what>" to Discord with the evidence and wait.
8. **Owner decisions.** Anything the owner would decide (deploys, live settings, spending, deleting data, changing an
   acceptance rule, changing the experiment plan) -> write it to `.foreman/codex_autopilot/BLOCKERS.md` (what, why,
   options, your recommendation, evidence) and continue with unblocked work. Do not decide it yourself.
9. **Record everything.** After every change batch: update `HANDOFF.md` (a dated block at the top, numbers + paths),
   commit and push to `main` with a clear message ending `Co-Authored-By: Codex (autopilot)`. NEVER stage `icebow/data/`
   (secrets incl. `discord_webhook.txt`; never print the webhook URL). Post a short Discord report after each milestone
   (`icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L69/discord/post.py <msg.txt>`): what was done, the numbers and
   what they mean, next steps.
10. **Stay in scope.** Do the queue in section 4. No refactors, no new frameworks, no re-auditing finished work, no long
    reports. If a gate blocks you, try the obvious fix first, then record the question and move to the next item.

## 2. State at the time of writing (2026-10-04 ~15:50 EDT)

- **Data:** full real-engine re-drive of 14,818 pro recordings (0 failures) with public observations: projectiles +
  time-to-impact, spell areas + timers, exact evo/hero ids, driven abilities. Dataset
  `icebow/data/pipeline/gen_dataset_v31_public.npz`: 3,517,863 rows, 14,661 replays, 4,283 decks, v3val 12,237.
- **Imitation models (feature version 4):** gen_v3.1a (inputs only), 3.1b (+ six-target pro-context weighting 2.0),
  3.1c (weight 4.0). **gen_v3.1c is the best gen model**: vs 3.1b +1.2 [-2.2, +4.5]; vs live-best RL u0155 -1.7
  [-4.7, +1.3]; reactive gen 13/24, S1 19/24.
- **R8 (look-ahead advances projectiles/effects, inference-only):** measured on 3.1a: pre-emptive Log 23.5% -> 49.8%
  (pros 39.1% same deck/definition); ghost +1.0 [-1.7, +3.7]. On by default for v4.
- **RL:** R1e = PPO from gen_v3.1c (5 actors, evo/hero census opponents, calibrated per-ability press models v2,
  R8), launched 15:06 by `scratchpad/gauntlet/L71/rl/run_r1e_v3.sh`; log `scratchpad/gauntlet/L71/rl/r1e.log`. Its
  verdict and the live decision are appended in section 6 when they arrive.
- **Live:** RUNNING on R1e u0155 (owner decision, to observe the new inputs live) -- see section 6. Start/stop: `start_live.sh` / `stop_live.sh`.
- **Abilities in the sim:** `ability_policy: v2` (royale_env / e1_eval / rl_royale / search_s0 `--ability-policy`).
  Calibrated models: `scratchpad/gauntlet/L70/abilities/ability_models_v2.json` (held-out share error <= 3 pp for 17/22).
- **Live ability:** Hero Ice Wizard = owner's interim rule (freeze clumps of >= 3 troops, or a win condition on our
  half when Tesla is not in hand / < 4 elixir). Reader v2 reports hero units as 203000000 + n (fixed lookup).

## 3. Findings that steer the next steps (all measured; files in HANDOFF)

- **Rocket is the biggest gap:** ~0.9% of plays vs pros ~5.8%; tower Rockets ~8-10 per 299 games; finish-offs 0;
  multi-Rocket cycles 0. Weighting 2x/4x barely moved it. Diagnosis (`scratchpad/gauntlet/L71/rocket_diag/`): at pro
  Rocket moments the model gives Rocket P = .24 (AUC .84, well calibrated) but **argmax** picks it only 22%; the gate is
  not the blocker (87% pass); and when Rocket IS chosen the **argmax cell hits a tower only 28.5%** (overtime-behind
  6.9%) because the cell distribution mixes troop and tower targets.
- **X-Bow:** pros use 2 offensive rows and ~24 cells; the model's distribution is spread (80% mass on lock-capable cells)
  but argmax collapses it to 2 cells; sampling X-Bow cells lowered agreement (not adopted). Dead-lane X-Bows: pros' are
  mostly POCKET plays; the bot's are mostly own-half (n = 30, weak). X-Bow reach for labels = 13.0384 tiles
  centre-to-centre (98.2% hit recall).
- **RL so far never increased Rocket use** (u0155 50 Rockets vs gen_v1 72 in the same 299 games). Hypothesis
  (untested): sampled Rockets with poor aim waste elixir, so RL learns to avoid them -- fix aim before expecting RL to help.
- **RL determinism:** results are now sorted before learning (actor count / timing no longer change runs).

## 4. Next steps (do in this order)

- **Q1 (CPU) Card choice: CONFIDENCE-FILTERED sampling, opt-in -- never plain sampling.** Owner concern (2026-10-04,
  correct): plain sampling over the hand would sometimes play a card the model itself rates as unviable when the top
  card is the only good answer (the diagnosis already shows plain T=1 sampling firing Rocket on 7.6% of non-Rocket pro
  moments). Design (`card_choice: argmax | filtered`, `card_ratio r`, `card_T T`; default argmax, byte-identical,
  test), in `pipeline/e1_eval.py` `live_decide` (SIM) and `pipeline/live_gen.py` (live):
  1. Only affordable hand cards are candidates (the existing mask).
  2. **Keep the argmax card whenever the model is confident:** a card is a candidate only if p_card >= r * p_top
     (r = 0.5 / 0.7 to test). If no other card passes, play the top card exactly as today. So a clear "only answer"
     (e.g. p_top .9) can never be replaced; only near-ties are randomised.
  3. Sample among the remaining candidates with temperature T (0.7 / 1.0), seeded (SIM: per match seed; live: logged).
  4. The play/wait gate stays deterministic (P(play) > tau). The cell rule is unchanged (Q2 handles spell cells).
  **Offline check BEFORE any SIM time** (CPU, extend `scratchpad/gauntlet/L71/rocket_diag/rocket_diag.py`, teacher-
  forced pro val rows of the icebow deck): for each (r, T) report (a) Rocket recall on pro-Rocket rows, (b) Rocket
  false-fire on non-Rocket rows, (c) overall card agreement with the pro (expected value) vs argmax, (d) **override
  rate on confident rows** (rows where argmax prob >= .6: must be ~0), (e) the share of decisions that change at all.
  Drop any (r, T) whose overall agreement falls more than 1 pp below argmax. Only the survivors go to Q3.
- **Q2 (CPU) Area-aware spell aim, opt-in.** For area spells, choose the cell that maximises the model's cell-probability
  mass inside the spell's catalog radius instead of the single argmax cell (same flag pattern, SIM + live). Test: a
  sharp off-target cell vs a broad on-tower cluster must pick the cluster.
- **Q3 (GPU, only when no other GPU job runs)** ghost-screen A/Bs on the live model (or gen_v3.1c), paired against its
  saved screen run with the SAME code: (a) the best filtered-sampling setting from Q1's offline check, (b) the
  second best, (c) area aim, (d) area aim + (a). Report win value CIs, reactive play (gen + S1, 24 seeds each) and the
  behaviour telemetry. **Adoption rule (pre-registered; the owner's performance concern):** an option is proposed for
  live ONLY if (1) its paired ghost point estimate is >= 0 vs the baseline (not just "CI touches 0"), (2) reactive wins
  are not lower than the baseline's by more than 2 of 48, and (3) Rocket use / tower-Rocket hits move toward the pro
  numbers. If Rocket use rises but win value falls, it is REJECTED (report it; do not tune until it passes). Then
  "APPROVAL NEEDED: enable <option> live?" -- the owner decides.
- **Q4** Re-run the diagnostics (`scratchpad/gauntlet/L71/rocket_diag/rocket_diag.py`,
  `scratchpad/gauntlet/L70/xbow_diversity/xbow_diversity.py`) on the live model and report what changed.
- **Q5 Small fixes:** `pipeline/tests/test_dataset_spool.py` (KeyError 'own_ability' in the model_gen mmap path);
  `scratchpad/gauntlet/L70/live/run_live.sh` `last_stop()` should also match "new checkpoint deployed" (edit only if no
  run_live.sh process is running; otherwise make `run_live_v2.sh`).
- **Not for you (owner/lead):** the Hero Ice Wizard pro-data crawl (RoyaleAPI needs the owner's Cloudflare click);
  any deploy; R1e follow-up RL runs (propose them in BLOCKERS with a one-change design; do not launch).

## 5. Where things are

`README.md` (pipeline + how to run), `HANDOFF.md` (state, numbers, traps), `.foreman/codex_autopilot/LEAD_RULINGS.md`
(the lead's rulings R1-R8 on labels, TTI, look-ahead -- follow them), `scratchpad/gauntlet/L71/` (today's scripts and
outputs: gen_v31/, rl/, rocket_diag/, barrel_log/), `pipeline/` (all model/data/sim/RL code, tests in
`pipeline/tests/`; run with `research/ext/Royale/.venv/Scripts/python.exe -m pytest`).

## 6. R1e verdict and live decision (final, 2026-10-04 ~20:55 EDT)

R1e = `icebow/data/bench/rl_royale/rseries_r1e31/rseries_r1e31_u{0080,0155}.pt` (base gen_v3.1c). All measured
(`scratchpad/gauntlet/L71/rl/r1e.log`, `r1e_accept/`):

| model | ghost vs gen_v3.1c | ghost vs old u0155 | reactive gen/S1 (old census) | reactive gen/S1 (evo/hero census, abilities v2) |
|---|---|---|---|---|
| R1e u0155 | +1.3 [-1.7, +4.3] | -0.3 [-3.3, +2.7] | 17 / 21 | 11 / 21 |
| R1e u0080 | -0.3 [-3.3, +2.7] | -2.0 [-5.4, +1.3] | 16 / 21 | 11 / 21 |
| gen_v3.1c | 0 | -1.7 [-4.7, +1.3] | 13 / 19 | 8 / 19 |
| old rseries_r1_u0155 | -- | 0 | 14 / 24 | 12 / 24 |

Reading: RL on top of gen_v3.1c helped (R1e beats its base on all three instruments) and nearly closes the gap to the
old RL model, but does not beat it in the simulator: a tie on the ghost screen and the old census (38/48 each), and
old u0155 wins the evo/hero census 36/48 vs 32/48 (mostly vs S1: 24 vs 21).

**OWNER DECISION 2026-10-04 ~21:00: LIVE = R1e `icebow/data/bench/rl_royale/rseries_r1e31/rseries_r1e31_u0155.pt`**
(CKPT_OVERRIDE), "mainly to observe if our input space change and fixes translated into better live performance" --
simulator ties do not settle live performance. Do NOT switch live back on your own; the owner decides.

**Implications for your queue:**
- **Q0 (new, first, CPU) Live comparison, R1e vs old u0155.** From the live logs
  (`scratchpad/gauntlet/L68/live_reader/live_play_*.jsonl`, `scratchpad/gauntlet/L70/live/overnight.out` results +
  the checkpoint each run loaded -- "checkpoint override" lines / process --ckpt), tabulate per checkpoint: matches,
  wins/losses with a Wilson 95% CI, trophies over time, and live behaviour (Rocket share of plays, pre-emptive Logs vs
  barrels, ability presses, X-Bow placements) from the play/frame events. Old u0155 has ~2 days of live matches on
  10-03/10-04 as the baseline. Report every ~30 R1e matches (Discord, short); say plainly when the CI cannot separate
  them yet. Measurement only -- never change live.
- Run Q3 on R1e u0155 (the live model) AND old u0155, each paired against its own fresh baseline screen made with the
  SAME code (first produce `--behaviour-telemetry` baseline screens for both -- the old u0155 screen in L70/rl/r1_accept
  has no telemetry).
- Any further RL run (e.g. R1e for more updates, or RL after the Rocket fixes) is an owner/lead decision: propose it in
  BLOCKERS.md with a one-change design, do not launch it.
