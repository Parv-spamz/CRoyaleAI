# O22 -- X-Bow dead-lane defect on the live path

## Defect (confirmed by reading, not just the ticket's claim)
play.py:1101-1109 (pre-fix): `xbow_target_lane_cell` moves an offensive bow OFF a dead lane, but
the very next call, `xbow_lock_cell(cx, cy, tower_tracker.enemy_a, xbow_range, xbow_live_defense_y,
actions)`, ran unconditionally with no aliveness argument at all (reward.py:469 pre-fix signature
had 5 positional params, no `enemy_alive`). It snapped to `min(princesses, key=lambda a:
abs(a[0]-cx))` -- the nearer of BOTH princesses, dead or alive -- so it could re-cement the bow
into the dead lane the previous line just corrected out of. Verified: env.py:1891-1908 (the
training sim, untouched, out of write set) has the identical two-call pattern and the identical
gap -- this is a real, structural defect in the shared assist, not a live-path-only slip. Fixing
`xbow_lock_cell` itself (with a default-None-preserves-HEAD kwarg) is therefore the right minimal
fix; only play.py was told to actually pass the new argument, so env.py/the training sim is
unaffected on purpose, per the ticket's write set.

## Fix
- `icebow/src/clashrl/reward.py`: `xbow_lock_cell` gained one optional kwarg, `enemy_alive=None`.
  - `None` (default): filtering is skipped entirely -- the `princesses` list and every line below
    it run byte-for-byte as before. This is the exact code path every other caller still takes.
  - A sequence: princesses are filtered to only the alive ones (missing entries pad as alive, same
    convention as the sibling `xbow_target_lane_cell`) BEFORE the existing range/nearest-lane logic
    runs unchanged. One alive -> that's the only candidate, so "nearest" trivially picks it. Zero
    alive -> the candidate list is empty and the function's existing `if not princesses: return
    None` fires -- the model's own cell is left alone, never redirected toward the king (the king
    anchor is never in `enemy_anchors[:2]` in the first place, so it was never reachable anyway).
    Two alive -> identical to the None path.
- `icebow/src/clashrl/play.py:1107-1109`: the live call now passes
  `enemy_alive=tower_tracker.enemy_alive`.

## Order-problem reasoning (ticket 2c) + proof
Could the lock, once filtered, ever move the bow back into the dead lane after the lane-fix moved
it out? No: with `enemy_alive` passed, the dead lane's anchor is removed from the candidate list
BEFORE the nearest-lane pick runs, so it can never be selected by "nearest" or any other branch --
there is nothing left to snap back to. Proved directly in
`icebow/tests/test_xbow_lane.py::XbowLockDeadLaneTests::test_the_play_sequence_lane_fix_then_lock_stays_in_the_live_lane`,
which replays play.py's exact two calls in order (lane-fix cell -> recompute cx,cy -> lock with a
deliberately tiny range so it is FORCED to re-snap) and asserts the final cell is still in the live
lane.

## Mapping check (ticket item 6)
`TowerTracker.__init__` (reward.py:653-657): `self.mine_a, self.enemy_a, self.thr = _anchors(cfg)`
then `self.enemy_alive = [True] * len(self.enemy_a)`, and `_update_side(frame, self.enemy_a,
self.enemy_alive, ...)` (reward.py:681) updates both in lockstep by the same index. So
`enemy_alive[i]` corresponds to `enemy_a[i]` (index 0 = left princess, 1 = right, 2 = king) --
matching order to `enemy_anchors[:2]` in both `xbow_target_lane_cell` (already relied on this) and
the new filtering in `xbow_lock_cell`. No mismatch; proceeded without stopping for NEEDS_CONTEXT.

## Every other caller of `xbow_lock_cell`, enumerated
- `icebow/src/clashrl/env.py:1906` -- `xbow_lock_cell(cx, cy, enemy_a, self.xbow_range,
  self.xbow_defense_front, self.actions)` -- 5 positional args, `enemy_alive` not passed -> hits
  the default `None` -> byte-identical to HEAD. Not edited (forbidden by write set; also confirms
  the training sim keeps today's exact behaviour, unaffected by this ticket).
- `icebow/tests/test_xbow_live_depth.py:49` -- direct call, 6 positional args, no `enemy_alive` ->
  default `None` -> unaffected, still passes.
- `icebow/tests/test_xbow_pocket.py:67` -- only checks the substring `"xbow_lock_cell("` is present
  in play.py's source; unaffected either way.
- `hogeq/src/clashrl/{reward,play}.py`, `hogeq/tests/test_xbow_*` -- a separate project tree, not
  `icebow`, out of the ticket's write set and not touched. It has the same unfixed defect but is
  explicitly not in scope.
- `scratchpad/gauntlet/L59/_head/**`, `scratchpad/gauntlet/L67/opp_fix/play_o19_wip.py`,
  `scratchpad/gauntlet/L67/opp_fix/backup/*.orig` -- old snapshots/backups, not live code, not
  imported by anything.

## KNOWN REGRESSION (not fixed -- outside the write set)
`icebow/tests/test_xbow_live_depth.py::test_play_passes_the_live_cut_to_all_three_assists` now
FAILS. It hardcodes an exact source substring,
`"xbow_lock_cell(cx, cy, tower_tracker.enemy_a, xbow_range, xbow_live_defense_y, actions)"`,
checked with `assertIn` against play.py's raw text. Any new argument to that call -- which the
ticket explicitly required -- makes this literal substring stop matching (the call no longer ends
`actions)`; it now ends `actions,\n                                     enemy_alive=tower_tracker.enemy_alive)`).
There is no way to add the required argument and keep that literal substring intact. This test
file is not in O22's write set, so it was not edited. Confirmed by running it (see below).

## Tests
Command: `icebow/.venv/Scripts/python.exe -m unittest icebow.tests.test_xbow_lane -v`
Result: **17 passed, 0 failed** (10 pre-existing `XbowLaneTests` unchanged and green; 7 new
`XbowLockDeadLaneTests` added covering: both-alive == default-None on two cases (in-range and
out-of-range), nearer-dead/farther-alive snaps to the farther lane (with the pre-fix buggy
behaviour also asserted as a precondition, proving the defect existed), both-dead returns None
(never aims at the king), the full lane-fix-then-lock sequence stays in the live lane, and a
defensive bow (cy >= defense_y) still returns None with `enemy_alive` passed).

Sanity/regression run: `icebow/.venv/Scripts/python.exe -m unittest icebow.tests.test_xbow_pocket
icebow.tests.test_xbow_live_depth -v` -> 8 passed, 1 failed (the known regression above, in a file
outside the write set).

`git diff --stat` (scoped to write set): `icebow/src/clashrl/play.py | 5 ++-`,
`icebow/src/clashrl/reward.py | 16 +++++++-`, `icebow/tests/test_xbow_lane.py | 86 +++...`. Full
repo `git diff --stat` additionally shows only the scratchpad files that were ALREADY modified in
the working tree before this ticket started (per the session's initial git-status snapshot,
L64/L67 `.out`/`.json`/`pids.txt` scratch files) -- none of them touched by this work.

Backups (`scratchpad/gauntlet/L67/opp_fix/backup/{reward,play,test_xbow_lane}.py.o22.orig`) verified
byte-identical to `git show HEAD:<path>` (compared with CRLF/LF normalized, since Windows checkout
uses CRLF and `git show` emits the LF-normalized blob -- content matches).

## What changes on the live path, exactly
On `play.py`'s in-match X-Bow placement only: after the dead-lane rule (`xbow_target_lane_cell`)
already moves an offensive bow to the lane with a live tower, the subsequent range-lock
(`xbow_lock_cell`) can no longer consider the dead tower's lane as a snap target -- it either keeps
the live-lane placement (in range) or re-centers within that same live lane (out of range). It can
never re-snap the bow back onto a destroyed tower's lane, and if both towers are down it leaves the
model's own cell alone rather than aiming at the king. `env.py`'s training sim, `config.yaml`,
`student_live.py`, and every other caller of `xbow_lock_cell` are byte-identical to HEAD because
the new parameter defaults to `None` and only play.py's live call passes it.

## Exact revert
No commits were made. To discard everything from this ticket:
```
git checkout -- icebow/src/clashrl/reward.py icebow/src/clashrl/play.py icebow/tests/test_xbow_lane.py
```
(equivalently, copy back `scratchpad/gauntlet/L67/opp_fix/backup/{reward,play,test_xbow_lane}.py.o22.orig`
over the three files).

## Attempt 2

Repair authorised by the coordinator: `icebow/tests/test_xbow_live_depth.py` added to the write
set for the sole purpose of fixing the regression flagged in Attempt 1.

Backup taken first: `scratchpad/gauntlet/L67/opp_fix/backup/test_xbow_live_depth.py.o22.orig`,
verified identical to `git show HEAD:icebow/tests/test_xbow_live_depth.py` (CRLF/LF-normalized).

`test_play_passes_the_live_cut_to_all_three_assists` no longer does `assertIn()` on the three
assist calls' literal source text. It now `ast.parse`s play.py, finds each `Call` node whose
function name is `xbow_target_lane_cell` / `xbow_lock_cell` / `xbow_offense_depth_cell`, and checks
by argument NAME (positional or keyword, walking `call.args` + `call.keywords`) that
`xbow_live_defense_y` is among the arguments and `xbow_defense_front` is not. This asserts the
actual behaviour the test exists to protect (the live cut reaches all three assists) rather than a
frozen spelling of the call, so it will not re-break the next time a signature gains/loses/reorders
an argument -- only dropping the live cut or reintroducing the stale global default fails it now.
Comment in the test file explains why the literal pin was replaced (O22 legitimately added
`enemy_alive=...` to the `xbow_lock_cell` call in this same ticket).

reward.py and play.py are UNCHANGED from Attempt 1 (only the test file was touched this round);
re-confirmed the `xbow_lock_cell` default-`None` path is still byte-identical whether `enemy_alive`
is omitted or passed explicitly as `None`.

### Other source-text-pinned assertions noticed (listed only, not fixed -- out of this ticket's scope)
- In the write-set files touched here: none remain in `test_xbow_live_depth.py` after this repair;
  no other test in `test_xbow_lane.py` reads source text.
- Outside the write set, seen while exploring in Attempt 1: `icebow/tests/test_xbow_pocket.py`
  (`test_play_tries_the_pocket_before_the_defensive_assists`, ~line 64-70) reads play.py's raw
  source and does `src.index("xbow_pocket_cell(tower_tracker.enemy_alive")` /
  `src.index("elif card_id in xbow_ids:")` / `assertIn('_xbow_pocket["side"] = None', src)` --
  the same brittle-to-cosmetic-change pattern (ordering-by-literal-substring-position and an
  assignment's exact spelling) that could instead assert on parsed structure or on the pocket
  assist's actual observed behaviour. Not touched: it currently passes and is not in this
  ticket's write set.

### Acceptance run
Command: `icebow/.venv/Scripts/python.exe -m unittest icebow.tests.test_xbow_lane
icebow.tests.test_xbow_live_depth icebow.tests.test_xbow_pocket -v`
Result: **26 passed, 0 failed** (17 from test_xbow_lane + 3 from test_xbow_live_depth + 6 from
test_xbow_pocket).

`git diff --stat` scoped to the write set: exactly 4 files -- `icebow/src/clashrl/play.py` (5+),
`icebow/src/clashrl/reward.py` (16+), `icebow/tests/test_xbow_lane.py` (86+),
`icebow/tests/test_xbow_live_depth.py` (45+). Full-repo `git diff --stat` additionally lists only
the scratchpad files that were already modified before this ticket started (per the session's
initial git-status snapshot); none touched by this work. No commits made. Engine was not booted or
touched (unit tests only).

STATUS: complete
