# gen_v3 smoke and pending integration

Status: DONE_WITH_CONCERNS. The approved continuation completed production SIM/RL integration. See SIM_REPORT.md for exact parity, smoke evidence, 274 passing CPU tests, one Windows pipe skip, five no-git exclusions and launch commands. Original dataset smoke results below are preserved.

50 replays; 12,448 rows; 50,440 tokens; 0 failures. Unit-form shape (50440,), opponent-history shape (12448, 3, 5). Evolved tokens 9.7304%; hero tokens 7.5139%; rows with opponent plays 94.0071%.

Per-card counts are entity observations across frames/play_frames, not unique bodies (no stable ids in these 50 recordings). Token shares count the emitted dataset tokens.

| Card | Evo observations | Hero observations | Ambiguous, kept base |
|---|---:|---:|---:|
| archers | 327 | 0 | 163 |
| baby-dragon | 224 | 0 | 70 |
| balloon | 0 | 462 | 0 |
| barbarian-barrel | 0 | 16 | 0 |
| barbarians | 130 | 0 | 0 |
| bats | 51 | 0 | 47 |
| battle-ram | 60 | 0 | 45 |
| berserker | 0 | 330 | 0 |
| bomber | 12 | 0 | 0 |
| bowler | 0 | 379 | 0 |
| cannon | 15 | 0 | 0 |
| dark-prince | 0 | 71 | 0 |
| electro-dragon | 55 | 0 | 0 |
| executioner | 51 | 0 | 0 |
| firecracker | 10 | 0 | 0 |
| furnace | 111 | 0 | 17 |
| giant | 0 | 87 | 0 |
| giant-snowball | 0 | 0 | 0 |
| goblin-barrel | 0 | 0 | 155 |
| goblin-giant | 227 | 0 | 0 |
| goblins | 0 | 315 | 0 |
| ice-golem | 0 | 164 | 0 |
| inferno-dragon | 129 | 0 | 38 |
| knight | 1508 | 1100 | 879 |
| lumberjack | 30 | 0 | 14 |
| mega-knight | 157 | 0 | 0 |
| mega-minion | 0 | 277 | 0 |
| mini-pekka | 0 | 308 | 0 |
| minion-horde | 351 | 0 | 96 |
| mortar | 109 | 0 | 58 |
| musketeer | 95 | 0 | 0 |
| pekka | 56 | 0 | 0 |
| royal-ghost | 77 | 0 | 0 |
| royal-giant | 75 | 0 | 0 |
| royal-hogs | 336 | 0 | 65 |
| skeleton-army | 378 | 0 | 1734 |
| skeleton-barrel | 294 | 0 | 234 |
| skeletons | 577 | 0 | 0 |
| tesla | 1253 | 0 | 444 |
| tombstone | 0 | 1193 | 0 |
| valkyrie | 33 | 495 | 0 |
| wall-breakers | 107 | 0 | 0 |
| witch | 259 | 0 | 25 |
| wizard | 13 | 15 | 0 |
| zap | 0 | 0 | 0 |

Goblin Barrel: no reliable evolution attribution in this smoke; units stay base. Zap and Giant Snowball have no board bodies to tag. Other cards can have partially untagged, ambiguous cohorts, listed above.

Recording checks: all Hero Goblins bodies include both 202-HP goblins and the 2560-HP flag. Tagged evolved Bats have 122 max HP; tagged Skeleton Barrel parents have 665 max HP (base parents are 532). Per-form HP distributions are in smoke_result.json.

The seven-column play-frame field is kind, not entity identity; all 37,560 play-frame entity observations in these 50 files use kind 12/13/14/15. No unique-body counts are claimed. Explicit ids are supported when a recording supplies entity_ids or entity_fields.

Previously missing integration (now completed by the approved SIM continuation; details in SIM_REPORT.md):

- pipeline/eval_gen.py: checkpoint args must reach GenModel(feature_version=...); shared GenRows must batch unit_form and opp_past. The implemented trainer currently uses its own versioned GenRows subclass.
- pipeline/royale_env.py: preserve entity status_flags and expose accepted public plays including landing tick, coordinates and actual form from pre-command evo/hero state; reset per match.
- pipeline/e1_view.py: preserve unit.form when constructing noisy copies (zero form on false-positive class substitutions).
- pipeline/rl_royale.py: use versioned row keys in policy_terms/value passes; carry both new arrays through trajectory aggregation and pro-agreement loading; construct actor models from stored feature_version.
- Then finish the already-authorized e1_eval wiring: enable version from the policy before env reset, preserve forms through compacting/noise/extrapolation, and consume the public landing log. Current v3 SIM helper refuses adapters lacking those fields. Old policies continue on their original path.

Public LIVE limitations: detected birth centroid approximates placement; first-sighting tick approximates play time; bodyless spells remain invisible to the existing PlayDetector. No opponent private state is read.

No full build, training, GPU jobs, ADB/live runs, git, agents or research/ext source edits were performed.
