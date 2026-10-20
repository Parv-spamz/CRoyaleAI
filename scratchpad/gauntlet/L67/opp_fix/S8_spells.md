# S8 scout — spell/effect-zone classes for opponent-elixir billing (LEAD TRANSCRIPTION)

NOTE: the foreman-scout agent type has Read/Glob/Grep only — it CANNOT write files. Both S7 and S8
"missing file" failures this session were tickets demanding the impossible. Transcribed by the lead from
the hand-back on 2026-09-16; the spell totals in §3 were re-derived by the lead from summary.json (the
scout's own total, ~630, undercounted). Citations are the scout's; (verified) = lead re-read.

## 1. Detector classes — pipeline/vocab.py:17-58 (DETECTOR_CLASSES), :73-81 (SPELL_CLASSES)
- 46 spell classes. Instant projectiles/flashes: tornado, rocket, the_log, arrows, barbarian_barrel,
  clone, earthquake, fireball, lightning, royal_delivery, zap (+ evo/hero variants).
- Persistent ground-effect zones (`_aoe`): arrows_aoe, barbarian_barrel_aoe, clone_aoe, earthquake_aoe,
  fireball_aoe, freeze_aoe, giant_snowball_aoe, goblin_barrel_aoe, goblin_curse_aoe, graveyard_aoe,
  lightning_aoe, poison_aoe, rage_aoe, rocket_aoe, royal_delivery_aoe, the_log_aoe, tornado_aoe,
  vines_aoe, void_aoe, zap_aoe.
- Zone durations (cards.yaml): poison 8.0 s, graveyard ~10 s, rage 4.5 s, earthquake 3.0 s, others 2-4 s.
- No per-class detector recall/precision for spell classes found (only the audit summary.json).

## 2. Whitelist mechanics — play.py:547, vocab.py:110-120
- play.py:547 compares `d.base` (base_key-stripped), not the raw class. `base_key` strips _ability,
  _hero, _evo, _aoe iteratively → `poison_aoe` → `poison`. A whitelist entry `poison` passes both.
- CardDB.elixir: clone 1; the_log, zap, freeze, rage 2; tornado, arrows, goblin_barrel, giant_snowball,
  void, vines, goblin_curse 3; fireball, lightning, barbarian_barrel, royal_delivery, poison, earthquake 4;
  graveyard 5; rocket 6. (Scout listed rage at 3; O12 read cards_stats.json directly: rage.elixir == 2.
  The §3 stakes total used the ledger's own elixir field, so it is unaffected.)

## 3. Stakes (lead-computed from summary.json `ghost_delivered_by_base`, 100 held-out ghosts)
- ZONES (persistent visual): graveyard 34/170, poison 26/104, vines 19/57, tornado 11/33, freeze 7/28,
  rage 12/24, earthquake 7/21, goblin_curse 5/10 → **447 elixir**.
- INSTANT: barbarian_barrel 133/266, lightning 22/132, fireball 30/120, goblin_barrel 37/111,
  rocket 18/108, the_log 43/86, zap 37/74, giant_snowball 36/72, arrows 18/54 → **1,023 elixir**.
- All delivered: 8,179. Spells = 18.0% of opponent spend; zones = 5.5% (~4.5 elixir/match).
- `the_log` IS whitelisted but was charged 0 in every engine condition: the engine BoardState carries no
  spells (compact_raw drops effects/projectiles), so spells cannot be billed on the engine instrument.

## 4. The team problem — replay_mine.py:364-393 (TeamTracker._verdict), opponent_elixir.py:94
- The evidence ladder (own-play anchor, motion, HP-bar votes, side prior, body art) fails for zones
  (no bar, no motion, ambiguous colour, centre-field) → "unknown" at :393.
- (verified) opponent_elixir.py:94 `if team != "enemy": continue` → zones are dropped before the
  whitelist matters. No zone team heuristic exists ("not found").

## 5. Re-billing risk — opponent_elixir.py:21-26
- forget_s 6.0, match_radius 0.07. A persistent zone is a long-lived stationary track: the tombstone
  pattern (7.6 charges/placement, BD) would apply until the estimator fix (step 2) lands.

## 6. hogeq — config.yaml detector_cards
- icebow:436-494 and hogeq:451-509 are identical (46 entries; `the_log` the only spell).

STATUS: complete (lead transcription)
