# S7 scout — estimator API + engine-truth sources (LEAD TRANSCRIPTION)

NOTE: the foreman-scout returned these findings in its hand-back message but did NOT write this file
(§2.5 violation). Transcribed by the lead from the report on 2026-09-16, trimmed to the facts that were
acted on. Items marked (verified) were independently re-read by the lead in source.

## Estimator — icebow/src/clashrl/opponent_elixir.py:20-132 (hogeq copy byte-identical)
- `OpponentElixirEstimator(db, match_radius=0.07, cluster_radius=0.10, forget_s=6.0)`; radii in
  normalized-frame [0,1] units (0.07 ≈ 1.3 tiles on 18×32).
- `reset(my_elixir=5.0, now=None)`, `record_my_play(base)` (adds `db.elixir(base)` to `_my_spent`),
  `update(my_elixir, enemy_dets, now) -> float` (returns NORMALIZED [0,1]; `._est` is the 0-10 value
  play.py:884 actually reads).
- (verified) line 113: `est = my_elixir + my_spent - opp_spent` — the pure counting identity, NO
  regeneration model; `now` only ages tracks (forget_s). Single/double elixir is inherited from the
  caller's `my_elixir`.
- L67g saturation re-baselining (lines ~114-129): overflow past [0,10] is charged into `_opp_spent`.
- `update()` filters `enemy_dets` by `d.team == "enemy"` internally (per O8's read).
- Dets need `.base`, `.cx`, `.gy`, `.team`. No live-only dependencies.

## Live call sites — icebow/src/clashrl/play.py
- :400 construct with `CardDB(cfg)`; :1196 `reset(my_elixir=OCR, now=time.time())` at match start;
  :558 per-frame `update(float(my_elixir), dets, now)`; :1130 `record_my_play(base_key(...))` on our
  accepted plays; :884 reads `._est`.
- (verified) :186 `_student_opp_elixir = cfg.get("play","student_opp_elixir", default=False)`;
  :884 sends `None` to the model unless set. Live feeds S1 NOTHING for opponent elixir today.
- (per O8) `dets` reaching update() are pre-filtered by the `observation.detector_cards` whitelist
  (config.yaml:436-504), which contains no spell classes → opponent spells are never subtracted.

## Engine truth per tick
- pipeline/e1_eval.py:258-259: `bs = from_engine(compact_raw(state))` (BoardState.opp_elixir exact,
  obs_contract.py:142/326) then `view = live_view(bs, rng_obs, deck, cfg["noise"])`,
  `rng_obs = np.random.default_rng(crc32(f"{tag}:eval:{k}"))` — one RNG per match.
- No per-tick BoardState dumps exist on disk; training .npz are pre-tokenized rows.
- scratchpad/gauntlet/L67/opp_estimator_sim.py measures the estimator against icebow's HAND-WRITTEN
  sim (`SimMatchEnv`), not the engine — wrong instrument (sim crown match 26% vs engine 78%). Only its
  `_Det` shim shape was reused.

## Coordinates / costs
- BoardState x,y already normalized [0,1] (obs_contract.py:28-39); same units as the radii; no
  conversion needed offline.
- Engine name → vocab via `vocab.engine_key` / `engine_unit_id(name, max_hp)` (sub-spawns by max_hp);
  base via `vocab.base_key`; cost via `CardDB.elixir(base)` (cards.py:201-211). `mirror` → None.

STATUS: complete (lead transcription)
