# O21 — audit of the owner's four live-play complaints (LEAD TRANSCRIPTION + lead follow-up)

Scout agents have Read/Glob/Grep only and cannot write; transcribed by the lead 2026-09-18 from the
hand-back, with the scout's own (a)/(b)/(c) labels CORRECTED where it mislabelled "not recoverable"
as "contradicted". Lead's own findings are marked **LEAD**.

## Data used
run20_utf8.log (v6aug tau 0.24, 90 plays / 609 s), run18_utf8.log (164 plays), run12b_utf8.log
(176 plays), session 20260912_152220. **Tonight's live run is NOT recorded** — newest session on
disk is 2026-09-12, so none of this covers the play the owner just watched.

## A. Reaction time (owner: "slowing down")
- (a) Median inter-decision gap **~4.2-4.3 s, stable across run12b / run18 / run20** — no downward
  trend in decision cadence.
- (a) run20 = 8.85 plays/min (90 plays / 609 s).
- (a, prior, HANDOFF 5cs.99 AU/AV) pause share: v6lat tau 0.27 **27%** -> v6aug tau 0.27 **35%** ->
  v6aug tau 0.24 **49%** of match time in >10 s pauses.
- **Reading (b):** what reads as "slower reaction" is almost certainly PAUSE SHARE, not latency —
  the gate no-ops for long stretches and then acts at normal speed. Tau 0.24 (what the owner has
  been running) pauses far more than 0.27. Not yet separated from a possible late-game effect of
  rising unit counts.

## B. Rocket (owner: rare; never finishes a low-HP princess; never rocket+tornado)
- (a) Usage: run20 1/90 = **1.1%**, run12b 2/176 = 1.1%, run18 1/164 = **0.6%**. Complaint CONFIRMED.
- (a) rocket+tornado: run20 tornado 23:33:18.4, rocket 23:36:47.6, tornado 23:36:57.1 — gaps 15.2 s
  and 9.5 s. **Zero pairs within 3 s.** Complaint CONFIRMED.
- **NOT RECOVERABLE (not "contradicted"):** tower HP per play is not in the logs, so "never finishes
  a low-HP princess" can be neither confirmed nor refuted from this data.

## C. Overtime / X-Bow (owner: barely defensive X-Bows; shoves cards at the bridge in OT)
> **WRONG — RETRACTED. See the LEAD ADDENDUM at the end of this file.** The classification below used
> a y > 0.5 threshold I invented; the code's own boundary is 0.58, and against it all 30 X-Bows were
> OFFENSIVE, not defensive. Do not cite this section.
- (a, RETRACTED) run20: 4 x_bow / 90 plays = **4.4%**, ALL at board y > 0.5 (own half, i.e. defensive):
  (0.14, 0.61) left and (0.75, 0.61) right. **Zero offensive X-Bows.**
- (b) Bridge concentration is consistent with the placement cluster but NOT quantified against the
  single-elixir mix; **overtime is not marked in the logs**, so OT-only plays cannot be filtered.
  The owner's overtime-specific claim is therefore untested, not disproved.

## D. Tower targeting (owner: never go for the king; 1-0 defend, 1-1 take the other princess)
- (c) **CONTRADICTED — nothing targets the king.** No `king_tower_cell` exists. play.py:343-344
  documents deliberate king avoidance ("a spell that reaches their king wakes it") and masks cells
  accordingly. The owner's hypothesis that bridge-shoving comes from being "forced towards the king
  tower" is not supported by the code.
- (b) Match state (1-0 vs 1-1) is tracked internally by `TowerTracker` but never emitted to the log,
  so play-to-state correlation cannot be done from these logs.

## **LEAD FOLLOW-UP — the doctrine assists ALREADY run on the student path**
`weaker_princess_cell`, `pump_rocket_cell`, `xbow_target_lane_cell` exist in reward.py and are called
from **play.py** (1062, 1065, 1101) and env.py — `student_live.py` calls none of them, which first
looked like "student bypasses doctrine". Reading play.py:1040-1109 shows the opposite:
- :1045-1047 take the STUDENT's chosen `(card_id, cell)` (after the affordability filter).
- :1052+ then operate on that same `cell`: rocket/miner snapped to the **weaker princess**
  (`weaker_princess_cell`), pump-punish rocket snapped king-safe (`pump_rocket_cell`), X-Bow snapped
  to the correct **lane** (`xbow_target_lane_cell`) and then locked (`xbow_lock_cell`), plus an
  X-Bow **pocket** placement when an enemy princess is down (:1084-1091).
So the doctrine layer is post-processing applied to the student's own choice. **The three behaviour
complaints are therefore probably NOT "the model must be retrained to learn this"** — the assist code
exists and runs on the live path; the question is why it does not fire (gating, config, or the
student rarely proposing the card in the first place — rocket is only ~1% of plays, and an assist
that snaps a rocket cannot help if no rocket is ever played).
- Note play.py:1095-1098, a prior recorded observation: `xbow_lock_cell` snaps to the NEARER princess,
  so with a tower already down it "will happily cement a bow into the dead lane -- which is what live
  overtime actually did, several times in one match". That is adjacent to the owner's overtime
  complaint and is already a known defect.

## What this does NOT establish
Why the assists do not fire; whether the owner's overtime observations reproduce (OT unmarked);
tower-HP-conditioned behaviour (not logged); anything about tonight's session (unrecorded).

STATUS: complete (lead transcription + follow-up)

## LEAD ADDENDUM 2026-09-18 — corrections and two decisive measurements

### RETRACTION: the X-Bow offensive/defensive split (owner-corrected)
I reported "4.4% of plays, ALL defensive, zero offensive" using a y > 0.5 rule I invented. The code
defines the boundary itself: `play.xbow_forward_board_y: 0.58` (config.yaml:1369 — "the live X-Bow
assists treat a bow as OFFENSIVE only forward of this BOARD depth"). Re-measured against 0.58:

| run | X-Bows | board y | verdict |
|---|---|---|---|
| run20 | 6 | all 0.61 | all FORWARD of 0.58 = offensive |
| run18 | 11 | all 0.61 | all offensive |
| run12b | 13 | all 0.61 | all offensive |

**30/30 offensive, zero defensive.** The owner ("literally every xbow the model played was
offensive") was right; my metric was wrong. X-Bow is exactly the card where own-half != defensive —
siege range ~11.5 tiles means the standard offensive placement sits behind the river on your own side.

### Overtime forwardness (owner item 3) — NOT SUPPORTED on available data
Only run12b reached overtime (12 non-X-Bow plays past t=180s; run18 never did, run20 had one).
Median board-y: **0.550 regular vs 0.550 overtime**; enemy-half placements 10% vs 17% (a two-play
difference). (c) not supported — but n=12, and run12b is a week-old v6aug run at a different tau
than the session the owner actually watched. Treat as UNTESTED, not refuted. Tonight's session was
not recorded; the newest on disk is 2026-09-12.

### Rocket: NOT gated, simply not chosen (a) — decides that this needs training, not a live fix
Counted decisions where rocket was in the tap hand AND elixir >= 6, versus rockets actually played:

| run | opportunities | rockets played | rate |
|---|---|---|---|
| run20 | 39 | 1 | 2.6% |
| run18 | 37 | 1 | 2.7% |
| run12b | 52 | 2 | 3.8% |

**128 opportunities, 4 rockets, under 3%.** Nothing filters or blocks it — the affordability mask and
the gate are not the cause. The model simply does not select rocket. That is card selection, which
imitation training determines, so it is NOT fixable on the live path and NOT fixable overnight. It
also explains the absent rocket+tornado combo without a separate theory: a two-card combo cannot
appear when one half is played once per match.

### The one live-path defect worth fixing tonight
play.py:1101-1109 runs `xbow_target_lane_cell` (the anti-dead-lane fix, reward.py:420, written after
the owner's 2026-08-16 report of this exact behaviour) and then runs `xbow_lock_cell`
UNCONDITIONALLY. That function takes `enemy_anchors[:2]` with no aliveness argument and snaps to the
NEARER princess — so the dead-lane correction can be overwritten two lines later by a function that
does not know the tower is dead. Ticket O22 dispatched to fix it with a backwards-compatible
`enemy_alive=None` parameter so the training sim (env.py, which shares reward.py) stays unchanged.
