# O23 — board-y direction, the 0.58 cut, and what actually gates X-Bow placement

Scout ran read-only and could not write; transcribed by the lead 2026-09-18, with the lead's own
independent verification of the branch structure marked **LEAD**. This file exists because the
question has now produced **three** different answers from me and the record needs one place that
is right.

## Verdict

**LARGER board y = CLOSER TO OUR OWN TOWER. Forward (toward the enemy) = DECREASING y.**
An X-Bow at board y **0.61** against the **0.58** cut is classified **DEFENSIVE** by the code.

## 1. The coordinate system, from code that COMPUTES it (not from comments)

`pipeline/obs_contract.py:32-35`:

    MY_KING_Y      = 1.0 - KING_TILE[1] / TILES_Y      # 0.90625
    MY_PRINCESS_Y  = 1.0 - PRINCESS_TILE[1] / TILES_Y  # 0.796875
    OPP_KING_Y     = KING_TILE[1] / TILES_Y            # 0.09375
    OPP_PRINCESS_Y = PRINCESS_TILE[1] / TILES_Y        # 0.203125

Enemy towers LOW y (0.094 / 0.203), ours HIGH y (0.797 / 0.906), river at 0.5
(`obs_contract.py:39`). Independently confirmed in FRAME space by the measured live config,
`icebow/config/config.yaml:1074-1075`: `enemy_towers` y ≈ 0.205/0.11, `my_towers` y ≈ 0.615/0.72 —
same ordering. Corroborated by `actions.py:84-85`, `geometry_reward.py:15`, `reward.py:396`
("forward is decreasing y"), `reward.py:501-502` ("your side is the HIGH-y half").

The board→frame warp (`actions.py:88,111-116`, anchors
`[(0.0,0.129),(0.203125,0.205),(0.5,0.4425),(0.796875,0.615),(0.90625,0.72),(1.0,0.762)]`) is
strictly **monotone increasing** in y and `_pw` (`actions.py:124-137`) is piecewise-linear, so the
sign never flips between board and frame space.

## 2. Every read of `xbow_forward_board_y`, and what it gates

Converted once to a frame-y cut: `play.py:323-324`
`xbow_live_defense_y = actions.warp.board_to_frame(0.5, _xbow_forward_board_y)[1]`.
It reaches exactly three assists as `defense_y`, and **all three use the same `>=` test and all
three `return None`** ("defensive bow — leave the placement alone"):

| assist | site | test |
|---|---|---|
| `xbow_target_lane_cell` | `reward.py:445-446` | `if len(princesses) < 2 or cy >= defense_y: return None` |
| `xbow_lock_cell` | `reward.py:492-493` | `if not princesses or cy >= defense_y: return None` |
| `xbow_offense_depth_cell` | `reward.py:539-540` | `if cy >= defense_y: return None` |

`cy` is a FRAME coordinate (`actions.cell_center`), matching the cut's units.

## 3. Board 0.61 vs cut 0.58 → DEFENSIVE

Through warp segment (0.5, 0.4425) → (0.796875, 0.615): cut board 0.58 → frame **0.4890**; bow at
board 0.61 → frame **0.5064**. `0.5064 >= 0.4890` is **True** → all three assists return `None`.

**The 0.58 value is NOT mis-set** — my earlier "appears mis-set" is (c) contradicted. It was chosen
deliberately so the pro row (board 0.604-0.609) counts as defensive, fixing a run15 regression in
which 16 of 17 X-Bows were shoved to the bridge (`play.py:318-322`). A committed passing test pins
the intent: `icebow/tests/test_xbow_live_depth.py:62-66` asserts *"the pro X-Bow row must count as
defensive"*.

The owner's gameplay point stands and is separate: an X-Bow's ~11.5-tile siege range
(`geometry_reward.py:34 DEFAULT_SIEGE_SIGHT`) means an own-half bow **does** reach the enemy tower.
So "every X-Bow was offensive" is true about EFFECT while the code calls the same bow defensive.
In this codebase "offensive" means only *"forward of 0.58, so the assists may reposition it."*
Both statements are true; they are about different things.

## 4. **LEAD** — the branch structure, and why commit 11c6e2f is probably INERT

`play.py:1084-1086` (read directly):

    if (card_id in xbow_ids and _xbow_pocket_on
            and (_pk := xbow_pocket_cell(tower_tracker.enemy_alive, actions, _xbow_pocket["side"],
                                         board_y=_xbow_pocket_y)) is not None):
        ...
    elif card_id in xbow_ids:      # the lane -> lock -> depth chain

The walrus means the pocket branch fires **only** when `xbow_pocket_cell` returns non-None, which
per `reward.py:374-382` requires `any(dead)` — an enemy princess actually down. So:

- **Enemy princess DOWN:** pocket overrides placement wholesale to board y **0.391**
  (`config.yaml:1373`), the ENEMY half. The lane/lock/depth chain never runs.
- **No princess down:** the chain runs — but for a bow at 0.61 all three assists hit `cy >=
  defense_y` and return `None`, leaving the cell unchanged.

**Therefore commit 11c6e2f (the O22 `enemy_alive=` argument on `xbow_lock_cell`) cannot change the
placement of a bow at 0.61 in either branch.** In the branch where a tower is down, the pocket
pre-empts it; in the branch where none is down, `xbow_lock_cell` returns None before reaching the
aliveness filter. It is correct code and its 26 tests pass, but it is (b) **probably inert on the
live path** for the bows the model actually plays. Needs live confirmation (see §5).

## 5. Tower state DOES gate placement — and it points the WRONG WAY for the owner's doctrine

Contrary to my earlier note that nothing consumes `TowerTracker` for placement, three paths do:

1. `play.py:1084-1091` `xbow_pocket_cell(tower_tracker.enemy_alive, ...)` — **overrides placement
   to the enemy half (board y 0.391) once an enemy princess is down**; `xbow_pocket_after_tower:
   true` (`config.yaml:1371`), enabled. Also narrows the deploy mask (`reward.py:385`).
2. `play.py:1101-1102` `xbow_target_lane_cell(..., tower_tracker.enemy_alive, ...)` — moves a bow
   off a dead lane (`reward.py:453-458`) and concentrates on the weaker tower by HP
   (`reward.py:460-465`, `hp_margin` 0.10).
3. `play.py:1109-1110` `xbow_lock_cell(..., enemy_alive=...)` — the O22 argument.

Other `tower_tracker` consumers, none of them X-Bow placement: `play.py:1062-1063`
(`pump_rocket_cell`), `:1065-1066` (`weaker_princess_cell`), `:915-916` (spell mask), `:550`/`:559`
(detector priors), `:657-660`, `:672-682`, `:739`, `:835-838`, `:980`, `:793`, `:1286`.

**No crown-count or damage-lead gate on placement exists anywhere in the live path.** The only
score-like signal is per-tower HP in (2).

**The conflict (a, in code; the judgement is the owner's).** The owner's doctrine is *"if it's
ahead on towers, it should defend until the match ends."* Path (1) does the opposite: in exactly
that state — an enemy princess down — the assist takes the model's cell and pushes the X-Bow
**forward into the enemy half**. It is a pro-derived play (`config.yaml:1371` cites pros at 25%
forward), so this is a genuine doctrine conflict, not a bug, and the owner must decide which wins.

### §6 **LEAD, measured** — the pocket DOES execute live, but only twice in the whole archive

Scanned all 19 `scratchpad/gauntlet/L67/live_run*_utf8.log`. `[assist] XBOW pocket` appears
**exactly 2 times, both in live_run18**, and both in precisely the 1-0 state:

    [assist] XBOW pocket cell 254->177 side right enemy_alive [True, False, True]  wall=15:24:45
    [assist] XBOW pocket cell 267->164 side left  enemy_alive [False, True, True]  wall=15:36:54

`enemy_alive` is `[princess_left, princess_right, king]`, so each firing had one enemy princess
down and the chosen side matches the dead tower — the mechanism works as designed. Every other
recorded run: **0 firings.** For scale, O21 counted 11 actual bow plays in run18, so roughly 2 of
11 bows in that one run were pocketed; `[assist]` lines of all kinds total 93 across the archive.

**This weakens my own §5 hypothesis (b → mostly (c)).** Two firings in the entire archive cannot
explain the owner's report of repeatedly *"playing much further forwards during overtime"*. The
pocket is a real doctrine conflict that genuinely executes, but it is far too rare to be the
mechanism behind the behaviour he watched. The cause of the forward overtime play is still
**unknown and unmeasured** — and still unrecordable until a live session is captured.

## What this does NOT establish
Why the model plays forward in overtime — the pocket is now largely ruled out as the explanation by
its own rarity. Whether 11c6e2f is inert *in practice*, as opposed to by code reading and by the
absence of any log line showing the lane/lock chain repositioning a bow. Anything about the session
the owner watched — still unrecorded. Whether the pocket is rare because the 1-0 state is rare at
X-Bow time, or because `_xbow_pocket_on`/state was off in the older runs — not separated.

STATUS: complete
