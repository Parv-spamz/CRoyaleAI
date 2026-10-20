# An RL framework past imitation — brainstorm (final, 2026-09-30)

Owner's goal, in three parts:
1. **Play near-perfectly almost all the time**, enough to give real pros a fight.
2. **Adapt within a match**: read the opponent's style as the match goes and change its own play to counter it.
3. **Predict the opponent's plays**: for example, fire a Rocket so it lands just as the opponent places a troop there.

The short version of this document: **the idea to build on is search, not a new policy-gradient
recipe.** "Search" means trying moves in the simulator before committing to one. Every measurement
this project has made points the same way. Plain RL from win/loss has never moved this model. Search
on top of the same frozen model has doubled or tripled its win rate twice. The one thing that broke
search-based training before, the student seeing a noisier board than the teacher, is mostly gone now
that the memory reader gives the live model the exact board.

---

## 1. What is already measured (so we build on evidence, not hope)

| What was tried | Result | Why it matters here |
|---|---|---|
| PPO on the real engine, 4 arms, ~1,500 matches (HANDOFF §5cs.44-51) | With a leash to the starting policy it stayed where it started; without the leash it fell apart (placement logits railed) | A win/loss reward alone gives too weak a signal for this model at our sample budget |
| league1: self-play league, 352 updates, ~22k matches, 16 h (old RoyaleSim) | No strength gain: ~0.50 against its own starting point in every window; acceptance +1.7 pp [-2.0, 5.4] | Same conclusion, on a far more faithful simulator |
| league1b: league1 on the updated engine (tonight, the one change; 75 updates, ~4.8k matches) | **No gain.** vs init at u20 / u30 / u75: +0.3 / -0.3 / -0.7 pp (each CI about +-3.7). league1 on the same new-engine evaluation at u10 / u20 / u75: -0.7 / +1.7 / +0.7. Self-play vs its own start 52.3% vs league1's 52.2% | **The old engine was not the blocker.** Plain league RL gives no signal on either engine |
| **Rollout search over a frozen policy** (HANDOFF 6-PRIORITY-B) | **37.0% -> 85.7% wins**, +20.7 sigma; six controls (heuristic, playing more, opponent oracle, perfect perception, crown weight, threshold) failed to explain it | The information for much better play is already in the policy's own ranking of moves; the policy just does not use it |
| **Search over the S1 student** (HANDOFF N) | 25.0% -> **91.7%**, +1.714 tower, t = 4.08; force-play, random-candidate and never-play controls all fail to explain it | Replicated on the network we actually deploy |
| Distilling the search's actions into the student (HANDOFF P) | Agreement with the teacher rose, yet it played **worse** (-0.54 / -0.39 tower) | The student copied the teacher's restraint without its judgement |
| A learned value head reranking moves (HANDOFF R-S; line closed by owner 2026-09-10) | As the play/wait gate: a clear loss; as a pure chooser: a null | **Both failures have one measured cause: the privileged-teacher gap.** The teacher searched on engine truth, while the student saw the old screen-reading view (the "degraded view": missed units, noisy positions, wrong teams, ~40 points of accuracy lost) |
| Tau sweep, tonight | 0.35 best (0.950), live 0.5 0.913; 0.35 vs 0.5 +3.7 pp [0.3, 7.0] | Cheap knobs are nearly exhausted |

**What changed since the distillation failures.** The live model now reads the game's memory, so
it sees what the engine sees: positions, HP and teams are exact (`noise_off=all` is the live
condition). The two things it still cannot see are the opponent's hand and their exact elixir, and
section 3a covers both. The owner's own condition for reopening this line, "a student that sees what
the teacher sees", is now mostly met.

A caveat on the search numbers: the two search results above were measured on the project's
**older, hand-written simulator** (lower fidelity), not on RoyaleSim. Whether they hold on RoyaleSim
is **untested**, and it is the first measurement in section 5.

---

## 2. Why plain RL stalled, in one paragraph

PPO learns from "this match was won" or "this match was lost", spread over ~360 decisions a match
(one every 10 ticks), ~90% of them "wait". At 64 matches per update, the signal telling any one decision whether it was
good is tiny next to the noise. The policy is also already decent, so the improvements left to find
are subtle. Systems that went superhuman on policy gradient alone (OpenAI Five, AlphaStar) paid
with the equivalent of centuries of play per agent, orders of magnitude beyond our ~1,400 matches an hour. Search fixes the credit problem directly. At one decision it tries each
candidate move in the simulator and compares the outcomes, so it gets a per-decision answer without
waiting for a match result. That is why the same frozen policy plays twice as well with search.

---

## 3. The proposed framework: search-driven self-play with an opponent model

This is expert iteration, the AlphaZero idea, adapted to Clash Royale's real-time play and hidden
information. There are four parts.

### 3a. Know the hidden information (the belief)
- **Opponent hand, from cycle tracking.** Clash Royale's hand is a queue: a played card goes to the
  back. Once an opponent has played all 8 of their cards, their hand is known exactly, as the 4 cards
  not among their last 4 plays. Before that, it is a distribution over the cards not yet seen, and a
  deck prior from the census data (their first cards usually give the archetype away).
- **Opponent elixir, from the counter** (already live). Measured error: MAE 1.34, reading high
  because bodiless spells are invisible. Search can sample from this uncertainty rather than trust
  one number.
- So after the first ~30-60 s the game is **nearly perfect-information**, which is the regime where
  search is strongest.

### 3b. An opponent model: the "predict and adapt" engine
A network predicting **the opponent's next play**: which card, where, and roughly when. It is
conditioned on (i) the board, (ii) the belief above, and (iii) **this match's history of the opponent's
plays** (for example "this player always answers a push at the bridge", or "they cycle Hog every 20 s").
- It is trained first by supervision on pro replays, which we already have in volume: every pro
  play is a label. Then it keeps training on league opponents.
- Its input is the current match's history, so it **adapts within a match by construction**. Once
  it has seen the opponent place Hog at the left bridge three times, it predicts the fourth.
- It is what makes **predictive plays** possible (below).
- A cheap first measurement: its top-1 and top-5 accuracy on held-out pro matches, and whether
  accuracy rises as the match goes on. If it does, it is learning this opponent, not just pros in
  general.

### 3c. Decision-time search in RoyaleSim
At each decision where the policy's gate says "maybe play" (plus a sample of waits):
1. **Candidates:** the policy's top K (card, cell) moves, plus WAIT. Spells also get
   **opponent-model-aimed candidates**: the cells where the opponent model expects a troop at spell
   impact time.
2. **Branch the battle:** RoyaleSim saves the state as ~12 kB and loads it back exactly. It runs about
   20,000 ticks/s per worker, so a 5 s lookahead is ~5 ms of engine time.
3. **Roll out** each candidate M times for H seconds. Our side plays the policy; the opponent's plays
   are **sampled from the opponent model**, with their hand drawn from the belief.
4. **Score** each rollout with a learned value head at the horizon plus the tower-HP change, never a
   hand-written damage score. The old S3 search picked placements 13.5 tiles from the pro's because
   it scored damage only ("the objective, not a bug", 5cs.90).
5. **Choose** the best candidate on average (a robust choice; a regret-minimising one later).

**This is where the "rocket the troop the opponent is about to place" behaviour comes from.** Nobody
programs it. If the opponent model says "70% they drop Musketeer at (4, 20) within 2 s", a Rocket
aimed there wins in 70% of the rollouts, and search picks it once that expected value beats the
alternatives. Leading a unit that is **already walking** is easier still, because the engine knows
exactly where it will be.

### 3d. The learning loop (the actual RL)
1. **Self-play with search** in a league: past snapshots, the S1 specialist, exploiters trained
   specifically to beat the current main agent, and deck variety. Every searched decision becomes a
   training example: the search's move distribution and the eventual outcome.
2. **Policy** trains toward the search's choices (not the pro's), with a KL leash to the IL policy
   early on so it cannot drift into nonsense. **Value** trains toward outcomes. **Opponent model**
   trains on what opponents actually did.
3. Repeat. A better policy gives better candidates, which gives a stronger search, which gives
   better targets. That compounding loop is what took AlphaZero past human play without human data.
4. **Where the distillation failed before, and why it should not now:** the student and teacher see
   the same exact board (the memory reader's view). The remaining asymmetry is the opponent's hidden
   hand and elixir. The student must see the same belief the teacher searched with, never the true
   hand.

### 3e. How it plays live
- **Phase 1:** deploy the distilled policy alone (fast, ~40 ms), exactly as now.
- **Phase 2:** live search. This needs a **shadow engine**: rebuild a RoyaleSim state from the live
  memory frame each decision, then search from it. The 26-tick action delay (1.3 s) is the time
  budget; ~64 rollouts x 100 ticks is ~0.3 s of engine time on one core, before policy cost. The
  owner said a shadow engine makes sense once RoyaleSim is mature; it now nearly is (132/144 cards).
  The hard part is internal state the reader cannot see (attack cooldowns, retarget timers), which
  is approximate at first.

---

### 3f. Known limitation: fast multi-card combos (owner question, 2026-09-30)
Some situations call for a precise sequence, "X here, then Y there, within ~1-2 s". Two things block it today.
- **Execution.** live_play and the sim both lock decisions until a play registers: ~26 ticks from decision to
  landing, plus the 10-tick cadence, so the fastest possible pair is ~1.5-1.8 s apart. Measured: building the
  latency-shifted dataset dropped 32,767 pro plays (~3.5% of all plays) that were the second card of a combo
  within 35 ticks, because the lock cannot execute them.
- **Search depth.** S0 scores one candidate with our side IDLE afterwards, so a move that is only good because of
  its follow-up is undervalued. Greedy X-then-Y can still happen, but only when X also looks good alone.
- **Planned remedies, one change each, after S0:**
  - (1) our side plays its own policy inside rollouts;
  - (2) two-move plan candidates (X, Y, delta-t) drawn from pro combo statistics, with a live "plan" mode that sends
    both taps back to back (the game allows it; the lock is ours);
  - (3) deeper tree search over our own moves.

---

### 3g. Owner concern: opponent follow-ups and prediction (2026-09-30)
"A play that makes sense for the current board may not make sense once the opponent drops new cards."
- **Already covered.** In S0 and option 1 the opponent keeps playing through the whole 12 s rollout (the self-model on
  its deck), so every candidate is scored on the board AFTER the opponent's responses.
- **Real gap: one deterministic guess.** The self-model is greedy, so each candidate sees exactly one opponent future.
  That guess is the wrong model against S1, the friend's bot or pros, and it knows the true hand (optimistic).
- **Evidence it is not S0's bottleneck (derived).** Against gen_v1 the rollout opponent IS the real opponent's policy
  and state; the fork-fidelity test reproduces the real continuation exactly. So prediction was perfect given our move,
  and search still gained nothing (t -0.04). The evaluation (12 s scorer) or the idle self is the likelier limit.
- **Remedy, queued after option 1 if search helps at all:** M sampled opponent continuations per candidate (a
  stochastic self-model), aggregated by the mean or a pessimistic quantile, at ~M x the cost. Later, the S2 opponent
  model conditioned on this match's history. If option 1 is null, the scorer-vs-full-playout check comes first.

---

## 4. How each goal maps onto the framework

| Goal | Which part delivers it | What limits it |
|---|---|---|
| Near-perfect play | Search corrects the policy's mistakes decision by decision; the loop bakes those corrections into the network | How good the value head is; simulator fidelity (search will exploit anything the sim gets wrong) |
| Adapt within a match | The opponent model is conditioned on this match's history; a league with diverse and exploiting opponents forces the policy to need that | Early in a match there is little history; diversity costs league time |
| Predict opponent plays | Search over the opponent model's sampled plays; spells aimed at predicted cells are candidates | How accurate the opponent model is; a "prediction" is a bet, and search will only take it when its expected value is positive |

Where it could be **superhuman**, not just pro-level: exact elixir and cycle counting every second;
exact HP, ranges and timings where humans estimate; zero reaction lag inside its 1.3 s budget; and
trying dozens of futures per decision, which no human can.

---

## 5. A staged plan (each step one change, each with a go/no-go measurement)

| # | Step | Cost | Go if |
|---|---|---|---|
| S0 | **Search over gen_v1_s0 on RoyaleSim**, closed loop against reacting opponents (frozen gen_v1, S1), no training. Reuse `student_search.py`'s design with RoyaleSim snapshots | ~1 day to build; hours of CPU (VM-able: CPU only) | Search beats the plain policy by a margin like the old sim's (tens of pp). **If not, stop and find out why before anything else** |
| S1 | Cycle-tracking hand belief: accuracy on pro replays, by match time | Hours, CPU | Exact hand in most decisions after ~60 s |
| S2 | Opponent model v0 (supervised on pro plays), accuracy by match phase | ~1 GPU night | Clearly above a history-blind baseline, rising within a match |
| S3 | Search with the opponent model inside, vs S0's search | CPU hours | Beats S0's search |
| S4 | One round of search -> distill into the exact-view policy; closed-loop check | 1 GPU night | The distilled policy beats gen_v1 **without search**. This is the test the old degraded-view student failed |
| S5 | The loop (expert iteration) + league with exploiters | Many nights; the VM for rollouts | Head-to-head Elo keeps climbing; live checks vs bots and the friend's hog 2.6 |
| S6 | Shadow engine + live search | Weeks | Live win rate with search > without |

**Evaluation must be closed loop.** The ghost screens (recorded pro plays replayed) cannot react,
so they cannot measure outplaying anyone. Use a head-to-head ladder of frozen agents, the S1
specialist and the friend's RoyaleLearn hog agents, plus live Training Camp and friend matches.
**Real pros:** under the standing rule the reader stays in Training Camp (bots), so "vs pros" can
only be approximated: pro ghost replays, the friend's strongest agent, and later, if the owner
decides, something else.

---

## 6. What could sink it (honest risks)

1. **Simulator gaps:** search optimises against RoyaleSim, not the real game, and will find and
   exploit any mismatch. Mitigations: the friend's fidelity work; live checks at each stage; a KL
   leash to the IL policy; never trusting a sim-only gain.
2. **Value head quality:** short-horizon rollouts need a good value at the horizon. The current
   head's accuracy is 0.70 on outcomes. It gets better as the loop feeds it self-play outcomes, but
   early search is only as good as it is.
3. **Compute:** the laptop is shared (ask before big runs) and has an 8 GB GPU. The VM is CPU-only,
   which suits rollouts well if the rollout policies are cheap (small network, or batched on the
   laptop GPU).
4. **The opponent model can be wrong, or exploited.** Mitigations: sample from it rather than
   trusting its top guess; include exploiters in the league.
5. **Early game hidden information:** until the opponent's cycle is known, search runs on a wide
   belief, and its edge is smaller there.

---

## 7. What would prove this wrong

- **S0 shows little gain from search on RoyaleSim.** Then the old result depended on the old sim's
  simplifications, and the framework needs a different improvement operator.
- **S4's distilled policy still loses to gen_v1 with exact inputs.** Then the privileged-teacher
  gap was not the whole story (the hidden hand, or model capacity), and the loop cannot compound.

## 8. league1b result, and what it settles

league1b = league1 with one change, the updated RoyaleSim. It was stopped at update 75 (06:00): the laptop was at
100% CPU from other programs, and a GPU out-of-memory crash at u49 was resumed. The comparison is at equal budget,
with both runs evaluated on the new engine, against the same starting model, on the same 299 recorded matches,
paired:

| checkpoint | vs the starting model (pp, 95% CI) |
|---|---|
| league1b u20 / u30 / u75 | +0.3 [-3.3, 4.0] / -0.3 [-4.0, 3.3] / -0.7 [-4.3, 2.7] |
| league1 u10 / u20 / u75 | -0.7 [-4.7, 3.3] / +1.7 [-2.0, 5.4] / +0.7 [-2.7, 4.0] |

In self-play against its own starting point, league1b won 52.3% (1,368 matches) and league1 52.2% (1,392) over the
same updates. Its held-out screen wandered 0.86-0.95 with no trend, as league1's did. Its policy drifted slightly
more (gate KL 0.045 vs 0.028 at u74) and bought nothing with it.

**Reading:** the engine update did not unlock plain league RL. This is the third independent null for win/loss policy
gradient on this model: the real engine, league1, and league1b. The null covers this recipe at this budget; it does
not say RL can't work here. It supports section 2's diagnosis that the missing piece is a per-decision improvement
signal, which is what search supplies. **S0 (search over gen_v1_s0 on RoyaleSim) is the next experiment.**
