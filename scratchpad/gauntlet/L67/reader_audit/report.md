# Live reader audit -- HP bars + velocity

Command: `python tools/live_reader_audit.py data/sessions/20260912_152220 ../scratchpad/gauntlet/L67/live_run18_utf8.log --out ../scratchpad/gauntlet/L67/reader_audit --max-minutes 18 --hz 5 --crops 30 --seed 0`

Processed 3650 in-match frames (3650/3950 state-checked frames were `vision.detect_state == IN_MATCH`) at 4.00 Hz (9628 detections) in 446s. Stop reason: completed the session.

## HP-bar fraction reader (`detect_obs.read_hp_frac`)

A read counts as "found" when the function returns anything other than its own 1.0 no-bar-found sentinel (see Limitations -- this conflates a genuinely full-health bar with no bar at all, which is rare because the game itself draws no bar on an undamaged unit).

- **Read rate, all detections:** 3.6% (n=9628)
- **By team:**
    - enemy: 2.6% (n=5264)
    - mine: 4.8% (n=4301)
    - unknown: 3.2% (n=63)
- **By class (top 10 by detection count):**
    - knight: 5.4% (n=1604)
    - skeletons: 2.0% (n=1105)
    - tesla: 3.4% (n=817)
    - x_bow: 7.3% (n=735)
    - the_log: 2.8% (n=462)
    - skeleton_dragons: 3.7% (n=374)
    - royal_recruits: 1.2% (n=245)
    - lava_hound: 9.4% (n=234)
    - earthquake: 0.0% (n=225)
    - bats: 4.3% (n=209)
- **Read rate, by TRACK (>=1 found read over the track's life):** 22.7% (n_tracks=643, min_hits=2)
    - enemy: 16.2% (n_tracks=402)
    - mine: 34.0% (n_tracks=238)
    - unknown: 0.0% (n_tracks=3)

- **At-deploy check** (our own PLAY -> matching own unit within 1.5s / 0.15 normalized-frame radius of the tap point):
    - plays in the processed window: 166, matched: 112, no own unit seen: 54
    - first HP read -- median: 1.000, share >= 0.90: 97.3%, share < 0.70: 0.9%
- **Monotonicity** (consecutive found-reads on the same track, share that INCREASE by more than 0.10): 20.2% (n_pairs=178)
- **Jitter** (median |diff| between consecutive found-reads ~0.2s apart): 0.000 (n_pairs=51)

## Velocity reader (`TeamTracker` per-track positions)

- **Share of tracks old enough to report a velocity** (age >= 0.5s): 89.0% (n_tracks=643)
- **Direction stability** (median |angle change| between consecutive ALREADY-MOVING >= 0.15 tiles/s velocity estimates on the same track): 43.7 deg (n_segment_pairs=5365)

- **Per-class measured speed vs `cards_stats.json.speed_tiles`** (straight [<30 deg heading change] and moving [>=0.15 tiles/s] segments only, n >= 8):

| class | n | median tiles/s | p25-p75 | card speed_tiles (tiles/s) | ratio |
|---|---|---|---|---|---|
| skeletons | 503 | 1.76 | 1.51-1.96 | 1.5 | 1.176 |
| knight | 487 | 1.19 | 0.89-1.53 | 1.0 | 1.187 |
| the_log | 197 | 3.59 | 3.13-3.99 | None | n/a |
| royal_recruits | 115 | 1.14 | 0.86-1.43 | 1.0 | 1.144 |
| night_witch | 98 | 1.20 | 0.96-1.44 | 1.0 | 1.200 |
| bomber | 89 | 1.18 | 0.82-1.62 | 1.0 | 1.179 |
| firecracker | 73 | 1.73 | 1.57-2.01 | 1.5 | 1.152 |
| tesla | 72 | 0.41 | 0.25-0.90 | None | n/a |
| bats | 72 | 2.28 | 1.86-2.75 | 2.0 | 1.139 |
| x_bow | 59 | 0.30 | 0.21-0.37 | None | n/a |
| balloon | 54 | 1.15 | 0.83-1.32 | 1.0 | 1.151 |
| skeleton_dragons | 53 | 1.49 | 0.62-2.34 | 1.5 | 0.994 |
| battle_ram | 49 | 1.37 | 1.00-2.34 | 1.0 | 1.366 |
| lava_hound | 40 | 1.03 | 0.70-1.27 | 0.75 | 1.376 |
| goblin_giant | 35 | 1.50 | 0.74-2.30 | 1.0 | 1.501 |
| golem | 35 | 0.77 | 0.51-1.20 | 0.75 | 1.023 |
| mega_knight | 33 | 1.57 | 0.67-2.53 | 1.0 | 1.568 |
| phoenix | 33 | 1.30 | 1.03-1.79 | 1.0 | 1.297 |
| prince | 33 | 2.01 | 1.68-2.69 | 1.0 | 2.007 |
| guards | 28 | 1.63 | 1.14-2.10 | 1.5 | 1.085 |
| electro_wizard | 24 | 1.91 | 1.24-2.22 | 1.5 | 1.276 |
| lumberjack | 23 | 2.28 | 1.89-2.73 | 2.0 | 1.141 |
| elixir_golemite | 22 | 1.18 | 0.84-1.41 | 1.0 | 1.181 |
| royal_recruit | 21 | 1.19 | 1.08-1.30 | None | n/a |
| elixir_golem | 16 | 0.71 | 0.44-1.00 | 0.75 | 0.951 |
| dark_prince | 16 | 1.63 | 1.05-2.30 | 1.0 | 1.633 |
| lava_pups | 11 | 1.13 | 0.91-1.49 | 1.0 | 1.130 |
| goblin_demolisher | 10 | 1.16 | 1.03-1.23 | 1.0 | 1.162 |
| golden_knight | 10 | 1.17 | 0.89-1.35 | 1.0 | 1.171 |
| baby_dragon | 10 | 1.61 | 1.00-2.09 | 1.5 | 1.073 |
| earthquake | 9 | 0.29 | 0.22-0.32 | None | n/a |
| ice_wizard | 9 | 1.21 | 1.13-1.56 | 1.0 | 1.206 |
| witch | 9 | 1.09 | 1.04-1.23 | 1.0 | 1.088 |
| elixir_blob | 8 | 0.95 | 0.49-1.65 | 1.5 | 0.636 |
| rage | 8 | 0.42 | 0.20-0.92 | None | n/a |

## Limitations -- what each check is a proxy for, and what it cannot see

- **No ground truth exists on the live screen.** Every number above is a self-consistency check against a game rule (own-play identity, no-heal monotonicity, a published speed constant), not a comparison to a labelled frame. A reader that is wrong in a way consistent with these rules would pass undetected.
- **HP "found" is a proxy.** `read_hp_frac` returns exactly `1.0` both when no bar exists (undamaged unit -- the common, correct case) and, in principle, when a bar is found completely full. The read-rate numbers here treat every `1.0` as "not found"; since the game itself draws no bar on a full-health unit, this should be a small underestimate of the true found-rate, not a large one, but it is not exact.
- **The at-deploy check needs the detector to see the unit at all.** A play with no own-unit match in the window is counted as `unmatched_no_own_unit_seen`, which mixes two different failures -- the detector missing a real, correctly-undamaged unit, and the placement/track-matching radius being too tight/wide -- into one number.
- **Monotonicity and jitter only run on tracks the detector re-acquires**, i.e. units that survive long enough with a HIT-count >= the tracker's own `min_hits` and get re-detected close enough in time (jitter needs a ~0.2s-spaced pair, dropped reads widen that gap and the pair is simply excluded, not counted as noise). A reader that is stably WRONG (a constant offset) is invisible to both checks.
- **Velocity uses the SAME anisotropic TILE_X/TILE_Y linear approximation `hero_ability.py` already uses** (a flat tiles-per-normalized-frame-unit scale); it ignores the perspective warp `actions.BoardWarp` corrects for taps, so speeds near the top/bottom of the arena (foreshortened by the camera) are somewhat over/under-stated versus the middle. This audit does not attempt the warp correction, so the same bias sits in every number here.
- **The "straight, moving" filter is a heuristic** (thresholds listed above), tuned by inspection, not measured against a labelled trajectory; a card whose typical play pattern is mostly turning (kiting, pathing around a building) will under-sample here, not because the reader is wrong but because few of its segments qualify as "straight".
- **No live tower-HP reader is run offline.** `TeamTracker.set_towers` is fed "all towers alive" for the whole session (matching `tools/detector_audit.py`'s own documented simplification), so the deploy-pocket side-prior (evidence rank 4) is slightly more permissive here than in a real match with a fallen tower. This cannot affect the at-deploy check, which relies only on the rank-1 own-play anchor.
- **The detector's own recall/precision is a separate, unmeasured variable here.** A unit the detector never boxes contributes zero evidence to every check above; none of these numbers say anything about units the detector missed entirely.
