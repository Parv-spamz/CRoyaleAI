# V12 — blind verification of O12 (TeamTracker zone team rule) — LEAD TRANSCRIPTION

NOTE: the verifier role does not write to the tree; this is the lead's transcription of its hand-back
(2026-09-16). Verdict on attempt 1: **PASS_WITH_NOTES**. Attempt 2 requested for F1 (below).

| # | criterion | verdict | evidence (verifier's) |
|---|---|---|---|
| 1 | diff scope | PASS | 4 hunks in replay_mine.py: vocab import (:51-56), `ZONE_CLASSES = vocab.AOE_CLASSES` (:263), a comment (:442-443), new `elif trk["rank"] > 1 and d.cls in self.ZONE_CLASSES` (:451-460). `_verdict` (:381-410) and `_claim` untouched. AOE_CLASSES = the 20 `_aoe` names (vocab.py:83); no troop/building class. |
| 2 | tests | PASS | 5 passed. Test (iii) reuses test_team_veto.py's knight fixture, asserting the pre-change literal — real but covers one rung only. |
| 3 | old vs new one-offs | PASS | (a) anchored poison_aoe: mine/mine. (b) unanchored mid-board: old unknown, new enemy. (c) unanchored deep in MY half: **old 'mine'** (side-prior rung), new enemy. (d) knight ×6 scenarios: identical. (e) stickiness: new stays enemy. |
| 4 | hogeq / backups | PASS | hogeq byte-identical (modulo CR); backups == 64d7eca. |
| 5 | downstream | PASS | estimator via play.py:547/558; S1 via play.py:900 -> student_live.py:141 -> obs_contract.py:459-463 (spell tokens carry the tracker's team). |
| 6 | whitelist diff | PASS | applies clean, not applied; adds exactly poison, graveyard, rage, freeze, earthquake, tornado to both configs; costs 4/5/2/4/3/3. |
| 7 | pre-existing failure | PASS | test_xbow_into_push::test_the_clamped_frontmost_ROW_counts_as_forward fails on the backup too (0.5625 >= 0.625); imports never touch replay_mine. |

## Findings
- **F1 (medium) — closed in attempt 2:** an OWN zone whose anchor misses (0.15 from the tap vs spawn_radius 0.10; or seen 3.0 s after the play vs window 2.5 s) became 'enemy' at rank 1 for the track's life: S1 sees my tornado (icebow) / earthquake (hogeq) as the opponent's, and once whitelisted it bills the opponent. Fix: deck-owned unanchored zones keep the old path; non-deck zones -> enemy; zone-specific anchor radius/window.
- F2 (low): the card-art class `poison` and `poison_aoe` share one track (link on base); the zone rule can override a rank-4 verdict on an art-first track.
- F3 (info): import-time `sys.path` insertion in a live-path module; precedent student_live.py:27-31.
- **F4 (info, important):** what the live model SEES changes as soon as this commits, whitelist or not: unanchored non-deck zones mid-board go from side -1 (unknown) to 1 (enemy); deep in my half from 0 (wrong, side prior) to 1. The estimator is unaffected until whitelist_zones.diff is applied.

## Attempt 2 (deck guard + zone anchor tolerance) — PASS_WITH_NOTES
- Shared path: `_plays` prune widened to max(window, 3.5 s) (:433-435) — retains more, never less; the anchor test (:470-474) re-applies the exact old radius/window per det for non-zone classes. Only two readers of `_plays` exist (prune, anchor). Ten troop/building scenarios old vs new: identical (knight 0.14 off, 0.09 off, @3.0 s, @2.4 s, multi-tag 1.0/2.6/3.0/3.6 s, enemy-half windows, baseless play, tesla-lookalike rescue).
- Deck guard (:479-481, `own_cards`): deck-owned unanchored tornado_aoe -> old-path verdict (unknown mid-board; 'mine' deep in my half = the pre-O12 side-prior result). Non-deck poison_aoe -> enemy.
- Zone anchor 0.16 / 3.5 s (:239-240): own tornado_aoe 0.14 off @0.3 s -> mine (old unknown); @3.2 s -> mine; @4.0 s -> old path. Earlier F1 (i)/(j) now resolve 'mine'; (k) resolves exactly as pre-O12.
- Tests: zone 12, team_veto 10, side_and_lookalikes 15 — all pass. hogeq identical; configs untouched.
- **N1 (accepted trade-off):** live callers pass `own_cards`, so the enemy-default NEVER fires for a deck-owned zone spell (icebow: tornado; hogeq: earthquake). The pre-O12 "enemy zone deep in my half reads mine" bug persists for those only. The gain is confined to non-deck zones (mid-board unknown -> enemy).
- N2: with `own_cards=None` (monitor overlay, offline tools) the default fires — not a live path.
- N3: shared-path equivalence assumes monotonic `t` (both live callers pass time.time()).
- **Untested (b):** the 0.16 / 3.5 s constants have no real-frame measurement behind them.

STATUS: complete (lead transcription)
