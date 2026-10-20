# Opening-hand recovery, October 5 10:45 EDT

The isolated reconstruction repair passes the training comparison and independent
recount. D1-D4 complete; N2-N7 remain open. It recovered **7 of 13** previously
excluded training replays under unchanged full-command, crown, terminal and
public-field requirements. All three previously successful training controls
retain identical logs, grades, final states and normalized public/pre-card frames.
All sixteen cases were repeated and match. Four openings remain unresolved;
two other captures remain excluded for crown mismatch (one also has missing,
rejected and skipped commands). None of those failures is waived.

The original driver abandoned both players' inferred opening arrangements when
either side failed its position-invariance probe. That explains early out-of-hand
rejections in the three reconstructable fresh Icebow/Witch encounters and appears
in thirteen historical training pilot records. The new resolver uses only the
original card sequence and measured initial hand/queue positions. It tries deck
permutations with forms/levels preserved, then verifies both complete card
sequences against the actual opening. It never sets hands, forces legal plays,
changes the random seed or selects an arrangement by game outcomes. Original
replay_drive.py and all native libraries/assets remain unchanged; the isolated
driver changes only its fallback and final opening verification.

The maximum is 61 solver resets plus the three inherited resets, or 64 total.
Successful training repairs used two or three solver resets. Fixed-budget
unresolved cases remain failures. The source audit covers all 807 original
collection records and all 183 unused exact-Icebow metadata groups. The latter
contain **zero opposing Goblin Barrel decks**, five Witch, 22 Night Witch and
17 Furnace deck encounters. Two Witch encounters still fail Void availability;
the other three are in the opening-fallback group. These counts do not establish
tactical opportunity denominators or sufficient power.

Validation: two positive/six negative solver controls, two positive/seven negative
independent frame/command controls, and the sixteen-case native comparison.
Receipts are l72-deal-recovery-source-audit, solver-controls, training-v3,
independent-v4 and recount-controls in L71/integration/checks. The independent
reader verifies original CSV/log membership, original forms, actual opening
hand/queue legality, full grades, every repeat and unchanged successful controls.

Preserve failures and precise corrections:

- v1 incorrectly asserted reset tick zero; the existing service bootstraps at
  tick ten. It stopped before replay commands. See RESET_CORRECTION.md.
- v2 compared in-memory integer side keys with string keys read from JSON. The
  saved first control matches. It also omitted three inherited resets from its
  budget. v3 uses serialized comparisons and tightens the solver to 61 resets.
- The initial new reader counted ability commands as pre-card frames. The
  unchanged source records pre-card frames only for ordinary card commands;
  v4 matches those exactly and still recounts every ability in the command log.

This creates no model or model improvement. The full replacement queue remains.
No IL/RL, model predictions, confirmation tuning, live setting change or Discord
model report occurred. Owner farming 37424/29536 remained active, STOP absent.

A separately frozen recovery batch is now running on all 65 non-training fallback
records: 12 development and 53 confirmation, tag ordered, every case repeated.
See deal_recovery/RESERVED_RECOVERY_PLAN.md, reserved_jobs.json and RESERVED_GATES.md.
Collector launcher 28292 / verifier launcher 18592 use the sole emulator5560.
At 10:45 five selections had completed, three usable, no fatal error. Do not
duplicate these jobs or edit their bound sources. Original collections remain
immutable. After completion review reserved_verified.json before a new capacity
inventory; the missing Barrel source and other N2 requirements remain unresolved.
PUBLIC_SOURCE_CHECK.md records additional dataset-schema checks without bulk
downloads, inferred forms, credentials or challenge bypass.
