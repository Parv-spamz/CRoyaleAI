# O12 -- bill opponent SPELL ZONES (TeamTracker), progress

## 0. Prerequisite check (BLOCKING NOTE, not a stop)
`scratchpad/gauntlet/L67/opp_fix/S8_spells.md` (the "read first" scout doc the ticket names) DOES
NOT EXIST -- `opp_fix/` was empty before this run. Proceeded on the ticket's own inline CONTEXT
(section 1) instead, independently re-verifying every citation it gives against the live source
(below) rather than trusting the ticket's prose. Flagging this as a concern in the hand-back: the
ticket implies a richer scout doc exists with more citations than what's in section 1.

## 1. Citation verification (against HEAD c5e4e1a)
- play.py:547 -- `dets = [d for d in dets_all if d.team == "enemy" and d.base in detector_cards]`
  CONFIRMED verbatim.
- opponent_elixir.py:94 -- `if getattr(d, "team", None) != "enemy": continue` CONFIRMED (estimator
  only bills d.team == "enemy" exactly; "unknown" or "mine" are silently dropped).
- pipeline/vocab.py -- `AOE_CLASSES` (line 83) = the 20 `_aoe` ground-effect classes, and
  `base_key` (110-120) strips `_aoe` along with `_evo/_hero/_ability`. CONFIRMED. Used
  `vocab.AOE_CLASSES` directly rather than re-deriving "ends with _aoe" by hand.
- replay_mine.py `_verdict` (364-393) CONFIRMED as cited.

## 2. Correction to the ticket's diagnosis (measured, not assumed)
Ran the actual pre-patch code (`icebow/.venv/Scripts/python.exe`) against 4 cases before touching
anything, because the ticket's blanket claim ("every rung of the ladder fails for zones, so they
are never billed") does not hold rung-by-rung:

| case | pre-patch verdict | matches ticket's claim? |
|---|---|---|
| poison_aoe near my own poison play | "mine" (rank 1, own-play anchor) | the anchor ALREADY covers zones -- `d.base` already strips `_aoe`, so `record_play(base="poison")` already matches a `poison_aoe` det. No anchor change needed. |
| poison_aoe, no anchor, mid-board | "unknown" | matches |
| poison_aoe, no anchor, deep in ENEMY half | **"enemy"** (side prior, rank 4) | CONTRADICTS "every rung fails" -- rung 4 already gets this one right by luck of geometry |
| poison_aoe, no anchor, deep in MY half | **"mine"** (side prior, rank 4) | worse than "never billed": this is a live bug -- an enemy zone landing on MY tower reads as OURS (the mirror of the earthquake-on-our-tower bug `test_team_veto.py` already documents for troops), and is invisible to the deck veto whenever the spell IS in our own deck |

So "zones are never billed" is imprecise: they are billed inconsistently, and the worst case
(enemy zone on my half) was silently miscounted as MINE, not "unknown". The rule specified in
section 2a of the ticket (anchor->mine, else->enemy, skip the ladder) fixes this correctly anyway
as a side effect, so I implemented it as specified. Noting this because "the diagnosis is close
but not exactly what's claimed" per the disagreement policy -- the fix is right, the stated reason
for rungs 2-4 failing generically is only half true.

## 3. Design (no new geometry constants)
`R` and the time window are NOT reinvented -- the existing own-play anchor block in `tag()`
(lines ~424-431, unchanged) already runs for every class including zones, because `Detection.base`
already strips `_aoe`. That block already handles case (i). What's missing is only the "else"
path: instead of falling into `_verdict()`'s ladder (which can return "unknown" OR the wrong "mine"
for zones, per section 2 above), zone classes now go straight to "enemy" when the anchor did not
match, at rank 1 (not 9/"unknown") so a LATER own play near the same track cannot reopen the
anchor branch (which gates on `trk["rank"] > 1`) and flip it. Rank 1 is reused, not invented, for
exactly that gate.

Zone-class membership: `pipeline.vocab.AOE_CLASSES` (imported the same way
`icebow/src/clashrl/student_live.py` already imports `pipeline.vocab`: resolve repo root via
`Path(__file__).resolve().parents[3]`, sys.path insert, `from pipeline import vocab`).

## 4. Files changed
- `icebow/src/clashrl/replay_mine.py` -- TeamTracker: zone-class import + one `elif` branch in
  `tag()`. Troop/building path (`_verdict`, the `if`/`else` around it) untouched.
- `hogeq/src/clashrl/replay_mine.py` -- confirmed byte-identical to icebow's before editing
  (`diff`/`cmp` both exit 0, see backups); same edit mirrored.
- `icebow/tests/test_zone_team_billing.py` -- new, 4 tests per ticket 2b.

## 5. Test run
- New tests: `pytest icebow/tests/test_zone_team_billing.py -v` -> 5 passed, 0 failed.
- Full `icebow/tests` suite, BEFORE (backup replay_mine.py, new test file moved out):
  `1 failed, 1408 passed, 21 skipped, 517 subtests passed in 397.79s`
  (failure: test_xbow_into_push.py::test_the_clamped_frontmost_ROW_counts_as_forward -- an
  xbow_front/placement-clamp assertion, nothing to do with TeamTracker/replay_mine.py; confirmed
  pre-existing by running it standalone against the untouched backup file).
- Full `icebow/tests` suite, AFTER (edit + new test file in place):
  `1 failed, 1413 passed, 21 skipped, 517 subtests passed in 416.99s`
  Same single failure, same skip count; the +5 passed is exactly the new test file. NO regressions.
- Files swapped back to the edited state and re-verified afterward (`diff --strip-trailing-cr`
  icebow vs hogeq replay_mine.py -> identical; `git diff --stat` -> only the two replay_mine.py).

## 6. Prepared config diff
`scratchpad/gauntlet/L67/opp_fix/whitelist_zones.diff` -- built by temporarily editing
icebow/config/config.yaml and hogeq/config/config.yaml, capturing `git diff` for exactly those
two files, then `git checkout --` to revert (confirmed clean both before and after via
`git status --porcelain`). `git apply --check` on the saved file returns success; `git status`
on the two config files stays empty after the check (dry run only, nothing applied).
Zone spells included (verified `_aoe` class in vocab.AOE_CLASSES + elixir cost in
icebow/config/cards_stats.json "cards" for all six): poison, graveyard, rage, freeze,
earthquake, tornado. None of the 9 instant spells were added.

## 7. S8_spells.md appeared mid-task (was empty at start, see section 0)
A lead-transcribed version materialized in opp_fix/ partway through this run (a scout agent
apparently cannot write files; the lead transcribed its hand-back). Cross-checked against my own
independent measurements:
- Matches: AOE class list, play.py:547 base_key mechanics, opponent_elixir.py:94, forget_s/
  match_radius, hogeq detector_cards identical to icebow's.
- One error caught in it: its elixir table buckets `rage` at cost 3 ("tornado, arrows,
  goblin_barrel, giant_snowball, rage, void, vines, goblin_curse 3"). Direct read of
  icebow/config/cards_stats.json says `rage.elixir == 2` (also the real game's cost). Did not
  rely on the scout's table for anything -- read cards_stats.json directly for section 2c --
  so this did not affect the implementation, but it is a caught inaccuracy worth flagging.
- Its §4 claim ("the ladder fails for zones ... -> unknown") is the same generalisation the
  ticket makes and is imprecise in the same way: see section 2 above (rung 4 side-prior actually
  fires, sometimes right, sometimes wrong, depending on board half; it is not a uniform "unknown").

STATUS: complete (attempt 1)

## Attempt 2 (F1 fix -- blind verifier's live-risk note)

### Finding F1 (verifier, reproduced)
Confirmed before touching code: attempt 1's zone rule was "no anchor -> enemy, sticky" with NO
account for MY OWN unrecognised zone. Reproduced the exact failure modes named:
- a zone detected 0.15 from the tap (spawn_radius is 0.10) -- outside the troop anchor radius.
- a zone first seen 3.0 s after the play (spawn_window_s is 2.5) -- outside the troop anchor window.
Both cases: attempt-1 code forced 'enemy' at rank 1 (sticky for the track's life) for MY OWN
tornado/earthquake. The pre-O12 code gave 'unknown' there instead (safe, if useless to the
estimator) -- so attempt 1 was strictly worse for this case, exactly as the verifier said.

### CHANGE 1 -- deck guard
`icebow/src/clashrl/replay_mine.py` `TeamTracker.tag()`: the zone-default elif now also requires
`not (self.own_cards is not None and d.base in self.own_cards)`. `self.own_cards` is the SAME
deck attribute `_claim`'s deck veto already reads (see its docstring, "DECK VETO" comment, and
`__init__`'s `self.own_cards = frozenset(...) if own_cards else None`). When the zone's base IS
ours, the elif is skipped and the det falls through to the unchanged `else: self._verdict(d, trk)`
branch -- i.e. exactly the pre-O12 code path, since `_verdict` was never modified by O12. When
`own_cards` is None (deck unknown -- offline tools / the monitor overlay), there is no positive
evidence the zone is ours, so the enemy default still applies (unchanged from attempt 1).

### CHANGE 2 -- zone anchor tolerance
New module-level constants (next to the existing `SPAWN_SPELLS` module constant, same style):
`ZONE_ANCHOR_RADIUS = 0.16`, `ZONE_ANCHOR_WINDOW_S = 3.5`. Used ONLY inside the OWN-PLAY ANCHOR
`if` test, and ONLY when `d.cls in self.ZONE_CLASSES`; a non-zone det still uses `sr2`
(`spawn_radius ** 2`) and the same per-play `enemy_window_s`/`spawn_window_s` split as before.
This DID require touching the shared anchor line (not a separate code path), because the radius
and the window test were previously baked into (a) a single `sr2` shared by every class and
(b) `_plays`' own pruning at the top of `tag()`, which runs once before the per-det loop and
therefore can't apply a wider window to zones only. Fix, kept minimal:
- top-of-`tag()` pruning now keeps the LONGER of a play's own window and `ZONE_ANCHOR_WINDOW_S`
  (`max(...)`) -- so a play a zone still needs is not dropped before the per-det check runs. This
  can only make `_plays` retain MORE entries than before, never fewer.
- the per-det anchor `if` now re-checks the WINDOW explicitly (`t - pt <= ...`) as well as the
  radius, branching on `is_zone`. For a troop this re-states exactly the same test the old code
  relied on implicit pruning to enforce -- verified equal to the pre-O12 module on the same input
  (see tests). For a zone it uses the wider radius/window.
This is a small, localized change (one conditional expression + one pruning line), not a
restructuring of the class, so NEEDS_CONTEXT was not needed.

### Tests added to `icebow/tests/test_zone_team_billing.py` (12 total, 5 kept from attempt 1 + 7 new)
- `TestZoneDeckGuard::test_a_deck_owned_zone_with_no_anchor_matches_the_old_module_exactly` --
  loads the attempt-1 backup (`backup/replay_mine.py.orig`) as a real module (via
  `importlib.util.spec_from_file_location` + an explicit `SourceFileLoader`, since the plain
  suffix-guessing form returns `None` for a `.py.orig` path; `sys.modules[name]` must be set
  BEFORE `exec_module` or the `@dataclass` on `Detection` fails resolving `from __future__ import
  annotations` postponed types) and asserts the new code's verdict equals the OLD module's for a
  deck-owned ('tornado' in `own_cards`), unanchored, mid-board `tornado_aoe` -- both 'unknown'.
- `test_a_non_deck_zone_with_no_anchor_is_still_enemy` / `test_stickiness_still_holds_for_the_non_deck_case`
  -- attempt 1's behaviour unchanged when the deck does not own the card.
- `TestZoneAnchorTolerance`: 0.14-offset zone -> mine (new tolerance); 0.14-offset KNIGHT compared
  live against the old module (both fall through, asserted equal, not hand-typed); 3.2 s zone ->
  mine; 4.0 s zone (past even the wider window) compared against the old module (both 'unknown').

### Test results
- `pytest icebow/tests/test_zone_team_billing.py -v` -> **12 passed** (was 5 in attempt 1).
- `pytest icebow/tests/test_team_veto.py icebow/tests/test_team_side_and_lookalikes.py -v` ->
  **25 passed**, 0 failed -- confirms troop/building anchor and ladder behaviour is byte-for-byte
  unchanged (per-test breakdown in the tool output; not re-pasted here).
- Did NOT re-run the full 7-minute suite per instruction.

### hogeq mirror
Confirmed `icebow/src/clashrl/replay_mine.py` and `hogeq/src/clashrl/replay_mine.py` were still
byte-identical (post attempt-1 mirror, pre attempt-2 edit) via `git diff --stat` on each
(hogeq: 29 insertions only, matching attempt 1's mirror exactly) before copying icebow's
attempt-2 file over hogeq's. Post-copy `diff --strip-trailing-cr` on the two -> identical (exit 0).

### Diff stat (my write set only)
`git diff --stat -- icebow/src/clashrl/replay_mine.py hogeq/src/clashrl/replay_mine.py` ->
both files, 75 insertions(+), 4 deletions(-) each (identical diffs).

### Unrelated concurrent change noticed -- NOT mine, NOT touched
`git diff --stat -- icebow hogeq` (repo-wide) also shows `icebow/src/clashrl/opponent_elixir.py`
with +293 lines. I did not open or edit this file at any point in either attempt (it is explicitly
out of my write set). This is almost certainly a DIFFERENT worker's concurrent edit (the "step 2"
re-billing fix the ticket references as in-progress) landing in the same working tree while I was
running. Flagging so the coordinator does not read the repo-wide diff as something I introduced.

STATUS: complete (attempt 2)
